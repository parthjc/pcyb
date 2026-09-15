#!/usr/bin/env python3
"""
ZYNTRASEC // GREEN BLACK RED
Professional local searcher for very large JSON-array databases.

Design:
- Does NOT load the whole database into RAM.
- Uses memory mapping for fast local scanning.
- Searches selected fields or all supported fields.
- Supports exact / contains / starts-with matching.
- Optional Region filter.
- Responsive Tkinter GUI with Pause / Resume / Stop.
- Results shown in a sortable table.
- Exports CSV / JSONL / XLSX (XLSX requires openpyxl).
- Keeps generated exports in ./data.
- Intended for local, authorized datasets.
"""

import csv
import json
import mmap
import os
import re
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP = "ZYNTRASEC // GREEN BLACK RED"
OUTPUT_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

FIELD_MAP = {
    "All fields": None,
    "Internal ID": "_id",
    "Mobile": "mobile",
    "Name": "name",
    "Father Name": "fname",
    "Address": "address",
    "Region": "circle",
    "Document ID": "id",
    "Email": "email",
    "Alternate": "alt",
}

DISPLAY_FIELDS = [
    ("_id", "Internal ID"),
    ("mobile", "Mobile"),
    ("name", "Name"),
    ("fname", "Father Name"),
    ("address", "Address"),
    ("circle", "Region"),
    ("id", "Document ID"),
    ("email", "Email"),
    ("alt", "Alternate"),
]


class Searcher:
    """
    V4 chunked native scanner.

    The file stays memory-mapped, but searching is performed in bounded chunks
    so the GUI receives frequent progress updates even when a match is rare.
    """

    CHUNK_SIZE = 4 * 1024 * 1024
    OVERLAP = 256 * 1024

    def __init__(self, path, field, query, mode, region, case_sensitive,
                 max_results, stop_event, pause_event, callback, progress,
                 start_offset=0):
        self.path = path
        self.field = field
        self.query = query
        self.mode = mode
        self.region = region
        self.case_sensitive = case_sensitive
        self.max_results = max_results
        self.stop_event = stop_event
        self.pause_event = pause_event
        self.callback = callback
        self.progress = progress
        self.matches = 0
        self.scanned = 0
        self.start_time = time.time()
        self.start_offset = max(0, int(start_offset))
        self._seen = set()

    def _text(self, v):
        if v is None:
            return ""
        if isinstance(v, dict):
            if "$oid" in v:
                return str(v["$oid"])
            return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
        if isinstance(v, list):
            return " ".join(self._text(x) for x in v)
        return str(v)

    def _match(self, value):
        a = self._text(value)
        b = self.query
        if not self.case_sensitive:
            a, b = a.casefold(), b.casefold()
        if self.mode == "Exact":
            return a == b
        if self.mode == "Starts with":
            return a.startswith(b)
        return b in a

    def _record_match(self, rec):
        if self.region:
            region = self._text(rec.get("circle"))
            if self.region.casefold() not in region.casefold():
                return False

        if self.field is None:
            return any(self._match(v) for v in rec.values())
        return self._match(rec.get(self.field))

    def _object_start(self, mm, pos):
        # IMPORTANT: a field value can be inside the nested _id object.
        # Searching for the nearest "{" can therefore decode {"$oid": ...}
        # instead of the complete record. Prefer the top-level record marker
        # used by the supplied database schema.
        floor = max(0, pos - 32 * 1024 * 1024)

        markers = (b'{"_id"', b'{ "_id"', b'{\n"_id"')
        candidates = [mm.rfind(marker, floor, pos + 1) for marker in markers]
        s = max(candidates)

        if s >= 0:
            return s

        # Generic fallback for JSON arrays whose objects do not start with
        # _id. This keeps the scanner usable with other simple JSON schemas.
        s = mm.rfind(b"{", floor, pos + 1)
        return s if s >= 0 else pos

    def _decode_candidate(self, mm, pos):
        s = self._object_start(mm, pos)
        # Give the decoder enough room for normal records while avoiding
        # allocating anything proportional to the whole database.
        raw = mm[s:s + 16 * 1024 * 1024]
        try:
            obj, end = json.JSONDecoder().raw_decode(
                raw.decode("utf-8", errors="replace"), 0
            )
            if isinstance(obj, dict):
                return obj, s, end
        except Exception:
            pass
        return None, s, 0

    def _regex(self):
        flags = 0 if self.case_sensitive else re.IGNORECASE
        key = re.escape(self.field.encode("utf-8"))
        q = re.escape(self.query.encode("utf-8"))

        if self.mode == "Exact":
            value = q
        elif self.mode == "Starts with":
            value = q + rb'(?:\\.|[^"\\])*'
        else:
            value = rb'(?:\\.|[^"\\])*?' + q + rb'(?:\\.|[^"\\])*'

        return re.compile(
            rb'"' + key + rb'"\s*:\s*"' + value + rb'"', flags
        )

    def _report(self, pos, total):
        elapsed = max(time.time() - self.start_time, 0.001)
        mbps = (pos / 1048576) / elapsed
        eta = ((total - pos) / 1048576) / mbps if mbps > 0 else 0
        self.progress(min(pos, total), total, self.scanned,
                      self.matches, mbps, eta)

    def _candidate(self, mm, pos):
        obj, obj_start, _ = self._decode_candidate(mm, pos)
        if obj is None or obj_start in self._seen:
            return
        self._seen.add(obj_start)
        self.scanned += 1

        if self._record_match(obj):
            self.matches += 1
            self.callback(obj)

    def _pause_point(self):
        while self.pause_event.is_set() and not self.stop_event.is_set():
            time.sleep(0.05)

    def _field_search(self, mm, total):
        pattern = self._regex()
        start = min(self.start_offset, total)
        last_report = 0.0

        while start < total and not self.stop_event.is_set():
            # Check control flags before every small work unit.
            self._pause_point()
            if self.stop_event.is_set():
                break

            end = min(total, start + self.CHUNK_SIZE)
            search_end = min(total, end + self.OVERLAP)

            # 4 MB bounded regex work keeps STOP/PAUSE responsive even when
            # there are no matches in a region.
            for m in pattern.finditer(mm, start, search_end):
                if self.stop_event.is_set():
                    break
                self._pause_point()
                if self.stop_event.is_set():
                    break

                if m.start() >= end and end < total:
                    break

                self._candidate(mm, m.start())

                if self.max_results and self.matches >= self.max_results:
                    self._report(end, total)
                    return

            start = end

            # Telemetry is emitted after every bounded chunk.
            now = time.time()
            if now - last_report >= 0.05 or start >= total:
                self._report(start, total)
                last_report = now

        final_pos = start
        self._report(final_pos, total)

    def _all_field_search(self, mm, total):
        needle = self.query.encode("utf-8")
        flags = re.IGNORECASE if not self.case_sensitive else 0
        pattern = re.compile(re.escape(needle), flags) if not self.case_sensitive else None

        start = min(self.start_offset, total)
        last_report = 0.0

        while start < total and not self.stop_event.is_set():
            self._pause_point()
            if self.stop_event.is_set():
                break

            end = min(total, start + self.CHUNK_SIZE)
            search_end = min(total, end + self.OVERLAP)

            if pattern:
                iterator = pattern.finditer(mm, start, search_end)
                positions = (m.start() for m in iterator)
            else:
                def positions_gen(a, b):
                    p = mm.find(needle, a, b)
                    while p >= 0:
                        yield p
                        p = mm.find(needle, p + 1, b)
                positions = positions_gen(start, search_end)

            for pos in positions:
                if self.stop_event.is_set():
                    break
                if pos >= end and end < total:
                    break

                self._pause_point()
                if self.stop_event.is_set():
                    break

                self._candidate(mm, pos)

                if self.max_results and self.matches >= self.max_results:
                    self._report(end, total)
                    return

            start = end
            now = time.time()
            if now - last_report >= 0.05 or start >= total:
                self._report(start, total)
                last_report = now

        self._report(start, total)

    def run(self):
        total = os.path.getsize(self.path)
        with open(self.path, "rb") as f, mmap.mmap(
            f.fileno(), 0, access=mmap.ACCESS_READ
        ) as mm:
            if mm[:1] != b"[":
                raise ValueError("Expected a top-level JSON array.")

            supported = {
                "mobile", "name", "fname", "address",
                "circle", "id", "email", "alt"
            }

            if self.field in supported:
                self._field_search(mm, total)
            else:
                self._all_field_search(mm, total)

            elapsed = max(time.time() - self.start_time, .001)
            self._report(total if not self.stop_event.is_set() else 0, total)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP)
        self.geometry("1280x760")
        self.minsize(1050, 650)

        self.file_var = tk.StringVar()
        self.field_var = tk.StringVar(value="All fields")
        self.query_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="Contains")
        self.region_var = tk.StringVar(value="")
        self.case_var = tk.BooleanVar(value=False)
        self.max_var = tk.StringVar(value="100")
        self.engine_var = tk.StringVar(value="AUTO")
        self.mask_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready")
        self.stats_var = tk.StringVar(value="Bytes scanned: 0 B / 0 B | Candidates: 0 | Matches: 0 | 0.0 MB/s | ETA --")
        self.progress_var = tk.DoubleVar()
        self.elapsed_var = tk.StringVar(value="Elapsed: 00:00:00")

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.worker = None
        self.rows = []
        self.search_args = None
        self.resume_offset = 0
        self.session_file = None
        self.results_file = None
        self.last_checkpoint_time = 0.0
        self.disk_error = False

        self._style()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

    def _style(self):
        # GREEN / BLACK / RED cyber-console theme.
        self.configure(bg="#030504")

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        bg = "#030504"
        panel = "#071009"
        panel2 = "#0a160d"
        field = "#020603"
        fg = "#d7e8dc"
        muted = "#66806e"
        green = "#00ff66"
        green2 = "#18c96b"
        red = "#ff304f"
        red_dark = "#5e1420"
        border = "#174a29"

        style.configure(".", background=bg, foreground=fg,
                        font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=bg, foreground=green,
                        font=("Segoe UI Semibold", 21, "bold"))
        style.configure("Sub.TLabel", background=bg, foreground=muted,
                        font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=bg, foreground=green,
                        font=("Consolas", 9, "bold"))

        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=panel, foreground=green,
                        bordercolor=border, relief="solid")
        style.configure("TLabelframe.Label", background=panel,
                        foreground=green, font=("Segoe UI Semibold", 9))
        style.configure("TLabel", background=panel, foreground=fg)

        style.configure("TButton", background=panel2, foreground=green,
                        bordercolor=border, padding=(13, 7),
                        font=("Segoe UI Semibold", 9))
        style.map("TButton",
                  background=[("active", "#102d18"),
                              ("pressed", "#174522"),
                              ("disabled", "#070b08")],
                  foreground=[("active", "#ffffff"),
                              ("disabled", "#3f5947")])

        style.configure("Accent.TButton", background="#092b16",
                        foreground=green, bordercolor="#23783d",
                        padding=(14, 7), font=("Segoe UI Semibold", 9))
        style.map("Accent.TButton",
                  background=[("active", "#124321"),
                              ("pressed", "#185a2d")],
                  foreground=[("active", "#ffffff")])

        style.configure("Danger.TButton", background="#26090f",
                        foreground=red, bordercolor=red_dark,
                        padding=(13, 7), font=("Segoe UI Semibold", 9))
        style.map("Danger.TButton",
                  background=[("active", "#48101b"),
                              ("pressed", "#611322")],
                  foreground=[("active", "#ffffff")])

        style.configure("TEntry", fieldbackground=field, foreground=fg,
                        insertcolor=green, bordercolor=border, padding=7)
        style.configure("TCombobox", fieldbackground=field, foreground=fg,
                        background=panel2, arrowcolor=green,
                        bordercolor=border, padding=5)
        style.map("TCombobox",
                  fieldbackground=[("readonly", field)],
                  foreground=[("readonly", fg)])

        style.configure("TCheckbutton", background=panel, foreground=fg)
        style.map("TCheckbutton", foreground=[("active", green)])

        style.configure("Horizontal.TProgressbar",
                        background=green, troughcolor="#0a100c",
                        bordercolor=border, lightcolor=green,
                        darkcolor=green)

        style.configure("Treeview", background="#020603",
                        fieldbackground="#020603", foreground=fg,
                        rowheight=29, font=("Segoe UI", 9),
                        bordercolor=border)
        style.map("Treeview",
                  background=[("selected", "#123b20")],
                  foreground=[("selected", "#ffffff")])
        style.configure("Treeview.Heading", background="#0a1b0f",
                        foreground=green, relief="flat",
                        font=("Segoe UI Semibold", 9))


    def _build(self):
        top = ttk.Frame(self, padding=14)
        top.pack(fill="x")

        ttk.Label(top, text="ZYNTRASEC // GREEN BLACK RED", style="Title.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(top, text="Local large-JSON search • native fast-path • chunked progress • RAM-friendly • authorized data only",
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w")

        file_frame = ttk.LabelFrame(self, text="Database", padding=10)
        file_frame.pack(fill="x", padx=14, pady=(0, 8))
        ttk.Entry(file_frame, textvariable=self.file_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(file_frame, text="Browse", command=self.browse).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(file_frame, text="Open Session", command=self._load_session).grid(row=0, column=2, padx=(6, 0))
        file_frame.columnconfigure(0, weight=1)

        search = ttk.LabelFrame(self, text="Search", padding=10)
        search.pack(fill="x", padx=14, pady=8)

        ttk.Label(search, text="Field").grid(row=0, column=0, sticky="w")
        self.field_combo = ttk.Combobox(
            search, textvariable=self.field_var,
            values=list(FIELD_MAP.keys()), state="readonly", width=18)
        self.field_combo.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        ttk.Label(search, text="Value").grid(row=0, column=1, sticky="w")
        ttk.Entry(search, textvariable=self.query_var).grid(
            row=1, column=1, padx=(0, 8), sticky="ew")

        ttk.Label(search, text="Match").grid(row=0, column=2, sticky="w")
        ttk.Combobox(search, textvariable=self.mode_var,
                     values=["Contains", "Exact", "Starts with"],
                     state="readonly", width=13).grid(
            row=1, column=2, padx=(0, 8))

        ttk.Label(search, text="Region filter").grid(row=0, column=3, sticky="w")
        ttk.Entry(search, textvariable=self.region_var, width=18).grid(
            row=1, column=3, padx=(0, 8))

        ttk.Label(search, text="Max results").grid(row=0, column=4, sticky="w")
        ttk.Entry(search, textvariable=self.max_var, width=10).grid(row=1, column=4)

        ttk.Checkbutton(search, text="Case sensitive",
                        variable=self.case_var).grid(row=1, column=5, padx=10)

        ttk.Label(search, text="Engine").grid(row=0, column=6, sticky="w")
        ttk.Combobox(search, textvariable=self.engine_var,
                     values=["AUTO", "NATIVE FAST", "STREAM"],
                     state="readonly", width=11).grid(row=1, column=6, padx=(8, 0))

        ttk.Checkbutton(search, text="Mask sensitive fields",
                        variable=self.mask_var).grid(row=1, column=7, padx=8)

        for c in range(8):
            search.columnconfigure(c, weight=1 if c in (0, 1) else 0)

        controls = ttk.Frame(self, padding=(14, 2))
        controls.pack(fill="x")

        self.search_btn = ttk.Button(controls, text="SEARCH", command=self.start, style="Accent.TButton")
        self.search_btn.pack(side="left", padx=(0, 6))
        self.pause_btn = ttk.Button(controls, text="PAUSE", command=self.pause,
                                    state="disabled")
        self.pause_btn.pack(side="left", padx=6)
        self.resume_btn = ttk.Button(controls, text="RESUME", command=self.resume,
                                     state="disabled")
        self.resume_btn.pack(side="left", padx=6)
        self.stop_btn = ttk.Button(controls, text="STOP", command=self.stop,
                                   state="disabled")
        self.stop_btn.pack(side="left", padx=6)
        ttk.Button(controls, text="CLEAR", command=self.clear).pack(side="left", padx=6)
        ttk.Button(controls, text="EXPORT", command=self.export).pack(side="left", padx=6)
        ttk.Button(controls, text="EXIT", command=self.exit_app,
                   style="Danger.TButton").pack(side="left", padx=6)

        ttk.Button(controls, text="Preview 100", command=self.preview).pack(
            side="right", padx=6)

        status = ttk.LabelFrame(self, text="Progress", padding=8)
        status.pack(fill="x", padx=14, pady=8)
        ttk.Progressbar(status, variable=self.progress_var,
                        maximum=100).pack(fill="x")
        ttk.Label(status, textvariable=self.status_var).pack(anchor="w", pady=(4, 0))
        ttk.Label(status, textvariable=self.stats_var).pack(anchor="w")
        ttk.Label(status, textvariable=self.elapsed_var).pack(anchor="w")

        result_frame = ttk.LabelFrame(self, text="Results", padding=6)
        result_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        columns = [x[0] for x in DISPLAY_FIELDS]
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="browse")
        for key, title in DISPLAY_FIELDS:
            self.tree.heading(key, text=title,
                              command=lambda k=key: self.sort_column(k, False))
            self.tree.column(key, width=130, minwidth=80)
        self.tree.column("address", width=300)
        self.tree.column("email", width=220)

        y = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        x = ttk.Scrollbar(result_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.show_detail)

        detail = ttk.LabelFrame(self, text="Selected Record", padding=8)
        detail.pack(fill="x", padx=14, pady=(0, 14))
        self.detail_text = tk.Text(detail, height=5, wrap="word",
                                   font=("Consolas", 9), relief="flat")
        self.detail_text.pack(fill="x")
        self.detail_text.insert("1.0", "Select a result to inspect its fields.")
        self.detail_text.config(state="disabled")

    def browse(self):
        p = filedialog.askopenfilename(
            title="Select JSON database",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if p:
            self.file_var.set(p)
            size = os.path.getsize(p)
            self.status_var.set(f"Ready • {Path(p).name} • {size/1073741824:.2f} GB • Engine: {self.engine_var.get()}")

    def _validate(self):
        p = self.file_var.get().strip()
        if not p or not os.path.isfile(p):
            messagebox.showerror("File", "Please select a valid JSON file.")
            return None
        q = self.query_var.get()
        if not q:
            messagebox.showwarning("Search", "Enter a search value.")
            return None
        try:
            m = int(self.max_var.get())
            if m < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Max results", "Use 0 for unlimited or a positive integer.")
            return None
        return p, q, m

    def _new_session_files(self):
        stamp = time.strftime("%Y%m%d_%H%M%S")
        self.session_file = OUTPUT_DIR / f"session_{stamp}.json"
        self.results_file = OUTPUT_DIR / f"session_{stamp}_results.jsonl"
        self.results_file.write_text("", encoding="utf-8")
        self._save_checkpoint(0, "running")

    def _save_checkpoint(self, offset, state):
        if not self.session_file:
            return
        self.resume_offset = max(0, int(offset))
        payload = {
            "version": 1,
            "state": state,
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "database": self.file_var.get().strip(),
            "field": self.field_var.get(),
            "query": self.query_var.get(),
            "match": self.mode_var.get(),
            "region": self.region_var.get().strip(),
            "case_sensitive": bool(self.case_var.get()),
            "max_results": int(self.max_var.get() or 0),
            "engine": self.engine_var.get(),
            "resume_offset": self.resume_offset,
            "results_file": str(self.results_file) if self.results_file else "",
            "result_count": len(self.rows),
        }
        tmp = self.session_file.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            os.replace(tmp, self.session_file)
        except OSError:
            # The checkpoint is on the app's local drive, not the database
            # drive. Never let a checkpoint failure kill the scan.
            pass

    def _autosave_result(self, rec):
        if not self.results_file:
            return
        try:
            with open(self.results_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _load_session(self):
        p = filedialog.askopenfilename(
            title="Open ZYNTRASEC session checkpoint",
            initialdir=str(OUTPUT_DIR),
            filetypes=[("Session files", "session_*.json"), ("JSON files", "*.json")]
        )
        if not p:
            return
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            db = data.get("database", "")
            if not db:
                raise ValueError("Session has no database path.")
            self.file_var.set(db)
            self.field_var.set(data.get("field", "All fields"))
            self.query_var.set(data.get("query", ""))
            self.mode_var.set(data.get("match", "Contains"))
            self.region_var.set(data.get("region", ""))
            self.case_var.set(bool(data.get("case_sensitive", False)))
            self.max_var.set(str(data.get("max_results", 100)))
            self.engine_var.set(data.get("engine", "AUTO"))
            self.session_file = Path(p)
            rf = data.get("results_file", "")
            self.results_file = Path(rf) if rf else None
            self.resume_offset = int(data.get("resume_offset", 0) or 0)
            self.rows.clear()
            for item in self.tree.get_children():
                self.tree.delete(item)
            if self.results_file and self.results_file.exists():
                with self.results_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                        except Exception:
                            continue
                        self.rows.append(rec)
                        self._add_row(rec, autosave=False)
            self.disk_error = False
            self.status_var.set(
                f"[+] CHECKPOINT LOADED  ::  resume at {self.resume_offset/1073741824:.2f} GB"
            )
            self.resume_btn.config(state="normal")
        except Exception as e:
            messagebox.showerror("Session", f"Could not load checkpoint:\n{e}")

    def start(self):
        args = self._validate()
        if not args:
            return
        if self.worker and self.worker.is_alive():
            self.status_var.set("[!] A SCAN IS ALREADY RUNNING")
            return

        self.clear_results_only()
        self.stop_event.clear()
        self.pause_event.clear()
        self._telemetry_start = time.time()
        self.resume_offset = 0
        self.disk_error = False
        self.last_checkpoint_time = 0.0
        self._new_session_files()

        p, q, m = args
        self.search_args = (p, FIELD_MAP[self.field_var.get()], q,
                            self.mode_var.get(), self.region_var.get().strip(),
                            self.case_var.get(), m)
        field = FIELD_MAP[self.field_var.get()]

        self.search_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Searching…")

        self.worker = threading.Thread(
            target=self._run_search,
            args=(p, field, q, self.mode_var.get(), self.region_var.get().strip(),
                  self.case_var.get(), m),
            daemon=True
        )
        self.worker.start()

    def _run_search(self, *args):
        try:
            offset = self.resume_offset
            s = Searcher(*args, self.stop_event, self.pause_event,
                         self.add_result, self.update_progress,
                         start_offset=offset)
            s.run()
            stopped = self.stop_event.is_set()
            self._save_checkpoint(self.resume_offset, "stopped" if stopped else "complete")
            self.after(0, self.finished, stopped)
        except (OSError, ValueError) as e:
            self.disk_error = True
            self._save_checkpoint(self.resume_offset, "disk_disconnected")
            self.after(0, lambda err=str(e): self._disk_lost(err))
        except Exception as e:
            self._save_checkpoint(self.resume_offset, "error")
            self.after(0, lambda err=str(e): messagebox.showerror("Search error", err))
            self.after(0, lambda: self.finished(True))

    def add_result(self, rec):
        self.after(0, lambda r=rec: self._add_row(r))

    def _display_value(self, key, value):
        if isinstance(value, dict):
            value = value.get("$oid", json.dumps(value, ensure_ascii=False))
        elif isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False)
        value = "" if value is None else str(value)

        if not self.mask_var.get():
            return value

        sensitive = {"mobile", "alt", "email", "address", "id"}
        if key not in sensitive or not value:
            return value
        if "@" in value:
            local, _, domain = value.partition("@")
            return (local[:1] + "•••@" + domain) if local else "•••@" + domain
        if len(value) <= 4:
            return "••••"
        return value[:2] + "•" * min(8, len(value) - 4) + value[-2:]

    def _add_row(self, rec, autosave=True):
        vals = []
        for key, _ in DISPLAY_FIELDS:
            vals.append(self._display_value(key, rec.get(key, "")))
        self.rows.append(rec)
        self.tree.insert("", "end", values=vals)
        if autosave:
            self._autosave_result(rec)
            self._save_checkpoint(self.resume_offset, "running")

    def show_detail(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if idx >= len(self.rows):
            return
        rec = self.rows[idx]
        lines = []
        for key, label in DISPLAY_FIELDS:
            lines.append(f"{label}: {self._display_value(key, rec.get(key, ''))}")
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.config(state="disabled")

    def update_progress(self, pos, total, scanned, matches, mbps, eta):
        self.resume_offset = max(0, int(pos))
        now = time.time()
        if now - self.last_checkpoint_time >= 1.0:
            self.last_checkpoint_time = now
            self._save_checkpoint(self.resume_offset, "running")
        pct = (pos / total * 100) if total else 0
        self.after(0, lambda: self._progress(pct, scanned, matches, mbps, eta))

    def _progress(self, pct, scanned, matches, mbps, eta):
        self.progress_var.set(pct)

        # Convert percentage back to bytes for a clear, byte-addressed view.
        p = self.file_var.get().strip()
        try:
            total = os.path.getsize(p)
            done = int(total * (pct / 100.0))
        except Exception:
            total = 0
            done = 0

        def fmt_bytes(n):
            units = ("B", "KB", "MB", "GB", "TB")
            x = float(max(n, 0))
            for u in units:
                if x < 1024 or u == units[-1]:
                    return f"{x:.1f} {u}" if u != "B" else f"{int(x)} B"
                x /= 1024

        eta_txt = "--"
        if eta > 0:
            sec = int(eta)
            h, sec = divmod(sec, 3600)
            m, sec = divmod(sec, 60)
            eta_txt = f"{h:02d}:{m:02d}:{sec:02d}"

        elapsed = max(time.time() - getattr(self, "_telemetry_start", time.time()), 0.0)
        h, rem = divmod(int(elapsed), 3600)
        m, s = divmod(rem, 60)

        self.stats_var.set(
            f"Bytes scanned: {fmt_bytes(done)} / {fmt_bytes(total)} | "
            f"Candidates: {scanned:,} | Matches: {matches:,} | "
            f"{mbps:.1f} MB/s | ETA {eta_txt}"
        )
        self.elapsed_var.set(f"Elapsed: {h:02d}:{m:02d}:{s:02d}")

    def pause(self):
        if not (self.worker and self.worker.is_alive()):
            self.status_var.set("[!] NO ACTIVE SCAN")
            return
        self.pause_event.set()
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="normal")
        self.status_var.set("[!] SCAN PAUSED  ::  waiting for RESUME")

    def resume(self):
        if self.worker and self.worker.is_alive():
            self.pause_event.clear()
            self.resume_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.status_var.set("[*] SCANNING DATABASE…")
            return

        if not self.search_args:
            self.status_var.set("[!] NO SAVED SCAN")
            return

        p = self.search_args[0]
        if not os.path.isfile(p):
            self.status_var.set("[!] DATABASE NOT AVAILABLE  ::  reconnect drive first")
            return

        self.stop_event.clear()
        self.pause_event.clear()
        self.disk_error = False
        self._telemetry_start = time.time()
        self.search_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set(
            f"[*] RESUMING FROM {self.resume_offset / 1073741824:.2f} GB…"
        )

        self.worker = threading.Thread(
            target=self._run_search,
            args=self.search_args,
            daemon=True
        )
        self.worker.start()

    def stop(self):
        if not (self.worker and self.worker.is_alive()):
            self.status_var.set("[!] NO ACTIVE SCAN")
            return
        self.stop_event.set()
        self.pause_event.clear()
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.status_var.set("[!] STOP REQUESTED  ::  finishing current small chunk")

    def _disk_lost(self, err):
        self.stop_event.set()
        self.pause_event.clear()
        self.worker = None
        self.search_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set(
            "[!] DATABASE DRIVE DISCONNECTED  ::  checkpoint saved  ::  reconnect drive and press RESUME"
        )
        messagebox.showwarning(
            "Database drive disconnected",
            "The database drive became unavailable.\n\n"
            "Your collected results and checkpoint were saved in the local data folder.\n"
            "Reconnect the drive, then press RESUME to continue from the saved byte position.\n\n"
            f"Last saved position: {self.resume_offset / 1073741824:.2f} GB"
        )

    def finished(self, stopped=False):
        self.search_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.resume_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self._save_checkpoint(self.resume_offset, "stopped" if stopped else "complete")
        self.status_var.set("[!] SCAN STOPPED  ::  checkpoint + results saved" if stopped else "[✓] SCAN COMPLETE  ::  results saved")
        self.worker = None

    def clear_results_only(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.rows.clear()
        self.progress_var.set(0)
        self.stats_var.set("Bytes scanned: 0 B / 0 B | Candidates: 0 | Matches: 0 | 0.0 MB/s | ETA --")
        self.elapsed_var.set("Elapsed: 00:00:00")
        if hasattr(self, "detail_text"):
            self.detail_text.config(state="normal")
            self.detail_text.delete("1.0", "end")
            self.detail_text.insert("1.0", "Select a result to inspect its fields.")
            self.detail_text.config(state="disabled")

    def clear(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.pause_event.clear()
            self.status_var.set("[!] CLEAR REQUESTED  ::  stopping scan…")
            self.after(50, self._clear_when_idle)
            return
        self.clear_results_only()
        self.status_var.set("[+] READY")

    def _clear_when_idle(self):
        if self.worker and self.worker.is_alive():
            self.after(50, self._clear_when_idle)
            return
        self.clear_results_only()
        self.status_var.set("[+] READY")

    def exit_app(self):
        # Wait for the worker before destroying Tk so queued callbacks
        # cannot target a destroyed interpreter.
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.pause_event.clear()
            self.search_btn.config(state="disabled")
            self.pause_btn.config(state="disabled")
            self.resume_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.status_var.set("[!] EXIT REQUESTED  ::  stopping scan…")
            self.after(50, self._exit_when_idle)
        else:
            self.destroy()

    def _exit_when_idle(self):
        if self.worker and self.worker.is_alive():
            self.after(50, self._exit_when_idle)
        else:
            self.destroy()


    def preview(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Preview", "Stop the active search before opening Preview 100.")
            return
        p = self.file_var.get().strip()
        if not p or not os.path.isfile(p):
            messagebox.showerror("File", "Select a JSON file first.")
            return

        self.clear_results_only()
        self.status_var.set("Reading first 100 records…")

        def work():
            try:
                data = []
                with open(p, "rb") as f:
                    dec = json.JSONDecoder()
                    raw = f.read(64 * 1024 * 1024).decode("utf-8", errors="replace")
                start = raw.find("[")
                pos = start + 1
                while len(data) < 100 and pos < len(raw):
                    while pos < len(raw) and raw[pos] in " \t\r\n,":
                        pos += 1
                    if pos >= len(raw) or raw[pos] == "]":
                        break
                    obj, end = dec.raw_decode(raw, pos)
                    if isinstance(obj, dict):
                        data.append(obj)
                    pos = end
                self.after(0, lambda: self._show_preview(data))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Preview", str(e)))

        threading.Thread(target=work, daemon=True).start()

    def _show_preview(self, data):
        for r in data:
            self._add_row(r)
        self.status_var.set(f"Preview loaded: {len(data)} records")

    def sort_column(self, col, reverse):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(key=lambda x: x[0].casefold(), reverse=reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def export(self):
        if not self.rows:
            messagebox.showinfo("Export", "No results to export.")
            return

        stamp = time.strftime("%Y%m%d_%H%M%S")
        base = OUTPUT_DIR / f"search_{stamp}"

        # Always create JSONL because it is streaming-friendly and dependency-free.
        jsonl = base.with_suffix(".jsonl")
        with open(jsonl, "w", encoding="utf-8") as f:
            for r in self.rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        csv_path = base.with_suffix(".csv")
        keys = [k for k, _ in DISPLAY_FIELDS]
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in self.rows:
                row = {}
                for k in keys:
                    v = r.get(k, "")
                    if isinstance(v, (dict, list)):
                        v = json.dumps(v, ensure_ascii=False)
                    row[k] = "" if v is None else str(v)
                w.writerow(row)

        # Standalone professional HTML report.
        html_path = base.with_suffix(".html")
        def esc(v):
            import html
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            return html.escape("" if v is None else str(v))

        title = "ZYNTRASEC // GREEN BLACK RED — Search Report"
        generated = time.strftime("%d %b %Y, %H:%M:%S")
        field_name = self.field_var.get()
        query_value = self.query_var.get()
        region_value = self.region_var.get().strip()

        rows_html = []
        for i, r in enumerate(self.rows, 1):
            cells = []
            for key, _ in DISPLAY_FIELDS:
                cells.append(f"<td>{esc(r.get(key, ''))}</td>")
            rows_html.append(f'<tr><td class="num">{i}</td>{"".join(cells)}</tr>')

        headers = "".join(f"<th>{esc(label)}</th>" for _, label in DISPLAY_FIELDS)

        html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>
:root {{
  --bg:#f4f6f8; --card:#ffffff; --text:#17202a; --muted:#667085;
  --line:#e4e7ec; --head:#101828; --accent:#2563eb;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
       font-family:Segoe UI,Arial,sans-serif; }}
.wrap {{ max-width:1500px; margin:0 auto; padding:28px; }}
.hero {{ background:linear-gradient(135deg,#111827,#26354a);
         color:white; border-radius:18px; padding:26px 30px;
         box-shadow:0 10px 30px rgba(16,24,40,.12); }}
.hero h1 {{ margin:0 0 6px; font-size:27px; }}
.hero p {{ margin:0; color:#d0d5dd; }}
.cards {{ display:grid; grid-template-columns:repeat(3,1fr);
          gap:14px; margin:18px 0; }}
.card {{ background:var(--card); border:1px solid var(--line);
         border-radius:14px; padding:17px; }}
.card .label {{ color:var(--muted); font-size:12px; text-transform:uppercase;
                letter-spacing:.06em; }}
.card .value {{ margin-top:6px; font-size:18px; font-weight:700;
                word-break:break-word; }}
.panel {{ background:var(--card); border:1px solid var(--line);
          border-radius:14px; overflow:hidden; }}
.table-wrap {{ overflow:auto; max-height:70vh; }}
table {{ border-collapse:separate; border-spacing:0; min-width:1300px;
         width:100%; font-size:13px; }}
th {{ position:sticky; top:0; z-index:2; background:#f2f4f7;
      color:#344054; text-align:left; padding:11px 12px;
      border-bottom:1px solid var(--line); white-space:nowrap; }}
td {{ padding:10px 12px; border-bottom:1px solid var(--line);
      vertical-align:top; max-width:380px; word-break:break-word; }}
tr:nth-child(even) td {{ background:#fafafa; }}
tr:hover td {{ background:#eef4ff; }}
.num {{ color:var(--muted); width:55px; }}
.footer {{ color:var(--muted); font-size:12px; padding:16px 2px; }}
@media(max-width:800px) {{
  .wrap {{ padding:14px; }} .cards {{ grid-template-columns:1fr; }}
  .hero h1 {{ font-size:22px; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <section class="hero">
    <h1>ZYNTRASEC // GREEN BLACK RED</h1>
    <p>Local search report • Generated {esc(generated)}</p>
  </section>

  <section class="cards">
    <div class="card"><div class="label">Results</div>
      <div class="value">{len(self.rows):,}</div></div>
    <div class="card"><div class="label">Search field</div>
      <div class="value">{esc(field_name)}</div></div>
    <div class="card"><div class="label">Match mode</div>
      <div class="value">{esc(self.mode_var.get())}</div></div>
    <div class="card"><div class="label">Search value</div>
      <div class="value">{esc(query_value)}</div></div>
    <div class="card"><div class="label">Region filter</div>
      <div class="value">{esc(region_value or "None")}</div></div>
    <div class="card"><div class="label">Source file</div>
      <div class="value">{esc(Path(self.file_var.get()).name)}</div></div>
  </section>

  <section class="panel">
    <div class="table-wrap">
      <table>
        <thead><tr><th>#</th>{headers}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
    </div>
  </section>

  <div class="footer">
    ZYNTRASEC // GREEN BLACK RED • Generated locally • {len(self.rows):,} result(s)
  </div>
</div>
</body>
</html>
"""
        html_path.write_text(html_doc, encoding="utf-8")

        messagebox.showinfo(
            "Export complete",
            f"Saved {len(self.rows):,} results locally to:\n\n"
            f"{jsonl}\n{csv_path}\n{html_path}"
        )


if __name__ == "__main__":
    App().mainloop()

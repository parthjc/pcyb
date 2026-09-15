#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZYNTRASEC Explorer

Simple GUI:
    1. Browse
    2. Discover Fields
    3. Select Field
    4. Enter Value
    5. SEARCH
    6. STOP / RESUME

Designed for very large JSON files containing an array of objects.
Works locally; source JSON is read-only.

Use only with data you own or are authorized to process.
"""

import json
import mmap
import os
from pathlib import Path
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


DEFAULT_FILE = r"E:\DATA LEAK\users_data.json"
SAMPLE_SIZE = 8 * 1024 * 1024
CHUNK_SIZE = 256 * 1024 * 1024
OVERLAP = 256 * 1024


class SimpleJSONSearch:
    def __init__(self, root):
        self.root = root
        self.root.title("ZYNTRASEC Explorer")
        self.root.geometry("1100x720")
        self.root.minsize(850, 560)

        self.file_var = tk.StringVar(value=DEFAULT_FILE)
        self.field_var = tk.StringVar()
        self.value_var = tk.StringVar()
        self.max_var = tk.IntVar(value=10)
        self.first_only_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.info_var = tk.StringVar(value="0 B / 0 B")
        self.speed_var = tk.StringVar(value="0 MB/s")
        self.match_var = tk.StringVar(value="Matches: 0")
        self.resume_var = tk.StringVar(value="Resume: none")

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        self.running = False
        self.paused = False

        self.file_size = 0
        self.position = 0
        self.started = 0

        self.fields = []
        self.results = []

        self.build_ui()
        try:
            self.app_data_dir()
        except Exception:
            pass

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):
        root = ttk.Frame(self.root, padding=10)
        root.pack(fill="both", expand=True)

        # File
        file_box = ttk.LabelFrame(
            root, text="JSON File", padding=8
        )
        file_box.pack(fill="x")

        ttk.Entry(
            file_box,
            textvariable=self.file_var
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 6)
        )

        ttk.Button(
            file_box,
            text="Browse",
            command=self.browse
        ).pack(side="left")

        # Search
        search_box = ttk.LabelFrame(
            root,
            text="Search",
            padding=8
        )
        search_box.pack(fill="x", pady=8)

        ttk.Label(
            search_box,
            text="Field:"
        ).grid(row=0, column=0, padx=4)

        self.field_combo = ttk.Combobox(
            search_box,
            textvariable=self.field_var,
            state="readonly",
            width=24
        )
        self.field_combo.grid(
            row=0, column=1, padx=4
        )

        ttk.Label(
            search_box,
            text="Value:"
        ).grid(row=0, column=2, padx=4)

        ttk.Entry(
            search_box,
            textvariable=self.value_var,
            width=32
        ).grid(
            row=0, column=3, padx=4
        )

        ttk.Label(
            search_box,
            text="Max:"
        ).grid(row=0, column=4, padx=4)

        ttk.Spinbox(
            search_box,
            from_=1,
            to=100000,
            textvariable=self.max_var,
            width=7
        ).grid(
            row=0, column=5, padx=4
        )

        ttk.Checkbutton(
            search_box,
            text="First match only",
            variable=self.first_only_var
        ).grid(
            row=0, column=6, padx=5
        )

        # Buttons
        buttons = ttk.Frame(root)
        buttons.pack(fill="x")

        self.discover_btn = ttk.Button(
            buttons,
            text="DISCOVER FIELDS",
            command=self.discover
        )
        self.discover_btn.pack(
            side="left",
            padx=3
        )

        ttk.Button(
            buttons,
            text="PREVIEW 100",
            command=self.preview_100
        ).pack(
            side="left",
            padx=3
        )

        self.search_btn = ttk.Button(
            buttons,
            text="SEARCH",
            command=self.start_search
        )
        self.search_btn.pack(
            side="left",
            padx=3
        )

        self.pause_btn = ttk.Button(
            buttons,
            text="PAUSE",
            command=self.pause_search,
            state="disabled"
        )
        self.pause_btn.pack(
            side="left",
            padx=3
        )

        self.resume_btn = ttk.Button(
            buttons,
            text="RESUME",
            command=self.resume_search
        )
        self.resume_btn.pack(
            side="left",
            padx=3
        )

        self.new_search_btn = ttk.Button(
            buttons,
            text="START FROM BEGINNING",
            command=self.start_from_beginning
        )
        self.new_search_btn.pack(
            side="left",
            padx=3
        )

        self.stop_btn = ttk.Button(
            buttons,
            text="STOP",
            command=self.stop_search,
            state="disabled"
        )
        self.stop_btn.pack(
            side="left",
            padx=3
        )

        ttk.Button(
            buttons,
            text="CLEAR",
            command=self.clear
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            buttons,
            text="EXPORT",
            command=self.export
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            buttons,
            text="EXIT",
            command=self.exit_app
        ).pack(
            side="left",
            padx=3
        )

        # Progress
        progress_box = ttk.LabelFrame(
            root,
            text="Progress",
            padding=8
        )
        progress_box.pack(
            fill="x",
            pady=8
        )

        ttk.Progressbar(
            progress_box,
            variable=self.progress_var,
            maximum=100
        ).pack(fill="x")

        info = ttk.Frame(progress_box)
        info.pack(fill="x", pady=5)

        ttk.Label(
            info,
            textvariable=self.status_var
        ).pack(side="left")

        ttk.Label(
            info,
            textvariable=self.match_var
        ).pack(side="right", padx=8)

        ttk.Label(
            info,
            textvariable=self.speed_var
        ).pack(side="right", padx=8)

        ttk.Label(
            info,
            textvariable=self.info_var
        ).pack(side="right", padx=8)

        ttk.Label(
            root,
            textvariable=self.resume_var
        ).pack(
            fill="x",
            pady=(0, 5)
        )

        # Results
        result_box = ttk.LabelFrame(
            root,
            text="Results",
            padding=5
        )
        result_box.pack(
            fill="both",
            expand=True
        )

        self.text = tk.Text(
            result_box,
            wrap="word",
            font=("Consolas", 10),
            undo=False
        )

        scroll = ttk.Scrollbar(
            result_box,
            orient="vertical",
            command=self.text.yview
        )

        self.text.configure(
            yscrollcommand=scroll.set
        )

        self.text.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll.pack(
            side="right",
            fill="y"
        )

    # ==========================================================
    # General
    # ==========================================================

    def path(self):
        return os.path.abspath(
            self.file_var.get()
        )

    def app_data_dir(self):
        # Always keep generated data in a top-level data folder on the same drive
        # as the selected JSON file. Example: E:\DATA LEAK\users_data.json -> E:\data
        drive_root = Path(self.path()).anchor
        if not drive_root:
            raise ValueError("Invalid JSON file path: drive drive not found")
        folder = Path(drive_root) / "data"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def state_path(self):
        return str(
            self.app_data_dir()
            / (Path(self.path()).name + ".resume.json")
        )

    def export_default_dir(self):
        folder = self.app_data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder)

    @staticmethod
    def hbytes(n):
        n = float(n)

        for unit in (
            "B", "KB", "MB", "GB", "TB"
        ):
            if n < 1024 or unit == "TB":
                return f"{n:.2f} {unit}"
            n /= 1024

    def browse(self):
        if self.running:
            return

        p = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if not p:
            return

        self.file_var.set(p)
        self.fields = []
        self.field_combo["values"] = ()
        self.field_var.set("")
        self.clear()
        self.load_resume_label()

    def clear(self):
        self.results = []
        self.text.delete("1.0", "end")
        self.match_var.set("Matches: 0")

    # ==========================================================
    # Field discovery
    # ==========================================================

    def discover(self):
        if self.running:
            return

        path = self.path()

        if not os.path.isfile(path):
            messagebox.showerror(
                "File",
                "JSON file not found."
            )
            return

        self.discover_btn.config(
            state="disabled"
        )

        self.status_var.set(
            "Discovering fields..."
        )

        threading.Thread(
            target=self._discover_worker,
            daemon=True
        ).start()

    def _discover_worker(self):
        try:
            with open(
                self.path(),
                "rb"
            ) as f:
                data = f.read(
                    SAMPLE_SIZE
                )

            records = self.parse_sample(
                data
            )

            fields = set()

            for record in records:
                if isinstance(
                    record,
                    dict
                ):
                    fields.update(
                        str(k)
                        for k in record.keys()
                    )

            fields = sorted(
                fields
            )

            self.root.after(
                0,
                self.show_fields,
                fields,
                len(records)
            )

        except Exception as e:
            self.root.after(
                0,
                self.show_error,
                "Discovery Error",
                str(e)
            )

    @staticmethod
    def parse_sample(data):
        text = data.decode(
            "utf-8",
            errors="ignore"
        )

        decoder = json.JSONDecoder()

        i = 0
        n = len(text)

        while (
            i < n
            and text[i].isspace()
        ):
            i += 1

        if (
            i < n
            and text[i] == "["
        ):
            i += 1

        records = []

        while (
            i < n
            and len(records) < 500
        ):
            while (
                i < n
                and text[i].isspace()
            ):
                i += 1

            if (
                i < n
                and text[i] == ","
            ):
                i += 1
                continue

            if (
                i >= n
                or text[i] == "]"
            ):
                break

            if text[i] != "{":
                i += 1
                continue

            try:
                obj, used = decoder.raw_decode(
                    text[i:]
                )
            except json.JSONDecodeError:
                break

            if isinstance(obj, dict):
                records.append(obj)

            i += used

        return records

    def show_fields(
        self,
        fields,
        record_count
    ):
        self.discover_btn.config(
            state="normal"
        )

        self.fields = fields
        self.field_combo["values"] = fields

        if fields:
            preferred = (
                "mobile"
                if "mobile" in fields
                else (
                    "phone"
                    if "phone" in fields
                    else (
                        "email"
                        if "email" in fields
                        else fields[0]
                    )
                )
            )

            self.field_var.set(
                preferred
            )

            self.status_var.set(
                f"Found {len(fields)} fields "
                f"from {record_count} records."
            )
        else:
            self.status_var.set(
                "No fields found."
            )

    # ==========================================================
    # Preview 100
    # ==========================================================

    def preview_100(self):
        if self.running:
            return

        path = self.path()
        if not os.path.isfile(path):
            messagebox.showerror(
                "File",
                "JSON file not found."
            )
            return

        self.discover_btn.config(state="disabled")
        self.search_btn.config(state="disabled")
        self.status_var.set("Loading first 100 records...")

        threading.Thread(
            target=self._preview_worker,
            daemon=True
        ).start()

    def _preview_worker(self):
        try:
            with open(
                self.path(),
                "rb"
            ) as f:
                data = f.read(SAMPLE_SIZE)

            records = self.parse_sample(data)[:100]

            self.root.after(
                0,
                self._show_preview,
                records
            )
        except Exception as e:
            self.root.after(
                0,
                self.show_error,
                "Preview Error",
                str(e)
            )

    def _show_preview(self, records):
        self.results = records
        self.match_var.set(
            f"Matches: {len(records)}"
        )
        self.render_results()

        # Save preview automatically inside the separate data folder.
        try:
            preview_path = (
                self.app_data_dir()
                / "preview_100.jsonl"
            )
            with open(
                preview_path,
                "w",
                encoding="utf-8"
            ) as f:
                for record in records:
                    f.write(
                        json.dumps(
                            record,
                            ensure_ascii=False
                        ) + "\n"
                    )
            self.status_var.set(
                f"Preview loaded: {len(records)} record(s) | "
                f"Saved in data\\preview_100.jsonl"
            )
        except Exception as e:
            self.status_var.set(
                f"Preview loaded: {len(records)} record(s) | "
                f"Preview save error: {e}"
            )

        self.discover_btn.config(state="normal")
        self.search_btn.config(state="normal")

    # ==========================================================
    # Search
    # ==========================================================

    def make_patterns(self):
        """Build literal JSON byte patterns for very fast mmap.find() searching."""
        field = self.field_var.get().strip()
        value = self.value_var.get()

        # JSON-escape without the surrounding quotes for the field name.
        field_escaped = json.dumps(
            field, ensure_ascii=False, separators=(",", ":")
        )[1:-1].encode("utf-8")
        value_json = json.dumps(
            value, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")

        prefix = b'"' + field_escaped + b'":'
        return (
            prefix + value_json,
            prefix + b" " + value_json,
        )

    def start_search(self):
        if self.running:
            return

        path = self.path()
        field = self.field_var.get().strip()
        value = self.value_var.get()

        if not os.path.isfile(path):
            messagebox.showerror(
                "File",
                "JSON file not found."
            )
            return

        if not field:
            messagebox.showwarning(
                "Search",
                "Click DISCOVER FIELDS first."
            )
            return

        if value == "":
            messagebox.showwarning(
                "Search",
                "Enter a value."
            )
            return

        try:
            self.max_results = max(
                1,
                int(self.max_var.get())
            )
        except Exception:
            self.max_results = 10

        self.clear()

        self.file_size = os.path.getsize(
            path
        )

        self.position = 0
        self.started = time.time()

        self.stop_event.clear()
        self.pause_event.clear()

        self.running = True
        self.paused = False

        self.set_running_buttons()

        self.status_var.set(
            "Searching..."
        )
        self.resume_var.set(
            "Resume: active"
        )

        threading.Thread(
            target=self.search_worker,
            args=(0,),
            daemon=True
        ).start()

    def start_from_beginning(self):
        """Clear old search state and begin again from byte 0."""
        if self.running:
            messagebox.showinfo(
                "Search running",
                "Stop or pause the current search first."
            )
            return

        try:
            self.save_resume(remove=True)
        except Exception:
            pass

        self.position = 0
        self.file_size = 0
        self.results = []
        self.text.delete("1.0", "end")
        self.match_var.set("Matches: 0")
        self.progress_var.set(0)
        self.info_var.set("0 B / 0 B")
        self.speed_var.set("0 B/s")
        self.resume_var.set("Resume: none")
        self.status_var.set("Starting from beginning...")

        self.start_search()

    def resume_search(self):
        if self.running:
            if self.paused:
                self.pause_event.clear()
                self.paused = False
                self.status_var.set(
                    "Resuming..."
                )
            return

        state = self.load_resume()

        if not state:
            messagebox.showinfo(
                "Resume",
                "No saved resume point."
            )
            return

        self.field_var.set(
            state.get(
                "field",
                ""
            )
        )
        self.value_var.set(
            state.get(
                "value",
                ""
            )
        )
        self.max_var.set(
            state.get(
                "max_results",
                10
            )
        )
        self.first_only_var.set(
            state.get(
                "first_only",
                False
            )
        )

        try:
            self.file_size = os.path.getsize(
                self.path()
            )
            saved = int(
                state.get(
                    "position",
                    0
                )
            )
        except Exception as e:
            messagebox.showerror(
                "Resume Error",
                str(e)
            )
            return

        self.position = max(
            0,
            min(
                saved,
                self.file_size
            )
        )

        # Go slightly backward to protect a field/value
        # crossing the old chunk boundary.
        start = max(
            0,
            self.position - OVERLAP
        )

        # IMPORTANT: keep results already found before PAUSE.
        # Do not clear the Results box here; RESUME should append new matches.
        self.stop_event.clear()
        self.pause_event.clear()

        self.running = True
        self.paused = False
        self.started = time.time()

        self.set_running_buttons()

        self.status_var.set(
            "Resuming from "
            + self.hbytes(self.position)
        )

        threading.Thread(
            target=self.search_worker,
            args=(start,),
            daemon=True
        ).start()

    def pause_search(self):
        if self.running:
            self.pause_event.set()
            self.status_var.set(
                "Pause requested..."
            )

    def stop_search(self):
        if self.running:
            self.stop_event.set()
            self.status_var.set(
                "Stop requested..."
            )

    def set_running_buttons(self):
        self.search_btn.config(
            state="disabled"
        )
        self.new_search_btn.config(
            state="disabled"
        )
        self.discover_btn.config(
            state="disabled"
        )
        self.pause_btn.config(
            state="normal"
        )
        self.stop_btn.config(
            state="normal"
        )

    def set_idle_buttons(self):
        self.search_btn.config(
            state="normal"
        )
        self.new_search_btn.config(
            state="normal"
        )
        self.discover_btn.config(
            state="normal"
        )
        self.pause_btn.config(
            state="disabled"
        )
        self.stop_btn.config(
            state="disabled"
        )

    # ==========================================================
    # Search worker
    # ==========================================================

    def search_worker(self, start):
        """High-speed literal search. No chunk slicing; mmap.find() searches the mapped file directly."""
        try:
            patterns = self.make_patterns()
        except Exception as e:
            self.root.after(0, self.search_error, str(e))
            return

        try:
            max_results = max(1, int(self.max_var.get()))
        except Exception:
            max_results = 10

        first_only = bool(self.first_only_var.get())
        # Preserve results already shown on screen when RESUME is used.
        # SEARCH / START FROM BEGINNING already clear self.results beforehand.
        results = list(self.results)
        existing_keys = set()
        for item in results:
            try:
                existing_keys.add(json.dumps(item, sort_keys=True, ensure_ascii=False))
            except Exception:
                pass
        path = self.path()

        try:
            with open(path, "rb") as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                scan = max(0, int(start))
                last_checkpoint = scan
                last_ui = scan
                pattern_len = max(len(p) for p in patterns)

                while scan < self.file_size:
                    if self.stop_event.is_set():
                        self.position = scan
                        self.save_resume()
                        mm.close()
                        self.root.after(0, self.finish, "stopped", results)
                        return

                    if self.pause_event.is_set():
                        self.position = scan
                        self.save_resume()
                        mm.close()
                        self.root.after(0, self.finish, "paused", results)
                        return

                    end = min(self.file_size, scan + CHUNK_SIZE)
                    search_end = min(self.file_size, end + pattern_len - 1)

                    # Search each literal JSON layout directly in the mmap.
                    # mmap.find() is implemented in native code and avoids creating
                    # a 256 MB Python bytes object for every chunk.
                    best = None
                    best_pat = None
                    for pat in patterns:
                        pos = mm.find(pat, scan, search_end)
                        if pos != -1 and (best is None or pos < best):
                            best = pos
                            best_pat = pat

                    while best is not None and best < end:
                        absolute = best
                        record = self.extract_record(mm, absolute)

                        if record is not None:
                            try:
                                record_key = json.dumps(record, sort_keys=True, ensure_ascii=False)
                            except Exception:
                                record_key = None

                            # Avoid duplicates caused by the overlap window on RESUME.
                            if record_key is None or record_key not in existing_keys:
                                results.append(record)
                                if record_key is not None:
                                    existing_keys.add(record_key)
                                # Show every match immediately in the GUI; no PAUSE needed.
                                self.root.after(0, self.add_live_result, record, len(results))

                            if first_only or len(results) >= max_results:
                                self.position = absolute + len(best_pat)
                                self.save_resume(remove=True)
                                mm.close()
                                self.root.after(0, self.finish, "limit", results)
                                return

                        # Find the next match after this one across all patterns.
                        next_best = None
                        next_pat = None
                        next_from = absolute + max(1, len(best_pat))
                        for pat in patterns:
                            pos = mm.find(pat, next_from, search_end)
                            if pos != -1 and (next_best is None or pos < next_best):
                                next_best = pos
                                next_pat = pat
                        best, best_pat = next_best, next_pat

                    scan = end
                    self.position = scan

                    if scan - last_checkpoint >= (64 * 1024 * 1024):
                        last_checkpoint = scan
                        self.save_resume()

                    if scan - last_ui >= (128 * 1024 * 1024):
                        last_ui = scan
                        self.root.after(0, self.update_progress)

                mm.close()

            self.position = self.file_size
            self.save_resume(remove=True)
            self.root.after(0, self.update_progress)
            self.root.after(0, self.finish, "completed", results)

        except Exception as e:
            self.root.after(0, self.search_error, str(e))

    def extract_record(
        self,
        mm,
        absolute_position
    ):
        """
        Extract the JSON object containing the matched field.
        Uses a bounded backward search for an object start and a
        forward brace/string-aware scan.
        """
        window = 1024 * 1024

        start = max(
            0,
            absolute_position - window
        )

        # Find likely top-level object start.
        marker = mm.rfind(
            b'{"_id"',
            start,
            absolute_position + 1
        )

        if marker < 0:
            marker = mm.rfind(
                b"{",
                start,
                absolute_position + 1
            )

        if marker < 0:
            return None

        end_limit = min(
            self.file_size,
            marker + (4 * 1024 * 1024)
        )

        depth = 0
        in_string = False
        escaped = False

        i = marker

        while i < end_limit:
            b = mm[i]

            if in_string:
                if escaped:
                    escaped = False
                elif b == 0x5C:  # \
                    escaped = True
                elif b == 0x22:  # "
                    in_string = False

            else:
                if b == 0x22:
                    in_string = True

                elif b == 0x7B:
                    depth += 1

                elif b == 0x7D:
                    depth -= 1

                    if depth == 0:
                        raw = mm[
                            marker:i + 1
                        ]

                        try:
                            obj = json.loads(
                                raw
                            )

                            # Safety: make sure the matched value belongs
                            # to the selected field.
                            if isinstance(
                                obj,
                                dict
                            ):
                                return obj

                        except Exception:
                            return None

            i += 1

        return None

    # ==========================================================
    # Resume
    # ==========================================================

    def save_resume(
        self,
        remove=False
    ):
        path = self.state_path()

        if remove:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
            except Exception:
                pass

            self.root.after(
                0,
                self.resume_var.set,
                "Resume: none"
            )
            return

        try:
            st = os.stat(
                self.path()
            )

            state = {
                "file": self.path(),
                "size": st.st_size,
                "mtime_ns": st.st_mtime_ns,
                "position": int(
                    self.position
                ),
                "field": self.field_var.get(),
                "value": self.value_var.get(),
                "max_results": int(
                    self.max_var.get()
                ),
                "first_only": bool(
                    self.first_only_var.get()
                )
            }

            tmp = path + ".tmp"

            with open(
                tmp,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    state,
                    f,
                    indent=2
                )

            os.replace(
                tmp,
                path
            )

            self.root.after(
                0,
                self.resume_var.set,
                "Resume checkpoint: "
                + self.hbytes(
                    self.position
                )
            )

        except Exception:
            pass

    def load_resume(self):
        try:
            with open(
                self.state_path(),
                "r",
                encoding="utf-8"
            ) as f:
                state = json.load(f)

            st = os.stat(
                self.path()
            )

            if state.get(
                "file"
            ) != self.path():
                return None

            if int(
                state.get(
                    "size",
                    -1
                )
            ) != st.st_size:
                return None

            if int(
                state.get(
                    "mtime_ns",
                    -1
                )
            ) != st.st_mtime_ns:
                return None

            return state

        except Exception:
            return None

    def load_resume_label(self):
        state = self.load_resume()

        if state:
            self.resume_var.set(
                "Resume available at "
                + self.hbytes(
                    int(
                        state.get(
                            "position",
                            0
                        )
                    )
                )
            )
        else:
            self.resume_var.set(
                "Resume: none"
            )

    # ==========================================================
    # Progress / results
    # ==========================================================

    def update_progress(self):
        if self.file_size <= 0:
            return

        pct = (
            self.position
            / self.file_size
            * 100
        )

        elapsed = max(
            0.001,
            time.time() - self.started
        )

        rate = (
            self.position
            / elapsed
        )

        self.progress_var.set(
            min(
                100,
                pct
            )
        )

        self.info_var.set(
            f"{self.hbytes(self.position)} / "
            f"{self.hbytes(self.file_size)}"
        )

        self.speed_var.set(
            f"{self.hbytes(rate)}/s"
        )

    def search_error(self, message):
        self.running = False
        self.paused = False
        self.set_idle_buttons()
        self.status_var.set("Search error")
        try:
            messagebox.showerror("Search Error", message)
        except Exception:
            pass

    def finish(
        self,
        reason,
        results
    ):
        self.running = False

        if reason == "completed":
            self.status_var.set(
                f"Completed — "
                f"{len(results)} result(s)"
            )
            self.resume_var.set(
                "Resume: none"
            )

        elif reason == "limit":
            self.status_var.set(
                f"Result limit reached — "
                f"{len(results)} result(s)"
            )
            self.resume_var.set(
                "Search stopped after result limit."
            )

        elif reason == "paused":
            self.paused = True
            self.status_var.set(
                f"Paused at "
                f"{self.hbytes(self.position)}"
            )

        elif reason == "stopped":
            self.status_var.set(
                f"Stopped at "
                f"{self.hbytes(self.position)}"
            )

        self.results = results
        self.match_var.set(
            f"Matches: {len(results)}"
        )

        self.render_results()

        # Automatically keep a copy in the separate data folder.
        try:
            result_path = (
                self.app_data_dir()
                / "last_search_results.jsonl"
            )
            with open(
                result_path,
                "w",
                encoding="utf-8"
            ) as f:
                for record in results:
                    f.write(
                        json.dumps(
                            record,
                            ensure_ascii=False
                        ) + "\n"
                    )
            self.status_var.set(
                self.status_var.get()
                + " | Saved: data\\last_search_results.jsonl"
            )
        except Exception:
            pass

        self.set_idle_buttons()

    def add_live_result(self, record, number=None):
        """Append a newly found result to the GUI immediately while search continues."""
        try:
            # The worker already deduplicates, but keep a UI-side guard for safety.
            key = json.dumps(record, sort_keys=True, ensure_ascii=False)
            for existing in self.results:
                try:
                    if json.dumps(existing, sort_keys=True, ensure_ascii=False) == key:
                        self.match_var.set(f"Matches: {len(self.results)}")
                        return
                except Exception:
                    pass
        except Exception:
            pass

        self.results.append(record)
        n = len(self.results)
        self.match_var.set(f"Matches: {n}")

        labels = {
            "email": "📩 Email",
            "mobile": "📞 Telephone",
            "phone": "📞 Telephone",
            "address": "🏘️ Address",
            "name": "👤 Full Name",
            "fname": "👨 Father Name",
            "circle": "🗺️ Region",
            "id": "🃏 Document ID",
            "_id": "🔑 Internal ID"
        }

        self.text.insert(
            "end",
            "\n" + "=" * 70 + "\n"
            f"RESULT #{n}\n"
            + "=" * 70 + "\n"
        )

        if isinstance(record, dict):
            for key, value in record.items():
                label = labels.get(str(key).lower(), str(key))
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                self.text.insert("end", f"{label}: {value}\n")
        else:
            self.text.insert("end", str(record) + "\n")

        # Always keep the newest match visible.
        self.text.see("end")

    def render_results(self):
        self.text.delete(
            "1.0",
            "end"
        )

        labels = {
            "email": "📩 Email",
            "mobile": "📞 Telephone",
            "phone": "📞 Telephone",
            "address": "🏘️ Address",
            "name": "👤 Full Name",
            "fname": "👨 Father Name",
            "circle": "🗺️ Region",
            "id": "🃏 Document ID",
            "_id": "🔑 Internal ID"
        }

        for n, record in enumerate(
            self.results,
            1
        ):
            self.text.insert(
                "end",
                "\n"
                + "=" * 70
                + "\n"
                f"RESULT #{n}\n"
                + "=" * 70
                + "\n"
            )

            if not isinstance(
                record,
                dict
            ):
                self.text.insert(
                    "end",
                    str(record)
                    + "\n"
                )
                continue

            for key, value in record.items():
                label = labels.get(
                    str(key).lower(),
                    str(key)
                )

                if isinstance(
                    value,
                    (dict, list)
                ):
                    value = json.dumps(
                        value,
                        ensure_ascii=False
                    )

                self.text.insert(
                    "end",
                    f"{label}: {value}\n"
                )

    # ==========================================================
    # Exit / Export
    # ==========================================================

    def exit_app(self):
        if self.running:
            ok = messagebox.askyesno(
                "Exit",
                "A search is running. Stop it and exit?"
            )
            if not ok:
                return

            self.stop_event.set()

            # Give the worker a short chance to save its checkpoint.
            self.root.after(150, self._force_exit)
            return

        self.root.destroy()

    def _force_exit(self):
        self.root.destroy()

    def _flatten_record(self, record):
        """Flatten nested JSON values into readable text for CSV/Excel/HTML."""
        out = {}
        if not isinstance(record, dict):
            return {"value": record}

        for key, value in record.items():
            if isinstance(value, (dict, list)):
                out[str(key)] = json.dumps(
                    value,
                    ensure_ascii=False,
                    separators=(",", ":")
                )
            elif value is None:
                out[str(key)] = ""
            else:
                out[str(key)] = value
        return out

    def _export_json(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                self.results,
                f,
                ensure_ascii=False,
                indent=2
            )

    def _export_jsonl(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for record in self.results:
                f.write(
                    json.dumps(
                        record,
                        ensure_ascii=False
                    ) + "\n"
                )

    def _export_csv(self, path):
        import csv

        rows = [self._flatten_record(r) for r in self.results]
        headers = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    headers.append(key)

        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=headers,
                extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(rows)

    def _export_tsv(self, path):
        import csv

        rows = [self._flatten_record(r) for r in self.results]
        headers = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    headers.append(key)

        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=headers,
                extrasaction="ignore",
                delimiter="\t"
            )
            writer.writeheader()
            writer.writerows(rows)

    def _export_txt(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for i, record in enumerate(self.results, 1):
                f.write("=" * 78 + "\n")
                f.write(f"RESULT #{i}\n")
                f.write("=" * 78 + "\n")
                if isinstance(record, dict):
                    for key, value in record.items():
                        if isinstance(value, (dict, list)):
                            value = json.dumps(
                                value,
                                ensure_ascii=False,
                                indent=2
                            )
                        f.write(f"{key}: {value}\n")
                else:
                    f.write(f"value: {record}\n")
                f.write("\n")

    def _export_html(self, path):
        from html import escape

        rows = [self._flatten_record(r) for r in self.results]
        headers = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    headers.append(key)

        with open(path, "w", encoding="utf-8") as f:
            f.write("<!doctype html>\n<html><head><meta charset='utf-8'>\n")
            f.write("<title>JSON Search Results</title>\n")
            f.write("<meta name='viewport' content='width=device-width,initial-scale=1'>\n")
            f.write("<style>")
            f.write("body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#f5f7fa;color:#202124}")
            f.write("h1{font-size:22px} .meta{margin-bottom:14px;color:#5f6368}")
            f.write("table{border-collapse:collapse;width:100%;background:#fff;box-shadow:0 1px 5px rgba(0,0,0,.12)}")
            f.write("th,td{border:1px solid #dfe3e8;padding:8px 10px;text-align:left;vertical-align:top;white-space:pre-wrap;word-break:break-word}")
            f.write("th{position:sticky;top:0;background:#eef1f4;font-weight:600}")
            f.write("</style></head><body>")
            f.write("<h1>JSON Search Results</h1>")
            f.write(f"<div class='meta'>Total matches: {len(rows)}</div>")
            f.write("<table><thead><tr>")
            for h in headers:
                f.write(f"<th>{escape(str(h))}</th>")
            f.write("</tr></thead><tbody>")
            for row in rows:
                f.write("<tr>")
                for h in headers:
                    f.write(f"<td>{escape(str(row.get(h, '')))}</td>")
                f.write("</tr>")
            f.write("</tbody></table></body></html>")

    def _export_xlsx(self, path):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
        except ImportError as e:
            raise RuntimeError(
                "Excel export needs openpyxl. Install it with: pip install openpyxl"
            ) from e

        rows = [self._flatten_record(r) for r in self.results]
        headers = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    headers.append(key)

        wb = Workbook()
        ws = wb.active
        ws.title = "Search Results"

        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.fill = PatternFill(fill_type="solid", fgColor="D9E2F3")

        for row in rows:
            ws.append([row.get(h, "") for h in headers])

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        ws.row_dimensions[1].height = 22

        # Useful widths without making very long fields enormous.
        for idx, h in enumerate(headers, 1):
            max_len = len(str(h))
            for row in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
                value = row[0].value
                if value is not None:
                    max_len = max(max_len, min(len(str(value)), 60))
            ws.column_dimensions[get_column_letter(idx)].width = min(max(max_len + 2, 12), 62)

        wb.save(path)

    def export(self):
        if not self.results:
            messagebox.showinfo(
                "Export",
                "No results to export."
            )
            return

        p = filedialog.asksaveasfilename(
            title="Export Search Results",
            initialdir=self.export_default_dir(),
            initialfile="search_results.xlsx",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel Workbook - XLSX (recommended)", "*.xlsx"),
                ("CSV - Excel / Google Sheets", "*.csv"),
                ("HTML - Browser Table", "*.html"),
                ("TXT - Readable Report", "*.txt"),
                ("JSON - Pretty / Structured", "*.json"),
                ("JSONL - One Record Per Line", "*.jsonl"),
                ("TSV - Tab Separated", "*.tsv")
            ]
        )

        if not p:
            return

        try:
            lower = p.lower()

            if lower.endswith(".xlsx"):
                self._export_xlsx(p)
            elif lower.endswith(".csv"):
                self._export_csv(p)
            elif lower.endswith(".html"):
                self._export_html(p)
            elif lower.endswith(".txt"):
                self._export_txt(p)
            elif lower.endswith(".jsonl"):
                self._export_jsonl(p)
            elif lower.endswith(".tsv"):
                self._export_tsv(p)
            elif lower.endswith(".json"):
                self._export_json(p)
            else:
                raise ValueError("Unsupported export format.")

            messagebox.showinfo(
                "Export Complete",
                f"Saved {len(self.results)} result(s) successfully.\n\n{p}"
            )

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                str(e)
            )

    def show_error(
        self,
        title,
        message
    ):
        self.running = False
        self.set_idle_buttons()

        messagebox.showerror(
            title,
            message
        )


def main():
    root = tk.Tk()
    app = SimpleJSONSearch(root)

    # Same behavior as the EXIT button when clicking the window X.
    root.protocol("WM_DELETE_WINDOW", app.exit_app)

    root.mainloop()


if __name__ == "__main__":
    main()

import os
import json
import time
import mmap
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText


# ============================================================
# SETTINGS
# ============================================================

READ_CHUNK = 16 * 1024 * 1024       # 16 MB
OVERLAP = 4096                       # boundary protection
DEFAULT_FILE = r"E:\LEAK DATA\users_data\users_data.json"


# ============================================================
# OBJECT EXTRACTION
# ============================================================

def extract_json_object(path, position):
    """
    Find the outer JSON object containing the matched field.
    Designed for JSON like:

    [
      {"_id": {...}, "mobile": "...", ...},
      {"_id": {...}, "mobile": "...", ...}
    ]
    """

    WINDOW = 1024 * 1024  # 1 MB around match

    file_size = os.path.getsize(path)

    start_read = max(0, position - WINDOW)
    end_read = min(file_size, position + WINDOW)

    with open(path, "rb") as f:
        f.seek(start_read)
        data = f.read(end_read - start_read)

    relative_pos = position - start_read

    # Prefer the outer record pattern from the user's dataset
    object_start = data.rfind(b'{"_id"', 0, relative_pos + 1)

    if object_start == -1:
        object_start = data.rfind(b"{", 0, relative_pos + 1)

    if object_start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(object_start, len(data)):

        c = data[i]

        if in_string:

            if escape:
                escape = False

            elif c == 92:  # backslash
                escape = True

            elif c == 34:  # quote
                in_string = False

            continue

        if c == 34:
            in_string = True

        elif c == 123:  # {
            depth += 1

        elif c == 125:  # }
            depth -= 1

            if depth == 0:

                raw = data[
                    object_start:i + 1
                ]

                try:
                    return json.loads(
                        raw.decode(
                            "utf-8",
                            errors="replace"
                        )
                    )

                except Exception:
                    return {
                        "_raw": raw.decode(
                            "utf-8",
                            errors="replace"
                        )
                    }

    return None


# ============================================================
# FAST SEARCH
# ============================================================

def fast_byte_search(
    path,
    field,
    value,
    limit,
    stop_after_first,
    stop_event,
    callback
):

    patterns = [
        f'"{field}":"{value}"'.encode("utf-8"),
        f'"{field}": "{value}"'.encode("utf-8"),
    ]

    file_size = os.path.getsize(path)

    found_positions = []
    seen = set()

    start_time = time.time()
    scanned = 0

    previous = b""

    with open(path, "rb", buffering=0) as f:

        while not stop_event.is_set():

            chunk = f.read(READ_CHUNK)

            if not chunk:
                break

            data = previous + chunk

            base_offset = scanned - len(previous)

            # ------------------------------------------------
            # SEARCH
            # ------------------------------------------------

            for pattern in patterns:

                pos = data.find(pattern)

                while pos != -1:

                    absolute_position = (
                        base_offset + pos
                    )

                    if absolute_position not in seen:

                        seen.add(
                            absolute_position
                        )

                        found_positions.append(
                            absolute_position
                        )

                        # IMPORTANT:
                        # Stop immediately after first result
                        if stop_after_first:
                            return found_positions

                        if len(found_positions) >= limit:
                            return found_positions

                    pos = data.find(
                        pattern,
                        pos + 1
                    )

            # ------------------------------------------------
            # PROGRESS
            # ------------------------------------------------

            scanned += len(chunk)

            elapsed = max(
                time.time() - start_time,
                0.001
            )

            speed_mb = (
                scanned / 1024 / 1024
            ) / elapsed

            percent = (
                scanned / file_size
            ) * 100

            if speed_mb > 0:

                remaining_mb = (
                    file_size - scanned
                ) / 1024 / 1024

                eta_seconds = (
                    remaining_mb / speed_mb
                )

            else:
                eta_seconds = 0

            callback(
                percent,
                speed_mb,
                eta_seconds,
                len(found_positions)
            )

            # ------------------------------------------------
            # KEEP OVERLAP
            # ------------------------------------------------

            max_pattern = max(
                len(p)
                for p in patterns
            )

            keep = max(
                OVERLAP,
                max_pattern + 100
            )

            previous = data[-keep:]

    return found_positions


# ============================================================
# PREVIEW FIRST 100 RECORDS
# ============================================================

def preview_first_records(
    path,
    max_records=100
):

    records = []

    buffer = b""

    with open(
        path,
        "rb",
        buffering=1024 * 1024
    ) as f:

        while len(records) < max_records:

            chunk = f.read(
                4 * 1024 * 1024
            )

            if not chunk:
                break

            buffer += chunk

            # Find JSON objects
            depth = 0
            in_string = False
            escape = False
            start = None

            i = 0

            while i < len(buffer):

                c = buffer[i]

                if in_string:

                    if escape:
                        escape = False

                    elif c == 92:
                        escape = True

                    elif c == 34:
                        in_string = False

                else:

                    if c == 34:
                        in_string = True

                    elif c == 123:

                        if depth == 0:
                            start = i

                        depth += 1

                    elif c == 125:

                        depth -= 1

                        if depth == 0 and start is not None:

                            raw = buffer[
                                start:i + 1
                            ]

                            try:

                                obj = json.loads(
                                    raw.decode(
                                        "utf-8",
                                        errors="replace"
                                    )
                                )

                                records.append(obj)

                            except Exception:
                                pass

                            start = None

                            if len(records) >= max_records:
                                break

                i += 1

            # Remove processed part
            if depth == 0:

                last_close = buffer.rfind(
                    b"}"
                )

                if last_close != -1:

                    buffer = buffer[
                        last_close + 1:
                    ]

    return records


# ============================================================
# FORMAT RESULT
# ============================================================

def format_result(obj):

    try:
        return json.dumps(
            obj,
            indent=2,
            ensure_ascii=False
        )

    except Exception:
        return str(obj)


# ============================================================
# MAIN GUI
# ============================================================

class FastJSONSearchApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Ultra Fast JSON Search"
        )

        self.root.geometry(
            "1050x720"
        )

        self.stop_event = threading.Event()

        self.results = []

        self.search_thread = None

        self.build_ui()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):

        main = ttk.Frame(
            self.root,
            padding=12
        )

        main.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # FILE
        # ====================================================

        ttk.Label(
            main,
            text="JSON File:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=5
        )

        self.file_var = tk.StringVar(
            value=DEFAULT_FILE
        )

        self.file_entry = ttk.Entry(
            main,
            textvariable=self.file_var
        )

        self.file_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5
        )

        ttk.Button(
            main,
            text="Browse",
            command=self.browse_file
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        # ====================================================
        # FIELD
        # ====================================================

        ttk.Label(
            main,
            text="Field:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=5
        )

        self.field_var = tk.StringVar(
            value="mobile"
        )

        self.field_entry = ttk.Entry(
            main,
            textvariable=self.field_var
        )

        self.field_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=5
        )

        # ====================================================
        # VALUE
        # ====================================================

        ttk.Label(
            main,
            text="Exact Value:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=5
        )

        self.value_var = tk.StringVar()

        self.value_entry = ttk.Entry(
            main,
            textvariable=self.value_var
        )

        self.value_entry.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=5
        )

        # ====================================================
        # MAX RESULTS
        # ====================================================

        ttk.Label(
            main,
            text="Max Results:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=5
        )

        self.limit_var = tk.StringVar(
            value="10"
        )

        ttk.Entry(
            main,
            textvariable=self.limit_var,
            width=10
        ).grid(
            row=3,
            column=1,
            sticky="w",
            padx=5
        )

        # ====================================================
        # FIRST MATCH
        # ====================================================

        self.first_only_var = tk.BooleanVar(
            value=True
        )

        ttk.Checkbutton(
            main,
            text="STOP after first match",
            variable=self.first_only_var
        ).grid(
            row=4,
            column=1,
            sticky="w",
            pady=5
        )

        # ====================================================
        # BUTTONS
        # ====================================================

        button_frame = ttk.Frame(
            main
        )

        button_frame.grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=10
        )

        self.search_btn = ttk.Button(
            button_frame,
            text="⚡ FAST SEARCH",
            command=self.start_search
        )

        self.search_btn.pack(
            side="left",
            padx=5
        )

        self.preview_btn = ttk.Button(
            button_frame,
            text="👁 PREVIEW 100",
            command=self.preview
        )

        self.preview_btn.pack(
            side="left",
            padx=5
        )

        self.stop_btn = ttk.Button(
            button_frame,
            text="⛔ STOP",
            command=self.stop_search
        )

        self.stop_btn.pack(
            side="left",
            padx=5
        )

        self.export_btn = ttk.Button(
            button_frame,
            text="💾 EXPORT JSONL",
            command=self.export_results
        )

        self.export_btn.pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="CLEAR",
            command=self.clear_output
        ).pack(
            side="left",
            padx=5
        )

        # ====================================================
        # PROGRESS
        # ====================================================

        self.progress = ttk.Progressbar(
            main,
            orient="horizontal",
            mode="determinate"
        )

        self.progress.grid(
            row=6,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=5
        )

        self.status_var = tk.StringVar(
            value="Ready"
        )

        ttk.Label(
            main,
            textvariable=self.status_var
        ).grid(
            row=7,
            column=0,
            columnspan=3,
            sticky="w",
            pady=5
        )

        # ====================================================
        # OUTPUT
        # ====================================================

        self.output = ScrolledText(
            main,
            wrap="none",
            font=("Consolas", 10)
        )

        self.output.grid(
            row=8,
            column=0,
            columnspan=3,
            sticky="nsew",
            pady=5
        )

        # ====================================================
        # EXAMPLES
        # ====================================================

        ttk.Label(
            main,
            text=(
                "Examples:  mobile | value     "
                "email | value     "
                "id | value     "
                "name | value"
            )
        ).grid(
            row=9,
            column=0,
            columnspan=3,
            sticky="w",
            pady=5
        )

        main.columnconfigure(
            1,
            weight=1
        )

        main.rowconfigure(
            8,
            weight=1
        )

    # --------------------------------------------------------
    # BROWSE
    # --------------------------------------------------------

    def browse_file(self):

        path = filedialog.askopenfilename(
            title="Select JSON File",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if path:

            self.file_var.set(path)

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    def start_search(self):

        path = self.file_var.get().strip()
        field = self.field_var.get().strip()
        value = self.value_var.get().strip()

        if not path:

            messagebox.showerror(
                "Error",
                "Please select JSON file."
            )

            return

        if not os.path.isfile(path):

            messagebox.showerror(
                "Error",
                "File not found."
            )

            return

        if not field:

            messagebox.showerror(
                "Error",
                "Enter field name."
            )

            return

        if not value:

            messagebox.showerror(
                "Error",
                "Enter exact value."
            )

            return

        try:

            limit = int(
                self.limit_var.get()
            )

            if limit < 1:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Error",
                "Max Results must be a number."
            )

            return

        self.output.delete(
            "1.0",
            tk.END
        )

        self.results = []

        self.stop_event.clear()

        self.progress["value"] = 0

        self.status_var.set(
            "⚡ Searching..."
        )

        self.search_btn.config(
            state="disabled"
        )

        self.preview_btn.config(
            state="disabled"
        )

        self.search_thread = threading.Thread(
            target=self.search_worker,
            args=(
                path,
                field,
                value,
                limit
            ),
            daemon=True
        )

        self.search_thread.start()

    # --------------------------------------------------------
    # SEARCH WORKER
    # --------------------------------------------------------

    def search_worker(
        self,
        path,
        field,
        value,
        limit
    ):

        first_only = (
            self.first_only_var.get()
        )

        def callback(
            percent,
            speed,
            eta,
            matches
        ):

            self.root.after(
                0,
                self.update_progress,
                percent,
                speed,
                eta,
                matches
            )

        try:

            positions = fast_byte_search(
                path,
                field,
                value,
                limit,
                first_only,
                self.stop_event,
                callback
            )

            results = []

            for position in positions:

                if self.stop_event.is_set():
                    break

                obj = extract_json_object(
                    path,
                    position
                )

                if obj is not None:
                    results.append(obj)

            self.root.after(
                0,
                self.search_finished,
                results
            )

        except Exception as e:

            self.root.after(
                0,
                self.search_error,
                str(e)
            )

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    def update_progress(
        self,
        percent,
        speed,
        eta,
        matches
    ):

        self.progress["value"] = percent

        if eta > 0:

            eta_text = self.format_time(
                eta
            )

        else:
            eta_text = "--"

        self.status_var.set(
            f"{percent:.4f}%   |   "
            f"{speed:.1f} MB/s   |   "
            f"ETA {eta_text}   |   "
            f"Matches: {matches}"
        )

    # --------------------------------------------------------
    # FINISHED
    # --------------------------------------------------------

    def search_finished(
        self,
        results
    ):

        self.results = results

        self.search_btn.config(
            state="normal"
        )

        self.preview_btn.config(
            state="normal"
        )

        if self.stop_event.is_set():

            self.status_var.set(
                "⛔ Search stopped."
            )

            return

        if not results:

            self.status_var.set(
                "❌ No match found."
            )

            self.output.insert(
                tk.END,
                "No matching record found.\n"
            )

            return

        self.status_var.set(
            f"✅ Found {len(results)} record(s)."
        )

        self.output.insert(
            tk.END,
            "=" * 80 + "\n"
        )

        for index, obj in enumerate(
            results,
            start=1
        ):

            self.output.insert(
                tk.END,
                f"\nRESULT #{index}\n"
            )

            self.output.insert(
                tk.END,
                "-" * 80 + "\n"
            )

            self.output.insert(
                tk.END,
                format_result(obj)
            )

            self.output.insert(
                tk.END,
                "\n\n"
            )

    # --------------------------------------------------------
    # ERROR
    # --------------------------------------------------------

    def search_error(
        self,
        error
    ):

        self.search_btn.config(
            state="normal"
        )

        self.preview_btn.config(
            state="normal"
        )

        self.status_var.set(
            "❌ Error"
        )

        messagebox.showerror(
            "Search Error",
            error
        )

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    def stop_search(self):

        self.stop_event.set()

        self.status_var.set(
            "⛔ Stopping..."
        )

        self.search_btn.config(
            state="normal"
        )

        self.preview_btn.config(
            state="normal"
        )

    # --------------------------------------------------------
    # PREVIEW
    # --------------------------------------------------------

    def preview(self):

        path = self.file_var.get().strip()

        if not os.path.isfile(path):

            messagebox.showerror(
                "Error",
                "File not found."
            )

            return

        self.output.delete(
            "1.0",
            tk.END
        )

        self.status_var.set(
            "👁 Reading first 100 records..."
        )

        self.preview_btn.config(
            state="disabled"
        )

        thread = threading.Thread(
            target=self.preview_worker,
            args=(path,),
            daemon=True
        )

        thread.start()

    # --------------------------------------------------------
    # PREVIEW WORKER
    # --------------------------------------------------------

    def preview_worker(
        self,
        path
    ):

        try:

            records = preview_first_records(
                path,
                100
            )

            self.root.after(
                0,
                self.preview_finished,
                records
            )

        except Exception as e:

            self.root.after(
                0,
                self.preview_error,
                str(e)
            )

    # --------------------------------------------------------
    # PREVIEW FINISHED
    # --------------------------------------------------------

    def preview_finished(
        self,
        records
    ):

        self.preview_btn.config(
            state="normal"
        )

        self.status_var.set(
            f"✅ Preview loaded: {len(records)} records"
        )

        for index, obj in enumerate(
            records,
            start=1
        ):

            self.output.insert(
                tk.END,
                f"\nRECORD #{index}\n"
            )

            self.output.insert(
                tk.END,
                "-" * 80 + "\n"
            )

            self.output.insert(
                tk.END,
                format_result(obj)
            )

            self.output.insert(
                tk.END,
                "\n\n"
            )

    # --------------------------------------------------------
    # PREVIEW ERROR
    # --------------------------------------------------------

    def preview_error(
        self,
        error
    ):

        self.preview_btn.config(
            state="normal"
        )

        messagebox.showerror(
            "Preview Error",
            error
        )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    def export_results(self):

        if not self.results:

            messagebox.showinfo(
                "Export",
                "No search results to export."
            )

            return

        path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".jsonl",
            filetypes=[
                ("JSON Lines", "*.jsonl"),
                ("JSON", "*.json")
            ]
        )

        if not path:
            return

        try:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                for obj in self.results:

                    f.write(
                        json.dumps(
                            obj,
                            ensure_ascii=False
                        )
                        + "\n"
                    )

            messagebox.showinfo(
                "Export Complete",
                f"Saved:\n{path}"
            )

        except Exception as e:

            messagebox.showerror(
                "Export Error",
                str(e)
            )

    # --------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------

    def clear_output(self):

        self.output.delete(
            "1.0",
            tk.END
        )

        self.results = []

        self.progress["value"] = 0

        self.status_var.set(
            "Ready"
        )

    # --------------------------------------------------------
    # FORMAT TIME
    # --------------------------------------------------------

    @staticmethod
    def format_time(seconds):

        seconds = int(seconds)

        if seconds < 60:

            return f"{seconds}s"

        minutes = seconds // 60

        if minutes < 60:

            return f"{minutes}m {seconds % 60}s"

        hours = minutes // 60

        return (
            f"{hours}h "
            f"{minutes % 60}m"
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = FastJSONSearchApp(
        root
    )

    root.mainloop()
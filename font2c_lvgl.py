import subprocess
import shutil
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel
import webbrowser
import importlib
import sys

def check_and_install_module(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    try:
        importlib.import_module(module_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

check_and_install_module('freetype', 'freetype-py')
import freetype

MAX_EXTRA_FONTS = 10
MAX_RANGES_PER_FONT = 5

LANGUAGE_UNICODE_RANGES = {
    "English": "0x0020-0x007F",
    "Hindi": "0x0900-0x097F",
    "Marathi": "0x0900-0x097F",
    "Kannada": "0x0C80-0x0CFF",
    "Malayalam": "0x0D00-0x0D7F",
    "Tamil": "0x0B80-0x0BFF",
    "Telugu": "0x0C00-0x0C7F",
    "Gujarati": "0x0A80-0x0AFF",
    "Punjabi": "0x0A00-0x0A7F",
    "Bengali": "0x0980-0x09FF",
    "Oriya": "0x0B00-0x0B7F",
    "Urdu": "0x0600-0x06FF",
}

LIGHT_BLACK_BORDER = "#444444"
DARK_TEXT = "#202124"
HEADER_BG = "#ffffff"
BOX_BG = "#f6f6fb"
ENTRY_BG = "#ffffff"

def normalize_path(path):
    return os.path.abspath(path).replace("\\", "/")

def call_lv_font_conv(ttf_files, fontnames, sizes, ranges_list, bpp=1, out_paths=None):
    exe = shutil.which('lv_font_conv') or shutil.which('lv_font_conv.cmd')
    if exe is None:
        msg = (
            "lv_font_conv not found in your PATH.\n"
            "Run 'npm config get prefix' in terminal and add that folder to your Windows user PATH.\n"
            "Restart your computer after updating PATH.\n"
            f"Current PATH:\n{os.environ['PATH']}"
        )
        messagebox.showerror("Missing tool", msg)
        raise FileNotFoundError("lv_font_conv not found in PATH")

    output_files = []
    for idx, ttf_file in enumerate(ttf_files):
        fontname = fontnames[idx]
        size = sizes[idx]
        ranges = ranges_list[idx]
        if out_paths:
            output_filename = out_paths[idx]
        else:
            output_filename = normalize_path(ttf_file) + ".c"
        cmd = [exe, "--font", normalize_path(ttf_file)]
        for rng in ranges.replace('\n', ',').split(','):
            rng = rng.strip()
            if rng:
                cmd += ["--range", rng]
        cmd += [
            "--size", str(size),
            "--format", "lvgl",
            "--output", normalize_path(output_filename),
            "--lv-font-name", fontname,
            "--no-compress",
            "--bpp", str(bpp)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            messagebox.showerror(
                "Font Converter Error",
                f"Failed to generate .c file!\n"
                f"Return code: {result.returncode}\n"
                f"Command:\n{' '.join(cmd)}\n\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
                "Try running this command in a terminal for details."
            )
            raise Exception("lv_font_conv failed")
        output_files.append(normalize_path(output_filename))
    return output_files

class StatusText(tk.Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(state="disabled", bg="#f0f0f0", relief=tk.FLAT, height=5, wrap="word", highlightthickness=0)
        self.tag_configure("center", justify="center")
        self.tag_configure("success", foreground="green")
        self.tag_configure("error", foreground="red")

    def set_status_messages(self, messages):
        self.config(state="normal")
        self.delete("1.0", "end")
        for msg, is_success in messages:
            tag = "success" if is_success else "error"
            self.insert("end", msg + "\n",("center", tag))
        self.config(state="disabled")

class FontFileEntry:
    def __init__(self, master, index, remove_callback=None):
        self.master = master
        self.index = index
        self.remove_callback = remove_callback
        box_width = 1300

        self.frame = tk.Frame(
            master,
            bg=BOX_BG,
            highlightbackground="#444", highlightcolor="#444", highlightthickness=2,
            relief="groove",
            bd=0,
            padx=16, pady=18, width=box_width, height=300
        )
        self.frame.pack_propagate(False)
        box_inner = tk.Frame(self.frame, bg=BOX_BG, width=box_width - 10)
        box_inner.pack(expand=True, fill="both")

        # --- Row 1: Name, Font Size, TTF File, Browse ---
        row1 = tk.Frame(box_inner, bg=BOX_BG)
        row1.pack(pady=(0, 6))
        tk.Label(row1, text="Name:", bg=BOX_BG, font=("Segoe UI", 11, "bold"), fg=DARK_TEXT, width=10, anchor="e"
                 ).pack(side="left", padx=(0, 3))
        self.font_name_var = tk.StringVar(value="file_name")
        self.font_name_entry = tk.Entry(row1, textvariable=self.font_name_var, width=22, font=("Segoe UI", 11),
                                        bg=ENTRY_BG, fg=DARK_TEXT, highlightbackground=LIGHT_BLACK_BORDER,
                                        highlightcolor=LIGHT_BLACK_BORDER, highlightthickness=1, bd=0, relief='flat')
        self.font_name_entry.pack(side="left", padx=(0, 18))
        tk.Label(row1, text="Font Size (px):", bg=BOX_BG, font=("Segoe UI", 11, "bold"), fg=DARK_TEXT).pack(side="left",
                                                                                                            padx=(0, 3))
        self.font_size_var = tk.IntVar(value=1)
        self.font_size_spin = tk.Spinbox(row1, from_=1, to=72, textvariable=self.font_size_var, width=7,
                                         font=("Segoe UI", 11),
                                         bg=ENTRY_BG, fg=DARK_TEXT, highlightbackground=LIGHT_BLACK_BORDER,
                                         highlightcolor=LIGHT_BLACK_BORDER, highlightthickness=1, bd=0, relief='flat')
        self.font_size_spin.pack(side="left", padx=(0, 18))
        tk.Label(row1, text=f"TTF file {index + 1}:", bg=BOX_BG, font=("Segoe UI", 11, "bold"), fg=DARK_TEXT).pack(
            side="left", padx=(0, 3))
        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(row1, textvariable=self.path_var, width=40, font=("Segoe UI", 11),
                                   bg=ENTRY_BG, fg=DARK_TEXT, highlightbackground=LIGHT_BLACK_BORDER,
                                   highlightcolor=LIGHT_BLACK_BORDER, highlightthickness=1, bd=0, relief='flat')
        self.path_entry.pack(side="left", padx=(0, 10))
        browse_btn = tk.Button(row1, text="Browse", command=self.browse_file, font=("Segoe UI", 10, "bold"),
                               bg="#e0e8f1", relief="raised")
        browse_btn.pack(side="left", padx=2)
        if remove_callback and index != 0:
            self.remove_btn = tk.Button(row1, text="🗑️ Remove", command=self.remove_self, font=("Segoe UI", 10),
                                        bg="#fbe4e4", fg="#b30000")
            self.remove_btn.pack(side="left", padx=8)

        # Whitespace spacer between top row and Languages/Range
        tk.Frame(box_inner, height=18, bg=BOX_BG).pack(fill="x")

        # --- Row 2: Languages + Range side by side ---
        row_mid = tk.Frame(box_inner, bg=BOX_BG)
        row_mid.pack(pady=(4, 6))
        tk.Frame(row_mid, bg=BOX_BG, width=40).pack(side="left", expand=True)
        content_frame = tk.Frame(row_mid, bg=BOX_BG)
        content_frame.pack(side="left")
        lang_frame = tk.Frame(content_frame, bg=BOX_BG)
        lang_frame.grid(row=0, column=0, padx=(0, 28))
        tk.Label(lang_frame, text="Language(s):", bg=BOX_BG, font=("Segoe UI", 11, "bold"), fg=DARK_TEXT,
                 anchor='w').pack(anchor='w')

        # Add scrollbar beside Listbox
        listbox_wrapper = tk.Frame(lang_frame, bg=BOX_BG)
        listbox_wrapper.pack()
        self.lang_listbox = tk.Listbox(
            listbox_wrapper, selectmode="multiple", exportselection=False,
            height=5, width=18, font=("Segoe UI", 10, "bold"),
            bg="#f4f7ff", fg=DARK_TEXT, highlightbackground=LIGHT_BLACK_BORDER, highlightcolor=LIGHT_BLACK_BORDER,
            highlightthickness=1, bd=0, relief='flat'
        )
        scrollbar = tk.Scrollbar(listbox_wrapper, orient="vertical", command=self.lang_listbox.yview)
        self.lang_listbox.config(yscrollcommand=scrollbar.set)
        self.lang_listbox.pack(side="left", anchor="w")
        scrollbar.pack(side="left", fill="y", anchor="w")

        for lang in LANGUAGE_UNICODE_RANGES.keys():
            self.lang_listbox.insert("end", lang)
        self.lang_listbox.selection_set(0)
        self.suppress_range_event = False
        self.lang_listbox.bind("<<ListboxSelect>>", self.on_language_select)

        self.lang_listbox.pack()
        range_frame = tk.Frame(content_frame, bg=BOX_BG)
        range_frame.grid(row=0, column=1)
        range_label_frame = tk.Frame(range_frame, bg=BOX_BG)
        range_label_frame.pack(anchor="w", fill="x")
        tk.Label(range_label_frame, text="Range (max 5, comma/line-separated):", bg=BOX_BG,
                 font=("Segoe UI", 11, "bold"), fg=DARK_TEXT).pack(side="left", anchor="w")
        link = tk.Label(
            range_label_frame, text="Unicode Character Ranges", fg="#17499e", cursor="hand2",
            bg=BOX_BG, font=("Segoe UI", 10, "underline"), anchor="w"
        )
        link.pack(side="left", padx=(16, 0))
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://jrgraphix.net/research/unicode.php"))
        self.range_text = tk.Text(range_frame, height=3, width=68, font=("Segoe UI", 11),
                                  bg=ENTRY_BG, fg=DARK_TEXT, highlightbackground=LIGHT_BLACK_BORDER,
                                  highlightcolor=LIGHT_BLACK_BORDER,
                                  highlightthickness=1, bd=0, relief='flat')
        self.range_text.insert("1.0", LANGUAGE_UNICODE_RANGES["English"])
        self.range_text.pack(pady=(2, 0))

        # After the range row (row_mid) is packed
        row_mid.pack(pady=(4, 6))

        # Add the centered status area here:
        self.range_support_status = StatusText(box_inner, height=5)
        self.range_support_status.pack(fill="x", pady=(14, 2), ipadx=20, anchor="center")

        self.range_text.bind('<KeyRelease>', self.on_range_manual_edit)
        tk.Frame(row_mid, bg=BOX_BG, width=40).pack(side="left", expand=True)

        # --- Status at bottom ---
        self.status_text = StatusText(box_inner)
        self.status_text.pack(fill="x", pady=2)

    def on_language_select(self, event=None):
        if self.suppress_range_event:
            return
        selected_indices = self.lang_listbox.curselection()
        unicode_ranges = []
        for idx in selected_indices:
            unicode_ranges.append(LANGUAGE_UNICODE_RANGES[self.lang_listbox.get(idx)])
        if len(unicode_ranges) > MAX_RANGES_PER_FONT:
            messagebox.showwarning(
                "Too many ranges",
                f"Maximum {MAX_RANGES_PER_FONT} ranges allowed. Deselect to add more."
            )
            for idx in selected_indices[MAX_RANGES_PER_FONT:]:
                self.lang_listbox.selection_clear(idx)
            unicode_ranges = unicode_ranges[:MAX_RANGES_PER_FONT]
        self.suppress_range_event = True
        self.range_text.delete("1.0", "end")
        self.range_text.insert("1.0", ",".join(unicode_ranges))
        self.suppress_range_event = False

    def on_range_manual_edit(self, event):
        if self.suppress_range_event:
            return
        raw_ranges = self.range_text.get("1.0", "end").strip()
        ranges = [r.strip() for r in raw_ranges.replace('\n', ',').split(',') if r.strip()]
        if len(ranges) > MAX_RANGES_PER_FONT:
            self.range_text.delete("1.0", "end")
            self.range_text.insert("1.0", ",".join(ranges[:MAX_RANGES_PER_FONT]))
            messagebox.showwarning(
                "Too many ranges",
                f"Maximum {MAX_RANGES_PER_FONT} ranges allowed."
            )
            ranges = ranges[:MAX_RANGES_PER_FONT]
        self.suppress_range_event = True
        self.lang_listbox.selection_clear(0, 'end')
        for idx, lang in enumerate(LANGUAGE_UNICODE_RANGES):
            if LANGUAGE_UNICODE_RANGES[lang] in ranges:
                self.lang_listbox.selection_set(idx)
        self.suppress_range_event = False

    def browse_file(self):
        window = self.frame.winfo_toplevel()
        filename = filedialog.askopenfilename(filetypes=[("TTF Font Files", "*.ttf")], parent=window)
        if filename:
            if not filename.lower().endswith('.ttf'):
                messagebox.showerror("Invalid File", "TTF file type is expected.")
                return
            self.path_var.set(filename)

    def remove_self(self):
        if self.remove_callback:
            self.frame.destroy()
            self.remove_callback(self)

    def get_font_data(self):
        return {
            "font_path": self.path_var.get().strip(),
            "range": self.range_text.get("1.0", "end").strip(),
            "font_name": self.font_name_var.get().strip(),
            "font_size": self.font_size_var.get() or 1,
            "widget": self,
        }

    def set_status(self, messages):
        self.status_text.set_status_messages(messages)

    def set_range_support_status(self, messages):
        self.range_support_status.set_status_messages(messages)

def check_block_ranges(block):
    data = block.get_font_data()
    if not data['font_path'] or not data['font_path'].lower().endswith('.ttf') or not os.path.isfile(data['font_path']):
        block.set_range_support_status([("supported: ", True), ("unsupported: File missing or not TTF.", False)])
        block.set_status([("File missing or not TTF.", False)])
        return False
    raw_ranges = [i.strip() for i in data['range'].replace('\n', ',').split(',') if i.strip()]
    if not raw_ranges:
        block.set_range_support_status([("supported: ", True), ("unsupported: Enter Unicode range.", False)])
        block.set_status([("Enter Unicode range.", False)])
        return False
    if len(raw_ranges) > MAX_RANGES_PER_FONT:
        block.set_range_support_status([("supported: ", True), (f"unsupported: Maximum {MAX_RANGES_PER_FONT} ranges or codepoints allowed!", False)])
        block.set_status([(f"Maximum {MAX_RANGES_PER_FONT} ranges or codepoints allowed!", False)])
        return False
    try:
        parsed_ranges = []
        for item in raw_ranges:
            if '-' in item:
                start, end = item.split('-', 1)
                start = int(start, 0)
                end = int(end, 0)
                if end < start:
                    raise ValueError(f"Invalid range: {item}")
                parsed_ranges.append((start, end))
            else:
                val = int(item, 0)
                parsed_ranges.append((val, val))
    except Exception as e:
        block.set_range_support_status([("supported: ", True), (f"unsupported: Unicode range error: {e}", False)])
        block.set_status([(f"Unicode range error: {e}", False)])
        return False
    try:
        face = freetype.Face(data['font_path'])
        supported, unsupported = [], []
        for idx, (start, end) in enumerate(parsed_ranges):
            found = False
            for code in range(start, end + 1):
                if face.get_char_index(code) != 0:
                    found = True
                    break
            raw_range = raw_ranges[idx]
            if found:
                supported.append(raw_range)
            else:
                unsupported.append(raw_range)
        block.set_range_support_status([
            ("supported: " + (", ".join(supported) if supported else "None"), True),
            ("unsupported: " + (", ".join(unsupported) if unsupported else "None"), False)
        ])
        block.set_status([("supported: " + (", ".join(supported) if supported else "None"), True),
                          ("unsupported: " + (", ".join(unsupported) if unsupported else "None"), False)])
        return len(unsupported) == 0
    except Exception as e:
        block.set_range_support_status([("supported: ", True), (f"unsupported: Font check failed: {e}", False)])
        block.set_status([(f"Font check failed: {e}", False)])
        return False

class FontConverterApp:
    def __init__(self, parent=None, bpp='1'):
        if parent is None:
            self.root = tk.Tk()
            show_back = False
        else:
            self.root = tk.Toplevel(parent)
            show_back = True
        self.root.title("Centum Configuration Font Converter Tool")
        self.root.configure(bg=HEADER_BG)

        width = min(self.root.winfo_screenwidth(), 1440)
        height = min(self.root.winfo_screenheight(), 880)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(width=920, height=620)

        container = tk.Frame(self.root, width=width - 30, height=height - 40, bg=HEADER_BG, relief='solid')
        container.pack_propagate(False)
        container.place(relx=0.5, rely=0.5, anchor="center")

        if show_back:
            back_btn = tk.Button(container, text="Back", font=("Segoe UI", 12, "bold"), command=self.root.destroy)
            back_btn.pack(anchor='nw', pady=(8, 0), padx=(8, 0))

        title_label = tk.Label(container, text="Centum Configuration Font Converter Tool",
                               font=("Segoe UI", 21, "bold"), bg=HEADER_BG, fg="#222241")
        title_label.pack(pady=(24, 4))
        subtitle_label = tk.Label(container,
                                  text="Generate C arrays from TTF and WOFF font files for embedded or display projects.",
                                  font=("Segoe UI", 12, "bold"), bg=HEADER_BG, fg="#2b66ad")
        subtitle_label.pack(pady=(0, 7))
        desc_label = tk.Label(container,
                              text="Select a font and Unicode range, adjust font size, and export to a C source file suitable for microcontroller applications. Multiple languages and font blocks are supported.",
                              font=("Segoe UI", 11), bg=HEADER_BG, fg="#46474a", wraplength=760, justify="center")
        desc_label.pack(pady=(0, 14))

        settings_fr = tk.Frame(container, pady=10, padx=8, bg=HEADER_BG)
        settings_fr.pack()

        self.selected_bpp = int(bpp)

        canvas_fr = tk.Frame(container, bg=HEADER_BG)
        canvas_fr.pack(expand=True, pady=26, fill="both")
        self.canvas = tk.Canvas(canvas_fr, bg=HEADER_BG, highlightthickness=0)
        v_scrollbar = tk.Scrollbar(canvas_fr, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        self.scrollable_frame = tk.Frame(self.canvas, bg=HEADER_BG)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.file_blocks = []
        self.add_font_block()
        self.buttons_frame = tk.Frame(container, bg=HEADER_BG)
        self.buttons_frame.pack(fill="x", pady=14)
        self.add_font_btn = tk.Button(
            self.buttons_frame, text="+ Include another font", command=self.add_font_block,
            font=("Segoe UI", 11, "bold"), bg="#3192e3", fg="#fff", relief="raised", bd=2, padx=8, pady=2
        )
        self.add_font_btn.pack(side="top", pady=6, ipadx=13)
        self.submit_btn = tk.Button(
            self.buttons_frame, text="Generate .C file", command=self.submit_all,
            font=("Segoe UI", 12, "bold"), bg="#232323", fg='#fff', relief="raised", bd=2, padx=9, pady=3
        )
        self.submit_btn.pack(side="top", pady=9, ipadx=36)
        self._bind_mousewheel(self.canvas)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def _bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))

    def add_font_block(self):
        if len(self.file_blocks) >= MAX_EXTRA_FONTS:
            messagebox.showwarning("Limit reached", f"Maximum {MAX_EXTRA_FONTS} fonts supported total.")
            return
        idx = len(self.file_blocks)
        remove_callback = self.remove_font_block if idx != 0 else None
        block = FontFileEntry(self.scrollable_frame, idx, remove_callback)
        block.frame.pack(fill="x", pady=30)
        self.file_blocks.append(block)

    def remove_font_block(self, block):
        if block in self.file_blocks:
            self.file_blocks.remove(block)

    def submit_all(self):
        ttf_files = []
        ranges_list = []
        font_names = []
        font_sizes = []
        all_supported = True

        for block in self.file_blocks:
            if not check_block_ranges(block):
                all_supported = False
        if not all_supported:
            return

        for block in self.file_blocks:
            data = block.get_font_data()
            ttf_files.append(data['font_path'])
            ranges_list.append(data["range"])
            fname = data["font_name"].strip()
            if not fname:
                fname = f"font{len(font_names)+1}"
            fname = fname.rstrip('.c').rstrip('.C')
            font_names.append(fname)
            font_sizes.append(data["font_size"])

        if not ttf_files:
            messagebox.showerror("Error", "Please select at least one font file.")
            return

        output_folder = filedialog.askdirectory(parent=self.root, title="Select folder to save generated .c file(s)")
        if not output_folder:
            messagebox.showwarning("Cancelled", "No output folder selected. Operation cancelled.")
            return

        out_c_files = []
        for fname in font_names:
            out_path = os.path.join(output_folder, f"{fname}.c")
            counter = 1
            while os.path.exists(out_path):
                out_path = os.path.join(output_folder, f"{fname}({counter}).c")
                counter += 1
            out_c_files.append(out_path)

        try:
            output_files = call_lv_font_conv(
                ttf_files=ttf_files,
                fontnames=font_names,
                sizes=font_sizes,
                ranges_list=ranges_list,
                bpp=self.selected_bpp,
                out_paths=out_c_files
            )
            for idx, block in enumerate(self.file_blocks):
                block.set_status([("Font generated: " + output_files[idx], True)])
            messagebox.showinfo(
                "Success",
                "Generated font files:\n" + "\n".join(output_files),
                parent=self.root
            )
        except Exception as e:
            for block in self.file_blocks:
                block.set_status([(f"Error during font generation: {e}", False)])


if __name__ == "__main__":
    app = FontConverterApp()
    app.root.mainloop()

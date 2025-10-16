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

def normalize_path(path):
    return os.path.abspath(path).replace("\\", "/")

def call_lv_font_conv(ttf_files, out_c_file, fontnames, sizes, bpp, ranges_list):
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

    for idx, ttf_file in enumerate(ttf_files):
        fontname = fontnames[idx]
        size = sizes[idx]
        ranges = ranges_list[idx]
        output_filename = out_c_file
        if len(ttf_files) > 1:
            namepart = fontname if fontname else f"font{idx+1}"
            output_filename = os.path.splitext(out_c_file)[0] + f"_{namepart}_{size}.c"
        cmd = [exe, "--font", normalize_path(ttf_file)]
        for rng in ranges.replace('\n', ',').split(','):
            rng = rng.strip()
            if rng:
                cmd += ["--range", rng]
        cmd += [
            "--size", str(size),
            "--bpp", str(bpp),
            "--format", "lvgl",
            "--output", normalize_path(output_filename),
            "--lv-font-name", fontname,
            "--no-compress"
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

def parse_individual_ranges(range_text):
    items = [i.strip() for i in range_text.replace('\n', ',').split(',') if i.strip()]
    if len(items) > MAX_RANGES_PER_FONT:
        raise ValueError(f"Maximum {MAX_RANGES_PER_FONT} ranges or codepoints allowed!")
    ranges = []
    for item in items:
        if '-' in item:
            start, end = item.split('-', 1)
            start = int(start, 0)
            end = int(end, 0)
            if end < start:
                raise ValueError(f"Invalid range: {item}")
            ranges.append((start, end))
        else:
            val = int(item, 0)
            ranges.append((val, val))
    return ranges

class StatusText(tk.Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(state="disabled", bg="#f0f0f0", relief=tk.FLAT, height=7, wrap="word")
        self.tag_configure("success", foreground="green")
        self.tag_configure("error", foreground="red")

    def set_status_messages(self, messages):
        self.config(state="normal")
        self.delete("1.0", "end")
        for msg, is_success in messages:
            tag = "success" if is_success else "error"
            self.insert("end", msg + "\n", tag)
        self.config(state="disabled")

def show_range_popup(messages):
    popup = Toplevel()
    popup.title("Font Range Support")
    popup.geometry("430x220")
    frame = tk.Frame(popup, padx=20, pady=22)
    frame.pack(expand=True, fill="both")
    for msg, is_success in messages:
        color = "green" if is_success else "red"
        label = tk.Label(frame, text=msg, fg=color, font=("Segoe UI", 12, "bold"))
        label.pack(anchor="w", pady=3)
    tk.Button(frame, text="OK", command=popup.destroy, width=14, font=("Segoe UI", 11, "bold")).pack(pady=13)
    popup.transient()
    popup.grab_set()
    frame.focus_set()
    return

class FontFileEntry:
    def __init__(self, master, index, remove_callback=None):
        self.master = master
        self.index = index
        self.remove_callback = remove_callback
        box_width = 1200
        self.frame = tk.Frame(
            master, relief=tk.GROOVE, bd=2, padx=18, pady=18,
            width=box_width, height=320, bg="#f9f9f9"
        )
        self.frame.pack_propagate(False)
        box_inner = tk.Frame(self.frame, bg="#f9f9f9", width=box_width-30)
        box_inner.pack(expand=True)
        # Row 1: Name, Font Size and TTF file + Browse in one line, centered
        row1 = tk.Frame(box_inner, bg="#f9f9f9")
        row1.pack(fill="x", pady=8)
        row1.grid_columnconfigure(0, weight=1)
        for col in range(8):
            row1.grid_columnconfigure(col, weight=1)
        tk.Label(row1, text="Name:", bg="#f9f9f9").grid(row=0, column=0, sticky="e", padx=3)
        self.font_name_var = tk.StringVar(value="file_name")
        self.font_name_entry = tk.Entry(row1, textvariable=self.font_name_var, width=22)
        self.font_name_entry.grid(row=0, column=1, padx=8)
        tk.Label(row1, text="Font Size (px):", bg="#f9f9f9").grid(row=0, column=2, sticky="e", padx=3)
        self.font_size_var = tk.IntVar(value=1)
        self.font_size_spin = tk.Spinbox(row1, from_=1, to=72, textvariable=self.font_size_var, width=7)
        self.font_size_spin.grid(row=0, column=3, padx=8)
        tk.Label(row1, text=f"TTF file {index + 1}:", bg="#f9f9f9").grid(row=0, column=4, sticky="e", padx=3)
        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(row1, textvariable=self.path_var, width=40)
        self.path_entry.grid(row=0, column=5, padx=8)
        browse_btn = tk.Button(row1, text="Browse", command=self.browse_file)
        browse_btn.grid(row=0, column=6, padx=6)
        if remove_callback and index != 0:
            self.remove_btn = tk.Button(row1, text="🗑️ Remove", command=self.remove_self)
            self.remove_btn.grid(row=0, column=7, padx=8)
        # Row 2: Language selector (multiselect Listbox + vertical scrollbar), centered
        row2 = tk.Frame(box_inner, bg="#f9f9f9")
        row2.pack(fill="x", pady=6)
        tk.Label(row2, text="Language(s):", bg="#f9f9f9", anchor="center").pack(side="top", anchor="n")
        listbox_frame = tk.Frame(row2, bg="#f9f9f9")
        listbox_frame.pack(side="top", anchor="center")
        self.lang_listbox = tk.Listbox(
            listbox_frame, selectmode="multiple", exportselection=False,
            height=5, width=20, font=("Segoe UI", 10)
        )
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=self.lang_listbox.yview)
        self.lang_listbox.config(yscrollcommand=scrollbar.set)
        self.lang_listbox.pack(side="left", anchor="center")
        scrollbar.pack(side="left", fill="y", anchor="center")
        for idx, lang in enumerate(LANGUAGE_UNICODE_RANGES.keys()):
            self.lang_listbox.insert("end", lang)
        self.lang_listbox.selection_set(0)
        self.suppress_range_event = False
        self.lang_listbox.bind("<<ListboxSelect>>", self.on_language_select)
        # Row 3: Range box, centered
        row3 = tk.Frame(box_inner, bg="#f9f9f9")
        row3.pack(fill="x", pady=10)
        tk.Label(row3, text="Range (max 5, comma/line-separated):",
                 bg="#f9f9f9", anchor="center").pack(anchor="center")
        self.range_text = tk.Text(row3, height=3, width=115)
        self.range_text.insert("1.0", LANGUAGE_UNICODE_RANGES["English"])
        self.range_text.pack(anchor="center", pady=(0, 4))
        self.range_text.bind('<KeyRelease>', self.on_range_manual_edit)
        # Row 4: Unicode Character Ranges link, centered
        link_frame = tk.Frame(box_inner, bg="#f9f9f9")
        link_frame.pack(fill="x", pady=3)
        link = tk.Label(
            link_frame, text="Unicode Character Ranges", fg="blue", cursor="hand2",
            bg="#f9f9f9", anchor="center"
        )
        link.pack(anchor="center")
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://jrgraphix.net/research/unicode.php"))
        # Status at bottom
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
        filename = filedialog.askopenfilename(filetypes=[("TTF Font Files", "*.ttf")])
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

def check_block_ranges(block):
    data = block.get_font_data()
    messages = []
    if not data['font_path'] or not data['font_path'].lower().endswith('.ttf') or not os.path.isfile(data['font_path']):
        messages.append(("File missing or not TTF.", False))
        block.set_status(messages)
        show_range_popup(messages)
        return False
    raw_ranges = [i.strip() for i in data['range'].replace('\n', ',').split(',') if i.strip()]
    if not raw_ranges:
        messages.append(("Enter Unicode range.", False))
        block.set_status(messages)
        show_range_popup(messages)
        return False
    if len(raw_ranges) > MAX_RANGES_PER_FONT:
        messages.append((f"Maximum {MAX_RANGES_PER_FONT} ranges or codepoints allowed!", False))
        block.set_status(messages)
        show_range_popup(messages)
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
        messages.append((f"Unicode range error: {e}", False))
        block.set_status(messages)
        show_range_popup(messages)
        return False
    try:
        face = freetype.Face(data['font_path'])
        all_supported = True
        for idx, (start, end) in enumerate(parsed_ranges):
            supported_chars = []
            for code in range(start, end + 1):
                if face.get_char_index(code) != 0:
                    supported_chars.append(code)
            raw_range = raw_ranges[idx]
            if not supported_chars:
                all_supported = False
                msg = f"{raw_range} - Not supported"
                messages.append((msg, False))
            else:
                msg = f"{raw_range} - Supported"
                messages.append((msg, True))
        block.set_status(messages)
        show_range_popup(messages)
        return all_supported
    except Exception as e:
        messages.append((f"Font check failed: {e}", False))
        block.set_status(messages)
        show_range_popup(messages)
        return False

class LVGLFontConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Centum Configuration Tool")

        # Set window size dynamically based on screen resolution
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(width=800, height=600)

        # Container holds everything, fixed size with expansion
        container = tk.Frame(self.root, width=width-20, height=height-40)
        container.pack_propagate(False)
        container.place(relx=0.5, rely=0.5, anchor="center")

        title_label = tk.Label(container, text="Centum Configuration Tool", font=("Segoe UI", 32, "bold"))
        title_label.pack(pady=(18, 8))
        subtitle_label = tk.Label(container, text="Convert TTF and WOFF font files to a C source array for microcontrollers.",
                                 font=("Segoe UI", 18, "bold"))
        subtitle_label.pack(pady=(0, 9))
        desc_text = (
            "This tool lets you turn any TrueType (TTF) or WOFF font file into a C array suitable for embedded devices. "
            "You can select Unicode range, font name and size, bit-per-pixel (bpp), and multiple languages per font block."
        )
        desc_label = tk.Label(container, text=desc_text, font=("Segoe UI", 12), wraplength=width-50, justify="center")
        desc_label.pack(pady=(0, 30))

        settings_fr = tk.Frame(container, pady=8, padx=5)
        settings_fr.pack()
        tk.Label(settings_fr, text="Bpp:", width=6, font=("Segoe UI", 10)).pack(side="left")
        self.bpp_var = tk.StringVar(value='1')
        ttk.Combobox(settings_fr, textvariable=self.bpp_var, values=['1', '2', '3', '4', '8'],
                     width=3, state='readonly', font=("Segoe UI", 10)).pack(side="left", padx=6)

        canvas_fr = tk.Frame(container)
        canvas_fr.pack(expand=True, pady=26, fill="both")
        self.canvas = tk.Canvas(canvas_fr)
        v_scrollbar = tk.Scrollbar(canvas_fr, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")

        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bindings to update canvas size with window resizing
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.file_blocks = []
        self.add_font_block()

        self.buttons_frame = tk.Frame(container)
        self.buttons_frame.pack(fill="x", pady=14)
        self.add_font_btn = tk.Button(
            self.buttons_frame, text="+ Include another font", command=self.add_font_block
        )
        self.add_font_btn.pack(side="top", pady=5, ipadx=18)
        self.submit_btn = tk.Button(
            self.buttons_frame, text="Submit", command=self.submit_all, bg='black', fg='white'
        )
        self.submit_btn.pack(side="top", pady=6, ipadx=34)
        self._bind_mousewheel(self.canvas)

    def _on_frame_configure(self, event):
        # Reset the scroll region to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # Update the window item width to fill canvas
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
        block.frame.pack(fill="x", pady=32)
        self.file_blocks.append(block)

    def remove_font_block(self, block):
        if block in self.file_blocks:
            self.file_blocks.remove(block)

    def submit_all(self):
        bpp = self.bpp_var.get()
        ttf_files = []
        ranges_list = []
        font_names = []
        font_sizes = []

        all_supported = True
        for block in self.file_blocks:
            result = check_block_ranges(block)
            if not result:
                all_supported = False
        if not all_supported:
            return

        for block in self.file_blocks:
            data = block.get_font_data()
            ttf_files.append(data['font_path'])
            ranges_list.append(data["range"])
            font_names.append(data["font_name"])
            font_sizes.append(data["font_size"])

        if not ttf_files:
            messagebox.showerror("Error", "Please select at least one font file.")
            return

        output_name = next((name for name in font_names if name), "file_name")
        output_folder = os.path.dirname(normalize_path(ttf_files[0]))
        output_filename = os.path.join(output_folder, f"{output_name}.c")
        counter = 1
        while os.path.exists(normalize_path(output_filename)):
            output_filename = os.path.join(output_folder, f"{output_name}({counter}).c")
            counter += 1

        try:
            call_lv_font_conv(
                ttf_files,
                output_filename,
                font_names,
                font_sizes,
                bpp,
                ranges_list
            )
            for block in self.file_blocks:
                block.set_status([("Font generated: " + os.path.basename(output_filename), True)])
            messagebox.showinfo("Success", f"Generated font file:\n{output_filename}")

        except Exception as e:
            for block in self.file_blocks:
                block.set_status([(f"Error during font generation: {e}", False)])

if __name__ == "__main__":
    root = tk.Tk()
    app = LVGLFontConverterApp(root)
    root.mainloop()

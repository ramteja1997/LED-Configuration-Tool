import subprocess
import shutil
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

MAX_EXTRA_FONTS = 10
MAX_RANGES_PER_FONT = 5

def normalize_path(path):
    return os.path.abspath(path).replace("\\", "/")

def call_lv_font_conv(ttf_files, out_c_file, fontname, size, bpp, ranges_list):
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

    cmd = [exe]
    for i, ttf_file in enumerate(ttf_files):
        norm_font = normalize_path(ttf_file)
        cmd += ["--font", norm_font]
        for rng in ranges_list[i].replace('\n', ',').split(','):
            rng = rng.strip()
            if rng:
                cmd += ["--range", rng]

    cmd += [
        "--size", str(size),
        "--bpp", str(bpp),
        "--format", "lvgl",
        "--output", normalize_path(out_c_file),
        "--lv-font-name", fontname,
        "--no-compress"  # Keep only supported flags
    ]

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
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

class FontFileEntry:
    def __init__(self, master, index, remove_callback=None):
        self.master = master
        self.index = index
        self.remove_callback = remove_callback
        self.frame = tk.Frame(master, relief=tk.GROOVE, bd=2, padx=16, pady=16, width=850, height=280, bg="#f9f9f9")
        self.frame.pack_propagate(False)
        row1 = tk.Frame(self.frame, bg="#f9f9f9")
        row1.pack(fill="x", pady=(0, 3))
        tk.Label(row1, text=f"TTF file {index + 1}:", width=12, bg="#f9f9f9").pack(side="left")
        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(row1, textvariable=self.path_var, width=45)
        self.path_entry.pack(side="left", padx=5)
        browse_btn = tk.Button(row1, text="Browse", command=self.browse_file)
        browse_btn.pack(side="left")
        row2 = tk.Frame(self.frame, bg="#f9f9f9")
        row2.pack(fill="x", pady=(0, 2))
        tk.Label(row2, text="Range (max 5, comma/line-separated):", bg="#f9f9f9").pack(anchor="w")
        self.range_text = tk.Text(row2, height=3, width=80)
        self.range_text.insert("1.0", "0x20-0x7F")
        self.range_text.pack(fill="both", pady=(0, 2))
        link = tk.Label(self.frame, text="Unicode Character Ranges", fg="blue", cursor="hand2", bg="#f9f9f9")
        link.pack(anchor="w", pady=1)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://jrgraphix.net/research/unicode.php"))
        if remove_callback:
            self.remove_btn = tk.Button(self.frame, text="🗑️ Remove", command=self.remove_self)
            self.remove_btn.pack(fill="x", pady=(2, 8))
        self.status_text = StatusText(self.frame)
        self.status_text.pack(fill="x", pady=2)
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
        return False
    if not data['range'].strip():
        messages.append(("Enter Unicode range.", False))
        block.set_status(messages)
        return False
    try:
        ranges = parse_individual_ranges(data['range'])
    except Exception as e:
        messages.append((f"Unicode range error: {e}", False))
        block.set_status(messages)
        return False
    if not ranges:
        messages.append(("Unicode range is empty.", False))
        block.set_status(messages)
        return False
    try:
        import freetype
        face = freetype.Face(data['font_path'])
        for (start, end) in ranges:
            unsupported_chars = []
            for code in range(start, end + 1):
                if face.get_char_index(code) == 0:
                    unsupported_chars.append(code)
            if unsupported_chars:
                messages.append((f"Range 0x{start:04X}-0x{end:04X} missing: {', '.join(hex(u) for u in unsupported_chars)}", False))
            else:
                messages.append((f"Range 0x{start:04X}-0x{end:04X} fully supported.", True))
    except Exception as e:
        messages.append((f"Font check failed: {e}", False))
        block.set_status(messages)
        return False
    block.set_status(messages)
    return all(s for m, s in messages)

class LVGLFontConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Centum Configuration Tool")
        self.root.geometry("1100x800")
        self.root.update_idletasks()
        container = tk.Frame(self.root, width=1000, height=800)
        container.pack_propagate(False)
        container.place(relx=0.5, rely=0.5, anchor="center")
        title_label = tk.Label(container, text="Centum Configuration Tool", font=("Segoe UI", 32, "bold"))
        title_label.pack(pady=(18, 6))
        subtitle_label = tk.Label(container, text="Convert TTF and WOFF fonts to C array.", font=("Segoe UI", 18, "bold"))
        subtitle_label.pack(pady=(0, 7))
        desc_text = ("With this free tool you can create a C array from any TTF or WOFF for LVGL. "
                     "Select Unicode range and specify bpp (bit-per-pixel).")
        desc_label = tk.Label(container, text=desc_text, font=("Segoe UI", 12), wraplength=830, justify="center")
        desc_label.pack(pady=(0, 30))
        settings_fr = tk.Frame(container, pady=5, padx=5)
        settings_fr.pack()
        tk.Label(settings_fr, text="Name:", width=12, font=("Segoe UI", 10)).pack(side="left")
        self.font_name_var = tk.StringVar()
        tk.Entry(settings_fr, textvariable=self.font_name_var, width=20, font=("Segoe UI", 10)).pack(side="left", padx=5)
        tk.Label(settings_fr, text="Font Size (px):", width=13, font=("Segoe UI", 10)).pack(side="left", padx=(15, 0))
        self.font_size_var = tk.IntVar(value=16)
        tk.Spinbox(settings_fr, from_=8, to=72, textvariable=self.font_size_var, width=5, font=("Segoe UI", 10)).pack(side="left", padx=3)
        tk.Label(settings_fr, text="Bpp:", width=6, font=("Segoe UI", 10)).pack(side="left", padx=(15, 0))
        self.bpp_var = tk.StringVar(value='1')
        ttk.Combobox(settings_fr, textvariable=self.bpp_var, values=['1', '2', '3', '4', '8'], width=3, state='readonly', font=("Segoe UI", 10)).pack(side="left", padx=3)
        canvas_fr = tk.Frame(container)
        canvas_fr.pack(expand=True, pady=32)
        self.canvas = tk.Canvas(canvas_fr, width=920, height=350)
        v_scrollbar = tk.Scrollbar(canvas_fr, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, width=920)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((450, 0), window=self.scrollable_frame, anchor="n")
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        self.file_blocks = []
        self.add_font_block()
        self.buttons_frame = tk.Frame(container)
        self.buttons_frame.pack(fill="x", pady=10)
        self.add_font_btn = tk.Button(
            self.buttons_frame, text="+ Include another font", command=self.add_font_block
        )
        self.add_font_btn.pack(side="top", pady=5, ipadx=10)
        self.submit_btn = tk.Button(
            self.buttons_frame, text="Submit", command=self.submit_all, bg='black', fg='white'
        )
        self.submit_btn.pack(side="top", pady=5, ipadx=30)
        self._bind_mousewheel(self.canvas)

    def _bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))

    def add_font_block(self):
        if len(self.file_blocks) >= MAX_EXTRA_FONTS:
            messagebox.showwarning("Limit reached", f"Maximum {MAX_EXTRA_FONTS} fonts supported total.")
            return
        block = FontFileEntry(self.scrollable_frame, len(self.file_blocks), self.remove_font_block)
        block.frame.pack(fill="x", pady=22)
        self.file_blocks.append(block)

    def remove_font_block(self, block):
        if block in self.file_blocks:
            self.file_blocks.remove(block)

    def submit_all(self):
        font_name = self.font_name_var.get().strip()
        bpp = self.bpp_var.get()
        font_size = self.font_size_var.get()
        if not font_name:
            messagebox.showerror("Input Error", "Please enter a font name (top settings).")
            return
        if not bpp or not font_size:
            messagebox.showerror("Input Error", "Specify valid font size and bpp (top settings).")
            return
        ok_flags = []
        for block in self.file_blocks:
            ok_flags.append(check_block_ranges(block))
        if not all(ok_flags):
            return
        ttf_files = []
        ranges_list = []
        for block in self.file_blocks:
            data = block.get_font_data()
            ttf_files.append(data['font_path'])
            ranges_list.append(data["range"])
        output_folder = os.path.dirname(normalize_path(ttf_files[0]))
        output_filename = os.path.join(output_folder, f"{font_name}.c")
        counter = 1
        while os.path.exists(normalize_path(output_filename)):
            output_filename = os.path.join(output_folder, f"{font_name}({counter}).c")
            counter += 1
        try:
            call_lv_font_conv(
                ttf_files,
                output_filename,
                font_name,
                int(font_size),
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

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import webbrowser
import freetype

# Allows maximum ranges 5 and ttf file upload 10
MAX_EXTRA_FONTS = 10
MAX_RANGES_PER_FONT = 5

def pack_4bpp(buffer, width, rows):
    packed = []
    for y in range(rows):
        for x in range(0, width, 2):
            p1 = buffer[y * width + x]
            p2 = buffer[y * width + x + 1] if (x + 1) < width else 0
            n1 = int(round(p1 / 17.0))
            n2 = int(round(p2 / 17.0))
            packed.append((n1 << 4) | n2)
    return packed

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
        self.frame = tk.Frame(master, relief=tk.GROOVE, bd=2, padx=8, pady=8)
        self.frame.pack(fill="x", padx=8, pady=8)

        row1 = tk.Frame(self.frame)
        row1.pack(fill="x", pady=(0,3))
        tk.Label(row1, text=f"Font file {index + 1}:", width=12).pack(side="left")
        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(row1, textvariable=self.path_var, width=45)
        self.path_entry.pack(side="left", padx=5)
        browse_btn = tk.Button(row1, text="Browse", command=self.browse_file)
        browse_btn.pack(side="left")

        row2 = tk.Frame(self.frame)
        row2.pack(fill="x", pady=(0,2))
        tk.Label(row2, text="Range (max 5, comma/line-separated):").pack(anchor="w")
        self.range_text = tk.Text(row2, height=3, width=70)
        self.range_text.insert("1.0", "0x20-0x7F")
        self.range_text.pack(fill="both", pady=(0,2))

        link = tk.Label(self.frame, text="Unicode Character Ranges", fg="blue", cursor="hand2")
        link.pack(anchor="w", pady=1)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://jrgraphix.net/research/unicode.php"))

        if remove_callback:
            self.remove_btn = tk.Button(self.frame, text="🗑️ Remove", command=self.remove_self)
            self.remove_btn.pack(fill="x", pady=(2,8))

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

def generate_lvgl_font_c_multi(font_inputs, out_font_name, size, bpp):
    first_font_path = font_inputs[0][0]
    output_folder = os.path.dirname(first_font_path)
    base_name = out_font_name
    output_filename = os.path.join(output_folder, f"{base_name}.c")
    counter = 1
    while os.path.exists(output_filename):
        output_filename = os.path.join(output_folder, f"{base_name}({counter}).c")
        counter += 1

    glyph_entries = []
    for font_path, codepoints in font_inputs:
        face = freetype.Face(font_path)
        face.set_pixel_sizes(0, size)
        for code in codepoints:
            try:
                face.load_char(chr(code))
                glyph_entries.append((font_path, face, code))
            except Exception:
                pass

    if not glyph_entries:
        ranges = []
        for font_path, codepoints in font_inputs:
            if len(codepoints) == 1:
                ranges.append(f"{codepoints[0]:#x}")
            else:
                ranges.append(f"{codepoints[0]:#x}-{codepoints[-1]:#x}")
        raise Exception(f"No characters found in supplied font(s) for range: {', '.join(ranges)}")

    glyph_descs = []
    bitmap_offset = 0
    unicode_list = []

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("/*******************************************************************************\n")
        f.write(f"* Size: {size} px\n* Bpp: {bpp}\n")
        f.write(f"* Opts: --multi-font\n")
        f.write(f"*******************************************************************************/\n\n")

        macro_name = base_name.upper().replace(" ", "_").replace("-", "_")
        f.write("#ifdef LV_LVGL_H_INCLUDE_SIMPLE\n#include \"lvgl.h\"\n#else\n#include \"lvgl/lvgl.h\"\n#endif\n\n")
        f.write(f"#ifndef {macro_name}\n#define {macro_name} 1\n#endif\n\n")
        f.write("/*-----------------\n* BITMAPS\n*----------------*/\n")
        f.write("static LV_ATTRIBUTE_LARGE_CONST const uint8_t glyph_bitmap[] = {\n")

        for font_path, face, code in glyph_entries:
            try:
                ft_flags = freetype.FT_LOAD_RENDER | (
                    freetype.FT_LOAD_TARGET_MONO if bpp == 1 else freetype.FT_LOAD_TARGET_NORMAL)
                face.load_char(chr(code), ft_flags)
            except Exception:
                glyph_descs.append((bitmap_offset, 0, 0, 0, 0, 0))
                unicode_list.append(code)
                continue

            bmp = face.glyph.bitmap
            width, rows = bmp.width, bmp.rows
            buffer = bmp.buffer
            ch = chr(code)
            f.write(f"\n/* U+{code:04X} \"{ch}\" ({os.path.basename(font_path)}) */\n\n")

            if bpp == 1:
                row_bytes = (width + 7) // 8 if width != 0 else 0
                for y in range(rows):
                    f.write("    ")
                    for b in range(row_bytes):
                        idx = y * row_bytes + b
                        f.write(f"0x{buffer[idx]:02X}" if idx < len(buffer) else "0x00")
                        if not (y == rows - 1 and b == row_bytes - 1):
                            f.write(", ")
                    f.write(",\n")
                bitmap_offset += rows * row_bytes
            else:
                packed = pack_4bpp(buffer, width, rows)
                for i in range(0, len(packed), 12):
                    chunk = ", ".join(f"0x{b:02X}" for b in packed[i:i + 12])
                    f.write(f"    {chunk},\n")
                bitmap_offset += len(packed)

            glyph_descs.append(
                (bitmap_offset, width, rows, face.glyph.advance.x // 64, face.glyph.bitmap_left, face.glyph.bitmap_top))
            unicode_list.append(code)
        f.write("};\n\n")

        f.write("static const lv_font_fmt_txt_glyph_dsc_t glyph_dsc[] = {\n")
        offset = 0
        for desc in glyph_descs:
            f.write(f"    {{ .bitmap_index = {offset}, .adv_w = {desc[3]}, .box_w = {desc[1]},"
                    f" .box_h = {desc[2]}, .ofs_x = {desc[4]}, .ofs_y = {desc[5]} }},\n")
            if desc[1] > 0 and desc[2] > 0:
                cells = ((desc[1] + 7) // 8 if bpp == 1 else (desc[1] + 1) // 2) * desc[2]
                offset += cells
        f.write("};\n\n")

        f.write("static const uint16_t unicode_list_0[] = {\n")
        for code in unicode_list:
            f.write(f"    0x{code:04X},\n")
        f.write("};\n\n")

        f.write("static const lv_font_fmt_txt_cmap_t cmaps[] = {\n")
        f.write("    {\n")
        f.write(f"        .range_start = 0x{unicode_list[0]:04X}, .range_length = {len(unicode_list)},"
                f" .glyph_id_start = 1,\n")
        f.write(f"        .unicode_list = unicode_list_0, .glyph_id_ofs_list = NULL,"
                f" .list_length = {len(unicode_list)}, .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY\n")
        f.write("    }\n};\n\n")

        f.write("static lv_font_fmt_txt_desc_t font_dsc = {\n")
        f.write("    .glyph_bitmap = glyph_bitmap,\n")
        f.write("    .glyph_dsc = glyph_dsc,\n")
        f.write("    .cmaps = cmaps,\n")
        f.write("    .kern_dsc = NULL, .kern_scale = 0,\n")
        f.write(f"    .cmap_num = 1, .bpp = {bpp}, .kern_classes = 0, .bitmap_format = 0\n")
        f.write("};\n\n")

        safe_name = base_name.replace(" ", "_").replace("-", "_").lower()
        f.write(f"const lv_font_t {safe_name} = {{\n")
        f.write("    .get_glyph_dsc = lv_font_get_glyph_dsc_fmt_txt,\n")
        f.write("    .get_glyph_bitmap = lv_font_get_bitmap_fmt_txt,\n")
        f.write(f"    .line_height = {size},\n")
        f.write("    .base_line = 0,\n")
        f.write("    .dsc = &font_dsc\n")
        f.write("};\n\n")

        f.write(f"#endif /* {macro_name} */\n")

    return output_filename

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
    font_path = data['font_path']
    all_supported = True
    for (start, end) in ranges:
        face = freetype.Face(font_path)
        unsupported_chars = []
        for code in range(start, end + 1):
            if face.get_char_index(code) == 0:
                unsupported_chars.append(code)
        if unsupported_chars:
            all_supported = False
            def format_range(codes):
                result = []
                sorted_codes = sorted(codes)
                s = e = sorted_codes[0]
                for c in sorted_codes[1:]:
                    if c == e + 1:
                        e = c
                    else:
                        if s == e:
                            result.append(f"U+{s:04X}")
                        else:
                            result.append(f"U+{s:04X}-U+{e:04X}")
                        s = e = c
                if s == e:
                    result.append(f"U+{s:04X}")
                else:
                    result.append(f"U+{s:04X}-U+{e:04X}")
                return ", ".join(result)
            msg = (
                f"Range 0x{start:04X}-0x{end:04X} unsupported, missing characters: {format_range(unsupported_chars)}"
            )
            messages.append((msg, False))
        else:
            messages.append((f"Range 0x{start:04X}-0x{end:04X} fully supported.", True))
    block.set_status(messages)
    return all_supported

class LVGLFontConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LVGL Multi Font Converter")
        self.root.geometry("1000x750")
        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        # font name, size, bpp at top globally
        settings_fr = tk.Frame(container, pady=5, padx=5)
        settings_fr.pack(fill="x", padx=5, pady=5)

        tk.Label(settings_fr, text="Font Name:", width=12).pack(side="left")
        self.font_name_var = tk.StringVar()
        tk.Entry(settings_fr, textvariable=self.font_name_var, width=20).pack(side="left", padx=5)
        tk.Label(settings_fr, text="Font Size (px):", width=13).pack(side="left", padx=(15,0))
        self.font_size_var = tk.IntVar(value=16)
        tk.Spinbox(settings_fr, from_=8, to=72, textvariable=self.font_size_var, width=5).pack(side="left", padx=3)
        tk.Label(settings_fr, text="Bpp:", width=6).pack(side="left", padx=(15,0))
        self.bpp_var = tk.StringVar(value='1')
        ttk.Combobox(settings_fr, textvariable=self.bpp_var, values=['1', '2', '3', '4', '8'], width=3, state='readonly').pack(
            side="left", padx=3)

        # Scrollable block panel
        canvas_fr = tk.Frame(container)
        canvas_fr.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_fr)
        v_scrollbar = tk.Scrollbar(canvas_fr, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
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
        self.submit_btn.pack(side="top", pady=5, ipadx=20)

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
        block.frame.pack(fill="x", padx=5, pady=8)
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

        font_inputs = []
        for block in self.file_blocks:
            data = block.get_font_data()
            try:
                ranges = parse_individual_ranges(data["range"])
            except Exception:
                continue  # skip block if parsing fails
            codepoints = []
            for (start, end) in ranges:
                codepoints.extend(range(start, end + 1))
            font_inputs.append((data["font_path"], codepoints))

        try:
            out_file = generate_lvgl_font_c_multi(font_inputs, font_name, int(font_size), int(bpp))
            for block in self.file_blocks:
                block.set_status([("Font generated: " + os.path.basename(out_file), True)])
            messagebox.showinfo("Success", f"Generated font file:\n{out_file}")
        except Exception as e:
            for block in self.file_blocks:
                block.set_status([(f"Error during font generation: {e}", False)])

if __name__ == "__main__":
    root = tk.Tk()
    app = LVGLFontConverterApp(root)
    root.mainloop()

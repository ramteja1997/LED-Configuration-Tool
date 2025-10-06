import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import webbrowser
import freetype


def pack_4bpp(buffer, width, rows):
    # Packs a grayscale buffer (values 0-255) to 4bpp format (two pixels per byte)
    packed = []
    for y in range(rows):
        for x in range(0, width, 2):
            p1 = buffer[y * width + x]
            p2 = buffer[y * width + x + 1] if (x + 1) < width else 0
            n1 = int(round(p1 / 17.0))  # Map 0-255 to 0-15
            n2 = int(round(p2 / 17.0))
            packed.append((n1 << 4) | n2)
    return packed


class SingleFontConverter:
    def __init__(self, master, index):
        self.master = master
        self.index = index

        self.frame = tk.Frame(master, relief=tk.RIDGE, bd=2, padx=5, pady=5)
        self.frame.pack(pady=5, fill="x")

        row1 = 0
        tk.Label(self.frame, text=f"Font {index + 1} Name:").grid(row=row1, column=0, sticky="e")
        self.name_var = tk.StringVar()
        tk.Entry(self.frame, textvariable=self.name_var, width=20).grid(row=row1, column=1, sticky="w", padx=2)

        tk.Label(self.frame, text="TTF File:").grid(row=row1, column=2, sticky="e")
        self.path_entry = tk.Entry(self.frame, width=50)
        self.path_entry.grid(row=row1, column=3, sticky="w", padx=2)

        self.browse_btn = tk.Button(self.frame, text="Browse", command=self.browse_file)
        self.browse_btn.grid(row=row1, column=4, padx=2)

        row2 = 1
        tk.Label(self.frame, text="Font Size (px):").grid(row=row2, column=0, sticky="e", padx=2, pady=2)
        self.size_var = tk.StringVar()
        tk.Entry(self.frame, textvariable=self.size_var, width=5).grid(row=row2, column=1, sticky="w", padx=2)

        tk.Label(self.frame, text="Bpp:").grid(row=row2, column=2, sticky="e", padx=2, pady=2)
        self.bpp_var = tk.StringVar()
        ttk.Combobox(self.frame, textvariable=self.bpp_var, values=["1", "2", "3", "4", "8"], width=3, state="readonly").grid(row=row2, column=3, sticky="w", padx=2)

        row3 = 2
        tk.Label(self.frame, text="Unicode Range Start (hex):").grid(row=row3, column=0, sticky="e", padx=2, pady=2)
        self.uni_start_var = tk.StringVar()
        tk.Entry(self.frame, textvariable=self.uni_start_var, width=6).grid(row=row3, column=1, sticky="w", padx=2)

        tk.Label(self.frame, text="Unicode Range End (hex):").grid(row=row3, column=2, sticky="e", padx=2, pady=2)
        self.uni_end_var = tk.StringVar()
        tk.Entry(self.frame, textvariable=self.uni_end_var, width=6).grid(row=row3, column=3, sticky="w", padx=2)

        row4 = 3
        link = tk.Label(self.frame, text="Unicode Character Ranges", fg="blue", cursor="hand2")
        link.grid(row=row4, column=0, columnspan=5, sticky="w", padx=2, pady=2)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://jrgraphix.net/research/unicode.php"))

        self.convert_btn = tk.Button(self.frame, text="Generate .c File", command=self.convert_font)
        self.convert_btn.grid(row=row4 + 1, column=0, columnspan=5, pady=5)

        self.status_label = tk.Label(self.frame, text="", fg="green")
        self.status_label.grid(row=row4 + 2, column=0, columnspan=5, sticky="w", padx=2)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("TTF Font Files", "*.ttf")])
        if filename:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, filename)
            self.status_label.config(text="")

    def get_unique_filename(self, path):
        base, ext = os.path.splitext(path)
        counter = 1
        candidate = path
        while os.path.exists(candidate):
            candidate = f"{base}({counter}){ext}"
            counter += 1
        return candidate

    def convert_font(self):
        font_path = self.path_entry.get().strip()
        font_name = self.name_var.get().strip()
        bpp = self.bpp_var.get().strip()
        uni_start = self.uni_start_var.get().strip()
        uni_end = self.uni_end_var.get().strip()
        size = self.size_var.get().strip()

        if not font_name:
            messagebox.showerror("Error", "Please enter the font name.")
            return
        if not font_path or not os.path.isfile(font_path):
            messagebox.showerror("Error", f"Please select a valid TTF font file for {font_name}.")
            return
        if not size:
            messagebox.showerror("Error", "Please enter the font size (px).")
            return
        if not bpp:
            messagebox.showerror("Error", "Please select Bpp.")
            return
        if not uni_start or not uni_end:
            messagebox.showerror("Error", "Please enter both Unicode range start and end.")
            return

        try:
            size = int(size)
            bpp = int(bpp)
            uni_start = int(uni_start, 16)
            uni_end = int(uni_end, 16)
            if uni_end < uni_start:
                raise ValueError("Unicode range end must be >= start")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input data: {e}")
            return

        self.status_label.config(text="Processing...")
        self.master.update()

        try:
            output_file = self.generate_lvgl_font_c(font_path, font_name, size, bpp, uni_start, uni_end)
            self.status_label.config(text=f"Success: {os.path.basename(output_file)}")
            messagebox.showinfo("Success", f"Generated LVGL font C file:\n{output_file}")
        except Exception as e:
            self.status_label.config(text="Error")
            messagebox.showerror("Error", f"Failed to generate font:\n{e}")

    def write_glyph_bitmap_comment(self, file_obj, char_code):
        ch = chr(char_code)
        if ch == '"':
            ch = '\\"'
        elif ch == "\\":
            ch = "\\\\"
        file_obj.write(f"\n/* U+{char_code:04X} \"{ch}\" */\n\n")

    def generate_lvgl_font_c(self, font_path, font_name, size, bpp, start, end):
        face = freetype.Face(font_path)
        face.set_pixel_sizes(0, size)

        base_name = font_name
        initial_path = os.path.join(os.path.dirname(font_path), f"{base_name}.c")
        output_filename = self.get_unique_filename(initial_path)

        glyph_descs = []
        bitmap_offset = 0

        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(f"/*******************************************************************************\n")
            f.write(f"* Size: {size} px\n* Bpp: {bpp}\n")
            f.write(f"* Opts: --font {font_path} --size {size} --bpp {bpp} --no-compress --format lvgl\n")
            f.write(f"*******************************************************************************/\n\n")

            macro_name = base_name.upper().replace(" ", "_").replace("-", "_")
            f.write("#ifdef LV_LVGL_H_INCLUDE_SIMPLE\n#include \"lvgl.h\"\n#else\n#include \"lvgl/lvgl.h\"\n#endif\n\n")
            f.write(f"#ifndef {macro_name}\n#define {macro_name} 1\n#endif\n\n")

            f.write("/*-----------------\n* BITMAPS\n*----------------*/\n")
            f.write("static LV_ATTRIBUTE_LARGE_CONST const uint8_t glyph_bitmap[] = {\n")

            for code in range(start, end + 1):
                try:
                    if bpp == 1:
                        ft_flags = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO
                    else:
                        ft_flags = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL
                    face.load_char(chr(code), ft_flags)
                except:
                    glyph_descs.append((bitmap_offset, 0, 0, 0, 0, 0))
                    continue

                bmp = face.glyph.bitmap
                width, rows = bmp.width, bmp.rows
                buffer = bmp.buffer

                self.write_glyph_bitmap_comment(f, code)

                if bpp == 1:
                    row_bytes = (width + 7) // 8 if width != 0 else 0
                    for y in range(rows):
                        f.write("    ")
                        for b in range(row_bytes):
                            idx = y * row_bytes + b
                            if idx < len(buffer):
                                f.write(f"0x{buffer[idx]:02X}")
                            else:
                                f.write("0x00")
                            if not (y == rows - 1 and b == row_bytes - 1):
                                f.write(", ")
                        f.write(",\n")
                    bitmap_offset += rows * row_bytes
                else:
                    packed = pack_4bpp(buffer, width, rows)
                    for i in range(0, len(packed), 12):
                        f.write("    " + ", ".join(f"0x{b:02X}" for b in packed[i:i + 12]) + ",\n")
                    bitmap_offset += len(packed)

                glyph_descs.append((bitmap_offset, width, rows, face.glyph.advance.x // 64,
                                    face.glyph.bitmap_left, face.glyph.bitmap_top))

            f.write("};\n\n")

            f.write("static const lv_font_fmt_txt_glyph_dsc_t glyph_dsc[] = {\n")
            offset = 0
            for desc in glyph_descs:
                f.write(f"    {{ .bitmap_index = {offset}, .adv_w = {desc[3]}, .box_w = {desc[1]}, .box_h = {desc[2]}, .ofs_x = {desc[4]}, .ofs_y = {desc[5]} }},\n")
                if desc[1] > 0 and desc[2] > 0:
                    if bpp == 1:
                        cells = ((desc[1] + 7) // 8) * desc[2]
                    else:
                        cells = ((desc[1] + 1) // 2) * desc[2]
                    offset += cells
            f.write("};\n\n")

            f.write("static const uint16_t unicode_list_0[] = {\n")
            for code in range(start, end + 1):
                f.write(f"    0x{code:04X},\n")
            f.write("};\n\n")

            f.write("static const lv_font_fmt_txt_cmap_t cmaps[] = {\n")
            f.write("    {\n")
            f.write(f"        .range_start = 0x{start:04X}, .range_length = {end - start + 1}, .glyph_id_start = 1,\n")
            f.write("        .unicode_list = unicode_list_0, .glyph_id_ofs_list = NULL, .list_length = {0}, .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY\n".format(end - start + 1))
            f.write("    }\n};\n\n")

            f.write("static lv_font_fmt_txt_desc_t font_dsc = {\n")
            f.write("    .glyph_bitmap = glyph_bitmap,\n")
            f.write("    .glyph_dsc = glyph_dsc,\n")
            f.write("    .cmaps = cmaps,\n")
            f.write("    .kern_dsc = NULL, .kern_scale = 0,\n")
            f.write("    .cmap_num = 1, .bpp = %d, .kern_classes = 0, .bitmap_format = 0\n" % bpp)
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


class LVGLFontConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LVGL Multi Font Converter")
        self.root.geometry("950x700")

        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container)
        v_scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = tk.Scrollbar(container, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

        self._bind_mousewheel(self.canvas)

        for i in range(5):
            SingleFontConverter(self.scrollable_frame, i)

    def _bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        widget.bind_all("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind_all("<Button-5>", lambda e: widget.yview_scroll(1, "units"))
        widget.bind_all("<Shift-MouseWheel>", lambda e: widget.xview_scroll(int(-1 * (e.delta / 120)), "units"))


if __name__ == "__main__":
    root = tk.Tk()
    app = LVGLFontConverterApp(root)
    root.mainloop()

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import freetype

class SingleFontConverter:
    def __init__(self, master, index):
        self.master = master
        self.index = index

        self.frame = tk.Frame(master)
        self.frame.pack(pady=5, fill="x")

        self.label = tk.Label(self.frame, text=f"Font {index+1}:")
        self.label.pack(side="left", padx=5)

        self.entry = tk.Entry(self.frame, width=60)
        self.entry.pack(side="left", padx=5)

        self.browse_btn = tk.Button(self.frame, text="Browse", command=self.browse_file)
        self.browse_btn.pack(side="left", padx=5)

        self.convert_btn = tk.Button(self.frame, text="Generate .c", command=self.convert_font)
        self.convert_btn.pack(side="left", padx=5)

        self.status_label = tk.Label(self.frame, text="", fg="green")
        self.status_label.pack(side="left", padx=10)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("TTF Font Files", "*.ttf")])
        if filename:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, filename)
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
        font_path = self.entry.get()
        if not os.path.isfile(font_path):
            messagebox.showerror("Error", f"Please select a valid TTF font file for Font {self.index+1}.")
            return

        try:
            self.status_label.config(text="Processing...")
            self.master.update()

            output_path = self.generate_lvgl_font_c(font_path)
            self.status_label.config(text=f"Success: {os.path.basename(output_path)}")
            messagebox.showinfo("Done", f"LVGL font C file generated:\n{output_path}")
        except Exception as e:
            self.status_label.config(text="Error")
            messagebox.showerror("Error", f"Font {self.index+1} failed:\n{str(e)}")

    def format_bitmap_bytes(self, buffer):
        lines = []
        line = "    "
        for i, byte in enumerate(buffer):
            line += f"0x{byte:02X}, "
            if (i + 1) % 12 == 0:
                lines.append(line)
                line = "    "
        if line.strip():
            lines.append(line)
        return "\n".join(lines)

    def write_glyph_bitmap_comment(self, f, char_code):
        ch = chr(char_code)
        if ch == '"':
            ch = '\\"'
        elif ch == '\\':
            ch = '\\\\'
        f.write(f"\n/* U+{char_code:04X} \"{ch}\" */\n\n")

    def generate_lvgl_font_c(self, font_path):
        FONT_SIZE = 16
        CHAR_START = 0x20
        CHAR_END = 0x7F

        face = freetype.Face(font_path)
        face.set_pixel_sizes(0, FONT_SIZE)

        base_name = os.path.splitext(os.path.basename(font_path))[0]
        initial_path = os.path.join(os.path.dirname(font_path), f"{base_name}.c")
        output_filename = self.get_unique_filename(initial_path)

        glyph_bitmap = []
        glyph_dsc = []
        bitmap_index = 0

        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(f"/*******************************************************************************\n\n")
            f.write(f"* Size: {FONT_SIZE} px\n\n* Bpp: 1\n\n")
            f.write(f"* Opts: --font {font_path} --size {FONT_SIZE} --bpp 1 --no-compress --format lvgl\n\n")
            f.write(f"*******************************************************************************/\n\n")

            f.write("#ifdef LV_LVGL_H_INCLUDE_SIMPLE\n\n#include \"lvgl.h\"\n\n#else\n\n#include \"lvgl/lvgl.h\"\n\n#endif\n\n")

            macro_name = base_name.upper().replace(" ", "_").replace("-", "_")
            f.write(f"#ifndef {macro_name}\n#define {macro_name} 1\n\n#endif\n\n")

            f.write("/*-----------------\n\n* BITMAPS\n\n*----------------*/\n\n")
            f.write("/*Store the image of the glyphs*/\n\n")
            f.write("static LV_ATTRIBUTE_LARGE_CONST const uint8_t glyph_bitmap[] = {\n")

            for code in range(CHAR_START, CHAR_END + 1):
                try:
                    face.load_char(chr(code), freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
                except:
                    continue

                bmp = face.glyph.bitmap
                width = bmp.width
                rows = bmp.rows
                buffer = bmp.buffer

                self.write_glyph_bitmap_comment(f, code)

                row_bytes = (width + 7) // 8 if width != 0 else 0

                for y in range(rows):
                    f.write("    ")
                    for b in range(row_bytes):
                        idx = y * row_bytes + b
                        if idx < len(buffer):
                            f.write(f"0x{buffer[idx]:02X}")
                        else:
                            f.write("0x00")
                        if not (y == rows -1 and b == row_bytes -1):
                            f.write(", ")
                    f.write(",\n")

                adv = face.glyph.advance.x >> 6
                left = face.glyph.bitmap_left
                top = face.glyph.bitmap_top

                glyph_dsc.append({
                    "bitmap_index": bitmap_index,
                    "adv_w": adv * 16,
                    "box_w": width,
                    "box_h": rows,
                    "ofs_x": left,
                    "ofs_y": top,
                })

                bitmap_index += len(buffer)

            f.write("};\n\n")

            f.write("/*-----------------\n\n* GLYPH DESCRIPTION\n\n*----------------*/\n\n")
            f.write("static const lv_font_fmt_txt_glyph_dsc_t glyph_dsc[] = {\n")
            f.write("    {.bitmap_index = 0, .adv_w = 0, .box_w = 0, .box_h = 0, .ofs_x = 0, .ofs_y = 0},\n")

            for d in glyph_dsc:
                f.write(f"    {{.bitmap_index = {d['bitmap_index']}, .adv_w = {d['adv_w']}, .box_w = {d['box_w']}, .box_h = {d['box_h']}, .ofs_x = {d['ofs_x']}, .ofs_y = {d['ofs_y']}}},\n")

            f.write("};\n\n")

            f.write("/*-----------------\n\n* CHARACTER MAPPING\n\n*----------------*/\n\n")
            f.write("static const lv_font_fmt_txt_cmap_t cmaps[] = {\n")
            f.write("    {\n")
            f.write(f"        .range_start = {CHAR_START},\n")
            f.write(f"        .range_length = {CHAR_END - CHAR_START + 1},\n")
            f.write("        .glyph_id_start = 1,\n")
            f.write("        .unicode_list = NULL,\n")
            f.write("        .glyph_id_ofs_list = NULL,\n")
            f.write("        .list_length = 0,\n")
            f.write("        .type = LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY\n")
            f.write("    }\n")
            f.write("};\n\n")

            f.write("/*-----------------\n\n* FONT DESCRIPTION\n\n*----------------*/\n\n")
            f.write("static lv_font_fmt_txt_dsc_t font_dsc = {\n")
            f.write("    .glyph_bitmap = glyph_bitmap,\n")
            f.write("    .glyph_dsc = glyph_dsc,\n")
            f.write("    .cmaps = cmaps,\n")
            f.write(f"    .cmap_num = 1,\n")
            f.write("    .bpp = 1,\n")
            f.write("    .kern_dsc = NULL,\n")
            f.write("    .kern_scale = 0,\n")
            f.write("    .kern_classes = 0,\n")
            f.write("    .bitmap_format = 0\n")
            f.write("};\n\n")

            f.write("/*-----------------\n\n* PUBLIC FONT\n\n*----------------*/\n\n")
            f.write("lv_font_t lv_font_custom = {\n")
            f.write("    .get_glyph_dsc = lv_font_get_glyph_dsc_fmt_txt,\n")
            f.write("    .get_glyph_bitmap = lv_font_get_bitmap_fmt_txt,\n")
            f.write(f"    .line_height = {FONT_SIZE},\n")
            f.write("    .base_line = 0,\n")
            f.write("    .dsc = &font_dsc\n")
            f.write("};\n\n")

            f.write(f"#endif /* {macro_name} */\n")

        return output_filename

class LVGLFontConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-TTF to LVGL C Font Converter")
        self.root.geometry("850x450")

        self.converters = []
        for i in range(5):
            converter = SingleFontConverter(root, i)
            self.converters.append(converter)

if __name__ == "__main__":
    root = tk.Tk()
    app = LVGLFontConverterApp(root)
    root.mainloop()

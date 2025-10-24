import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import os

MAX_IMAGES = 10

class ImageConverterTool:
    def __init__(self, parent=None):
        self.selected_files = []
        self.entries = []

        if parent is None:
            self.root = tk.Tk()
            show_back = False
        else:
            self.root = tk.Toplevel(parent)  # initialize first!
            self.root.transient(parent)
            self.root.grab_set()
            self.root.focus_set()
            show_back = True

            if show_back:
                back_btn = tk.Button(
                    self.root,
                    text="Back",
                    font=("Helvetica", 12, "bold"),
                    command=self.root.destroy
                )
                back_btn.pack(anchor='nw', pady=(8, 0), padx=(8, 0))

        self.root.title("Centum Configuration Image Converter Tool")
        self.root.configure(bg="#e8e3f7")
        self.root.geometry('950x750')
        self.root.minsize(750, 400)
        self.root.resizable(True, True)

        self._setup_ui()

    def _setup_ui(self):
        tk.Label(self.root, text="Centum Configuration Image Converter Tool\n",
                 font=('Helvetica', 22, "bold"), bg="#e8e3f7").pack(pady=(18, 2))
        tk.Label(self.root, text="This tool converts BMP, JPG, JPEG, PNG, GIF, and ICO images into C arrays with RGB888 Color Format",
                 font=('Helvetica', 11), bg="#e8e3f7").pack(pady=(0, 14))

        below_header_frame = tk.Frame(self.root, bg="#e8e3f7")
        below_header_frame.pack(pady=(0,0))
        content_frame = tk.Frame(below_header_frame, bg="#e8e3f7")
        content_frame.pack(pady=(0,0))

        left_panel = tk.Frame(content_frame, bg="#e8e3f7")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, expand=False, anchor="n", padx=(0,18))

        tk.Button(left_panel, text="Select image file(s)", font=('Helvetica', 10),
                  command=self.select_files, width=17, height=1).pack(pady=(10, 20), anchor="w")
        tk.Button(left_panel, text="Convert", font=('Helvetica', 11, "bold"),
                  height=1, width=16, bg="#222", fg="#fff", command=self.convert_images).pack(pady=(0,5), anchor="w")

        right_panel = tk.Frame(content_frame, bg="#fff", bd=1, relief=tk.SOLID, width=480, height=500)
        right_panel.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 1), pady=1)
        right_panel.pack_propagate(False)
        self.canvas = tk.Canvas(right_panel, bg="#fff", highlightthickness=0, width=440, height=500)
        self.canvas.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=0, pady=0)

        self.files_container = tk.Frame(self.canvas, bg="#fff")
        self.canvas.create_window((0, 0), window=self.files_container, anchor='nw')

    class ImageEntry(tk.Frame):
        def __init__(self, parent, img_path, remove_callback):
            super().__init__(parent, bg="#f9f9f9", bd=1, relief=tk.SOLID, padx=2, pady=2)
            self.img_path = img_path
            self.remove_callback = remove_callback

            img = Image.open(img_path)
            img.thumbnail((48, 48))
            self.photo = ImageTk.PhotoImage(img)
            self.img_label = tk.Label(self, image=self.photo, bg="#f9f9f9")
            self.img_label.pack(side=tk.LEFT, padx=(2, 6))
            file_size = os.path.getsize(img_path)
            size_str = ImageConverterTool.human_size(file_size)
            filename = os.path.basename(img_path)
            path_label = tk.Label(
                self, text=f"{filename} ({size_str})", bg="#f9f9f9", font=('Helvetica', 10, 'normal'),
                width=36, anchor='w'
            )
            path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.remove_btn = tk.Button(self, text="✖", command=self.on_remove, bg="#ff4d4d", fg="white",
                                        font=('Helvetica', 11, 'bold'), relief=tk.FLAT, width=2, height=1, borderwidth=0)
            self.remove_btn.pack(side=tk.RIGHT, padx=8, pady=4)

        def on_remove(self):
            self.remove_callback(self.img_path)
            self.destroy()

    @staticmethod
    def format_c_array(arr, hex_fmt, per_line=5760):
        lines = []
        for i in range(0, len(arr), per_line):
            chunk = arr[i:i+per_line]
            line = ", ".join([hex_fmt.format(x) for x in chunk])
            lines.append(line)
        return ",\n".join(lines)

    @staticmethod
    def convert_image(image):
        img = image.convert('RGB')
        data = np.array(img)
        data = data[..., [2, 1, 0]]
        flat = data.flatten(order='C')
        dtype = 'uint8_t'
        hex_fmt = '0x{:02x}'
        return flat, dtype, hex_fmt

    def image_to_c_content(self, img_path):
        base = os.path.splitext(os.path.basename(img_path))[0]
        img = Image.open(img_path)
        arr, dtype, hex_fmt = self.convert_image(img)
        w, h = img.size
        color_format_str = "LV_COLOR_FORMAT_RGB888"
        array_name = f"{base}_map"
        struct_name = base
        bytes_per_pixel = 3
        data_size_expr = f"{w * h} * {bytes_per_pixel}"
        header = (
            "#ifdef __has_include\n"
            "#  if __has_include(\"lvgl.h\")\n"
            "#    ifndef LV_LVGL_H_INCLUDE_SIMPLE\n"
            "#      define LV_LVGL_H_INCLUDE_SIMPLE\n"
            "#    endif\n\n"
            "#  endif\n\n"
            "#endif\n\n"
            "#if defined(LV_LVGL_H_INCLUDE_SIMPLE)\n"
            "#  include \"lvgl.h\"\n"
            "#else\n"
            "#  include \"lvgl/lvgl.h\"\n"
            "#endif\n\n"
            "#ifndef LV_ATTRIBUTE_MEM_ALIGN\n"
            "#define LV_ATTRIBUTE_MEM_ALIGN\n"
            "#endif\n\n"
            f"#ifndef LV_ATTRIBUTE_IMAGE_{struct_name}\n"
            f"#define LV_ATTRIBUTE_IMAGE_{struct_name}\n"
            "#endif\n\n"
        )
        array_str = self.format_c_array(arr, hex_fmt, per_line=5760)
        data_array = (
            f"const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMAGE_{struct_name} {dtype} {array_name}[] = {{\n"
            f"{array_str}\n}};\n"
        )
        struct_str = (
            f"const lv_image_dsc_t {struct_name} = {{\n"
            f"  .header.cf = {color_format_str},\n"
            "  .header.magic = LV_IMAGE_HEADER_MAGIC,\n"
            f"  .header.w = {w},\n"
            f"  .header.h = {h},\n"
            f"  .data_size = {data_size_expr},\n"
            f"  .data = {array_name},\n"
            "};\n"
        )
        c_content = header + data_array + struct_str
        return base, c_content

    @staticmethod
    def human_size(num_bytes):
        for unit in ['B','KB','MB','GB']:
            if num_bytes < 1024.0:
                return "%3.1f %s" % (num_bytes, unit)
            num_bytes /= 1024.0
        return "%.2f TB" % num_bytes

    def add_image_entry(self, img_path):
        if img_path in self.selected_files or len(self.selected_files) >= MAX_IMAGES:
            return
        self.selected_files.append(img_path)
        entry = self.ImageEntry(self.files_container, img_path, self.remove_image)
        self.entries.append(entry)
        entry.pack(fill=tk.X, pady=2, padx=2)
        self.files_container.update_idletasks()

    def remove_image(self, img_path):
        if img_path in self.selected_files:
            self.selected_files.remove(img_path)
        self.files_container.update_idletasks()

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Image files", "*.png;*.bmp;*.jpg;*.jpeg;*.gif;*.ico")])
        files = [f for f in files if f not in self.selected_files]
        if len(files) + len(self.selected_files) > MAX_IMAGES:
            messagebox.showerror("Image Limit Exceeded", f"Selecting these files would exceed the limit of {MAX_IMAGES} images.")
            return
        for f in files:
            self.add_image_entry(f)

    def convert_images(self):
        if not self.selected_files:
            messagebox.showwarning("Missing Input", "Select image file(s).")
            return

        # Ask once for folder to save all files
        folder = filedialog.askdirectory(title="Select folder to save all .c files")
        if not folder:
            messagebox.showwarning("Save Cancelled", "Saving of files was cancelled.")
            return

        results = []
        for file_path in self.selected_files:
            base, c_content = self.image_to_c_content(file_path)
            c_path = os.path.join(folder, f"{base}.c")
            try:
                with open(c_path, "w") as f:
                    f.write(c_content)
                results.append(f"{os.path.basename(file_path)} → {c_path}")
            except Exception as e:
                messagebox.showerror("Error Saving File", f"Failed to save {c_path}:\n{str(e)}")

        if results:
            messagebox.showinfo("Conversion Completed", "The following files were converted:\n\n" + "\n".join(results))
        else:
            messagebox.showinfo("Conversion Completed", "No files were saved.")

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    tool = ImageConverterTool()
    tool.root.mainloop()

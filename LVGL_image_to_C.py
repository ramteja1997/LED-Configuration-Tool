import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import numpy as np
import os

COLOR_FORMATS = {
    "RGB565": "LV_COLOR_FORMAT_RGB565",
    "RGB565A8": "LV_COLOR_FORMAT_RGB565A8",
    "RGB888": "LV_COLOR_FORMAT_RGB888",
    "XRGB8888": "LV_COLOR_FORMAT_XRGB8888",
    "ARGB8888": "LV_COLOR_FORMAT_ARGB8888",
}

def format_c_array(arr, hex_fmt, per_line=5760):
    lines = []
    for i in range(0, len(arr), per_line):
        chunk = arr[i:i+per_line]
        line = ", ".join([hex_fmt.format(x) for x in chunk])
        lines.append(line)
    return ",\n".join(lines)

def convert_image(image, color_fmt):
    if color_fmt == "RGB888":
        img = image.convert('RGB')
        data = np.array(img)
        flat = data.flatten(order='C')
        dtype = 'uint8_t'
        hex_fmt = '0x{:02X}'
    else:
        img = image.convert('RGBA')
        data = np.array(img)
        if color_fmt == "RGB565":
            r = (data[..., 0] >> 3) & 0x1F
            g = (data[..., 1] >> 2) & 0x3F
            b = (data[..., 2] >> 3) & 0x1F
            arr = (r << 11) | (g << 5) | b
            arr = arr.byteswap()
            flat = arr.flatten(order='C')
            dtype = 'uint16_t'
            hex_fmt = '0x{:04X}'
        elif color_fmt == "RGB565A8":
            r = (data[..., 0] >> 3) & 0x1F
            g = (data[..., 1] >> 2) & 0x3F
            b = (data[..., 2] >> 3) & 0x1F
            arr = (r << 11) | (g << 5) | b
            arr = arr.byteswap()
            alpha = data[..., 3]
            flat = np.empty(arr.size * 2, dtype=np.uint8)
            flat[0::2] = arr.view(np.uint8)
            flat[1::2] = alpha.flatten(order='C')
            dtype = 'uint16_t'
            hex_fmt = '0x{:04X}'
        elif color_fmt == "XRGB8888":
            x = np.zeros(data.shape[:-1], dtype=np.uint8)
            rgb = data[..., :3]
            combined = np.stack((x, rgb[...,0], rgb[...,1], rgb[...,2]), axis=-1)
            flat = combined.flatten(order='C')
            dtype = 'uint8_t'
            hex_fmt = '0x{:02X}'
        elif color_fmt == "ARGB8888":
            combined = np.stack((data[...,3], data[...,0], data[...,1], data[...,2]), axis=-1)
            flat = combined.flatten(order='C')
            dtype = 'uint8_t'
            hex_fmt = '0x{:02X}'
        else:
            raise ValueError("Unknown format")
    return flat, dtype, hex_fmt

def image_to_c_file(img_path, color_fmt):
    base = os.path.splitext(os.path.basename(img_path))[0]
    img = Image.open(img_path)
    arr, dtype, hex_fmt = convert_image(img, color_fmt)
    w, h = img.size
    color_format_str = COLOR_FORMATS.get(color_fmt, "LV_COLOR_FORMAT_RGB888")
    array_name = f"{base}_map"
    struct_name = base
    if color_fmt == "RGB565":
        bytes_per_pixel = 2
    elif color_fmt == "RGB565A8":
        bytes_per_pixel = 3
    elif color_fmt == "RGB888":
        bytes_per_pixel = 3
    elif color_fmt in ["XRGB8888", "ARGB8888"]:
        bytes_per_pixel = 4
    else:
        bytes_per_pixel = 1
    data_size_expr = f"{w * h} * {bytes_per_pixel}"
    header = (
        "#ifdef __has_include\n"
        "#  if __has_include(\"lvgl.h\")\n"
        "#    ifndef LV_LVGL_H_INCLUDE_SIMPLE\n"
        "#      define LV_LVGL_H_INCLUDE_SIMPLE\n"
        "#    endif\n"
        "#  endif\n"
        "#endif\n"
        "#if defined(LV_LVGL_H_INCLUDE_SIMPLE)\n"
        "#  include \"lvgl.h\"\n"
        "#else\n"
        "#  include \"lvgl/lvgl.h\"\n"
        "#endif\n"
        "#ifndef LV_ATTRIBUTE_MEM_ALIGN\n"
        "#define LV_ATTRIBUTE_MEM_ALIGN\n"
        "#endif\n"
        f"#ifndef LV_ATTRIBUTE_IMAGE_{struct_name}\n"
        f"#define LV_ATTRIBUTE_IMAGE_{struct_name}\n"
        "#endif\n"
    )
    array_str = format_c_array(arr, hex_fmt, per_line=5760)
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
    fname = f"{base}.c"
    with open(fname, "w") as f:
        f.write(c_content)
    return fname

def select_files():
    files = filedialog.askopenfilenames(filetypes=[("Image files", "*.png;*.bmp;*.jpg;*.jpeg")])
    files_entry.config(state='normal')
    files_entry.delete(0, tk.END)
    base_names = [os.path.basename(f) for f in files]
    files_entry.insert(0, ", ".join(base_names))
    files_entry.config(state='readonly')
    global selected_files
    selected_files = files

def convert_images():
    if not selected_files or not color_var.get():
        messagebox.showwarning("Missing Input", "Select image file(s) and color format.")
        return
    for file_path in selected_files:
        fname = image_to_c_file(file_path, color_var.get())
        messagebox.showinfo("Done", f"Converted {os.path.basename(file_path)} to {fname}")

if __name__ == '__main__':
    selected_files = []
    root = tk.Tk()
    root.title("Centum Configuration Image Converter Tool")
    root.configure(bg="#e8e3f7")
    root.geometry('620x350')
    tk.Label(root, text="Centum Configuration Image Converter Tool", font=('Helvetica',18,"bold"), bg="#e8e3f7").pack(pady=(18,2))
    tk.Label(root, text="Convert BMP, JPG, PNG to C array for LVGL", font=('Helvetica',11), bg="#e8e3f7").pack()
    card_frame = tk.Frame(root, bg="#fff", bd=2, relief=tk.RIDGE)
    card_frame.pack(pady=28, padx=36, fill=tk.X)
    picker_frame = tk.Frame(card_frame, bg="#fff")
    picker_frame.pack(pady=16)
    files_entry = tk.Entry(picker_frame, width=46, font=('Helvetica',11))
    files_entry.pack(side=tk.LEFT, padx=(0,10))
    tk.Button(picker_frame, text="Select image file(s)", font=('Helvetica',11), command=select_files, width=16).pack(side=tk.LEFT)
    drop_label = tk.Label(card_frame, text="Color format", font=('Helvetica',13), bg="#fff")
    drop_label.pack(pady=(7,3))
    color_var = tk.StringVar()
    color_dropdown = tk.OptionMenu(card_frame, color_var, *COLOR_FORMATS.keys())
    color_dropdown.config(width=19, font=('Helvetica',11))
    color_dropdown.pack()
    tk.Button(card_frame, text="Convert", font=('Helvetica',13,"bold"), width=22, bg="#222", fg="#fff", command=convert_images).pack(pady=(18,12))
    root.mainloop()

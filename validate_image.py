import re
import numpy as np
from PIL import Image

def parse_lvgl_c_file(cfile_path):
    with open(cfile_path, 'r') as f:
        content = f.read()

    # Get pixel dimensions from struct (.header.w, .header.h)
    w = int(re.search(r'\.header\.w\s*=\s*(\d+),', content).group(1))
    h = int(re.search(r'\.header\.h\s*=\s*(\d+),', content).group(1))

    # Find the start of the image array and extract all hex bytes
    array_match = re.search(r'{([^}]*)}', content)
    hex_list = re.findall(r'0x[0-9a-fA-F]+', array_match.group(1))
    pixels = [int(b, 16) for b in hex_list]

    # Convert flat BGR array to RGB image
    arr = np.array(pixels, dtype=np.uint8)
    arr = arr.reshape((h, w, 3))
    arr = arr[..., [2, 1, 0]] # Convert BGR back to RGB

    return Image.fromarray(arr, 'RGB')

def save_jpeg_from_c(cfile_path, out_path):
    img = parse_lvgl_c_file(cfile_path)
    img.save(out_path, format='JPEG')
    print(f"Saved JPEG: {out_path}")

# Example usage
save_jpeg_from_c(r"C:\Users\Kushal\Downloads\car.c", 'output_image1.jpeg')

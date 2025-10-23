import tkinter as tk
from font2c_lvgl import FontConverterApp
from img2_c_lvgl import ImageConverterTool
from PIL import Image, ImageTk  # Optional but better for png/jpg
import os

def resource_path(relative_path):
    try:
        base_path =os.path.dirname(os.path.abspath(__file__))
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def open_font_converter():
    FontConverterApp(parent=root)

def open_image_converter():
    ImageConverterTool(parent=root)


root = tk.Tk()
root.title("Centum configuration Tool")
root.geometry("900x500")

header = tk.Label(root, text="Centum configuration Tool", font=("Segoe UI", 22, "bold"))
header.pack(pady=(8, 0))

subtitle = tk.Label(
    root,text="Easily convert fonts and images to C arrays for embedded and display project.",font=("Segoe UI", 12))
subtitle.pack(pady=(4, 18))

main_frame = tk.Frame(root, bg="#ffffff", bd=2, relief="ridge")
main_frame.pack(pady=18, padx=30)

# Load images for buttons
font_icon_img = Image.open(resource_path(os.path.join("icons", "FontConverterToC.jpg"))).resize((128,128), Image.Resampling.LANCZOS)
font_icon = ImageTk.PhotoImage(font_icon_img)

img_icon_img = Image.open(resource_path(os.path.join("icons", "ImageConverterToC.jpg"))).resize((128,128), Image.Resampling.LANCZOS)
img_icon = ImageTk.PhotoImage(img_icon_img)

font_btn = tk.Button(
    main_frame,
    text="Font converter to C",  # Unicode symbol instead of image (optionally use: image=font_icon, compound="top")
    font=("Segoe UI", 15),
    image=font_icon,
    compound='top',
    command=open_font_converter,
    relief='solid',
    padx=20, pady=16,  # These are pixels!
    anchor='center'
)
font_btn.grid(row=0, column=0, padx=(30,20), pady=18)

img_btn = tk.Button(
    main_frame,
    text="Image converter to C",  # Unicode symbol or: image=img_icon, compound="top"
    font=("Segoe UI", 15),
    image=img_icon,
    compound='top',
    command=open_image_converter,
    relief='solid',
    padx=20, pady=16,  # These are pixels!
    anchor='center'
)
img_btn.grid(row=0, column=1, padx=(20,30), pady=18)

# Keep reference to images so they aren't garbage collected
font_btn.image = font_icon
img_btn.image = img_icon

# Footer with version/info
footer = tk.Label(
    root,
    text="v1.0   |   For help, contact support@example.com",
    font=("Segoe UI", 9),
    fg="#888"
)
footer.pack(side="bottom", pady=8)

root.mainloop()
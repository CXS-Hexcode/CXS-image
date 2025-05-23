import os
import time
import base64
import csv
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import piexif
import exifread

def clean_value(value):
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8', errors='replace')
        except:
            return base64.b64encode(value).decode('utf-8')
    elif isinstance(value, (list, tuple)):
        return ', '.join(str(v) for v in value)
    elif isinstance(value, dict):
        return {k: clean_value(v) for k, v in value.items()}
    return str(value)

def convert_to_degrees(value):
    d, m, s = value
    return d[0] / d[1] + (m[0] / m[1]) / 60 + (s[0] / s[1]) / 3600

def extract_gps_coordinates(exif_data):
    try:
        gps_latitude = exif_data.get("GPSLatitude")
        gps_latitude_ref = exif_data.get("GPSLatitudeRef", "N")
        gps_longitude = exif_data.get("GPSLongitude")
        gps_longitude_ref = exif_data.get("GPSLongitudeRef", "E")

        if gps_latitude and gps_longitude:
            lat = convert_to_degrees(eval(gps_latitude))
            lon = convert_to_degrees(eval(gps_longitude))
            if gps_latitude_ref == 'S':
                lat = -lat
            if gps_longitude_ref == 'W':
                lon = -lon
            return {"GPS Coordinates": f"{lat}, {lon}"}
    except Exception as e:
        return {"GPS Conversion Error": str(e)}
    return {}

def extract_exif_piexif(image_path):
    data = {}
    try:
        exif_dict = piexif.load(image_path)
        for ifd in exif_dict:
            if isinstance(exif_dict[ifd], dict):
                for tag_id, raw in exif_dict[ifd].items():
                    name = piexif.TAGS[ifd].get(tag_id, {"name": str(tag_id)})["name"]
                    data[name] = clean_value(raw)
    except Exception as e:
        data["PIEXIF_ERROR"] = str(e)
    return data

def extract_exif_exifread(image_path, existing_keys):
    data = {}
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=True)
            for tag, value in tags.items():
                key = tag.split()[-1]
                if key not in existing_keys:
                    data[key] = clean_value(value)
    except Exception as e:
        data["EXIFREAD_ERROR"] = str(e)
    return data

def extract_image_info(image_path):
    data = {}
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            d = len(img.getbands())
            data['Dimensions'] = f"{w}x{h}"
            data['Width'] = w
            data['Height'] = h
            data['Color Depth'] = d
    except Exception as e:
        data["Image Error"] = str(e)
    return data

def extract_file_info(image_path):
    data = {}
    try:
        stats = os.stat(image_path)
        data['Filename'] = os.path.basename(image_path)
        data['File Type'] = os.path.splitext(image_path)[1]
        data['Created'] = time.ctime(stats.st_ctime)
        data['Modified'] = time.ctime(stats.st_mtime)
        data['Attributes'] = oct(stats.st_mode)
        data['Accessible'] = 'Yes' if os.access(image_path, os.R_OK) else 'No'
        data['Exists'] = 'Yes' if os.path.exists(image_path) else 'No'
    except Exception as e:
        data["File Info Error"] = str(e)
    return data

def get_all_exif(image_path):
    exif = {}
    exif.update(extract_exif_piexif(image_path))
    exif.update(extract_exif_exifread(image_path, exif.keys()))
    exif.update(extract_image_info(image_path))
    exif.update(extract_file_info(image_path))
    exif.update(extract_gps_coordinates(exif))
    return exif

def choose_image():
    types = [("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.tif"), ("All files", "*.*")]
    filename = filedialog.askopenfilename(filetypes=types)
    if filename:
        global current_image_path, current_exif_data
        current_image_path = filename
        current_exif_data = get_all_exif(filename)
        show_image_preview(filename)
        display_exif_data(current_exif_data)
        export_btn["state"] = "normal"
        copy_btn["state"] = "normal"

def display_exif_data(data):
    for widget in result_frame.winfo_children():
        widget.destroy()
    scroll = ttk.Scrollbar(result_frame)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    tree = ttk.Treeview(result_frame, columns=("Key", "Value"), show="headings",
                        yscrollcommand=scroll.set, style="Dark.Treeview")
    tree.heading("Key", text="Clé")
    tree.heading("Value", text="Valeur")
    tree.column("Key", width=200, anchor=tk.W)
    tree.column("Value", width=580, anchor=tk.W)
    for k in sorted(data):
        tree.insert('', 'end', values=(k, data[k]))
    tree.pack(fill=tk.BOTH, expand=True)
    scroll.config(command=tree.yview)

def export_csv():
    if not current_exif_data:
        messagebox.showinfo("Info", "Aucune image chargée.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if path:
        try:
            with open(path, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Key", "Value"])
                for k, v in current_exif_data.items():
                    writer.writerow([k, v])
            messagebox.showinfo("Fichier enregistré", f"Données exportées vers :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

def copy_to_clipboard():
    if not current_exif_data:
        messagebox.showinfo("Info", "Rien à copier.")
        return
    text = '\n'.join(f"{k}: {v}" for k, v in current_exif_data.items())
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    messagebox.showinfo("Copié", "Les données EXIF sont dans le presse-papier.")

def show_image_preview(path):
    try:
        with Image.open(path) as img:
            img.thumbnail((200, 200))
            img_tk = ImageTk.PhotoImage(img)
            preview_label.configure(image=img_tk, text="")
            preview_label.image = img_tk
    except:
        preview_label.configure(image='', text="Prévisualisation non dispo", foreground="#bdc3c7")

root = tk.Tk()
root.title("CXS-image")
root.geometry("900x650")
root.configure(bg="#1e272e")

current_image_path = ""
current_exif_data = {}

style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background="#1e272e")
style.configure("Dark.Treeview", background="#2c3e50", foreground="#ecf0f1",
                rowheight=25, fieldbackground="#2c3e50", font=("Segoe UI", 10))
style.configure("Dark.Treeview.Heading", background="#34495e", foreground="#f1c40f",
                font=("Segoe UI", 10, "bold"))
style.configure("TLabel", background="#1e272e", foreground="#ecf0f1", font=("Segoe UI", 11))

top_frame = ttk.Frame(root)
top_frame.pack(pady=10)

preview_label = ttk.Label(top_frame, text="Aucune image", background="#1e272e", foreground="#95a5a6")
preview_label.grid(row=0, column=0, padx=20)

btn_style = {
    "font": ("Segoe UI", 10, "bold"),
    "bg": "#2980b9",
    "fg": "white",
    "activebackground": "#3498db",
    "activeforeground": "white",
    "relief": tk.FLAT,
    "bd": 0,
    "cursor": "hand2",
    "highlightthickness": 0,
    "padx": 20,
    "pady": 10
}

button_frame = tk.Frame(top_frame, bg="#1e272e")
button_frame.grid(row=0, column=1, sticky="n")

tk.Button(button_frame, text="📂 Choisir une image", command=choose_image, **btn_style).pack(pady=5)

export_btn = tk.Button(button_frame, text="💾 Exporter CSV", command=export_csv, state="disabled", **btn_style)
export_btn.pack(pady=5)

copy_btn = tk.Button(button_frame, text="📤 Copier les données", command=copy_to_clipboard, state="disabled", **btn_style)
copy_btn.pack(pady=5)

result_frame = ttk.Frame(root)
result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

root.mainloop()

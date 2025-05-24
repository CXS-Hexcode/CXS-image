import sys
import os
import time
import base64
import csv
from PIL import Image, ImageQt
import piexif
import exifread

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QMessageBox, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QSizePolicy, QCheckBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import qdarkstyle

LABELS_MAP = {
    "Filename": "Nom du fichier",
    "File Type": "Type de fichier",
    "Created": "Créé le",
    "Modified": "Modifié le",
    "Accessible": "Accessible",
    "Exists": "Existe",
    "Width": "Largeur",
    "Height": "Hauteur",
    "Color Depth": "Profondeur de couleur",
    "Dimensions": "Dimensions",
    "GPS Coordinates": "Coordonnées GPS",
    "Make": "Marque",
    "Model": "Modèle",
    "DateTimeOriginal": "Date de prise de vue",
    "DateTime": "Date de modification",
    "FNumber": "Ouverture (f/)",
    "ExposureTime": "Temps d’exposition",
    "ISOSpeedRatings": "ISO",
    "Orientation": "Orientation",
    "ExposureProgram": "Programme d’exposition",
    "Software": "Logiciel"
}

CATEGORY_MAP = {
    "Nom du fichier": "Fichier",
    "Type de fichier": "Fichier",
    "Créé le": "Fichier",
    "Modifié le": "Fichier",
    "Accessible": "Fichier",
    "Existe": "Fichier",
    "Largeur": "Image",
    "Hauteur": "Image",
    "Profondeur de couleur": "Image",
    "Dimensions": "Image",
    "Coordonnées GPS": "GPS",
    "Date de prise de vue": "Prise de vue",
    "Date de modification": "Prise de vue",
    "Marque": "Appareil",
    "Modèle": "Appareil",
    "Ouverture (f/)": "Paramètres",
    "Temps d’exposition": "Paramètres",
    "ISO": "Paramètres",
    "Orientation": "Paramètres",
    "Programme d’exposition": "Paramètres",
    "Logiciel": "Appareil"
}

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

def format_exif_data(raw_exif):
    formatted = {}
    for k, v in raw_exif.items():
        label = LABELS_MAP.get(k, k)
        category = CATEGORY_MAP.get(label, "Autre")
        if category not in formatted:
            formatted[category] = []
        formatted[category].append((label, v))
    return formatted

class EXIFViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CXS-image PyQt5")
        self.resize(950, 700)

        self.image_path = ""
        self.exif_data = {}

        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()

        self.preview = QLabel("Aucune image")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(200, 200)
        self.preview.setStyleSheet("border: 1px solid #666;")
        self.preview.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Clé", "Valeur"])
        self.tree.setSortingEnabled(True)

        self.btn_open = QPushButton("📂 Choisir une image")
        self.btn_open.clicked.connect(self.open_image)

        self.btn_export = QPushButton("💾 Exporter CSV")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_csv)

        self.btn_copy = QPushButton("📤 Copier les données")
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.show_all_checkbox = QCheckBox("Afficher les données techniques")
        self.show_all_checkbox.setChecked(False)

        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_copy)
        btn_layout.addWidget(self.show_all_checkbox)

        layout.addWidget(self.preview)
        layout.addLayout(btn_layout)
        layout.addWidget(self.tree)

    def open_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Choisir une image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.gif)")
        if fname:
            self.image_path = fname
            self.exif_data = get_all_exif(fname)
            self.update_tree()
            self.show_preview()
            self.btn_export.setEnabled(True)
            self.btn_copy.setEnabled(True)

    def update_tree(self):
        self.tree.clear()
        grouped = format_exif_data(self.exif_data)
        for category, entries in grouped.items():
            if not self.show_all_checkbox.isChecked() and category == "Autre":
                continue
            cat_item = QTreeWidgetItem([category])
            for key, value in entries:
                QTreeWidgetItem(cat_item, [key, str(value)])
            self.tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)

    def export_csv(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Exporter en CSV", "", "CSV Files (*.csv)")
        if fname:
            try:
                with open(fname, "w", newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Catégorie", "Clé", "Valeur"])
                    grouped = format_exif_data(self.exif_data)
                    for cat, entries in grouped.items():
                        for key, val in entries:
                            writer.writerow([cat, key, val])
                QMessageBox.information(self, "Exporté", f"Exporté vers :\n{fname}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def copy_to_clipboard(self):
        if self.exif_data:
            grouped = format_exif_data(self.exif_data)
            text = ""
            for cat, entries in grouped.items():
                text += f"[{cat}]\n"
                for key, val in entries:
                    text += f"{key}: {val}\n"
                text += "\n"
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copié", "Les données EXIF sont dans le presse-papier.")

    def show_preview(self):
        try:
            pixmap = QPixmap(self.image_path)
            if pixmap.isNull():
                self.preview.setText("Erreur de prévisualisation")
            else:
                pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview.setPixmap(pixmap)
        except Exception as e:
            self.preview.setText(f"Erreur de prévisualisation: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = EXIFViewer()
    window.show()
    sys.exit(app.exec_())

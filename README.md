# 🖼️ CXS-image – Outil d’analyse EXIF avec interface graphique
<p align="center">
   <img src="CXS-exif.png" width="100%">

   
**CXS-image** est une application Python avec une interface élégante (Tkinter) qui permet d’extraire, visualiser et exporter toutes les métadonnées EXIF d’une image, y compris les **coordonnées GPS** si elles sont présentes.

---

## ⚙️ Fonctionnalités

- 🧠 Extraction complète des données EXIF :
  - Dimensions, format, profondeur de couleur
  - Métadonnées de fichier (création, modification, etc.)
  - Coordonnées GPS (latitude/longitude)
- 📂 Interface graphique moderne avec prévisualisation
- 📤 Export CSV des métadonnées
- 📋 Copie rapide des données dans le presse-papiers
- 📸 Prise en charge de nombreux formats d’image :  
  `.jpg`, `.jpeg`, `.tiff`, `.png`, `.bmp`, `.gif`

---

## 🧱 Prérequis

- Python 3.x  
- Modules nécessaires :

```bash
pip install pillow piexif exifread

```
# 🚀 Utilisation
Lance l'application :


python Get-Image-Exif.py```
Clique sur "📂 Choisir une image"

Visualise les métadonnées EXIF et, si présentes, les coordonnées GPS

Utilise les boutons pour :

💾 Exporter les données en CSV

📤 Copier les informations dans le presse-papiers


# 💡 Astuces
- Les fichiers PNG et GIF ne contiennent souvent pas de données EXIF.

- Le programme détecte automatiquement les erreurs de décodage EXIF.

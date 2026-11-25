import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

os.makedirs("qrs_generados", exist_ok=True)

USUARIOS = [
    ("USR01", "Josue Sifuentes", "Admin"),
    ("USR02", "Marco Galicia", "Admin"),
    ("USR03", "Felipe Gonzalez", "Recepcion"),
]

try:
    font = ImageFont.truetype("arial.ttf", 18)
except OSError:
    font = ImageFont.load_default()

for uid, nombre, rol in USUARIOS:
    contenido_qr = f"{uid}|{nombre}|{rol}"
    etiqueta = f"{uid} | {nombre} | {rol}"

    qr_img = qrcode.make(contenido_qr).convert("RGB")
    w, h = qr_img.size

    lienzo = Image.new("RGB", (w, h + 50), "white")
    lienzo.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(lienzo)
    bbox = draw.textbbox((0, 0), etiqueta, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((w - text_w) / 2, h + 10), etiqueta, fill="black", font=font)

    archivo = f"qrs_generados/{uid}_{nombre.replace(' ', '_')}.png"
    lienzo.save(archivo)
    print(f"Generado: {archivo}")
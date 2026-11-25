"""Foto de evidencia: reduce peso, elimina EXIF (puede traer GPS del domicilio) y sella fecha y coordenadas."""

from __future__ import annotations

import hashlib
import io

from PIL import Image, ImageDraw, ImageFont, ImageOps


def procesar(data: bytes, sello: str, max_px: int = 1280, calidad: int = 75) -> tuple[bytes, str]:
    """Devuelve (jpeg_bytes, descripcion). La descripción incluye una huella SHA-256 de integridad."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    img.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
    w, h = img.size

    try:
        fuente = ImageFont.load_default(size=max(12, w // 50))
    except TypeError:
        fuente = ImageFont.load_default()

    d = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = d.textbbox((0, 0), sello, font=fuente)
    alto_texto = y1 - y0
    ancho_franja = max(w, (x1 - x0) + 16)
    alto_franja = alto_texto + 16

    # Si el sello supera el ancho de la imagen, ampliamos ligeramente el lienzo inferior para que no se corte
    if ancho_franja > w:
        lienzo = Image.new("RGB", (ancho_franja, h + alto_franja), (15, 23, 42))
        lienzo.paste(img, (0, 0))
        img = lienzo
        w, h = img.size
        d = ImageDraw.Draw(img, "RGBA")
        y_top = h - alto_franja
    else:
        y_top = h - alto_franja

    d.rectangle([0, y_top, w, h], fill=(0, 0, 0, 165))
    d.text((8, y_top + 8), sello, fill=(255, 255, 255, 255), font=fuente)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=calidad, optimize=True)
    jpeg = out.getvalue()

    kb = max(1, len(jpeg) // 1024)
    huella = hashlib.sha256(jpeg).hexdigest()[:12]
    return jpeg, f"Foto comprimida · {kb} KB · sha256:{huella}"
"""v6 Cover — minimal-art обложка через Pillow. Никаких сетевых зависимостей."""

from __future__ import annotations

import hashlib
import random
from pathlib import Path


def make_cover(recipe: dict, out_png: str, size: int = 1500) -> dict:
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except Exception as e:
        return {"ok": False, "reason": f"Pillow missing: {e}"}
    title = recipe.get("title") or recipe.get("theme") or "ZS Track"
    h = hashlib.md5(title.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    rnd = random.Random(seed)
    palette = [
        [(15, 15, 20), (255, 90, 40), (255, 200, 60)],
        [(20, 8, 40), (180, 60, 200), (60, 220, 255)],
        [(6, 6, 6), (255, 40, 90), (255, 255, 255)],
        [(10, 30, 20), (0, 200, 120), (250, 230, 100)],
    ]
    bg, c1, c2 = rnd.choice(palette)
    img = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(img)
    # диагональные полосы
    for i in range(0, size, 28):
        d.line([(0, i), (i, 0)], fill=c1, width=2)
    d.rectangle(
        [size // 12, size // 2 - size // 8, size - size // 12, size // 2 + size // 8],
        fill=c2,
    )
    try:
        font = ImageFont.truetype("arialbd.ttf", size // 10)
    except Exception:
        font = ImageFont.load_default()
    txt = title[:22].upper()
    bbox = d.textbbox((0, 0), txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - tw) // 2, (size - th) // 2), txt, fill=bg, font=font)
    img = img.filter(ImageFilter.SMOOTH)
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, "PNG")
    return {"ok": True, "path": out_png}

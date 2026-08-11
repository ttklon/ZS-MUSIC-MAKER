"""
ZS Music Maker v10 — Cover Art Generator
==========================================
Автогенерация обложки трека (ТЗ 3.12, 32 «cover.png»).

БЕЗ нейросети, только PIL — гарантированно работает офлайн и на слабом
железе. Стили: minimal, gradient, glitch, retro, neon, chrome.

Автор выбирается из recipe.json или задаётся вручную.
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    PIL_OK = True
except Exception:
    PIL_OK = False


STYLE_PALETTES = {
    "minimal": [((20, 20, 25), (240, 240, 245))],
    "gradient": [
        ((255, 94, 77), (255, 175, 64)),
        ((94, 33, 175), (33, 150, 243)),
        ((0, 200, 150), (10, 20, 40)),
    ],
    "glitch": [((255, 0, 100), (0, 255, 200)), ((20, 0, 40), (255, 60, 60))],
    "retro": [((255, 200, 100), (60, 30, 60))],
    "neon": [((15, 15, 40), (255, 0, 200)), ((0, 20, 50), (0, 255, 255))],
    "chrome": [((30, 30, 30), (200, 200, 220))],
}


def generate(
    title: str,
    artist: str,
    out_path: str,
    style: str = "gradient",
    size: int = 1400,
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Генерирует обложку 1400x1400 (Spotify/Apple Music стандарт).
    """
    if not PIL_OK:
        return {"ok": False, "reason": "PIL not available"}

    if seed is None:
        seed = int(hashlib.md5(f"{title}{artist}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    palettes = STYLE_PALETTES.get(style, STYLE_PALETTES["gradient"])
    c1, c2 = rng.choice(palettes)

    img = Image.new("RGB", (size, size), c1)
    _fill_gradient(img, c1, c2)

    # Стилевые доп. эффекты
    if style == "glitch":
        img = _apply_glitch(img, rng)
    elif style == "neon":
        img = _apply_neon_grid(img, rng, c2)
    elif style == "retro":
        img = _apply_sun(img, rng)
    elif style == "chrome":
        img = _apply_chrome(img, rng)

    # Текст: артист сверху мелко, тайтл — крупно по центру
    draw = ImageDraw.Draw(img)
    font_big = _load_font(int(size * 0.09))
    font_sml = _load_font(int(size * 0.035))

    artist_txt = (artist or "ZS").upper()[:24]
    title_txt = (title or "Untitled").upper()

    _center_text(
        draw,
        artist_txt,
        (size // 2, int(size * 0.12)),
        font_sml,
        fill=_contrast(c2),
        letter_spacing=int(size * 0.015),
    )

    lines = _wrap_title(title_txt, max_chars=14)
    total_h = len(lines) * int(size * 0.11)
    y = (size - total_h) // 2
    for line in lines:
        _center_text(
            draw,
            line,
            (size // 2, y),
            font_big,
            fill=_contrast(c1),
            stroke_fill=_contrast(c2),
            stroke_width=2,
        )
        y += int(size * 0.11)

    # Нижний блок: MM ZS watermark
    _center_text(
        draw,
        "MM · ZS MUSIC MAKER",
        (size // 2, int(size * 0.94)),
        font_sml,
        fill=_contrast(c2),
        letter_spacing=int(size * 0.01),
    )

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return {"ok": True, "path": out_path, "style": style, "seed": seed, "size": size}


def _fill_gradient(img: Image.Image, c1, c2) -> None:
    w, h = img.size
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)


def _apply_glitch(img, rng):
    w, h = img.size
    for _ in range(rng.randint(5, 12)):
        y = rng.randint(0, h - 20)
        dx = rng.randint(-40, 40)
        strip = img.crop((0, y, w, y + rng.randint(5, 30)))
        img.paste(strip, (dx, y))
    return img


def _apply_neon_grid(img, rng, colour):
    d = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    step = max(40, w // 20)
    a = 90
    for x in range(0, w, step):
        d.line((x, 0, x, h), fill=(*colour, a), width=1)
    for y in range(0, h, step):
        d.line((0, y, w, y), fill=(*colour, a), width=1)
    return img


def _apply_sun(img, rng):
    d = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    cx, cy = w // 2, int(h * 0.62)
    for r in range(min(w, h) // 3, 0, -6):
        alpha = int(255 * (1 - r / (min(w, h) // 3)) * 0.15)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 220, 90, alpha))
    return img


def _apply_chrome(img, rng):
    img = img.filter(ImageFilter.GaussianBlur(radius=3))
    return img


def _load_font(size: int):
    candidates = [
        "arialbd.ttf",
        "Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _center_text(
    draw,
    text,
    xy,
    font,
    fill=(255, 255, 255),
    stroke_fill=None,
    stroke_width=0,
    letter_spacing=0,
):
    if letter_spacing > 0:
        # рисуем побуквенно
        total_w = 0
        widths = []
        for ch in text:
            bbox = draw.textbbox((0, 0), ch, font=font)
            widths.append(bbox[2] - bbox[0])
            total_w += bbox[2] - bbox[0] + letter_spacing
        total_w -= letter_spacing
        x = xy[0] - total_w // 2
        y = xy[1]
        for ch, cw in zip(text, widths):
            draw.text(
                (x, y),
                ch,
                font=font,
                fill=fill,
                stroke_fill=stroke_fill,
                stroke_width=stroke_width,
            )
            x += cw + letter_spacing
    else:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(
            (xy[0] - w // 2, xy[1] - h // 2),
            text,
            font=font,
            fill=fill,
            stroke_fill=stroke_fill,
            stroke_width=stroke_width,
        )


def _wrap_title(text: str, max_chars: int = 14):
    words = text.split()
    out, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out or [text[:max_chars]]


def _contrast(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return (20, 20, 25) if lum > 140 else (245, 245, 250)


if __name__ == "__main__":
    if PIL_OK:
        r = generate(
            "Turkish Nights", "ZS", "output/covers/test_cover.png", style="neon"
        )
        print(r)
    else:
        print("PIL missing")

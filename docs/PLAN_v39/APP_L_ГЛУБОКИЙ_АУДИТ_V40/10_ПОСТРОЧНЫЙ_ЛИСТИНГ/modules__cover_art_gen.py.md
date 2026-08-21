# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/cover_art_gen.py`

**Всего строк:** 248

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 140 | 56.5 |
| blank | 39 | 15.7 |
| branch | 15 | 6.0 |
| docstring | 11 | 4.4 |
| def | 10 | 4.0 |
| loop | 10 | 4.0 |
| return | 9 | 3.6 |
| import | 7 | 2.8 |
| comment | 5 | 2.0 |
| try_block | 2 | 0.8 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Cover Art Generator
    3 [docstring ] ==========================================
    4 [docstring ] Автогенерация обложки трека (ТЗ 3.12, 32 «cover.png»).
    5 [blank     ] 
    6 [docstring ] БЕЗ нейросети, только PIL — гарантированно работает офлайн и на слабом
    7 [docstring ] железе. Стили: minimal, gradient, glitch, retro, neon, chrome.
    8 [blank     ] 
    9 [docstring ] Автор выбирается из recipe.json или задаётся вручную.
   10 [docstring ] """
   11 [blank     ] 
   12 [import    ] from __future__ import annotations
   13 [blank     ] 
   14 [import    ] import hashlib
   15 [import    ] import random
   16 [import    ] from pathlib import Path
   17 [import    ] from typing import Any
   18 [blank     ] 
   19 [try_block ] try:
   20 [import    ]     from PIL import Image, ImageDraw, ImageFilter, ImageFont
   21 [blank     ] 
   22 [code      ]     PIL_OK = True
   23 [try_block ] except Exception:
   24 [code      ]     PIL_OK = False
   25 [blank     ] 
   26 [blank     ] 
   27 [code      ] STYLE_PALETTES = {
   28 [code      ]     "minimal": [((20, 20, 25), (240, 240, 245))],
   29 [code      ]     "gradient": [
   30 [code      ]         ((255, 94, 77), (255, 175, 64)),
   31 [code      ]         ((94, 33, 175), (33, 150, 243)),
   32 [code      ]         ((0, 200, 150), (10, 20, 40)),
   33 [code      ]     ],
   34 [code      ]     "glitch": [((255, 0, 100), (0, 255, 200)), ((20, 0, 40), (255, 60, 60))],
   35 [code      ]     "retro": [((255, 200, 100), (60, 30, 60))],
   36 [code      ]     "neon": [((15, 15, 40), (255, 0, 200)), ((0, 20, 50), (0, 255, 255))],
   37 [code      ]     "chrome": [((30, 30, 30), (200, 200, 220))],
   38 [code      ] }
   39 [blank     ] 
   40 [blank     ] 
   41 [def       ] def generate(
   42 [code      ]     title: str,
   43 [code      ]     artist: str,
   44 [code      ]     out_path: str,
   45 [code      ]     style: str = "gradient",
   46 [code      ]     size: int = 1400,
   47 [code      ]     seed: int | None = None,
   48 [code      ] ) -> dict[str, Any]:
   49 [docstring ]     """
   50 [docstring ]     Генерирует обложку 1400x1400 (Spotify/Apple Music стандарт).
   51 [docstring ]     """
   52 [branch    ]     if not PIL_OK:
   53 [return    ]         return {"ok": False, "reason": "PIL not available"}
   54 [blank     ] 
   55 [branch    ]     if seed is None:
   56 [code      ]         seed = int(hashlib.md5(f"{title}{artist}".encode()).hexdigest()[:8], 16)
   57 [code      ]     rng = random.Random(seed)
   58 [code      ]     palettes = STYLE_PALETTES.get(style, STYLE_PALETTES["gradient"])
   59 [code      ]     c1, c2 = rng.choice(palettes)
   60 [blank     ] 
   61 [code      ]     img = Image.new("RGB", (size, size), c1)
   62 [code      ]     _fill_gradient(img, c1, c2)
   63 [blank     ] 
   64 [comment   ]     # Стилевые доп. эффекты
   65 [branch    ]     if style == "glitch":
   66 [code      ]         img = _apply_glitch(img, rng)
   67 [branch    ]     elif style == "neon":
   68 [code      ]         img = _apply_neon_grid(img, rng, c2)
   69 [branch    ]     elif style == "retro":
   70 [code      ]         img = _apply_sun(img, rng)
   71 [branch    ]     elif style == "chrome":
   72 [code      ]         img = _apply_chrome(img, rng)
   73 [blank     ] 
   74 [comment   ]     # Текст: артист сверху мелко, тайтл — крупно по центру
   75 [code      ]     draw = ImageDraw.Draw(img)
   76 [code      ]     font_big = _load_font(int(size * 0.09))
   77 [code      ]     font_sml = _load_font(int(size * 0.035))
   78 [blank     ] 
   79 [code      ]     artist_txt = (artist or "ZS").upper()[:24]
   80 [code      ]     title_txt = (title or "Untitled").upper()
   81 [blank     ] 
   82 [code      ]     _center_text(
   83 [code      ]         draw,
   84 [code      ]         artist_txt,
   85 [code      ]         (size // 2, int(size * 0.12)),
   86 [code      ]         font_sml,
   87 [code      ]         fill=_contrast(c2),
   88 [code      ]         letter_spacing=int(size * 0.015),
   89 [code      ]     )
   90 [blank     ] 
   91 [code      ]     lines = _wrap_title(title_txt, max_chars=14)
   92 [code      ]     total_h = len(lines) * int(size * 0.11)
   93 [code      ]     y = (size - total_h) // 2
   94 [loop      ]     for line in lines:
   95 [code      ]         _center_text(
   96 [code      ]             draw,
   97 [code      ]             line,
   98 [code      ]             (size // 2, y),
   99 [code      ]             font_big,
  100 [code      ]             fill=_contrast(c1),
  101 [code      ]             stroke_fill=_contrast(c2),
  102 [code      ]             stroke_width=2,
  103 [code      ]         )
  104 [code      ]         y += int(size * 0.11)
  105 [blank     ] 
  106 [comment   ]     # Нижний блок: MM ZS watermark
  107 [code      ]     _center_text(
  108 [code      ]         draw,
  109 [code      ]         "MM · ZS MUSIC MAKER",
  110 [code      ]         (size // 2, int(size * 0.94)),
  111 [code      ]         font_sml,
  112 [code      ]         fill=_contrast(c2),
  113 [code      ]         letter_spacing=int(size * 0.01),
  114 [code      ]     )
  115 [blank     ] 
  116 [code      ]     Path(out_path).parent.mkdir(parents=True, exist_ok=True)
  117 [code      ]     img.save(out_path, "PNG", optimize=True)
  118 [return    ]     return {"ok": True, "path": out_path, "style": style, "seed": seed, "size": size}
  119 [blank     ] 
  120 [blank     ] 
  121 [def       ] def _fill_gradient(img: Image.Image, c1, c2) -> None:
  122 [code      ]     w, h = img.size
  123 [code      ]     px = img.load()
  124 [loop      ]     for y in range(h):
  125 [code      ]         t = y / max(1, h - 1)
  126 [code      ]         r = int(c1[0] + (c2[0] - c1[0]) * t)
  127 [code      ]         g = int(c1[1] + (c2[1] - c1[1]) * t)
  128 [code      ]         b = int(c1[2] + (c2[2] - c1[2]) * t)
  129 [loop      ]         for x in range(w):
  130 [code      ]             px[x, y] = (r, g, b)
  131 [blank     ] 
  132 [blank     ] 
  133 [def       ] def _apply_glitch(img, rng):
  134 [code      ]     w, h = img.size
  135 [loop      ]     for _ in range(rng.randint(5, 12)):
  136 [code      ]         y = rng.randint(0, h - 20)
  137 [code      ]         dx = rng.randint(-40, 40)
  138 [code      ]         strip = img.crop((0, y, w, y + rng.randint(5, 30)))
  139 [code      ]         img.paste(strip, (dx, y))
  140 [return    ]     return img
  141 [blank     ] 
  142 [blank     ] 
  143 [def       ] def _apply_neon_grid(img, rng, colour):
  144 [code      ]     d = ImageDraw.Draw(img, "RGBA")
  145 [code      ]     w, h = img.size
  146 [code      ]     step = max(40, w // 20)
  147 [code      ]     a = 90
  148 [loop      ]     for x in range(0, w, step):
  149 [code      ]         d.line((x, 0, x, h), fill=(*colour, a), width=1)
  150 [loop      ]     for y in range(0, h, step):
  151 [code      ]         d.line((0, y, w, y), fill=(*colour, a), width=1)
  152 [return    ]     return img
  153 [blank     ] 
  154 [blank     ] 
  155 [def       ] def _apply_sun(img, rng):
  156 [code      ]     d = ImageDraw.Draw(img, "RGBA")
  157 [code      ]     w, h = img.size
  158 [code      ]     cx, cy = w // 2, int(h * 0.62)
  159 [loop      ]     for r in range(min(w, h) // 3, 0, -6):
  160 [code      ]         alpha = int(255 * (1 - r / (min(w, h) // 3)) * 0.15)
  161 [code      ]         d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 220, 90, alpha))
  162 [return    ]     return img
  163 [blank     ] 
  164 [blank     ] 
  165 [def       ] def _apply_chrome(img, rng):
  166 [code      ]     img = img.filter(ImageFilter.GaussianBlur(radius=3))
  167 [return    ]     return img
  168 [blank     ] 
  169 [blank     ] 
  170 [def       ] def _load_font(size: int):
  171 [comment   ]     # v39.4 (ШАГ 002): hardcoded C:\Windows\Fonts убран — единый font_utils
  172 [import    ]     from app.core.font_utils import load_pil_font
  173 [return    ]     return load_pil_font(size, bold=True)
  174 [blank     ] 
  175 [blank     ] 
  176 [def       ] def _center_text(
  177 [code      ]     draw,
  178 [code      ]     text,
  179 [code      ]     xy,
  180 [code      ]     font,
  181 [code      ]     fill=(255, 255, 255),
  182 [code      ]     stroke_fill=None,
  183 [code      ]     stroke_width=0,
  184 [code      ]     letter_spacing=0,
  185 [code      ] ):
  186 [branch    ]     if letter_spacing > 0:
  187 [comment   ]         # рисуем побуквенно
  188 [code      ]         total_w = 0
  189 [code      ]         widths = []
  190 [loop      ]         for ch in text:
  191 [code      ]             bbox = draw.textbbox((0, 0), ch, font=font)
  192 [code      ]             widths.append(bbox[2] - bbox[0])
  193 [code      ]             total_w += bbox[2] - bbox[0] + letter_spacing
  194 [code      ]         total_w -= letter_spacing
  195 [code      ]         x = xy[0] - total_w // 2
  196 [code      ]         y = xy[1]
  197 [loop      ]         for ch, cw in zip(text, widths):
  198 [code      ]             draw.text(
  199 [code      ]                 (x, y),
  200 [code      ]                 ch,
  201 [code      ]                 font=font,
  202 [code      ]                 fill=fill,
  203 [code      ]                 stroke_fill=stroke_fill,
  204 [code      ]                 stroke_width=stroke_width,
  205 [code      ]             )
  206 [code      ]             x += cw + letter_spacing
  207 [branch    ]     else:
  208 [code      ]         bbox = draw.textbbox((0, 0), text, font=font)
  209 [code      ]         w = bbox[2] - bbox[0]
  210 [code      ]         h = bbox[3] - bbox[1]
  211 [code      ]         draw.text(
  212 [code      ]             (xy[0] - w // 2, xy[1] - h // 2),
  213 [code      ]             text,
  214 [code      ]             font=font,
  215 [code      ]             fill=fill,
  216 [code      ]             stroke_fill=stroke_fill,
  217 [code      ]             stroke_width=stroke_width,
  218 [code      ]         )
  219 [blank     ] 
  220 [blank     ] 
  221 [def       ] def _wrap_title(text: str, max_chars: int = 14):
  222 [code      ]     words = text.split()
  223 [code      ]     out, cur = [], ""
  224 [loop      ]     for w in words:
  225 [branch    ]         if len(cur) + len(w) + 1 <= max_chars:
  226 [code      ]             cur = (cur + " " + w).strip()
  227 [branch    ]         else:
  228 [branch    ]             if cur:
  229 [code      ]                 out.append(cur)
  230 [code      ]             cur = w
  231 [branch    ]     if cur:
  232 [code      ]         out.append(cur)
  233 [return    ]     return out or [text[:max_chars]]
  234 [blank     ] 
  235 [blank     ] 
  236 [def       ] def _contrast(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
  237 [code      ]     lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
  238 [return    ]     return (20, 20, 25) if lum > 140 else (245, 245, 250)
  239 [blank     ] 
  240 [blank     ] 
  241 [branch    ] if __name__ == "__main__":
  242 [branch    ]     if PIL_OK:
  243 [code      ]         r = generate(
  244 [code      ]             "Turkish Nights", "ZS", "output/covers/test_cover.png", style="neon"
  245 [code      ]         )
  246 [code      ]         print(r)
  247 [branch    ]     else:
  248 [code      ]         print("PIL missing")
```
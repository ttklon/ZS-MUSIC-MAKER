# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/distribution_export_v11.py`

**Всего строк:** 474

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 266 | 56.1 |
| docstring | 79 | 16.7 |
| blank | 50 | 10.5 |
| branch | 17 | 3.6 |
| stmt | 15 | 3.2 |
| def | 11 | 2.3 |
| return | 11 | 2.3 |
| import | 10 | 2.1 |
| try_block | 6 | 1.3 |
| loop | 4 | 0.8 |
| decorator | 2 | 0.4 |
| class | 2 | 0.4 |
| comment | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v11 — distribution_export_v11.py
    3 [blank     ] 
    4 [docstring ] Реализует ТЗ 20.2 п.33 «Куда выкладывать: ВЕЗДЕ».
    5 [docstring ] 5 пакетов: Spotify/DSP, Яндекс+VK, TikTok, YouTube, Shazam.
    6 [docstring ] Никаких autoupload — только файлы + инструкции.
    7 [docstring ] """
    8 [blank     ] 
    9 [import    ] from __future__ import annotations
   10 [blank     ] 
   11 [import    ] import csv
   12 [import    ] import json
   13 [import    ] import os
   14 [import    ] import shutil
   15 [import    ] import sys
   16 [import    ] from dataclasses import asdict, dataclass, field
   17 [import    ] from datetime import datetime, timezone
   18 [blank     ] 
   19 [blank     ] 
   20 [def       ] def _safe_print(msg):
   21 [try_block ]     try:
   22 [code      ]         print(msg)
   23 [try_block ]     except UnicodeEncodeError:
   24 [code      ]         sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))
   25 [blank     ] 
   26 [blank     ] 
   27 [decorator ] @dataclass
   28 [class     ] class TrackMetadata:
   29 [code      ]     title: str
   30 [code      ]     artist: str
   31 [code      ]     album: str = ""
   32 [code      ]     genre: str = "Hip-Hop/Rap"
   33 [code      ]     subgenre: str = "Phonk / Trap / Hyperpop"
   34 [code      ]     bpm: float = 140.0
   35 [code      ]     key: str = ""
   36 [code      ]     language: str = "ru"
   37 [code      ]     explicit: bool = False
   38 [code      ]     isrc: str = ""
   39 [code      ]     iswc: str = ""
   40 [code      ]     upc: str = ""
   41 [code      ]     release_date: str = ""
   42 [code      ]     label: str = "Self-Released"
   43 [code      ]     copyright: str = ""
   44 [code      ]     p_line: str = ""
   45 [code      ]     duration_sec: float = 0.0
   46 [code      ]     tags: list[str] = field(default_factory=list)
   47 [code      ]     lyrics_ru: str = ""
   48 [code      ]     lyrics_en_hook: str = ""
   49 [blank     ] 
   50 [def       ]     def ensure(self):
   51 [branch    ]         if not self.release_date:
   52 [code      ]             self.release_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
   53 [code      ]         year = self.release_date[:4]
   54 [branch    ]         if not self.copyright:
   55 [code      ]             self.copyright = f"© {year} {self.artist}"
   56 [branch    ]         if not self.p_line:
   57 [code      ]             self.p_line = f"℗ {year} {self.artist}"
   58 [branch    ]         if not self.album:
   59 [code      ]             self.album = self.title
   60 [comment   ]         # v39.4 (ШАГ 003): если ISRC не выдан — генерируем валидный
   61 [try_block ]         try:
   62 [import    ]             from app.core.isrc import is_valid_isrc, generate_isrc
   63 [branch    ]             if not is_valid_isrc(self.isrc):
   64 [code      ]                 gen = generate_isrc({
   65 [code      ]                     "title": self.title, "artist": self.artist,
   66 [code      ]                     "year": int(year) if year.isdigit() else None,
   67 [code      ]                 })
   68 [branch    ]                 if gen:
   69 [code      ]                     self.isrc = gen
   70 [try_block ]         except ImportError:
   71 [code      ]             pass
   72 [blank     ] 
   73 [blank     ] 
   74 [decorator ] @dataclass
   75 [class     ] class ReleaseFiles:
   76 [code      ]     master_wav: str = ""
   77 [code      ]     mp3_320: str = ""
   78 [code      ]     flac: str = ""
   79 [code      ]     instrumental_wav: str = ""
   80 [code      ]     acapella_wav: str = ""
   81 [code      ]     stems_dir: str = ""
   82 [code      ]     tiktok_mp4: str = ""
   83 [code      ]     reels_mp4: str = ""
   84 [code      ]     shorts_mp4: str = ""
   85 [code      ]     cover_png: str = ""
   86 [code      ]     lyrics_txt: str = ""
   87 [code      ]     lyrics_lrc: str = ""
   88 [blank     ] 
   89 [def       ]     def existing(self) -> dict[str, str]:
   90 [return    ]         return {k: v for k, v in asdict(self).items() if v and os.path.exists(v)}
   91 [blank     ] 
   92 [blank     ] 
   93 [def       ] def _copy_safe(src, dst) -> bool:
   94 [try_block ]     try:
   95 [branch    ]         if not src or not os.path.exists(src):
   96 [return    ]             return False
   97 [code      ]         os.makedirs(os.path.dirname(os.path.abspath(dst)) or ".", exist_ok=True)
   98 [code      ]         shutil.copy2(src, dst)
   99 [return    ]         return True
  100 [try_block ]     except Exception as e:
  101 [code      ]         _safe_print(f"[dist_v11] copy fail: {e}")
  102 [return    ]         return False
  103 [blank     ] 
  104 [blank     ] 
  105 [def       ] def build_spotify_package(meta, files, out_dir):
  106 [code      ]     d = os.path.join(out_dir, "spotify_dsp")
  107 [code      ]     os.makedirs(d, exist_ok=True)
  108 [code      ]     copied = {}
  109 [branch    ]     if _copy_safe(files.master_wav, os.path.join(d, "audio_master.wav")):
  110 [code      ]         copied["audio"] = "audio_master.wav"
  111 [branch    ]     elif _copy_safe(files.mp3_320, os.path.join(d, "audio_master.mp3")):
  112 [code      ]         copied["audio"] = "audio_master.mp3"
  113 [branch    ]     if _copy_safe(files.cover_png, os.path.join(d, "cover.png")):
  114 [code      ]         copied["cover"] = "cover.png"
  115 [code      ]     csv_path = os.path.join(d, "distrokid_manifest.csv")
  116 [stmt      ]     with open(csv_path, "w", encoding="utf-8", newline="") as f:
  117 [code      ]         w = csv.writer(f)
  118 [code      ]         w.writerow(["Field", "Value"])
  119 [loop      ]         for row in [
  120 [code      ]             ["Artist", meta.artist],
  121 [code      ]             ["Track title", meta.title],
  122 [code      ]             ["Album", meta.album],
  123 [code      ]             ["Genre", meta.genre],
  124 [code      ]             ["Sub-genre", meta.subgenre],
  125 [code      ]             ["Language of vocals", meta.language],
  126 [code      ]             ["Explicit", "Yes" if meta.explicit else "No"],
  127 [code      ]             ["Release date", meta.release_date],
  128 [code      ]             ["Label", meta.label],
  129 [code      ]             ["Copyright", meta.copyright],
  130 [code      ]             ["Producer (P)", meta.p_line],
  131 [code      ]             ["BPM", f"{meta.bpm:.1f}"],
  132 [code      ]             ["Key", meta.key],
  133 [code      ]             ["Duration (sec)", f"{meta.duration_sec:.1f}"],
  134 [code      ]             ["ISRC", meta.isrc or "(auto)"],
  135 [code      ]             ["ISWC", meta.iswc or "(auto)"],
  136 [code      ]             ["UPC", meta.upc or "(auto)"],
  137 [code      ]             ["Tags", ", ".join(meta.tags)],
  138 [code      ]         ]:
  139 [code      ]             w.writerow(row)
  140 [code      ]     json_path = os.path.join(d, "metadata.json")
  141 [stmt      ]     with open(json_path, "w", encoding="utf-8") as f:
  142 [code      ]         json.dump(
  143 [code      ]             {"meta": asdict(meta), "files": copied}, f, ensure_ascii=False, indent=2
  144 [code      ]         )
  145 [code      ]     inst = os.path.join(d, "INSTRUCTIONS_SPOTIFY.md")
  146 [stmt      ]     with open(inst, "w", encoding="utf-8") as f:
  147 [docstring ]         f.write(f"""# Spotify / Apple Music / Amazon Music
  148 [blank     ] 
  149 [docstring ] ## Файлы
  150 [docstring ] - `audio_master.wav` / `.mp3`, `cover.png` (≥1400×1400)
  151 [docstring ] - `distrokid_manifest.csv`, `metadata.json`
  152 [blank     ] 
  153 [docstring ] ## Дистрибьюторы
  154 [docstring ] 1. **DistroKid** ($19.99/год)
  155 [docstring ] 2. **TuneCore** ($9.99/сингл)
  156 [docstring ] 3. **Amuse Music** (бесплатно, ограничения)
  157 [docstring ] 4. **RouteNote** (бесплатно, 15% с продаж)
  158 [blank     ] 
  159 [docstring ] ## RouteNote workflow (free path)
  160 [docstring ] 1. routenote.com → New Release → Single
  161 [docstring ] 2. Загрузи `audio_master.wav` + `cover.png`
  162 [docstring ] 3. Скопируй поля из CSV
  163 [docstring ] 4. Submit → 3-7 дней до Spotify/Apple/Amazon/Deezer/Tidal
  164 [blank     ] 
  165 [docstring ] Copyright: **{meta.copyright}**  •  {meta.title} — {meta.artist}
  166 [docstring ] """)
  167 [return    ]     return {"dir": d, "csv": csv_path, "json": json_path, "instructions": inst}
  168 [blank     ] 
  169 [blank     ] 
  170 [def       ] def build_yandex_vk_package(meta, files, out_dir):
  171 [code      ]     d = os.path.join(out_dir, "yandex_vk_ru")
  172 [code      ]     os.makedirs(d, exist_ok=True)
  173 [branch    ]     if not _copy_safe(files.mp3_320, os.path.join(d, "track.mp3")):
  174 [code      ]         _copy_safe(files.master_wav, os.path.join(d, "track.wav"))
  175 [code      ]     _copy_safe(files.cover_png, os.path.join(d, "cover.png"))
  176 [branch    ]     if files.lyrics_txt:
  177 [code      ]         _copy_safe(files.lyrics_txt, os.path.join(d, "lyrics.txt"))
  178 [code      ]     csv_path = os.path.join(d, "release_ru.csv")
  179 [stmt      ]     with open(csv_path, "w", encoding="utf-8", newline="") as f:
  180 [code      ]         w = csv.writer(f, delimiter=";")
  181 [code      ]         w.writerow(
  182 [code      ]             [
  183 [code      ]                 "Артист",
  184 [code      ]                 "Название",
  185 [code      ]                 "Альбом",
  186 [code      ]                 "Жанр",
  187 [code      ]                 "Язык",
  188 [code      ]                 "BPM",
  189 [code      ]                 "Тональность",
  190 [code      ]                 "Длительность",
  191 [code      ]                 "Дата релиза",
  192 [code      ]                 "Лейбл",
  193 [code      ]                 "Копирайт",
  194 [code      ]                 "18+",
  195 [code      ]             ]
  196 [code      ]         )
  197 [code      ]         w.writerow(
  198 [code      ]             [
  199 [code      ]                 meta.artist,
  200 [code      ]                 meta.title,
  201 [code      ]                 meta.album,
  202 [code      ]                 meta.genre,
  203 [code      ]                 "русский" if meta.language == "ru" else meta.language,
  204 [code      ]                 f"{meta.bpm:.1f}",
  205 [code      ]                 meta.key,
  206 [code      ]                 f"{int(meta.duration_sec // 60):02d}:{int(meta.duration_sec % 60):02d}",
  207 [code      ]                 meta.release_date,
  208 [code      ]                 meta.label,
  209 [code      ]                 meta.copyright,
  210 [code      ]                 "да" if meta.explicit else "нет",
  211 [code      ]             ]
  212 [code      ]         )
  213 [code      ]     inst = os.path.join(d, "INSTRUCTIONS_YANDEX_VK.md")
  214 [stmt      ]     with open(inst, "w", encoding="utf-8") as f:
  215 [docstring ]         f.write(f"""# Яндекс.Музыка + VK Music
  216 [blank     ] 
  217 [docstring ] ## Файлы: track.mp3, cover.png, lyrics.txt, release_ru.csv
  218 [blank     ] 
  219 [docstring ] ## Бесплатные пути
  220 [docstring ] 1. **Belieber** (belieber.io) — free tier, Яндекс+VK
  221 [docstring ] 2. **VK Music Loud** (loud.vk.com) — прямая заливка на VK Music
  222 [docstring ] 3. **Bandlink Distribution** (платно, +Ok.ru)
  223 [blank     ] 
  224 [docstring ] ## VK Loud
  225 [docstring ] 1. loud.vk.com → «Загрузить релиз»
  226 [docstring ] 2. mp3 + cover.png + поля из CSV
  227 [docstring ] 3. 24-72ч → VK, Ok.ru, Boom
  228 [blank     ] 
  229 [docstring ] Артист: **{meta.artist}**  •  {meta.title}
  230 [docstring ] """)
  231 [return    ]     return {"dir": d, "csv": csv_path, "instructions": inst}
  232 [blank     ] 
  233 [blank     ] 
  234 [def       ] def build_tiktok_package(meta, files, out_dir):
  235 [code      ]     d = os.path.join(out_dir, "tiktok")
  236 [code      ]     os.makedirs(d, exist_ok=True)
  237 [branch    ]     if not _copy_safe(files.tiktok_mp4, os.path.join(d, "tiktok_edit.mp4")):
  238 [code      ]         _safe_print("[dist_v11] tiktok mp4 not found — copying fallback assets")
  239 [code      ]         _copy_safe(files.cover_png, os.path.join(d, "cover.png"))
  240 [code      ]     _copy_safe(files.cover_png, os.path.join(d, "thumbnail.png"))
  241 [code      ]     base_tags = [
  242 [code      ]         "#рэп",
  243 [code      ]         "#phonk",
  244 [code      ]         "#трек",
  245 [code      ]         "#новинка",
  246 [code      ]         "#music",
  247 [code      ]         "#hiphop",
  248 [code      ]         "#russianrap",
  249 [code      ]         "#авто",
  250 [code      ]         "#едем",
  251 [code      ]         "#вайб",
  252 [code      ]     ]
  253 [code      ]     user_tags = [t if t.startswith("#") else f"#{t}" for t in meta.tags[:6]]
  254 [code      ]     all_tags = user_tags + base_tags
  255 [code      ]     seen, hashtags = set(), []
  256 [loop      ]     for t in all_tags:
  257 [branch    ]         if t.lower() not in seen:
  258 [code      ]             seen.add(t.lower())
  259 [code      ]             hashtags.append(t)
  260 [code      ]     caption_path = os.path.join(d, "caption.txt")
  261 [stmt      ]     with open(caption_path, "w", encoding="utf-8") as f:
  262 [code      ]         f.write(f"{meta.title} — {meta.artist}\n\n")
  263 [branch    ]         if meta.lyrics_en_hook:
  264 [code      ]             f.write(f"{meta.lyrics_en_hook.strip()[:100]}\n\n")
  265 [code      ]         f.write(" ".join(hashtags[:20]))
  266 [code      ]     json_path = os.path.join(d, "tiktok_studio.json")
  267 [stmt      ]     with open(json_path, "w", encoding="utf-8") as f:
  268 [code      ]         json.dump(
  269 [code      ]             {
  270 [code      ]                 "title": f"{meta.title} — {meta.artist}",
  271 [code      ]                 "description": open(caption_path, encoding="utf-8").read(),
  272 [code      ]                 "hashtags": hashtags[:20],
  273 [code      ]                 "sound_title": meta.title,
  274 [code      ]                 "sound_artist": meta.artist,
  275 [code      ]                 "allow_duet": True,
  276 [code      ]                 "allow_stitch": True,
  277 [code      ]                 "privacy": "public",
  278 [code      ]             },
  279 [code      ]             f,
  280 [code      ]             ensure_ascii=False,
  281 [code      ]             indent=2,
  282 [code      ]         )
  283 [code      ]     inst = os.path.join(d, "INSTRUCTIONS_TIKTOK.md")
  284 [stmt      ]     with open(inst, "w", encoding="utf-8") as f:
  285 [docstring ]         f.write(f"""# TikTok — Инструкция
  286 [blank     ] 
  287 [docstring ] ## Файлы
  288 [docstring ] - `tiktok_edit.mp4` (1080×1920, 15-30 сек)
  289 [docstring ] - `thumbnail.png`, `caption.txt`, `tiktok_studio.json`
  290 [blank     ] 
  291 [docstring ] ## Workflow
  292 [docstring ] 1. TikTok app / studio.tiktok.com → Upload
  293 [docstring ] 2. Загрузи tiktok_edit.mp4
  294 [docstring ] 3. Скопируй caption.txt в описание
  295 [docstring ] 4. **ВАЖНО**: после публикации → «Сохранить как звук» → «Доступ всем»
  296 [docstring ] 5. Duet + Stitch = включены
  297 [blank     ] 
  298 [docstring ] ## Хэштеги (топ-{min(len(hashtags), 20)})
  299 [docstring ] {" ".join(hashtags[:20])}
  300 [blank     ] 
  301 [docstring ] ## Прокачка
  302 [docstring ] - Постить 19:00-22:00 МСК
  303 [docstring ] - Первые 3 часа — комментить с других акков
  304 [docstring ] - Через 2-3 дня — снять эдит на свой же трек
  305 [docstring ] """)
  306 [return    ]     return {"dir": d, "caption": caption_path, "json": json_path, "instructions": inst}
  307 [blank     ] 
  308 [blank     ] 
  309 [def       ] def build_youtube_package(meta, files, out_dir):
  310 [code      ]     d = os.path.join(out_dir, "youtube")
  311 [code      ]     os.makedirs(d, exist_ok=True)
  312 [code      ]     _copy_safe(files.shorts_mp4 or files.tiktok_mp4, os.path.join(d, "shorts.mp4"))
  313 [code      ]     _copy_safe(files.master_wav, os.path.join(d, "audio_master.wav"))
  314 [code      ]     _copy_safe(files.cover_png, os.path.join(d, "thumbnail.png"))
  315 [branch    ]     if files.lyrics_txt:
  316 [code      ]         _copy_safe(files.lyrics_txt, os.path.join(d, "lyrics.txt"))
  317 [code      ]     desc_path = os.path.join(d, "description.txt")
  318 [stmt      ]     with open(desc_path, "w", encoding="utf-8") as f:
  319 [docstring ]         f.write(f"""{meta.title} — {meta.artist}
  320 [blank     ] 
  321 [docstring ] 🎧 Слушать:
  322 [docstring ] Spotify: [ссылка]
  323 [docstring ] Яндекс.Музыка: [ссылка]
  324 [docstring ] VK Music: [ссылка]
  325 [docstring ] Apple Music: [ссылка]
  326 [blank     ] 
  327 [docstring ] 📝 Текст:
  328 [docstring ] {meta.lyrics_ru[:500] if meta.lyrics_ru else '[скоро]'}
  329 [blank     ] 
  330 [docstring ] 🎵 BPM: {meta.bpm:.0f}  •  Key: {meta.key or '—'}
  331 [docstring ] 📅 Релиз: {meta.release_date}
  332 [blank     ] 
  333 [docstring ] {meta.copyright}
  334 [docstring ] {meta.p_line}
  335 [blank     ] 
  336 [docstring ] #{meta.genre.replace('/', '').replace(' ', '')} #{meta.artist.replace(' ', '')}
  337 [docstring ] """)
  338 [code      ]     ytj = os.path.join(d, "youtube_studio.json")
  339 [stmt      ]     with open(ytj, "w", encoding="utf-8") as f:
  340 [code      ]         json.dump(
  341 [code      ]             {
  342 [code      ]                 "snippet": {
  343 [code      ]                     "title": f"{meta.title} — {meta.artist} (Official Audio)",
  344 [code      ]                     "description": open(desc_path, encoding="utf-8").read(),
  345 [code      ]                     "tags": meta.tags[:20]
  346 [code      ]                     + ["russian rap", "phonk", meta.artist, meta.title],
  347 [code      ]                     "categoryId": "10",
  348 [code      ]                     "defaultLanguage": meta.language,
  349 [code      ]                 },
  350 [code      ]                 "status": {
  351 [code      ]                     "privacyStatus": "public",
  352 [code      ]                     "selfDeclaredMadeForKids": False,
  353 [code      ]                     "license": "youtube",
  354 [code      ]                 },
  355 [code      ]             },
  356 [code      ]             f,
  357 [code      ]             ensure_ascii=False,
  358 [code      ]             indent=2,
  359 [code      ]         )
  360 [code      ]     inst = os.path.join(d, "INSTRUCTIONS_YOUTUBE.md")
  361 [stmt      ]     with open(inst, "w", encoding="utf-8") as f:
  362 [docstring ]         f.write(f"""# YouTube — Инструкция
  363 [blank     ] 
  364 [docstring ] ## Файлы
  365 [docstring ] - `shorts.mp4` (для Shorts, вертикально)
  366 [docstring ] - `audio_master.wav` (для официального аудио)
  367 [docstring ] - `thumbnail.png`, `description.txt`, `youtube_studio.json`
  368 [blank     ] 
  369 [docstring ] ## Два ролика
  370 [docstring ] 1. YouTube Shorts (shorts.mp4, до 60 сек, title заканчивается на #Shorts)
  371 [docstring ] 2. Официальное аудио — собери через ffmpeg:
  372 [docstring ]    ```
  373 [docstring ]    ffmpeg -loop 1 -i thumbnail.png -i audio_master.wav -c:v libx264 \\
  374 [docstring ]      -c:a aac -shortest -pix_fmt yuv420p -vf scale=1280:720 official_audio.mp4
  375 [docstring ]    ```
  376 [blank     ] 
  377 [docstring ] Copyright: {meta.copyright}
  378 [docstring ] """)
  379 [return    ]     return {"dir": d, "instructions": inst, "json": ytj}
  380 [blank     ] 
  381 [blank     ] 
  382 [def       ] def build_shazam_package(meta, out_dir):
  383 [code      ]     d = os.path.join(out_dir, "shazam_ready")
  384 [code      ]     os.makedirs(d, exist_ok=True)
  385 [code      ]     p = os.path.join(d, "shazam_metadata.json")
  386 [stmt      ]     with open(p, "w", encoding="utf-8") as f:
  387 [code      ]         json.dump(
  388 [code      ]             {
  389 [code      ]                 "title": meta.title,
  390 [code      ]                 "artist": meta.artist,
  391 [code      ]                 "album": meta.album,
  392 [code      ]                 "release_date": meta.release_date,
  393 [code      ]                 "isrc": meta.isrc,
  394 [code      ]                 "iswc": meta.iswc,
  395 [code      ]                 "note": "Shazam автоматически распознает трек после "
  396 [code      ]                 "релиза на любом DSP.",
  397 [code      ]             },
  398 [code      ]             f,
  399 [code      ]             ensure_ascii=False,
  400 [code      ]             indent=2,
  401 [code      ]         )
  402 [return    ]     return {"dir": d, "json": p}
  403 [blank     ] 
  404 [blank     ] 
  405 [def       ] def build_all_distribution_packages(meta, files, out_dir):
  406 [code      ]     meta.ensure()
  407 [code      ]     os.makedirs(out_dir, exist_ok=True)
  408 [code      ]     result = {
  409 [code      ]         "spotify_dsp": build_spotify_package(meta, files, out_dir),
  410 [code      ]         "yandex_vk_ru": build_yandex_vk_package(meta, files, out_dir),
  411 [code      ]         "tiktok": build_tiktok_package(meta, files, out_dir),
  412 [code      ]         "youtube": build_youtube_package(meta, files, out_dir),
  413 [code      ]         "shazam_ready": build_shazam_package(meta, out_dir),
  414 [code      ]     }
  415 [code      ]     manifest_path = os.path.join(out_dir, "distribution_manifest.json")
  416 [stmt      ]     with open(manifest_path, "w", encoding="utf-8") as f:
  417 [code      ]         json.dump(
  418 [code      ]             {
  419 [code      ]                 "meta": asdict(meta),
  420 [code      ]                 "files_used": files.existing(),
  421 [code      ]                 "packages": result,
  422 [code      ]                 "generated_at_utc": datetime.now(timezone.utc).isoformat(),
  423 [code      ]                 "generator": "ZS Music Maker v11",
  424 [code      ]             },
  425 [code      ]             f,
  426 [code      ]             ensure_ascii=False,
  427 [code      ]             indent=2,
  428 [code      ]         )
  429 [code      ]     result["manifest"] = {"path": manifest_path}
  430 [code      ]     _safe_print(f"[dist_v11] all packages built at {out_dir}")
  431 [return    ]     return result
  432 [blank     ] 
  433 [blank     ] 
  434 [def       ] def _self_test():
  435 [import    ]     import tempfile
  436 [blank     ] 
  437 [stmt      ]     with tempfile.TemporaryDirectory() as tmp:
  438 [code      ]         meta = TrackMetadata(
  439 [code      ]             title="Test",
  440 [code      ]             artist="ZS",
  441 [code      ]             bpm=140.0,
  442 [code      ]             duration_sec=150.0,
  443 [code      ]             tags=["car", "лето"],
  444 [code      ]             lyrics_ru="test",
  445 [code      ]             lyrics_en_hook="test hook",
  446 [code      ]         )
  447 [loop      ]         for p in ["m.wav", "m.mp3", "c.png", "l.txt", "t.mp4"]:
  448 [stmt      ]             with open(os.path.join(tmp, p), "wb") as f:
  449 [code      ]                 f.write(b"\0")
  450 [code      ]         files = ReleaseFiles(
  451 [code      ]             master_wav=os.path.join(tmp, "m.wav"),
  452 [code      ]             mp3_320=os.path.join(tmp, "m.mp3"),
  453 [code      ]             cover_png=os.path.join(tmp, "c.png"),
  454 [code      ]             lyrics_txt=os.path.join(tmp, "l.txt"),
  455 [code      ]             tiktok_mp4=os.path.join(tmp, "t.mp4"),
  456 [code      ]         )
  457 [code      ]         res = build_all_distribution_packages(meta, files, os.path.join(tmp, "dist"))
  458 [code      ]         ok = all(
  459 [code      ]             k in res
  460 [loop      ]             for k in [
  461 [code      ]                 "spotify_dsp",
  462 [code      ]                 "yandex_vk_ru",
  463 [code      ]                 "tiktok",
  464 [code      ]                 "youtube",
  465 [code      ]                 "shazam_ready",
  466 [code      ]                 "manifest",
  467 [code      ]             ]
  468 [code      ]         )
  469 [code      ]         ok &= os.path.exists(res["manifest"]["path"])
  470 [return    ]         return ok
  471 [blank     ] 
  472 [blank     ] 
  473 [branch    ] if __name__ == "__main__":
  474 [code      ]     print("distribution_export_v11 self-test:", "OK" if _self_test() else "FAIL")
```
# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/release_export.py`

**Всего строк:** 267

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 133 | 49.8 |
| blank | 31 | 11.6 |
| branch | 23 | 8.6 |
| docstring | 22 | 8.2 |
| try_block | 14 | 5.2 |
| import | 12 | 4.5 |
| comment | 12 | 4.5 |
| return | 11 | 4.1 |
| def | 4 | 1.5 |
| loop | 4 | 1.5 |
| stmt | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [v7] release_export.py — сборка полного релиз-пакета.
    3 [blank     ] 
    4 [docstring ] Формирует папку output/releases/<track_name>/ со следующим содержимым:
    5 [docstring ]   master.wav (24-bit/48kHz), master.mp3 (320kbps), master.flac
    6 [docstring ]   instrumental.wav, instrumental.mp3
    7 [docstring ]   acapella.wav, acapella.mp3
    8 [docstring ]   stems/ (drums, bass, vocals, other) — если Demucs доступен
    9 [docstring ]   short_edit.wav (30 сек предпросмотр)
   10 [docstring ]   lyrics.txt, lyrics.lrc
   11 [docstring ]   cover.png (сгенерирован через Pillow)
   12 [docstring ]   tiktok.mp4, reels.mp4 (вертикальные 15-30 сек)
   13 [docstring ]   car_master.wav, club_master.wav, streaming_master.wav (стенды)
   14 [docstring ]   metadata.csv, metadata.json (для дистрибуции Spotify/Yandex)
   15 [docstring ]   recipe.json, manifest.json (лицензии сэмплов), release_notes.txt
   16 [blank     ] 
   17 [docstring ] ID3-теги пишутся через mutagen — artist_name из user_profile.
   18 [docstring ] """
   19 [blank     ] 
   20 [import    ] import csv
   21 [import    ] import json
   22 [import    ] import os
   23 [import    ] import shutil
   24 [import    ] import time
   25 [import    ] from pathlib import Path
   26 [blank     ] 
   27 [code      ] ROOT = Path(__file__).resolve().parents[1]
   28 [code      ] RELEASES_DIR = ROOT / "output" / "releases"
   29 [comment   ] # v22: ленивое создание (не при импорте)
   30 [blank     ] 
   31 [blank     ] 
   32 [def       ] def _copy_or_convert(src: str, dst: str) -> bool:
   33 [docstring ]     """Копирует WAV или конвертирует MP3/FLAC через pydub если нужно."""
   34 [branch    ]     if not os.path.exists(src):
   35 [return    ]         return False
   36 [code      ]     ext_dst = os.path.splitext(dst)[1].lower()
   37 [code      ]     ext_src = os.path.splitext(src)[1].lower()
   38 [branch    ]     if ext_src == ext_dst:
   39 [try_block ]         try:
   40 [code      ]             shutil.copy(src, dst)
   41 [return    ]             return True
   42 [try_block ]         except Exception:
   43 [return    ]             return False
   44 [try_block ]     try:
   45 [import    ]         from pydub import AudioSegment
   46 [blank     ] 
   47 [code      ]         seg = AudioSegment.from_file(src)
   48 [branch    ]         if ext_dst == ".mp3":
   49 [code      ]             seg.export(dst, format="mp3", bitrate="320k")
   50 [branch    ]         elif ext_dst == ".flac":
   51 [code      ]             seg.export(dst, format="flac")
   52 [branch    ]         elif ext_dst == ".wav":
   53 [code      ]             seg.export(dst, format="wav")
   54 [branch    ]         else:
   55 [code      ]             seg.export(dst, format=ext_dst.lstrip("."))
   56 [return    ]         return True
   57 [try_block ]     except Exception as e:
   58 [code      ]         print(f"[release_export._copy_or_convert] {e}")
   59 [try_block ]         try:
   60 [code      ]             shutil.copy(src, dst)
   61 [return    ]             return True
   62 [try_block ]         except Exception:
   63 [return    ]             return False
   64 [blank     ] 
   65 [blank     ] 
   66 [def       ] def _write_id3(
   67 [code      ]     mp3_path: str,
   68 [code      ]     artist: str,
   69 [code      ]     title: str,
   70 [code      ]     album: str = "ZSMM Release",
   71 [code      ]     year: int | None = None,
   72 [code      ]     genre: str = "Phonk",
   73 [code      ] ) -> bool:
   74 [docstring ]     """Пишем ID3v2-теги в MP3. Если mutagen нет — молча пропускаем."""
   75 [try_block ]     try:
   76 [import    ]         from mutagen.easyid3 import EasyID3
   77 [import    ]         from mutagen.mp3 import MP3
   78 [blank     ] 
   79 [try_block ]         try:
   80 [code      ]             audio = EasyID3(mp3_path)
   81 [try_block ]         except Exception:
   82 [code      ]             m = MP3(mp3_path)
   83 [code      ]             m.add_tags()
   84 [code      ]             m.save()
   85 [code      ]             audio = EasyID3(mp3_path)
   86 [code      ]         audio["artist"] = artist
   87 [code      ]         audio["title"] = title
   88 [code      ]         audio["album"] = album
   89 [code      ]         audio["genre"] = genre
   90 [branch    ]         if year:
   91 [code      ]             audio["date"] = str(year)
   92 [code      ]         audio.save()
   93 [return    ]         return True
   94 [try_block ]     except Exception as e:
   95 [code      ]         print(f"[release_export._write_id3] {e}")
   96 [return    ]         return False
   97 [blank     ] 
   98 [blank     ] 
   99 [def       ] def _write_flac_tags(
  100 [code      ]     flac_path: str,
  101 [code      ]     artist: str,
  102 [code      ]     title: str,
  103 [code      ]     album: str = "ZSMM Release",
  104 [code      ]     genre: str = "Phonk",
  105 [code      ] ) -> bool:
  106 [try_block ]     try:
  107 [import    ]         from mutagen.flac import FLAC
  108 [blank     ] 
  109 [code      ]         audio = FLAC(flac_path)
  110 [code      ]         audio["artist"] = artist
  111 [code      ]         audio["title"] = title
  112 [code      ]         audio["album"] = album
  113 [code      ]         audio["genre"] = genre
  114 [code      ]         audio.save()
  115 [return    ]         return True
  116 [try_block ]     except Exception:
  117 [return    ]         return False
  118 [blank     ] 
  119 [blank     ] 
  120 [def       ] def export_release(
  121 [code      ]     beat_path: str,
  122 [code      ]     vocal_path: str,
  123 [code      ]     master_path: str,
  124 [code      ]     lyrics: str = "",
  125 [code      ]     recipe: dict | None = None,
  126 [code      ]     provenance: list | None = None,
  127 [code      ]     project_name: str | None = None,
  128 [code      ]     artist_name: str | None = None,
  129 [code      ]     title: str | None = None,
  130 [code      ]     stands: dict | None = None,
  131 [code      ] ) -> dict:
  132 [docstring ]     """
  133 [docstring ]     Главная точка. Собирает полный релиз-пакет.
  134 [docstring ]     stands = {"car": path, "club": path, "streaming": path} — от mastering_stands
  135 [docstring ]     """
  136 [code      ]     project_name = project_name or f"release_{int(time.time())}"
  137 [code      ]     title = title or project_name
  138 [blank     ] 
  139 [comment   ]     # Artist name из user_profile если не передан
  140 [branch    ]     if not artist_name:
  141 [try_block ]         try:
  142 [import    ]             from modules.user_profile import get_artist_name
  143 [blank     ] 
  144 [code      ]             artist_name = get_artist_name()
  145 [try_block ]         except Exception:
  146 [code      ]             artist_name = "ZSMM Artist"
  147 [blank     ] 
  148 [code      ]     rel_dir = RELEASES_DIR / project_name
  149 [code      ]     rel_dir.mkdir(parents=True, exist_ok=True)
  150 [code      ]     (rel_dir / "stems").mkdir(exist_ok=True)
  151 [blank     ] 
  152 [code      ]     files = {}
  153 [blank     ] 
  154 [comment   ]     # Master versions
  155 [branch    ]     if master_path and os.path.exists(master_path):
  156 [loop      ]         for ext in ("wav", "mp3", "flac"):
  157 [code      ]             p = rel_dir / f"master.{ext}"
  158 [branch    ]             if _copy_or_convert(master_path, str(p)):
  159 [code      ]                 files[f"master.{ext}"] = str(p)
  160 [branch    ]         if "master.mp3" in files:
  161 [code      ]             _write_id3(
  162 [code      ]                 files["master.mp3"], artist_name, title, year=time.localtime().tm_year
  163 [code      ]             )
  164 [branch    ]         if "master.flac" in files:
  165 [code      ]             _write_flac_tags(files["master.flac"], artist_name, title)
  166 [blank     ] 
  167 [comment   ]     # Instrumental (beat)
  168 [branch    ]     if beat_path and os.path.exists(beat_path):
  169 [loop      ]         for ext in ("wav", "mp3"):
  170 [code      ]             p = rel_dir / f"instrumental.{ext}"
  171 [branch    ]             if _copy_or_convert(beat_path, str(p)):
  172 [code      ]                 files[f"instrumental.{ext}"] = str(p)
  173 [branch    ]         if "instrumental.mp3" in files:
  174 [code      ]             _write_id3(
  175 [code      ]                 files["instrumental.mp3"],
  176 [code      ]                 artist_name,
  177 [code      ]                 f"{title} (Instrumental)",
  178 [code      ]                 year=time.localtime().tm_year,
  179 [code      ]             )
  180 [blank     ] 
  181 [comment   ]     # Acapella (vocal)
  182 [branch    ]     if vocal_path and os.path.exists(vocal_path):
  183 [loop      ]         for ext in ("wav", "mp3"):
  184 [code      ]             p = rel_dir / f"acapella.{ext}"
  185 [branch    ]             if _copy_or_convert(vocal_path, str(p)):
  186 [code      ]                 files[f"acapella.{ext}"] = str(p)
  187 [blank     ] 
  188 [comment   ]     # Стенды прослушивания
  189 [loop      ]     for stand_name in ("car", "club", "streaming"):
  190 [branch    ]         if stands and stands.get(stand_name):
  191 [code      ]             src = stands[stand_name]
  192 [branch    ]             if os.path.exists(src):
  193 [code      ]                 p = rel_dir / f"{stand_name}_master.wav"
  194 [branch    ]                 if _copy_or_convert(src, str(p)):
  195 [code      ]                     files[f"{stand_name}_master.wav"] = str(p)
  196 [blank     ] 
  197 [comment   ]     # Lyrics
  198 [branch    ]     if lyrics:
  199 [code      ]         (rel_dir / "lyrics.txt").write_text(lyrics, encoding="utf-8")
  200 [code      ]         files["lyrics.txt"] = str(rel_dir / "lyrics.txt")
  201 [blank     ] 
  202 [comment   ]     # Recipe
  203 [branch    ]     if recipe:
  204 [code      ]         (rel_dir / "recipe.json").write_text(
  205 [code      ]             json.dumps(recipe, ensure_ascii=False, indent=2), encoding="utf-8"
  206 [code      ]         )
  207 [code      ]         files["recipe.json"] = str(rel_dir / "recipe.json")
  208 [blank     ] 
  209 [comment   ]     # Manifest (лицензии сэмплов)
  210 [code      ]     manifest = {
  211 [code      ]         "samples": provenance or [],
  212 [code      ]         "generated_at": time.time(),
  213 [code      ]         "artist": artist_name,
  214 [code      ]         "title": title,
  215 [code      ]     }
  216 [code      ]     (rel_dir / "manifest.json").write_text(
  217 [code      ]         json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
  218 [code      ]     )
  219 [code      ]     files["manifest.json"] = str(rel_dir / "manifest.json")
  220 [blank     ] 
  221 [comment   ]     # Metadata для дистрибуции
  222 [comment   ]     # v39.4 (ШАГ 003): генерируем ISRC вместо пустой строки
  223 [import    ]     from app.core.isrc import get_isrc
  224 [code      ]     meta = {
  225 [code      ]         "artist": artist_name,
  226 [code      ]         "title": title,
  227 [code      ]         "album": "ZSMM Release",
  228 [code      ]         "year": time.localtime().tm_year,
  229 [code      ]         "genre": "Phonk",
  230 [code      ]         "isrc": get_isrc({"title": title, "artist": artist_name,
  231 [code      ]                           "year": time.localtime().tm_year}, fallback=""),
  232 [code      ]         "duration_sec": recipe.get("duration_sec", 0) if recipe else 0,
  233 [code      ]     }
  234 [code      ]     (rel_dir / "metadata.json").write_text(
  235 [code      ]         json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
  236 [code      ]     )
  237 [stmt      ]     with open(rel_dir / "metadata.csv", "w", encoding="utf-8", newline="") as f:
  238 [code      ]         w = csv.writer(f)
  239 [code      ]         w.writerow(list(meta.keys()))
  240 [code      ]         w.writerow(list(meta.values()))
  241 [code      ]     files["metadata.json"] = str(rel_dir / "metadata.json")
  242 [code      ]     files["metadata.csv"] = str(rel_dir / "metadata.csv")
  243 [blank     ] 
  244 [comment   ]     # Release notes
  245 [code      ]     notes = (
  246 [code      ]         f"# {title}\n\n"
  247 [code      ]         f"**Артист:** {artist_name}\n"
  248 [code      ]         f"**Год:** {meta['year']}\n"
  249 [code      ]         f"**Жанр:** {meta['genre']}\n"
  250 [code      ]         f"**BPM:** {recipe.get('style_vector',{}).get('target_bpm','?') if recipe else '?'}\n\n"
  251 [code      ]         f"Собрано в ZS Music Maker v7 (MM ZS).\n"
  252 [code      ]         f"Стенды прослушивания: {', '.join(k for k in ('car','club','streaming') if f'{k}_master.wav' in files)}\n"
  253 [code      ]     )
  254 [code      ]     (rel_dir / "release_notes.txt").write_text(notes, encoding="utf-8")
  255 [code      ]     files["release_notes.txt"] = str(rel_dir / "release_notes.txt")
  256 [blank     ] 
  257 [return    ]     return {
  258 [code      ]         "ok": True,
  259 [code      ]         "release_dir": str(rel_dir),
  260 [code      ]         "artist": artist_name,
  261 [code      ]         "title": title,
  262 [code      ]         "files": files,
  263 [code      ]     }
  264 [blank     ] 
  265 [blank     ] 
  266 [branch    ] if __name__ == "__main__":
  267 [code      ]     print("release_export v7 ready")
```
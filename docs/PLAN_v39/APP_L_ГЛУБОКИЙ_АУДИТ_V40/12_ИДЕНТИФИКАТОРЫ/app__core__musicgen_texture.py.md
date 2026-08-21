# Идентификаторы `app/core/musicgen_texture.py`

## Имена (ast.Name) (уникальных: 48)

| Имя | Использований |
|-----|--------------:|
| `str` | 22 |
| `size` | 10 |
| `model` | 8 |
| `r` | 7 |
| `duration_sec` | 7 |
| `_MODEL_CACHE` | 6 |
| `cached` | 6 |
| `vram_gb` | 6 |
| `int` | 6 |
| `dict` | 5 |
| `a` | 5 |
| `results` | 5 |
| `prompts` | 5 |
| `prompt` | 5 |
| `float` | 5 |
| `Exception` | 5 |
| `CACHE` | 4 |
| `list` | 4 |
| `quality_mode` | 4 |
| `print` | 4 |
| `ROOT` | 3 |
| `avail` | 3 |
| `generate_texture` | 3 |
| `vibe` | 3 |
| `e` | 3 |
| `OUT_DIR` | 2 |
| `d` | 2 |
| `h` | 2 |
| `key` | 2 |
| `p` | 2 |
| `detect_availability` | 2 |
| `wav` | 2 |
| `__name__` | 1 |
| `Any` | 1 |
| `choose_size` | 1 |
| `_cache_key` | 1 |
| `_load_musicgen` | 1 |
| `RuntimeError` | 1 |
| `generate_batch` | 1 |
| `count` | 1 |
| `MusicGen` | 1 |
| `Path` | 1 |
| `__file__` | 1 |
| `torch` | 1 |
| `torchaudio` | 1 |
| `hashlib` | 1 |
| `type` | 1 |
| `duration` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 30)

| Имя | Использований |
|-----|--------------:|
| `print` | 4 |
| `str` | 4 |
| `get` | 3 |
| `generate_texture` | 3 |
| `detect_availability` | 2 |
| `mkdir` | 1 |
| `clear` | 1 |
| `choose_size` | 1 |
| `_cache_key` | 1 |
| `_load_musicgen` | 1 |
| `RuntimeError` | 1 |
| `generate_batch` | 1 |
| `resolve` | 1 |
| `get_pretrained` | 1 |
| `empty_cache` | 1 |
| `list` | 1 |
| `hexdigest` | 1 |
| `exists` | 1 |
| `append` | 1 |
| `lower` | 1 |
| `keys` | 1 |
| `set_generation_params` | 1 |
| `generate` | 1 |
| `save` | 1 |
| `Path` | 1 |
| `md5` | 1 |
| `stat` | 1 |
| `cpu` | 1 |
| `encode` | 1 |
| `type` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 22)

| Имя | Использований |
|-----|--------------:|
| `get` | 3 |
| `parents` | 1 |
| `mkdir` | 1 |
| `clear` | 1 |
| `resolve` | 1 |
| `get_pretrained` | 1 |
| `empty_cache` | 1 |
| `hexdigest` | 1 |
| `exists` | 1 |
| `st_size` | 1 |
| `append` | 1 |
| `lower` | 1 |
| `cuda` | 1 |
| `keys` | 1 |
| `set_generation_params` | 1 |
| `generate` | 1 |
| `save` | 1 |
| `md5` | 1 |
| `stat` | 1 |
| `cpu` | 1 |
| `__name__` | 1 |
| `encode` | 1 |

## Строковые литералы (уникальных: 73)

| Имя | Использований |
|-----|--------------:|
| `reason` | 6 |
| `install_hint` | 6 |
| `available` | 5 |
| `status` | 5 |
| `path` | 5 |
| `quality` | 4 |
| `ok` | 4 |
| `` | 3 |
| `cached` | 3 |
| `size` | 3 |
| `duration` | 3 |
| `small` | 2 |
| `medium` | 2 |
| `.wav` | 2 |
| `fast` | 2 |
| `BLOCKED` | 2 |
| `\|` | 2 |
| `textures` | 1 |
| `musicgen_cache` | 1 |
| `\n    Выбираем размер модели в зависимости от VRAM и режима качества.\n      quality_mode: "fast" \| "quality" \| "max"\` | 1 |
| `Ленивая загрузка модели MusicGen. Кэшируется в памяти.` | 1 |
| `Освобождаем VRAM (после генерации, перед RVC-инференсом).` | 1 |
| `v35: сводный статус для health/dashboard (как get_status() у midi_generator).` | 1 |
| `\n    Генерирует одну текстуру (атмосфера/FX/пэд/хук).\n    Возвращает dict с путём к WAV.\n    ` | 1 |
| `Батч-генерация — несколько промтов сразу для аранжировки.` | 1 |
| `Атмосферная подложка под вайб.` | 1 |
| `Набор коротких FX-хитов (риверсы/удары/переходы).` | 1 |
| `__main__` | 1 |
| `output` | 1 |
| `models` | 1 |
| `REAL_PASS` | 1 |
| `audiocraft + torch доступны` | 1 |
| `module` | 1 |
| `cached_models` | 1 |
| `cache_dir` | 1 |
| `musicgen_texture` | 1 |
| `warning` | 1 |
| `unavailable` | 1 |
| `audiocraft/MusicGen unavailable; no synthetic fallback used` | 1 |
| `P0.06: pink-noise as MusicGen is FORBIDDEN by TZ 33.5. Install audiocraft for real MusicGen generation.` | 1 |
| `phonk` | 1 |
| `drift` | 1 |
| `hyperpop` | 1 |
| `lofi` | 1 |
| `trap` | 1 |
| `summer` | 1 |
| `dark cinematic phonk atmosphere with sub bass drones and distant chimes` | 1 |
| `night city drift atmosphere with rain and neon hum` | 1 |
| `glitchy hyperpop atmosphere with pitched vocal chops` | 1 |
| `warm lofi tape atmosphere with vinyl crackle and soft pads` | 1 |
| `dark trap atmosphere with 808 sub and hi-hat rolls` | 1 |
| `warm summer atmosphere with soft synths and beach sounds` | 1 |
| `dark phonk atmosphere` | 1 |
| `large` | 1 |
| `tex_` | 1 |
| `cinematic ` | 1 |
| ` atmosphere with sub bass` | 1 |
| `reverse cinematic riser build-up 4 seconds` | 1 |
| `impact bass hit with sub tail` | 1 |
| `hi-hat roll fill 2 seconds` | 1 |
| `vinyl scratch transition` | 1 |
| `808 sub drop with distortion` | 1 |
| `facebook/musicgen-` | 1 |
| `pip install torch  (CPU-сборка достаточна для musicgen-small)` | 1 |
| `audiocraft не установлен — MusicGen-текстуры отключены (это опциональная фича, ядро не ломается)` | 1 |
| `pip install audiocraft  # ~тяжёлая зависимость, тянет torch+audio-стек` | 1 |
| `[musicgen_texture] BLOCKED: ` | 1 |
| ` \| ` | 1 |
| `atmo_` | 1 |
| `[musicgen_texture] audiocraft недоступен: ` | 1 |
| `torch не установлен (` | 1 |
| `)` | 1 |
| `[musicgen_texture] generation failed: ` | 1 |

## Числовые литералы (уникальных: 17)

| Имя | Использований |
|-----|--------------:|
| `True` | 7 |
| `4.0` | 5 |
| `False` | 5 |
| `20` | 2 |
| `12` | 2 |
| `2` | 1 |
| `30` | 1 |
| `5` | 1 |
| `6` | 1 |
| `1000` | 1 |
| `4` | 1 |
| `10` | 1 |
| `250` | 1 |
| `0.0` | 1 |
| `1.0` | 1 |
| `32000` | 1 |
| `0` | 1 |
# Идентификаторы `modules/mastering.py`

## Имена (ast.Name) (уникальных: 72)

| Имя | Использований |
|-----|--------------:|
| `y` | 32 |
| `np` | 21 |
| `str` | 19 |
| `float` | 10 |
| `stand` | 10 |
| `sr` | 8 |
| `dict` | 7 |
| `info` | 7 |
| `out` | 7 |
| `out_wav` | 6 |
| `low` | 5 |
| `prev` | 5 |
| `target` | 5 |
| `masters` | 5 |
| `int` | 5 |
| `Exception` | 4 |
| `stands` | 4 |
| `r` | 4 |
| `len` | 4 |
| `e` | 4 |
| `STAND_TARGET_DBFS` | 3 |
| `_HAS_PYLN` | 3 |
| `dt` | 3 |
| `g` | 3 |
| `n` | 3 |
| `high` | 3 |
| `eq` | 3 |
| `fallback` | 3 |
| `errors` | 3 |
| `squeeze` | 3 |
| `band` | 3 |
| `cutoff` | 3 |
| `gdb` | 3 |
| `Any` | 3 |
| `_loudness_dbfs` | 3 |
| `y2` | 3 |
| `sys` | 3 |
| `ALL_STANDS` | 2 |
| `list` | 2 |
| `rc` | 2 |
| `a_lp` | 2 |
| `rms` | 2 |
| `pyln` | 2 |
| `range` | 2 |
| `cur` | 2 |
| `delta` | 2 |
| `round` | 2 |
| `meter` | 2 |
| `mono` | 2 |
| `mix_wav` | 2 |
| `print` | 2 |
| `drive` | 2 |
| `sf` | 2 |
| `os` | 2 |
| `type` | 2 |
| `_` | 1 |
| `tuple` | 1 |
| `__name__` | 1 |
| `ceiling` | 1 |
| `_apply_stand_eq` | 1 |
| `Path` | 1 |
| `out_dir` | 1 |
| `gain_db` | 1 |
| `_tanh_limit` | 1 |
| `_loudness_lufs` | 1 |
| `_try_numpy_dsp` | 1 |
| `master_one` | 1 |
| `bool` | 1 |
| `abs` | 1 |
| `_one_pole_shelf` | 1 |
| `max` | 1 |
| `master_all_stands` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 38)

| Имя | Использований |
|-----|--------------:|
| `get` | 5 |
| `len` | 4 |
| `float` | 3 |
| `_loudness_dbfs` | 3 |
| `range` | 2 |
| `round` | 2 |
| `str` | 2 |
| `print` | 2 |
| `tanh` | 2 |
| `mean` | 2 |
| `type` | 2 |
| `list` | 1 |
| `keys` | 1 |
| `zeros_like` | 1 |
| `zeros` | 1 |
| `_apply_stand_eq` | 1 |
| `Path` | 1 |
| `mkdir` | 1 |
| `log10` | 1 |
| `_tanh_limit` | 1 |
| `_loudness_lufs` | 1 |
| `read` | 1 |
| `repeat` | 1 |
| `_try_numpy_dsp` | 1 |
| `makedirs` | 1 |
| `write` | 1 |
| `master_one` | 1 |
| `bool` | 1 |
| `abs` | 1 |
| `_one_pole_shelf` | 1 |
| `sqrt` | 1 |
| `max` | 1 |
| `Meter` | 1 |
| `astype` | 1 |
| `int` | 1 |
| `master_all_stands` | 1 |
| `integrated_loudness` | 1 |
| `dirname` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 26)

| Имя | Использований |
|-----|--------------:|
| `ndarray` | 10 |
| `get` | 5 |
| `shape` | 3 |
| `argv` | 3 |
| `ndim` | 2 |
| `tanh` | 2 |
| `mean` | 2 |
| `__name__` | 2 |
| `keys` | 1 |
| `zeros_like` | 1 |
| `zeros` | 1 |
| `mkdir` | 1 |
| `float64` | 1 |
| `log10` | 1 |
| `read` | 1 |
| `repeat` | 1 |
| `makedirs` | 1 |
| `write` | 1 |
| `pi` | 1 |
| `sqrt` | 1 |
| `Meter` | 1 |
| `astype` | 1 |
| `float32` | 1 |
| `integrated_loudness` | 1 |
| `dirname` | 1 |
| `path` | 1 |

## Строковые литералы (уникальных: 43)

| Имя | Использований |
|-----|--------------:|
| `low` | 9 |
| `high` | 8 |
| `ok` | 5 |
| `streaming` | 4 |
| `reason` | 3 |
| `car` | 2 |
| `club` | 2 |
| `tiktok` | 2 |
| `airpods` | 2 |
| `bluetooth` | 2 |
| `headphones` | 2 |
| `monitors` | 2 |
| `fallback_used` | 2 |
| `engine` | 2 |
| `: ` | 2 |
| `Простейший shelving EQ на однополюсном фильтре (low/high band).` | 1 |
| `Характер стенда: низ/верх под сценарий прослушивания.` | 1 |
| `LUFS через pyloudnorm если есть; иначе dBFS -3dB (sweet-spot под\n    mono-downmix, v26).` | 1 |
| `Soft-knee tanh limiter: glue + защита от клиппинга.` | 1 |
| `Основной DSP-путь мастеринга (честный, fallback_used=False):\n    EQ → итеративная loudness-компенсация → tanh-limiter.` | 1 |
| `Мастеринг одного WAV под конкретный стенд. Сохраняет стерео.` | 1 |
| `__main__` | 1 |
| `numpy_dsp_v27` | 1 |
| `target_dbfs` | 1 |
| `final_dbfs` | 1 |
| `final_lufs` | 1 |
| `masters` | 1 |
| `summary` | 1 |
| `modules/mastering.py v27 (numpy_dsp + optional pyloudnorm)` | 1 |
| `path` | 1 |
| `stand` | 1 |
| `channels` | 1 |
| `total` | 1 |
| `done` | 1 |
| `fallback` | 1 |
| `errors` | 1 |
| `usage: python -m modules.mastering <mix.wav> <out_dir>` | 1 |
| `.` | 1 |
| `read failed: ` | 1 |
| `dsp failed: ` | 1 |
| `master_` | 1 |
| `.wav` | 1 |
| `unknown` | 1 |

## Числовые литералы (уникальных: 38)

| Имя | Использований |
|-----|--------------:|
| `1` | 9 |
| `True` | 7 |
| `1.0` | 7 |
| `2` | 7 |
| `False` | 5 |
| `13.5` | 4 |
| `0.5` | 4 |
| `20.0` | 3 |
| `2.0` | 3 |
| `150` | 3 |
| `1.5` | 3 |
| `0` | 2 |
| `10.0` | 2 |
| `3.1` | 2 |
| `1e-12` | 2 |
| `8000` | 2 |
| `9000` | 2 |
| `0.0` | 2 |
| `0.98` | 1 |
| `12.0` | 1 |
| `11.0` | 1 |
| `12.5` | 1 |
| `14.0` | 1 |
| `14.5` | 1 |
| `3.0` | 1 |
| `3` | 1 |
| `1e-06` | 1 |
| `120` | 1 |
| `6500` | 1 |
| `100` | 1 |
| `2.5` | 1 |
| `200` | 1 |
| `7500` | 1 |
| `250` | 1 |
| `180` | 1 |
| `7000` | 1 |
| `10000` | 1 |
| `1.4` | 1 |
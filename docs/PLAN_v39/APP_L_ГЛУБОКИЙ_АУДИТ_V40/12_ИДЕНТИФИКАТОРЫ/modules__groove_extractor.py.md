# Идентификаторы `modules/groove_extractor.py`

## Имена (ast.Name) (уникальных: 92)

| Имя | Использований |
|-----|--------------:|
| `steps_per_bar` | 20 |
| `bar` | 14 |
| `np` | 14 |
| `kick_pattern` | 13 |
| `len` | 12 |
| `range` | 11 |
| `grooves` | 11 |
| `g` | 11 |
| `step` | 9 |
| `n_bars` | 9 |
| `float` | 9 |
| `w` | 9 |
| `weights` | 8 |
| `spb` | 8 |
| `v` | 8 |
| `round` | 8 |
| `hihat_pattern` | 7 |
| `kick_binary` | 7 |
| `min` | 7 |
| `bar_start` | 7 |
| `idx` | 7 |
| `librosa` | 6 |
| `i` | 6 |
| `S` | 5 |
| `freqs` | 5 |
| `snare_pattern` | 5 |
| `swing_vals` | 5 |
| `bar_energies` | 5 |
| `merged_kick` | 5 |
| `merged_snare` | 5 |
| `start` | 5 |
| `end` | 5 |
| `bar_sec` | 4 |
| `frames_per_step` | 4 |
| `sr` | 4 |
| `bpm` | 4 |
| `even_vals` | 4 |
| `sum` | 4 |
| `tempo` | 4 |
| `kick_envelope` | 3 |
| `hihat_mask` | 3 |
| `total_frames` | 3 |
| `snare_binary` | 3 |
| `swing` | 3 |
| `triplet_rolls` | 3 |
| `pattern_changes` | 3 |
| `drop_intensity` | 3 |
| `y` | 3 |
| `max` | 3 |
| `bar_end` | 3 |
| `zip` | 3 |
| `kp` | 3 |
| `sp` | 3 |
| `prev_start` | 3 |
| `curr_start` | 3 |
| `dict` | 2 |
| `beat_sec` | 2 |
| `step_sec` | 2 |
| `kick_mask` | 2 |
| `snare_mask` | 2 |
| `snare_envelope` | 2 |
| `hihat_envelope` | 2 |
| `hop` | 2 |
| `total_steps` | 2 |
| `kick_thresh` | 2 |
| `snare_thresh` | 2 |
| `hihat_mean` | 2 |
| `hihat_density` | 2 |
| `groove_template` | 2 |
| `avg_hihat` | 2 |
| `avg_swing` | 2 |
| `audio_path` | 2 |
| `kick_val` | 2 |
| `snare_val` | 2 |
| `hihat_val` | 2 |
| `list` | 2 |
| `prev_pat` | 2 |
| `curr_pat` | 2 |
| `print` | 2 |
| `sys` | 2 |
| `ImportError` | 1 |
| `hihat_std` | 1 |
| `__name__` | 1 |
| `str` | 1 |
| `RuntimeError` | 1 |
| `_` | 1 |
| `int` | 1 |
| `any` | 1 |
| `os` | 1 |
| `json` | 1 |
| `extract_groove` | 1 |
| `abs` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 26)

| Имя | Использований |
|-----|--------------:|
| `mean` | 14 |
| `len` | 12 |
| `range` | 11 |
| `float` | 8 |
| `round` | 8 |
| `min` | 7 |
| `get` | 7 |
| `append` | 6 |
| `sum` | 4 |
| `max` | 3 |
| `zip` | 3 |
| `std` | 3 |
| `abs` | 2 |
| `any` | 2 |
| `print` | 2 |
| `load` | 1 |
| `fft_frequencies` | 1 |
| `RuntimeError` | 1 |
| `beat_track` | 1 |
| `stft` | 1 |
| `zeros` | 1 |
| `int` | 1 |
| `basename` | 1 |
| `dumps` | 1 |
| `ndim` | 1 |
| `extract_groove` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 18)

| Имя | Использований |
|-----|--------------:|
| `mean` | 14 |
| `get` | 7 |
| `append` | 6 |
| `std` | 3 |
| `argv` | 2 |
| `load` | 1 |
| `abs` | 1 |
| `fft_frequencies` | 1 |
| `beat_track` | 1 |
| `stft` | 1 |
| `any` | 1 |
| `zeros` | 1 |
| `basename` | 1 |
| `beat` | 1 |
| `shape` | 1 |
| `path` | 1 |
| `dumps` | 1 |
| `ndim` | 1 |

## Строковые литералы (уникальных: 25)

| Имя | Использований |
|-----|--------------:|
| `bpm` | 3 |
| `kick_pattern` | 3 |
| `snare_pattern` | 3 |
| `hihat_density` | 3 |
| `swing` | 3 |
| `triplet_rolls` | 3 |
| `source` | 2 |
| `steps_per_bar` | 2 |
| `Объединяет несколько groove templates в один (взвешенное слияние).` | 1 |
| `__main__` | 1 |
| `kick_pattern_full` | 1 |
| `snare_pattern_full` | 1 |
| `pattern_changes` | 1 |
| `drop_intensity` | 1 |
| `n_bars_analyzed` | 1 |
| `bar_sec` | 1 |
| `sources` | 1 |
| `merged` | 1 |
| `librosa не установлен` | 1 |
| `error` | 1 |
| `Не удалось извлечь groove (слишком короткий трек)` | 1 |
| `Usage: python groove_extractor.py <track.mp3>` | 1 |
| `?` | 1 |
| `bar` | 1 |
| `time_sec` | 1 |

## Числовые литералы (уникальных: 23)

| Имя | Использований |
|-----|--------------:|
| `0` | 22 |
| `1` | 11 |
| `2` | 10 |
| `3` | 7 |
| `1.0` | 5 |
| `False` | 3 |
| `True` | 3 |
| `1e-09` | 3 |
| `16` | 2 |
| `512` | 2 |
| `0.0` | 2 |
| `4` | 2 |
| `1024` | 2 |
| `0.3` | 2 |
| `0.4` | 2 |
| `60.0` | 1 |
| `80` | 1 |
| `5000` | 1 |
| `22050` | 1 |
| `150` | 1 |
| `400` | 1 |
| `8` | 1 |
| `128` | 1 |
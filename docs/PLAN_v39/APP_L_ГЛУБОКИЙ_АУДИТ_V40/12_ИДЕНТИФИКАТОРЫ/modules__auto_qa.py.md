# Идентификаторы `modules/auto_qa.py`

## Имена (ast.Name) (уникальных: 61)

| Имя | Использований |
|-----|--------------:|
| `result` | 28 |
| `len` | 10 |
| `y` | 9 |
| `str` | 9 |
| `a` | 8 |
| `m` | 7 |
| `neuro` | 7 |
| `np` | 7 |
| `rms` | 6 |
| `master_wav` | 6 |
| `chunks` | 6 |
| `i` | 6 |
| `w` | 5 |
| `round` | 5 |
| `dict` | 4 |
| `rms_db` | 4 |
| `best_corr` | 4 |
| `float` | 4 |
| `ad` | 4 |
| `int` | 4 |
| `sr` | 4 |
| `b` | 4 |
| `peak_db` | 3 |
| `n_actions` | 3 |
| `out` | 3 |
| `Exception` | 3 |
| `Path` | 3 |
| `lu` | 3 |
| `range` | 3 |
| `y_mono` | 3 |
| `da` | 3 |
| `db` | 3 |
| `e` | 3 |
| `ROOT` | 2 |
| `QA_DIR` | 2 |
| `peak` | 2 |
| `lufs_approx` | 2 |
| `crest` | 2 |
| `verdict` | 2 |
| `targets` | 2 |
| `list` | 2 |
| `j` | 2 |
| `qa_report` | 2 |
| `math` | 2 |
| `den` | 2 |
| `c` | 2 |
| `time` | 2 |
| `target_lufs` | 2 |
| `tuple` | 1 |
| `current_iter` | 1 |
| `max_iterations` | 1 |
| `bool` | 1 |
| `analyze_track` | 1 |
| `_loudness` | 1 |
| `_structure_check` | 1 |
| `set` | 1 |
| `sf` | 1 |
| `json` | 1 |
| `__file__` | 1 |
| `max` | 1 |
| `librosa` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 29)

| Имя | Использований |
|-----|--------------:|
| `len` | 10 |
| `str` | 7 |
| `mean` | 5 |
| `round` | 5 |
| `append` | 5 |
| `get` | 4 |
| `float` | 3 |
| `range` | 3 |
| `Path` | 2 |
| `log10` | 2 |
| `int` | 2 |
| `time` | 2 |
| `max` | 2 |
| `norm` | 2 |
| `write_text` | 1 |
| `list` | 1 |
| `resolve` | 1 |
| `exists` | 1 |
| `analyze_track` | 1 |
| `read` | 1 |
| `_loudness` | 1 |
| `_structure_check` | 1 |
| `dumps` | 1 |
| `set` | 1 |
| `sqrt` | 1 |
| `rms` | 1 |
| `abs` | 1 |
| `join` | 1 |
| `dot` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 21)

| Имя | Использований |
|-----|--------------:|
| `mean` | 5 |
| `append` | 5 |
| `get` | 4 |
| `ndim` | 2 |
| `log10` | 2 |
| `time` | 2 |
| `norm` | 2 |
| `linalg` | 2 |
| `parents` | 1 |
| `write_text` | 1 |
| `resolve` | 1 |
| `exists` | 1 |
| `read` | 1 |
| `dumps` | 1 |
| `max` | 1 |
| `sqrt` | 1 |
| `rms` | 1 |
| `abs` | 1 |
| `feature` | 1 |
| `join` | 1 |
| `dot` | 1 |

## Строковые литералы (уникальных: 55)

| Имя | Использований |
|-----|--------------:|
| `actions` | 9 |
| `target` | 7 |
| `reason` | 5 |
| `fix` | 5 |
| `verdict` | 4 |
| `hook_score` | 4 |
| `error` | 3 |
| `loudness` | 3 |
| `verdict_text` | 3 |
| `peak_db` | 2 |
| `lufs_approx` | 2 |
| `ok` | 2 |
| `release` | 2 |
| `sections_detected` | 2 |
| `ai_detector` | 2 |
| `structure` | 2 |
| `mastering` | 2 |
| `AI detector: ` | 2 |
| `% нейроношности` | 2 |
| `auto_qa` | 1 |
| `Приблизительный интегрированный LUFS / peak / crest factor.` | 1 |
| `Ищем хук: повторяющийся куск ~8 сек с высокой энергией.` | 1 |
| `\n    Решаем — гонять ли pipeline снова.\n    Возвращает (retry: bool, targets: list[str]).\n    ` | 1 |
| `output` | 1 |
| `rms_db` | 1 |
| `crest_factor_db` | 1 |
| `master` | 1 |
| `ts` | 1 |
| `master.wav не найден` | 1 |
| `✅ Готов к релизу` | 1 |
| `report_path` | 1 |
| `neuronoshnost_percent` | 1 |
| `patch` | 1 |
| `rebuild` | 1 |
| `❌ Пересобрать всё` | 1 |
| `qa_` | 1 |
| `.json` | 1 |
| `utf-8` | 1 |
| `neuroness_percent` | 1 |
| `loudness_error` | 1 |
| `⚠ Переделать: ` | 1 |
| `voice` | 1 |
| `переделать голос через ProVoice Mode + добавить бэки` | 1 |
| `усилить лимитер, повторить Matchering` | 1 |
| `Клиппинг на пиках` | 1 |
| `мягкий true-peak limiter −1 dBTP` | 1 |
| `beat` | 1 |
| `Не найден яркий хук` | 1 |
| `усилить контраст припева, повторить Beat Constructor` | 1 |
| `vocal_humanization` | 1 |
| `усилить humanization (тайминг, дыхания, adlibs)` | 1 |
| `Слишком тихо (LUFS≈` | 1 |
| `, target=` | 1 |
| `)` | 1 |
| `, ` | 1 |

## Числовые литералы (уникальных: 18)

| Имя | Использований |
|-----|--------------:|
| `2` | 8 |
| `0` | 6 |
| `1` | 5 |
| `0.0` | 5 |
| `3` | 4 |
| `False` | 4 |
| `1e-09` | 3 |
| `True` | 2 |
| `20` | 2 |
| `1024` | 2 |
| `3.0` | 1 |
| `9.0` | 1 |
| `0.35` | 1 |
| `70` | 1 |
| `0.2` | 1 |
| `2048` | 1 |
| `8` | 1 |
| `40` | 1 |
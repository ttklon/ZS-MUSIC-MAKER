# Идентификаторы `app/ai/quality.py`

## Имена (ast.Name) (уникальных: 69)

| Имя | Использований |
|-----|--------------:|
| `metrics` | 39 |
| `str` | 27 |
| `result` | 20 |
| `len` | 20 |
| `dict` | 13 |
| `tokens` | 12 |
| `Any` | 12 |
| `float` | 12 |
| `missing` | 10 |
| `source` | 10 |
| `round` | 10 |
| `payload` | 10 |
| `Path` | 9 |
| `samples` | 9 |
| `np` | 9 |
| `text` | 7 |
| `key` | 7 |
| `input_duration` | 6 |
| `ratio` | 6 |
| `TOKEN_RE` | 4 |
| `tag_count` | 4 |
| `target` | 4 |
| `normalized` | 4 |
| `base` | 4 |
| `int` | 4 |
| `path` | 4 |
| `validate_audio_artifact` | 4 |
| `line` | 4 |
| `left` | 4 |
| `right` | 4 |
| `normalized_lines` | 3 |
| `token_count` | 3 |
| `expected_min_duration` | 3 |
| `unique_tokens` | 3 |
| `sample_rate` | 3 |
| `denominator` | 3 |
| `audio_metrics` | 3 |
| `isinstance` | 3 |
| `value` | 3 |
| `line_counts` | 2 |
| `max_repeated_line` | 2 |
| `unique_ratio` | 2 |
| `title` | 2 |
| `descriptions` | 2 |
| `peak` | 2 |
| `rms` | 2 |
| `duration` | 2 |
| `output_duration` | 2 |
| `required` | 2 |
| `re` | 2 |
| `max` | 2 |
| `min_characters` | 2 |
| `correlation` | 2 |
| `min_duration_sec` | 2 |
| `input_path` | 2 |
| `output_path` | 2 |
| `set` | 2 |
| `Counter` | 1 |
| `lyrics_metrics` | 1 |
| `sum` | 1 |
| `Exception` | 1 |
| `min` | 1 |
| `bool` | 1 |
| `track_level` | 1 |
| `any` | 1 |
| `abs` | 1 |
| `sf` | 1 |
| `list` | 1 |
| `exc` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 37)

| Имя | Использований |
|-----|--------------:|
| `len` | 20 |
| `get` | 12 |
| `round` | 10 |
| `float` | 9 |
| `strip` | 6 |
| `validate_audio_artifact` | 4 |
| `str` | 4 |
| `findall` | 3 |
| `max` | 3 |
| `audio_metrics` | 3 |
| `join` | 3 |
| `lower` | 3 |
| `isinstance` | 3 |
| `append` | 3 |
| `sqrt` | 2 |
| `int` | 2 |
| `set` | 2 |
| `abs` | 2 |
| `mean` | 2 |
| `norm` | 2 |
| `startswith` | 2 |
| `compile` | 1 |
| `Counter` | 1 |
| `lyrics_metrics` | 1 |
| `sum` | 1 |
| `Path` | 1 |
| `min` | 1 |
| `values` | 1 |
| `any` | 1 |
| `read` | 1 |
| `exists` | 1 |
| `split` | 1 |
| `splitlines` | 1 |
| `sub` | 1 |
| `items` | 1 |
| `dot` | 1 |
| `lstrip` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 25)

| Имя | Использований |
|-----|--------------:|
| `get` | 12 |
| `strip` | 6 |
| `findall` | 3 |
| `join` | 3 |
| `lower` | 3 |
| `append` | 3 |
| `sqrt` | 2 |
| `shape` | 2 |
| `mean` | 2 |
| `norm` | 2 |
| `startswith` | 2 |
| `linalg` | 2 |
| `compile` | 1 |
| `size` | 1 |
| `values` | 1 |
| `read` | 1 |
| `max` | 1 |
| `exists` | 1 |
| `split` | 1 |
| `splitlines` | 1 |
| `abs` | 1 |
| `sub` | 1 |
| `items` | 1 |
| `dot` | 1 |
| `lstrip` | 1 |

## Строковые литералы (уникальных: 80)

| Имя | Использований |
|-----|--------------:|
| `metrics` | 44 |
| `ok` | 34 |
| `reason` | 34 |
| `duration_sec` | 8 |
| `` | 8 |
| `readable` | 6 |
| `keys` | 4 |
| `characters` | 3 |
| `tokens` | 3 |
| `tags` | 3 |
| `unique_token_ratio` | 2 |
| `max_repeated_line` | 2 |
| `channels` | 2 |
| `peak` | 2 |
| `rms` | 2 |
| `input_duration_sec` | 2 |
| `duration_ratio` | 2 |
| `unique_ratio` | 2 |
| `title` | 2 |
| `stereo_correlation` | 2 |
| `stereo_side_rms` | 2 |
| ` ` | 2 |
| `missing` | 2 |
| `input` | 2 |
| `, ` | 2 |
| `[A-Za-zА-Яа-яЁё0-9']+` | 1 |
| `Вернуть воспроизводимые метрики длины и повторяемости текста песни.` | 1 |
| `Проверить минимальную пригодность текста для следующей audio-стадии.` | 1 |
| `Проверить минимальный контракт метаданных релиза из metadata_llm.` | 1 |
| `Измерить базовые объективные показатели WAV/аудиофайла без ML.` | 1 |
| `Отсечь пустой, короткий, silent или клиппующий audio output.` | 1 |
| `Проверить, что синтезированный вокал существует и не слишком короток для текста.` | 1 |
| `Проверить output RVC: аудио валидно и сохраняет временную структуру исходного вокала.` | 1 |
| `Проверить пригодность transcript, полученного ASR: содержательность и отсутствие зацикливания.` | 1 |
| `Проверить stem Demucs: пригодный audio output с длительностью исходного трека.` | 1 |
| `Проверить, что texture-artifact является слышимым и фактически стерео.` | 1 |
| `Проверить минимальный контракт JSON-ответа analysis_llm.` | 1 |
| `lines` | 1 |
| `sample_rate` | 1 |
| `text_tokens` | 1 |
| `expected_min_duration_sec` | 1 |
| `unique_tokens` | 1 |
| `empty lyrics` | 1 |
| `too few lyric tokens` | 1 |
| `line repetition exceeds hook limit` | 1 |
| `token diversity too low` | 1 |
| `metadata response is not an object` | 1 |
| `description` | 1 |
| `audio is empty` | 1 |
| `audio file missing` | 1 |
| `audio duration below minimum` | 1 |
| `audio is silent` | 1 |
| `audio clips` | 1 |
| `RVC input audio is unreadable` | 1 |
| `RVC output duration diverges from input` | 1 |
| `ASR transcript is empty or too short` | 1 |
| `ASR transcript is excessively repetitive` | 1 |
| `stem input audio is unreadable` | 1 |
| `stem duration diverges from input` | 1 |
| `texture is not stereo` | 1 |
| `stereo side energy too low` | 1 |
| `stereo channels are over-correlated` | 1 |
| `analysis response is not an object` | 1 |
| `storyline` | 1 |
| `hook` | 1 |
| `reusable_elements` | 1 |
| `core_themes` | 1 |
| `lexicon` | 1 |
| `flow` | 1 |
| `lyrics shorter than ` | 1 |
| ` characters` | 1 |
| `spotify_desc` | 1 |
| `youtube_desc` | 1 |
| `missing or invalid metadata fields: ` | 1 |
| `path` | 1 |
| `missing analysis fields: ` | 1 |
| `\s+` | 1 |
| `audio read failed: ` | 1 |
| `[` | 1 |
| `tags_` | 1 |

## Числовые литералы (уникальных: 27)

| Имя | Использований |
|-----|--------------:|
| `False` | 26 |
| `True` | 10 |
| `0` | 7 |
| `3` | 7 |
| `0.0` | 5 |
| `2` | 5 |
| `1.0` | 4 |
| `6` | 4 |
| `0.25` | 4 |
| `1` | 3 |
| `4` | 2 |
| `60` | 1 |
| `12` | 1 |
| `0.12` | 1 |
| `1e-05` | 1 |
| `1.0001` | 1 |
| `3.0` | 1 |
| `0.0005` | 1 |
| `0.995` | 1 |
| `120` | 1 |
| `0.85` | 1 |
| `1.15` | 1 |
| `0.95` | 1 |
| `1.05` | 1 |
| `1e-12` | 1 |
| `0.05` | 1 |
| `0.5` | 1 |
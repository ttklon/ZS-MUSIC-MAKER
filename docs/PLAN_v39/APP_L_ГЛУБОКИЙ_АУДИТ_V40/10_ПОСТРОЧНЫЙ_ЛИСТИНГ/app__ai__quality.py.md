# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/ai/quality.py`

**Всего строк:** 234

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 94 | 40.2 |
| return | 39 | 16.7 |
| branch | 33 | 14.1 |
| blank | 28 | 12.0 |
| docstring | 17 | 7.3 |
| def | 11 | 4.7 |
| import | 7 | 3.0 |
| comment | 2 | 0.9 |
| try_block | 2 | 0.9 |
| loop | 1 | 0.4 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """Лёгкие детерминированные проверки outputs локальных LLM-ролей.
    3 [blank     ] 
    4 [docstring ] Валидаторы не оценивают художественную ценность текста. Они отсекают только
    5 [docstring ] объективно непригодные результаты: пустой/слишком короткий ответ, чрезмерные
    6 [docstring ] дубли строк и неполное структурированное досье. Это позволяет честно включать
    7 [docstring ] fallback до сохранения артефакта на диск.
    8 [docstring ] """
    9 [import    ] from __future__ import annotations
   10 [blank     ] 
   11 [import    ] import re
   12 [import    ] from collections import Counter
   13 [import    ] from pathlib import Path
   14 [import    ] from typing import Any
   15 [blank     ] 
   16 [blank     ] 
   17 [code      ] TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9']+")
   18 [blank     ] 
   19 [blank     ] 
   20 [def       ] def lyrics_metrics(text: str) -> dict[str, float | int]:
   21 [docstring ]     """Вернуть воспроизводимые метрики длины и повторяемости текста песни."""
   22 [code      ]     normalized_lines = [
   23 [code      ]         re.sub(r"\s+", " ", line.strip()).lower()
   24 [loop      ]         for line in (text or "").splitlines()
   25 [branch    ]         if line.strip() and not line.lstrip().startswith("[")
   26 [code      ]     ]
   27 [code      ]     tokens = TOKEN_RE.findall((text or "").lower())
   28 [code      ]     line_counts = Counter(normalized_lines)
   29 [code      ]     max_repeated_line = max(line_counts.values(), default=0)
   30 [code      ]     unique_ratio = len(set(tokens)) / len(tokens) if tokens else 0.0
   31 [return    ]     return {
   32 [code      ]         "characters": len((text or "").strip()),
   33 [code      ]         "lines": len(normalized_lines),
   34 [code      ]         "tokens": len(tokens),
   35 [code      ]         "unique_token_ratio": round(unique_ratio, 3),
   36 [code      ]         "max_repeated_line": max_repeated_line,
   37 [code      ]     }
   38 [blank     ] 
   39 [blank     ] 
   40 [def       ] def validate_lyrics(text: str, *, min_characters: int = 60) -> dict[str, Any]:
   41 [docstring ]     """Проверить минимальную пригодность текста для следующей audio-стадии."""
   42 [code      ]     metrics = lyrics_metrics(text)
   43 [branch    ]     if not (text or "").strip():
   44 [return    ]         return {"ok": False, "reason": "empty lyrics", "metrics": metrics}
   45 [branch    ]     if metrics["characters"] < min_characters:
   46 [return    ]         return {
   47 [code      ]             "ok": False,
   48 [code      ]             "reason": f"lyrics shorter than {min_characters} characters",
   49 [code      ]             "metrics": metrics,
   50 [code      ]         }
   51 [branch    ]     if metrics["tokens"] < 12:
   52 [return    ]         return {"ok": False, "reason": "too few lyric tokens", "metrics": metrics}
   53 [comment   ]     # До четырёх повторов допустимы для припева; больше — признак зацикливания.
   54 [branch    ]     if metrics["max_repeated_line"] > 4:
   55 [return    ]         return {"ok": False, "reason": "line repetition exceeds hook limit", "metrics": metrics}
   56 [branch    ]     if metrics["unique_token_ratio"] < 0.12:
   57 [return    ]         return {"ok": False, "reason": "token diversity too low", "metrics": metrics}
   58 [return    ]     return {"ok": True, "reason": None, "metrics": metrics}
   59 [blank     ] 
   60 [blank     ] 
   61 [def       ] def validate_metadata_json(payload: Any) -> dict[str, Any]:
   62 [docstring ]     """Проверить минимальный контракт метаданных релиза из metadata_llm."""
   63 [branch    ]     if not isinstance(payload, dict):
   64 [return    ]         return {"ok": False, "reason": "metadata response is not an object", "metrics": {}}
   65 [code      ]     title = str(payload.get("title") or "").strip()
   66 [code      ]     descriptions = [str(payload.get(key) or "").strip() for key in ("spotify_desc", "youtube_desc")]
   67 [code      ]     missing = []
   68 [branch    ]     if not 2 <= len(title) <= 120:
   69 [code      ]         missing.append("title")
   70 [branch    ]     if not any(descriptions):
   71 [code      ]         missing.append("description")
   72 [code      ]     tag_count = sum(
   73 [code      ]         len(value) for key, value in payload.items()
   74 [branch    ]         if key.startswith("tags_") and isinstance(value, list)
   75 [code      ]     )
   76 [branch    ]     if tag_count == 0:
   77 [code      ]         missing.append("tags")
   78 [branch    ]     if missing:
   79 [return    ]         return {
   80 [code      ]             "ok": False,
   81 [code      ]             "reason": "missing or invalid metadata fields: " + ", ".join(missing),
   82 [code      ]             "metrics": {"keys": len(payload), "tags": tag_count},
   83 [code      ]         }
   84 [return    ]     return {"ok": True, "reason": None, "metrics": {"keys": len(payload), "tags": tag_count}}
   85 [blank     ] 
   86 [blank     ] 
   87 [def       ] def audio_metrics(path: str | Path) -> dict[str, Any]:
   88 [docstring ]     """Измерить базовые объективные показатели WAV/аудиофайла без ML."""
   89 [try_block ]     try:
   90 [import    ]         import numpy as np
   91 [import    ]         import soundfile as sf
   92 [blank     ] 
   93 [code      ]         samples, sample_rate = sf.read(str(path), always_2d=True)
   94 [try_block ]     except Exception as exc:
   95 [return    ]         return {"readable": False, "reason": f"audio read failed: {exc}"}
   96 [branch    ]     if samples.size == 0:
   97 [return    ]         return {"readable": False, "reason": "audio is empty"}
   98 [code      ]     peak = float(np.max(np.abs(samples)))
   99 [code      ]     rms = float(np.sqrt(np.mean(samples ** 2)))
  100 [code      ]     duration = len(samples) / sample_rate
  101 [code      ]     metrics = {
  102 [code      ]         "readable": True,
  103 [code      ]         "duration_sec": round(duration, 3),
  104 [code      ]         "sample_rate": int(sample_rate),
  105 [code      ]         "channels": int(samples.shape[1]),
  106 [code      ]         "peak": round(peak, 6),
  107 [code      ]         "rms": round(rms, 6),
  108 [code      ]     }
  109 [branch    ]     if samples.shape[1] >= 2:
  110 [code      ]         left, right = samples[:, 0], samples[:, 1]
  111 [code      ]         denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
  112 [code      ]         correlation = float(np.dot(left, right) / denominator) if denominator > 1e-12 else 1.0
  113 [code      ]         metrics["stereo_correlation"] = round(correlation, 6)
  114 [code      ]         metrics["stereo_side_rms"] = round(float(np.sqrt(np.mean(((left - right) * 0.5) ** 2))), 6)
  115 [return    ]     return metrics
  116 [blank     ] 
  117 [blank     ] 
  118 [def       ] def validate_audio_artifact(path: str | Path, *, min_duration_sec: float = 1.0) -> dict[str, Any]:
  119 [docstring ]     """Отсечь пустой, короткий, silent или клиппующий audio output."""
  120 [code      ]     target = Path(path)
  121 [branch    ]     if not target.exists():
  122 [return    ]         return {"ok": False, "reason": "audio file missing", "metrics": {"path": str(target)}}
  123 [code      ]     metrics = audio_metrics(target)
  124 [branch    ]     if not metrics.get("readable"):
  125 [return    ]         return {"ok": False, "reason": metrics.get("reason"), "metrics": metrics}
  126 [branch    ]     if metrics["duration_sec"] < min_duration_sec:
  127 [return    ]         return {"ok": False, "reason": "audio duration below minimum", "metrics": metrics}
  128 [branch    ]     if metrics["rms"] < 1e-5:
  129 [return    ]         return {"ok": False, "reason": "audio is silent", "metrics": metrics}
  130 [branch    ]     if metrics["peak"] > 1.0001:
  131 [return    ]         return {"ok": False, "reason": "audio clips", "metrics": metrics}
  132 [return    ]     return {"ok": True, "reason": None, "metrics": metrics}
  133 [blank     ] 
  134 [blank     ] 
  135 [def       ] def validate_vocal_artifact(path: str | Path, text: str) -> dict[str, Any]:
  136 [docstring ]     """Проверить, что синтезированный вокал существует и не слишком короток для текста."""
  137 [code      ]     token_count = len(TOKEN_RE.findall(text or ""))
  138 [code      ]     expected_min_duration = min(3.0, max(0.25, token_count * 0.05))
  139 [code      ]     result = validate_audio_artifact(path, min_duration_sec=expected_min_duration)
  140 [code      ]     result["metrics"]["text_tokens"] = token_count
  141 [code      ]     result["metrics"]["expected_min_duration_sec"] = round(expected_min_duration, 3)
  142 [return    ]     return result
  143 [blank     ] 
  144 [blank     ] 
  145 [def       ] def validate_rvc_artifact(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
  146 [docstring ]     """Проверить output RVC: аудио валидно и сохраняет временную структуру исходного вокала."""
  147 [code      ]     source = audio_metrics(input_path)
  148 [branch    ]     if not source.get("readable"):
  149 [return    ]         return {"ok": False, "reason": "RVC input audio is unreadable", "metrics": {"input": source}}
  150 [code      ]     result = validate_audio_artifact(output_path, min_duration_sec=0.25)
  151 [code      ]     result["metrics"]["input_duration_sec"] = source.get("duration_sec")
  152 [branch    ]     if not result["ok"]:
  153 [return    ]         return result
  154 [code      ]     input_duration = float(source["duration_sec"])
  155 [code      ]     output_duration = float(result["metrics"]["duration_sec"])
  156 [code      ]     ratio = output_duration / input_duration if input_duration > 0 else 0.0
  157 [code      ]     result["metrics"]["duration_ratio"] = round(ratio, 3)
  158 [branch    ]     if not 0.85 <= ratio <= 1.15:
  159 [return    ]         return {"ok": False, "reason": "RVC output duration diverges from input", "metrics": result["metrics"]}
  160 [return    ]     return {"ok": True, "reason": None, "metrics": result["metrics"]}
  161 [blank     ] 
  162 [blank     ] 
  163 [def       ] def validate_asr_transcript(text: str) -> dict[str, Any]:
  164 [docstring ]     """Проверить пригодность transcript, полученного ASR: содержательность и отсутствие зацикливания."""
  165 [code      ]     normalized = " ".join((text or "").split())
  166 [code      ]     tokens = TOKEN_RE.findall(normalized.lower())
  167 [code      ]     unique_tokens = len(set(tokens))
  168 [code      ]     metrics = {
  169 [code      ]         "characters": len(normalized),
  170 [code      ]         "tokens": len(tokens),
  171 [code      ]         "unique_tokens": unique_tokens,
  172 [code      ]         "unique_ratio": round(unique_tokens / len(tokens), 3) if tokens else 0.0,
  173 [code      ]     }
  174 [branch    ]     if len(normalized) < 3 or not tokens:
  175 [return    ]         return {"ok": False, "reason": "ASR transcript is empty or too short", "metrics": metrics}
  176 [branch    ]     if len(tokens) >= 4 and metrics["unique_ratio"] <= 0.25:
  177 [return    ]         return {"ok": False, "reason": "ASR transcript is excessively repetitive", "metrics": metrics}
  178 [return    ]     return {"ok": True, "reason": None, "metrics": metrics}
  179 [blank     ] 
  180 [blank     ] 
  181 [def       ] def validate_stem_artifact(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
  182 [docstring ]     """Проверить stem Demucs: пригодный audio output с длительностью исходного трека."""
  183 [code      ]     source = audio_metrics(input_path)
  184 [branch    ]     if not source.get("readable"):
  185 [return    ]         return {"ok": False, "reason": "stem input audio is unreadable", "metrics": {"input": source}}
  186 [code      ]     result = validate_audio_artifact(output_path, min_duration_sec=0.25)
  187 [code      ]     result["metrics"]["input_duration_sec"] = source.get("duration_sec")
  188 [branch    ]     if not result["ok"]:
  189 [return    ]         return result
  190 [code      ]     input_duration = float(source["duration_sec"])
  191 [code      ]     ratio = float(result["metrics"]["duration_sec"]) / input_duration if input_duration > 0 else 0.0
  192 [code      ]     result["metrics"]["duration_ratio"] = round(ratio, 3)
  193 [branch    ]     if not 0.95 <= ratio <= 1.05:
  194 [return    ]         return {"ok": False, "reason": "stem duration diverges from input", "metrics": result["metrics"]}
  195 [return    ]     return {"ok": True, "reason": None, "metrics": result["metrics"]}
  196 [blank     ] 
  197 [blank     ] 
  198 [def       ] def validate_stereo_texture(path: str | Path, *, min_duration_sec: float = 1.0) -> dict[str, Any]:
  199 [docstring ]     """Проверить, что texture-artifact является слышимым и фактически стерео."""
  200 [code      ]     base = validate_audio_artifact(path, min_duration_sec=min_duration_sec)
  201 [branch    ]     if not base["ok"]:
  202 [return    ]         return base
  203 [code      ]     metrics = base["metrics"]
  204 [branch    ]     if metrics.get("channels") != 2:
  205 [return    ]         return {"ok": False, "reason": "texture is not stereo", "metrics": metrics}
  206 [branch    ]     if metrics.get("stereo_side_rms", 0.0) < 5e-4:
  207 [return    ]         return {"ok": False, "reason": "stereo side energy too low", "metrics": metrics}
  208 [branch    ]     if abs(metrics.get("stereo_correlation", 1.0)) > 0.995:
  209 [return    ]         return {"ok": False, "reason": "stereo channels are over-correlated", "metrics": metrics}
  210 [return    ]     return {"ok": True, "reason": None, "metrics": metrics}
  211 [blank     ] 
  212 [blank     ] 
  213 [def       ] def validate_analysis_json(payload: Any, *, track_level: bool = False) -> dict[str, Any]:
  214 [docstring ]     """Проверить минимальный контракт JSON-ответа analysis_llm."""
  215 [branch    ]     if not isinstance(payload, dict):
  216 [return    ]         return {"ok": False, "reason": "analysis response is not an object", "metrics": {}}
  217 [blank     ] 
  218 [code      ]     required = ("storyline", "hook", "reusable_elements") if track_level else (
  219 [code      ]         "core_themes",
  220 [code      ]         "lexicon",
  221 [code      ]         "flow",
  222 [code      ]     )
  223 [code      ]     missing = [key for key in required if not payload.get(key)]
  224 [branch    ]     if missing:
  225 [return    ]         return {
  226 [code      ]             "ok": False,
  227 [code      ]             "reason": "missing analysis fields: " + ", ".join(missing),
  228 [code      ]             "metrics": {"keys": len(payload), "missing": len(missing)},
  229 [code      ]         }
  230 [return    ]     return {
  231 [code      ]         "ok": True,
  232 [code      ]         "reason": None,
  233 [code      ]         "metrics": {"keys": len(payload), "missing": 0},
  234 [code      ]     }
```
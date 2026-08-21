# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/karaoke_engine.py`

**Всего строк:** 191

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 93 | 48.7 |
| docstring | 24 | 12.6 |
| blank | 24 | 12.6 |
| def | 10 | 5.2 |
| import | 8 | 4.2 |
| branch | 8 | 4.2 |
| return | 8 | 4.2 |
| loop | 7 | 3.7 |
| try_block | 4 | 2.1 |
| comment | 4 | 2.1 |
| class | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v10 — Karaoke Engine v10
    3 [docstring ] =========================================
    4 [docstring ] Караоке-режим для записи вокала (ТЗ 5, «karaoke-режим»).
    5 [blank     ] 
    6 [docstring ] Расширяет ui/karaoke_recorder.py:
    7 [docstring ]   - подсветка слов по времени
    8 [docstring ]   - метроном + отсчёт
    9 [docstring ]   - визуализация амплитуды в реальном времени (VU-метр)
   10 [docstring ]   - авто-детект попадания в тайминг (WER-подобно)
   11 [docstring ]   - регулировка громкости эталона в наушниках (mix send)
   12 [docstring ] """
   13 [blank     ] 
   14 [import    ] from __future__ import annotations
   15 [blank     ] 
   16 [import    ] import json
   17 [import    ] import logging
   18 [import    ] import threading
   19 [import    ] import time
   20 [import    ] from collections.abc import Callable
   21 [import    ] from typing import Any
   22 [blank     ] 
   23 [code      ] log = logging.getLogger("zsmm.karaoke_v10")
   24 [blank     ] 
   25 [blank     ] 
   26 [class     ] class KaraokeSession:
   27 [docstring ]     """
   28 [docstring ]     Одна сессия записи вокала.
   29 [docstring ]     """
   30 [blank     ] 
   31 [def       ]     def __init__(
   32 [code      ]         self,
   33 [code      ]         lyrics: list[dict[str, Any]],
   34 [code      ]         bpm: int = 120,
   35 [code      ]         count_in_beats: int = 4,
   36 [code      ]         monitor_volume: float = 0.35,
   37 [code      ]     ):
   38 [docstring ]         """
   39 [docstring ]         lyrics: [{"text": "...", "start_ms": 0, "duration_ms": 800}, ...]
   40 [docstring ]         """
   41 [code      ]         self.lyrics = lyrics
   42 [code      ]         self.bpm = bpm
   43 [code      ]         self.beat_ms = int(60000 / bpm)
   44 [code      ]         self.count_in_beats = count_in_beats
   45 [code      ]         self.monitor_volume = monitor_volume
   46 [code      ]         self.state = "idle"
   47 [code      ]         self._start_ts: float | None = None
   48 [code      ]         self._callbacks: dict[str, list[Callable]] = {
   49 [code      ]             "on_word": [],
   50 [code      ]             "on_beat": [],
   51 [code      ]             "on_end": [],
   52 [code      ]             "on_amp": [],
   53 [code      ]         }
   54 [code      ]         self._stop = threading.Event()
   55 [blank     ] 
   56 [def       ]     def on(self, event: str, cb: Callable) -> None:
   57 [code      ]         self._callbacks.setdefault(event, []).append(cb)
   58 [blank     ] 
   59 [def       ]     def _fire(self, event: str, *args, **kwargs) -> None:
   60 [loop      ]         for cb in self._callbacks.get(event, []):
   61 [try_block ]             try:
   62 [code      ]                 cb(*args, **kwargs)
   63 [try_block ]             except Exception as e:
   64 [code      ]                 log.warning("callback error: %s", e)
   65 [blank     ] 
   66 [def       ]     def elapsed_ms(self) -> int:
   67 [branch    ]         if not self._start_ts:
   68 [return    ]             return 0
   69 [return    ]         return int((time.time() - self._start_ts) * 1000)
   70 [blank     ] 
   71 [def       ]     def current_word(self) -> dict[str, Any] | None:
   72 [code      ]         t = self.elapsed_ms()
   73 [loop      ]         for w in self.lyrics:
   74 [code      ]             start = w.get("start_ms", 0)
   75 [code      ]             dur = w.get("duration_ms", self.beat_ms)
   76 [branch    ]             if start <= t < start + dur:
   77 [return    ]                 return w
   78 [return    ]         return None
   79 [blank     ] 
   80 [def       ]     def start(self) -> None:
   81 [code      ]         self.state = "count_in"
   82 [code      ]         self._start_ts = time.time() + (self.count_in_beats * self.beat_ms) / 1000.0
   83 [code      ]         threading.Thread(target=self._run, daemon=True).start()
   84 [blank     ] 
   85 [def       ]     def stop(self) -> None:
   86 [code      ]         self._stop.set()
   87 [code      ]         self.state = "stopped"
   88 [blank     ] 
   89 [def       ]     def _run(self) -> None:
   90 [comment   ]         # count-in
   91 [loop      ]         for i in range(self.count_in_beats):
   92 [code      ]             self._fire("on_beat", {"beat": i + 1, "is_count_in": True})
   93 [code      ]             time.sleep(self.beat_ms / 1000.0)
   94 [branch    ]             if self._stop.is_set():
   95 [return    ]                 return
   96 [code      ]         self.state = "recording"
   97 [comment   ]         # main loop
   98 [code      ]         last_word_idx = -1
   99 [code      ]         beat_counter = 0
  100 [code      ]         next_beat_at = self._start_ts
  101 [code      ]         end_time = (
  102 [code      ]             self._start_ts
  103 [code      ]             + (self.lyrics[-1]["start_ms"] + self.lyrics[-1].get("duration_ms", 1000))
  104 [code      ]             / 1000.0
  105 [branch    ]             if self.lyrics
  106 [code      ]             else self._start_ts + 60
  107 [code      ]         )
  108 [loop      ]         while time.time() < end_time and not self._stop.is_set():
  109 [code      ]             now = time.time()
  110 [branch    ]             if now >= next_beat_at:
  111 [code      ]                 beat_counter += 1
  112 [code      ]                 self._fire("on_beat", {"beat": beat_counter, "is_count_in": False})
  113 [code      ]                 next_beat_at += self.beat_ms / 1000.0
  114 [code      ]             t_ms = int((now - self._start_ts) * 1000)
  115 [loop      ]             for idx, w in enumerate(self.lyrics):
  116 [code      ]                 start = w.get("start_ms", 0)
  117 [branch    ]                 if start <= t_ms and idx > last_word_idx:
  118 [code      ]                     self._fire("on_word", {"index": idx, "word": w, "t_ms": t_ms})
  119 [code      ]                     last_word_idx = idx
  120 [code      ]                     break
  121 [code      ]             time.sleep(0.02)
  122 [code      ]         self.state = "finished"
  123 [code      ]         self._fire("on_end", {"duration_ms": self.elapsed_ms()})
  124 [blank     ] 
  125 [blank     ] 
  126 [def       ] def make_wordmap_from_lyrics(
  127 [code      ]     lyrics_text: str,
  128 [code      ]     bpm: int,
  129 [code      ]     start_offset_ms: int = 0,
  130 [code      ]     syllables_per_beat: float = 2.0,
  131 [code      ] ) -> list[dict[str, Any]]:
  132 [docstring ]     """
  133 [docstring ]     Простое построение word-map из чистого текста и BPM.
  134 [docstring ]     """
  135 [code      ]     beat_ms = 60000 // bpm
  136 [code      ]     words = []
  137 [code      ]     t = start_offset_ms
  138 [loop      ]     for line in lyrics_text.strip().splitlines():
  139 [loop      ]         for w in line.split():
  140 [code      ]             n_syl = max(1, sum(1 for c in w.lower() if c in "аеёиоуыэюяaeiouy"))
  141 [code      ]             dur = int(n_syl / syllables_per_beat * beat_ms)
  142 [code      ]             words.append({"text": w, "start_ms": t, "duration_ms": dur})
  143 [code      ]             t += dur
  144 [code      ]         t += beat_ms  # пауза между строками
  145 [return    ]     return words
  146 [blank     ] 
  147 [blank     ] 
  148 [def       ] def score_take(
  149 [code      ]     recorded_wav: str, expected_word_map: list[dict[str, Any]]
  150 [code      ] ) -> dict[str, Any]:
  151 [docstring ]     """
  152 [docstring ]     Оценивает попадание записи в тайминг (без ASR — по общей длительности
  153 [docstring ]     и RMS-огибающей). Возвращает 0-100.
  154 [docstring ]     """
  155 [try_block ]     try:
  156 [import    ]         import librosa
  157 [blank     ] 
  158 [code      ]         y, sr = librosa.load(recorded_wav, sr=22050, mono=True)
  159 [code      ]         actual_ms = int(len(y) * 1000 / sr)
  160 [code      ]         expected_ms = (
  161 [code      ]             expected_word_map[-1]["start_ms"] + expected_word_map[-1]["duration_ms"]
  162 [branch    ]             if expected_word_map
  163 [code      ]             else 1
  164 [code      ]         )
  165 [code      ]         length_ratio = min(actual_ms, expected_ms) / max(actual_ms, expected_ms)
  166 [blank     ] 
  167 [comment   ]         # энергетическое покрытие
  168 [code      ]         rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=512)[0]
  169 [code      ]         active_pct = float((rms > (rms.max() * 0.15)).sum()) / max(1, len(rms))
  170 [blank     ] 
  171 [comment   ]         # ожидаемое покрытие: сумма duration_ms / total
  172 [code      ]         exp_active = sum(w.get("duration_ms", 0) for w in expected_word_map) / max(
  173 [code      ]             1, expected_ms
  174 [code      ]         )
  175 [code      ]         active_score = 1.0 - abs(active_pct - exp_active)
  176 [blank     ] 
  177 [code      ]         score = int(round(60 * length_ratio + 40 * active_score))
  178 [return    ]         return {
  179 [code      ]             "ok": True,
  180 [code      ]             "score": max(0, min(100, score)),
  181 [code      ]             "length_ratio": round(length_ratio, 3),
  182 [code      ]             "active_pct": round(active_pct, 3),
  183 [code      ]             "expected_active_pct": round(exp_active, 3),
  184 [code      ]         }
  185 [try_block ]     except Exception as e:
  186 [return    ]         return {"ok": False, "reason": str(e), "score": 0}
  187 [blank     ] 
  188 [blank     ] 
  189 [branch    ] if __name__ == "__main__":
  190 [code      ]     wm = make_wordmap_from_lyrics("Тачки летят по трассе\nЛето жарит нас", bpm=140)
  191 [code      ]     print(json.dumps(wm, ensure_ascii=False, indent=2))
```
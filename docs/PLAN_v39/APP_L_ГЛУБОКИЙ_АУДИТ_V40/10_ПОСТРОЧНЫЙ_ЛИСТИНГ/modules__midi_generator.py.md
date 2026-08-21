# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/midi_generator.py`

**Всего строк:** 204

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 78 | 38.2 |
| docstring | 29 | 14.2 |
| blank | 27 | 13.2 |
| branch | 22 | 10.8 |
| comment | 19 | 9.3 |
| return | 7 | 3.4 |
| try_block | 6 | 2.9 |
| def | 5 | 2.5 |
| loop | 5 | 2.5 |
| import | 4 | 2.0 |
| class | 1 | 0.5 |
| decorator | 1 | 0.5 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — midi_generator.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Алгоритмическая генерация MIDI паттернов.
    6 [docstring ] Использует mido для создания MIDI файлов и паттернов для разных жанров.
    7 [blank     ] 
    8 [docstring ] v29 FIX (P0):
    9 [docstring ]   * generate_melody_pattern() падал `TypeError: 'NoneType' object is not
   10 [docstring ]     callable` когда mido не установлен — не было guard'а как в drum-версии.
   11 [docstring ]     Это валило весь God Mode pipeline на стадии midi_generation.
   12 [docstring ]   * Возврат "" при отсутствии mido трактовался ядром как fallback без
   13 [docstring ]     файла (валидно), но orchestrator_god ожидал dict {ok,...}. Оставляем
   14 [docstring ]     строковый путь (совместимо со стадией), но при отсутствии mido —
   15 [docstring ]     честный BLOCKED-return без исключения.
   16 [docstring ]   * Добавлен guard в generate_melody_pattern.
   17 [docstring ]   * Убран дубликат `if not _HAS_MIDO: return ""` в drum-версии.
   18 [docstring ]   * Определены расширенные жанровые паттерны (trap/phonk/drift/techno/
   19 [docstring ]     hiphop) с более музыкальной ритмикой.
   20 [docstring ]   * Добавлена get_status() для честного отчёта о доступности.
   21 [docstring ] """
   22 [blank     ] 
   23 [import    ] import os
   24 [import    ] import random
   25 [blank     ] 
   26 [blank     ] 
   27 [comment   ] # v27 FIX (P0): mido был жёстким top-level импортом — без него падал
   28 [comment   ] # orchestrator_god. Ленивый импорт: MIDI-генерация помечается BLOCKED,
   29 [comment   ] # если mido не установлен, но импорт модуля не ломается.
   30 [try_block ] try:
   31 [import    ]     import mido  # type: ignore
   32 [import    ]     from mido import Message, MidiFile, MidiTrack  # type: ignore
   33 [code      ]     _HAS_MIDO = True
   34 [try_block ] except Exception:  # pragma: no cover
   35 [code      ]     mido = None
   36 [code      ]     Message = MidiFile = MidiTrack = None  # type: ignore
   37 [code      ]     _HAS_MIDO = False
   38 [blank     ] 
   39 [blank     ] 
   40 [class     ] class MIDIGenerator:
   41 [docstring ]     """Алгоритмический MIDI-генератор с honest BLOCKED-fallback."""
   42 [blank     ] 
   43 [def       ]     def __init__(self, output_dir: str = "output/midi"):
   44 [code      ]         self.output_dir = output_dir
   45 [comment   ]         # v22-style: lazy dir — не создаём при импорте, только когда пишем
   46 [code      ]         self._dir_ready = False
   47 [blank     ] 
   48 [def       ]     def _ensure_dir(self) -> None:
   49 [branch    ]         if not self._dir_ready:
   50 [code      ]             os.makedirs(self.output_dir, exist_ok=True)
   51 [code      ]             self._dir_ready = True
   52 [blank     ] 
   53 [decorator ]     @staticmethod
   54 [def       ]     def get_status() -> dict:
   55 [docstring ]         """Возвращает честный статус движка."""
   56 [return    ]         return {
   57 [code      ]             "ok": _HAS_MIDO,
   58 [code      ]             "engine": "mido" if _HAS_MIDO else "BLOCKED",
   59 [code      ]             "reason": None if _HAS_MIDO else "mido not installed — MIDI export disabled, honest fallback",
   60 [code      ]         }
   61 [blank     ] 
   62 [comment   ]     # ------------------------------------------------------------------ #
   63 [comment   ]     #  DRUM PATTERN
   64 [comment   ]     # ------------------------------------------------------------------ #
   65 [def       ]     def generate_drum_pattern(self, genre: str, bpm: int) -> str:
   66 [docstring ]         """Генерирует MIDI барабанный паттерн в зависимости от жанра.
   67 [blank     ] 
   68 [docstring ]         Возвращает путь к .mid или "" если mido недоступен (honest BLOCKED).
   69 [docstring ]         Не бросает исключения при отсутствии mido — это критично для God Mode.
   70 [docstring ]         """
   71 [branch    ]         if not _HAS_MIDO:
   72 [return    ]             return ""  # BLOCKED: mido not installed (honest, non-fatal)
   73 [blank     ] 
   74 [try_block ]         try:
   75 [code      ]             self._ensure_dir()
   76 [code      ]             mid = MidiFile()
   77 [code      ]             track = MidiTrack()
   78 [code      ]             mid.tracks.append(track)
   79 [blank     ] 
   80 [code      ]             tempo = mido.bpm2tempo(max(40, min(int(bpm), 240)))
   81 [code      ]             track.append(mido.MetaMessage('set_tempo', tempo=tempo))
   82 [blank     ] 
   83 [code      ]             ticks_per_16th = max(1, mid.ticks_per_beat // 4)
   84 [code      ]             g = (genre or "").lower()
   85 [blank     ] 
   86 [branch    ]             if "techno" in g or "house" in g:
   87 [comment   ]                 # 4-on-the-floor kick + off-beat hats
   88 [loop      ]                 for i in range(16):
   89 [branch    ]                     if i % 4 == 0:
   90 [code      ]                         track.append(Message('note_on', note=36, velocity=110, time=0))
   91 [code      ]                         track.append(Message('note_off', note=36, velocity=110, time=ticks_per_16th))
   92 [branch    ]                     else:
   93 [code      ]                         track.append(Message('note_on', note=42, velocity=78, time=0))
   94 [code      ]                         track.append(Message('note_off', note=42, velocity=78, time=ticks_per_16th))
   95 [branch    ]             elif "phonk" in g or "drift" in g:
   96 [comment   ]                 # Cowbell + syncopated kick — classic drift-phonk
   97 [loop      ]                 for i in range(16):
   98 [branch    ]                     if i in (0, 6, 10):
   99 [code      ]                         note, vel = 36, 118
  100 [branch    ]                     elif i in (4, 12):
  101 [code      ]                         note, vel = 38, 100
  102 [branch    ]                     elif i == 8:
  103 [code      ]                         note, vel = 56, 90  # cowbell
  104 [branch    ]                     else:
  105 [code      ]                         note, vel = 42, 70
  106 [code      ]                     track.append(Message('note_on', note=note, velocity=vel, time=0))
  107 [code      ]                     track.append(Message('note_off', note=note, velocity=vel, time=ticks_per_16th))
  108 [branch    ]             elif "trap" in g or "hiphop" in g or "hip-hop" in g:
  109 [comment   ]                 # Trap: kick/snare + rolling hats
  110 [loop      ]                 for i in range(16):
  111 [branch    ]                     if i == 0 or i == 10:
  112 [code      ]                         note, vel = 36, 115
  113 [branch    ]                     elif i in (4, 12):
  114 [code      ]                         note, vel = 38, 105
  115 [branch    ]                     else:
  116 [comment   ]                         # rolling hats with velocity variation
  117 [code      ]                         note = 42
  118 [code      ]                         vel = random.randint(55, 95)
  119 [code      ]                     track.append(Message('note_on', note=note, velocity=vel, time=0))
  120 [code      ]                     track.append(Message('note_off', note=note, velocity=vel, time=ticks_per_16th))
  121 [branch    ]             else:
  122 [comment   ]                 # Default: pop-rock 4/4
  123 [loop      ]                 for i in range(16):
  124 [branch    ]                     if i in (0, 8):
  125 [code      ]                         note, vel = 36, 108
  126 [branch    ]                     elif i in (4, 12):
  127 [code      ]                         note, vel = 38, 102
  128 [branch    ]                     else:
  129 [code      ]                         note, vel = 42, random.randint(70, 90)
  130 [code      ]                     track.append(Message('note_on', note=note, velocity=vel, time=0))
  131 [code      ]                     track.append(Message('note_off', note=note, velocity=vel, time=ticks_per_16th))
  132 [blank     ] 
  133 [code      ]             safe_genre = "".join(c for c in g if c.isalnum() or c in ("_", "-")) or "gen"
  134 [code      ]             out_path = os.path.join(self.output_dir, f"{safe_genre}_drums.mid")
  135 [code      ]             mid.save(out_path)
  136 [return    ]             return out_path
  137 [try_block ]         except Exception as e:
  138 [code      ]             print(f"[midi_generator] drum error: {e}")
  139 [return    ]             return ""
  140 [blank     ] 
  141 [comment   ]     # ------------------------------------------------------------------ #
  142 [comment   ]     #  MELODY PATTERN  (v29 P0 fix — добавлен guard)
  143 [comment   ]     # ------------------------------------------------------------------ #
  144 [def       ]     def generate_melody_pattern(
  145 [code      ]         self,
  146 [code      ]         genre: str,
  147 [code      ]         key_root: str = "A",
  148 [code      ]         mode: str = "minor",
  149 [code      ]         bpm: int = 120,
  150 [code      ]     ) -> str:
  151 [docstring ]         """Генерирует MIDI мелодию на основе музыкальной теории.
  152 [blank     ] 
  153 [docstring ]         v29 P0: раньше падал TypeError при отсутствии mido — валил God Mode.
  154 [docstring ]         Теперь: honest BLOCKED-return "" вместо исключения.
  155 [docstring ]         """
  156 [branch    ]         if not _HAS_MIDO:
  157 [return    ]             return ""  # BLOCKED: mido not installed
  158 [blank     ] 
  159 [try_block ]         try:
  160 [code      ]             self._ensure_dir()
  161 [blank     ] 
  162 [comment   ]             # Гаммы: MIDI-ноты для root + intervals
  163 [code      ]             root_map = {"C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65,
  164 [code      ]                         "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71}
  165 [code      ]             root = root_map.get((key_root or "A").upper(), 69)
  166 [branch    ]             if (mode or "minor").lower().startswith("min"):
  167 [code      ]                 intervals = [0, 2, 3, 5, 7, 8, 10, 12]  # natural minor
  168 [branch    ]             else:
  169 [code      ]                 intervals = [0, 2, 4, 5, 7, 9, 11, 12]  # major
  170 [code      ]             scale = [root + iv for iv in intervals]
  171 [blank     ] 
  172 [code      ]             mid = MidiFile()
  173 [code      ]             track = MidiTrack()
  174 [code      ]             mid.tracks.append(track)
  175 [blank     ] 
  176 [code      ]             tempo = mido.bpm2tempo(max(40, min(int(bpm), 240)))
  177 [code      ]             track.append(mido.MetaMessage('set_tempo', tempo=tempo))
  178 [blank     ] 
  179 [code      ]             ticks_per_8th = max(1, mid.ticks_per_beat // 2)
  180 [blank     ] 
  181 [comment   ]             # 16 нот с музыкальной логикой (весовое приближение к тонике)
  182 [code      ]             weights = [3, 1, 2, 1, 2, 1, 1, 3]
  183 [loop      ]             for step in range(16):
  184 [comment   ]                 # Разная длительность (варьируем 8th и 16th)
  185 [code      ]                 dur = ticks_per_8th if step % 2 == 0 else ticks_per_8th // 2
  186 [code      ]                 note = random.choices(scale, weights=weights, k=1)[0]
  187 [code      ]                 vel = random.randint(64, 96)
  188 [code      ]                 track.append(Message('note_on', note=note, velocity=vel, time=0))
  189 [code      ]                 track.append(Message('note_off', note=note, velocity=vel, time=dur))
  190 [blank     ] 
  191 [code      ]             safe_genre = "".join(c for c in (genre or "gen").lower() if c.isalnum() or c in ("_", "-")) or "gen"
  192 [code      ]             out_path = os.path.join(self.output_dir, f"{safe_genre}_melody.mid")
  193 [code      ]             mid.save(out_path)
  194 [return    ]             return out_path
  195 [try_block ]         except Exception as e:
  196 [code      ]             print(f"[midi_generator] melody error: {e}")
  197 [return    ]             return ""
  198 [blank     ] 
  199 [blank     ] 
  200 [branch    ] if __name__ == "__main__":
  201 [code      ]     gen = MIDIGenerator()
  202 [code      ]     print("Status:", gen.get_status())
  203 [code      ]     print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
  204 [code      ]     print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")
```
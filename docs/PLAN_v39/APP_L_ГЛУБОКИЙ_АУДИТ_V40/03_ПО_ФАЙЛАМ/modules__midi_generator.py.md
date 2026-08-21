# АУДИТ ФАЙЛА: `modules/midi_generator.py`

**LOC:** 204  |  **Размер:** 9695 байт  |  **Проблем:** 6  |  **Risk score:** 2

## Импорты

| Строка | Имя | Вид |
|-------:|-----|-----|
| 23 | `os` | import |
| 24 | `random` | import |
| 31 | `mido` | import |
| 32 | `mido.Message` | from |
| 32 | `mido.MidiFile` | from |
| 32 | `mido.MidiTrack` | from |

## Функции

| Строка | Имя | LOC | Complexity | Docstring |
|-------:|-----|----:|-----------:|-----------|
| 43 | `__init__` | 3 | 0 | ❌ |
| 48 | `_ensure_dir` | 3 | 1 | ❌ |
| 54 | `get_status` | 6 | 0 | ✅ |
| 65 | `generate_drum_pattern` | 74 | 24 | ✅ |
| 144 | `generate_melody_pattern` | 53 | 9 | ✅ |

## Классы

| Строка | Имя | Docstring |
|-------:|-----|-----------|
| 40 | `MIDIGenerator` | ✅ |

## Проблемы (детально, с цитатой кода)

### BARE_PRINT — 5 шт. — 🟢 LOW
**Смысл:** print() вместо logger
**Fix:** `print(x)` → `logger.info(x)`.

- **строка 138** — print() вместо logger

  ```
        136 |             return out_path
        137 |         except Exception as e:
  >>>   138 |             print(f"[midi_generator] drum error: {e}")
        139 |             return ""
        140 | 
  ```

- **строка 196** — print() вместо logger

  ```
        194 |             return out_path
        195 |         except Exception as e:
  >>>   196 |             print(f"[midi_generator] melody error: {e}")
        197 |             return ""
        198 | 
  ```

- **строка 202** — print() вместо logger

  ```
        200 | if __name__ == "__main__":
        201 |     gen = MIDIGenerator()
  >>>   202 |     print("Status:", gen.get_status())
        203 |     print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
        204 |     print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")
  ```

- **строка 203** — print() вместо logger

  ```
        201 |     gen = MIDIGenerator()
        202 |     print("Status:", gen.get_status())
  >>>   203 |     print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
        204 |     print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")
  ```

- **строка 204** — print() вместо logger

  ```
        202 |     print("Status:", gen.get_status())
        203 |     print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
  >>>   204 |     print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")
  ```

### HIGH_COMPLEXITY — 1 шт. — 🟡 MEDIUM
**Смысл:** Цикломатическая сложность > 15
**Fix:** Разбить на подфункции; if-цепочки → dict-диспатчер.

- **строка 65** — generate_drum_pattern: сложность ≈ 24 (>15)

  ```
         63 |     #  DRUM PATTERN
         64 |     # ------------------------------------------------------------------ #
  >>>    65 |     def generate_drum_pattern(self, genre: str, bpm: int) -> str:
         66 |         """Генерирует MIDI барабанный паттерн в зависимости от жанра.
         67 | 
  ```

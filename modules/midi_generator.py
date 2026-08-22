# -*- coding: utf-8 -*-
"""
ZS Music Maker — midi_generator.py (GOD MODE)
========================================================================
Алгоритмическая генерация MIDI паттернов.
Использует mido для создания MIDI файлов и паттернов для разных жанров.

v29 FIX (P0):
  * generate_melody_pattern() падал `TypeError: 'NoneType' object is not
    callable` когда mido не установлен — не было guard'а как в drum-версии.
    Это валило весь God Mode pipeline на стадии midi_generation.
  * Возврат "" при отсутствии mido трактовался ядром как fallback без
    файла (валидно), но orchestrator_god ожидал dict {ok,...}. Оставляем
    строковый путь (совместимо со стадией), но при отсутствии mido —
    честный BLOCKED-return без исключения.
  * Добавлен guard в generate_melody_pattern.
  * Убран дубликат `if not _HAS_MIDO: return ""` в drum-версии.
  * Определены расширенные жанровые паттерны (trap/phonk/drift/techno/
    hiphop) с более музыкальной ритмикой.
  * Добавлена get_status() для честного отчёта о доступности.
"""

import logging
import os
import random


# v27 FIX (P0): mido был жёстким top-level импортом — без него падал
# orchestrator_god. Ленивый импорт: MIDI-генерация помечается BLOCKED,
# если mido не установлен, но импорт модуля не ломается.
try:
    import mido  # type: ignore
    from mido import Message, MidiFile, MidiTrack  # type: ignore
    _HAS_MIDO = True
except Exception:  # pragma: no cover
    mido = None
    Message = MidiFile = MidiTrack = None  # type: ignore
    _HAS_MIDO = False


SLOT_NOTES = {"kick": 36, "snare": 38, "hat": 42, "bass": 36, "melody": 60}
LOGGER = logging.getLogger(__name__)


def slot_events_for_genre(genre: str, bars: int = 8) -> dict[str, list[int]]:
    """Expose complete 16-step events for kick/snare/hat/bass/melody."""
    from modules.beat_constructor import slot_preset_for_genre

    if bars < 1:
        raise ValueError("bars must be positive")
    return {slot: pattern * bars for slot, pattern in slot_preset_for_genre(genre).items()}


class MIDIGenerator:
    """Алгоритмический MIDI-генератор с honest BLOCKED-fallback."""

    def __init__(self, output_dir: str = "output/midi"):
        self.output_dir = output_dir
        # v22-style: lazy dir — не создаём при импорте, только когда пишем
        self._dir_ready = False

    def _ensure_dir(self) -> None:
        if not self._dir_ready:
            os.makedirs(self.output_dir, exist_ok=True)
            self._dir_ready = True

    @staticmethod
    def get_status() -> dict:
        """Возвращает честный статус движка."""
        return {
            "ok": _HAS_MIDO,
            "engine": "mido" if _HAS_MIDO else "BLOCKED",
            "reason": None if _HAS_MIDO else "mido not installed — MIDI export disabled, honest fallback",
        }

    def export_slot_pattern(
        self,
        genre: str,
        bpm: int,
        bars: int = 8,
        out_name: str | None = None,
    ) -> dict:
        """Export all five deterministic slots to one MIDI file when mido is available."""
        events = slot_events_for_genre(genre, bars=bars)
        if not _HAS_MIDO:
            return {
                "ok": False,
                "status": "BLOCKED",
                "reason": "mido not installed — five-slot MIDI export unavailable",
                "events": events,
            }
        try:
            self._ensure_dir()
            midi = MidiFile()
            ticks = max(1, midi.ticks_per_beat // 4)
            tempo = mido.bpm2tempo(max(40, min(int(bpm), 240)))
            for slot, pattern in events.items():
                track = MidiTrack()
                midi.tracks.append(track)
                track.append(mido.MetaMessage("track_name", name=slot, time=0))
                track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
                note = SLOT_NOTES[slot]
                for active in pattern:
                    if active:
                        track.append(Message("note_on", note=note, velocity=96, time=0, channel=9 if slot in {"kick", "snare", "hat"} else 0))
                        track.append(Message("note_off", note=note, velocity=0, time=ticks, channel=9 if slot in {"kick", "snare", "hat"} else 0))
                    else:
                        track.append(mido.MetaMessage("marker", text="rest", time=ticks))
            safe_genre = "".join(char for char in genre.lower() if char.isalnum() or char in ("_", "-")) or "genre"
            target = os.path.join(self.output_dir, out_name or f"{safe_genre}_{bars}bars_slots.mid")
            midi.save(target)
            return {"ok": True, "status": "REAL_PASS", "path": target, "events": events, "slots": list(events)}
        except Exception as exc:
            return {"ok": False, "status": "FAILED", "reason": str(exc), "events": events}

    # ------------------------------------------------------------------ #
    #  DRUM PATTERN
    # ------------------------------------------------------------------ #
    @staticmethod
    def _drum_events(genre: str) -> list[tuple[int, int]]:
        """Return the 16-step note/velocity pattern for a supported drum genre."""
        normalized = (genre or "").lower()
        if "techno" in normalized or "house" in normalized:
            return [(36, 110) if index % 4 == 0 else (42, 78) for index in range(16)]
        if "phonk" in normalized or "drift" in normalized:
            return [
                (36, 118) if index in (0, 6, 10) else (38, 100) if index in (4, 12)
                else (56, 90) if index == 8 else (42, 70)
                for index in range(16)
            ]
        if "trap" in normalized or "hiphop" in normalized or "hip-hop" in normalized:
            return [
                (36, 115) if index in (0, 10) else (38, 105) if index in (4, 12)
                else (42, random.randint(55, 95))
                for index in range(16)
            ]
        return [
            (36, 108) if index in (0, 8) else (38, 102) if index in (4, 12)
            else (42, random.randint(70, 90))
            for index in range(16)
        ]

    def generate_drum_pattern(self, genre: str, bpm: int) -> str:
        """Генерирует MIDI барабанный паттерн в зависимости от жанра.

        Возвращает путь к .mid или "" если mido недоступен (honest BLOCKED).
        Не бросает исключения при отсутствии mido — это критично для God Mode.
        """
        if not _HAS_MIDO:
            return ""  # BLOCKED: mido not installed (honest, non-fatal)

        try:
            self._ensure_dir()
            mid = MidiFile()
            track = MidiTrack()
            mid.tracks.append(track)

            tempo = mido.bpm2tempo(max(40, min(int(bpm), 240)))
            track.append(mido.MetaMessage('set_tempo', tempo=tempo))

            ticks_per_16th = max(1, mid.ticks_per_beat // 4)
            for note, velocity in self._drum_events(genre):
                track.append(Message('note_on', note=note, velocity=velocity, time=0))
                track.append(
                    Message('note_off', note=note, velocity=velocity, time=ticks_per_16th)
                )

            normalized = (genre or "").lower()
            safe_genre = "".join(c for c in normalized if c.isalnum() or c in ("_", "-")) or "gen"
            out_path = os.path.join(self.output_dir, f"{safe_genre}_drums.mid")
            mid.save(out_path)
            return out_path
        except Exception as error:
            LOGGER.warning("MIDI drum export failed: %s", error)
            return ""

    # ------------------------------------------------------------------ #
    #  MELODY PATTERN  (v29 P0 fix — добавлен guard)
    # ------------------------------------------------------------------ #
    def generate_melody_pattern(
        self,
        genre: str,
        key_root: str = "A",
        mode: str = "minor",
        bpm: int = 120,
    ) -> str:
        """Генерирует MIDI мелодию на основе музыкальной теории.

        v29 P0: раньше падал TypeError при отсутствии mido — валил God Mode.
        Теперь: honest BLOCKED-return "" вместо исключения.
        """
        if not _HAS_MIDO:
            return ""  # BLOCKED: mido not installed

        try:
            self._ensure_dir()

            # Гаммы: MIDI-ноты для root + intervals
            root_map = {"C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65,
                        "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71}
            root = root_map.get((key_root or "A").upper(), 69)
            if (mode or "minor").lower().startswith("min"):
                intervals = [0, 2, 3, 5, 7, 8, 10, 12]  # natural minor
            else:
                intervals = [0, 2, 4, 5, 7, 9, 11, 12]  # major
            scale = [root + iv for iv in intervals]

            mid = MidiFile()
            track = MidiTrack()
            mid.tracks.append(track)

            tempo = mido.bpm2tempo(max(40, min(int(bpm), 240)))
            track.append(mido.MetaMessage('set_tempo', tempo=tempo))

            ticks_per_8th = max(1, mid.ticks_per_beat // 2)

            # 16 нот с музыкальной логикой (весовое приближение к тонике)
            weights = [3, 1, 2, 1, 2, 1, 1, 3]
            for step in range(16):
                # Разная длительность (варьируем 8th и 16th)
                dur = ticks_per_8th if step % 2 == 0 else ticks_per_8th // 2
                note = random.choices(scale, weights=weights, k=1)[0]
                vel = random.randint(64, 96)
                track.append(Message('note_on', note=note, velocity=vel, time=0))
                track.append(Message('note_off', note=note, velocity=vel, time=dur))

            safe_genre = "".join(c for c in (genre or "gen").lower() if c.isalnum() or c in ("_", "-")) or "gen"
            out_path = os.path.join(self.output_dir, f"{safe_genre}_melody.mid")
            mid.save(out_path)
            return out_path
        except Exception as e:
            print(f"[midi_generator] melody error: {e}")
            return ""


if __name__ == "__main__":
    gen = MIDIGenerator()
    print("Status:", gen.get_status())
    print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)!r}")
    print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)!r}")

# -*- coding: utf-8 -*-
"""
ZS Music Maker — midi_generator.py (GOD MODE)
========================================================================
Алгоритмическая генерация MIDI паттернов.
Использует mido для создания MIDI файлов и паттернов для разных жанров.
"""

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

class MIDIGenerator:
    def __init__(self):
        self.output_dir = "output/midi"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_drum_pattern(self, genre: str, bpm: int) -> str:
        """Генерирует MIDI барабанный паттерн в зависимости от жанра."""
        if not _HAS_MIDO:
            return ""  # BLOCKED: mido not installed
        if not _HAS_MIDO:
            return ""
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        
        # 1. Настройка темпа (mido использует микросекунды на четверть)
        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo))
        
        # 2. Базовый паттерн (Kick: 36, Snare: 38, Hi-Hat: 42)
        ticks_per_16th = mid.ticks_per_beat // 4
        
        if "techno" in genre.lower():
            # 4/4 Kick
            for i in range(16):
                if i % 4 == 0:
                    track.append(Message('note_on', note=36, velocity=100, time=0))
                    track.append(Message('note_off', note=36, velocity=100, time=ticks_per_16th))
                else:
                    track.append(Message('note_on', note=42, velocity=80, time=0))
                    track.append(Message('note_off', note=42, velocity=80, time=ticks_per_16th))
        else:
            # Trap/Hip-Hop style
            for i in range(16):
                note = 36 if i % 8 == 0 else (38 if i % 8 == 4 else 42)
                track.append(Message('note_on', note=note, velocity=random.randint(80, 110), time=0))
                track.append(Message('note_off', note=note, velocity=80, time=ticks_per_16th))

        out_path = os.path.join(self.output_dir, f"{genre}_drums.mid")
        mid.save(out_path)
        return out_path

    def generate_melody_pattern(self, genre: str, key_root: str, mode: str, bpm: int) -> str:
        """Генерирует MIDI мелодию на основе музыкальной теории."""
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        
        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo))
        
        # Упрощенная гамма (A minor: 69, 71, 72, 74, 76, 77, 79)
        scale = [69, 71, 72, 74, 76, 77, 79] 
        
        ticks_per_8th = mid.ticks_per_beat // 2
        
        for _ in range(8):
            note = random.choice(scale)
            track.append(Message('note_on', note=note, velocity=random.randint(60, 90), time=0))
            track.append(Message('note_off', note=note, velocity=60, time=ticks_per_8th))
            
        out_path = os.path.join(self.output_dir, f"{genre}_melody.mid")
        mid.save(out_path)
        return out_path

if __name__ == "__main__":
    gen = MIDIGenerator()
    print(f"Drum MIDI: {gen.generate_drum_pattern('techno', 128)}")
    print(f"Melody MIDI: {gen.generate_melody_pattern('techno', 'A', 'minor', 128)}")

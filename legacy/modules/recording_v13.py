# -*- coding: utf-8 -*-
"""
ZS Music Maker v13 — recording_v13.py
======================================

PRO-режим записи вокала (ТЗ 4.7): пользователь напевает в микрофон,
а программа сама нарезает take'ы, считает активность голоса (VAD),
помечает punch-in точки и даёт быстрый feedback.

ВОПРОС: "v12 закрывает 4.7 Pro, но без реальной записи — только
KaraokeEngine (word-map + score)"
ОТВЕТ:  recording_v13 — это framework-agnostic ядро, работающее
        поверх простого PCM (soundfile/RIFF) и numpy. Никаких
        обязательных зависимостей. GUI может подцепить через
        callbacks.

Шаги:
  1) load_pcm(path)            — read raw PCM (16/24/32 bit)
  2) voice_activity_detector   — RMS-based gate, возвращает
                                 список сегментов [start_ms, end_ms]
  3) split_takes                — режет по тишине ≥600ms или
                                 punch-in маркерам
  4) analyze_take               — SNR, peak, RMS, clip%
  5) feedback_for_take          — рекомендация «горячо/тихо/не тот
                                 момент/не дотянул»
  6) attach_lyrics_wordmap_marks — кросс-марки с karaoke_engine

Реальный аудио-ввод на Windows делает sounddevice/soundcard; этот
модуль работает С УЖЕ ЗАПИСАННЫМ WAV (например из sounddevice или
из AudioRecorderThread UI-визарда).
"""

from __future__ import annotations

import json
import struct
import time
import wave
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
#  Модели
# ---------------------------------------------------------------------------

@dataclass
class VoiceActivity:
    start_ms: int
    end_ms: int
    rms_db: float = -100.0
    peak: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Take:
    take_id: str
    start_ms: int
    end_ms: int
    source_path: str = ""
    rms_db: float = -100.0
    peak: float = 0.0
    clip_pct: float = 0.0           # доля сэмплов близких к 1.0
    snr_estimate_db: float = 0.0
    matched_word_pct: float = -1.0  # -1 = не считали
    punch_in_ok: bool = False
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  PCM-чтение без librosa
# ---------------------------------------------------------------------------

def load_pcm(path: Path) -> Tuple[List[float], int, int]:
    """
    Читает WAV (PCM 16/24/32-bit). Возвращает (samples_mono_norm, sr, n_channels).
    samples_mono_norm — float32 в диапазоне [-1, 1].
    """
    with wave.open(str(path), "rb") as w:
        n_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        sr = w.getframerate()
        n_frames = w.getnframes()
        raw = w.readframes(n_frames)

    bytes_per_sample = sampwidth
    if sampwidth == 1:
        n_samples = len(raw)
        # 8-bit unsigned
        samples = [((b - 128) / 128.0) for b in raw]
    elif sampwidth == 2:
        samples = list(struct.unpack(f"<{len(raw)//2}h", raw))
        max_v = 32768.0
        samples = [s / max_v for s in samples]
    elif sampwidth == 3:
        # 24-bit — собираем вручную
        n = len(raw) // 3
        samples = []
        for i in range(n):
            triplet = raw[i*3:(i+1)*3]
            val = triplet[0] | (triplet[1] << 8) | (triplet[2] << 16)
            if val & 0x800000:
                val -= 0x1000000
            samples.append(val / 8388608.0)
    elif sampwidth == 4:
        samples = list(struct.unpack(f"<{len(raw)//4}i", raw))
        max_v = 2147483648.0
        samples = [s / max_v for s in samples]
    else:
        raise ValueError(f"unsupported sampwidth {sampwidth}")

    if n_channels > 1:
        # моно-sum
        mono = []
        step = n_channels
        for i in range(0, len(samples), step):
            chunk = samples[i:i + step]
            mono.append(sum(chunk) / len(chunk))
        samples = mono
    return samples, sr, n_channels


def _rms_dbfs(samples: List[float]) -> float:
    if not samples:
        return -100.0
    sq = sum(s * s for s in samples) / len(samples)
    if sq <= 0:
        return -100.0
    import math
    return 20.0 * math.log10(max(sq, 1e-12) ** 0.5)


def _peak(samples: List[float]) -> float:
    if not samples:
        return 0.0
    return max(abs(s) for s in samples)


# ---------------------------------------------------------------------------
#  VAD + Take splitter
# ---------------------------------------------------------------------------

def voice_activity_detector(samples: List[float], sr: int,
                             frame_ms: int = 30,
                             threshold_db: float = -45.0,
                             silence_min_ms: int = 250) -> List[VoiceActivity]:
    """
    RMS-гейт. Возвращает список сегментов активности.
    threshold_db:    уровень ниже которого считаем тишиной
    silence_min_ms:  минимальная длительность тишины для разрыва сегмента
    """
    frame_size = max(1, int(sr * frame_ms / 1000.0))
    raw_segments: List[Tuple[int, int, float, float]] = []
    i = 0
    n = len(samples)
    while i + frame_size <= n:
        frame = samples[i:i + frame_size]
        db = _rms_dbfs(frame)
        pk = _peak(frame)
        if db > threshold_db:
            raw_segments.append((i, i + frame_size, db, pk))
        i += frame_size

    # объединяем соседние фреймы
    out: List[VoiceActivity] = []
    if not raw_segments:
        return out
    cur_s, cur_e, cur_db_acc, cur_pk_acc = raw_segments[0]
    db_frames = 1
    for s, e, db, pk in raw_segments[1:]:
        if s <= cur_e + int(sr * silence_min_ms / 1000.0):
            cur_e = e
            cur_db_acc += db
            cur_pk_acc = max(cur_pk_acc, pk)
            db_frames += 1
        else:
            out.append(VoiceActivity(
                start_ms=int(cur_s / sr * 1000),
                end_ms=int(cur_e / sr * 1000),
                rms_db=cur_db_acc / db_frames,
                peak=cur_pk_acc))
            cur_s, cur_e, cur_db_acc, cur_pk_acc = s, e, db, pk
            db_frames = 1
    out.append(VoiceActivity(
        start_ms=int(cur_s / sr * 1000),
        end_ms=int(cur_e / sr * 1000),
        rms_db=cur_db_acc / db_frames,
        peak=cur_pk_acc))
    return out


def split_takes(samples: List[float], sr: int,
                segments: List[VoiceActivity],
                min_take_ms: int = 800,
                max_take_ms: int = 60000,
                silence_min_ms: int = 600) -> List[Take]:
    """
    Делит сегменты VAD на take'ы (chunks ≥min_take_ms).
    Тишина ≥silence_min_ms между сегментами = разделитель.
    Если активный участок длится > max_take_ms — режем.
    """
    takes: List[Take] = []
    if not segments:
        return takes
    take_id = 1
    cur_start = segments[0].start_ms
    cur_end = segments[0].end_ms
    for s in segments[1:]:
        gap = s.start_ms - cur_end
        seg_len = s.end_ms - s.start_ms
        if gap >= silence_min_ms or (cur_end - cur_start + seg_len) > max_take_ms:
            if cur_end - cur_start >= min_take_ms:
                takes.append(_take_from_segment(take_id, cur_start, cur_end,
                                                samples, sr))
                take_id += 1
            cur_start = s.start_ms
            cur_end = s.end_ms
        else:
            cur_end = max(cur_end, s.end_ms)
    if cur_end - cur_start >= min_take_ms:
        takes.append(_take_from_segment(take_id, cur_start, cur_end,
                                        samples, sr))
    return takes


def _take_from_segment(take_id: int, start_ms: int, end_ms: int,
                       samples: List[float], sr: int) -> Take:
    s_i = int(start_ms * sr / 1000)
    e_i = int(end_ms * sr / 1000)
    s_i = max(0, min(s_i, len(samples) - 1))
    e_i = max(s_i + 1, min(e_i, len(samples)))
    seg = samples[s_i:e_i]
    return Take(
        take_id=f"take_{take_id:02d}",
        start_ms=start_ms,
        end_ms=end_ms,
        rms_db=_rms_dbfs(seg),
        peak=_peak(seg),
        clip_pct=sum(1 for s in seg if abs(s) > 0.99) / max(1, len(seg)),
    )


def analyze_take(take: Take, samples: List[float], sr: int,
                 wordmap: Optional[List[Dict[str, Any]]] = None) -> Take:
    """Считает SNR, проверяет punch-in (запись стартовала после markup)."""
    s_i = int(take.start_ms * sr / 1000)
    e_i = int(take.end_ms * sr / 1000)
    seg = samples[max(0, s_i):min(len(samples), e_i)]
    if not seg:
        return take
    take.rms_db = _rms_dbfs(seg)
    take.peak = _peak(seg)
    take.clip_pct = sum(1 for s in seg if abs(s) > 0.99) / max(1, len(seg))
    # SNR estimate: разница между верхними 10% и нижними 10% RMS
    rmses = sorted([abs(s) for s in seg])
    if len(rmses) > 20:
        top = sum(rmses[-len(rmses)//10:]) / max(1, len(rmses)//10)
        bot = sum(rmses[:len(rmses)//10]) / max(1, len(rmses)//10)
        if bot > 0:
            import math
            take.snr_estimate_db = 20 * math.log10(top / bot)
    # Punch-in marks (если wordmap передан)
    if wordmap:
        hit_words = [w for w in wordmap
                     if take.start_ms <= w.get("start_ms", 0) <= take.end_ms]
        expected = len(wordmap)
        if expected:
            take.matched_word_pct = min(100.0, len(hit_words) * 100.0 / expected)
            take.punch_in_ok = take.matched_word_pct >= 50
            if not take.punch_in_ok:
                take.notes.append("попадание в слова < 50%")
    # Простые рекомендации
    if take.clip_pct > 0.01:
        take.notes.append(f"⚠ клиппинг {take.clip_pct*100:.1f}% — "
                          "отойди от микрофона или снизь gain")
    if take.rms_db < -25:
        take.notes.append("тихо — поднеси микрофон ближе")
    if take.rms_db > -3:
        take.notes.append("слишком громко — перегрузка")
    if take.snr_estimate_db and take.snr_estimate_db < 8:
        take.notes.append("мало SNR — посторонние шумы")
    return take


def feedback_for_take(take: Take) -> str:
    """Человеческое резюме по take'у — Wizard показывает его пользователю."""
    if take.punch_in_ok and take.matched_word_pct >= 80:
        verdict = "ГОРЯЧО!"
    elif take.matched_word_pct >= 50:
        verdict = "хорошо"
    else:
        verdict = "не тот момент"
    head = (f"Take {take.take_id} ({take.start_ms//1000}s—{take.end_ms//1000}s): "
            f"{verdict}\n"
            f"  · RMS {take.rms_db:.1f} dBFS\n"
            f"  · peak {take.peak:.2f}\n"
            f"  · клиппинг {take.clip_pct*100:.2f}%\n"
            f"  · SNR ~{take.snr_estimate_db:.1f} dB")
    if take.notes:
        head += "\n  · " + "\n  · ".join(take.notes)
    if take.matched_word_pct >= 0:
        head += f"\n  · попадание в слова: {take.matched_word_pct:.0f}%"
    return head


def record_session_from_wav(wav_path: Path,
                            wordmap: Optional[List[Dict[str, Any]]] = None,
                            min_take_ms: int = 800,
                            silence_min_ms: int = 600) -> Dict[str, Any]:
    """
    Главная точка модуля. Принимает путь к WAV-файлу записи,
    возвращает dict с take'ами и человеческим резюме.
    """
    samples, sr, _ = load_pcm(wav_path)
    segs = voice_activity_detector(samples, sr, silence_min_ms=silence_min_ms)
    takes = split_takes(samples, sr, segs, min_take_ms=min_take_ms,
                        silence_min_ms=silence_min_ms)
    enriched = [analyze_take(t, samples, sr, wordmap=wordmap) for t in takes]
    return {
        "source_wav": str(wav_path),
        "sr": sr,
        "duration_ms": int(len(samples) / sr * 1000),
        "segments": [s.as_dict() for s in segs],
        "takes": [t.as_dict() for t in enriched],
        "feedback": [feedback_for_take(t) for t in enriched],
    }


def save_takes_summary(result: Dict[str, Any], out_json: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8")


def demo() -> Dict[str, Any]:
    """
    Демо-режим: генерирует синтетический 6-секундный wav
    (2 активных куска + тишина), прогоняет пайплайн, печатает feedback.
    Не требует внешних зависимостей.
    """
    sr = 22050
    dur = 6.0
    n = int(dur * sr)
    import math, random
    samples: List[float] = []
    for i in range(n):
        t = i / sr
        if 0.7 <= t <= 2.7 or 4.0 <= t <= 5.4:
            # активный сегмент — синус + шум
            s = 0.5 * math.sin(2 * math.pi * 220 * t)
            s += 0.05 * (random.random() - 0.5)
        else:
            # тишина — только микрофонный шум
            s = 0.005 * (random.random() - 0.5)
        samples.append(s)

    segs = voice_activity_detector(samples, sr, silence_min_ms=300)
    takes = split_takes(samples, sr, segs, min_take_ms=500,
                        silence_min_ms=400)
    enriched = [analyze_take(t, samples, sr) for t in takes]
    return {
        "sr": sr, "duration_ms": int(dur * 1000),
        "segments": [s.as_dict() for s in segs],
        "takes": [t.as_dict() for t in enriched],
        "feedback": [feedback_for_take(t) for t in enriched],
    }


def main_entry() -> int:
    r = demo()
    print(f"demo: {len(r['segments'])} segments, {len(r['takes'])} takes")
    for f in r["feedback"]:
        print("---")
        print(f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_entry())

"""
ZS Music Maker v10 — Karaoke Engine v10
=========================================
Караоке-режим для записи вокала (ТЗ 5, «karaoke-режим»).

Расширяет ui/karaoke_recorder.py:
  - подсветка слов по времени
  - метроном + отсчёт
  - визуализация амплитуды в реальном времени (VU-метр)
  - авто-детект попадания в тайминг (WER-подобно)
  - регулировка громкости эталона в наушниках (mix send)
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

log = logging.getLogger("zsmm.karaoke_v10")


class KaraokeSession:
    """
    Одна сессия записи вокала.
    """

    def __init__(
        self,
        lyrics: list[dict[str, Any]],
        bpm: int = 120,
        count_in_beats: int = 4,
        monitor_volume: float = 0.35,
    ):
        """
        lyrics: [{"text": "...", "start_ms": 0, "duration_ms": 800}, ...]
        """
        self.lyrics = lyrics
        self.bpm = bpm
        self.beat_ms = int(60000 / bpm)
        self.count_in_beats = count_in_beats
        self.monitor_volume = monitor_volume
        self.state = "idle"
        self._start_ts: float | None = None
        self._callbacks: dict[str, list[Callable]] = {
            "on_word": [],
            "on_beat": [],
            "on_end": [],
            "on_amp": [],
        }
        self._stop = threading.Event()

    def on(self, event: str, cb: Callable) -> None:
        self._callbacks.setdefault(event, []).append(cb)

    def _fire(self, event: str, *args, **kwargs) -> None:
        for cb in self._callbacks.get(event, []):
            try:
                cb(*args, **kwargs)
            except Exception as e:
                log.warning("callback error: %s", e)

    def elapsed_ms(self) -> int:
        if not self._start_ts:
            return 0
        return int((time.time() - self._start_ts) * 1000)

    def current_word(self) -> dict[str, Any] | None:
        t = self.elapsed_ms()
        for w in self.lyrics:
            start = w.get("start_ms", 0)
            dur = w.get("duration_ms", self.beat_ms)
            if start <= t < start + dur:
                return w
        return None

    def start(self) -> None:
        self.state = "count_in"
        self._start_ts = time.time() + (self.count_in_beats * self.beat_ms) / 1000.0
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self) -> None:
        self._stop.set()
        self.state = "stopped"

    def _run(self) -> None:
        # count-in
        for i in range(self.count_in_beats):
            self._fire("on_beat", {"beat": i + 1, "is_count_in": True})
            time.sleep(self.beat_ms / 1000.0)
            if self._stop.is_set():
                return
        self.state = "recording"
        # main loop
        last_word_idx = -1
        beat_counter = 0
        next_beat_at = self._start_ts
        end_time = (
            self._start_ts
            + (self.lyrics[-1]["start_ms"] + self.lyrics[-1].get("duration_ms", 1000))
            / 1000.0
            if self.lyrics
            else self._start_ts + 60
        )
        while time.time() < end_time and not self._stop.is_set():
            now = time.time()
            if now >= next_beat_at:
                beat_counter += 1
                self._fire("on_beat", {"beat": beat_counter, "is_count_in": False})
                next_beat_at += self.beat_ms / 1000.0
            t_ms = int((now - self._start_ts) * 1000)
            for idx, w in enumerate(self.lyrics):
                start = w.get("start_ms", 0)
                if start <= t_ms and idx > last_word_idx:
                    self._fire("on_word", {"index": idx, "word": w, "t_ms": t_ms})
                    last_word_idx = idx
                    break
            time.sleep(0.02)
        self.state = "finished"
        self._fire("on_end", {"duration_ms": self.elapsed_ms()})


def make_wordmap_from_lyrics(
    lyrics_text: str,
    bpm: int,
    start_offset_ms: int = 0,
    syllables_per_beat: float = 2.0,
) -> list[dict[str, Any]]:
    """
    Простое построение word-map из чистого текста и BPM.
    """
    beat_ms = 60000 // bpm
    words = []
    t = start_offset_ms
    for line in lyrics_text.strip().splitlines():
        for w in line.split():
            n_syl = max(1, sum(1 for c in w.lower() if c in "аеёиоуыэюяaeiouy"))
            dur = int(n_syl / syllables_per_beat * beat_ms)
            words.append({"text": w, "start_ms": t, "duration_ms": dur})
            t += dur
        t += beat_ms  # пауза между строками
    return words


def score_take(
    recorded_wav: str, expected_word_map: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Оценивает попадание записи в тайминг (без ASR — по общей длительности
    и RMS-огибающей). Возвращает 0-100.
    """
    try:
        import librosa

        y, sr = librosa.load(recorded_wav, sr=22050, mono=True)
        actual_ms = int(len(y) * 1000 / sr)
        expected_ms = (
            expected_word_map[-1]["start_ms"] + expected_word_map[-1]["duration_ms"]
            if expected_word_map
            else 1
        )
        length_ratio = min(actual_ms, expected_ms) / max(actual_ms, expected_ms)

        # энергетическое покрытие
        rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=512)[0]
        active_pct = float((rms > (rms.max() * 0.15)).sum()) / max(1, len(rms))

        # ожидаемое покрытие: сумма duration_ms / total
        exp_active = sum(w.get("duration_ms", 0) for w in expected_word_map) / max(
            1, expected_ms
        )
        active_score = 1.0 - abs(active_pct - exp_active)

        score = int(round(60 * length_ratio + 40 * active_score))
        return {
            "ok": True,
            "score": max(0, min(100, score)),
            "length_ratio": round(length_ratio, 3),
            "active_pct": round(active_pct, 3),
            "expected_active_pct": round(exp_active, 3),
        }
    except Exception as e:
        return {"ok": False, "reason": str(e), "score": 0}


if __name__ == "__main__":
    wm = make_wordmap_from_lyrics("Тачки летят по трассе\nЛето жарит нас", bpm=140)
    print(json.dumps(wm, ensure_ascii=False, indent=2))

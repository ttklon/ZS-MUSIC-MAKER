# -*- coding: utf-8 -*-
"""
[v9] hit_scorer.py — HIT POTENTIAL SCORER.

Оценивает «хитовость» финального master.wav по 12 метрикам, скоррелированным
с реальными чартовыми характеристиками (Spotify Viral 50 / TikTok Sounds /
Apple Music Top 100). Идеологически — расширение auto_qa, но фокус смещён с
«живости звука» на «шансы попасть в чарт / зайти на TikTok».

Метрики (0..100 каждая, weighted sum → HitScore 0..100):
  1. hook_energy          — пик громкости в припеве vs куплете
  2. hook_repeatability   — сколько раз повторяется главный мотив
  3. chorus_catchiness    — гармоническая яркость + ритмическая простота припева
  4. drop_impact          — контраст drop/build (bass energy delta)
  5. tiktok_hookability   — есть ли 15-30 сек «вирусный кусок» с моментальным входом
  6. bpm_dance_fitness    — BPM в диапазоне 120-140 (dance) или 70-95 (trap)
  7. loudness_lufs        — интегральный LUFS близко к -8..-10 (стриминг-мастер)
  8. stereo_width         — стерео-разъезд (correlation < 0.85)
  9. low_end_power        — sub-bass (20-80 Hz) не рыхлый
 10. vocal_presence       — вокал в диапазоне 2-5 kHz читается
 11. structure_clarity    — узнаваемые границы intro/verse/chorus/outro
 12. novelty              — не «формульный» — уникальные звуковые события

Возвращает:
  {
    "hit_score": float 0..100,
    "verdict":   "chart_ready" | "solid" | "needs_work" | "flop_risk",
    "metrics":   {name: {"score": float, "raw": Any, "hint": str}},
    "tiktok_slice": {"start_sec": float, "end_sec": float, "reason": str},
    "actions":     [str, ...]  # что доработать
  }

Без внешних сервисов. librosa/numpy — единственные зависимости.
Graceful fallback при отсутствии librosa: только LUFS-подобная оценка через soundfile.
"""
from __future__ import annotations
import json, math, time
from pathlib import Path
from typing import Optional

# ---------- граcеful imports ----------
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    import librosa
    HAS_LIBROSA = True
except Exception:
    HAS_LIBROSA = False

try:
    import soundfile as sf
    HAS_SF = True
except Exception:
    HAS_SF = False


# ============================================================ utils
def _load_audio(path: str, sr: int = 22050):
    """Возвращает (y, sr). Использует librosa если есть, иначе soundfile+resample naive."""
    if HAS_LIBROSA:
        y, s = librosa.load(path, sr=sr, mono=True)
        return y, s
    if HAS_SF:
        y, s = sf.read(path, always_2d=False)
        if hasattr(y, "ndim") and y.ndim > 1:
            y = y.mean(axis=1)
        return y, s
    raise RuntimeError("Neither librosa nor soundfile available")


def _rms(y) -> float:
    if np is None or y is None or len(y) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(y)) + 1e-12))


def _db(x: float) -> float:
    return float(20.0 * math.log10(max(x, 1e-9)))


# ============================================================ metrics
def _hook_energy(y, sr) -> tuple[float, float]:
    """Ищем сегмент с максимальной локальной громкостью — это предполагаемый припев."""
    if np is None or len(y) < sr * 8:
        return 50.0, _rms(y)
    win = int(sr * 4)
    hop = int(sr * 1)
    rms_curve = []
    for i in range(0, len(y) - win, hop):
        rms_curve.append(_rms(y[i:i+win]))
    if not rms_curve:
        return 50.0, 0.0
    peak = max(rms_curve)
    median = sorted(rms_curve)[len(rms_curve)//2]
    ratio = peak / max(median, 1e-6)
    # Хит-припев обычно на +30-60% громче медианы
    score = min(100.0, max(0.0, (ratio - 1.0) * 200.0))
    return score, ratio


def _hook_repeatability(y, sr) -> tuple[float, int]:
    """Повторяемость главного мотива.

    v26 FIX (P1): короткие треки (<20 с) раньше всегда получали 55.0/0
    (ложный нейтрал) и не теряли баллы, но не давали сигнала к улучшению.
    Теперь считаем AC RMS-огибающей даже без librosa — честный signal.
    """
    if not HAS_LIBROSA or len(y) < sr * 20:
        if np is None or len(y) < sr * 2:
            return 55.0, 0
        try:
            win = int(sr * 0.5); hop = int(sr * 0.25)
            rms_curve = np.array([_rms(y[i:i+win])
                                  for i in range(0, len(y) - win, hop)],
                                 dtype="float32")
            if len(rms_curve) < 8:
                return 55.0, 0
            rms_curve = rms_curve - rms_curve.mean()
            _norm = float(np.sum(rms_curve * rms_curve)) + 1e-9
            _peaks = 0
            for lag in range(4, min(len(rms_curve) - 1, 32)):
                ac = float(np.sum(rms_curve[:-lag] * rms_curve[lag:])) / _norm
                if ac > 0.5: _peaks += 1
            score = min(100.0, 40.0 + _peaks * 6.0)
            return score, _peaks
        except Exception:
            return 55.0, 0
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=1024)
        ssm = np.dot(chroma.T, chroma)
        ssm /= (np.linalg.norm(chroma, axis=0)[:, None] *
                np.linalg.norm(chroma, axis=0)[None, :] + 1e-9)
        off = int(20 * sr / 1024)
        if off >= ssm.shape[0]:
            off = int(4 * sr / 1024)
            if off >= ssm.shape[0] - 1 or off < 1:
                return 50.0, 0
        diag = np.diagonal(ssm, offset=off)
        repeats = int((diag > 0.85).sum())
        score = min(100.0, repeats * 8.0 + 30.0)
        return score, repeats
    except Exception:
        return 50.0, 0


def _chorus_catchiness(y, sr) -> tuple[float, dict]:
    """Комбинация: гармоническая простота (мажор/минор readable) + ритмическая регулярность."""
    if not HAS_LIBROSA:
        return 55.0, {}
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        # Регулярность: sharpness пиков огибающей
        peaks = librosa.util.peak_pick(onset_env,
                                       pre_max=3, post_max=3,
                                       pre_avg=5, post_avg=5,
                                       delta=0.5, wait=10)
        regularity = min(100.0, len(peaks) * 0.6 + 40.0)
        # Гармоническая простота — chroma variance (низкая = простая гармония)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_var = float(np.mean(np.var(chroma, axis=1)))
        harmonic_simplicity = max(0.0, min(100.0, 100.0 - chroma_var * 400.0))
        score = 0.6 * regularity + 0.4 * harmonic_simplicity
        return score, {"tempo": float(tempo), "peaks": len(peaks),
                       "chroma_var": chroma_var}
    except Exception:
        return 55.0, {}


def _drop_impact(y, sr) -> tuple[float, float]:
    """Ищем самый резкий скачок RMS — drop. Хит-drop даёт +6..+9 dB."""
    if np is None or len(y) < sr * 8:
        return 50.0, 0.0
    win = int(sr * 2)
    hop = int(sr * 0.5)
    rms_curve = np.array([_rms(y[i:i+win])
                          for i in range(0, len(y) - win, hop)])
    if len(rms_curve) < 4:
        return 50.0, 0.0
    diff = np.diff(rms_curve)
    max_jump = float(diff.max())
    baseline = float(np.median(np.abs(diff)))
    ratio = max_jump / max(baseline, 1e-6)
    score = min(100.0, ratio * 12.0)
    return score, ratio


def _tiktok_hookability(y, sr) -> tuple[float, dict]:
    """Находит 15-30 сек кусок с моментальным входом (energy>median в первые 2 сек)."""
    if np is None or len(y) < sr * 15:
        return 40.0, {"start_sec": 0.0, "end_sec": 15.0,
                      "reason": "трек короткий"}
    win_len = int(sr * 25)  # 25 sec — sweet spot TikTok
    hop = int(sr * 2)
    best = {"score": 0.0, "start": 0}
    global_med = _rms(y)
    for i in range(0, len(y) - win_len, hop):
        seg = y[i:i+win_len]
        head_rms = _rms(seg[:int(sr * 2)])
        overall = _rms(seg)
        # Хороший TikTok-slice: сразу громко + держит уровень
        if head_rms > global_med * 0.9 and overall > global_med:
            score = (head_rms / max(global_med, 1e-6)) * 30.0 + \
                    (overall / max(global_med, 1e-6)) * 20.0
            if score > best["score"]:
                best["score"] = score
                best["start"] = i
    if best["score"] == 0.0:
        # fallback: самый громкий 25-сек кусок
        rms_c = [_rms(y[i:i+win_len])
                 for i in range(0, len(y) - win_len, hop)]
        idx = int(np.argmax(rms_c)) if rms_c else 0
        best["start"] = idx * hop
        best["score"] = 45.0
    start_sec = best["start"] / sr
    return min(100.0, best["score"] + 20.0), {
        "start_sec": round(start_sec, 2),
        "end_sec":   round(start_sec + 25.0, 2),
        "reason":    "immediate hook + sustained energy"
    }


def _bpm_dance_fitness(y, sr) -> tuple[float, float]:
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        t = float(tempo)
        # Sweet spots
        best_ranges = [(120, 140, 100), (70, 95, 90),
                       (95, 120, 75), (140, 160, 80)]
        score = 40.0
        for lo, hi, s in best_ranges:
            if lo <= t <= hi:
                score = float(s)
                break
        return score, t
    except Exception:
        return 60.0, 0.0


def _loudness_lufs(y, sr) -> tuple[float, float]:
    """Псевдо-LUFS через простую A-weighting-approx RMS в dBFS.

    v26 FIX (P1): librosa грузит mono-downmix (L+R)/2 — теряет ~3 dB RMS
    относительно стерео dBFS. Sweet-spot сдвинут на -3 dB:
    - стерео dBFS -11..-7 → mono-RMS -14..-10 = score 95.
    """
    if np is None:
        return 60.0, -14.0
    rms = _rms(y)
    dbfs = _db(rms)
    if -14.0 <= dbfs <= -10.0:
        score = 95.0
    elif -17.0 <= dbfs < -14.0:
        score = 75.0
    elif -10.0 < dbfs <= -7.0:
        score = 80.0
    elif -7.0 < dbfs <= -4.0:
        score = 60.0
    else:
        score = 40.0
    return score, dbfs


def _stereo_width(path: str) -> tuple[float, float]:
    """Требуется стерео-файл. Считает корреляцию каналов."""
    if not HAS_SF or np is None:
        return 60.0, 1.0
    try:
        y, _ = sf.read(path, always_2d=True)
        if y.shape[1] < 2:
            return 30.0, 1.0
        l, r = y[:, 0], y[:, 1]
        corr = float(np.corrcoef(l, r)[0, 1])
        # width = 1 - corr; хиты обычно 0.15..0.4 → corr 0.6..0.85
        if 0.55 <= corr <= 0.85:
            score = 90.0
        elif corr < 0.55:
            score = 70.0  # слишком широко
        elif corr < 0.95:
            score = 65.0
        else:
            score = 40.0  # почти моно
        return score, corr
    except Exception:
        return 60.0, 1.0


def _low_end_power(y, sr) -> tuple[float, float]:
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        low_mask = (freqs >= 20) & (freqs <= 80)
        mid_mask = (freqs >= 200) & (freqs <= 2000)
        low_energy = float(S[low_mask, :].mean())
        mid_energy = float(S[mid_mask, :].mean())
        ratio = low_energy / max(mid_energy, 1e-9)
        # Хиты dance/trap: low/mid ≈ 0.6..1.2
        if 0.55 <= ratio <= 1.3:
            score = 92.0
        elif 0.3 <= ratio < 0.55:
            score = 68.0
        elif ratio > 1.3:
            score = 70.0
        else:
            score = 45.0
        return score, ratio
    except Exception:
        return 60.0, 0.0


def _vocal_presence(y, sr) -> tuple[float, float]:
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        voc_mask = (freqs >= 2000) & (freqs <= 5000)
        all_energy = float(S.mean())
        voc_energy = float(S[voc_mask, :].mean())
        ratio = voc_energy / max(all_energy, 1e-9)
        score = min(100.0, ratio * 90.0 + 25.0)
        return score, ratio
    except Exception:
        return 60.0, 0.0


def _structure_clarity(y, sr) -> tuple[float, int]:
    if not HAS_LIBROSA or len(y) < sr * 30:
        return 55.0, 0
    try:
        # segmentation по chroma+mfcc через spectral clustering — простая версия
        rms = librosa.feature.rms(y=y, hop_length=1024)[0]
        # normalize
        rms = (rms - rms.mean()) / (rms.std() + 1e-9)
        # найдём точки сильного изменения
        changes = np.where(np.abs(np.diff(rms)) > 1.2)[0]
        # ожидаем 3-6 крупных секций
        n = len(changes)
        if 3 <= n <= 8:
            score = 90.0
        elif n < 3:
            score = 50.0
        else:
            score = 70.0
        return score, n
    except Exception:
        return 55.0, 0


def _novelty(y, sr) -> tuple[float, float]:
    """Насколько трек «неформульный» — вариативность спектра во времени."""
    if not HAS_LIBROSA:
        return 60.0, 0.0
    try:
        S = np.abs(librosa.stft(y, n_fft=2048))
        col_var = float(np.mean(np.var(S, axis=1)))
        row_var = float(np.mean(np.var(S, axis=0)))
        # чем выше col_var (изменения во времени) — тем более событийный трек
        score = min(100.0, col_var * 8e5 + 40.0) if col_var > 0 else 40.0
        return score, col_var
    except Exception:
        return 60.0, 0.0


# ============================================================ verdict
WEIGHTS = {
    "hook_energy":         1.5,
    "hook_repeatability":  1.3,
    "chorus_catchiness":   1.4,
    "drop_impact":         1.2,
    "tiktok_hookability":  1.5,
    "bpm_dance_fitness":   0.8,
    "loudness_lufs":       1.0,
    "stereo_width":        0.7,
    "low_end_power":       1.0,
    "vocal_presence":      1.1,
    "structure_clarity":   1.0,
    "novelty":             0.8,
}


def _verdict(score: float) -> str:
    if score >= 82.0: return "chart_ready"
    if score >= 68.0: return "solid"
    if score >= 50.0: return "needs_work"
    return "flop_risk"


def _actions(metrics: dict) -> list[str]:
    out = []
    for name, m in metrics.items():
        s = m.get("score", 0.0)
        if s >= 65.0:
            continue
        if name == "hook_energy":
            out.append("Припев тише куплета — подними RMS припева на +2 dB "
                       "или сделай drop громче")
        elif name == "hook_repeatability":
            out.append("Повторяй главный мотив ≥3 раза (chorus/hook loop)")
        elif name == "chorus_catchiness":
            out.append("Упрости гармонию припева до 2-3 аккордов, ритм — "
                       "равномерные 4/4")
        elif name == "drop_impact":
            out.append("Добавь build-up (риз) перед drop и полусекунду тишины "
                       "перед first-beat drop")
        elif name == "tiktok_hookability":
            out.append("Сделай моментальный вход в первые 2 сек (без длинного "
                       "intro) — для TikTok/Reels")
        elif name == "bpm_dance_fitness":
            out.append("BPM вне dance-диапазонов. Целься в 120-140 "
                       "(dance/phonk) или 70-95 (trap)")
        elif name == "loudness_lufs":
            out.append("LUFS вне streaming-target. Смастеринг под -9 dBFS "
                       "интегрированной громкости")
        elif name == "stereo_width":
            out.append("Стерео-картинка слишком узкая или слишком широкая. "
                       "Целься в correlation 0.6-0.85")
        elif name == "low_end_power":
            out.append("Проработай sub-bass 20-80 Hz — добавь 808 или "
                       "sub-sine")
        elif name == "vocal_presence":
            out.append("Вокал не читается в 2-5 kHz. Подними presence-полку "
                       "+2 dB на 3 kHz")
        elif name == "structure_clarity":
            out.append("Секции слишком похожи. Добавь контраст между "
                       "куплетом и припевом (плотность, элементы)")
        elif name == "novelty":
            out.append("Трек звучит формульно. Добавь уникальный саунд-дизайн "
                       "элемент (FX, стоп, воб, риверс)")
    return out


# ============================================================ main API
def score_track(master_wav: str,
                out_json: Optional[str] = None,
                sr: int = 22050) -> dict:
    """
    Основной API. `master_wav` — путь к финальному мастеру.
    Возвращает полный отчёт. Если out_json — сохраняет.
    """
    t0 = time.time()
    p = Path(master_wav)
    if not p.exists():
        return {"error": f"file not found: {master_wav}",
                "hit_score": 0.0, "verdict": "flop_risk"}

    try:
        y, s = _load_audio(str(p), sr=sr)
    except Exception as e:
        return {"error": f"load failed: {e}",
                "hit_score": 0.0, "verdict": "flop_risk"}

    metrics = {}

    def _add(name, val_tuple, hint=""):
        score, raw = val_tuple if isinstance(val_tuple, tuple) else (val_tuple, None)
        metrics[name] = {"score": round(float(score), 2),
                         "raw": raw,
                         "hint": hint}

    _add("hook_energy",         _hook_energy(y, s),
         "loud-quiet dynamic between chorus and verse")
    _add("hook_repeatability",  _hook_repeatability(y, s),
         "how many times main motif repeats")
    _add("chorus_catchiness",   _chorus_catchiness(y, s),
         "harmonic simplicity + rhythmic regularity")
    _add("drop_impact",         _drop_impact(y, s),
         "biggest RMS jump = drop")
    tt_score, tt_slice = _tiktok_hookability(y, s)
    _add("tiktok_hookability",  (tt_score, tt_slice),
         "instant-hook 25 sec slice for TikTok")
    _add("bpm_dance_fitness",   _bpm_dance_fitness(y, s),
         "BPM in dance/trap sweet spot")
    _add("loudness_lufs",       _loudness_lufs(y, s),
         "integrated dBFS ≈ LUFS streaming target")
    _add("stereo_width",        _stereo_width(str(p)),
         "channel correlation 0.6-0.85")
    _add("low_end_power",       _low_end_power(y, s),
         "20-80 Hz vs 200-2000 Hz ratio")
    _add("vocal_presence",      _vocal_presence(y, s),
         "2-5 kHz vocal readability")
    _add("structure_clarity",   _structure_clarity(y, s),
         "distinct intro/verse/chorus/outro")
    _add("novelty",             _novelty(y, s),
         "non-formulaic spectral variety")

    # weighted total
    total_w = sum(WEIGHTS.values())
    hit_score = sum(metrics[k]["score"] * WEIGHTS[k]
                    for k in WEIGHTS) / total_w

    report = {
        "hit_score":    round(hit_score, 2),
        "verdict":      _verdict(hit_score),
        "metrics":      metrics,
        "tiktok_slice": tt_slice,
        "actions":      _actions(metrics),
        "meta": {
            "file":        str(p),
            "duration_s":  round(len(y) / s, 2),
            "sr":          s,
            "elapsed_s":   round(time.time() - t0, 2),
            "librosa":     HAS_LIBROSA,
            "soundfile":   HAS_SF,
        },
    }

    if out_json:
        Path(out_json).write_text(json.dumps(report, ensure_ascii=False,
                                             indent=2), encoding="utf-8")
    return report


# ============================================================ CLI
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python hit_scorer.py <master.wav> [out.json]")
        sys.exit(1)
    r = score_track(sys.argv[1],
                    out_json=sys.argv[2] if len(sys.argv) > 2 else None)
    print(json.dumps(r, ensure_ascii=False, indent=2))

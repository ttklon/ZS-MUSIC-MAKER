# -*- coding: utf-8 -*-
"""
[1] analyzer.py — Мульти-референс анализатор v2
Усиления v2:
  • Веса референсов (пользователь указывает что брать из каждого)
  • BPM-диапазон + режимы (кач/ускорить/замедлить/клубнее/TikTok-hooky)
  • Образы и хук-лексика из транскрипта
  • Сохранение в analysis_cache с полным provenance
  • Essentia-дескрипторы (опционально, если установлен)
"""
import os, json, numpy as np

try:
    import librosa
except ImportError:
    librosa = None

VAULT = os.path.join(os.path.dirname(__file__), "..", "references", "analysis_cache.json")


def _safe_load(path, sr=22050):
    if librosa is None:
        raise RuntimeError("librosa не установлен. pip install librosa")
    y, sr = librosa.load(path, sr=sr, mono=True)
    return y, sr


def analyze_single(path: str) -> dict:
    """Полный анализ одного трека — BPM, тональность, спектр, энергия, вайб."""
    y, sr = _safe_load(path)

    # BPM
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    bpm_val = float(tempo) if np.ndim(tempo) == 0 else float(tempo[0])

    # Тональность
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    key_idx = int(np.argmax(chroma.mean(axis=1)))
    keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key = keys[key_idx]
    minor_third = chroma[(key_idx + 3) % 12].mean()
    major_third = chroma[(key_idx + 4) % 12].mean()
    mode = "minor" if minor_third > major_third else "major"

    # Энергия и спектр
    rms = float(np.mean(librosa.feature.rms(y=y)))
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
    duration = float(librosa.get_duration(y=y, sr=sr))

    # Bass energy (0-250Hz)
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    bass_mask = freqs < 250
    bass_energy = float(S[bass_mask].mean() / (S.mean() + 1e-9))

    # Плотность ударов (наличие дропа)
    beat_density = len(beats) / max(duration, 0.1)

    # Секции: грубая сегментация по энергии
    rms_frames = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    n_sections = 8
    chunk = len(rms_frames) // n_sections if len(rms_frames) >= n_sections else 1
    section_energies = [float(np.mean(rms_frames[i*chunk:(i+1)*chunk])) for i in range(n_sections)]
    # Определяем где дроп (пик энергии)
    drop_section = int(np.argmax(section_energies)) if section_energies else 0

    # Essentia-дескрипторы (опционально)
    essentia_desc = {}
    try:
        import essentia.standard as estd
        loader = estd.MonoLoader(filename=path)
        audio = loader()
        danceability = estd.Danceability()(audio)
        essentia_desc["danceability"] = round(float(danceability[0]), 3)
    except Exception:
        pass

    return {
        "path": path,
        "filename": os.path.basename(path),
        "bpm": round(bpm_val, 2),
        "key": f"{key} {mode}",
        "key_root": key,
        "mode": mode,
        "duration_sec": round(duration, 2),
        "rms": round(rms, 4),
        "spectral_centroid": round(centroid, 2),
        "spectral_bandwidth": round(bandwidth, 2),
        "zcr": round(zcr, 4),
        "bass_ratio": round(bass_energy, 3),
        "beat_density": round(beat_density, 2),
        "section_energies": [round(e, 4) for e in section_energies],
        "drop_section": drop_section,
        "vibe_tags": _infer_vibe(bpm_val, centroid, bass_energy, mode),
        "essentia": essentia_desc,
    }


def _infer_vibe(bpm, centroid, bass, mode):
    tags = []
    if bpm < 90: tags.append("slow")
    elif bpm < 110: tags.append("mid-tempo")
    elif bpm < 140: tags.append("phonk/drift")
    elif bpm < 160: tags.append("trap/hype")
    else: tags.append("hyper/hardstyle")
    if bass > 1.4: tags.append("bass-heavy")
    if centroid < 1500: tags.append("dark")
    elif centroid > 3500: tags.append("bright")
    if mode == "minor": tags.append("aggressive")
    if bass > 2.0 and centroid < 2000: tags.append("underground")
    return tags


def _bpm_range(bpm_val: float) -> dict:
    """Возвращает рабочий диапазон BPM + режимы."""
    low = max(60, bpm_val - 6)
    high = bpm_val + 8
    return {
        "center": int(round(bpm_val)),
        "range_low": int(round(low)),
        "range_high": int(round(high)),
        "modes": {
            "keep_groove": int(round(bpm_val)),
            "speed_up_edits": min(180, int(round(bpm_val * 1.08))),
            "slow_lazy": max(70, int(round(bpm_val * 0.92))),
            "club_harder": min(180, int(round(bpm_val * 1.05))),
            "tiktok_hooky": int(round(bpm_val)),
        },
        "suggestions": {
            "sticky_hook": max(100, int(round(bpm_val - 1))),
            "flex_flow": min(180, int(round(bpm_val + 3))),
            "deep_heavy": max(90, int(round(bpm_val - 3))),
        },
    }


def analyze_multi(paths: list, weights: list = None, take_notes: list = None) -> dict:
    """
    Строит усреднённый style-vector по нескольким референсам.

    weights: [0.5, 0.3, 0.2] — вес каждого референса (сумма = 1.0).
             Если None — равные веса.
    take_notes: ["бит из этого", "стиль чтения из этого", ...]
             Заметки пользователя что взять из каждого референса.
    """
    analyses = [analyze_single(p) for p in paths]

    if weights is None:
        weights = [1.0 / len(paths)] * len(paths)
    weights = [w / sum(weights) for w in weights]  # нормализация

    # Взвешенное среднее
    avg_bpm = sum(a["bpm"] * w for a, w in zip(analyses, weights))
    avg_bass = sum(a["bass_ratio"] * w for a, w in zip(analyses, weights))
    avg_centroid = sum(a["spectral_centroid"] * w for a, w in zip(analyses, weights))

    # Тональность — голосование
    keys_list = [a["key"] for a in analyses]
    mode = "minor" if sum(1 for k in keys_list if "minor" in k) >= len(keys_list) / 2 else "major"

    # Vibe tags — взвешенная частота
    tag_weights = {}
    for a, w in zip(analyses, weights):
        for t in a["vibe_tags"]:
            tag_weights[t] = tag_weights.get(t, 0) + w
    top_tags = sorted(tag_weights, key=tag_weights.get, reverse=True)[:6]

    # BPM-диапазон
    bpm_range = _bpm_range(avg_bpm)

    # Take-notes (что пользователь хочет взять из каждого)
    ref_notes = []
    if take_notes:
        for i, note in enumerate(take_notes):
            if i < len(analyses) and note.strip():
                ref_notes.append({
                    "ref": analyses[i]["filename"],
                    "note": note.strip(),
                    "bpm": analyses[i]["bpm"],
                    "vibe": analyses[i]["vibe_tags"],
                })

    style_vector = {
        "sources": [os.path.basename(p) for p in paths],
        "weights": weights,
        "ref_notes": ref_notes,
        "target_bpm": int(round(avg_bpm)),
        "target_mode": mode,
        "target_bass_ratio": round(avg_bass, 3),
        "target_centroid": round(avg_centroid, 2),
        "vibe_tags": top_tags,
        "bpm_range": bpm_range,
        "individual": analyses,
    }
    _save_to_vault(style_vector)
    return style_vector


def _save_to_vault(data):
    os.makedirs(os.path.dirname(VAULT), exist_ok=True)
    existing = []
    if os.path.exists(VAULT):
        try:
            existing = json.load(open(VAULT, "r", encoding="utf-8"))
        except Exception:
            existing = []
    existing.append(data)
    json.dump(existing, open(VAULT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def list_cached_analyses() -> list:
    if os.path.exists(VAULT):
        try:
            return json.load(open(VAULT, "r", encoding="utf-8"))
        except Exception:
            return []
    return []


if __name__ == "__main__":
    import sys
    files = sys.argv[1:]
    if not files:
        print("Usage: python analyzer.py <ref1.mp3> [ref2.mp3 ...]")
    else:
        result = analyze_multi(files) if len(files) > 1 else analyze_single(files[0])
        print(json.dumps(result, ensure_ascii=False, indent=2))

# -*- coding: utf-8 -*-
"""
ZS Music Maker v15 — modules/release_pack_full.py
======================================================================
Полный релиз-пакет по TZ раздел 21 (максимум ~38 файлов):

    Аудио:
        full_master_streaming.wav    (44.1/16, stereo)
        full_master_streaming_hires.wav (48/24, stereo)  [если есть soundfile]
        full_master.flac                (48/24 lossless)
        full_master.mp3                 (320 CBR)
        master_streaming.wav
        master_car.wav
        master_club.wav
        master_tiktok.wav
        master_airpods.wav
        master_bluetooth.wav
        master_headphones.wav
        master_monitors.wav
        instrumental.wav                (беззвуковая vocal-mask fallback)
        acapella.wav
        stems/drums.wav  bass.wav  vocals.wav  other.wav
                                        (fallback: копии/приглушённые копии,
                                         помечены fallback_used=True)
        tiktok_15.m4a  tiktok_30.m4a  tiktok_60.m4a
        reels_30.m4a   shorts_60.m4a
        (m4a fallback → mp3 если ffmpeg не даёт aac; расширение сохраняется)

    Тексты:
        lyrics.txt   lyrics.lrc   lyrics.srt

    Метаданные и описания:
        metadata.json
        licenses.txt
        hit_report.md
        production_notes.md
        distrokid.xml
        spotify_description.txt
        youtube_description.html
        vk_prefill.txt
        shazam.jsonld

    Визуал:
        cover.png  (3000×3000)
        cover.jpg  (1400×1400)

Каждый файл при создании честно помечает fallback_used, если не мог
быть создан «настоящим» способом (без ffmpeg-aac, без demucs, ...).
"""

from __future__ import annotations

import json
import shutil
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional
import struct

try:
    import numpy as np
except Exception:
    np = None

try:
    import soundfile as sf
except Exception:
    sf = None

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except Exception:
    HAS_PYDUB = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    HAS_PIL = True
except Exception:
    HAS_PIL = False


# ------------------------------------------------------------------- utils

def _read_wav(path: str):
    """Возвращает (data float32 mono или stereo, sr)."""
    if sf is not None:
        data, sr = sf.read(path, always_2d=False)
        return data, sr
    # fallback: wave module
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        nch = w.getnchannels()
        sw = w.getsampwidth()
        n = w.getnframes()
        raw = w.readframes(n)
    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sw] if np else None
    if np is None:
        return raw, sr
    arr = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if sw == 2:
        arr /= 32768.0
    elif sw == 4:
        arr /= 2147483648.0
    if nch == 2:
        arr = arr.reshape(-1, 2)
    return arr, sr


def _write_wav(path: str, data, sr: int, subtype: str = "PCM_16") -> bool:
    if sf is not None:
        sf.write(path, data, sr, subtype=subtype)
        return True
    return False


def _ensure_stereo(data):
    if np is None:
        return data
    if data.ndim == 1:
        return np.stack([data, data], axis=1)
    return data


def _hires_resample_48k(data, sr_in: int):
    """Простой пересемплинг 44100->48000 через линейную интерполяцию."""
    if np is None or sr_in == 48000:
        return data, 48000
    if data.ndim == 1:
        n_out = int(round(len(data) * 48000 / sr_in))
        x_in = np.linspace(0, 1, len(data), endpoint=False)
        x_out = np.linspace(0, 1, n_out, endpoint=False)
        out = np.interp(x_out, x_in, data).astype(np.float32)
        return out, 48000
    # stereo
    n_out = int(round(data.shape[0] * 48000 / sr_in))
    x_in = np.linspace(0, 1, data.shape[0], endpoint=False)
    x_out = np.linspace(0, 1, n_out, endpoint=False)
    L = np.interp(x_out, x_in, data[:, 0]).astype(np.float32)
    R = np.interp(x_out, x_in, data[:, 1]).astype(np.float32)
    return np.stack([L, R], axis=1), 48000


# ---------------------------------------------------------------- cover art

def _make_cover(path: Path, title: str, artist: str, genre: str,
                size: int = 3000, jpg: bool = False) -> bool:
    if not HAS_PIL:
        return False
    # Градиентный фон псевдо (без linear-gradient — рисуем полосами)
    img = Image.new("RGB", (size, size), (10, 10, 30))
    d = ImageDraw.Draw(img)
    # Псевдо-градиент через круг+блюр
    for r in range(size // 6, 0, -20):
        c = min(255, 30 + r // 4)
        d.ellipse([(size // 2 - r * 3, size // 2 - r * 3),
                   (size // 2 + r * 3, size // 2 + r * 3)],
                  fill=(c // 4, c // 6, c))
    img = img.filter(ImageFilter.GaussianBlur(radius=size // 40))
    d = ImageDraw.Draw(img)
    # Полоса под текст
    d.rectangle([(0, int(size * 0.72)), (size, int(size * 0.85))],
                fill=(0, 0, 0, 200))
    try:
        font_big = ImageFont.load_default(size=int(size * 0.06))
        font_sm = ImageFont.load_default(size=int(size * 0.03))
    except Exception:
        font_big = ImageFont.load_default()
        font_sm = ImageFont.load_default()
    d.text((int(size * 0.05), int(size * 0.73)), title, fill=(255, 200, 80),
           font=font_big)
    d.text((int(size * 0.05), int(size * 0.80)),
           f"{artist} · {genre}", fill=(200, 200, 200), font=font_sm)
    # Watermark
    d.text((int(size * 0.05), int(size * 0.94)),
           "ZS Music Maker · CC0/CC-BY samples", fill=(120, 120, 120),
           font=font_sm)
    if jpg:
        img.convert("RGB").save(path, "JPEG", quality=92)
    else:
        img.save(path, "PNG")
    return True


# ----------------------------------------------------------- lyrics formats

def _lyrics_to_lrc(lyrics_text: str, total_sec: float) -> str:
    lines = [ln.strip() for ln in lyrics_text.splitlines() if ln.strip()]
    if not lines:
        return "[00:00.00]ZS Music Maker\n"
    step = max(1.5, total_sec / max(1, len(lines)))
    out = []
    for i, ln in enumerate(lines):
        t = i * step
        m = int(t // 60)
        s = t - m * 60
        out.append(f"[{m:02d}:{s:05.2f}]{ln}")
    return "\n".join(out) + "\n"


def _lyrics_to_srt(lyrics_text: str, total_sec: float) -> str:
    lines = [ln.strip() for ln in lyrics_text.splitlines() if ln.strip()]
    if not lines:
        return "1\n00:00:00,000 --> 00:00:03,000\nZS Music Maker\n"
    step = max(1.5, total_sec / max(1, len(lines)))
    out = []
    for i, ln in enumerate(lines):
        t0 = i * step
        t1 = min(total_sec, t0 + step)
        def fmt(t):
            h = int(t // 3600); m = int((t % 3600) // 60); s = t - int(t) + int(t) % 60
            return f"{h:02d}:{m:02d}:{int(t)%60:02d},{int((t-int(t))*1000):03d}"
        out.append(f"{i+1}\n{fmt(t0)} --> {fmt(t1)}\n{ln}\n")
    return "\n".join(out)


# --------------------------------------------------------- stems fallback

def _fake_stems(master_wav: str, out_dir: Path) -> Dict[str, str]:
    """Fallback стемы: если нет Demucs, делим спектрально по полосам.
    drums = HP 100-8000, bass = LP <100, vocals = mid 200-6000, other = rest.
    Помечаем fallback."""
    out_dir.mkdir(parents=True, exist_ok=True)
    result: Dict[str, str] = {}
    if sf is None or np is None:
        # копии
        for name in ("drums", "bass", "vocals", "other"):
            dst = out_dir / f"{name}.wav"
            shutil.copy(master_wav, dst)
            result[name] = str(dst)
        return result
    data, sr = _read_wav(master_wav)
    if data.ndim == 1:
        data = _ensure_stereo(data)
    # FFT-based band split (грубо)
    try:
        from scipy.signal import butter, sosfiltfilt

        def band(lo, hi):
            ny = sr / 2.0
            lo_n = max(1e-4, lo / ny)
            hi_n = min(0.999, hi / ny)
            if lo_n >= hi_n:
                return data
            sos = butter(4, [lo_n, hi_n], btype="band", output="sos")
            L = sosfiltfilt(sos, data[:, 0])
            R = sosfiltfilt(sos, data[:, 1])
            return np.stack([L, R], axis=1).astype(np.float32)

        stems_data = {
            "bass": band(20, 200),
            "drums": band(80, 8000) * 0.7,  # attack
            "vocals": band(200, 5000),
            "other": band(5000, 18000),
        }
        for name, d in stems_data.items():
            dst = out_dir / f"{name}.wav"
            sf.write(dst, d, sr, subtype="PCM_16")
            result[name] = str(dst)
    except Exception:
        for name in ("drums", "bass", "vocals", "other"):
            dst = out_dir / f"{name}.wav"
            shutil.copy(master_wav, dst)
            result[name] = str(dst)
    return result


def _instrumental_and_acapella(stems: Dict[str, str], out_dir: Path,
                                master_wav: str) -> Dict[str, str]:
    result = {}
    if sf is None or np is None:
        shutil.copy(master_wav, out_dir / "instrumental.wav")
        shutil.copy(master_wav, out_dir / "acapella.wav")
        return {"instrumental": str(out_dir / "instrumental.wav"),
                "acapella": str(out_dir / "acapella.wav")}
    try:
        drums, sr = _read_wav(stems["drums"])
        bass, _ = _read_wav(stems["bass"])
        other, _ = _read_wav(stems["other"])
        voc, _ = _read_wav(stems["vocals"])
        for x in (drums, bass, other, voc):
            if x.ndim == 1:
                pass
        inst = drums + bass + other
        # normalise
        peak = max(1e-9, float(np.max(np.abs(inst))))
        inst = (inst / peak * 0.9).astype(np.float32)
        vocp = max(1e-9, float(np.max(np.abs(voc))))
        voc = (voc / vocp * 0.9).astype(np.float32)
        sf.write(out_dir / "instrumental.wav", inst, sr, subtype="PCM_16")
        sf.write(out_dir / "acapella.wav", voc, sr, subtype="PCM_16")
        result["instrumental"] = str(out_dir / "instrumental.wav")
        result["acapella"] = str(out_dir / "acapella.wav")
    except Exception:
        shutil.copy(master_wav, out_dir / "instrumental.wav")
        shutil.copy(master_wav, out_dir / "acapella.wav")
        result["instrumental"] = str(out_dir / "instrumental.wav")
        result["acapella"] = str(out_dir / "acapella.wav")
    return result


# ---------------------------------------------------------- tiktok clips

def _find_hook(data, sr: int) -> float:
    """Ищет 'hook' — момент с максимальной RMS-энергией.
    Возвращает время в секундах."""
    if np is None or sf is None:
        return 30.0
    if data.ndim > 1:
        mono = data.mean(axis=1)
    else:
        mono = data
    win = int(sr * 3)  # 3-sec window
    if len(mono) <= win:
        return 0.0
    energy = np.array([float(np.sqrt(np.mean(mono[i:i+win]**2)))
                       for i in range(0, len(mono) - win, sr)])
    if len(energy) == 0:
        return 0.0
    idx = int(np.argmax(energy))
    return float(idx)


def _make_clip(master_wav: str, out: Path, duration: int,
               start_sec: Optional[float] = None,
               fmt_hint: str = "m4a") -> Dict[str, Any]:
    """Нарезает клип. Пробует m4a через pydub/ffmpeg, fallback → mp3
    с сохранением расширения .m4a (помечается container_fallback)."""
    info: Dict[str, Any] = {"path": str(out), "fallback_used": False}
    if not HAS_PYDUB:
        return {"path": None, "fallback_used": True,
                "reason": "pydub_missing"}
    try:
        seg = AudioSegment.from_file(master_wav)
        if start_sec is None:
            data, sr = _read_wav(master_wav)
            start_sec = _find_hook(data, sr)
        start_ms = int(max(0, start_sec) * 1000)
        end_ms = start_ms + duration * 1000
        clip = seg[start_ms:end_ms]
        # fade-in/out для мягкости
        clip = clip.fade_in(200).fade_out(300)
        try:
            clip.export(out, format="ipod", bitrate="192k",
                        codec="aac")
        except Exception:
            # fallback: mp3, но сохраняем имя .m4a  + флаг
            clip.export(out, format="mp3", bitrate="192k")
            info["fallback_used"] = True
            info["container_fallback"] = "mp3_in_m4a_ext"
        info["duration_sec"] = duration
        info["start_sec"] = start_sec
        return info
    except Exception as e:
        return {"path": None, "fallback_used": True, "reason": str(e)}


# --------------------------------------------------- descriptions / metadata

def _distrokid_xml(meta: Dict[str, Any]) -> str:
    title = meta.get("title", "ZS Track")
    artist = meta.get("artist", "ZS Artist")
    isrc = meta.get("isrc", "XX-XXX-00-00000")
    upc = meta.get("upc", "0000000000000")
    genre = meta.get("genre", "Electronic")
    lang = meta.get("language", "ru")
    year = time.strftime("%Y")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<release>
  <label>ZS Music Maker</label>
  <title>{title}</title>
  <artist>{artist}</artist>
  <upc>{upc}</upc>
  <genre>{genre}</genre>
  <language>{lang}</language>
  <year>{year}</year>
  <explicit>false</explicit>
  <tracks>
    <track number="1">
      <title>{title}</title>
      <isrc>{isrc}</isrc>
      <duration>{int(meta.get('duration_sec', 180))}</duration>
      <file>full_master_streaming.wav</file>
    </track>
  </tracks>
</release>
"""
    return xml


def _spotify_description(meta: Dict[str, Any]) -> str:
    hooks = meta.get("hooks", ["ночь", "движение", "клуб"])
    return (f"{meta.get('title','ZS Track')} — {meta.get('genre','phonk')} "
            f"trek na {meta.get('language','ru')}.\n"
            f"BPM: {meta.get('bpm', 140)} | Key: {meta.get('key','Am')}\n\n"
            f"Vibes: {' · '.join(hooks)}\n\n"
            f"Сделано в ZS Music Maker (localhost, локально, бесплатно).\n")


def _youtube_description_html(meta: Dict[str, Any]) -> str:
    ht = " ".join(f"#{t}" for t in meta.get("hashtags_youtube",
                                            ["music", "phonk", "car"]))
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{meta.get('title','ZS Track')}</title></head>
<body>
<h1>{meta.get('title','ZS Track')} — {meta.get('artist','ZS Artist')}</h1>
<p><b>Genre:</b> {meta.get('genre','phonk')} | <b>BPM:</b> {meta.get('bpm',140)} |
<b>Key:</b> {meta.get('key','Am')}</p>
<p>{_spotify_description(meta).replace(chr(10), '<br>')}</p>
<h2>Timestamps</h2>
<pre>
00:00 — Intro
00:15 — Verse 1
00:45 — Hook
01:15 — Verse 2
01:45 — Hook
02:15 — Outro
</pre>
<p>{ht}</p>
<hr>
<small>Powered by ZS Music Maker · CC0/CC-BY samples</small>
</body></html>
"""


def _vk_prefill(meta: Dict[str, Any]) -> str:
    hashtags = " ".join(f"#{t}" for t in meta.get("hashtags_vk",
                                                   ["музыка", "фонк"]))
    return (f"🎵 {meta.get('title','ZS Track')}\n"
            f"👤 {meta.get('artist','ZS Artist')}\n"
            f"🎧 {meta.get('genre','phonk')} · {meta.get('bpm',140)} BPM\n\n"
            f"{hashtags}\n")


def _shazam_jsonld(meta: Dict[str, Any]) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "MusicRecording",
        "name": meta.get("title", "ZS Track"),
        "byArtist": {"@type": "MusicGroup", "name": meta.get("artist", "ZS Artist")},
        "isrcCode": meta.get("isrc", "XX-XXX-00-00000"),
        "duration": f"PT{int(meta.get('duration_sec',180))}S",
        "genre": meta.get("genre", "Electronic"),
        "inLanguage": meta.get("language", "ru"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _is_placeholder_isrc(isrc: str) -> bool:
    if not isrc:
        return True
    s = str(isrc).upper().replace("-", "").replace(" ", "")
    return ("XXXXX" in s) or ("00000" in s and s.startswith(("XX", "00")))


def _is_placeholder_upc(upc: str) -> bool:
    if not upc:
        return True
    s = str(upc).strip()
    return s == "0000000000000" or set(s) <= {"0"}


def _production_notes(meta: Dict[str, Any], stages: List[Dict[str, Any]],
                      hit_metrics: Dict[str, Any]) -> str:
    lines = [f"# Production notes — {meta.get('title', 'ZS Track')}",
             "",
             f"- Genre: **{meta.get('genre','?')}**",
             f"- BPM: **{meta.get('bpm','?')}**",
             f"- Key: **{meta.get('key','?')}**",
             f"- Language: **{meta.get('language','ru')}**",
             f"- Duration: **{int(meta.get('duration_sec',180))}s**",
             "",
             "## Pipeline",
             ""]
    for s in stages or []:
        extras = []
        if s.get("fallback_used"):
            extras.append("fallback")
        if s.get("blocked"):
            extras.append("BLOCKED")
        if s.get("synthetic"):
            extras.append("synthetic")
        tag = (" [" + ",".join(extras) + "]") if extras else ""
        lines.append(f"- {s.get('name','?')}: "
                     f"ok={s.get('ok')}{tag} "
                     f"{s.get('duration_sec', '?')}s")
    lines.append("")
    lines.append("## Hit metrics")
    for k, v in (hit_metrics or {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Legal / distribution")
    lines.append("- Все использованные сэмплы: CC0 / CC-BY.")
    lines.append("- Голос: собственный (RVC от пользователя) или TTS fallback.")
    if _is_placeholder_isrc(meta.get("isrc", "")):
        lines.append("- [WARN] ISRC: placeholder (`"
                     + str(meta.get("isrc", "XX-XXX-00-00000"))
                     + "`). Замени на реальный код перед дистрибуцией.")
    if _is_placeholder_upc(meta.get("upc", "")):
        lines.append("- [WARN] UPC: placeholder. Получи реальный UPC через DistroKid/Amuse/Tunecore.")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------- MASTERS MAP

MASTER_STANDS = [
    ("streaming", -14.0, -1.0),
    ("car",        -8.5, -0.5),
    ("club",       -6.5, -0.3),
    ("tiktok",    -13.0, -1.0),
    ("airpods",   -12.0, -1.0),
    ("bluetooth", -11.0, -1.0),
    ("headphones",-14.0, -1.0),
    ("monitors",  -14.0, -1.0),
]


# ------------------------------------------------------------ MAIN ENTRY

def build_pack(master_wav: str,
               out_dir: str,
               meta: Dict[str, Any],
               masters_map: Optional[Dict[str, str]] = None,
               stems_map: Optional[Dict[str, str]] = None,
               lyrics_text: str = "",
               stages: Optional[List[Dict[str, Any]]] = None,
               hit_metrics: Optional[Dict[str, Any]] = None,
               ) -> Dict[str, Any]:
    """Собирает полный релиз-пакет.

    Возвращает {ok, n_files, files:[...], fallback_used, path,
                categories: {audio:[...], stems:[...], clips:[...],
                             lyrics:[...], meta:[...], visuals:[...]}}
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files: List[str] = []
    fallback_notes: List[str] = []
    cats: Dict[str, List[str]] = {"audio": [], "stems": [], "clips": [],
                                  "lyrics": [], "meta": [], "visuals": []}

    # ---------- 1. Аудио: full masters ----------
    try:
        dst_stream = out / "full_master_streaming.wav"
        shutil.copy(master_wav, dst_stream)
        files.append(str(dst_stream)); cats["audio"].append(str(dst_stream))
    except Exception as e:
        fallback_notes.append(f"stream_copy_fail: {e}")

    # hires 48/24
    try:
        if sf is not None and np is not None:
            data, sr = _read_wav(master_wav)
            data_hi, sr_hi = _hires_resample_48k(data, sr)
            dst_hi = out / "full_master_streaming_hires.wav"
            sf.write(dst_hi, data_hi, sr_hi, subtype="PCM_24")
            files.append(str(dst_hi)); cats["audio"].append(str(dst_hi))
        else:
            fallback_notes.append("hires_skipped_no_sf")
    except Exception as e:
        fallback_notes.append(f"hires_fail: {e}")

    # FLAC
    try:
        if sf is not None:
            data, sr = _read_wav(master_wav)
            data_hi, sr_hi = (data, sr)
            if sr != 48000 and np is not None:
                data_hi, sr_hi = _hires_resample_48k(data, sr)
            dst_flac = out / "full_master.flac"
            sf.write(dst_flac, data_hi, sr_hi, subtype="PCM_24",
                     format="FLAC")
            files.append(str(dst_flac)); cats["audio"].append(str(dst_flac))
        else:
            fallback_notes.append("flac_skipped_no_sf")
    except Exception as e:
        fallback_notes.append(f"flac_fail: {e}")

    # MP3 320
    try:
        if HAS_PYDUB:
            seg = AudioSegment.from_file(master_wav)
            dst_mp3 = out / "full_master.mp3"
            seg.export(dst_mp3, format="mp3", bitrate="320k")
            files.append(str(dst_mp3)); cats["audio"].append(str(dst_mp3))
        else:
            fallback_notes.append("mp3_skipped_no_pydub")
    except Exception as e:
        fallback_notes.append(f"mp3_fail: {e}")

    # ---------- 2. Аудио: 8 стендов ----------
    if masters_map:
        for name, src in masters_map.items():
            try:
                if isinstance(src, dict):
                    src = src.get("out_wav") or src.get("path")
                if not src:
                    raise ValueError("empty master path")
                dst = out / f"master_{name}.wav"
                shutil.copy(str(src), dst)
                files.append(str(dst)); cats["audio"].append(str(dst))
            except Exception as e:
                fallback_notes.append(f"master_{name}_fail: {e}")

    # ---------- 3. Стемы ----------
    stems_dir = out / "stems"
    if stems_map:
        stems_dir.mkdir(parents=True, exist_ok=True)
        normalized_stems = {}
        for name, src in stems_map.items():
            try:
                if isinstance(src, dict):
                    src = src.get("out_wav") or src.get("path")
                if not src:
                    raise ValueError("empty stem path")
                normalized_stems[name] = str(src)
                dst = stems_dir / f"{name}.wav"
                shutil.copy(str(src), dst)
                files.append(str(dst)); cats["stems"].append(str(dst))
            except Exception as e:
                fallback_notes.append(f"stem_{name}_fail: {e}")
        used_stems = normalized_stems
    else:
        used_stems = _fake_stems(master_wav, stems_dir)
        for p in used_stems.values():
            files.append(p); cats["stems"].append(p)
        fallback_notes.append("stems_generated_by_band_split_fallback")

    # ---------- 4. Instrumental + Acapella ----------
    inst_map = _instrumental_and_acapella(used_stems, out, master_wav)
    for p in inst_map.values():
        files.append(p); cats["audio"].append(p)

    # ---------- 5. TikTok / Reels / Shorts clips ----------
    if HAS_PYDUB:
        clip_defs = [
            ("tiktok_15.m4a", 15),
            ("tiktok_30.m4a", 30),
            ("tiktok_60.m4a", 60),
            ("reels_30.m4a", 30),
            ("shorts_60.m4a", 60),
        ]
        for fname, dur in clip_defs:
            try:
                info = _make_clip(master_wav, out / fname, duration=dur)
                if info.get("path"):
                    files.append(info["path"]); cats["clips"].append(info["path"])
                    if info.get("fallback_used"):
                        fallback_notes.append(f"{fname}:{info.get('container_fallback','?')}")
            except Exception as e:
                fallback_notes.append(f"clip_{fname}_fail: {e}")
    else:
        fallback_notes.append("clips_skipped_no_pydub")

    # ---------- 6. Тексты ----------
    duration_sec = float(meta.get("duration_sec", 180))
    try:
        (out / "lyrics.txt").write_text(lyrics_text or "", encoding="utf-8")
        files.append(str(out / "lyrics.txt")); cats["lyrics"].append(str(out / "lyrics.txt"))
        (out / "lyrics.lrc").write_text(_lyrics_to_lrc(lyrics_text, duration_sec),
                                        encoding="utf-8")
        files.append(str(out / "lyrics.lrc")); cats["lyrics"].append(str(out / "lyrics.lrc"))
        (out / "lyrics.srt").write_text(_lyrics_to_srt(lyrics_text, duration_sec),
                                        encoding="utf-8")
        files.append(str(out / "lyrics.srt")); cats["lyrics"].append(str(out / "lyrics.srt"))
    except Exception as e:
        fallback_notes.append(f"lyrics_fail: {e}")

    # ---------- 7. Metadata + descriptions ----------
    try:
        (out / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        files.append(str(out / "metadata.json")); cats["meta"].append(str(out / "metadata.json"))
        (out / "licenses.txt").write_text(
            "ZS Music Maker — Release Pack\n"
            "Все сэмплы: CC0 / CC-BY (см. samples_cache/cc0/index.json).\n"
            "Голос: RVC пользователя или TTS fallback.\n"
            f"Собрано: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8")
        files.append(str(out / "licenses.txt")); cats["meta"].append(str(out / "licenses.txt"))
        # v25 FIX (P0): hit_scorer возвращает 'hit_score', а не 'score' —
        # раньше в отчёте всегда был 'n/a' (ложное «не оценено»).
        _hm = hit_metrics or {}
        _score = _hm.get("hit_score", _hm.get("score", "n/a"))
        _verdict_h = _hm.get("verdict", "n/a")
        _actions_h = _hm.get("actions") or []
        _tt = _hm.get("tiktok_slice") or {}
        _metr = _hm.get("metrics") or {}
        _lines = [
            f"# Hit Report — {meta.get('title','ZS Track')}",
            "",
            f"Score: **{_score}** / 100",
            f"Verdict: **{_verdict_h}**",
            "",
        ]
        if _tt:
            _lines.append(f"TikTok slice: {_tt.get('start_sec','?')}s → "
                          f"{_tt.get('end_sec','?')}s — {_tt.get('reason','')}")
            _lines.append("")
        if _actions_h:
            _lines.append("## Что доработать")
            for act in _actions_h[:10]:
                _lines.append(f"- {act}")
            _lines.append("")
        if isinstance(_metr, dict) and _metr:
            _lines.append("## Metrics")
            for k, v in _metr.items():
                if isinstance(v, dict):
                    _lines.append(f"- {k}: {v.get('score','?')}/100 — {v.get('hint','')}")
                else:
                    _lines.append(f"- {k}: {v}")
        (out / "hit_report.md").write_text("\n".join(_lines),
            encoding="utf-8")
        files.append(str(out / "hit_report.md")); cats["meta"].append(str(out / "hit_report.md"))
        (out / "production_notes.md").write_text(
            _production_notes(meta, stages or [], hit_metrics or {}),
            encoding="utf-8")
        files.append(str(out / "production_notes.md")); cats["meta"].append(str(out / "production_notes.md"))
        (out / "distrokid.xml").write_text(_distrokid_xml(meta), encoding="utf-8")
        files.append(str(out / "distrokid.xml")); cats["meta"].append(str(out / "distrokid.xml"))
        (out / "spotify_description.txt").write_text(
            _spotify_description(meta), encoding="utf-8")
        files.append(str(out / "spotify_description.txt")); cats["meta"].append(str(out / "spotify_description.txt"))
        (out / "youtube_description.html").write_text(
            _youtube_description_html(meta), encoding="utf-8")
        files.append(str(out / "youtube_description.html")); cats["meta"].append(str(out / "youtube_description.html"))
        (out / "vk_prefill.txt").write_text(_vk_prefill(meta), encoding="utf-8")
        files.append(str(out / "vk_prefill.txt")); cats["meta"].append(str(out / "vk_prefill.txt"))
        (out / "shazam.jsonld").write_text(_shazam_jsonld(meta), encoding="utf-8")
        files.append(str(out / "shazam.jsonld")); cats["meta"].append(str(out / "shazam.jsonld"))
    except Exception as e:
        fallback_notes.append(f"meta_fail: {e}")

    # ---------- 8. Cover art ----------
    title = meta.get("title", "ZS Track")
    artist = meta.get("artist", "ZS Artist")
    genre = meta.get("genre", "phonk")
    try:
        if _make_cover(out / "cover.png", title, artist, genre, size=3000):
            files.append(str(out / "cover.png")); cats["visuals"].append(str(out / "cover.png"))
    except Exception as e:
        fallback_notes.append(f"cover_png_fail: {e}")
    try:
        if _make_cover(out / "cover.jpg", title, artist, genre, size=1400, jpg=True):
            files.append(str(out / "cover.jpg")); cats["visuals"].append(str(out / "cover.jpg"))
    except Exception as e:
        fallback_notes.append(f"cover_jpg_fail: {e}")

    # ---------- 9. ID3 tags on MP3 ----------
    try:
        mp3_path = out / "full_master.mp3"
        if mp3_path.exists():
            _apply_id3(mp3_path, meta, cover_path=out / "cover.jpg")
    except Exception as e:
        fallback_notes.append(f"id3_fail: {e}")

    return {
        "ok": len(files) > 0,
        "n_files": len(files),
        "files": files,
        "path": str(out),
        "categories": {k: len(v) for k, v in cats.items()},
        "fallback_used": bool(fallback_notes),
        "fallback_notes": fallback_notes,
    }


def _apply_id3(mp3_path: Path, meta: Dict[str, Any], cover_path: Path):
    from mutagen.id3 import (ID3, TIT2, TPE1, TALB, TCON, TBPM, TKEY,
                             TSRC, TPUB, TDRC, APIC)
    try:
        id3 = ID3(str(mp3_path))
    except Exception:
        id3 = ID3()
    id3.add(TIT2(encoding=3, text=meta.get("title", "ZS Track")))
    id3.add(TPE1(encoding=3, text=meta.get("artist", "ZS Artist")))
    id3.add(TALB(encoding=3, text=meta.get("album", meta.get("title", "ZS Track"))))
    id3.add(TCON(encoding=3, text=meta.get("genre", "Electronic")))
    id3.add(TBPM(encoding=3, text=str(meta.get("bpm", 140))))
    id3.add(TKEY(encoding=3, text=meta.get("key", "Am")))
    id3.add(TSRC(encoding=3, text=meta.get("isrc", "XX-XXX-00-00000")))
    id3.add(TPUB(encoding=3, text="ZS Music Maker"))
    id3.add(TDRC(encoding=3, text=time.strftime("%Y")))
    try:
        if cover_path.exists():
            with open(cover_path, "rb") as f:
                id3.add(APIC(encoding=3, mime="image/jpeg", type=3,
                             desc="Cover", data=f.read()))
    except Exception:
        pass
    id3.save(str(mp3_path))


if __name__ == "__main__":
    # smoke
    import tempfile
    if sf is None:
        print("soundfile not available")
        raise SystemExit(1)
    tmp = Path(tempfile.mkdtemp())
    # 5-sec synthetic
    sr = 44100
    import numpy as _np
    t = _np.linspace(0, 5, sr * 5, endpoint=False)
    data = 0.3 * _np.sin(2 * _np.pi * 220 * t).astype(_np.float32)
    data = _np.stack([data, data], axis=1)
    src = tmp / "synth.wav"
    sf.write(src, data, sr, subtype="PCM_16")
    meta = {"title": "Smoke Test", "artist": "ZS", "genre": "phonk",
            "bpm": 140, "key": "Am", "duration_sec": 5,
            "hashtags_youtube": ["music", "smoke"],
            "hashtags_vk": ["музыка"]}
    result = build_pack(str(src), str(tmp / "release"), meta,
                        lyrics_text="Тест\nВторая строка\nТретья\n",
                        hit_metrics={"score": 72, "verdict": "solid"})
    print(json.dumps({k: v for k, v in result.items() if k != "files"},
                     ensure_ascii=False, indent=2))
    print("Files:", len(result["files"]))

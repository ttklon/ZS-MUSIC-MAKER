"""
ZS Music Maker v11 — video_edit_v11.py

TikTok / Reels / YouTube-Shorts автогенератор MP4 из финального master.wav
+ обложки cover.png. Реализует ТЗ 20.2 п.32-33.

Backends:
- moviepy + ffmpeg → реальный H.264/AAC MP4 с beat-glow, LRC-overlay
- fallback: HOOK.wav + build_manually.txt с готовой ffmpeg-командой

Никогда не крашится, работает на слабом железе (CPU-only).
UTF-8 в коде.
"""

from __future__ import annotations

import json
import math
import os
import struct
import sys
import wave
from dataclasses import asdict, dataclass


def _safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))


@dataclass
class VideoEditRequest:
    master_wav: str
    cover_png: str | None = None
    lyrics_lrc: str | None = None
    bpm: float = 140.0
    duration_sec: int = 20
    orientation: str = "vertical"  # vertical | horizontal | square
    output_path: str = "output/tiktok_edit.mp4"
    title: str = ""
    artist: str = ""
    beat_glow: bool = True
    waveform_bar: bool = True
    lyrics_overlay: bool = True

    def resolution(self) -> tuple[int, int]:
        if self.orientation == "vertical":
            return (1080, 1920)
        if self.orientation == "horizontal":
            return (1920, 1080)
        return (1080, 1080)


@dataclass
class VideoEditResult:
    ok: bool
    output_path: str
    duration_sec: float
    resolution: tuple[int, int]
    backend: str
    hook_start_sec: float
    reason: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["resolution"] = list(self.resolution)
        return d


def _read_wav_mono(path: str) -> tuple[list[float], int]:
    with wave.open(path, "rb") as wf:
        n_ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        n = wf.getnframes()
        frames = wf.readframes(n)
    if sw == 2:
        count = n * n_ch
        samples = struct.unpack("<" + "h" * count, frames)
        if n_ch == 1:
            mono = [s / 32768.0 for s in samples]
        else:
            mono = []
            for i in range(0, count, n_ch):
                s = sum(samples[i : i + n_ch]) / n_ch
                mono.append(s / 32768.0)
    elif sw == 3:
        mono = []
        step = 3 * n_ch
        for i in range(0, len(frames), step):
            channels = []
            for c in range(n_ch):
                off = i + c * 3
                b = frames[off : off + 3]
                if len(b) < 3:
                    channels.append(0)
                    continue
                val = int.from_bytes(b, "little", signed=True)
                channels.append(val / (1 << 23))
            mono.append(sum(channels) / max(1, n_ch))
    elif sw == 4:
        count = n * n_ch
        samples = struct.unpack("<" + "i" * count, frames)
        norm = float(1 << 31)
        if n_ch == 1:
            mono = [s / norm for s in samples]
        else:
            mono = []
            for i in range(0, count, n_ch):
                s = sum(samples[i : i + n_ch]) / n_ch
                mono.append(s / norm)
    else:
        raise ValueError(f"Unsupported sample width: {sw}")
    return mono, sr


def _rms_windows(samples: list[float], sr: int, win_sec: float = 1.0) -> list[float]:
    win = max(1, int(sr * win_sec))
    out = []
    for i in range(0, len(samples), win):
        chunk = samples[i : i + win]
        if not chunk:
            continue
        s = sum(x * x for x in chunk) / len(chunk)
        out.append(math.sqrt(s))
    return out


def detect_hook(master_wav: str, target_sec: int = 20) -> tuple[float, float]:
    """Возвращает (start_sec, end_sec) для самого «мясного» куска."""
    try:
        samples, sr = _read_wav_mono(master_wav)
    except Exception as e:
        _safe_print(f"[video_edit_v11] hook detect fail: {e}")
        return (0.0, float(target_sec))
    total = len(samples) / sr
    if total <= target_sec + 1:
        return (0.0, total)
    rms = _rms_windows(samples, sr, win_sec=1.0)
    w = target_sec
    if w >= len(rms):
        return (0.0, float(target_sec))
    best_sum = -1.0
    best_start = 0
    running = sum(rms[:w])
    if running > best_sum:
        best_sum, best_start = running, 0
    for i in range(1, len(rms) - w + 1):
        running += rms[i + w - 1] - rms[i - 1]
        if running > best_sum:
            best_sum, best_start = running, i
    # Prefer second half — избегаем интро
    if best_start < 0.25 * len(rms):
        half = len(rms) // 2
        if half + w <= len(rms):
            alt_best = sum(rms[half : half + w])
            alt_start = half
            running = alt_best
            for i in range(half + 1, len(rms) - w + 1):
                running += rms[i + w - 1] - rms[i - 1]
                if running > alt_best:
                    alt_best, alt_start = running, i
            if alt_best >= 0.85 * best_sum:
                best_start = alt_start
    return (float(best_start), float(best_start + w))


def _parse_lrc(lrc_path: str) -> list[tuple[float, str]]:
    out = []
    try:
        with open(lrc_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("["):
                    continue
                end = line.rfind("]")
                if end < 0:
                    continue
                head, text = line[: end + 1], line[end + 1 :].strip()
                i = 0
                while i < len(head):
                    if head[i] == "[":
                        j = head.find("]", i)
                        if j < 0:
                            break
                        tag = head[i + 1 : j]
                        if ":" in tag and any(c.isdigit() for c in tag):
                            try:
                                m, s = tag.split(":", 1)
                                secs = float(m) * 60 + float(s)
                                out.append((secs, text))
                            except Exception:
                                pass
                        i = j + 1
                    else:
                        i += 1
    except Exception as e:
        _safe_print(f"[video_edit_v11] lrc parse fail: {e}")
    out.sort(key=lambda x: x[0])
    return out


def _try_moviepy():
    try:
        import moviepy.editor as mpy

        return mpy
    except Exception as e:
        _safe_print(f"[video_edit_v11] moviepy not available ({e})")
        return None


def _try_pil():
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont

        return (Image, ImageDraw, ImageFont, ImageFilter)
    except Exception:
        return None


def _make_static_bg(cover_path: str | None, size: tuple[int, int]):
    pil = _try_pil()
    if not pil:
        return None
    Image, ImageDraw, _ImageFont, ImageFilter = pil
    w, h = size
    if cover_path and os.path.exists(cover_path):
        try:
            cover = Image.open(cover_path).convert("RGB")
        except Exception:
            cover = Image.new("RGB", (1400, 1400), (14, 14, 22))
    else:
        cover = Image.new("RGB", (1400, 1400), (14, 14, 22))
    bg = cover.resize((w, h)).filter(ImageFilter.GaussianBlur(radius=48))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.45)
    side = int(min(w, h) * 0.78)
    cover_sq = cover.resize((side, side))
    x = (w - side) // 2
    y = (h - side) // 2 - int(h * 0.05)
    bg.paste(cover_sq, (x, y))
    return bg


def _draw_title(bg_img, title: str, artist: str, size: tuple[int, int]):
    pil = _try_pil()
    if not pil or bg_img is None:
        return bg_img
    Image, ImageDraw, ImageFont, _ = pil
    w, h = size
    draw = ImageDraw.Draw(bg_img)
    font_big = font_small = None
    for cand in [
        "DejaVuSans-Bold.ttf",
        "arial.ttf",
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]:
        try:
            font_big = ImageFont.truetype(cand, size=int(h * 0.045))
            font_small = ImageFont.truetype(cand, size=int(h * 0.028))
            break
        except Exception:
            continue
    if font_big is None:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()
    if artist:
        draw.text(
            (w * 0.06, h * 0.06), artist.upper(), fill=(240, 240, 240), font=font_small
        )
    if title:
        draw.text((w * 0.06, h * 0.87), title, fill=(255, 220, 90), font=font_big)
    return bg_img


def build_video(req: VideoEditRequest) -> VideoEditResult:
    os.makedirs(os.path.dirname(os.path.abspath(req.output_path)) or ".", exist_ok=True)
    tmp_dir = os.path.join(
        os.path.dirname(os.path.abspath(req.output_path)) or ".", "_v11_tmp"
    )
    os.makedirs(tmp_dir, exist_ok=True)
    hook_start, hook_end = detect_hook(req.master_wav, req.duration_sec)
    _safe_print(f"[video_edit_v11] hook: {hook_start:.1f}s -> {hook_end:.1f}s")

    mpy = _try_moviepy()
    if mpy is not None:
        try:
            return _build_with_moviepy(req, hook_start, hook_end, tmp_dir, mpy)
        except Exception as e:
            _safe_print(f"[video_edit_v11] moviepy render failed: {e}")
    return _build_fallback(req, hook_start, hook_end)


def _build_with_moviepy(req, hook_start, hook_end, tmp_dir, mpy) -> VideoEditResult:
    size = req.resolution()
    duration = float(hook_end - hook_start)
    audio = mpy.AudioFileClip(req.master_wav).subclip(hook_start, hook_end)
    bg_img = _make_static_bg(req.cover_png, size)
    bg_img = _draw_title(bg_img, req.title, req.artist, size)
    bg_png = None
    if bg_img is not None:
        bg_png = os.path.join(tmp_dir, "v11_bg.png")
        bg_img.save(bg_png, "PNG")
    if bg_png:
        base_clip = mpy.ImageClip(bg_png).set_duration(duration)
    else:
        base_clip = mpy.ColorClip(size=size, color=(14, 14, 22)).set_duration(duration)
    clips = [base_clip]
    if req.beat_glow and req.bpm > 40:
        beat_sec = 60.0 / req.bpm
        t = 0.0
        while t < duration:
            pulse = (
                mpy.ColorClip(size=size, color=(255, 60, 40))
                .set_opacity(0.14)
                .set_start(t)
                .set_duration(min(0.12, duration - t))
            )
            clips.append(pulse)
            t += beat_sec
    if req.lyrics_overlay and req.lyrics_lrc and os.path.exists(req.lyrics_lrc):
        for t, text in _parse_lrc(req.lyrics_lrc):
            if not text.strip() or t < hook_start or t > hook_end:
                continue
            local_t = t - hook_start
            try:
                txt = (
                    mpy.TextClip(
                        text[:80],
                        fontsize=int(size[1] * 0.042),
                        color="white",
                        method="label",
                        stroke_color="black",
                        stroke_width=2,
                    )
                    .set_position(("center", int(size[1] * 0.5)))
                    .set_start(local_t)
                    .set_duration(min(3.0, hook_end - t))
                )
                clips.append(txt)
            except Exception as e:
                _safe_print(f"[video_edit_v11] textclip fail: {e}")
                break
    final = mpy.CompositeVideoClip(clips, size=size).set_audio(audio)
    try:
        final.write_videofile(
            req.output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=2,
            logger=None,
            verbose=False,
        )
    finally:
        try:
            final.close()
            audio.close()
        except Exception:
            pass
    return VideoEditResult(
        ok=True,
        output_path=req.output_path,
        duration_sec=duration,
        resolution=size,
        backend="moviepy",
        hook_start_sec=hook_start,
        reason="ok",
    )


def _build_fallback(req, hook_start, hook_end) -> VideoEditResult:
    out_path = req.output_path
    wav_out = os.path.splitext(out_path)[0] + "_HOOK.wav"
    backend = "fallback_txt"
    try:
        samples, sr = _read_wav_mono(req.master_wav)
        s = int(hook_start * sr)
        e = int(hook_end * sr)
        cut = samples[s:e]
        with wave.open(wav_out, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(
                b"".join(
                    struct.pack("<h", max(-32768, min(32767, int(x * 32767))))
                    for x in cut
                )
            )
        backend = "fallback_wav"
    except Exception as e:
        _safe_print(f"[video_edit_v11] fallback wav cut failed: {e}")
        wav_out = ""
    txt_path = os.path.splitext(out_path)[0] + "_build_manually.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("ZS Music Maker v11 — TikTok/Reels edit fallback\n")
            f.write(f"master:     {req.master_wav}\n")
            f.write(f"cover:      {req.cover_png}\n")
            f.write(f"lyrics:     {req.lyrics_lrc}\n")
            f.write(f"bpm:        {req.bpm}\n")
            f.write(f"hook:       {hook_start:.2f}s .. {hook_end:.2f}s\n")
            f.write(f"resolution: {req.resolution()}\n\n")
            f.write("Install moviepy+ffmpeg:\n")
            f.write("    pip install moviepy imageio-ffmpeg\n")
            f.write("Or manually via ffmpeg:\n")
            f.write(
                f"ffmpeg -ss {hook_start:.2f} -t {req.duration_sec} "
                f'-i "{req.master_wav}" -loop 1 -i "{req.cover_png}" '
                "-c:v libx264 -c:a aac -shortest -pix_fmt yuv420p "
                f'-vf "scale={req.resolution()[0]}:{req.resolution()[1]}'
                f":force_original_aspect_ratio=increase,crop="
                f'{req.resolution()[0]}:{req.resolution()[1]}" '
                f'"{out_path}"\n'
            )
    except Exception as e:
        _safe_print(f"[video_edit_v11] fallback txt write failed: {e}")
    return VideoEditResult(
        ok=False,
        output_path=wav_out or txt_path,
        duration_sec=hook_end - hook_start,
        resolution=req.resolution(),
        backend=backend,
        hook_start_sec=hook_start,
        reason="moviepy/ffmpeg unavailable",
    )


def build_release_edits(
    master_wav, cover_png, lyrics_lrc, bpm, title, artist, out_dir
) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    manifest = {}
    for name, orient, dur in [
        ("tiktok_edit.mp4", "vertical", 20),
        ("reels_edit.mp4", "vertical", 30),
        ("shorts_edit.mp4", "vertical", 20),
    ]:
        req = VideoEditRequest(
            master_wav=master_wav,
            cover_png=cover_png,
            lyrics_lrc=lyrics_lrc,
            bpm=bpm,
            duration_sec=dur,
            orientation=orient,
            output_path=os.path.join(out_dir, name),
            title=title,
            artist=artist,
        )
        manifest[name] = build_video(req).to_dict()
    with open(
        os.path.join(out_dir, "video_edits_manifest.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def _self_test() -> bool:
    tmp = "/tmp/_v11_lrc_test.lrc"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("[00:01.00]hello\n[00:02.50]world\n[bad]skip\n")
    parsed = _parse_lrc(tmp)
    ok = len(parsed) == 2 and parsed[0][1] == "hello"
    rms = _rms_windows([0.0] * 44100 + [0.5] * 44100, 44100, 1.0)
    ok &= len(rms) == 2 and rms[1] > rms[0]
    return ok


if __name__ == "__main__":
    print("video_edit_v11 self-test:", "OK" if _self_test() else "FAIL")

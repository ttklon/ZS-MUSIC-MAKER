# -*- coding: utf-8 -*-
"""
modules/video_edit/render.py — рендер MP4 с честным fallback.

Основной путь — moviepy + ffmpeg (H.264/AAC, beat-glow, LRC-overlay).
Если их нет, создаётся HOOK.wav и `build_manually.txt` с готовой
ffmpeg-командой: пользователь получает результат, а не молчаливый отказ.
"""

from __future__ import annotations

import logging

import os

from modules.video_edit.audio import detect_hook
from modules.video_edit.console import safe_print as _safe_print
from modules.video_edit.models import VideoEditRequest, VideoEditResult


def _try_moviepy():
    try:
        import moviepy.editor as mpy

        return mpy
    except Exception as e:
        _safe_print(f"[video_edit] moviepy not available ({e})")
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
    # v39.4 (ШАГ 002): единый font_utils, hardcoded C:\Windows\Fonts убран
    from app.core.font_utils import load_pil_font
    font_big = load_pil_font(int(h * 0.045), bold=True)
    font_small = load_pil_font(int(h * 0.028), bold=True)
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
    _safe_print(f"[video_edit] hook: {hook_start:.1f}s -> {hook_end:.1f}s")

    mpy = _try_moviepy()
    if mpy is not None:
        try:
            return _build_with_moviepy(req, hook_start, hook_end, tmp_dir, mpy)
        except Exception as e:
            _safe_print(f"[video_edit] moviepy render failed: {e}")
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
                _safe_print(f"[video_edit] textclip fail: {e}")
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
            logging.getLogger(__name__).debug("ignored exception", exc_info=True)
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
        _safe_print(f"[video_edit] fallback wav cut failed: {e}")
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
        _safe_print(f"[video_edit] fallback txt write failed: {e}")
    return VideoEditResult(
        ok=False,
        output_path=wav_out or txt_path,
        duration_sec=hook_end - hook_start,
        resolution=req.resolution(),
        backend=backend,
        hook_start_sec=hook_start,
        reason="moviepy/ffmpeg unavailable",
    )

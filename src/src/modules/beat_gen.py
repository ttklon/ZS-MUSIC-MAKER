# -*- coding: utf-8 -*-
"""
[3b] beat_gen.py — MusicGen Texture Engine (пониженная роль)
На RX 580 4GB используется ТОЛЬКО для:
  • атмосферы, этнических фоновых текстур
  • переходных FX, интро/аутро пэдов
  • набросков альтернативного хука
  • мелодических "затравок"
Основной бит делает beat_constructor.py (сэмпл-ориентированный).
"""
import os, math, tempfile, numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "beats")
# v22: ленивое создание (не при импорте)

def _pick_device():
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        try:
            import torch_directml  # noqa
            return "dml"
        except ImportError:
            pass
        return "cpu"
    except ImportError:
        return "cpu"


def _load_model(size: str = "small"):
    from audiocraft.models import MusicGen
    device = _pick_device()
    model_name = {
        "small": "facebook/musicgen-small",
        "melody": "facebook/musicgen-melody",
        "medium": "facebook/musicgen-medium",
    }.get(size, "facebook/musicgen-small")
    model = MusicGen.get_pretrained(model_name, device="cpu" if device == "dml" else device)
    return model, device


def build_prompt(style_vector: dict, user_extra: str = "", samples_desc: str = "") -> str:
    tags = ", ".join(style_vector.get("vibe_tags", []))
    bpm = style_vector.get("target_bpm", 128)
    mode = style_vector.get("target_mode", "minor")
    base = f"{tags}, {bpm} BPM, {mode} key, distorted 808, memphis cowbell, oriental saz melody, aggressive, drift phonk"
    if samples_desc:
        base += f", uses samples: {samples_desc}"
    if user_extra:
        base += f", {user_extra}"
    return base


def generate_texture(prompt: str, duration_sec: int = 15,
                     size: str = "small",
                     out_name: str = "texture.wav") -> str:
    """Генерирует короткую текстуру/FX/пад (для вставки в бит)."""
    from audiocraft.data.audio import audio_write
    import torch

    model, device = _load_model(size)
    model.set_generation_params(duration=duration_sec)
    out = model.generate([prompt], progress=True)
    out_path = os.path.join(OUTPUT_DIR, out_name.replace(".wav", ""))
    audio_write(out_path, out[0].cpu(), model.sample_rate,
                strategy="loudness", loudness_compressor=True)
    return out_path + ".wav"


def generate_beat(prompt: str, duration_sec: int = 90,
                  melody_ref: str = None, size: str = "small",
                  out_name: str = "beat.wav") -> str:
    """Полная генерация через MusicGen с continuation stitching (для мощных GPU)."""
    from audiocraft.data.audio import audio_write
    import torch, torchaudio

    model, device = _load_model(size)
    chunk = 30
    n_chunks = math.ceil(duration_sec / chunk)
    model.set_generation_params(duration=chunk)

    all_wavs = []
    if melody_ref and os.path.exists(melody_ref):
        wav_ref, sr_ref = torchaudio.load(melody_ref)
        wav_ref = wav_ref.mean(dim=0, keepdim=True)
        out = model.generate_with_chroma([prompt], wav_ref[None], sr_ref, progress=True)
    else:
        out = model.generate([prompt], progress=True)
    all_wavs.append(out[0].cpu())

    for i in range(n_chunks - 1):
        prev = all_wavs[-1]
        model.set_generation_params(duration=chunk)
        cont = model.generate_continuation(prev[None], prompt=[prompt],
                                           prompt_sample_rate=model.sample_rate,
                                           progress=True)
        all_wavs.append(cont[0].cpu())

    full = torch.cat(all_wavs, dim=-1)
    out_path = os.path.join(OUTPUT_DIR, out_name.replace(".wav", ""))
    audio_write(out_path, full, model.sample_rate,
                strategy="loudness", loudness_compressor=True)
    return out_path + ".wav"


def generate_from_samples(sample_paths: list, style_vector: dict,
                          duration_sec: int = 90) -> str:
    prompt = build_prompt(style_vector, samples_desc=f"{len(sample_paths)} user samples")
    ref = sample_paths[0] if sample_paths else None
    return generate_beat(prompt, duration_sec=duration_sec, melody_ref=ref,
                         out_name="beat_from_samples.wav")


if __name__ == "__main__":
    demo_style = {"target_bpm": 129, "target_mode": "minor",
                  "vibe_tags": ["phonk/drift", "bass-heavy", "dark", "aggressive"]}
    print(build_prompt(demo_style, user_extra="summer, cars, istanbul"))

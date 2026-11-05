"""Canonical metadata for registered AI roles and resource estimates."""
from typing import Any, Dict

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "lyrics_llm": {
        "role": "Генерация текстов (Qwen2.5-14B GGUF; требуется достаточно памяти)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "sha256": "e47ad95dad6ff848b431053b375adb5d39321290ea2c638682577dafca87c008",
        "expected_size_bytes": 8988110976,
        "context": 8192, "vram_est_gb": 9.5, "ram_est_gb": 12.0, "device_pref": "auto"},
    "analysis_llm": {
        "role": "Досье на артистов/треки (длинный контекст 32k)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "sha256": "e47ad95dad6ff848b431053b375adb5d39321290ea2c638682577dafca87c008",
        "expected_size_bytes": 8988110976,
        "context": 32768, "vram_est_gb": 9.5, "ram_est_gb": 14.0, "device_pref": "auto"},
    "metadata_llm": {
        "role": "Названия/описания/хэштеги (Llama-3.1-8B)",
        "engine": "llama_cpp",
        "hf_repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "file": "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf",
        "sha256": "14e10feba0c82a55da198dcd69d137206ad22d116a809926d27fa5f2398c69c7",
        "expected_size_bytes": 5732992416,
        "context": 8192, "vram_est_gb": 7.0, "ram_est_gb": 10.0, "device_pref": "auto"},
    "music_generation": {
        "role": "Генерация бита (MusicGen-large 3.3B)",
        "engine": "audiocraft_musicgen", "hf_repo": "facebook/musicgen-large",
        "file": "musicgen-large", "vram_est_gb": 11.0, "ram_est_gb": 14.0,
        "device_pref": "cuda", "cpu_fallback": "facebook/musicgen-medium"},
    "music_stereo": {
        "role": "Стерео-текстуры (переходы, интро, пэды)",
        "engine": "audiocraft_musicgen", "hf_repo": "facebook/musicgen-stereo-medium",
        "file": "musicgen-stereo-medium", "vram_est_gb": 8.0, "ram_est_gb": 10.0,
        "device_pref": "auto"},
    "tts_vocal": {
        "role": "Речевой черновик (XTTS-v2; не проверенное пение)",
        "engine": "xtts_v2", "hf_repo": "coqui/XTTS-v2", "file": "XTTS-v2",
        "vram_est_gb": 4.0, "ram_est_gb": 6.0, "device_pref": "cuda"},
    "vocal_rvc": {
        "role": "Voice-conversion собственного/разрешённого голоса (.pth пользователя)",
        "engine": "rvc", "hf_repo": "user_supplied", "file": "data/ai_models/vocal_rvc/*.pth",
        "vram_est_gb": 3.0, "ram_est_gb": 4.0, "device_pref": "cuda"},
    "stem_splitter": {
        "role": "Демиксинг референса (Demucs htdemucs)",
        "engine": "demucs", "hf_repo": "facebook/demucs-htdemucs",
        "file": "htdemucs.th", "vram_est_gb": 6.0, "ram_est_gb": 10.0,
        "device_pref": "cuda"},
    "asr": {
        "role": "Распознавание речи референса (faster-whisper large-v3)",
        "engine": "faster_whisper", "hf_repo": "Systran/faster-whisper-large-v3",
        "file": "faster-whisper-large-v3", "vram_est_gb": 6.0, "ram_est_gb": 8.0,
        "device_pref": "cuda", "cpu_fallback": "Systran/faster-whisper-medium"},
    "audio_tagger": {
        "role": "Автотегирование (CLAP HTSAT-fused)",
        "engine": "clap", "hf_repo": "laion/clap-htsat-fused",
        "file": "clap-htsat-fused", "vram_est_gb": 2.5, "ram_est_gb": 4.0,
        "device_pref": "auto"},
    "essentia": {
        "role": "BPM/key/loudness (librosa DSP)",
        "engine": "essentia_or_librosa", "hf_repo": "", "file": "",
        "vram_est_gb": 0.0, "ram_est_gb": 2.0, "device_pref": "cpu"},
    "cover_art": {
        "role": "Обложка (SDXL Base 1.0 fp16)",
        "engine": "diffusers", "hf_repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "file": "sdxl-base-1.0", "vram_est_gb": 10.0, "ram_est_gb": 8.0,
        "device_pref": "cuda", "cpu_fallback": "stabilityai/sd-turbo"},
    "mastering_ai": {
        "role": "AI-мастеринг (matchering под референс)",
        "engine": "matchering_plus", "hf_repo": "", "file": "",
        "vram_est_gb": 0.0, "ram_est_gb": 4.0, "device_pref": "cpu"},
}

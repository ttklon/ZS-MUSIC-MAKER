"""Voice archive used by the wizard and thin delegation to the RVC manager.

The user's recording is retained on disk even if indexing fails. RVC training
and inference require their own verified backend; no pitch shift is presented
as voice conversion.
"""

import re
import shutil
import uuid
from pathlib import Path

from modules.voice_index_store import VoiceIndexError, lock_index, read_index, write_index

ROOT = Path(__file__).resolve().parents[1]
VAULT_DIR = ROOT / "voice_vault"
MODELS_DIR = ROOT / "models" / "rvc"
OUTPUT_DIR = ROOT / "output" / "voice_final"


def _ensure_dirs():
    """v23 FIX: каталоги создаются лениво (не при импорте модуля).
    Раньше import voice_convert создавал voice_vault/, models/rvc/ и
    output/voice_final/ как побочный эффект — это нарушало политику v22
    «no import side effects» и засоряло диск при простом импорте."""
    for d in (VAULT_DIR, MODELS_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)


VOICE_INDEX = VAULT_DIR / "vault_index.json"

# 33 русских фонем-эквивалента для покрытия
PHONEMES = list("аоуыэеёиюя") + list("бвгджзйклмнпрстфхцчшщъь")

# 8 стилей записи (из ТЗ 3.8)
STYLES = [
    "slow_clear",
    "fast_clear",
    "conversational",
    "aggressive",
    "whisper",
    "raspy",
    "singing",
    "semi_recitative",
]


# ---------- Voice Vault ----------
def _load_index() -> list:
    return read_index(VOICE_INDEX, list, lambda data: isinstance(data, list) and
                      all(isinstance(item, dict) for item in data))


def _save_index(idx: list) -> None:
    write_index(VOICE_INDEX, idx)


def add_recording(wav_path: str, meta: dict) -> dict:
    """Register a take without replacing a damaged index or an existing recording."""
    source = Path(wav_path)
    if not source.is_file():
        return {"error": f"copy failed: source not found: {source}"}
    safe_style = re.sub(r"[^\w-]", "_", str(meta.get("style", "unk")))[:40] or "voice"
    dst = source
    copy_complete = False
    try:
        _ensure_dirs()
        with lock_index(VOICE_INDEX):
            idx = _load_index()
            if source.resolve().parent != VAULT_DIR.resolve():
                dst = VAULT_DIR / f"rec_{uuid.uuid4().hex}_{safe_style}.wav"
                # Exclusive create: do not overwrite pre-existing or concurrent takes.
                with source.open("rb") as src, dst.open("xb") as target:
                    shutil.copyfileobj(src, target)
            else:
                dst = source.resolve()
            copy_complete = True
            entry = {
                "file": dst.name, "path": str(dst), "style": meta.get("style", "unk"),
                "text": meta.get("text", ""), "duration_sec": float(meta.get("duration_sec", 0)),
                "quality_score": meta.get("quality_score"), "timestamp": meta.get("timestamp"),
                "backing_path": str(meta.get("backing_path") or ""),
                "backing_sha256": str(meta.get("backing_sha256") or ""),
            }
            idx.append(entry)
            _save_index(idx)
        return entry
    except (OSError, ValueError, TypeError, VoiceIndexError) as exc:
        failure = {"error": f"voice archive update failed: {type(exc).__name__}: {exc}",
                   "unindexed_path": str(dst) if copy_complete and dst.is_file() else str(source)}
        if not copy_complete and dst != source and dst.is_file():
            failure["partial_copy_path"] = str(dst)
        return failure


def recording_backing(wav_path: str) -> dict:
    """Read known binding without letting duplicate unbound entries erase it."""
    path = Path(wav_path).resolve()
    binding = {}
    for entry in reversed(_load_index()):
        if not entry.get("path") or Path(entry["path"]).resolve() != path:
            continue
        recorded_path = entry.get("backing_path") or ""
        digest = entry.get("backing_sha256") or ""
        if not recorded_path and not digest:
            continue
        if (not isinstance(recorded_path, str) or not recorded_path or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise VoiceIndexError("recording archive has incomplete or invalid backing metadata")
        if binding and binding["sha256"] != digest:
            raise VoiceIndexError("recording archive has conflicting backing metadata")
        if not binding:
            binding = {"path": recorded_path, "sha256": digest}
    return binding


def vault_summary() -> dict:
    """Duration and entered-letter counts; not ASR, phoneme coverage or training proof."""
    idx = _load_index()
    by_style = {}
    total_sec = 0
    for e in idx:
        by_style[e.get("style", "unknown")] = (
            by_style.get(e.get("style", "unknown"), 0) + 1
        )
        total_sec += float(e.get("duration_sec", 0))
    text = " ".join(e.get("text", "") for e in idx).lower()
    covered = [p for p in PHONEMES if p in text]
    missing = [p for p in PHONEMES if p not in text]
    return {
        "recordings": len(idx),
        "total_minutes": round(total_sec / 60, 2),
        "by_style": by_style,
        "minimum_duration_met": total_sec >= 300,
        "duration_kind": "index_metadata_unverified",
        "ready_for_training": False,  # no integrated trainer has been verified
        "training_status": "UNVERIFIED",
        "recommended_for_full": False,  # duration does not establish dataset quality
        "coverage_kind": "entered_letters_not_asr",
        "audio_coverage_verified": False,
        "phoneme_coverage_pct": round(len(covered) / len(PHONEMES) * 100, 1),
        "missing_phonemes": missing,
        "recommended_next_styles": [s for s in STYLES if by_style.get(s, 0) < 3],
    }


def rate_recording(index: int, quality_score: int) -> dict:
    try:
        with lock_index(VOICE_INDEX):
            idx = _load_index()
            if index < 0 or index >= len(idx):
                return {"error": "индекс вне диапазона"}
            idx[index]["quality_score"] = quality_score
            _save_index(idx)
        return {"ok": True, "entry": idx[index]}
    except (OSError, ValueError, TypeError, VoiceIndexError) as exc:
        return {"error": f"voice archive update failed: {type(exc).__name__}: {exc}"}


# ---------- Training (делегируем rvc_manager) ----------
def train_rvc_model(
    voice_name: str = "my_voice", epochs: int = 100, night_mode: bool = False
) -> dict:
    """Запрос обучения RVC; возвращает blocked, пока нет проверенного backend."""
    from modules import rvc_manager

    trainer = rvc_manager.RVCTrainer()
    job = trainer.train(voice_name=voice_name, epochs=epochs, night_mode=night_mode)
    return {
        "ok": job.status not in {"blocked_backend", "error"},
        "job_started": job.status not in {"blocked_backend", "error"},
        "reason": job.error,
        "voice_name": voice_name,
        "backend": trainer.backend.kind,
        "fork": trainer.backend.fork,
        "epochs": job.epochs,
        "device": job.device,
        "note": job.stage,
    }


def incremental_finetune(voice_name: str = "my_voice", added_epochs: int = 20) -> dict:
    """Инкрементальное дообучение по новым записям."""
    return train_rvc_model(voice_name, epochs=added_epochs, night_mode=False)


def get_training_status(voice_name: str = "my_voice") -> dict:
    """Прогресс текущего обучения (для UI)."""
    from modules import rvc_manager

    return rvc_manager.get_state(voice_name)


# ---------- Conversion ----------
def convert(
    input_wav: str,
    voice_name: str = "my_voice",
    pitch_shift: int = 0,
    out_name: str = "converted.wav",
) -> str:
    """RVC-инференс. Основной путь v7."""
    from modules import rvc_manager

    return rvc_manager.infer(
        input_wav, voice_name=voice_name, pitch_shift=pitch_shift, out_name=out_name
    )


def polish_vocal(
    user_vocal_path: str,
    voice_name: str = "my_voice",
    out_name: str = "polished_vocal.wav",
) -> str:
    """
    ProVoice Mode: пользователь сам записал вокал под бит.
    RVC полирует — стабилизирует тембр, добавляет ровности, но сохраняет
    живое дыхание и микро-фальшь пользователя.
    """
    return convert(
        user_vocal_path, voice_name=voice_name, pitch_shift=0, out_name=out_name
    )


def polish_vocal_offline(
    user_vocal_path: str, out_name: str = "polished_offline.wav", n_steps: int = 0
) -> str:
    """
    ⚠ ПОСЛЕДНЯЯ ЛИНИЯ ОБОРОНЫ. Используется ТОЛЬКО когда RVC полностью
    недоступен. НЕ является основным путём в v7.
    """
    from modules import rvc_manager

    _ensure_dirs()
    return rvc_manager._fallback_pitch(
        user_vocal_path, str(OUTPUT_DIR / out_name), n_steps
    )


if __name__ == "__main__":
    print(json.dumps(vault_summary(), indent=2, ensure_ascii=False))

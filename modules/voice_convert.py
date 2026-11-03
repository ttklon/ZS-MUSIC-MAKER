"""
[v7] voice_convert.py — тонкая обёртка над rvc_manager.

Изменения относительно v6:
  • RVC теперь ОСНОВНОЙ путь (см. 20.1 ТЗ).
  • Offline pitch-shift оставлен только как аварийный fallback с WARNING.
  • Тренировку и инференс полностью делегируем rvc_manager.
  • Voice Vault (записи по 8 стилям + phoneme coverage) сохранён.
"""

import json
import re
import shutil
import uuid
from pathlib import Path

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
    if VOICE_INDEX.exists():
        try:
            return json.load(open(VOICE_INDEX, "r", encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_index(idx: list):
    _ensure_dirs()
    json.dump(
        idx, open(VOICE_INDEX, "w", encoding="utf-8"), ensure_ascii=False, indent=2
    )


def add_recording(wav_path: str, meta: dict) -> dict:
    """Добавить запись в Voice Vault."""
    _ensure_dirs()
    idx = _load_index()
    style = meta.get("style", "unk")
    source = Path(wav_path)
    safe_style = re.sub(r"[^\w-]", "_", str(style))[:40] or "voice"
    fname = f"rec_{uuid.uuid4().hex}_{safe_style}.wav"
    dst = VAULT_DIR / fname
    try:
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.resolve().parent == VAULT_DIR.resolve():
            dst = source.resolve()
            fname = dst.name
        else:
            # Never overwrite a pre-existing take, including unindexed recordings.
            with source.open("rb") as src, dst.open("xb") as target:
                shutil.copyfileobj(src, target)
    except Exception as e:
        return {"error": f"copy failed: {e}"}
    entry = {
        "file": fname,
        "path": str(dst),
        "style": style,
        "text": meta.get("text", ""),
        "duration_sec": float(meta.get("duration_sec", 0)),
        "quality_score": meta.get("quality_score"),
        "timestamp": meta.get("timestamp"),
    }
    idx.append(entry)
    _save_index(idx)
    return entry


def vault_summary() -> dict:
    """Сводка по vault: сколько минут, покрытие фонем, рекомендации."""
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
        "ready_for_training": total_sec >= 300,  # 5 минут — минимум
        "recommended_for_full": total_sec >= 600,  # 10 минут — идеал
        "phoneme_coverage_pct": round(len(covered) / len(PHONEMES) * 100, 1),
        "missing_phonemes": missing,
        "recommended_next_styles": [s for s in STYLES if by_style.get(s, 0) < 3],
    }


def rate_recording(index: int, quality_score: int) -> dict:
    idx = _load_index()
    if index < 0 or index >= len(idx):
        return {"error": "индекс вне диапазона"}
    idx[index]["quality_score"] = quality_score
    _save_index(idx)
    return {"ok": True, "entry": idx[index]}


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

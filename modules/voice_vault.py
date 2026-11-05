"""Alternative Voice Vault index for speaker selection and explicit analysis.

This index is distinct from the wizard's archive index; neither is migrated or
deleted automatically. Optional transcription may require external backends.
Index updates preserve damaged or unreadable user data rather than resetting it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import shutil
import time
import uuid
from pathlib import Path

from modules.voice_index_store import VoiceIndexError, lock_index, read_index, write_index

try:
    import numpy as np
except Exception:
    np = None

try:
    import soundfile as sf

    HAS_SF = True
except Exception:
    HAS_SF = False

try:
    HAS_LIBROSA = True
except Exception:
    HAS_LIBROSA = False

ROOT = Path(__file__).resolve().parents[1]
VAULT_DIR = ROOT / "voice_vault"
INDEX_FILE = VAULT_DIR / "index.json"
MANIFEST_FILE = VAULT_DIR / "voice_manifest.json"
LOGGER = logging.getLogger(__name__)
# v22: ленивое создание (не при импорте)

STYLES = (
    "rap",
    "sing",
    "adlib",
    "shout",
    "whisper",
    "melodic",
    "aggressive",
    "deadpan",
)

# Порог для авто-триггера дообучения RVC (в секундах чистого голоса)
RETRAIN_THRESHOLD_SEC = 300.0  # 5 минут


# ============================================================ index
def _load_index() -> dict:
    return read_index(INDEX_FILE, lambda: {"items": {}},
                      lambda data: isinstance(data, dict) and isinstance(data.get("items"), dict)
                      and all(isinstance(item, dict) for item in data["items"].values()))


def _save_index(idx: dict) -> None:
    write_index(INDEX_FILE, idx)


def _content_digest(path: Path) -> str:
    """Hash the entire file; a shared first megabyte must not hide another take."""
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ============================================================ audio quality
def _snr_and_clipping(path: Path) -> dict:
    if not HAS_SF or np is None:
        return {"snr_db": None, "clip_ratio": None, "duration_s": None}
    try:
        y, sr = sf.read(str(path), always_2d=False)
        if hasattr(y, "ndim") and y.ndim > 1:
            y = y.mean(axis=1)
        dur = len(y) / sr
        win = max(1, int(sr * 0.05))
        chunks = [y[i : i + win] for i in range(0, len(y) - win, win)]
        rmss = sorted([float(np.sqrt(np.mean(np.square(c)) + 1e-12)) for c in chunks])
        if len(rmss) < 20:
            return {"snr_db": None, "clip_ratio": None, "duration_s": dur}
        noise = float(np.mean(rmss[: max(1, len(rmss) // 20)]))
        signal = float(np.mean(rmss[-max(1, len(rmss) // 5) :]))
        snr = 20 * math.log10(max(signal, 1e-9) / max(noise, 1e-9))
        clip = float(np.mean(np.abs(y) > 0.98))
        return {
            "snr_db": round(snr, 2),
            "clip_ratio": round(clip, 5),
            "duration_s": round(dur, 2),
        }
    except Exception as e:
        return {"snr_db": None, "clip_ratio": None, "duration_s": None, "err": str(e)}


def _guess_style(features: dict, hint: str | None = None) -> str:
    if hint and hint in STYLES:
        return hint
    dur = features.get("duration_s") or 0.0
    if dur < 2.0:
        return "adlib"
    return "rap"  # безопасный дефолт


# ============================================================ transcript
def _transcribe_with_diagnostics(path: Path) -> tuple[str | None, dict]:
    """Пробует доступные Whisper backends и сохраняет причину отсутствия текста."""
    attempts: list[dict[str, str | bool]] = []
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(path))
        text = " ".join(segment.text.strip() for segment in segments)[:500]
        return text, {"ok": True, "engine": "faster_whisper", "attempts": attempts}
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("faster_whisper transcription unavailable for %s: %s", path, error)
        attempts.append({"engine": "faster_whisper", "ok": False, "error": error})
    try:
        import whisper

        model = whisper.load_model("tiny")
        text = (model.transcribe(str(path)).get("text") or "")[:500]
        return text, {"ok": True, "engine": "whisper", "attempts": attempts}
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("whisper transcription unavailable for %s: %s", path, error)
        attempts.append({"engine": "whisper", "ok": False, "error": error})
    return None, {"ok": False, "engine": None, "attempts": attempts}


def _transcribe(path: Path) -> str | None:
    """Совместимый text-only API для транскрипции записи."""
    return _transcribe_with_diagnostics(path)[0]


def calculate_phoneme_coverage(text: str) -> dict:
    """Считает покрытие алфавита (русский + английский)."""
    if not text:
        return {}
    text = text.lower()
    ru = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    en = "abcdefghijklmnopqrstuvwxyz"

    found_ru = [c for c in ru if c in text]
    found_en = [c for c in en if c in text]

    return {
        "ru_count": len(found_ru),
        "ru_total": len(ru),
        "ru_percent": round(len(found_ru) / len(ru) * 100, 1),
        "en_count": len(found_en),
        "en_total": len(en),
        "en_percent": round(len(found_en) / len(en) * 100, 1),
        "found": "".join(sorted(set(found_ru + found_en))),
    }


# ============================================================ main API
def add_recording(
    src_path: str,
    style_hint: str | None = None,
    transcribe: bool = False,
    overwrite: bool = False,
) -> dict:
    p = Path(src_path)
    if not p.is_file():
        return {"ok": False, "error": f"not found: {src_path}"}
    dst = p
    copy_verified = False
    try:
        digest = _content_digest(p)
        mid = digest
        VAULT_DIR.mkdir(parents=True, exist_ok=True)
        with lock_index(INDEX_FILE):
            idx = _load_index()
            items = idx["items"]
            if mid in items and not overwrite:
                return {"ok": True, "already_indexed": True, "item": items[mid]}
            # Earlier versions keyed by MD5 of only the first MiB. Confirm the
            # entire old file before treating that legacy entry as a duplicate.
            with p.open("rb") as source:
                legacy_id = hashlib.md5(source.read(1024 * 1024)).hexdigest()
            legacy = items.get(legacy_id)
            if isinstance(legacy, dict) and legacy.get("vault_path"):
                old_path = Path(legacy["vault_path"])
                if old_path.is_file() and _content_digest(old_path) == digest:
                    if not overwrite:
                        return {"ok": True, "already_indexed": True, "item": legacy}
                    mid = legacy_id
            previous = items.get(mid) or {}
            dst = VAULT_DIR / f"{mid[:12]}_{p.name}"
            if dst.exists() and _content_digest(dst) != digest:
                dst = VAULT_DIR / f"{mid[:12]}_{uuid.uuid4().hex}_{p.name}"
            if not dst.exists():
                # Exclusive create prevents replacing any unindexed take.
                with p.open("rb") as source, dst.open("xb") as target:
                    shutil.copyfileobj(source, target)
            if _content_digest(dst) != digest:
                raise VoiceIndexError("source changed during copy; unindexed copy preserved")
            copy_verified = True
            feats = _snr_and_clipping(dst)
            style = _guess_style(feats, style_hint)
            if transcribe:
                transcript, transcription = _transcribe_with_diagnostics(dst)
            else:
                transcript = None
                transcription = {"ok": False, "engine": None, "status": "not_requested"}
            coverage = calculate_phoneme_coverage(transcript) if transcript else {}
            entry = {
                "id": mid, "src_name": p.name, "vault_path": str(dst), "size": dst.stat().st_size,
                "style": style, "features": feats, "transcript": transcript,
                "transcription": transcription, "coverage": coverage,
                "added_at": previous.get("added_at", time.time()),
                "used_in_rvc_rounds": previous.get("used_in_rvc_rounds", []),
            }
            items[mid] = entry
            _save_index(idx)
        return {"ok": True, "already_indexed": False, "item": entry}
    except (OSError, ValueError, TypeError, VoiceIndexError) as exc:
        failure = {"ok": False, "error": f"voice archive update failed: {type(exc).__name__}: {exc}",
                   "unindexed_path": str(dst) if copy_verified and dst.is_file() else str(p)}
        if not copy_verified and dst != p and dst.is_file():
            failure["partial_copy_path"] = str(dst)
        return failure


def list_recordings(style: str | None = None) -> list[dict]:
    idx = _load_index()
    items = list(idx.get("items", {}).values())
    if style:
        items = [x for x in items if x.get("style") == style]
    return items


def select_speaker_wav(style: str | None = None) -> str | None:
    """Выбрать лучший существующий clean Voice Vault clip для XTTS speaker conditioning."""
    candidates = []
    for item in list_recordings(style=style):
        features = item.get("features") or {}
        path = Path(item.get("vault_path") or "")
        if not path.is_file():
            continue
        snr = features.get("snr_db")
        clipping = features.get("clip_ratio")
        if clipping is not None and clipping >= 0.01:
            continue
        candidates.append((float(snr) if snr is not None else 15.0, item.get("added_at", 0.0), path))
    if not candidates and style:
        return select_speaker_wav(style=None)
    return str(max(candidates)[2]) if candidates else None


def clean_stats() -> dict:
    idx = _load_index()
    items = list(idx.get("items", {}).values())
    total_sec = 0.0
    good_sec = 0.0
    by_style = {}
    all_text = ""
    for x in items:
        dur = (x.get("features") or {}).get("duration_s") or 0.0
        snr = (x.get("features") or {}).get("snr_db") or 0.0
        clip = (x.get("features") or {}).get("clip_ratio") or 0.0
        total_sec += dur
        if (snr is None or snr >= 15.0) and (clip is None or clip < 0.01):
            good_sec += dur
        st = x.get("style") or "unknown"
        by_style[st] = by_style.get(st, 0.0) + dur
        if x.get("transcript"):
            all_text += x["transcript"] + " "

    coverage = calculate_phoneme_coverage(all_text)

    return {
        "n_items": len(items),
        "total_sec": round(total_sec, 2),
        "good_sec": round(good_sec, 2),
        "by_style": {k: round(v, 2) for k, v in by_style.items()},
        "coverage": coverage,
        "ready_for_retrain": good_sec >= RETRAIN_THRESHOLD_SEC,
        "threshold_sec": RETRAIN_THRESHOLD_SEC,
    }


def export_manifest_for_rvc(out_path: str | None = None) -> str:
    idx = _load_index()
    good = []
    for x in idx.get("items", {}).values():
        f = x.get("features") or {}
        snr = f.get("snr_db")
        clip = f.get("clip_ratio")
        if (snr is None or snr >= 15.0) and (clip is None or clip < 0.01):
            good.append(
                {
                    "id": x["id"],
                    "path": x["vault_path"],
                    "style": x.get("style"),
                    "duration_s": f.get("duration_s"),
                    "snr_db": snr,
                }
            )
    payload = {
        "ts": time.time(),
        "n_items": len(good),
        "total_sec": round(sum(x.get("duration_s") or 0 for x in good), 2),
        "items": good,
    }
    dst = Path(out_path) if out_path else MANIFEST_FILE
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(dst)


def maybe_trigger_retrain(rvc_trainer=None) -> dict:
    stats = clean_stats()
    if not stats["ready_for_retrain"]:
        return {"triggered": False, "reason": "not enough clean voice", "stats": stats}
    manifest = export_manifest_for_rvc()
    if rvc_trainer is None:
        try:
            from modules import rvc_trainer as rvc_trainer
        except Exception as e:
            return {
                "triggered": False,
                "reason": f"rvc_trainer unavailable: {e}",
                "manifest": manifest,
                "stats": stats,
            }
    try:
        job = rvc_trainer.retrain_incremental(manifest_path=manifest)
        return {"triggered": True, "manifest": manifest, "stats": stats, "job": job}
    except Exception as e:
        return {
            "triggered": False,
            "reason": str(e),
            "manifest": manifest,
            "stats": stats,
        }


# ============================================================ CLI
if __name__ == "__main__":
    print(json.dumps(clean_stats(), ensure_ascii=False, indent=2))

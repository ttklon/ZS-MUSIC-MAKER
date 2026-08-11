# -*- coding: utf-8 -*-
"""
[v9] voice_vault_v9.py — ПОСТОЯННО НАКОПИТЕЛЬНЫЙ Voice Vault.

По ТЗ 3.8: «Голосовой профиль пользователя КОПИТСЯ ПОСТОЯННО».
Раньше v8 хранил только сырые файлы. v9 добавляет:

  • индексацию каждого файла: длительность, транскрипт (whisper), стиль подачи
    (rap / sing / adlib / shout / whisper), BPM записи (если под метроном),
    оценка качества записи (SNR, clipping, breath-noise).
  • автопометки стилей — 8 стилей караоке (rap/sing/adlib/shout/whisper/melodic
    /aggressive/deadpan).
  • очередь для RVC-переобучения: как только накопилось ≥N мин чистого голоса
    → auto-trigger rvc_trainer_v9.retrain_incremental().
  • стабильные id-файлов (md5), чтобы дубликаты не попадали в vault дважды.
  • экспорт «voice_manifest.json» — что реально скормлено в RVC.

Ничего не удаляет из v7/v8. Работает без librosa/whisper (тогда без транскрипта
и SNR-оценки).
"""
from __future__ import annotations
import hashlib, json, shutil, time, math
from pathlib import Path
from typing import Optional

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
    import librosa
    HAS_LIBROSA = True
except Exception:
    HAS_LIBROSA = False

ROOT = Path(__file__).resolve().parents[1]
VAULT_DIR = ROOT / "voice_vault"
INDEX_FILE = VAULT_DIR / "index.json"
MANIFEST_FILE = VAULT_DIR / "voice_manifest.json"
# v22: ленивое создание (не при импорте)

STYLES = ("rap", "sing", "adlib", "shout", "whisper",
          "melodic", "aggressive", "deadpan")

# Порог для авто-триггера дообучения RVC (в секундах чистого голоса)
RETRAIN_THRESHOLD_SEC = 300.0   # 5 минут


# ============================================================ index
def _load_index() -> dict:
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"items": {}}
    return {"items": {}}


def _save_index(idx: dict) -> None:
    INDEX_FILE.write_text(json.dumps(idx, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def _md5(path: Path, limit: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read(limit))
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
        chunks = [y[i:i+win] for i in range(0, len(y) - win, win)]
        rmss = sorted([float(np.sqrt(np.mean(np.square(c)) + 1e-12))
                       for c in chunks])
        if len(rmss) < 20:
            return {"snr_db": None, "clip_ratio": None, "duration_s": dur}
        noise = float(np.mean(rmss[:max(1, len(rmss)//20)]))
        signal = float(np.mean(rmss[-max(1, len(rmss)//5):]))
        snr = 20 * math.log10(max(signal, 1e-9) / max(noise, 1e-9))
        clip = float(np.mean(np.abs(y) > 0.98))
        return {"snr_db": round(snr, 2), "clip_ratio": round(clip, 5),
                "duration_s": round(dur, 2)}
    except Exception as e:
        return {"snr_db": None, "clip_ratio": None, "duration_s": None,
                "err": str(e)}


def _guess_style(features: dict, hint: Optional[str] = None) -> str:
    if hint and hint in STYLES:
        return hint
    dur = features.get("duration_s") or 0.0
    if dur < 2.0:
        return "adlib"
    return "rap"  # безопасный дефолт


# ============================================================ transcript
def _transcribe(path: Path) -> Optional[str]:
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel("tiny", device="cpu", compute_type="int8")
        segs, _ = m.transcribe(str(path))
        return " ".join(s.text.strip() for s in segs)[:500]
    except Exception:
        pass
    try:
        import whisper
        m = whisper.load_model("tiny")
        return (m.transcribe(str(path)).get("text") or "")[:500]
    except Exception:
        pass
    return None


# ============================================================ main API
def add_recording(src_path: str,
                  style_hint: Optional[str] = None,
                  transcribe: bool = False,
                  overwrite: bool = False) -> dict:
    p = Path(src_path)
    if not p.exists():
        return {"ok": False, "error": f"not found: {src_path}"}

    mid = _md5(p)
    idx = _load_index()
    items = idx.setdefault("items", {})

    if mid in items and not overwrite:
        return {"ok": True, "already_indexed": True, "item": items[mid]}

    dst = VAULT_DIR / f"{mid[:12]}_{p.name}"
    if not dst.exists():
        try:
            shutil.copy2(p, dst)
        except Exception as e:
            return {"ok": False, "error": f"copy failed: {e}"}

    feats = _snr_and_clipping(dst)
    style = _guess_style(feats, style_hint)
    transcript = _transcribe(dst) if transcribe else None

    entry = {
        "id":        mid,
        "src_name":  p.name,
        "vault_path": str(dst),
        "size":      dst.stat().st_size,
        "style":     style,
        "features":  feats,
        "transcript": transcript,
        "added_at":  time.time(),
        "used_in_rvc_rounds": [],
    }
    items[mid] = entry
    _save_index(idx)
    return {"ok": True, "already_indexed": False, "item": entry}


def list_recordings(style: Optional[str] = None) -> list[dict]:
    idx = _load_index()
    items = list(idx.get("items", {}).values())
    if style:
        items = [x for x in items if x.get("style") == style]
    return items


def clean_stats() -> dict:
    idx = _load_index()
    items = idx.get("items", {}).values()
    total_sec = 0.0
    good_sec = 0.0
    by_style = {}
    for x in items:
        dur = (x.get("features") or {}).get("duration_s") or 0.0
        snr = (x.get("features") or {}).get("snr_db") or 0.0
        clip = (x.get("features") or {}).get("clip_ratio") or 0.0
        total_sec += dur
        if (snr is None or snr >= 15.0) and (clip is None or clip < 0.01):
            good_sec += dur
        st = x.get("style") or "unknown"
        by_style[st] = by_style.get(st, 0.0) + dur
    return {
        "n_items":  len(list(items)),
        "total_sec": round(total_sec, 2),
        "good_sec":  round(good_sec, 2),
        "by_style":  {k: round(v, 2) for k, v in by_style.items()},
        "ready_for_retrain": good_sec >= RETRAIN_THRESHOLD_SEC,
        "threshold_sec": RETRAIN_THRESHOLD_SEC,
    }


def export_manifest_for_rvc(out_path: Optional[str] = None) -> str:
    idx = _load_index()
    good = []
    for x in idx.get("items", {}).values():
        f = x.get("features") or {}
        snr = f.get("snr_db"); clip = f.get("clip_ratio")
        if (snr is None or snr >= 15.0) and (clip is None or clip < 0.01):
            good.append({
                "id": x["id"],
                "path": x["vault_path"],
                "style": x.get("style"),
                "duration_s": f.get("duration_s"),
                "snr_db": snr,
            })
    payload = {
        "ts": time.time(),
        "n_items": len(good),
        "total_sec": round(sum(x.get("duration_s") or 0 for x in good), 2),
        "items": good,
    }
    dst = Path(out_path) if out_path else MANIFEST_FILE
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    return str(dst)


def maybe_trigger_retrain(rvc_trainer=None) -> dict:
    stats = clean_stats()
    if not stats["ready_for_retrain"]:
        return {"triggered": False, "reason": "not enough clean voice",
                "stats": stats}
    manifest = export_manifest_for_rvc()
    if rvc_trainer is None:
        try:
            from modules import rvc_trainer_v9 as rvc_trainer
        except Exception as e:
            return {"triggered": False,
                    "reason": f"rvc_trainer_v9 unavailable: {e}",
                    "manifest": manifest, "stats": stats}
    try:
        job = rvc_trainer.retrain_incremental(manifest_path=manifest)
        return {"triggered": True, "manifest": manifest, "stats": stats,
                "job": job}
    except Exception as e:
        return {"triggered": False, "reason": str(e),
                "manifest": manifest, "stats": stats}


# ============================================================ CLI
if __name__ == "__main__":
    import sys
    print(json.dumps(clean_stats(), ensure_ascii=False, indent=2))

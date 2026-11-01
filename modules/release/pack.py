# -*- coding: utf-8 -*-
"""
modules/release/pack.py — полный релизный пакет из результата пайплайна.

Собирает мастер (+ варианты стендов), стемы, тексты (txt/lrc/srt), метаданные,
пакеты площадок, отчёт хит-метрик, манифест с SHA-256 и ZIP. Всё, что не
удалось сделать, честно попадает в `missing`/`warnings` — «тихий успех»
запрещён.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from modules.release.channels import build_all_channels
from modules.release.export import export_release, refresh_zip, sha256_file


def _lyrics_to_lrc(lyrics_text: str, total_sec: float) -> str:
    """LRC по строкам: строки раскладываются ровно по длительности трека."""
    lines = [line.strip() for line in (lyrics_text or "").splitlines() if line.strip()]
    if not lines:
        return ""
    step = max(1.0, float(total_sec or 0) / len(lines)) if total_sec else 4.0
    out = []
    for index, line in enumerate(lines):
        seconds = index * step
        out.append(f"[{int(seconds // 60):02d}:{seconds % 60:05.2f}]{line}")
    return "\n".join(out) + "\n"


def _lyrics_to_srt(lyrics_text: str, total_sec: float) -> str:
    lines = [line.strip() for line in (lyrics_text or "").splitlines() if line.strip()]
    if not lines:
        return ""
    step = max(1.0, float(total_sec or 0) / len(lines)) if total_sec else 4.0

    def stamp(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    blocks = []
    for index, line in enumerate(lines):
        start = index * step
        blocks.append(f"{index + 1}\n{stamp(start)} --> {stamp(start + step)}\n{line}\n")
    return "\n".join(blocks)


def _copy_masters(masters_map: dict[str, str] | None, out: Path) -> list[str]:
    """Копирует мастер-стенды в пакет; отсутствующие просто не выдумываются."""
    files: list[str] = []
    for name, source in (masters_map or {}).items():
        if not source or not Path(source).is_file():
            continue
        destination = out / "masters" / f"{name}.wav"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if Path(source).resolve() != destination.resolve():
            shutil.copy(source, destination)
        files.append(str(destination))
    return files


def _copy_stems(stems_map: dict[str, str] | None, out: Path) -> list[str]:
    files: list[str] = []
    for name, source in (stems_map or {}).items():
        if not source or not Path(source).is_file():
            continue
        destination = out / "stems" / f"{name}.wav"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if Path(source).resolve() != destination.resolve():
            shutil.copy(source, destination)
        files.append(str(destination))
    return files


def _hit_report(meta: dict[str, Any], hit_metrics: dict[str, Any] | None) -> str:
    metrics = hit_metrics or {}
    lines = [
        f"# Hit Report — {meta.get('title') or 'Untitled'}",
        "",
        f"- Score: {metrics.get('hit_score', meta.get('hit_score', 'n/a'))}",
        f"- Verdict: {metrics.get('verdict', meta.get('verdict', 'n/a'))}",
    ]
    for key in ("hook_strength", "mix_balance", "loudness", "originality"):
        if key in metrics:
            lines.append(f"- {key}: {metrics[key]}")
    lines.append("")
    return "\n".join(lines)


def build_pack(
    master_wav: str,
    out_dir: str,
    meta: dict[str, Any] | None = None,
    masters_map: dict[str, str] | None = None,
    stems_map: dict[str, str] | None = None,
    lyrics_text: str = "",
    stages: Any = None,
    hit_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Собирает полный релизный пакет; путь к мастеру обязателен."""
    meta = dict(meta or {})
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    missing: list[str] = []

    if not master_wav or not Path(master_wav).is_file():
        return {
            "ok": False,
            "engine": "modules.release.pack",
            "reason": f"master not found: {master_wav!r}",
        }

    meta.setdefault("title", Path(master_wav).stem)
    meta.setdefault("artist", "ZS Music Maker")
    meta.setdefault("lyrics_text", lyrics_text)

    duration = meta.get("duration_sec") or 0.0
    files: dict[str, str] = {}

    masters = _copy_masters(masters_map, out)
    if masters_map and not masters:
        missing.append("masters")
    stems = _copy_stems(stems_map, out)
    if stems_map and not stems:
        missing.append("stems")

    extra_artifacts: list[Path] = []
    if lyrics_text.strip():
        lrc_path = out / "lyrics.lrc"
        lrc_path.write_text(_lyrics_to_lrc(lyrics_text, float(duration)), encoding="utf-8")
        files["lyrics.lrc"] = str(lrc_path)
        srt_path = out / "lyrics.srt"
        srt_path.write_text(_lyrics_to_srt(lyrics_text, float(duration)), encoding="utf-8")
        files["lyrics.srt"] = str(srt_path)
        extra_artifacts += [lrc_path, srt_path]
    else:
        missing.append("lyrics")

    hit_path = out / "hit_report.md"
    hit_path.write_text(_hit_report(meta, hit_metrics), encoding="utf-8")
    files["hit_report.md"] = str(hit_path)
    extra_artifacts.append(hit_path)

    channels = build_all_channels(meta, out / "channels")
    if channels.get("failed"):
        warnings.append(f"channel packages failed: {channels['failed']}")

    exported = export_release(
        beat_path=str(meta.get("beat_path") or ""),
        vocal_path=str(meta.get("vocal_path") or ""),
        master_path=master_wav,
        lyrics=lyrics_text,
        recipe=dict(meta),
        project_name=str(meta.get("project") or meta.get("title") or "release"),
        artist_name=str(meta.get("artist") or ""),
        title=str(meta.get("title") or ""),
        out_dir=out,
    )
    if not exported.get("ok"):
        return {
            "ok": False,
            "engine": "modules.release.pack",
            "reason": exported.get("reason", "export failed"),
        }

    manifest_path = Path(exported["files"]["manifest.json"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = dict(manifest.get("artifacts_sha256") or {})
    for path in masters + stems + channels.get("files", []) + [str(p) for p in extra_artifacts]:
        file_path = Path(path)
        if file_path.is_file():
            artifacts[file_path.name] = sha256_file(file_path)
    manifest["artifacts_sha256"] = artifacts
    manifest["masters"] = masters
    manifest["stems"] = stems
    manifest["channels"] = channels.get("channels")
    manifest["stages"] = _stage_summary(stages)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )

    # Манифест обновлён — пересобираем ZIP, чтобы архив совпадал с папкой релиза.
    zip_ok = refresh_zip(out)
    if not zip_ok:
        warnings.append("release.zip could not be rebuilt after the manifest update")
    exported["files"]["release.zip"] = str(out / "release.zip")

    all_files = sorted(set(list(exported["files"].values()) + masters + stems))
    return {
        "ok": True,
        "engine": "modules.release.pack",
        "path": str(out),
        "release_dir": str(out),
        "files": all_files,
        "n_files": len(all_files),
        "master": str(Path(master_wav)),
        "isrc": exported.get("isrc", ""),
        "isrc_status": exported.get("isrc_status", "UNREGISTERED"),
        "masters": masters,
        "stems": stems,
        "channels": channels,
        "manifest": manifest,
        "missing": missing,
        "warnings": warnings,
        "fallback_used": False,
    }


def _stage_summary(stages: Any) -> dict[str, Any] | None:
    """Короткая сводка стадий пайплайна для манифеста (если передана)."""
    if stages is None:
        return None
    try:
        summary: dict[str, Any] = {}
        for stage in stages:
            name = getattr(stage, "name", None) or (stage.get("name") if isinstance(stage, dict) else None)
            status = getattr(stage, "status", None) or (stage.get("status") if isinstance(stage, dict) else None)
            if name:
                summary[str(name)] = getattr(status, "value", status)
        return summary
    except Exception:
        return None


def capability_report() -> dict[str, Any]:
    return {"engine": "modules.release.pack", "channels": 5, "zip": True, "sha256": True}

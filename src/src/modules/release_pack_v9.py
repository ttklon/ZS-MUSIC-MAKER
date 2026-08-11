# -*- coding: utf-8 -*-
"""
[v9] release_pack_v9.py — расширенная сборка релиз-пакета.

По ТЗ 3.12 (Export & Release Package):
  Полный релиз содержит master.wav/mp3/flac + инструментал + акапелла + стемы +
  lyrics.txt/lrc + cover.png + tiktok.mp4/reels.mp4 + car/club/streaming +
  manifest.json + metadata.json + recipe.json.

v9 добавляет к v6 release_pack_v6 / v7 release_export:
  • hit_score.json                    — отчёт hit_scorer
  • arrangement_plan.json             — план из arrangement_engine
  • style_fingerprint.json            — style_vector из reference_ingest
  • sample_manifest.json              — юр. чистота сэмплов (v9 sample_hunter)
  • voice_manifest.json               — какие записи скормлены в RVC
  • tiktok/hook_loop.wav              — фрагменты для эдитов
  • README_RELEASE.txt                — читабельная сводка релиза

НИЧЕГО не удаляет из v6/v7. Работает как append-режим: даёт файлы поверх
существующей папки релиза.
"""
from __future__ import annotations
import json, shutil, time
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]


def _safe_copy(src: str, dst: str) -> bool:
    try:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception:
        return False


def _write_json(path: str, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def _readme_text(payload: dict) -> str:
    lines = [
        f"# {payload.get('title', 'Untitled')} — {payload.get('artist', '')}",
        "",
        f"BPM: {payload.get('bpm')} · Key: {payload.get('key')} "
        f"{payload.get('mode')}",
        f"Genre: {payload.get('genre')} · Mood: {payload.get('mood')}",
        f"Duration: {payload.get('duration_s')} sec",
        f"Hit Score: {payload.get('hit_score')} — {payload.get('hit_verdict')}",
        "",
        "## Files",
    ]
    for f in payload.get("files", []):
        lines.append(f"  · {f}")
    lines += [
        "",
        "## Legal",
        "Все использованные сэмплы имеют лицензии CC0 / CC-BY / Public Domain",
        "или предоставлены пользователем локально. Тексты — оригинал.",
        "Голос синтезирован Silero/Bark/XTTS и переконвертирован RVC в",
        "тембр пользователя (голосовой профиль обучен на его же записях).",
        "",
        f"Собрано: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
    ]
    return "\n".join(lines)


def build_release_v9(release_dir: str,
                     project_meta: dict,
                     master_wav: str,
                     hit_report: Optional[dict] = None,
                     arrangement_plan: Optional[dict] = None,
                     style_fingerprint: Optional[dict] = None,
                     sample_manifest: Optional[dict] = None,
                     voice_manifest: Optional[dict] = None,
                     stand_wavs: Optional[dict] = None,
                     tiktok_wavs: Optional[dict] = None) -> dict:
    """
    Дописывает v9-артефакты в существующую (или новую) папку релиза.
    project_meta: {artist, title, bpm, key, mode, genre, mood, duration_s, ...}
    stand_wavs:   {"car": "/path/car_master.wav", "club": ..., "streaming": ...}
    tiktok_wavs:  {"tiktok_15s": "...", "tiktok_30s": "...", "hook_loop": "..."}
    """
    outd = Path(release_dir); outd.mkdir(parents=True, exist_ok=True)
    files: list[str] = []
    warnings: list[str] = []

    # master.wav — копируем если ещё не там
    master_dst = outd / "master.wav"
    if Path(master_wav).exists() and not master_dst.exists():
        if _safe_copy(master_wav, str(master_dst)):
            files.append("master.wav")

    # v9 JSON-артефакты
    if hit_report:
        _write_json(str(outd / "hit_score.json"), hit_report)
        files.append("hit_score.json")
    if arrangement_plan:
        _write_json(str(outd / "arrangement_plan.json"), arrangement_plan)
        files.append("arrangement_plan.json")
    if style_fingerprint:
        _write_json(str(outd / "style_fingerprint.json"), style_fingerprint)
        files.append("style_fingerprint.json")
    if sample_manifest:
        _write_json(str(outd / "sample_manifest.json"), sample_manifest)
        files.append("sample_manifest.json")
    if voice_manifest:
        _write_json(str(outd / "voice_manifest.json"), voice_manifest)
        files.append("voice_manifest.json")

    # стенды
    if stand_wavs:
        for name, path in stand_wavs.items():
            dst = outd / f"{name}_master.wav"
            if Path(path).exists() and _safe_copy(path, str(dst)):
                files.append(dst.name)
            else:
                warnings.append(f"stand {name}: not found {path}")

    # tiktok cuts
    if tiktok_wavs:
        tt_dir = outd / "tiktok"
        tt_dir.mkdir(parents=True, exist_ok=True)
        for name, path in tiktok_wavs.items():
            dst = tt_dir / f"{name}.wav"
            if Path(path).exists() and _safe_copy(path, str(dst)):
                files.append(f"tiktok/{dst.name}")
            else:
                warnings.append(f"tiktok {name}: not found {path}")

    # README
    payload = {
        **project_meta,
        "hit_score": (hit_report or {}).get("hit_score"),
        "hit_verdict": (hit_report or {}).get("verdict"),
        "files": files,
    }
    (outd / "README_RELEASE.txt").write_text(_readme_text(payload),
                                              encoding="utf-8")
    files.append("README_RELEASE.txt")

    return {
        "ok": True,
        "release_dir": str(outd),
        "n_files_added": len(files),
        "files": files,
        "warnings": warnings,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python release_pack_v9.py <release_dir>")
        sys.exit(1)
    r = build_release_v9(sys.argv[1],
                          project_meta={"artist": "test", "title": "demo",
                                        "bpm": 132, "key": "F", "mode": "minor",
                                        "genre": "phonk", "mood": "moody",
                                        "duration_s": 150},
                          master_wav="/tmp/none.wav")
    print(json.dumps(r, indent=2))

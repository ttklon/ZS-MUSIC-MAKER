# -*- coding: utf-8 -*-
"""
modules.hit_factory.release — автопубликация лучшего хита.

Берёт лучший хит из hits_kpi, копирует его release/ в output/releases/<id>/
и готовит манифест для ручной загрузки на дистрибьютора.

Использование:
    python -m modules.hit_factory.release
    python -m modules.hit_factory.release --id hit_phonk_20261114_094153_0e7cbb
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def best_hit_id(output_root: str | Path = "output/hits") -> str | None:
    kpi_path = Path(output_root) / "hits_kpi.json"
    if not kpi_path.exists():
        return None
    try:
        data = json.loads(kpi_path.read_text(encoding="utf-8"))
        best = data.get("best")
        if best and best.get("project_id"):
            return best["project_id"]
    except Exception:
        pass
    return None

def publish(project_id: str | None = None, output_root: str | Path = "output/hits", releases_root: str | Path = "output/releases") -> dict:
    output_root = Path(output_root)
    releases_root = Path(releases_root)
    if project_id is None:
        project_id = best_hit_id(output_root)
        if not project_id:
            return {"ok": False, "reason": "no best hit — run hitmaker first"}
    src = output_root / project_id
    if not src.exists():
        return {"ok": False, "reason": f"hit not found: {src}"}
    dst = releases_root / project_id
    if dst.exists():
        shutil.rmtree(dst)
    # копируем ключевые артефакты
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("masters", "tiktok", "cover.png", "report.json", "hit_report.json", "factory_summary.json"):
        s = src / name
        d = dst / name
        if s.exists():
            if s.is_dir():
                shutil.copytree(s, d)
            else:
                shutil.copyfile(s, d)
    # release пакет если есть
    rel = src / "release"
    if rel.exists():
        shutil.copytree(rel, dst / "release", dirs_exist_ok=True)
    # манифест публикации
    manifest = {
        "project_id": project_id,
        "src": str(src),
        "dst": str(dst),
        "files": [str(p.relative_to(dst)) for p in dst.rglob("*") if p.is_file()],
        "note": "Проверь лицензию, ISRC, таймкоды и права перед загрузкой к дистрибьютору. output/releases — не автозалив.",
    }
    (dst / "publish_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "project_id": project_id, "dst": str(dst), "files": len(manifest["files"]), "manifest": str(dst / "publish_manifest.json")}

def _cli() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Автопубликация лучшего хита в output/releases/")
    p.add_argument("--id", type=str, default="", help="project_id (пусто=лучший из KPI)")
    p.add_argument("--output", type=str, default="output/hits", help="корень хитов")
    p.add_argument("--releases", type=str, default="output/releases", help="куда публиковать")
    args = p.parse_args()
    res = publish(project_id=args.id or None, output_root=args.output, releases_root=args.releases)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(_cli())

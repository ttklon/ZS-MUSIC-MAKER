# -*- coding: utf-8 -*-
"""
tools/blind_listening_prep.py — подготовка набора для слепого прослушивания.

Берёт N хитов из output/hits/ + N референсов (опц.) и готовит папку
output/blind_test/ со случайным переименованием и ключом.

Использование:
    python tools/blind_listening_prep.py --hits 5 --refs data/reference_cache
    python tools/blind_listening_prep.py --hits 5  # только хиты vs хиты (для отладки)
    # затем слушай по docs/BLIND_LISTENING.md и заполни docs/BLIND_LISTENING_RESULT.md
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def prep(hits: int = 5, refs_dir: str | None = None, seed: int = 42, out_dir: str = "output/blind_test") -> dict:
    rng = random.Random(seed)
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    # собираем хиты
    hit_files = []
    for p in sorted((ROOT / "output" / "hits").glob("hit_*/masters/master_streaming.wav")):
        hit_files.append(p)
    # берём самые свежие с highest hit_score
    # сортируем по hit_score если есть
    scored = []
    for f in hit_files:
        try:
            hr = f.parents[1] / "hit_report.json"
            score = 0
            if hr.exists():
                score = json.loads(hr.read_text(encoding="utf-8")).get("hit_score", 0)
            scored.append((score, f))
        except Exception:
            scored.append((0, f))
    scored.sort(key=lambda x: -x[0])
    chosen_hits = [p for _, p in scored[:hits]]
    if len(chosen_hits) < hits:
        # добираем рандомом
        remaining = [p for p in hit_files if p not in chosen_hits]
        rng.shuffle(remaining)
        chosen_hits += remaining[:hits - len(chosen_hits)]

    # референсы
    ref_files = []
    if refs_dir:
        rp = Path(refs_dir)
        if rp.exists():
            for ext in ("*.wav", "*.mp3", "*.flac"):
                ref_files.extend(list(rp.glob(ext)))
                ref_files.extend(list(rp.glob(f"**/{ext}")))
            ref_files = ref_files[:hits]

    # если референсов нет — делаем копии хитов с пометкой reference (для теста протокола)
    items = []  # list of (src, is_hit, hit_id)
    for p in chosen_hits:
        items.append((p, True, p.parents[1].name))
    for p in ref_files:
        items.append((p, False, p.name))
    # если референсов 0 — дублируем хиты как pseudo-refs для проверки перемешивания
    if not ref_files and len(items) < hits*2:
        # берём другие хиты как псевдо-референсы
        extra = [p for _, p in scored[hits:hits*2]]
        for p in extra:
            items.append((p, False, f"pseudo_ref_{p.parents[1].name}"))

    rng.shuffle(items)

    key = []
    for idx, (src, is_hit, orig) in enumerate(items, 1):
        dst = out / f"{idx:02d}.wav"
        try:
            shutil.copyfile(src, dst)
        except Exception as e:
            # если исходник mp3/flac — копируем как есть, плеер разберётся
            try:
                shutil.copy(src, dst.with_suffix(src.suffix))
                dst = dst.with_suffix(src.suffix)
            except Exception:
                continue
        key.append({
            "n": idx,
            "file": dst.name,
            "is_hit": is_hit,
            "orig": str(orig),
            "src": str(src),
        })

    # сохраняем ключ (не показывать слушателям!)
    (out / "_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "_key.txt").write_text("\n".join([f"{k['n']:02d} {'HIT' if k['is_hit'] else 'REF'} {k['orig']}" for k in key]), encoding="utf-8")
    # инструкция
    (out / "README.txt").write_text(
        "СЛЕПОЕ ПРОСЛУШИВАНИЕ\n"
        "1. Слушай файлы 01.wav ... в случайном порядке по docs/BLIND_LISTENING.md\n"
        "2. Оцени каждый по 5 пунктам 1-5\n"
        "3. Только после всех оценок открой _key.txt\n"
        "НЕ показывай _key слушателям до конца!\n",
        encoding="utf-8"
    )

    return {"out": str(out), "key": key, "hits": len(chosen_hits), "refs": len(ref_files), "total": len(items)}

def _cli() -> int:
    p = argparse.ArgumentParser(description="Подготовка слепого прослушивания")
    p.add_argument("--hits", type=int, default=5, help="сколько хитов взять")
    p.add_argument("--refs", type=str, default="", help="папка с референсами (wav/mp3)")
    p.add_argument("--seed", type=int, default=42, help="seed перемешивания")
    p.add_argument("--out", type=str, default="output/blind_test", help="куда")
    args = p.parse_args()
    res = prep(hits=args.hits, refs_dir=args.refs or None, seed=args.seed, out_dir=args.out)
    print(f"Готово: {res['out']} — {res['total']} файлов (хитов {res['hits']}, refs {res['refs']})")
    print(f"Ключ: {Path(res['out']) / '_key.txt'} — НЕ показывать слушателям!")
    return 0

if __name__ == "__main__":
    raise SystemExit(_cli())

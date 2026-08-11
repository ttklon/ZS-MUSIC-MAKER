# -*- coding: utf-8 -*-
"""
[14] recipe_importer.py — Воспроизведение трека по recipe.json (v5)
Позволяет: (1) загрузить recipe.json из прошлого релиза → пересобрать трек
с теми же параметрами, (2) экспортировать текущие настройки в recipe.
"""
import os, json, time


def load_recipe(recipe_path: str) -> dict:
    if not os.path.exists(recipe_path):
        return {"error": f"файл не найден: {recipe_path}"}
    try:
        return json.load(open(recipe_path, encoding="utf-8"))
    except Exception as e:
        return {"error": f"parse fail: {e}"}


def validate_recipe(recipe: dict) -> dict:
    required = ["bpm", "key", "vibe_tags"]
    missing = [k for k in required if k not in recipe]
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "has_groove": "groove" in recipe,
        "has_samples": "samples" in recipe or "sample_query" in recipe,
        "has_lyrics_theme": "theme" in recipe or "lyrics" in recipe,
    }


def recipe_to_pipeline_args(recipe: dict) -> dict:
    mode = "minor"
    if isinstance(recipe.get("key"), str) and "major" in recipe["key"].lower():
        mode = "major"
    key_root = "A"
    if isinstance(recipe.get("key"), str):
        parts = recipe["key"].split()
        if parts:
            key_root = parts[0][0].upper()
    bpm = int(recipe.get("bpm", 128))
    sv = {
        "sources": recipe.get("sources", ["recipe_import"]),
        "target_bpm": bpm, "target_mode": mode,
        "vibe_tags": recipe.get("vibe_tags", []),
        "target_bass_ratio": recipe.get("bass_ratio", 1.5),
        "target_centroid": recipe.get("centroid", 1500.0),
        "bpm_range": {"center": bpm, "range_low": bpm - 6, "range_high": bpm + 8,
                      "modes": {"keep_groove": bpm}},
        "individual": [{"key_root": key_root, "bpm": bpm,
                        "vibe_tags": recipe.get("vibe_tags", [])}],
        "imported_from_recipe": True,
    }
    groove = recipe.get("groove") or {
        "kick_pattern":  [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat_density": 0.5, "swing": 0.1,
    }
    return {
        "style_vector": sv, "groove": groove,
        "theme": recipe.get("theme", ", ".join(recipe.get("vibe_tags", ["движ"]))),
        "duration_sec": int(recipe.get("duration_sec", 120)),
        "sample_query": recipe.get("sample_query", " ".join(recipe.get("vibe_tags", [])[:3])),
        "n_verses": int(recipe.get("n_verses", 2)),
        "aggression": float(recipe.get("aggression", 0.7)),
        "steal_notes": recipe.get("steal_notes", []),
    }


def save_recipe(recipe: dict, out_path: str) -> dict:
    recipe.setdefault("exported_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    recipe.setdefault("format_version", "zsmm-v5")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(recipe, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    return {"ok": True, "saved_to": out_path}


def build_recipe_from_pipeline(style_vector: dict, groove: dict,
                                theme: str, duration_sec: int,
                                sample_query: str = "",
                                lyrics: str = "",
                                provenance: list = None,
                                steal_notes: list = None) -> dict:
    return {
        "format_version": "zsmm-v5",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bpm": style_vector.get("target_bpm", 128),
        "key": f"{style_vector.get('individual', [{}])[0].get('key_root', 'A')} "
               f"{style_vector.get('target_mode', 'minor')}",
        "vibe_tags": style_vector.get("vibe_tags", []),
        "groove": groove,
        "theme": theme, "duration_sec": duration_sec,
        "sample_query": sample_query, "lyrics": lyrics,
        "provenance": provenance or [],
        "steal_notes": steal_notes or [],
        "sources": style_vector.get("sources", []),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        r = load_recipe(sys.argv[1])
        print(json.dumps(validate_recipe(r), ensure_ascii=False, indent=2))
    else:
        print("Usage: python recipe_importer.py <recipe.json>")

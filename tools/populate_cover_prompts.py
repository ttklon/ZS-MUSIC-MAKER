"""Populate/verify prompt_cover metadata for versioned genre presets."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS_DIR = ROOT / "data" / "genre_presets"
PROMPT_TEMPLATE = (
    "Square album cover for {genre}: {mood} mood, {key} tonal palette, "
    "visual motifs of {instruments}; cinematic editorial lighting, original artwork, "
    "no logos, no watermark, no copied artist identity."
)


def instruments_for_genre(genre: str) -> str:
    name = genre.lower()
    if "phonk" in name or "drift" in name:
        return "cowbell, 808 bass, clipped drums and neon road reflections"
    if "trap" in name or "drill" in name:
        return "808 bass, sparse hi-hats, snare rolls and urban silhouettes"
    if "house" in name or "techno" in name or "edm" in name:
        return "four-on-the-floor drums, synth stabs, lasers and club architecture"
    if "lofi" in name or "chill" in name:
        return "dusty keys, tape texture, soft drums and intimate room light"
    if "rock" in name or "metal" in name:
        return "electric guitars, live drums, stage smoke and stark typography"
    if "pop" in name:
        return "bright synths, polished drums and high-fashion color fields"
    return "rhythmic drums, bass, melodic synths and atmospheric light"


def populate(presets_dir: Path = PRESETS_DIR) -> int:
    changed = 0
    for path in sorted(presets_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        instruments = instruments_for_genre(str(payload.get("genre") or path.stem))
        if payload.get("prompt_cover") != PROMPT_TEMPLATE or payload.get("cover_instruments") != instruments:
            payload["prompt_cover"] = PROMPT_TEMPLATE
            payload["cover_instruments"] = instruments
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed += 1
    return changed


def main() -> int:
    changed = populate()
    print(f"cover prompts populated: {changed}")
    return 0


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "ZS Music Maker tool"):
        raise SystemExit(0)
    raise SystemExit(main())

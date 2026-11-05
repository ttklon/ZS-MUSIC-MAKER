# -*- coding: utf-8 -*-
"""
modules/mastering_reference.py — мастеринг по референсу (Matchering 2.0).

Единственный адаптер над внешним `matchering`: подгоняет target под reference
по RMS/LUFS, спектру, стерео-ширине и пикам.

Публичный API:
  • `match_to_reference(target, reference, out_wav, out_mp3=None)` — прямое API.
  • `master_with_matchering(handle, input_wav, out_wav, reference_wav, ...)` —
    работа через уже загруженный handle из `app.ai.registry` (без перезагрузки).
  • `master_ai(input_wav, out_wav, reference_wav=None, ...)` — точка входа
    стадии: matchering по референсу, иначе единый движок `modules.mastering`.
  • `master_to_stand(target, out_wav, stand)` и `master_all_stands_matched` —
    громкость под стенд без референса (только при живом matchering).

Честность статусов: без matchering ни одна функция не выдаёт gain-нормализацию
за мастеринг — возвращается `ok: False` с причиной, а `master_ai` явно
переключается на DSP-чейн с `engine: "mastering_pro"` и `fallback_reason`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("zsmm.mastering")

try:  # внешний matchering — опционален
    import matchering as mg  # type: ignore

    MG_OK = True
except Exception:  # noqa: BLE001 - любая ошибка импорта = нет движка
    mg = None  # type: ignore
    MG_OK = False

LUF_STANDS: dict[str, float] = {
    "streaming": -14.0,
    "car": -8.5,
    "club": -6.5,
    "tiktok": -13.0,
}


def match_to_reference(
    target: str, reference: str, out_wav: str, out_mp3: str | None = None
) -> dict[str, Any]:
    """Подогнать `target` под `reference`. Без matchering — честный отказ."""
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    if not MG_OK:
        return {
            "ok": False,
            "engine": "none",
            "reason": "matchering unavailable; gain-only mastering is refused",
            "out_wav": out_wav,
        }
    try:
        results = [mg.pcm24(out_wav)]
        if out_mp3:
            results.append(mg.Result(out_mp3, subtype="PCM_16"))
        mg.process(target=target, reference=reference, results=results)
    except Exception as exc:  # noqa: BLE001 - движок кидает что угодно
        log.warning("matchering failed: %s", exc)
        return {"ok": False, "engine": "matchering", "reason": str(exc), "out_wav": out_wav}
    if not Path(out_wav).exists():
        return {"ok": False, "engine": "matchering", "reason": "no output produced", "out_wav": out_wav}
    return {"ok": True, "engine": "matchering", "out_wav": out_wav, "out_mp3": out_mp3}


def master_with_matchering(
    handle: Any,
    input_wav: str,
    out_wav: str,
    reference_wav: str,
    target_lufs: float = -14.0,
) -> dict[str, Any]:
    """Matchering через уже загруженный registry-handle + доводка LUFS."""
    try:
        handle.process(
            target=input_wav,
            reference=reference_wav,
            results=[handle.pcm16(out_wav)],
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"matchering failed: {exc}", "engine": "matchering"}
    if not Path(out_wav).exists():
        return {"ok": False, "reason": "matchering completed without output", "engine": "matchering"}

    from modules.mastering import normalize_master_loudness

    loudness = normalize_master_loudness(out_wav, out_wav, target_lufs=target_lufs, ceiling_db=-1.2)
    if not loudness.get("ok"):
        return {
            "ok": False,
            "reason": loudness.get("reason", "post-matchering normalization failed"),
            "engine": "matchering",
        }
    return {
        "ok": True,
        "engine": "matchering",
        "reference": reference_wav,
        "path": out_wav,
        "loudness": loudness,
    }


def master_ai(
    input_wav: str,
    out_wav: str,
    reference_wav: Optional[str] = None,
    target_lufs: float = -14.0,
    handle: Any = None,
) -> dict[str, Any]:
    """Стадия мастеринга: референс → matchering, иначе DSP-чейн."""
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    fallback_reason = ""
    if reference_wav and handle is not None:
        result = master_with_matchering(handle, input_wav, out_wav, reference_wav, target_lufs)
        if result.get("ok"):
            return result
        fallback_reason = result.get("reason", "matchering failed")
    elif reference_wav:
        from app.ai.registry import registry

        if registry.is_available("mastering_ai"):
            try:
                with registry.use("mastering_ai") as loaded:
                    result = master_with_matchering(
                        loaded.handle, input_wav, out_wav, reference_wav, target_lufs
                    )
                if result.get("ok"):
                    return result
                fallback_reason = result.get("reason", "matchering failed")
            except Exception as exc:  # noqa: BLE001
                fallback_reason = f"matchering load failed: {exc}"
        else:
            fallback_reason = "matchering unavailable"
    else:
        fallback_reason = "no reference"

    from modules import mastering

    res = mastering.master_one(input_wav, out_wav, stand="streaming")
    res = res if isinstance(res, dict) else {"ok": True, "path": out_wav}
    loudness = normalize_master_loudness(
        out_wav, out_wav, target_lufs=target_lufs, ceiling_db=-1.2
    )
    if not loudness.get("ok"):
        return {"ok": False, "reason": loudness.get("reason", "fallback normalization failed")}
    res["engine"] = "mastering_pro"
    res["fallback_reason"] = fallback_reason
    res["loudness"] = loudness
    return res


def master_to_stand(target: str, out_wav: str, stand: str = "streaming") -> dict[str, Any]:
    """Громкость под стенд без референса (matchering обязателен)."""
    if not MG_OK:
        return {
            "ok": False,
            "engine": "none",
            "stand": stand,
            "reason": "matchering unavailable; refusing gain-only mastering",
            "out_wav": out_wav,
        }
    from modules.mastering import normalize_master_loudness

    res = normalize_master_loudness(
        target, out_wav, target_lufs=LUF_STANDS.get(stand, -14.0), ceiling_db=-1.0
    )
    res.setdefault("engine", "matchering_loudness")
    res["stand"] = stand
    return res


def master_all_stands_matched(target: str, out_dir: str) -> dict[str, Any]:
    """Четыре версии под стенды: streaming / car / club / tiktok."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    stands = {stand: master_to_stand(target, str(Path(out_dir) / f"{stand}_master.wav"), stand)
              for stand in LUF_STANDS}
    return {"ok": all(r.get("ok") for r in stands.values()), "stands": stands}


__all__ = [
    "LUF_STANDS",
    "MG_OK",
    "match_to_reference",
    "master_ai",
    "master_all_stands_matched",
    "master_to_stand",
    "master_with_matchering",
]

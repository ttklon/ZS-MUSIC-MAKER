"""
[v8] auto_qa.py — Auto Quality Assurance loop.

ТЗ 20.2 п.34: «Программа должна сделать и прослушать трек так, как это сделал
бы человек. Прям чтобы это 100% было слушабельно.»

Auto-QA берёт финальный master.wav и прогоняет его через 3 виртуальных «уха»:
  1. AI Detector Pro (9 метрик) — оценка «нейроношности».
  2. Loudness/LUFS/peak/DR — соответствие коммерческому уровню.
  3. Structure & hook check — есть ли зацепляющий припев, не «плоско».

По сумме выдаёт verdict:
  • ✅ РЕЛИЗ — можно выпускать;
  • ⚠ ПЕРЕДЕЛАТЬ ЧАСТЬ — конкретно какой узел (beat/vocal/master);
  • ❌ ПЕРЕСОБРАТЬ ВСЁ — критично много флагов, нужен полный ре-run.

Возвращает JSON с рекомендациями. Orchestrator сам решает — цикл повторить или
завершить, если пользователь включил auto_qa_loop=True.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QA_DIR = ROOT / "output" / "auto_qa"
# v22: ленивое создание (не при импорте)


def _loudness(y, sr) -> dict:
    """Громкость для QA: настоящий BS.1770, а не «RMS минус 3».

    Раньше здесь стояло `lufs_approx = rms_db - 3.0` с комментарием «very
    rough K-weighting». На живом мастере это давало −20.4 LUFS там, где
    мастеринг измерил −14.4: QA объявлял правильно сведённый трек «слишком
    тихим» и выставлял `verdict=rebuild`. Теперь метрика одна на всё
    приложение — `modules.dsp.metrics.integrated_lufs` (pyloudnorm/BS.1770),
    а `lufs_approx` остаётся в ответе только как грубая оценка для сравнения.
    """
    import numpy as np

    if y.ndim > 1:
        m = y.mean(axis=1)
    else:
        m = y
    peak = float(np.max(np.abs(m))) if len(m) else 0.0
    rms = float(np.sqrt(np.mean(m * m))) if len(m) else 0.0
    peak_db = 20 * math.log10(peak + 1e-9)
    rms_db = 20 * math.log10(rms + 1e-9)
    crest = peak_db - rms_db
    out = {
        "peak_db": round(peak_db, 2),
        "rms_db": round(rms_db, 2),
        "lufs_approx": round(rms_db - 3.0, 2),
        "crest_factor_db": round(crest, 2),
    }
    try:
        from modules.dsp import metrics as dsp_metrics

        lufs, info = dsp_metrics.integrated_lufs(np.asarray(y), sr)
        out["lufs"] = round(float(lufs), 2)
        out["lufs_engine"] = str(info.get("engine") or "unknown")
    except Exception as exc:  # noqa: BLE001 - без движка остаётся оценка
        out["lufs"] = out["lufs_approx"]
        out["lufs_engine"] = f"approx ({type(exc).__name__})"
    return out


def _structure_check(y, sr) -> dict:
    """Ищем хук: повторяющийся куск ~8 сек с высокой энергией."""
    try:
        import librosa
        import numpy as np

        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=1024)[0]
        # Окно хука: 8 секунд на нормальном треке, но не больше трети самого
        # трека. Фиксированные 8 с требовали минимум 24 с и любой короткий
        # рендер (20 с по умолчанию в хит-фабрике) получал «структура не
        # проверена» — то есть QA молчал именно там, где нужен.
        w = max(int(sr * 2 / 1024), min(int(sr * 8 / 1024), len(rms) // 3))
        if len(rms) < 3 * w:
            # Раньше здесь не было error, а вызывающий код его читает:
            # структура считалась проверенной с hook_score 0 и без причины.
            return {
                "hook_score": 0.0,
                "sections_detected": 0,
                "error": f"too short for hook check: need >= {3 * w} frames, got {len(rms)}",
            }
        chunks = [rms[i : i + w] for i in range(0, len(rms) - w, w // 2)]
        best_corr = 0.0
        for i in range(len(chunks)):
            for j in range(i + 2, len(chunks)):
                a = chunks[i]
                b = chunks[j]
                if len(a) != len(b):
                    continue
                da = a - a.mean()
                db = b - b.mean()
                den = np.linalg.norm(da) * np.linalg.norm(db) + 1e-9
                c = float(np.dot(da, db) / den)
                best_corr = max(best_corr, c)
        return {
            "hook_score": round(best_corr, 3),
            "sections_detected": len(chunks),
        }
    except Exception as e:
        return {"hook_score": 0.0, "error": str(e)}


def _audit_ai_detector(master_wav: Path) -> tuple[dict, list[dict]]:
    """Первое «ухо»: оценка нейроношности. Возвращает (блок, действия)."""
    actions: list[dict] = []
    try:
        from modules.ai_detector_pro import analyze_track

        ad = analyze_track(str(master_wav))
        # Отсутствие метрики — это отсутствие вердикта, а не 0 %: пустой ответ
        # детектора нельзя читать как «нейросети не найдено».
        # Имена полей берём из реального контракта `analyze_track`:
        # `ai_risk_percent` (текущее) и `score` (0..1). Прежние
        # `neuronoshnost_percent`/`neuroness_percent` не существовали никогда,
        # поэтому QA всегда писал «AI Detector не дал оценку», хотя детектор
        # отвечал `ai_risk_percent: 11.1`, а это `verdict=patch` вместо
        # `rebuild`. `verdict` и `advice` тоже нужно донести до пользователя.
        neuro = ad.get("ai_risk_percent")
        if neuro is None and isinstance(ad.get("score"), (int, float)):
            neuro = round(float(ad["score"]) * 100.0, 1)
        # analyze_track возвращает {"error": ...} вместо исключения. Молча
        # прочитать это как 0 % — значит объявить трек чистым от нейросети
        # на основании того, что его не анализировали.
        if ad.get("error") or neuro is None:
            actions.append(
                {
                    "target": "ai_detector",
                    "reason": f"AI Detector не дал оценку: {ad.get('error') or 'нет метрики'}",
                    "fix": "проверить зависимости детектора и повторить аудит",
                }
            )
            neuro = 0
        if ad.get("advice"):
            for item in ad["advice"]:
                actions.append(
                    {
                        "target": "ai_detector",
                        "reason": str(item),
                        "fix": "правка звука по совету детектора (не атрибуция ИИ)",
                    }
                )
        if neuro and neuro > 70:
            actions.append(
                {
                    "target": "voice",
                    "reason": f"AI detector: {neuro}% нейроношности",
                    "fix": "переделать голос через ProVoice Mode + добавить бэки",
                }
            )
        elif neuro and neuro > 40:
            actions.append(
                {
                    "target": "vocal_humanization",
                    "reason": f"AI detector: {neuro}% нейроношности",
                    "fix": "усилить humanization (тайминг, дыхания, adlibs)",
                }
            )
        return ad, actions
    except Exception as e:
        return {"error": str(e)}, actions


def _audit_loudness(y, sr, target_lufs: float) -> tuple[dict, list[dict]]:
    """Второе «ухо»: громкость, пики и крест-фактор."""
    actions: list[dict] = []
    loudness = _loudness(y, sr)
    lu = float(loudness.get("lufs", loudness["lufs_approx"]))
    if lu < target_lufs - 3:
        actions.append(
            {
                "target": "mastering",
                "reason": f"Слишком тихо (LUFS≈{lu}, target={target_lufs})",
                "fix": "усилить лимитер, повторить Matchering",
            }
        )
    if loudness["peak_db"] > -0.2:
        actions.append(
            {
                "target": "mastering",
                "reason": "Клиппинг на пиках",
                "fix": "мягкий true-peak limiter −1 dBTP",
            }
        )
    return loudness, actions


def _audit_structure(structure: dict) -> list[dict]:
    """Третье «ухо»: есть ли хук. Провал разбора — не «хука нет»."""
    if structure.get("error"):
        # Аудит структуры не состоялся — это отдельная запись, а не
        # «не найден хук»: иначе пользователь ищет несуществующую проблему.
        return [
            {
                "target": "structure",
                "reason": f"Проверка структуры не выполнена: {structure['error']}",
                "fix": "проверить длительность мастера и наличие librosa",
            }
        ]
    if structure.get("hook_score", 0.0) < 0.35:
        return [
            {
                "target": "beat",
                "reason": "Не найден яркий хук",
                "fix": "усилить контраст припева, повторить Beat Constructor",
            }
        ]
    return []


def _verdict_for(actions: list[dict]) -> tuple[str, str]:
    """Свести замечания к одному вердикту и человеческому тексту."""
    if not actions:
        return "release", "✅ Готов к релизу"
    targets = ", ".join(str(item.get("target")) for item in actions)
    if len(actions) <= 2:
        return "patch", f"⚠ Переделать: {targets}"
    return "rebuild", "❌ Пересобрать всё"


def audit_track(master_wav: str | Path, target_lufs: float | None = None) -> dict:
    """Полный аудит финального трека.

    Возвращает dict с блоками `{ai_detector, loudness, structure, verdict,
    actions[]}`. `ok` здесь значит «аудит проведён и записан», а не «трек
    хорош»: качество описывает `verdict`, и `ok=true` рядом с
    `verdict=rebuild` — норма.

    `target_lufs` по умолчанию берётся из `mastering.targets` (−14.0 для
    streaming). Раньше здесь стоял литерал −9.0, из-за чего правильно
    сведённый по §7.2 мастер получал замечание «слишком тихо» и уезжал в
    `verdict=patch` — то есть QA спорил с собственным мастерингом.
    """
    if target_lufs is None:
        from modules.mastering.targets import STAND_TARGET_LUFS

        target_lufs = STAND_TARGET_LUFS["streaming"]
    master_wav = Path(master_wav)
    result = {
        "master": str(master_wav),
        "ts": time.time(),
        "ok": False,
        "actions": [],
    }
    if not master_wav.exists():
        result["error"] = "master.wav не найден"
        return result

    result["ai_detector"], ai_actions = _audit_ai_detector(master_wav)
    result["actions"].extend(ai_actions)

    try:
        import soundfile as sf

        y, sr = sf.read(str(master_wav))
        y_mono = y.mean(axis=1) if y.ndim > 1 else y
        result["loudness"], loud_actions = _audit_loudness(y, sr, target_lufs)
        result["actions"].extend(loud_actions)
        result["structure"] = _structure_check(y_mono, sr)
        result["actions"].extend(_audit_structure(result["structure"]))
    except Exception as e:
        result["loudness_error"] = str(e)

    # 3) Verdict
    result["verdict"], result["verdict_text"] = _verdict_for(result["actions"])

    # Save
    # QA_DIR в чистой установке отсутствует (output/ не в git) — без mkdir
    # удачный аудит падал FileNotFoundError прямо перед возвратом отчёта.
    QA_DIR.mkdir(parents=True, exist_ok=True)
    out = QA_DIR / f"qa_{int(time.time())}.json"
    result["report_path"] = str(out)
    result["ok"] = True
    # Пишем уже с заполненными ok/report_path: иначе файл на диске отличается
    # от возвращённого словаря (ok=true в ответе, ok=false в отчёте).
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def should_retry(
    qa_report: dict, max_iterations: int = 3, current_iter: int = 0
) -> tuple[bool, list[str]]:
    """
    Решаем — гонять ли pipeline снова.
    Возвращает (retry: bool, targets: list[str]).
    """
    if current_iter >= max_iterations:
        return False, []
    verdict = qa_report.get("verdict")
    if verdict == "release":
        return False, []
    targets = list(set(a["target"] for a in qa_report.get("actions", [])))
    return True, targets

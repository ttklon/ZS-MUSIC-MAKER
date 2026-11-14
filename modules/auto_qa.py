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
    """Приблизительный интегрированный LUFS / peak / crest factor."""
    import numpy as np

    if y.ndim > 1:
        m = y.mean(axis=1)
    else:
        m = y
    peak = float(np.max(np.abs(m))) if len(m) else 0.0
    rms = float(np.sqrt(np.mean(m * m))) if len(m) else 0.0
    peak_db = 20 * math.log10(peak + 1e-9)
    rms_db = 20 * math.log10(rms + 1e-9)
    lufs_approx = rms_db - 3.0  # very rough K-weighting
    crest = peak_db - rms_db
    return {
        "peak_db": round(peak_db, 2),
        "rms_db": round(rms_db, 2),
        "lufs_approx": round(lufs_approx, 2),
        "crest_factor_db": round(crest, 2),
    }


def _structure_check(y, sr) -> dict:
    """Ищем хук: повторяющийся куск ~8 сек с высокой энергией."""
    try:
        import librosa
        import numpy as np

        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=1024)[0]
        # 8-сек окно ~ 44100*8/1024
        w = int(sr * 8 / 1024)
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
        neuro = ad.get("neuronoshnost_percent", ad.get("neuroness_percent"))
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
    lu = loudness["lufs_approx"]
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


def audit_track(master_wav: str | Path, target_lufs: float = -9.0) -> dict:
    """
    Полный аудит финального трека. Возвращает dict с 3 блоками:
    {ai_detector, loudness, structure, verdict, actions[]}

    `ok` здесь значит «аудит проведён и записан», а не «трек хорош»: качество
    описывает `verdict`, и `ok=true` рядом с `verdict=rebuild` — норма.
    """
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
    n_actions = len(result["actions"])
    if n_actions == 0:
        result["verdict"] = "release"
        result["verdict_text"] = "✅ Готов к релизу"
    elif n_actions <= 2:
        result["verdict"] = "patch"
        result["verdict_text"] = "⚠ Переделать: " + ", ".join(
            a["target"] for a in result["actions"]
        )
    else:
        result["verdict"] = "rebuild"
        result["verdict_text"] = "❌ Пересобрать всё"

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

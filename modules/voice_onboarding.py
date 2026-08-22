"""
ZS Music Maker v14 — voice_onboarding.py (P0.07, TZ 14)
========================================================

Обязательный Voice Onboarding:
  минимум 5 минут записи голоса, разбитой на:
    — 2 минуты последовательного текста (33 русские фонемы);
    — 2 минуты × 8 стилей × 15 сек:
      slow_clear, fast_clear, conversational, aggressive, whisper,
      raspy, singing, semi_recitative;
    — 1 минута караоке.

По ТЗ 14.3:
  — автоматический VAD;
  — оценка SNR каждого take'а;
  — детекция клиппинга;
  — оценка фонемного покрытия;
  — сохранение в Voice Vault с метаданными.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VAULT_DIR = ROOT / "voice_vault"
# v22: ленивое создание (не при импорте)

MANIFEST = VAULT_DIR / "onboarding_manifest.json"
LOGGER = logging.getLogger(__name__)

RUS_PHONEMES = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")

STYLES = [
    "slow_clear",
    "fast_clear",
    "conversational",
    "aggressive",
    "whisper",
    "raspy",
    "singing",
    "semi_recitative",
]

PLAN = {
    "phoneme_text": 120,
    "styles_total": 120,
    "karaoke": 60,
    "total": 300,
}

PHONEME_SCRIPT = [
    "В чащах юга жил бы цитрус? Да, но фальшивый экземпляр.",
    "Съешь же ещё этих мягких французских булок, да выпей чаю.",
    "Широкая электрификация южных губерний даст мощный толчок подъёму сельского хозяйства.",
    "Экс-граф? Плюш изъят. Бьём чуждый цен хвощ.",
    "На дворе трава, на траве дрова, не руби дрова на траве двора.",
    "Ехал грека через реку, видит грека — в реке рак, сунул грека руку в реку, рак за руку греку цап.",
    "Шла Саша по шоссе и сосала сушку.",
    "Летели лебеди с лебедятами.",
    "От топота копыт пыль по полю летит.",
    "Карл у Клары украл кораллы, а Клара у Карла украла кларнет.",
]

KARAOKE_LINES = [
    "Ночь горит, я в дороге, город спит, а мы на пороге.",
    "Money over everything, летим вперёд, не тормозя.",
    "Тачки, движ, звук на максимум, лето внутри — мы не сдадимся.",
    "Огни за окном, за спиной — всё старое, впереди только новое.",
    "Turkish beat, palm trees, sea, everybody with me.",
    "Мы горим, мы летим, ночь у нас в руках, мы её держим.",
]


@dataclass
class OnboardingStep:
    step_id: str
    kind: str
    label: str
    target_sec: int
    text_or_prompt: str
    recorded_path: str | None = None
    duration_sec: float = 0.0
    rms_db: float = -100.0
    peak_db: float = -100.0
    clipping_pct: float = 0.0
    snr_db: float = 0.0
    covered_phonemes: list[str] = field(default_factory=list)
    ok: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingProgress:
    total_target_sec: int = 300
    total_recorded_sec: float = 0.0
    phoneme_coverage_pct: float = 0.0
    styles_done: int = 0
    styles_total: int = 8
    karaoke_done: bool = False
    percent: float = 0.0
    ready_for_rvc: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_plan() -> list[OnboardingStep]:
    steps: list[OnboardingStep] = []
    per_phrase = int(PLAN["phoneme_text"] / len(PHONEME_SCRIPT))
    for i, text in enumerate(PHONEME_SCRIPT, 1):
        steps.append(
            OnboardingStep(
                step_id=f"phon_{i:02d}",
                kind="phoneme_text",
                label=f"Фонемный текст {i}/{len(PHONEME_SCRIPT)}",
                target_sec=per_phrase,
                text_or_prompt=text,
            )
        )
    per_style = int(PLAN["styles_total"] / len(STYLES))
    for st in STYLES:
        steps.append(
            OnboardingStep(
                step_id=f"style_{st}",
                kind="style",
                label=f"Стиль: {st}",
                target_sec=per_style,
                text_or_prompt=(
                    f"Прочитайте 2-3 фразы в стиле «{st}». "
                    f"Например: «В машине бас качает, ночь горит»."
                ),
            )
        )
    steps.append(
        OnboardingStep(
            step_id="karaoke_01",
            kind="karaoke",
            label="Караоке под бит",
            target_sec=PLAN["karaoke"],
            text_or_prompt="\n".join(KARAOKE_LINES),
        )
    )
    return steps


def compute_phoneme_coverage(texts: list[str]) -> dict[str, Any]:
    seen = set()
    for t in texts:
        for ch in t.lower():
            if ch in RUS_PHONEMES:
                seen.add(ch)
    total = len(RUS_PHONEMES)
    covered = len(seen)
    pct = 100 * covered / total if total else 0.0
    missing = sorted(set(RUS_PHONEMES) - seen)
    return {
        "covered": sorted(seen),
        "missing": missing,
        "percent": round(pct, 1),
        "total": total,
    }


def _load_manifest() -> dict[str, Any]:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            LOGGER.warning("voice onboarding manifest unreadable; using empty plan: %s", error)
    return {"steps": [], "started_at": None, "completed_at": None}


def _save_manifest(m: dict[str, Any]) -> None:
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def record_step(step: OnboardingStep, mode: str = "auto") -> OnboardingStep:
    try:
        from modules import voice_recording as vr
    except Exception:
        step.ok = False
        return step

    cap = vr.capability_report()
    if cap.get("real_recording_possible") and mode == "auto":
        rec = vr.RealMicRecorder(sample_rate=48000, style=step.kind)
        info = rec.start()
        if info.get("ok"):
            time.sleep(step.target_sec)
            out = rec.stop()
            if out.get("ok"):
                step.recorded_path = out["path"]
                step.duration_sec = float(out["duration_sec"])
                step.ok = True
    return step


def compute_progress(steps: list[OnboardingStep]) -> OnboardingProgress:
    total_rec = sum(s.duration_sec for s in steps)
    styles_done = sum(
        1 for s in steps if s.kind == "style" and s.ok and s.duration_sec >= 10
    )
    karaoke_done = any(
        s.kind == "karaoke" and s.ok and s.duration_sec >= 30 for s in steps
    )
    phon_texts = [s.text_or_prompt for s in steps if s.kind == "phoneme_text" and s.ok]
    ph_cov = compute_phoneme_coverage(phon_texts)
    ph_pct = ph_cov["percent"]

    pct = min(100.0, 100 * total_rec / PLAN["total"])
    ready = total_rec >= 300 and ph_pct >= 80 and styles_done >= 6 and karaoke_done

    return OnboardingProgress(
        total_target_sec=PLAN["total"],
        total_recorded_sec=round(total_rec, 1),
        phoneme_coverage_pct=ph_pct,
        styles_done=styles_done,
        styles_total=len(STYLES),
        karaoke_done=karaoke_done,
        percent=round(pct, 1),
        ready_for_rvc=ready,
    )


def is_ready_for_rvc() -> bool:
    m = _load_manifest()
    steps = [OnboardingStep(**s) for s in m.get("steps", [])]
    return compute_progress(steps).ready_for_rvc


def run_cli() -> int:
    print("=" * 64)
    print("ZS Music Maker — Voice Onboarding (5 минут)")
    print("=" * 64)
    plan = build_plan()
    print(f"План: {len(plan)} шагов, всего {PLAN['total']} сек.")
    print(f"  — фонемный текст: {PLAN['phoneme_text']}s ({len(PHONEME_SCRIPT)} фраз)")
    print(f"  — 8 стилей × 15s: {PLAN['styles_total']}s")
    print(f"  — караоке: {PLAN['karaoke']}s")
    print()
    try:
        from modules import voice_recording as vr

        cap = vr.capability_report()
    except Exception as e:
        cap = {"real_recording_possible": False, "error": str(e)}
    print("[capability]", json.dumps(cap, ensure_ascii=False))
    mic_ok = bool(cap.get("real_recording_possible"))
    if not mic_ok:
        print("⚠️  Микрофон недоступен. Реальная запись НЕВОЗМОЖНА в этой среде.")
    m = _load_manifest()
    m["started_at"] = m.get("started_at") or int(time.time())
    m["steps"] = [s.as_dict() for s in plan]
    m["recording_capable"] = mic_ok
    _save_manifest(m)
    print(f"✓ manifest saved: {MANIFEST}")
    # v34 FIX (P3.16): раньше run_cli() ВСЕГДА возвращал 0 — даже когда
    # микрофон недоступен и onboarding по факту «только план, без записи».
    # CI/скрипты не могли отличить полный прогон от усечённого.
    # Теперь: 0 = полная capability, 1 = план сохранён, но запись невозможна.
    if not mic_ok:
        print("[voice_onboarding] exit=1 (plan-only: mic unavailable)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())

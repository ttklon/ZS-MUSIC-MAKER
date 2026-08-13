"""
ZS Music Maker v10 — Interactive Onboarding Tour
==================================================
Пошаговый интерактивный тур (ТЗ 5, «ONBOARDING»).

Framework-agnostic — работает и с PySide6, и с Gradio, и в консоли.
Данные тура: 15 шагов на русском, каждый привязан к элементу wizard'а.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger("zsmm.tour")


def _tour_state_path() -> Path:
    """v34 FIX (P3.26): раньше путь был относительным `Path("tutorial_settings.json")` —
    т.е. зависел от CWD: при запуске из другой папки создавался дубль-файл,
    а прогресс тура терялся. Теперь единый путь data/tutorial_settings.json
    с миграцией старого файла из корня репозитория."""
    root = Path(__file__).resolve().parents[1]
    new = root / "data" / "tutorial_settings.json"
    old_root = root / "tutorial_settings.json"
    old_cwd = Path("tutorial_settings.json")
    try:
        new.parent.mkdir(parents=True, exist_ok=True)
        if not new.exists():
            for cand in (old_root, old_cwd):
                if cand.exists() and cand.resolve() != new.resolve():
                    new.write_text(cand.read_text(encoding="utf-8"), encoding="utf-8")
                    break
    except Exception as e:
        log.warning(f"tour state migration failed: {e}")
    return new


TOUR_STATE = _tour_state_path()

TOUR_STEPS: list[dict[str, Any]] = [
    {
        "id": "welcome",
        "title": "Привет!",
        "text": "Это ZS Music Maker v10. Тур займёт 3 минуты. "
        "После него ты сможешь собрать свой первый трек за 10 минут.",
        "action": "next",
        "anchor": None,
    },
    {
        "id": "artist_name",
        "title": "Твоё имя",
        "text": "Введи артист-имя. Оно пойдёт в ID3-теги и на обложку.",
        "action": "input",
        "anchor": "artist_name_field",
    },
    {
        "id": "references",
        "title": "Референсы",
        "text": "Загрузи 1–7 треков, которые задают вайб. Можешь указать вес каждого.",
        "action": "highlight",
        "anchor": "step1_references",
    },
    {
        "id": "weights",
        "title": "Вес референсов",
        "text": "Слайдеры справа: например, 50% вайб первого + 30% ритм второго. "
        "Программа смешает.",
        "action": "highlight",
        "anchor": "weight_sliders",
    },
    {
        "id": "length",
        "title": "Длительность",
        "text": "Ползунок от 1:30 до 3:20+. Для TikTok-хита оптимум 2:00-2:30.",
        "action": "highlight",
        "anchor": "length_slider",
    },
    {
        "id": "style",
        "title": "Пресет стиля",
        "text": "Trap, Turkish-pop, phonk, hyperpop... Или свой микс.",
        "action": "highlight",
        "anchor": "style_preset",
    },
    {
        "id": "samples",
        "title": "Сэмплы",
        "text": "Split-view: локальные слева, Freesound/Wikimedia справа. "
        "Фильтр по CC0 включён по умолчанию.",
        "action": "highlight",
        "anchor": "sample_browser",
    },
    {
        "id": "lyrics",
        "title": "Текст",
        "text": "Три источника: твои строки, транскрипция референсов, Trend Scout. "
        "Все твои строки на 100% попадут в трек.",
        "action": "highlight",
        "anchor": "lyrics_editor",
    },
    {
        "id": "voice_vault",
        "title": "Voice Vault",
        "text": "Здесь копится твой голос. Записывай короткие фразы в разных стилях. "
        "Через 5-10 минут — RVC натренит модель.",
        "action": "highlight",
        "anchor": "voice_vault",
    },
    {
        "id": "karaoke",
        "title": "Караоке",
        "text": "В Pro-режиме открывается окно записи с подсветкой слов, "
        "метрономом и регулятором громкости эталона в ушах.",
        "action": "highlight",
        "anchor": "karaoke_button",
    },
    {
        "id": "polish",
        "title": "Anti-neuro polish",
        "text": "Экспертные опции: gentle / standard / aggressive. "
        "Устраняет «пластмассовый» вокал.",
        "action": "highlight",
        "anchor": "polish_dropdown",
    },
    {
        "id": "stands",
        "title": "Стенды",
        "text": "Каждый релиз даёт 3 мастера: car -8.5, club -6.5, streaming -14 LUFS. "
        "Проверь в машине!",
        "action": "highlight",
        "anchor": "stands_toggle",
    },
    {
        "id": "release_pack",
        "title": "Релиз-пакет",
        "text": "После рендера: WAV/MP3/FLAC + инструментал + акапелла + стемы + "
        "TikTok/Reels + обложка + LRC + метаданные.",
        "action": "highlight",
        "anchor": "release_folder",
    },
    {
        "id": "hit_score",
        "title": "HIT SCORE",
        "text": "12 метрик оценят чарт-потенциал. Вердикт + список конкретных доработок.",
        "action": "highlight",
        "anchor": "hit_score_widget",
    },
    {
        "id": "finish",
        "title": "Готово!",
        "text": "Тур завершён. Начни с загрузки одного референса — программа проведёт дальше. "
        "Тур можно перезапустить в меню Помощь.",
        "action": "finish",
        "anchor": None,
    },
]


def load_state() -> dict[str, Any]:
    if TOUR_STATE.exists():
        try:
            return json.loads(TOUR_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tour_done": False, "last_step": 0}


def save_state(state: dict[str, Any]) -> None:
    TOUR_STATE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def should_show() -> bool:
    return not load_state().get("tour_done", False)


def steps() -> list[dict[str, Any]]:
    return list(TOUR_STEPS)


def get_step(idx: int) -> dict[str, Any] | None:
    if 0 <= idx < len(TOUR_STEPS):
        return TOUR_STEPS[idx]
    return None


def mark_done() -> None:
    save_state({"tour_done": True, "last_step": len(TOUR_STEPS) - 1})


def reset() -> None:
    save_state({"tour_done": False, "last_step": 0})


def run_console_demo() -> None:
    """
    Демо-тур в консоли (для CI и slow-железа).
    """
    for i, step in enumerate(TOUR_STEPS):
        print(f"\n=== Шаг {i+1}/{len(TOUR_STEPS)}: {step['title']} ===")
        print(step["text"])
        if step.get("anchor"):
            print(f"  → элемент интерфейса: {step['anchor']}")
    mark_done()
    print("\nТур завершён.")


if __name__ == "__main__":
    run_console_demo()

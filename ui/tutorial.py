"""
UI: Tutorial System v2 (НОВЫЙ)
Пошаговый интерактивный туториал — показывает весь функционал приложения.
Пользователь идёт шаг за шагом, каждый шаг объясняет что и зачем.
Можно включить/выключить.
"""

import json
import os

# v34 FIX (P3.26): единый путь data/tutorial_settings.json (раньше этот модуль
# писал в корень репо, а modules/onboarding_tour.py — в CWD: получалось ДВА
# рассинхронизированных файла состояния). Миграция старого файла сохранена.
def _resolve_settings_file() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    new = os.path.join(root, "data", "tutorial_settings.json")
    old = os.path.join(root, "tutorial_settings.json")
    try:
        os.makedirs(os.path.dirname(new), exist_ok=True)
        if not os.path.exists(new) and os.path.exists(old):
            with open(old, encoding="utf-8") as f:
                payload = f.read()
            with open(new, "w", encoding="utf-8") as f:
                f.write(payload)
    except Exception:
        pass
    return new


SETTINGS_FILE = _resolve_settings_file()


STEPS = [
    {
        "id": "welcome",
        "title": "Добро пожаловать в ZS Music Maker!",
        "text": "Это автономная локальная студия для написания хитовых фонк/дрифт/эдит-треков. "
        "Всё работает бесплатно на твоём ПК. Давай пройдём по всем вкладкам за 2 минуты.",
        "action": "Нажми 'Далее' чтобы продолжить.",
        "tab": None,
    },
    {
        "id": "analysis",
        "title": "① Анализ референсов",
        "text": "Сюда ты закидываешь 1-7 треков, которые тебе нравятся. "
        "Программа проанализирует их: BPM, тональность, энергию, вайб. "
        "Если треков несколько — построит усреднённый style-vector. "
        "Ты можешь указать ВЕС каждого трека и что именно из него взять "
        "(бит, стиль чтения, образы, ритм). "
        "BPM определяется не как одно число, а как диапазон с режимами "
        "(кач/ускорить/замедлить/клубнее/TikTok-hooky).",
        "action": "Попробуй: закинь 2-3 трека и нажми 'Анализировать'.",
        "tab": "① Анализ",
    },
    {
        "id": "stems",
        "title": "② Сплит стемов",
        "text": "Demucs v4 разбирает трек на 4 дорожки: вокал, барабаны, бас, остальное. "
        "Это нужно ТОЛЬКО для АНАЛИЗА — как устроен грув, где хук, где дроп. "
        "Никакого копирования! Прямое заимствование стемов отключено.",
        "action": "Закинь трек и нажми 'Разобрать на стемы'.",
        "tab": "② Стемы",
    },
    {
        "id": "groove",
        "title": "③ Rhythm DNA",
        "text": "НОВОЕ: извлекает ритмическую ДНК из референса. "
        "Не ноты и не лупы, а абстрактный groove template: "
        "где кик, где снейр, плотность хэта, свинг, triplet-rolls. "
        "Потом этот шаблон пересобирается ДРУГИМИ звуками — "
        "похожий ритм, но оригинальное звучание.",
        "action": "Выбери референс и извлеки groove.",
        "tab": "③ Rhythm DNA",
    },
    {
        "id": "samples",
        "title": "④ Сэмплы — наше всё!",
        "text": "Три режима:\n"
        "• Find Online — поиск бесплатных сэмплов (Freesound, Pixabay)\n"
        "• Pick From Library — из локальной библиотеки\n"
        "• Upload My Sample — загрузить свой звук\n"
        "Фильтры по жанру, BPM, тональности, лицензии. "
        "Каждый сэмпл регистрируется в Provenance Manager "
        "(отслеживание лицензий для безопасности).",
        "action": "Попробуй найти сэмплы по запросу 'phonk 808'.",
        "tab": "④ Сэмплы",
    },
    {
        "id": "beat",
        "title": "⑤ Конструктор бита (ЯДРО)",
        "text": "Это ГЛАВНОЕ для твоего железа (RX 580 4GB). "
        "Бит собирается из сэмплов + groove template, а не из нейронки. "
        "Ты указываешь: длительность, количество куплетов/припевов, "
        "агрессию/качёвость. Программа собирает аранжировку из блоков: "
        "intro → verse → pre_chorus → hook → verse → hook → outro. "
        "Делает вариации: смена хэта, фильтр перед дропом, стоп-таймы. "
        "MusicGen (вкладка Текстуры) — для атмосферы и FX, не для основного бита.",
        "action": "Нажми 'Собрать бит' с groove из шага ③.",
        "tab": "⑤ Бит",
    },
    {
        "id": "textures",
        "title": "⑥ Нейро-текстуры (MusicGen)",
        "text": "MusicGen работает на CPU (медленно на RX 580, но работает). "
        "Используется ТОЛЬКО для: атмосферы, этнических пэдов, "
        "переходных FX, набросков хука. Не как основной движок! "
        "Когда купишь карту на 12GB — здесь можно будет генерить "
        "более жирные текстуры.",
        "action": "Сгенерируй 15-сек текстуру для интро.",
        "tab": "⑥ Текстуры",
    },
    {
        "id": "lyrics",
        "title": "⑦ Текст",
        "text": "Три источника:\n"
        "1. Твои идеи — тема, слова, эмоции\n"
        "2. Анализ референсов — транскрипция через Whisper\n"
        "3. Тренд-агент — ищет сленг и мемы в интернете\n"
        "Ollama (Llama 3) генерирует текст локально. "
        "Lyric Vault хранит все удачные строки, панчи, хуки. "
        "Тегируй их: заезжено/свежо/сильно/под лето/под машину. "
        "Можешь написать текст сам — просто вставь его.",
        "action": "Напиши тему и сгенерируй текст.",
        "tab": "⑦ Текст",
    },
    {
        "id": "voice",
        "title": "⑧ Голос — АНТИ-ПАЛЕВО (САМОЕ ВАЖНОЕ)",
        "text": "Voice Vault — постоянное хранилище твоего голоса. "
        "Чем больше записей — тем лучше модель. "
        "ПРОЦЕСС:\n"
        "1. Жми 'Дай текст для записи' → получишь текст + стиль\n"
        "2. Запиши через микрофон (8 стилей: медленно/громко/шёпот/пение...)\n"
        "3. Сохраняй в Voice Vault\n"
        "4. Повтори 20-50 раз (цель: ≥5 минут)\n"
        "5. Жми 'Обучить модель' — RVC дообучится\n\n"
        "Два режима вокала:\n"
        "• Lazy: Bark озвучивает текст → RVC подменяет тембр\n"
        "• Pro: ты поёшь в караоке → RVC полирует\n\n"
        "Программа отслеживает phoneme coverage — каких звуков не хватает.",
        "action": "Запиши первый сэмпл голоса прямо сейчас!",
        "tab": "⑧ Голос",
    },
    {
        "id": "karaoke",
        "title": "⑧-б Караоке-запись",
        "text": "Для режима Pro: программа генерирует 'как должно звучать' "
        "(референс-вокал), показывает текст с подсветкой слов, "
        "включает бит. Ты поёшь в микрофон, слыша референс в наушниках. "
        "Потом RVC полирует твой вокал под твой же голос.",
        "action": "Попробуй караоке-режим с готовым текстом.",
        "tab": "⑧ Голос",
    },
    {
        "id": "humanization",
        "title": "⑨ Анти-нейроношность",
        "text": "Проверяет вокал на AI-признаки:\n"
        "• слишком ровная динамика\n"
        "• смазанные согласные\n"
        "• переавтотюненность\n"
        "• 'ghost harmonies'\n"
        "Humanization Layer добавляет живости:\n"
        "• микро-timing сдвиги\n"
        "• дыхание в паузах\n"
        "• разные динамики между секциями\n"
        "• нормальную развязку (fade вместо обрубания)",
        "action": "Проверь вокал на AI-признаки.",
        "tab": "⑨ Humanization",
    },
    {
        "id": "mix",
        "title": "⑩ Финальный микс",
        "text": "Склеивает бит + вокал, добавляет sidechain-компрессию, "
        "эквалайзер. Matchering подгоняет мастеринг под ЛЮБОЙ "
        "выбранный референс (не только один трек). "
        "Ты сегодня ориентируешься на один трек, завтра на другой — "
        "движок универсальный.",
        "action": "Загрузи beat, vocal и reference — нажми 'Собрать'.",
        "tab": "⑩ Микс",
    },
    {
        "id": "release",
        "title": "⑪ Релиз-пакет",
        "text": "Создаёт полный пакет для публикации:\n"
        "• WAV 24-bit master\n"
        "• MP3 320\n"
        "• FLAC\n"
        "• instrumental\n"
        "• acapella\n"
        "• TikTok edit (30 сек)\n"
        "• lyrics.txt\n"
        "• recipe.json (как сделано)\n"
        "• sample_manifest.json (лицензии)\n"
        "• release_notes.txt\n"
        "• metadata.json (для дистрибуции)",
        "action": "Собери релиз-пакет из готового трека.",
        "tab": "⑪ Релиз",
    },
    {
        "id": "autopilot",
        "title": "🚀 Полный автопилот",
        "text": "Один клик — весь пайплайн: референсы → анализ → groove → "
        "сэмплы → бит → текст → вокал → RVC → humanization → микс → "
        "релиз. Для ленивых дней. "
        "Программа становится умнее с каждым использованием: "
        "Voice Vault копится, Lyric Vault пополняется, "
        "анализы кэшируются.",
        "action": "Попробуй автопилот!",
        "tab": "🚀 Автопилот",
    },
    {
        "id": "done",
        "title": "🎉 Туториал завершён!",
        "text": "Теперь ты знаешь весь функционал. "
        "Начни с записи голоса (вкладка ⑧) — это самое важное для "
        "анти-палева. Потом анализируй референсы и собирай биты. "
        "Удачи в создании хитов! 🎧🔥",
        "action": "Туториал можно пройти заново в любое время.",
        "tab": None,
    },
]


def get_tutorial_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            return json.load(open(SETTINGS_FILE, encoding="utf-8"))
        except Exception:
            return {}
    return {"enabled": True, "current_step": 0, "completed": False}


def save_tutorial_settings(settings: dict):
    json.dump(
        settings,
        open(SETTINGS_FILE, "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )


def get_step(index: int) -> dict:
    if 0 <= index < len(STEPS):
        return STEPS[index]
    return None


def next_step() -> dict:
    settings = get_tutorial_settings()
    idx = settings.get("current_step", 0)
    if idx < len(STEPS) - 1:
        settings["current_step"] = idx + 1
        save_tutorial_settings(settings)
        return get_step(idx + 1)
    settings["completed"] = True
    save_tutorial_settings(settings)
    return {
        "id": "done",
        "title": "Завершено",
        "text": "Туториал пройден!",
        "action": "",
    }


def prev_step() -> dict:
    settings = get_tutorial_settings()
    idx = settings.get("current_step", 0)
    if idx > 0:
        settings["current_step"] = idx - 1
        save_tutorial_settings(settings)
        return get_step(idx - 1)
    return get_step(0)


def skip_tutorial():
    settings = get_tutorial_settings()
    settings["enabled"] = False
    settings["completed"] = True
    save_tutorial_settings(settings)


def reset_tutorial():
    settings = {"enabled": True, "current_step": 0, "completed": False}
    save_tutorial_settings(settings)


def get_total_steps() -> int:
    return len(STEPS)


if __name__ == "__main__":
    for i, s in enumerate(STEPS):
        print(f"{i+1}. {s['title']}")

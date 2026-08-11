"""
[v7] onboarding.py — Scriptable Tour при первом запуске.

Полноэкранное приветственное окно с пошаговым туром по интерфейсу.
Появляется автоматически при первом запуске (user_profile.first_run=True).
Можно вручную запустить из меню "Помощь".
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

TOUR_STEPS = [
    {
        "title": "🎛 Добро пожаловать в MM ZS v7",
        "text": (
            "Это ZS Music Maker v7 — твоя локальная студия хитов.\n\n"
            "Мы собираем оригинальные треки на твоём ПК, без подписок и облаков. "
            "Всё бесплатно, всё локально.\n\n"
            "Через 5 минут ты сделаешь свой первый трек.\n\n"
            "Двинули?"
        ),
    },
    {
        "title": "① Референсы — что качает",
        "text": (
            "Первый шаг — покажи, какая музыка тебе нравится.\n\n"
            "Просто перетащи 1–7 треков (mp3/wav) в окно. Программа НЕ КОПИРУЕТ их — "
            "она вытянет вайб, BPM, ритм-паттерн, тональность.\n\n"
            "Хочешь без референсов? Пропусти шаг — на шаге ② выбери пресет."
        ),
    },
    {
        "title": "② Стиль — тема, длина, режим",
        "text": (
            "Выбери:\n"
            "  • Что должно быть в тексте (тема)\n"
            "  • Длину трека (от 1:30 до 3:30)\n"
            "  • Режим: Быстрый (10-15 мин) / Качественный (30-60 мин) / Максимальный (1-3 часа)\n\n"
            "По умолчанию — Качественный. Максимальный для релизов."
        ),
    },
    {
        "title": "③ Сэмплы — только чистые (CC0/Royalty-Free)",
        "text": (
            "Слева — твоя локальная библиотека (samples_cache/).\n"
            "Справа — интернет-поиск (Wikimedia CC0, Pixabay, Freesound).\n\n"
            "Программа блокирует всё, что нельзя выпускать коммерчески. "
            "Ты выпускаешь под своим именем — юридически чисто с первого трека."
        ),
    },
    {
        "title": "④ Текст — русские куплеты + английский хук",
        "text": (
            "У тебя есть ОБЯЗАТЕЛЬНОЕ поле «Моя тема / Мои строчки».\n"
            "Что впишешь — то ГАРАНТИРОВАННО попадёт в трек, дословно.\n\n"
            "Куплеты — по-русски. Хуки — короткие английские фразы.\n\n"
            "Тексты пишет Llama 3 через Ollama (если запущено). Или наш шаблонник."
        ),
    },
    {
        "title": "⑤ Голос — ФУНДАМЕНТ",
        "text": (
            "Это самый важный шаг для «не-нейроношности».\n\n"
            "  • Lazy — синтезируем текст → RVC переодевает голос под тебя\n"
            "  • Pro — ТЫ САМ поёшь под бит в наушниках → RVC полирует\n\n"
            "Voice Vault копит твои записи по 8 стилям (медленно, быстро, "
            "агрессивно, шёпот, с хрипом, нараспев и т.д.).\n\n"
            "Обучение RVC: ~30 минут на 12GB VRAM, до 3 часов на слабом железе. "
            "Идёт в фоне — не блокирует работу."
        ),
    },
    {
        "title": "⑥ Мастеринг → 3 стенда прослушивания",
        "text": (
            "Мы делаем не один мастер, а сразу три:\n"
            "  🚗 Автомобиль — жирный саб, буст низов\n"
            "  🎧 Клуб — громкость + суб\n"
            "  📱 Стриминг — нейтральный, для Spotify/Yandex\n\n"
            "Каждый под свою среду. Матчеринг подгоняет под ЛЮБОЙ выбранный референс."
        ),
    },
    {
        "title": "⑦ Релиз-пакет — 20+ файлов автоматически",
        "text": (
            "В конце получаешь всё сразу:\n"
            "  • master.wav (24-bit) + mp3 320 + flac\n"
            "  • instrumental + acapella\n"
            "  • стемы (drums/bass/vocals/other)\n"
            "  • lyrics.txt + lyrics.lrc (караоке)\n"
            "  • cover.png (обложка)\n"
            "  • tiktok.mp4 + reels.mp4 (15-30 сек, вертикально)\n"
            "  • car/club/streaming мастера\n"
            "  • recipe.json (пересобрать этот же трек по recipe)\n"
            "  • manifest.json (лицензии сэмплов)\n\n"
            "Всё с твоим именем в ID3-тегах. Готово к загрузке в дистрибьютор."
        ),
    },
    {
        "title": "🎯 На результате — 3 кнопки",
        "text": (
            "Не понравилось? Не проблема.\n\n"
            "  🔁 Пересобрать всё — полный рестарт с теми же настройками\n"
            "  ✂️ Переделать часть — только бит / только текст / только голос / только мастер\n"
            "  🎲 3 варианта — параллельно сделает 3 версии для сравнения\n\n"
            "И ещё: ставь в очередь до 5+ проектов на ночь. Утром — готовый пак."
        ),
    },
    {
        "title": "🔧 Экспертный режим",
        "text": (
            "Всё, что ты видел до этого — Wizard, «средний контроль».\n\n"
            "Хочешь глубже? Ctrl+E — откроется старый Gradio-режим v5 со всеми "
            "15+ вкладками: BPM-override, EQ, Whisper-параметры, тонкие настройки "
            "мастеринга, humanization, groove-веса и т.д.\n\n"
            "По умолчанию всё это спрятано — не пугает новичка."
        ),
    },
    {
        "title": "🚀 Готово!",
        "text": (
            "Всё, ты в теме. Программа работает автономно, локально, бесплатно.\n\n"
            "Иди на шаг ①, кинь пару треков — и запускай.\n\n"
            "Помощь (F1) на каждом шаге. Тур можно повторить в меню Помощь."
        ),
    },
]


class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MM ZS v7 — Обучающий тур")
        self.resize(720, 520)
        self.step = 0

        v = QVBoxLayout(self)

        self.title = QLabel()
        self.title.setStyleSheet("font-size:22px;font-weight:700;color:#ff5a28;")
        v.addWidget(self.title)

        self.body = QTextBrowser()
        self.body.setStyleSheet(
            "background:#17171d;color:#e8e8ee;border:1px solid #2a2a34;padding:12px;font-size:14px;"
        )
        v.addWidget(self.body, 1)

        self.dont_show = QCheckBox("Больше не показывать при запуске")
        v.addWidget(self.dont_show)

        bar = QHBoxLayout()
        self.btn_prev = QPushButton("← Назад")
        self.btn_skip = QPushButton("Пропустить")
        self.btn_next = QPushButton("Далее →")
        self.progress = QLabel()
        self.progress.setStyleSheet("color:#9a9aa4;")
        for b in (self.btn_prev, self.btn_skip):
            bar.addWidget(b)
        bar.addStretch()
        bar.addWidget(self.progress)
        bar.addStretch()
        bar.addWidget(self.btn_next)
        v.addLayout(bar)

        self.btn_prev.clicked.connect(self.prev)
        self.btn_next.clicked.connect(self.next)
        self.btn_skip.clicked.connect(self.reject)

        self.render()

    def render(self):
        s = TOUR_STEPS[self.step]
        self.title.setText(s["title"])
        # HTML для абзацев + сохранения переносов
        html = s["text"].replace("\n\n", "<br><br>").replace("\n", "<br>")
        self.body.setHtml(
            f"<div style='font-family:Segoe UI,Arial;line-height:1.5;'>{html}</div>"
        )
        self.progress.setText(f"Шаг {self.step+1} / {len(TOUR_STEPS)}")
        self.btn_prev.setEnabled(self.step > 0)
        self.btn_next.setText(
            "Закрыть ✓" if self.step == len(TOUR_STEPS) - 1 else "Далее →"
        )

    def prev(self):
        if self.step > 0:
            self.step -= 1
            self.render()

    def next(self):
        if self.step < len(TOUR_STEPS) - 1:
            self.step += 1
            self.render()
        else:
            self.accept()


def maybe_show_onboarding(parent=None) -> bool:
    """
    Показать тур если это первый запуск. Возвращает True если показан.
    """
    try:
        from modules.user_profile import is_first_run, mark_onboarded
    except Exception:
        return False
    if not is_first_run():
        return False
    d = OnboardingDialog(parent)
    d.exec()
    if d.dont_show.isChecked() or True:  # всегда фиксируем, что первый запуск прошёл
        mark_onboarded()
    return True


def show_help_tour(parent=None) -> None:
    """Ручной вызов тура из меню «Помощь»."""
    OnboardingDialog(parent).exec()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    a = QApplication(sys.argv)
    d = OnboardingDialog()
    d.exec()

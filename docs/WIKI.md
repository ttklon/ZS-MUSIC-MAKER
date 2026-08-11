# ZS Music Maker — ULTIMATE WIKI (Singularity)
========================================================================

Добро пожаловать в официальную базу знаний самого продвинутого AI-музыкального движка.

## 🚀 Быстрый старт
Для установки всех зависимостей и подготовки моделей запустите:
```bash
python install.py
```

Запуск основного пайплайна (GOD MODE):
```bash
python main.py --god --genre techno
```

## 🏗 Архитектура
Проект построен на базе **PipelineCore** — модульной системы задач с поддержкой чекпоинтов и асинхронности.

### Основные компоненты:
1.  **Genre Engine**: Поддержка 119+ музыкальных жанров.
2.  **Plugin System**: Динамическая цепочка аудио-эффектов (Distortion, Obfuscation, Mastering).
3.  **Model Manager**: Автоматическая загрузка и безопасная работа с нейросетями.
4.  **Async Orchestrator**: Параллельная генерация компонентов трека.

## 🎹 Список жанров
Программа поддерживает 119 жанров, разделенных на категории:
- **Electronic**: Techno, House, Drum & Bass, Dubstep...
- **Hip-Hop**: Drift Phonk, Lo-Fi, Trap, Boom Bap...
- **Rock/Metal**: Heavy Metal, Punk, Grunge...
- **Classical/Cinematic**: Baroque, Ambient, Orchestral...

Полный список можно получить командой: `python main.py --list-genres`

## 🛠 Инструменты разработчика
- `tools/genre_validator.py`: Валидация всех конфигов.
- `tools/smoke_v26.py`: Комплексные тесты качества звука.
- `app/core/logger.py`: Централизованное логирование с ротацией.

## 🛡 Безопасность и Стабильность
- Все сетевые вызовы проходят через `security_utils.py` (SHA-256).
- Память очищается принудительно через `gc.collect()`.
- Промежуточные данные сохраняются в бинарные чекпоинты `.pkl`.

---
*© 2026 ZS Music Maker Team. Coding like a God.*

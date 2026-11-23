# -*- coding: utf-8 -*-
"""app/core/ollama_bootstrap.py — подготовка Ollama в авто-докачке.

Вынесено из `bootstrap.py`: там файл уже был на пределе 400 строк, а проверка
`test_production_files_stay_readable` — не формальность. Логика при этом одна:
если бинаря нет — скачать официальный установщик (только при разрешённой сети),
если бинарь есть — тихо `ollama pull` нужной модели.
"""

from __future__ import annotations

import logging
import os
import subprocess

_LOG = logging.getLogger(__name__)

# Тег модели. Раньше здесь стояло `qwen3.5:4b` — такого тега в библиотеке Ollama
# нет, `ollama pull` молча падал, и текст оставался без LLM. `qwen3:4b` (~2.5 ГБ,
# Q4) — проверенная CPU-модель.
OLLAMA_TEXT_MODEL = os.environ.get("ZSMM_OLLAMA_PULL_MODEL", "qwen3:4b")

# Отчёт последней попытки: `auto_bootstrap` отдаёт его окну, чтобы «текст
# BLOCKED» имел объяснение и команду, а не только статус.
last_attempt: dict = {}


def install_when_missing(allow_download: bool | None = None) -> list[str]:
    """Скачать установщик Ollama, если бинаря нет; отчёт — в `last_attempt`."""
    _LOG.info("[bootstrap] ollama not installed — скачиваю установщик (если сеть разрешена)")
    try:
        from modules.llm.ollama_setup import ensure_ollama

        prepared = ensure_ollama(allow_download=allow_download)
    except Exception as exc:  # noqa: BLE001 - bootstrap не должен падать из-за этого
        _LOG.info(f"[bootstrap] ollama installer skip: {exc}")
        return []
    last_attempt["ollama"] = prepared
    if prepared.get("needs_user_action"):
        _LOG.info(f"[bootstrap] ollama: нужен шаг человека — {prepared.get('action')}")
    return ["ollama_installer"] if prepared.get("installer") else []


def pull_model() -> list[str]:
    """`ollama pull`, если модели нет; хвост ошибки — в лог, а не в пустоту."""
    try:
        listed = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=20)
        if OLLAMA_TEXT_MODEL.split(":")[0] in (listed.stdout or "").lower():
            _LOG.info(f"[bootstrap] ollama already has {OLLAMA_TEXT_MODEL}")
            return []
        _LOG.info(f"[bootstrap] ollama pull {OLLAMA_TEXT_MODEL} ...")
        pulled = subprocess.run(
            ["ollama", "pull", OLLAMA_TEXT_MODEL],
            capture_output=True, text=True, timeout=1800,
        )
        if pulled.returncode == 0:
            return ["ollama_qwen"]
        _LOG.warning(f"[bootstrap] ollama pull failed: {(pulled.stderr or '')[:300]}")
    except Exception as exc:  # noqa: BLE001 - отсутствие демона не ошибка bootstrap
        _LOG.debug(f"[bootstrap] ollama pull skip: {exc}")
    return []


def ensure_ollama_qwen(allow_download: bool | None = None) -> list[str]:
    """Идемпотентно: нет бинаря → установщик; есть → только `pull` модели."""
    from modules.llm.ollama_setup import ensure_ollama

    prepared = ensure_ollama(allow_download=allow_download)
    last_attempt["ollama"] = prepared
    if prepared.get("installer"):
        return ["ollama_installer"]
    if prepared.get("ok") and prepared.get("changed"):
        return ["ollama_qwen"]
    return []

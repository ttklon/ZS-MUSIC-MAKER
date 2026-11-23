# -*- coding: utf-8 -*-
"""modules/llm/ollama_setup.py — установка Ollama и текстовой модели из приложения.

Разрыв, который закрывает модуль: `app/core/bootstrap.py::_ensure_ollama_qwen()`
молча возвращал `[]`, если `ollama` не было в `PATH` («текст будет BLOCKED до её
установки»). Человек ставил программу на чистую Windows, нажимал «сделать хит» —
и получал `BLOCKED` без единой возможности это исправить из окна: установить
Ollama и `ollama pull` можно было только руками в консоли.

Что здесь есть:

* `install_report()` — без сети и без изменений на диске: что уже стоит, что
  мешает, какая команда нужна. Это то, что показывает окно.
* `ensure_ollama(allow_download=None)` — идемпотентная подготовка: `ollama pull`
  нужной модели, если демон есть; скачивание установщика и его запуск — только
  по явному согласию на сеть.

Честность важнее оптимизма: установщик Ollama — интерактивный MSI/EXE, поэтому
`ensure_ollama()` **скачивает** его и возвращает путь (`installer`), а не
утверждает, что «всё установилось»: запуск установщика требует прав
пользователя и подтверждения UAC, и это остаётся действием человека. Поле
`needs_user_action` с готовой командой — часть результата, а не побочный вывод.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
# Тег проверен: `qwen3.5:4b` в библиотеке Ollama нет, `ollama pull` на нём молча
# падал (см. `app/core/bootstrap.py`). `qwen3:4b` (~2.5 ГБ, Q4) работает на CPU.
DEFAULT_TEXT_MODEL = "qwen3:4b"

# Официальные адреса: только они, никакой «поиск установщика в интернете».
_INSTALLERS = {
    "Windows": "https://ollama.com/download/OllamaSetup.exe",
    "Darwin": "https://ollama.com/download/Ollama-darwin.zip",
}
_LINUX_HINT = "curl -fsSL https://ollama.com/install.sh | sh"


def text_model() -> str:
    """Модель, которую ставит приложение: `ZSMM_OLLAMA_PULL_MODEL` её меняет."""
    return os.environ.get("ZSMM_OLLAMA_PULL_MODEL", "").strip() or DEFAULT_TEXT_MODEL


def _ollama_bin() -> str | None:
    """Путь к `ollama`, если он есть в PATH (None — не установлена)."""
    return shutil.which("ollama")


def _daemon_models(base_url: str, timeout: float = 2.0) -> list[str] | None:
    """Имена моделей из `/api/tags`; `None` — демон не отвечает.

    Разница принципиальна: пустой список — «демон жив, моделей нет», `None` —
    «демона нет». Первое лечится `ollama pull`, второе — `ollama serve` или
    установкой, и путать их в отчёте нельзя.
    """
    try:
        import requests
    except ImportError:  # pragma: no cover - requests есть в requirements
        return None
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        if response.status_code != 200:
            return None
        payload = response.json()
    except Exception as exc:  # noqa: BLE001 - недоступность демона не исключение
        _LOGGER.debug("Ollama /api/tags failed: %s", exc)
        return None
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return None
    return [str(m.get("name") or m.get("model") or "") for m in models if isinstance(m, dict)]


def _has_model(models: list[str], wanted: str) -> bool:
    normalized = wanted.lower() if ":" in wanted else wanted.lower() + ":latest"
    return any(
        (name.lower() if ":" in name else name.lower() + ":latest") == normalized
        for name in models
    )


def install_report(base_url: str | None = None) -> dict[str, Any]:
    """Что с Ollama прямо сейчас — без сети и без записи на диск.

    Окно показывает это в «Диагностике», а `--ollama-setup` печатает как JSON.
    """
    base_url = base_url or os.environ.get("ZSMM_OLLAMA_URL", DEFAULT_OLLAMA_URL)
    wanted = text_model()
    binary = _ollama_bin()
    models = _daemon_models(base_url)

    if models is None:
        daemon = "down"
    elif not models:
        daemon = "up_no_models"
    else:
        daemon = "up"

    installed = bool(binary) or models is not None
    ready = bool(models) and _has_model(models, wanted)
    if ready:
        reason = ""
        action = ""
    elif not installed:
        reason = "Ollama не установлена: текст песен без неё невозможен"
        action = _install_hint()
    elif daemon == "down":
        reason = "Ollama установлена, но демон не отвечает на 127.0.0.1:11434"
        action = "ollama serve"
    elif not _has_model(models, wanted):
        reason = f"модели {wanted} нет на диске"
        action = f"ollama pull {wanted}"
    else:  # pragma: no cover - защитная ветка, ready уже True
        reason = "Ollama отвечает, но модель не выбрана"
        action = f"ollama pull {wanted}"

    return {
        "ok": ready,
        "ready": ready,
        "binary": binary,
        "base_url": base_url,
        "daemon": daemon,
        "models": models or [],
        "model": wanted,
        "has_model": bool(models) and _has_model(models, wanted),
        "reason": reason,
        "action": action,
        "platform": platform.system(),
    }


def _install_hint() -> str:
    system = platform.system()
    if system in _INSTALLERS:
        return f"скачать установщик: {_INSTALLERS[system]}"
    return f"установить: {_LINUX_HINT}"


def _download(url: str, target: Path, timeout: float = 900.0) -> dict[str, Any]:
    """Скачать один файл потоком; частичный файл удаляется, а не остаётся «битым»."""
    try:
        import requests
    except ImportError:  # pragma: no cover
        return {"ok": False, "reason": "requests_missing"}
    tmp = target.with_suffix(target.suffix + ".part")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=timeout) as response:
            if response.status_code != 200:
                return {"ok": False, "reason": f"http_{response.status_code}", "url": url}
            with tmp.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        handle.write(chunk)
        tmp.replace(target)
        return {"ok": True, "path": str(target), "bytes": target.stat().st_size}
    except Exception as exc:  # noqa: BLE001 - сеть падает по-разному
        try:
            tmp.unlink(missing_ok=True)
        except OSError as cleanup_error:
            _LOGGER.debug("частичный файл не удалён: %s", cleanup_error)
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}", "url": url}


def _pull_model(model: str, timeout: float = 1800.0, base_url: str | None = None) -> dict[str, Any]:
    """`ollama pull` с честным хвостом stderr — без него причина непонятна."""
    binary = _ollama_bin()
    if not binary:
        return {"ok": False, "reason": "ollama_not_installed"}
    try:
        done = subprocess.run(  # noqa: S603 - команда собрана из констант
            [binary, "pull", model],
            capture_output=True, text=True, timeout=timeout,
            env=dict(os.environ, OLLAMA_HOST=base_url or os.environ.get("ZSMM_OLLAMA_URL", DEFAULT_OLLAMA_URL)),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "timeout", "model": model}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}", "model": model}
    if done.returncode != 0:
        tail = ((done.stderr or "") + (done.stdout or "")).strip()[-400:]
        return {"ok": False, "reason": f"pull_failed: {tail or 'без вывода'}", "model": model}
    return {"ok": True, "model": model}


def ensure_ollama(
    allow_download: bool | None = None,
    base_url: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Подготовить Ollama и текстовую модель; идемпотентно.

    Порядок: уже готово → ничего не делаем; демон есть — только `pull`;
    установленный демон остановлен — запускаем локально; бинаря нет —
    скачиваем установщик (при разрешённой сети). Установка требует UAC.
    Уже скачанная модель работает без сети, включая запуск демона.

    `dry_run=True` ничего не скачивает и не запускает: возвращает тот же отчёт
    с планом. Это то, что безопасно звать из интерфейса при наведении.
    """
    report = install_report(base_url)
    if report["ready"]:
        return {**report, "ok": True, "changed": False, "reason": "", "action": ""}
    if dry_run:
        return {**report, "ok": False, "dry_run": True, "changed": False}

    if report["daemon"] == "down" and report.get("binary"):
        from modules.llm.ollama_daemon import start_local_daemon

        startup = start_local_daemon(report["binary"], report["base_url"], _daemon_models)
        if not startup["ok"]:
            return {**report, "ok": False, "changed": False, "startup": startup,
                    "reason": startup["reason"]}
        report = {**install_report(base_url), "startup": startup}
        if report["ready"]:
            return {**report, "ok": True, "changed": bool(startup.get("started"))}

    if allow_download is None:
        from app.core.net_policy import network_allowed

        allow_download = network_allowed()
    if not allow_download:
        return {
            **report, "ok": False, "changed": False,
            "reason": "network disabled: установка Ollama и загрузка модели требуют сети",
            "action": "включите «Разрешить приложению выходить в сеть» в «Диагностике»",
        }
    if report["daemon"] in ("up", "up_no_models"):
        return _pull_only(report, base_url)
    return _install_installer(report)


def _pull_only(report: dict[str, Any], base_url: str | None) -> dict[str, Any]:
    """Демон жив — нужен только `ollama pull`; состояние перечитывается заново."""
    pulled = _pull_model(report["model"], base_url=base_url) if base_url else _pull_model(report["model"])
    after = install_report(base_url)
    return {
        **after, "ok": bool(pulled.get("ok")) and after["ready"],
        "changed": bool(pulled.get("ok")),
        "pull": pulled,
        "reason": after["reason"] if pulled.get("ok") else str(pulled.get("reason")),
        "action": after["action"] if pulled.get("ok") else f"ollama pull {report['model']}",
    }


def _install_installer(report: dict[str, Any]) -> dict[str, Any]:
    """Демона нет: скачать официальный установщик и назвать шаг человека.

    Установщик не запускается сам: MSI/EXE просит UAC, и «тихая» установка из
    GUI выглядела бы как зависание приложения.
    """
    system = platform.system()
    url = _INSTALLERS.get(system)
    if not url:
        return {
            **report, "ok": False, "changed": False,
            "reason": "автоматическая установка Ollama поддерживается только на Windows и macOS",
            "action": _LINUX_HINT,
        }
    target = Path("models") / "installers" / Path(url).name
    downloaded = _download(url, target)
    if not downloaded.get("ok"):
        return {
            **report, "ok": False, "changed": False, "download": downloaded,
            "reason": f"установщик не скачан: {downloaded.get('reason')}",
            "action": _install_hint(),
        }
    if system != "Windows":  # pragma: no cover - macOS-ветка не проверяется в CI
        return {
            **report, "ok": False, "changed": True, "download": downloaded,
            "reason": "архив Ollama скачан: распакуйте и перенесите в /Applications",
            "action": f"open {downloaded['path']}",
            "needs_user_action": True,
        }
    return {
        **report, "ok": False, "changed": True, "download": downloaded,
        "reason": "установщик Ollama скачан; установка требует подтверждения Windows (UAC)",
        "action": f'start "" "{downloaded["path"]}"',
        "needs_user_action": True,
        "installer": downloaded["path"],
    }


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - тонкая обёртка
    """`python -m modules.llm.ollama_setup [--install]` — для отладки руками."""
    args = list(sys.argv[1:] if argv is None else argv)
    result = ensure_ollama(allow_download="--offline" not in args) if "--install" in args \
        else install_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

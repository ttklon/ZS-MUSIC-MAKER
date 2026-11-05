"""План 6.6: в коде не должно быть «немых» обработчиков исключений.

Гейт держит планку: любое `except: pass` снова сделает тест красным, а не
тихо спрячет поломку стадии.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_repository_has_no_silent_exception_handlers() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tools.audit_honesty", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout[-3000:] or result.stderr
    assert '"clean": true' in result.stdout


def test_audit_detects_a_silent_handler(tmp_path: Path) -> None:
    """Сам аудит обязан ловить проблему, иначе это фикция, а не гейт."""
    sys.path.insert(0, str(ROOT))
    from tools.audit_honesty import audit

    sample = tmp_path / "app" / "bad.py"
    sample.parent.mkdir(parents=True)
    sample.write_text(
        "def f():\n    try:\n        return 1\n    except Exception:\n        pass\n",
        encoding="utf-8",
    )

    report = audit(roots=[tmp_path / "app"])

    assert len(report.findings) == 1
    assert report.findings[0].kind == "silent_except"


def test_audit_accepts_a_logged_handler(tmp_path: Path) -> None:
    sys.path.insert(0, str(ROOT))
    from tools.audit_honesty import audit

    sample = tmp_path / "app" / "good.py"
    sample.parent.mkdir(parents=True)
    sample.write_text(
        "import logging\n\n"
        "def f():\n"
        "    try:\n"
        "        return 1\n"
        "    except Exception:\n"
        '        logging.getLogger(__name__).debug("ignored", exc_info=True)\n',
        encoding="utf-8",
    )

    report = audit(roots=[tmp_path / "app"])

    assert report.findings == []

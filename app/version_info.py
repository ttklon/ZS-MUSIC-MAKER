# -*- coding: utf-8 -*-
"""
ZS Music Maker — app/version_info.py (v39.5, ШАГ 009 PLAN_v39)
========================================================================
Единый источник версии: читает version.json ПО ОДНОМУ РАЗУ при импорте.
pyproject.toml ссылается на этот атрибут через [tool.setuptools.dynamic],
main.py уже читает version.json напрямую — расхождений быть не может.
"""
import json
from pathlib import Path

__version__: str = json.loads(
    (Path(__file__).resolve().parents[1] / "version.json").read_text(encoding="utf-8")
)["version"]

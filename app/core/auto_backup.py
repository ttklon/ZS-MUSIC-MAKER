# -*- coding: utf-8 -*-
"""
ZS Music Maker — auto_backup.py (GOD MODE V7)
========================================================================
Автоматическое архивирование результатов сессии в ZIP-пакеты.
Предотвращает потерю данных при сбоях.
"""

import os
import zipfile
from pathlib import Path
import logging

logger = logging.getLogger("AutoBackup")

def backup_output_folder(project_id: str) -> str:
    output_dir = Path("output") / project_id
    if not output_dir.exists():
        return ""
        
    backup_path = Path("output") / f"{project_id}_backup.zip"
    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file.endswith(".zip"):
                        continue
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(output_dir.parent)
                    zipf.write(file_path, arcname)
        logger.info(f"Auto-backup created successfully: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.warning(f"Auto-backup failed: {e}")
        return ""

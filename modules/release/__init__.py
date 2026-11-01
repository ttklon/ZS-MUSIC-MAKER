# -*- coding: utf-8 -*-
"""
modules/release — релизный пакет: экспорт, полный пакет, площадки.

Раскладка:
* `export`   — `export_release()`: файлы + манифест SHA-256 + ZIP;
* `pack`     — `build_pack()`: мастер-стенды, стемы, тексты, отчёт, площадки;
* `channels` — `build_all_channels()`: Spotify / Яндекс-VK / TikTok / YouTube / Shazam.

Всё возвращает dict с `ok` и честным `reason`; ни один шаг не притворяется
успешным, если файла нет.
"""

from modules.release.channels import (  # noqa: F401
    CHANNELS,
    build_all_channels,
    build_channel_package,
)
from modules.release.export import (  # noqa: F401
    RELEASES_DIR,
    export_release,
    refresh_zip,
    sha256_file,
)
from modules.release.pack import build_pack, capability_report  # noqa: F401

__all__ = [
    "CHANNELS",
    "RELEASES_DIR",
    "build_all_channels",
    "build_channel_package",
    "build_pack",
    "capability_report",
    "export_release",
    "refresh_zip",
    "sha256_file",
]

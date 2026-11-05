# -*- coding: utf-8 -*-
"""modules/mastering — единственный мастеринг проекта (план 4.6).

Цепочка: коррекция тона под стенд → двухполосная компрессия → look-ahead
лимитер с потолком −1 dBTP → сходимость по LUFS. Всё измеряется настоящими
метриками (`modules.dsp.metrics`), а не «на слух»:

* true peak — 4× oversample (≤ −1.0 dBTP на каждом стенде);
* LUFS — pyloudnorm (ITU-R BS.1770), с явным статусом, если его нет;
* клиппинг — 0 сэмплов; корреляция и потеря в моно — гейты §7.2.

Устройство пакета (раньше это был один файл на 632 строки):

* `targets.py` — цели и коридоры по стендам;
* `loudness.py` — сходимость громкости (бисекция + доводки);
* `chain.py` — цепь одного стенда и `master_one`;
* `normalize.py` — добить громкость готового мастера;
* `stands.py` — все стенды, параллельно и с отчётом по гейтам.

`master_all_stands` пишет `master_<stand>.wav` и возвращает отчёт с гейтами
по каждому стенду. Недостижимая цель (например, клуб −8.5 LUFS на очень
динамичном миксе) не выдаётся за успех: `gates[lufs] = False` и в отчёте
стоит фактическое значение.
"""

from __future__ import annotations

from modules.mastering.chain import master_one  # noqa: F401 - публичный реэкспорт
from modules.mastering.loudness import _converge_loudness, _render_candidate  # noqa: F401
from modules.mastering.normalize import normalize_master_loudness  # noqa: F401
from modules.mastering.stands import (  # noqa: F401 - публичный реэкспорт
    _master_stand_job,
    _run_stands,
    _stand_workers,
    master_all_stands,
)
from modules.mastering.targets import (  # noqa: F401 - публичный реэкспорт
    ALL_STANDS,
    CORRELATION_RANGE,
    CREST_RANGE,
    DEFAULT_CORRELATION,
    DEFAULT_CREST,
    LUFS_TOLERANCE,
    STAND_EQ,
    STAND_TARGET_DBFS,
    STAND_TARGET_LUFS,
    TRUE_PEAK_CEILING,
)

__all__ = [
    "ALL_STANDS",
    "STAND_TARGET_LUFS",
    "master_all_stands",
    "master_one",
    "normalize_master_loudness",
]


def _cli(argv: list[str]) -> int:
    import json

    if len(argv) < 3:
        print("usage: python -m modules.mastering <mix.wav> <out_dir> [stand]")
        return 2
    mix_wav, out_dir = argv[1], argv[2]
    stands = [argv[3]] if len(argv) > 3 else None
    result = master_all_stands(mix_wav, out_dir, stands=stands)
    print(json.dumps(result.get("summary", result), ensure_ascii=False, indent=2))
    return 0 if result.get("summary", {}).get("gates_passed") else 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(_cli(sys.argv))

# -*- coding: utf-8 -*-
"""tools/import_samples.py — собрать сэмпловый банк из CC0-источников.

Скрипт делает ровно одну вещь: берёт курированный набор one-shot'ов из
скачанных паков, приводит их к единому виду (моно, 44.1 кГц, PCM-16),
считает SHA-256 и пишет `data/samples/manifest.json` вместе с атрибуцией.

Курирование — в коде, а не «на глаз»: так банк воспроизводим. Источники:

* `tidalcycles/sounds-tr808-fischer` — реальные удары Roland TR-808,
  сведённые Майклом Фишером, CC0-1.0. Имена файлов кодируют положение ручек:
  `BD<tone><decay>.WAV`, где `00` = минимум, `10` = максимум.
* `Boochi44/free-drum-samples` — три набора (hard trap / bounce / vintage),
  CC0-1.0, часть звуков — производные от того же набора TR-808.

Оба источника без требования атрибуции, но она всё равно пишется в
`data/samples/ATTRIBUTION.md` — провенанс должен быть проверяемым.

Запуск (нужны скачанные паки рядом):

    python tools/import_samples.py --source output/_samples_src
    python tools/import_samples.py --source output/_samples_src --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SAMPLES_DIR = ROOT / "data" / "samples"
MANIFEST_PATH = SAMPLES_DIR / "manifest.json"
ATTRIBUTION_PATH = SAMPLES_DIR / "ATTRIBUTION.md"
TARGET_SR = 44_100

TR808 = "tidalcycles/sounds-tr808-fischer"
TR808_URL = "https://github.com/tidalcycles/sounds-tr808-fischer"
BOOCHI = "Boochi44/free-drum-samples"
BOOCHI_URL = "https://github.com/Boochi44/free-drum-samples"


@dataclass(frozen=True)
class Pick:
    """Один сэмпл: откуда берём, куда кладём и в какую группу."""

    instrument: str
    source: str  # путь относительно --source
    target: str  # путь относительно data/samples
    pack: str  # TR808 | BOOCHI
    round_robin: int
    note: str = ""


# Курирование: 6 инструментов, которые реально использует бит-движок
# (`modules/beat/voices.py`), плюс разные характеры — 808-бочка TR-808,
# жёсткий трэп, круглый bounce, лоу-фай винтаж.
PICKS: tuple[Pick, ...] = (
    # --- kick ---------------------------------------------------------
    Pick("kick", "bd8/BD0050.WAV", "kick/808-bd-tone0-decay50.wav", TR808, 0, "средний распад, самый универсальный"),
    Pick("kick", "bd8/BD0025.WAV", "kick/808-bd-tone0-decay25.wav", TR808, 1, "короткий панч"),
    Pick("kick", "bd8/BD2550.WAV", "kick/808-bd-tone25-decay50.wav", TR808, 2, "выше по тону — для быстрых битов"),
    Pick("kick", "drum-samples/01-hard-trap/kicks/hard-kick-01.wav", "kick/hard-trap-01.wav", BOOCHI, 3),
    Pick("kick", "drum-samples/01-hard-trap/kicks/hard-kick-02.wav", "kick/hard-trap-02.wav", BOOCHI, 4),
    Pick("kick", "drum-samples/02-bounce/kicks/bounce-kick-01.wav", "kick/bounce-01.wav", BOOCHI, 5),
    Pick("kick", "drum-samples/02-bounce/kicks/bounce-kick-03.wav", "kick/bounce-03.wav", BOOCHI, 6),
    Pick("kick", "drum-samples/03-soulful-vintage/kicks/vintage-kick-01.wav", "kick/vintage-01.wav", BOOCHI, 7),
    Pick("kick", "drum-samples/03-soulful-vintage/kicks/vintage-kick-02.wav", "kick/vintage-02.wav", BOOCHI, 8),
    # --- snare --------------------------------------------------------
    Pick("snare", "sd8/SD7550.WAV", "snare/808-sd-crisp.wav", TR808, 0, "ручки на максимум — самый «острый»"),
    Pick("snare", "sd8/SD5010.WAV", "snare/808-sd-roomy.wav", TR808, 1),
    Pick("snare", "sd8/SD2500.WAV", "snare/808-sd-dull.wav", TR808, 2),
    Pick("snare", "drum-samples/01-hard-trap/snares/hard-snare-01.wav", "snare/hard-trap-01.wav", BOOCHI, 3),
    Pick("snare", "drum-samples/01-hard-trap/snares/hard-snare-02.wav", "snare/hard-trap-02.wav", BOOCHI, 4),
    Pick("snare", "drum-samples/02-bounce/snares/bounce-snare-01.wav", "snare/bounce-01.wav", BOOCHI, 5),
    Pick("snare", "drum-samples/02-bounce/snares/bounce-snare-03.wav", "snare/bounce-03.wav", BOOCHI, 6),
    Pick("snare", "drum-samples/03-soulful-vintage/snares/vintage-snare-01.wav", "snare/vintage-01.wav", BOOCHI, 7),
    Pick("snare", "drum-samples/03-soulful-vintage/snares/vintage-snare-02.wav", "snare/vintage-02.wav", BOOCHI, 8),
    # --- clap ---------------------------------------------------------
    Pick("clap", "cp8/CP.WAV", "clap/808-cp.wav", TR808, 0),
    Pick("clap", "drum-samples/01-hard-trap/claps/clap-01.wav", "clap/hard-trap-01.wav", BOOCHI, 1),
    Pick("clap", "drum-samples/02-bounce/claps/clap-01.wav", "clap/bounce-01.wav", BOOCHI, 2),
    Pick("clap", "drum-samples/03-soulful-vintage/claps/vintage-clap-01.wav", "clap/vintage-01.wav", BOOCHI, 3),
    # --- hat ----------------------------------------------------------
    Pick("hat", "ch8/CH.WAV", "hat/808-ch.wav", TR808, 0, "closed hat с реальной машины"),
    Pick("hat", "drum-samples/01-hard-trap/hi-hats/hi-hat-closed-01.wav", "hat/hard-trap-01.wav", BOOCHI, 1),
    Pick("hat", "drum-samples/03-soulful-vintage/hi-hats/hi-hat-closed-01.wav", "hat/vintage-01.wav", BOOCHI, 2),
    # --- open hat -----------------------------------------------------
    Pick("open_hat", "oh8/OH00.WAV", "open_hat/808-oh-short.wav", TR808, 0),
    Pick("open_hat", "oh8/OH25.WAV", "open_hat/808-oh-mid.wav", TR808, 1),
    Pick("open_hat", "oh8/OH50.WAV", "open_hat/808-oh-long.wav", TR808, 2),
    Pick("open_hat", "drum-samples/02-bounce/open-hats/open-hat-01.wav", "open_hat/bounce-01.wav", BOOCHI, 3),
    # --- 808 ----------------------------------------------------------
    Pick("808", "bd8/BD0010.WAV", "808/808-sub-long.wav", TR808, 0, "распад на максимум — классический 808-бас"),
    Pick("808", "bd8/BD2510.WAV", "808/808-sub-high.wav", TR808, 1),
    Pick("808", "drum-samples/01-hard-trap/808s/808-bass-sub.wav", "808/hard-trap-sub.wav", BOOCHI, 2),
    Pick("808", "drum-samples/01-hard-trap/808s/808-bass-dist.wav", "808/hard-trap-dist.wav", BOOCHI, 3),
    Pick("808", "drum-samples/02-bounce/808s/808-bass-long.wav", "808/bounce-long.wav", BOOCHI, 4),
    Pick("808", "drum-samples/03-soulful-vintage/808s/808-bass-lofi.wav", "808/vintage-lofi.wav", BOOCHI, 5),
)

# Инструменты, которым нужна подстройка под тонику трека (низ «спорит» иначе).
TUNED = ("kick", "808")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fundamental_hz(mono: np.ndarray, sample_rate: int) -> float:
    """Основной тон низкого удара — по хвосту, а не по атаке.

    У кика и 808 высота слухом берётся из затухающего «тела»: атака — это
    клик с широким спектром. Поэтому берём последнюю треть сэмпла, где
    остался почти чистый синус, и ищем максимум спектра в 25…160 Гц с
    параболической интерполяцией по соседним бинам.
    """
    tail = mono[int(len(mono) * 0.65) :] if len(mono) > 2048 else mono
    if tail.size < 512:
        return 0.0
    window = tail * np.hanning(tail.size)
    spectrum = np.abs(np.fft.rfft(window, n=1 << 15))
    freqs = np.fft.rfftfreq(1 << 15, d=1.0 / sample_rate)
    band = np.where((freqs >= 25.0) & (freqs <= 160.0))[0]
    if band.size == 0:
        return 0.0
    peak = band[int(np.argmax(spectrum[band]))]
    if 0 < peak < len(spectrum) - 1:
        alpha, beta, gamma = spectrum[peak - 1], spectrum[peak], spectrum[peak + 1]
        denominator = alpha - 2.0 * beta + gamma
        shift = 0.5 * (alpha - gamma) / denominator if denominator else 0.0
        shift = float(np.clip(shift, -0.5, 0.5))
    else:
        shift = 0.0
    return float(round(freqs[peak] + shift * (freqs[1] - freqs[0]), 1))


def prepare(source: Path, target: Path) -> dict[str, float]:
    """Привести one-shot к моно 44.1 кГц PCM-16 и вернуть его метрики."""
    data, rate = sf.read(str(source), always_2d=True, dtype="float64")
    mono = data.mean(axis=1)
    if rate != TARGET_SR and mono.size > 1:
        positions = np.linspace(0.0, mono.size - 1.0, int(round(mono.size * TARGET_SR / rate)))
        mono = np.interp(positions, np.arange(mono.size), mono)
        rate = TARGET_SR
    peak = float(np.max(np.abs(mono))) or 1.0
    # Оставляем запас −1 dBFS: банк не должен быть «на клиппинге».
    mono = (mono / peak * 0.891).astype(np.float32)
    # Хвосты ниже −70 dBFS — это уже шум квантования; обрезаем, чтобы
    # 808-бочка не тянула за собой секунду тишины.
    threshold = 10 ** (-70.0 / 20.0)
    loud = np.where(np.abs(mono) > threshold)[0]
    if loud.size:
        end = min(mono.size, int(loud[-1]) + int(0.01 * rate))
        mono = mono[:end]
    target.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(target), mono, rate, subtype="PCM_16")
    return {
        "duration_sec": round(float(mono.size) / rate, 3),
        "fundamental_hz": fundamental_hz(mono.astype(np.float64), rate),
    }


def build_manifest(source: Path, dry_run: bool = False) -> dict:
    """Скопировать выбранные сэмплы и собрать манифест банка."""
    instruments: dict[str, list[dict]] = {}
    missing: list[str] = []
    replaced: list[str] = []
    seen_hashes: dict[str, str] = {}
    for pick in PICKS:
        source_path = source / pick.source
        if not source_path.is_file():
            missing.append(str(source_path.relative_to(source)))
            continue
        digest = _sha256(source_path)
        if digest in seen_hashes:
            replaced.append(f"{pick.target} (дубль {seen_hashes[digest]})")
            continue
        seen_hashes[digest] = pick.target
        target_path = SAMPLES_DIR / pick.target
        stats = {"duration_sec": 0.0, "fundamental_hz": 0.0}
        if not dry_run:
            stats = prepare(source_path, target_path)
        entry = {
            "file": pick.target,
            "license": "CC0-1.0",
            "source": TR808_URL if pick.pack == TR808 else BOOCHI_URL,
            "origin": f"{pick.pack}:{pick.source}",
            # TR-808 не имеет velocity-слоёв: громкость удара задаёт движок
            # (`voice * velocity`), а round-robin — это реальные разные удары.
            "velocity": 1.0,
            "round_robin": pick.round_robin,
            "sha256": "" if dry_run else _sha256(target_path),
            "duration_sec": stats["duration_sec"] or None,
            "tuning_hz": stats["fundamental_hz"] if pick.instrument in TUNED else None,
            "note": pick.note or None,
        }
        if entry["tuning_hz"] is None:
            entry.pop("tuning_hz")
        if entry["duration_sec"] is None:
            entry.pop("duration_sec")
        if entry["note"] is None:
            entry.pop("note")
        instruments.setdefault(pick.instrument, []).append(entry)

    manifest = {
        "schema": "zsmm.sample-bank.v1",
        "note": (
            "CC0 one-shots (Roland TR-808 sample set by Michael Fischer и три "
            "набора Boochi44/free-drum-samples). Собрано tools/import_samples.py; "
            "пересборка детерминированная — не редактируйте вручную."
        ),
        "velocity_mode": "engine-gain",
        "instruments": {name: rows for name, rows in sorted(instruments.items())},
    }
    return {"manifest": manifest, "missing": missing, "skipped_duplicates": replaced}


def write_attribution(manifest: dict) -> str:
    """Текст атрибуции: лицензия, источник, что именно взято."""
    lines = [
        "# Сэмплы: происхождение и лицензии",
        "",
        "Все файлы в этом каталоге — **CC0-1.0** (public domain): их можно",
        "использовать в коммерческих релизах без разрешения и без указания",
        "автора. Атрибуция ниже — не обязанность, а проверяемый провенанс:",
        "по нему видно, откуда взялся каждый удар.",
        "",
        "| Источник | Лицензия | Что взято |",
        "|---|---|---|",
        f"| [Michael Fischer, TR-808 Sound Sample Set 1.0.0]({TR808_URL}) | CC0-1.0 | удары TR-808 (бочка, снейр, клэп, хэты, 808-бас) |",
        f"| [Boochi44/free-drum-samples]({BOOCHI_URL}) | CC0-1.0 | наборы hard trap / bounce / vintage |",
        "",
        "Набор Boochi44 частично произведён от того же TR-808-набора Фишера",
        "(CC0). Файлы приведены к моно / 44.1 кГц / PCM-16 и нормализованы",
        "до −1 dBFS скриптом `tools/import_samples.py`.",
        "",
        "## Файлы",
        "",
        "| Файл | Инструмент | Источник |",
        "|---|---|---|",
    ]
    for instrument, rows in manifest["instruments"].items():
        for row in rows:
            lines.append(f"| `{row['file']}` | {instrument} | `{row.get('origin', '')}` |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Импорт CC0-сэмплов в data/samples")
    parser.add_argument("--source", required=True, help="каталог со скачанными паками")
    parser.add_argument("--dry-run", action="store_true", help="только показать, что будет сделано")
    args = parser.parse_args(argv)

    source = Path(args.source)
    if not source.is_dir():
        print(f"[samples] нет каталога {source}", file=sys.stderr)
        return 2

    result = build_manifest(source, dry_run=args.dry_run)
    manifest = result["manifest"]
    total = sum(len(rows) for rows in manifest["instruments"].values())
    for name, rows in manifest["instruments"].items():
        print(f"[samples] {name:9} {len(rows):2} шт.")
    print(f"[samples] всего {total}; дублей отброшено: {len(result['skipped_duplicates'])}")
    if result["missing"]:
        print(f"[samples] не найдено ({len(result['missing'])}): {result['missing']}", file=sys.stderr)
    if args.dry_run:
        return 0 if not result["missing"] else 1

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ATTRIBUTION_PATH.write_text(write_attribution(manifest), encoding="utf-8")
    print(f"[samples] записан {MANIFEST_PATH.relative_to(ROOT)} и ATTRIBUTION.md")
    return 0 if not result["missing"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

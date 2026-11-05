# -*- coding: utf-8 -*-
"""
app/audio/samples.py — сэмпловый банк: манифест, velocity-слои, round-robin.

Живой one-shot всегда лучше синтеза, поэтому банк — фундамент качества
(Этап 4.1). Модуль отвечает на три вопроса честно:

1. **Что есть?** `load_bank()` читает `data/samples/manifest.json` и отдаёт
   инструменты с файлами, лицензией, источником и SHA-256.
2. **Можно ли брать?** `license_of()` — только CC0/CC-BY/public-domain
   проходят; всё остальное помечается `REJECTED` и в бит не попадает.
3. **Есть ли чем заменить синтез?** `capability()` — если банк пуст, статус
   `FALLBACK`, и вызывающий код обязан отчитаться об этом, а не делать вид.

Формат манифеста (`data/samples/manifest.json`):

```json
{
  "schema": "zsmm.sample-bank.v1",
  "instruments": {
    "kick": [
      {"file": "kick/kick_01.wav", "license": "CC0-1.0",
       "source": "https://...", "sha256": "...", "velocity": 0.9,
       "round_robin": 0, "tuning_hz": 55.0}
    ]
  }
}
```
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = ROOT / "data" / "samples"
MANIFEST_PATH = SAMPLES_DIR / "manifest.json"
SCHEMA = "zsmm.sample-bank.v1"

# Лицензии, которые можно класть в коммерческий трек без разрешения автора.
ALLOWED_LICENSES = ("CC0-1.0", "CC0", "PUBLIC-DOMAIN", "CC-BY-4.0", "CC-BY-3.0")
INSTRUMENTS = ("kick", "snare", "clap", "hat", "open_hat", "808", "bass", "melody", "fx", "foley")

try:
    import numpy as np

    HAS_NUMPY = True
except Exception:  # pragma: no cover
    HAS_NUMPY = False

try:
    import soundfile as sf

    HAS_SOUNDFILE = True
except Exception:  # pragma: no cover
    sf = None
    HAS_SOUNDFILE = False


@dataclass
class SampleEntry:
    instrument: str
    path: Path
    license: str
    source: str
    sha256: str = ""
    velocity: float = 1.0
    round_robin: int = 0
    tuning_hz: float = 0.0
    problems: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.license.upper() in ALLOWED_LICENSES and not self.problems


@dataclass
class SampleBank:
    entries: dict[str, list[SampleEntry]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    # Как банк задаёт громкость удара:
    #   "layers"      — отдельные записи на каждый уровень (акустика);
    #   "engine-gain" — одна запись, громкость считает движок (драм-машина).
    velocity_mode: str = "layers"

    def usable(self, instrument: str) -> list[SampleEntry]:
        return [entry for entry in self.entries.get(instrument, []) if entry.allowed]

    def instrument_names(self) -> list[str]:
        return sorted(name for name in self.entries if self.usable(name))

    @property
    def empty(self) -> bool:
        return not any(self.usable(name) for name in self.entries)

    def choose(self, instrument: str, rng: Any = None, velocity: float = 1.0) -> SampleEntry | None:
        """Выбор сэмпла: ближайший velocity-слой, затем round-robin."""
        candidates = self.usable(instrument)
        if not candidates:
            return None
        layers = sorted({round(entry.velocity, 3) for entry in candidates})
        nearest = min(layers, key=lambda layer: abs(layer - velocity))
        layer_entries = [entry for entry in candidates if round(entry.velocity, 3) == nearest]
        if rng is None or len(layer_entries) == 1:
            return sorted(layer_entries, key=lambda entry: entry.round_robin)[0]
        return layer_entries[int(rng.integers(0, len(layer_entries)))]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(payload: Any) -> list[str]:
    """Проверяет структуру манифеста; возвращает список проблем (пусто = ок)."""
    problems: list[str] = []
    if not isinstance(payload, dict):
        return ["manifest must be a JSON object"]
    if payload.get("schema") != SCHEMA:
        problems.append(f"schema must be '{SCHEMA}', got {payload.get('schema')!r}")
    instruments = payload.get("instruments")
    if not isinstance(instruments, dict):
        return problems + ["'instruments' must be an object"]
    for name, rows in instruments.items():
        if name not in INSTRUMENTS:
            problems.append(f"unknown instrument '{name}'")
        if not isinstance(rows, list):
            problems.append(f"'{name}' must be a list")
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or not row.get("file"):
                problems.append(f"{name}[{index}] has no 'file'")
                continue
            if not row.get("license"):
                problems.append(f"{name}[{index}] has no 'license'")
            if not row.get("source"):
                problems.append(f"{name}[{index}] has no 'source'")
    return problems


def load_bank(manifest_path: str | Path | None = None, verify_hash: bool = False) -> SampleBank:
    """Читает банк с диска; отсутствующий манифест — пустой банк, не ошибка."""
    path = Path(manifest_path) if manifest_path else MANIFEST_PATH
    bank = SampleBank()
    if not path.exists():
        bank.warnings.append(f"no sample manifest at {path} — synthesised FALLBACK will be used")
        return bank
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        bank.warnings.append(f"manifest unreadable: {type(error).__name__}: {error}")
        return bank

    base = path.parent
    for problem in validate_manifest(payload):
        bank.warnings.append(problem)
    if not isinstance(payload, dict) or not isinstance(payload.get("instruments"), dict):
        return bank

    mode = str(payload.get("velocity_mode") or "layers").strip().lower()
    bank.velocity_mode = mode if mode in ("layers", "engine-gain") else "layers"

    for instrument, rows in (payload.get("instruments") or {}).items():
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict) or not row.get("file"):
                continue
            sample_path = base / str(row["file"])
            entry = SampleEntry(
                instrument=instrument,
                path=sample_path,
                license=str(row.get("license") or ""),
                source=str(row.get("source") or ""),
                sha256=str(row.get("sha256") or ""),
                velocity=float(row.get("velocity") or 1.0),
                round_robin=int(row.get("round_robin") or 0),
                tuning_hz=float(row.get("tuning_hz") or 0.0),
            )
            if not sample_path.is_file():
                entry.problems.append("file missing")
            elif entry.license.upper() not in ALLOWED_LICENSES:
                entry.problems.append(f"license '{entry.license}' is not cleared for release")
            elif not entry.source.strip():
                entry.problems.append("source missing")
            elif verify_hash and entry.sha256 and _sha256(sample_path) != entry.sha256:
                entry.problems.append("sha256 mismatch")
            bank.entries.setdefault(instrument, []).append(entry)
    return bank


def read_sample(path: str | Path, sample_rate: int = 44_100) -> "Any | None":
    """Читает сэмпл в моно float32; ресемплинг — линейной интерполяцией."""
    if not (HAS_NUMPY and HAS_SOUNDFILE):
        return None
    try:
        data, rate = sf.read(str(path), always_2d=True, dtype="float32")
    except Exception:
        return None
    mono = data.mean(axis=1)
    if rate != sample_rate and len(mono) > 1:
        target = int(round(len(mono) * sample_rate / rate))
        positions = np.linspace(0.0, len(mono) - 1.0, target)
        mono = np.interp(positions, np.arange(len(mono)), mono).astype(np.float32)
    return mono


def pitch_shift(signal: "Any", semitones: float, sample_rate: int = 44_100) -> "Any":
    """Питч-шифт пересчётом скорости (без сохранения длины).

    Для one-shot'ов это именно то, что нужно: кик, ускоренный на 2 полутона,
    становится короче и ярче — как на реальной драм-машине.
    """
    if not HAS_NUMPY or semitones == 0 or signal is None or len(signal) < 2:
        return signal
    ratio = 2.0 ** (semitones / 12.0)
    target = max(2, int(round(len(signal) / ratio)))
    positions = np.linspace(0.0, len(signal) - 1.0, target)
    return np.interp(positions, np.arange(len(signal)), signal).astype(np.float32)


def time_stretch(signal: "Any", factor: float) -> "Any":
    """Изменение длины без сдвига высоты (гранулярно, детерминированно)."""
    if not HAS_NUMPY or factor <= 0 or signal is None or len(signal) < 64:
        return signal
    if abs(factor - 1.0) < 0.01:
        return signal
    grain = max(32, int(len(signal) * 0.05))
    hop_out = max(1, int(grain * 0.5))
    target = max(grain, int(len(signal) * factor))
    out = np.zeros(target + grain, dtype=np.float32)
    window = np.hanning(grain).astype(np.float32)
    read = 0.0
    write = 0
    while write + grain < len(out):
        start = int(read)
        chunk = signal[start : start + grain]
        if len(chunk) < grain:
            chunk = np.pad(chunk, (0, grain - len(chunk)))
        out[write : write + grain] += chunk * window
        read += hop_out / max(factor, 1e-6)
        write += hop_out
        if read >= len(signal) - grain:
            break
    return out[:target]


def capability(bank: SampleBank | None = None) -> dict[str, Any]:
    """Честный отчёт: есть ли банк, сколько инструментов, что синтезируется."""
    bank = bank or load_bank()
    names = bank.instrument_names()
    total = sum(len(bank.usable(name)) for name in bank.entries)
    covered = [name for name in INSTRUMENTS if name in names]
    fallback = [name for name in INSTRUMENTS if name not in names]
    return {
        "status": "REAL_PASS" if len(covered) >= 6 else ("PARTIAL" if covered else "FALLBACK"),
        "engine": "app.audio.samples",
        "numpy_soundfile": HAS_NUMPY and HAS_SOUNDFILE,
        "instruments_with_samples": covered,
        "instruments_on_synth": fallback,
        "total_samples": total,
        "warnings": list(bank.warnings),
    }


def iter_entries(bank: SampleBank) -> Iterable[SampleEntry]:
    for rows in bank.entries.values():
        yield from rows


if __name__ == "__main__":  # pragma: no cover - ручная проверка
    print(json.dumps(capability(), ensure_ascii=False, indent=2))

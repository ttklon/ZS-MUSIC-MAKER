# -*- coding: utf-8 -*-
"""Порт аудио-движка в окно: сверка с Python-версией, а не «на глаз».

Две вещи, которые нельзя проверить внутри `node --test`:

* таблицы ритма и акцентов в `desktop/src/core/audio/pattern-data.js` должны
  совпадать с `modules/beat/patterns.py` — иначе окно и CLI начнут играть
  разные грувы, и заметить это можно только на слух;
* рендер бита в JS должен давать непустой, не перегруженный WAV, который
  Python читает как обычный звук.

Тесты не требуют Electron и не запускают окно: только Node.js, как и
`test_desktop_shell.py`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="Node.js не установлен в окружении")


def _node(script: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        [NODE, "-e", script],
        cwd=DESKTOP,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def test_pattern_tables_match_python_source() -> None:
    """Ритм и акценты в JS-движке совпадают с Python один в один."""
    from modules.beat import patterns as py_patterns

    script = """
    const p = require('./src/core/audio/patterns');
    const data = require('./src/core/audio/pattern-data');
    const families = p.families();
    const out = {
      families,
      presets: Object.fromEntries(families.map((f) => [f, p.slotPresetForGenre(f)])),
      velocity: Object.fromEntries(families.map((f) => [f, p.velocityMapForGenre(f)])),
      rules: data.FAMILY_RULES,
      legacy: p.LEGACY_PATTERN,
    };
    process.stdout.write(JSON.stringify(out));
    """
    result = _node(script)
    assert result.returncode == 0, result.stderr
    js = json.loads(result.stdout)

    py_families = sorted(py_patterns.PATTERN_FAMILIES)
    assert js["families"] == py_families, "набор семейств разошёлся с Python"

    for family in py_families:
        js_preset = js["presets"][family]
        for slot in ("kick", "snare", "hat", "bass", "melody"):
            expected = [int(bool(value)) for value in py_patterns.PATTERN_FAMILIES[family][slot]]
            assert js_preset[slot] == expected, f"{family}/{slot}: шаги разошлись с Python"

        js_velocity = js["velocity"][family]
        expected_velocity = py_patterns.velocity_map_for_genre(family)
        for slot, values in expected_velocity.items():
            assert len(js_velocity[slot]) == len(values), f"{family}/{slot}: длина карты"
            for index, (got, want) in enumerate(zip(js_velocity[slot], values)):
                assert abs(got - float(want)) < 1e-9, (
                    f"{family}/{slot}[{index}]: {got} != {want}"
                )

    legacy = py_patterns.LEGACY_SLOT_PRESET
    for slot in ("kick", "snare", "hat", "bass", "melody"):
        assert js["legacy"][slot] == [int(bool(value)) for value in legacy[slot]], f"legacy/{slot}"


def test_family_projection_matches_python_for_whole_catalog() -> None:
    """Каждый жанр каталога проецируется на то же семейство, что в Python."""
    import json as js_json

    from modules.beat import patterns as py_patterns

    # Каталог — словарь категорий со списками строк, а пресеты лежат отдельными
    # JSON: проверяем оба источника, потому что окно читает именно их.
    catalog = js_json.loads((ROOT / "config" / "genres_100.json").read_text(encoding="utf-8"))
    names = [name for values in catalog.values() for name in values if isinstance(name, str)]
    for preset_path in sorted((ROOT / "data" / "genre_presets").glob("*.json")):
        names.append(preset_path.stem.replace("_", " "))
        try:
            preset = js_json.loads(preset_path.read_text(encoding="utf-8"))
        except js_json.JSONDecodeError:  # pragma: no cover - битый пресет не наша тема
            continue
        if isinstance(preset, dict) and isinstance(preset.get("genre"), str):
            names.append(preset["genre"])
    names = sorted({name for name in names if name})
    assert len(names) >= 100, f"жанров для сверки слишком мало: {len(names)}"

    script = """
    const p = require('./src/core/audio/patterns');
    const names = JSON.parse(process.argv[1]);
    process.stdout.write(JSON.stringify(names.map((n) => p.familyForGenre(n))));
    """
    result = subprocess.run(
        [NODE, "-e", script, js_json.dumps(names)],
        cwd=DESKTOP,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    js_families = js_json.loads(result.stdout)
    expected = [py_patterns.family_for_genre(name) for name in names]
    assert js_families == expected, "проекция жанров на семейства разошлась с Python"


def test_js_engine_renders_playable_wav(tmp_path: Path) -> None:
    """Движок окна пишет WAV, который читается как звук и не перегружен."""
    np = pytest.importorskip("numpy")
    sf = pytest.importorskip("soundfile")

    target = tmp_path / "beat.wav"
    script = f"""
    const fs = require('node:fs');
    const {{ renderBeat }} = require('./src/core/audio/engine');
    const {{ wav, report }} = renderBeat({{ bpm: 140, genre: 'phonk', seed: 7, durationSec: 8 }});
    fs.writeFileSync({json.dumps(str(target))}, wav);
    process.stdout.write(JSON.stringify(report));
    """
    result = _node(script, timeout=300)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)

    assert target.exists() and target.stat().st_size > 44
    samples, sample_rate = sf.read(str(target))
    assert sample_rate == 44100
    assert samples.ndim == 2 and samples.shape[1] == 2, "окно пишет стерео"
    peak = float(np.max(np.abs(samples)))
    assert 0.05 < peak <= 1.0, f"пик {peak} вне ожидаемого"
    assert float(np.sqrt((samples ** 2).mean())) > 0.005, "трек почти пустой"

    assert report["drum_engine"]["status"] == "FALLBACK"
    assert report["deterministic"] is True
    assert report["seed"] == 7
    assert [section["name"] for section in report["sections"]][0] == "intro"
    assert report["dramaturgy"]["hook_within_15s"] is True


def test_engine_is_deterministic_across_processes() -> None:
    """Один и тот же seed даёт тот же WAV и в другом процессе."""
    script = """
    const { renderBeat } = require('./src/core/audio/engine');
    const crypto = require('node:crypto');
    const { wav } = renderBeat({ bpm: 120, genre: 'trap', seed: 99, durationSec: 4 });
    process.stdout.write(crypto.createHash('sha256').update(wav).digest('hex'));
    """
    first = _node(script)
    second = _node(script)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout.strip() == second.stdout.strip(), "seed не гарантирует одинаковый WAV"

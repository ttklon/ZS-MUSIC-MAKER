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


def test_sample_bank_parity_with_python() -> None:
    """Банк в окне видит те же инструменты и тот же статус, что Python."""
    from app.audio import samples as py_samples
    from modules.beat import drums as py_drums

    script = """
    const { createNodeFs } = require('./src/core/fs-node');
    const bank = require('./src/core/audio/bank');
    const root = require('node:path').resolve('..');
    const loaded = bank.loadBank(createNodeFs(), root);
    process.stdout.write(JSON.stringify({
      report: bank.capability(loaded),
      checksums: bank.verifyChecksums(createNodeFs(), root),
      total: loaded.total,
      warnings: loaded.warnings,
    }));
    """
    result = _node(script, timeout=120)
    assert result.returncode == 0, result.stderr
    js = json.loads(result.stdout)

    py_report = py_samples.capability()
    assert js["report"]["status"] == py_report["status"], "статус банка разошёлся с Python"
    assert js["report"]["instruments_with_samples"] == py_report["instruments_with_samples"]
    assert js["report"]["total_samples"] == py_report["total_samples"]
    assert js["total"] == py_report["total_samples"]
    assert js["warnings"] == [], f"банк в окне ругается: {js['warnings']}"

    broken = [item for item in js["checksums"] if not item["ok"]]
    assert broken == [], f"хэши сэмплов не сходятся: {broken}"

    # Гейны банка в окне — те же числа, что в Python-движке.
    gains = _node("""
    const drums = require('./src/core/audio/instruments');
    process.stdout.write(JSON.stringify(drums.BANK_GAIN));
    """)
    assert json.loads(gains.stdout) == py_drums.BANK_GAIN
    assert js["report"]["velocity_mode"] == "engine-gain"


def test_window_render_with_bank_is_real_pass(tmp_path: Path) -> None:
    """С банком окно рендерит живой звук и не врёт про статус движка."""
    np = pytest.importorskip("numpy")
    sf = pytest.importorskip("soundfile")

    target = tmp_path / "beat_bank.wav"
    script = f"""
    const fs = require('node:fs');
    const path = require('node:path');
    const {{ renderBeat }} = require('./src/core/audio/engine');
    const {{ SampleSource }} = require('./src/core/audio/bank');
    const {{ createNodeFs }} = require('./src/core/fs-node');
    const bank = new SampleSource({{ fileSystem: createNodeFs(), rootDir: path.resolve('..') }});
    const {{ wav, report }} = renderBeat({{ bpm: 140, genre: 'phonk', seed: 7, durationSec: 8, bank }});
    fs.writeFileSync({json.dumps(str(target))}, wav);
    process.stdout.write(JSON.stringify(report));
    """
    result = _node(script, timeout=300)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)

    engine = report["drum_engine"]
    assert engine["status"] == "REAL_PASS"
    assert engine["engine"] == "sample_bank+procedural"
    assert engine["sample_bank"]["loaded_samples"] >= 6, "банк должен реально читать файлы"

    samples, sample_rate = sf.read(str(target))
    assert sample_rate == 44100
    peak = float(np.max(np.abs(samples)))
    assert 0.05 < peak <= 1.0
    rms = float(np.sqrt((samples ** 2).mean()))
    assert rms > 0.02, "трек с банком не должен быть тише синтезированного"


def test_bank_toggle_changes_the_sound() -> None:
    """Выключенный банк действительно меняет звук, а не только отчёт."""
    script = """
    const path = require('node:path');
    const crypto = require('node:crypto');
    const { renderBeat } = require('./src/core/audio/engine');
    const { SampleSource } = require('./src/core/audio/bank');
    const { createNodeFs } = require('./src/core/fs-node');
    const bank = new SampleSource({ fileSystem: createNodeFs(), rootDir: path.resolve('..') });
    const hash = (options) => crypto.createHash('sha256')
      .update(renderBeat(options).wav).digest('hex');
    const base = { bpm: 130, genre: 'trap', seed: 5, durationSec: 4 };
    process.stdout.write(JSON.stringify({
      withBank: hash({ ...base, bank }),
      synth: hash({ ...base, bank: null }),
    }));
    """
    result = _node(script, timeout=300)
    assert result.returncode == 0, result.stderr
    hashes = json.loads(result.stdout)
    assert hashes["withBank"] != hashes["synth"], "банк и синтез дали одинаковый WAV"


# Полосы для сверки: низ (808/кик), тело (бас, корпус снейра), верх (хэты, шум).
PARITY_BANDS = ((20, 60), (60, 120), (120, 250), (250, 500), (500, 1000),
                (1000, 2000), (2000, 4000), (4000, 8000))


def _band_energy(mono, sample_rate: int) -> dict[str, float]:
    np = pytest.importorskip("numpy")
    spectrum = np.abs(np.fft.rfft(mono * np.hanning(mono.size))) / mono.size * 2
    freqs = np.fft.rfftfreq(mono.size, 1.0 / sample_rate)
    out = {}
    for low, high in PARITY_BANDS:
        mask = (freqs >= low) & (freqs < high)
        energy = float(np.sqrt((spectrum[mask] ** 2).sum()))
        out[f"{low}-{high}"] = 20 * np.log10(max(energy, 1e-12))
    return out


def _js_section(name: str, bank: bool, target: Path) -> None:
    script = f"""
    const path = require('node:path');
    const fs = require('node:fs');
    const {{ renderBeat, buildSection }} = require('./src/core/audio/engine');
    const {{ VoiceEngine }} = require('./src/core/audio/voices');
    const {{ SampleSource }} = require('./src/core/audio/bank');
    const {{ createNodeFs }} = require('./src/core/fs-node');
    const patterns = require('./src/core/audio/patterns');
    const arrangement = require('./src/core/audio/arrangement');
    const {{ Rng }} = require('./src/core/audio/rng');
    const {{ encodeWav }} = require('./src/core/audio/wav');

    const plans = arrangement.planSections({{ bpm: 140, durationSec: 12 }});
    const plan = plans.find((item) => item.name === {json.dumps(name)});
    const bank = {str(bank).lower()}
      ? new SampleSource({{ fileSystem: createNodeFs(), rootDir: path.resolve('..') }})
      : null;
    const engine = new VoiceEngine({{
      bpm: 140,
      key: 'A minor',
      genre: 'phonk',
      rng: new Rng(7),
      noiseRng: new Rng((7 ^ 0x9e3779b9) >>> 0),
      slotPatterns: patterns.slotPresetForGenre('phonk'),
      velocityMap: patterns.velocityMapForGenre('phonk'),
      bank,
    }});
    engine.aggression = 0.7;
    const section = buildSection(engine, plan.name, plan.bars, plan);
    fs.writeFileSync({json.dumps(str(target))}, encodeWav([section.left, section.right], 44100, {{ float32: true }}));
    """
    result = _node(script, timeout=300)
    assert result.returncode == 0, result.stderr


def _py_section(name: str, bank: bool, monkeypatch) -> object:
    np = pytest.importorskip("numpy")
    from modules.beat import samples as py_samples
    from modules.beat.constructor import BeatConstructor
    from modules.beat.dramaturgy import plan_sections

    if not bank:
        monkeypatch.setattr(py_samples.SampleBankMixin, "_bank", lambda self: None)
    plans = plan_sections(bpm=140, duration_sec=12)
    plan = [item for item in plans if item.name == name][0]
    constructor = BeatConstructor(bpm=140, key="A minor", groove={}, samples=[], genre="phonk", seed=7)
    return constructor._build_section(name, plan.bars, 0.7, plan=plan).mean(axis=1)


@pytest.mark.parametrize("section", ["intro", "verse", "hook"])
def test_synth_path_matches_python_within_2_db(section: str, tmp_path: Path, monkeypatch) -> None:
    """Синтез в окне звучит как синтез в Python — полоса в полосу.

    Это главная проверка порта: одинаковые формулы, огибающие, фильтры и
    гейны должны давать одинаковый спектральный баланс. Допуск 2 дБ — это
    разница между шумовыми реализациями (numpy PCG64 против mulberry32),
    а не «примерно похоже»: расхождение по полосам видно сразу.
    """
    sf = pytest.importorskip("soundfile")

    target = tmp_path / f"js_{section}.wav"
    _js_section(section, bank=False, target=target)
    js_mono = sf.read(str(target))[0].mean(axis=1)
    py_mono = _py_section(section, bank=False, monkeypatch=monkeypatch)

    js_bands = _band_energy(js_mono, 44100)
    py_bands = _band_energy(py_mono, 44100)
    diffs = {band: js_bands[band] - py_bands[band] for band in js_bands}
    worst = max(diffs.items(), key=lambda item: abs(item[1]))
    assert abs(worst[1]) <= 2.0, f"{section}: полоса {worst[0]} разошлась на {worst[1]:.1f} дБ"


def test_bank_path_keeps_the_same_character(tmp_path: Path, monkeypatch) -> None:
    """С банком окно звучит в том же характере, но не сэмпл-в-сэмпл.

    Причина честная: Python выбирает one-shot через `_np_rng` (поток общий с
    шумом синтеза), окно — через отдельный поток. Совпадение выборки не
    гарантируется, поэтому сравнивается не сигнал, а грув и спектр.
    """
    sf = pytest.importorskip("soundfile")

    target = tmp_path / "js_bank.wav"
    _js_section("hook", bank=True, target=target)
    js_mono = sf.read(str(target))[0].mean(axis=1)
    py_mono = _py_section("hook", bank=True, monkeypatch=monkeypatch)

    js_bands = _band_energy(js_mono, 44100)
    py_bands = _band_energy(py_mono, 44100)
    # Низ (808) выбирается случайно в каждом такте, поэтому по нему допуск шире;
    # тело и верх обязаны совпасть.
    for band in ("60-120", "120-250", "250-500", "500-1000", "4000-8000"):
        assert abs(js_bands[band] - py_bands[band]) <= 3.0, (
            f"полоса {band}: {js_bands[band]:.1f} против {py_bands[band]:.1f} дБ"
        )
    assert abs(js_bands["20-60"] - py_bands["20-60"]) <= 6.0, "низ разошёлся сильнее допустимого"

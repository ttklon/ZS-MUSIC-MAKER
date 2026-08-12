# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS = []


def _record(name, ok, detail="", err=""):
    RESULTS.append({"name": name, "ok": ok, "detail": detail, "err": err})


def _run(name, fn):
    try:
        ok, detail = fn()
        _record(name, ok, detail)
    except Exception as e:
        _record(name, False, "", f"{type(e).__name__}: {e}\n" + traceback.format_exc(limit=3))


def t_main_desktop_launcher_wired():
    src = (ROOT / 'main.py').read_text(encoding='utf-8')
    if 'from app.runtime_orchestrator import RuntimeOrchestrator' not in src:
        return False, 'RuntimeOrchestrator not wired into main.py'
    if 'from app.gui.wizard import Wizard' not in src:
        return False, 'Wizard import missing in main.py'
    if 'from app.gui.wizard import ZSWizard' in src or 'w = ZSWizard(' in src:
        return False, 'stale executable ZSWizard reference still present'
    if 'if "--desktop" in args:' not in src or 'if "--gradio" in args:' not in src:
        return False, 'explicit desktop/gradio flags missing'
    return True, 'desktop launcher uses Wizard + RuntimeOrchestrator'


def t_app_main_is_wrapper():
    src = (ROOT / 'app' / 'main.py').read_text(encoding='utf-8')
    bad = ['from app.core.orchestrator import Orchestrator', 'probe_hw()', 'make_logger(']
    if any(x in src for x in bad):
        return False, 'stale executable v6 symbols still present'
    if 'import main as root_main' not in src:
        return False, 'wrapper to root main missing'
    return True, 'app/main.py delegates to root main'


def t_release_pack_accepts_dict_masters():
    from app.core import orchestrator
    r = orchestrator.run_full_pipeline('smoke_v20_pack', {'references': [], 'theme': 'test', 'genre': 'phonk'}, dry_run=False, out_root=ROOT / 'output' / 'smoke_v20_pack')
    rp = [s for s in r['stages'] if s['name'] == '_stage_release_pack'][0]
    notes = (rp.get('output') or {}).get('fallback_notes') or []
    bad = [n for n in notes if 'master_streaming_fail:' in n or 'path should be string' in n]
    if bad:
        return False, '; '.join(bad[:2])
    cats = (rp.get('output') or {}).get('categories') or {}
    if int(cats.get('audio', 0)) < 8:
        return False, f'audio count too low: {cats}'
    return True, f'audio={cats.get("audio")} fallback_notes={len(notes)}'


def t_honest_fallback_not_simulation():
    from app.core import orchestrator
    honest = {'ok': True, 'fallback_used': True, 'reason': 'texture skipped honestly'}
    synth = {'ok': True, 'synthetic': True, 'engine': 'rap_scaffold_numpy'}
    if orchestrator._is_simulation_result(honest):
        return False, 'honest fallback still classified as simulation'
    if not orchestrator._is_simulation_result(synth):
        return False, 'explicit synthetic result stopped being classified as simulation'
    return True, 'simulation detector separates honest fallback from synthetic placeholder'


def main():
    tests = [
        ('v20.main_desktop_launcher_wired', t_main_desktop_launcher_wired),
        ('v20.app_main_is_wrapper', t_app_main_is_wrapper),
        ('v20.release_pack_accepts_dict_masters', t_release_pack_accepts_dict_masters),
        ('v20.honest_fallback_not_simulation', t_honest_fallback_not_simulation),
    ]
    print('=' * 64)
    print('ZS Music Maker v20 — smoke_v20')
    print('=' * 64)
    for name, fn in tests:
        _run(name, fn)
    for r in RESULTS:
        status = 'PASS' if r['ok'] else 'FAIL'
        print(f'[{status}] {r["name"]:42s} {r["detail"]}')
        if r['err']:
            print(f'       err: {r["err"].splitlines()[0]}')
    n_pass = sum(1 for r in RESULTS if r['ok'])
    n_fail = sum(1 for r in RESULTS if not r['ok'])
    print('-' * 64)
    print(f'RESULT: {n_pass} PASS / {n_fail} FAIL / {len(RESULTS)} total')
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

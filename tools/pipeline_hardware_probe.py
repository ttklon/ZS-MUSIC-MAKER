"""Measured real classic Python orchestration. Partial output is never a PASS.

CPU procedural instrumental, no voice and no neural model certification.
Use a NEW output directory; previous runs must not be overwritten.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import sys
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.neural_benchmark import block_python_network, measure_render, sha256


def scenario(seconds):
    if type(seconds) is not int or seconds not in (20, 120):
        raise ValueError('Only explicit 20 or 120 second scenarios are supported')
    return dict(genre='drift_phonk', theme='CPU hardware probe instrumental',
                seed=7, duration_sec=seconds, bpm_override=140, voice_mode='off',
                beat_engine='procedural', stands=['streaming'], quality_mode='fast',
                export_stems=False, user_lyrics_lines=['Instrumental hardware probe metadata'])


def inspect_master(report, expected_seconds):
    import soundfile as sf
    from tools.windows_neural_smoke import check_audio
    master = Path(report.get('master_path') or '')
    if not master.is_file():
        raise ValueError('Successful pipeline did not provide a master file')
    metrics = check_audio(master)
    if abs(metrics['seconds'] - expected_seconds) > 0.1:
        raise ValueError('Master duration does not match the scenario')
    if sf.info(master).channels != 2:
        raise ValueError('Expected stereo master')
    return dict(**metrics, sha256=sha256(master))


def evaluate(report, expected_seconds):
    if report.get('dry_run') is True or report.get('only'):
        raise ValueError('Partial/dry execution is not full orchestration evidence')
    outcome = report.get('outcome') or {}
    if outcome.get('succeeded') is not True or outcome.get('status') != 'success':
        raise ValueError('Pipeline outcome did not succeed; existing audio is diagnostic only')
    return inspect_master(report, expected_seconds)


def probe(seconds, directory, *, without_texture=False):
    state = scenario(seconds)
    if without_texture:
        state["use_texture"] = False
    directory.mkdir(parents=True, exist_ok=False)
    report = dict(schema=1, ok=False, kind='real_classic_cpu_instrumental_probe_not_neural',
                  product_profile_accepted=False, os=platform.system(), python=sys.version,
                  source=os.environ.get('GITHUB_SHA'), input=state, measurements={},
                  network_guard='python_socket_only_not_os_firewall')
    try:
        with patch.dict(os.environ, {'ZSMM_ONLINE': '0', 'CUDA_VISIBLE_DEVICES': '', 'ZSMM_PROBE_LOCAL_SERVICES': '0'}), block_python_network() as attempts:
            report['network_attempts'] = attempts
            from app.core.orchestrator import run_full_pipeline
            from app.ai.profiles import measure_profile
            report['hardware'] = measure_profile(directory)
            with measure_render(report['measurements']):
                result = run_full_pipeline('hardware_cpu', state, dry_run=False, out_root=directory / 'pipeline')
            report['pipeline'] = result
            from app.core.stage_request import classic_outcome, classic_result
            report['adapter_outcome'] = classic_outcome(result, state)
            report['typed_result'] = classic_result(result, state, requested_kind='instrumental')
            if report['adapter_outcome']['status'] != result['outcome']['status']:
                raise ValueError('Caller-scoped adapter disagrees with producer outcome')
            try:
                report['diagnostic_audio'] = inspect_master(result, seconds)
            except Exception as exc:
                report['diagnostic_audio_error'] = str(exc)
            report['audio'] = evaluate(result, seconds)
        report.update(ok=True, network_attempts=attempts)
    except Exception:
        report['error'] = traceback.format_exc()
    (directory / 'probe_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    return report


def summary_for(report):
    result = report.get('pipeline') or {}
    return {**{key: value for key, value in report.items() if key not in ('pipeline', 'hardware')},
            'outcome': result.get('outcome'),
            'stages': [{key: stage.get(key) for key in ('name', 'status', 'reason')}
                       for stage in result.get('stages', [])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=int, choices=(20, 120), default=20)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--without-texture', action='store_true', help='Explicit caller request: no neural texture')
    args = parser.parse_args()
    report = probe(args.duration, args.out, without_texture=args.without_texture)
    print(json.dumps(summary_for(report), ensure_ascii=True, indent=2))
    summary = {key: report.get(key) for key in ('ok', 'kind', 'source', 'measurements', 'diagnostic_audio')}
    summary['product_profile_accepted'] = False
    summary['render_evidence'] = (report.get('pipeline') or {}).get('render_evidence')
    summary['adapter_status'] = (report.get('adapter_outcome') or {}).get('status')
    summary['typed_result_status'] = (report.get('typed_result') or {}).get('status')
    summary['outcome_status'] = (report.get('pipeline', {}).get('outcome') or {}).get('status')
    print('::notice title=Classic pipeline diagnostic::' + json.dumps(summary, ensure_ascii=True))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

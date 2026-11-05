"""JIT cache process isolation: CPU-only; no claim about Windows or AI."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def env_for(base):
    env = os.environ.copy()
    env.update(NUMBA_CACHE_DIR=str(base), OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', NUMBA_NUM_THREADS='1')
    env.pop('ZSMM_NUMBA_CACHE_ISOLATED', None)
    env.pop('ZSMM_NUMBA_CACHE_BASE', None)
    env['PYTHONPATH'] = str(ROOT)
    return env


def test_temporary_cache_is_private_and_only_its_own_directory_is_removed(tmp_path):
    base = tmp_path/'base'; base.mkdir()
    sentinel = base/'keep'; sentinel.write_text('user data')
    program = '''
import json, os
from pathlib import Path
from app.core.numba_cache import isolated_numba_cache
before = os.environ["NUMBA_CACHE_DIR"]
with isolated_numba_cache() as cache:
    assert os.environ["NUMBA_CACHE_DIR"] == cache
    Path(cache, "created_by_numba").write_text("temporary")
    print(json.dumps({"cache": cache, "parent": str(Path(cache).parent)}))
assert os.environ["NUMBA_CACHE_DIR"] == before
assert not Path(cache).exists()
'''
    out = subprocess.check_output([sys.executable, '-c', program], env=env_for(base), text=True)
    report = json.loads(out)
    assert Path(report['parent']) == base and sentinel.read_text() == 'user data'
    assert list(base.iterdir()) == [sentinel]


def test_already_imported_numba_and_invalid_base_fail_before_work(tmp_path):
    if importlib.util.find_spec('numba') is None:
        pytest.skip('Numba not installed')
    program = '''
import numba
from app.core.numba_cache import isolated_numba_cache
try:
    with isolated_numba_cache(): pass
except RuntimeError as exc:
    assert "after Numba was imported" in str(exc)
else: raise AssertionError("late initialization must fail")
'''
    subprocess.run([sys.executable, '-c', program], env=env_for(tmp_path), check=True, timeout=30)
    program2 = '''
from app.core.numba_cache import isolated_numba_cache
try:
    with isolated_numba_cache(): pass
except RuntimeError as exc:
    assert "cannot create private Numba cache" in str(exc)
else: raise AssertionError("nonexistent cache base must fail")
'''
    subprocess.run([sys.executable, '-c', program2], env=env_for(tmp_path/'missing'), check=True, timeout=30)
    assert not (tmp_path/'missing').exists()


def test_inherited_parent_and_child_caches_are_siblings(tmp_path):
    program = '''
import json, os, subprocess, sys
from pathlib import Path
from app.core.numba_cache import isolated_numba_cache
with isolated_numba_cache() as parent:
    script = "from app.core.numba_cache import isolated_numba_cache;\\nwith isolated_numba_cache() as p: print(p)"
    child = subprocess.check_output([sys.executable, "-c", script], text=True).strip()
    assert Path(parent).parent == Path(child).parent
    assert parent != child
    assert not Path(child).exists() and Path(parent).is_dir()
    print(json.dumps({"parent": parent, "child": child}))
assert not Path(parent).exists()
'''
    result = json.loads(subprocess.check_output([sys.executable, '-c', program], env=env_for(tmp_path), text=True))
    assert Path(result['parent']).parent == tmp_path and Path(result['child']).parent == tmp_path
    assert not list(tmp_path.iterdir())


def test_concurrent_librosa_processes_use_different_caches(tmp_path):
    if importlib.util.find_spec('numba') is None or importlib.util.find_spec('librosa') is None:
        pytest.skip('librosa/Numba not installed')
    base = tmp_path/'cache'; base.mkdir()
    worker = tmp_path/'worker.py'
    worker.write_text('''
import json, os
from pathlib import Path
from app.core.numba_cache import isolated_numba_cache
with isolated_numba_cache() as cache:
    import numpy as np, librosa
    onset = np.random.default_rng(4).random(256, dtype=np.float32)
    for _ in range(3):
        peaks = librosa.util.localmax(onset)
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=22050)
        assert len(peaks) == len(onset) and np.isfinite(tempo).all()
    Path(os.environ['RESULT']).write_text(json.dumps({'cache': cache}))
''', encoding='utf-8')
    procs = []
    try:
        for i in range(3):
            env = env_for(base); env['RESULT'] = str(tmp_path/f'result{i}.json')
            procs.append(subprocess.Popen([sys.executable, str(worker)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        for proc in procs:
            out, err = proc.communicate(timeout=150)
            assert proc.returncode == 0, f'exit {proc.returncode}\n{out}\n{err}'
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.kill(); proc.wait()
    paths = [json.loads((tmp_path/f'result{i}.json').read_text())['cache'] for i in range(3)]
    assert len(set(paths)) == 3
    assert all(Path(path).parent == base and not Path(path).exists() for path in paths)
    assert not list(base.iterdir())

def test_cli_and_pytest_entrypoints_isolate_before_audio_imports(tmp_path):
    base = tmp_path/'base'; base.mkdir()
    cli = '''
import os
from pathlib import Path
import main
original = os.environ["NUMBA_CACHE_DIR"]
def check():
    cache = Path(os.environ["NUMBA_CACHE_DIR"])
    assert cache.parent == Path(original) and cache.is_dir()
    Path(os.environ["MARKER"]).write_text(str(cache))
    return 0
main.main = check
assert main.cli_entry() == 0
assert os.environ["NUMBA_CACHE_DIR"] == original
'''
    env = env_for(base); env['MARKER'] = str(tmp_path/'cli-cache.txt')
    subprocess.run([sys.executable, '-c', cli], env=env, check=True, timeout=30)
    cache = Path((tmp_path/'cli-cache.txt').read_text())
    assert cache.parent == base and not cache.exists()
    sample = tmp_path/'test_sample.py'
    sample.write_text('''import os\nfrom pathlib import Path\ndef test_cache():\n    cache = Path(os.environ['NUMBA_CACHE_DIR'])\n    assert cache.is_dir() and cache.name.startswith('zsmm-numba-')\n    Path(os.environ['MARKER']).write_text(str(cache))\n''')
    env['MARKER'] = str(tmp_path/'test-cache.txt')
    subprocess.run([sys.executable, '-m', 'tools.pytest_isolated', str(sample), '-q', '-p', 'no:cacheprovider'],
                   cwd=ROOT, env=env, check=True, timeout=60, capture_output=True, text=True)
    test_cache = Path((tmp_path/'test-cache.txt').read_text())
    assert test_cache.parent == base and not test_cache.exists() and not list(base.iterdir())

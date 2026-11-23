"""Real Windows integration: terminating host must reap detached grandchildren."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


@pytest.mark.skipif(os.name != 'nt', reason='requires Windows kernel job objects')
def test_job_host_reaps_detached_descendant(tmp_path):
    import ctypes
    from ctypes import wintypes
    child_pid = tmp_path / 'child.pid'
    script = tmp_path / 'spawn.py'
    grandchild_code = (
        'import subprocess,sys,time,os,json\nfrom pathlib import Path\n'
        'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(180)"],'
        'creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP)\n'
        f'q=Path({str(child_pid)!r}); q.with_suffix(".tmp").write_text(json.dumps([os.getpid(),p.pid])); q.with_suffix(".tmp").replace(q)\n'
        'time.sleep(180)\n')
    script.write_text(
        'import subprocess,sys,time\n'
        f'p=subprocess.Popen([sys.executable,"-c",{grandchild_code!r}],'
        'creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP)\n'
        'time.sleep(180)\n', encoding='utf-8')
    host = Path(__file__).resolve().parents[1] / 'app/cli/managed_task_host.py'
    process = subprocess.Popen([sys.executable, str(host), str(script)])
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handles = []
    try:
        deadline = time.monotonic() + 20
        while not child_pid.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(.05)
        assert child_pid.exists(), f'host exited before child launch: {process.poll()}'
        for pid in json.loads(child_pid.read_text()):
            handle = kernel.OpenProcess(0x100000, False, pid)
            assert handle, 'descendant must be alive before cancellation'
            handles.append(handle)
        process.kill()  # deliberately do NOT taskkill /T: job must supply containment
        process.wait(timeout=10)
        for handle in handles:
            assert kernel.WaitForSingleObject(handle, 10000) == 0, 'detached descendant survived job host'
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        for handle in handles:
            kernel.CloseHandle(handle)

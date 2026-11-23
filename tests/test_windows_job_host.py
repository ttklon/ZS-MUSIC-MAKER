"""Real Windows integration: terminating host must reap detached grandchildren."""
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
    script.write_text(
        'import subprocess,sys,time\n'
        'from pathlib import Path\n'
        'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(180)"],'
        'creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP)\n'
        f'Path({str(child_pid)!r}).write_text(str(p.pid))\n'
        'time.sleep(180)\n', encoding='utf-8')
    host = Path(__file__).resolve().parents[1] / 'app/cli/managed_task_host.py'
    process = subprocess.Popen([sys.executable, str(host), str(script)])
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = None
    try:
        deadline = time.monotonic() + 20
        while not child_pid.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(.05)
        assert child_pid.exists(), f'host exited before child launch: {process.poll()}'
        handle = kernel.OpenProcess(0x100000, False, int(child_pid.read_text()))
        assert handle, 'descendant must be alive before cancellation'
        process.kill()  # deliberately do NOT taskkill /T: job must supply containment
        process.wait(timeout=10)
        assert kernel.WaitForSingleObject(handle, 10000) == 0, 'detached child survived job host'
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        if handle:
            kernel.CloseHandle(handle)

"""Task entrypoint: enter a Windows Job before executing the real CLI/worker."""
import os
from pathlib import Path
import runpy
import sys


def main():
    if len(sys.argv) < 2:
        return 2
    script = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    if os.name == 'nt':
        from app.cli.windows_job import enter_kill_on_close_job
        try:
            enter_kill_on_close_job()
        except OSError as error:
            print(f'[process-host] job assignment failed; task was NOT started: {error}', file=sys.stderr, flush=True)
            return 78
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *sys.argv[2:]]
    runpy.run_path(str(script), run_name='__main__')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

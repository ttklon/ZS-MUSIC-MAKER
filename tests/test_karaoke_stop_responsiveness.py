from __future__ import annotations

import threading
import time

from modules.karaoke_engine import KaraokeSession


def test_count_in_stop_is_prompt_and_keeps_stopped_state() -> None:
    session = KaraokeSession([], bpm=1, count_in_beats=1)
    first_beat = threading.Event()
    session.on("on_beat", lambda _payload: first_beat.set())
    worker = threading.Thread(target=session._run, daemon=True)
    worker.start()

    assert first_beat.wait(timeout=0.5)
    started = time.monotonic()
    session.stop()
    worker.join(timeout=0.5)

    assert not worker.is_alive()
    assert session.state == "stopped"
    assert time.monotonic() - started < 0.5

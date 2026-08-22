from __future__ import annotations

import tempfile
from pathlib import Path

from modules import release_pack_v9, video_edit_v11


def test_release_pack_manual_example_uses_os_temp_directory() -> None:
    example_path = Path(release_pack_v9._example_missing_master_path())

    assert example_path.parent == Path(tempfile.gettempdir())
    assert example_path.name == "zsmm_release_pack_missing_master.wav"


def test_video_editor_self_test_uses_portable_temporary_fixture() -> None:
    assert video_edit_v11._self_test() is True


def test_affected_production_modules_have_no_fixed_posix_tmp_literal() -> None:
    root = Path(__file__).resolve().parents[1]
    for relative_path in ("modules/release_pack_v9.py", "modules/video_edit_v11.py"):
        assert '"/tmp/' not in (root / relative_path).read_text(encoding="utf-8")

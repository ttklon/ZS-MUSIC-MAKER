from modules import video_edit_v11


def test_lrc_diagnostics_preserve_valid_cues_and_report_bad_timestamp(tmp_path):
    lrc = tmp_path / "lyrics.lrc"
    lrc.write_text("[00:01.50]First line\n[0a:01]Broken\n[00:03.00][00:04.00]Repeat\n", encoding="utf-8")

    result = video_edit_v11._parse_lrc_with_diagnostics(str(lrc))

    assert result["cues"] == [(1.5, "First line"), (3.0, "Repeat"), (4.0, "Repeat")]
    assert result["diagnostics"] == [
        {"line": 2, "tag": "0a:01", "error": "ValueError: could not convert string to float: '0a'"}
    ]


def test_legacy_lrc_parser_returns_cues_when_source_is_unreadable(tmp_path):
    missing = tmp_path / "absent.lrc"

    result = video_edit_v11._parse_lrc_with_diagnostics(str(missing))

    assert video_edit_v11._parse_lrc(str(missing)) == []
    assert result["cues"] == []
    assert result["diagnostics"][0]["error"].startswith("FileNotFoundError: ")

"""Контракт CLI: флаги классического прогона и разбор `--only`."""

from __future__ import annotations

from app.cli.pipeline import parse_only
from app.cli.parser import build_parser


def test_parse_only_is_none_when_flag_is_empty() -> None:
    assert parse_only("") is None
    assert parse_only("  , ") is None


def test_parse_only_normalises_whitespace_and_duplicates() -> None:
    assert parse_only(" beat , mix ,beat ") == {"beat", "mix"}


def test_parser_exposes_deterministic_run_flags() -> None:
    args = build_parser().parse_args(
        ["--run", "--seed", "42", "--resume", "--only", "beat,lyrics"]
    )

    assert args.run is True
    assert args.seed == 42
    assert args.resume is True
    assert args.only == "beat,lyrics"


def test_parser_defaults_keep_pipeline_off() -> None:
    args = build_parser().parse_args([])

    assert args.run is False
    assert args.resume is False
    assert args.seed is None
    assert args.only == ""
    assert args.list_stages is False


def test_list_stages_covers_every_selectable_key(capsys) -> None:
    from app.cli.pipeline import run_list_stages
    from app.core.pipeline_runtime import STAGE_KEYS

    assert run_list_stages() == 0
    out = capsys.readouterr().out
    for key in STAGE_KEYS:
        assert f"  - {key}" in out

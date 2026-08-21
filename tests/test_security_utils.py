from __future__ import annotations

from app.core.security_utils import redact_secrets, safe_child_path, safe_identifier


def test_safe_identifier_rejects_path_traversal_and_separators(tmp_path) -> None:
    for hostile in ("../artist", "..", "/absolute", "a/b", r"a\\b", ""):
        assert safe_identifier(hostile) == "unknown"
        assert safe_child_path(tmp_path, hostile).parent == tmp_path.resolve()
    assert safe_identifier("MC Ночь-7") == "MC_Ночь-7"


def test_redact_secrets_removes_token_shaped_values() -> None:
    github_token = "github" + "_pat_" + "A" * 32
    text = f"authorization: Bearer abcdefghijklmnopqrstuvwxyz; token={github_token}; api_key=sk-abcdefghijklmnop"
    redacted = redact_secrets(text)

    assert github_token not in redacted
    assert "sk-abcdefghijklmnop" not in redacted
    assert "[REDACTED]" in redacted

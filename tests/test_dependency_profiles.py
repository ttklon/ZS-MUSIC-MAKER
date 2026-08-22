from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _package_name(requirement: str) -> str:
    line = requirement.strip()
    if line.startswith("git+"):
        return "bark" if "suno-ai/bark" in line.lower() else line.rsplit("/", 1)[-1].removesuffix(".git").lower()
    line = line.split(";", 1)[0].strip()
    if " @ " in line:
        line = line.split(" @ ", 1)[0]
    return re.match(r"[A-Za-z0-9_.-]+", line).group(0).lower().replace("_", "-")


def _manifest_names(path: Path) -> set[str]:
    return {
        _package_name(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _project_names(requirements: list[str]) -> set[str]:
    return {_package_name(value) for value in requirements}


def test_pyproject_profiles_match_requirements_manifests() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    extras = project["optional-dependencies"]

    assert _project_names(project["dependencies"]) == _manifest_names(ROOT / "requirements.txt")
    assert _project_names(extras["ai"]) == _manifest_names(ROOT / "requirements_ai.txt")
    assert _project_names(extras["amd"]) == _manifest_names(ROOT / "requirements_amd.txt")


def test_torch_heavy_dependencies_are_optional_only() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    base = _project_names(project["dependencies"])
    ai = _project_names(project["optional-dependencies"]["ai"])
    amd = _project_names(project["optional-dependencies"]["amd"])
    heavy = {"torch", "torchaudio", "audiocraft", "demucs", "tts", "faster-whisper", "diffusers", "xformers", "torch-directml"}

    assert base.isdisjoint(heavy)
    assert {"torch", "torchaudio", "audiocraft", "demucs", "tts", "faster-whisper", "diffusers", "xformers"}.issubset(ai)
    assert amd == {"torch-directml"}

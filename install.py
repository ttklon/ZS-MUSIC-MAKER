# -*- coding: utf-8 -*-
"""Идемпотентный installer ZS Music Maker без shell command execution."""
from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE_REQUIREMENTS = ROOT / "requirements.txt"
AI_REQUIREMENTS = ROOT / "requirements_ai.txt"
REQUIRED_DIRS = (
    "output/logs", "output/god_cli", "output/async_cli", "output/queue",
    "models", "samples_cache", "checkpoints", "data/ai_models", "voice_vault",
)


def run_cmd(cmd: list[str], critical: bool = False) -> bool:
    """Выполнить только explicit argv (никогда shell=True)."""
    print("Executing:", " ".join(cmd))
    try:
        subprocess.check_call(cmd, cwd=ROOT)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] Command failed with exit code {exc.returncode}: {exc}")
    except OSError as exc:
        print(f"[ERROR] Cannot execute command: {exc}")
    if critical:
        raise RuntimeError(f"critical installer command failed: {cmd[0]}")
    return False


def _initialise_filesystem() -> None:
    for directory in REQUIRED_DIRS:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    example = ROOT / ".env.example"
    env = ROOT / ".env"
    if example.is_file() and not env.exists():
        shutil.copyfile(example, env)
        print("Created .env from .env.example")


def installation_plan(install_ai: bool, system_deps: bool) -> list[list[str]]:
    plan: list[list[str]] = []
    if system_deps and platform.system() == "Linux":
        plan.append(["sudo", "apt-get", "install", "-y", "ffmpeg", "graphviz", "libsndfile1"])
    plan.append([sys.executable, "-m", "pip", "install", "-r", str(CORE_REQUIREMENTS)])
    if install_ai:
        plan.append([sys.executable, "-m", "pip", "install", "-r", str(AI_REQUIREMENTS)])
    return plan


def setup(*, install_ai: bool = False, system_deps: bool = False, dry_run: bool = False) -> int:
    print("=== ZS Music Maker Installer ===")
    print(f"Detected OS: {platform.system()}")
    _initialise_filesystem()
    plan = installation_plan(install_ai, system_deps)
    if dry_run:
        print("DRY RUN: no packages will be installed")
        for command in plan:
            print("PLAN:", " ".join(command))
        return 0
    for command in plan:
        run_cmd(command, critical=(command[0] == sys.executable))
    print("Installation complete. Run: python main.py --ai-status")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install ZS Music Maker dependencies")
    parser.add_argument("--ai", action="store_true", help="Install optional AI dependency manifest")
    parser.add_argument("--system-deps", action="store_true", help="Install Linux system packages (requires sudo)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan and initialise directories without installation")
    args = parser.parse_args()
    try:
        return setup(install_ai=args.ai, system_deps=args.system_deps, dry_run=args.dry_run)
    except RuntimeError as exc:
        print(f"[CRITICAL] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

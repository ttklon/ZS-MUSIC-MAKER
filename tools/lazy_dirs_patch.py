"""v22: одноразовый скрипт — заменить top-level mkdir() на ленивое создание.

Стратегия:
  • если top-level `X.mkdir(...)` или `os.makedirs(X, ...)` — убираем;
  • перед первой записью в X добавляем `X.mkdir(parents=True, exist_ok=True)`;
  • для модулей с простым `OUTPUT_DIR` — оставляем константу, убираем side-effect.

Скрипт работает по whitelist модулей, чтобы не сломать остальное.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODS = ROOT / "modules"

# whitelist модулей и их паттернов (regex → replacement)
PATCHES = {
    "mixdown.py": [
        (
            r"^os\.makedirs\(OUTPUT_DIR, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "beat_gen.py": [
        (
            r"^os\.makedirs\(OUTPUT_DIR, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "humanization.py": [
        (
            r"^os\.makedirs\(OUTPUT_DIR, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "provenance.py": [
        (
            r"^os\.makedirs\(os\.path\.dirname\(VAULT\), exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "release_export.py": [
        (
            r"^RELEASES_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "track_templates.py": [
        (
            r"^TPL_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
        (
            r"^HIST_FILE\.parent\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "render_queue.py": [
        (
            r"^QUEUE_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "lyrics_gen.py": [
        (
            r"^VAULT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "female_backing.py": [
        (
            r"^BACK_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "user_profile.py": [
        (
            r"^PROFILE_FILE\.parent\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "voice_recording.py": [
        (
            r"^VAULT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "voice_onboarding.py": [
        (
            r"^VAULT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "voice_vault_v9.py": [
        (
            r"^VAULT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "rvc_trainer_v9.py": [
        (
            r"^JOBS_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "reference_ingest.py": [
        (
            r"^CACHE_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "auto_qa.py": [
        (
            r"^QA_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "self_diag_v13.py": [
        (
            r"^LOGS\.mkdir\(exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "wizard_v12_integration.py": [
        (
            r"^LOGS\.mkdir\(exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "master_pipeline_v12.py": [
        (
            r"^LOGS\.mkdir\(exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "llm_clients_v15.py": [
        (
            r"^SECRETS_FILE\.parent\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
    "voice_synth.py": [
        (
            r"^OUT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
            "# v22: ленивое создание (не при импорте)\n",
        ),
    ],
}


def main():
    modified = []
    for fname, rules in PATCHES.items():
        p = MODS / fname
        if not p.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        src = p.read_text(encoding="utf-8")
        orig = src
        for pattern, replacement in rules:
            src = re.sub(pattern, replacement, src, count=1, flags=re.MULTILINE)
        if src != orig:
            p.write_text(src, encoding="utf-8")
            modified.append(fname)
            print(f"  [OK] {fname}")
        else:
            print(f"  [NOOP] {fname}")
    print(f"\nTotal modified: {len(modified)}")
    return 0


if __name__ == "__main__":
    from cli_contract import help_or_error

    if help_or_error(__doc__ or "ZS Music Maker tool"):
        raise SystemExit(0)
    raise SystemExit(main())

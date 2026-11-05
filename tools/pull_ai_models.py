# -*- coding: utf-8 -*-
"""Загрузка и проверка весов 13 AI-ролей.

Примеры:
  python tools/pull_ai_models.py --list
  python tools/pull_ai_models.py --role lyrics_llm
  python tools/pull_ai_models.py --all
  python tools/pull_ai_models.py --verify --role lyrics_llm

Скачиваемые артефакты хранятся в ``data/ai_models/<role>/``.  ``manifest.json``
фиксирует точный source, размер и SHA-256 локального результата. Хэши весов не
выдумываются: если upstream не публикует pinned SHA-256 в registry, manifest
маркирует проверку как local integrity verification, а не source attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.ai.registry import MODEL_REGISTRY  # noqa: E402

AI_MODELS_DIR = ROOT / "data" / "ai_models"
MANIFEST_NAME = "manifest.json"


def _role_dir(key: str) -> Path:
    return AI_MODELS_DIR / key


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.name not in {MANIFEST_NAME, ".gitattributes"}
    )


def _write_manifest(key: str, *, status: str, source: str, files: list[dict[str, Any]],
                    expected_sha256: str | None = None,
                    expected_size_bytes: int | None = None, note: str = "") -> Path:
    target_dir = _role_dir(key)
    target_dir.mkdir(parents=True, exist_ok=True)
    verified = (
        bool(expected_sha256)
        and len(files) == 1
        and files[0]["sha256"] == expected_sha256
        and (expected_size_bytes is None or files[0]["bytes"] == expected_size_bytes)
    )
    payload = {
        "schema_version": 1,
        "role": key,
        "status": status,
        "source": source,
        "created_at_unix": int(time.time()),
        "expected_sha256": expected_sha256,
        "expected_size_bytes": expected_size_bytes,
        "verification": "upstream_sha256_and_size" if expected_sha256 else "local_manifest_sha256",
        "verified": verified if expected_sha256 else bool(files),
        "note": note,
        "files": files,
    }
    destination = target_dir / MANIFEST_NAME
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
    return destination


def _build_file_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _manifest_for_local_files(key: str, *, status: str, source: str,
                              expected_sha256: str | None = None,
                              expected_size_bytes: int | None = None, note: str = "") -> Path:
    target_dir = _role_dir(key)
    records = [_build_file_record(path, target_dir) for path in _iter_files(target_dir)]
    return _write_manifest(
        key,
        status=status,
        source=source,
        files=records,
        expected_sha256=expected_sha256,
        expected_size_bytes=expected_size_bytes,
        note=note,
    )


def verify(key: str) -> bool:
    """Проверить все файлы роль-артефакта против записанного manifest SHA-256."""
    target_dir = _role_dir(key)
    manifest_path = target_dir / MANIFEST_NAME
    if not manifest_path.exists():
        print(f"[verify] {key}: manifest missing at {manifest_path}")
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest.get("files", [])
        if not isinstance(records, list):
            raise ValueError("files is not a list")
        if not records and manifest.get("status") != "pip_only":
            raise ValueError("no model files recorded; external or user-supplied weights not verified")
        for record in records:
            path = target_dir / str(record["path"])
            if not path.is_file():
                raise FileNotFoundError(path)
            actual_size = path.stat().st_size
            actual_hash = _sha256(path)
            if actual_size != record["bytes"] or actual_hash != record["sha256"]:
                raise ValueError(f"checksum mismatch: {record['path']}")
        expected = manifest.get("expected_sha256")
        expected_size = manifest.get("expected_size_bytes")
        if expected and len(records) == 1 and records[0]["sha256"] != expected:
            raise ValueError("upstream expected_sha256 mismatch")
        if expected_size is not None and len(records) == 1 and records[0]["bytes"] != expected_size:
            raise ValueError("upstream expected_size_bytes mismatch")
        print(f"[verify] {key}: OK ({len(records)} files, {manifest.get('verification')})")
        return True
    except Exception as exc:
        print(f"[verify] {key}: FAILED: {exc}")
        return False


def _pull_gguf(key: str) -> bool:
    spec = MODEL_REGISTRY[key]
    target_dir = _role_dir(key)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / spec["file"]
    expected_sha256 = spec.get("sha256")
    expected_size_bytes = spec.get("expected_size_bytes")
    if target.is_file():
        _manifest_for_local_files(
            key,
            status="installed",
            source=f"hf://{spec['hf_repo']}/{spec['file']}",
            expected_sha256=expected_sha256,
            expected_size_bytes=expected_size_bytes,
            note="Existing local GGUF was indexed; use --verify to recheck it.",
        )
        return verify(key)
    try:
        from huggingface_hub import hf_hub_download
    except Exception as exc:
        print(f"[err] {key}: huggingface_hub unavailable: {exc}")
        return False
    try:
        print(f"[pull] {key} <- hf://{spec['hf_repo']}/{spec['file']}")
        downloaded = Path(hf_hub_download(
            repo_id=spec["hf_repo"],
            filename=spec["file"],
            local_dir=str(target_dir),
        ))
        if downloaded != target and downloaded.is_file() and not target.exists():
            downloaded.replace(target)
        _manifest_for_local_files(
            key,
            status="installed",
            source=f"hf://{spec['hf_repo']}/{spec['file']}",
            expected_sha256=expected_sha256,
            expected_size_bytes=expected_size_bytes,
            note="Hugging Face client supports resumable cache downloads; no upstream SHA-256 was declared in registry."
                 if not expected_sha256 else "Verified against registry upstream SHA-256.",
        )
        return verify(key)
    except Exception as exc:
        print(f"[err] {key}: {exc}")
        return False


def _pull_hf_snapshot(key: str) -> bool:
    spec = MODEL_REGISTRY[key]
    repo = spec.get("hf_repo")
    if not repo:
        return False
    target_dir = _role_dir(key)
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        print(f"[err] {key}: huggingface_hub unavailable: {exc}")
        return False
    try:
        print(f"[pull] {key} <- hf://{repo} (resume enabled by huggingface cache)")
        snapshot_download(repo_id=repo, local_dir=str(target_dir))
        _manifest_for_local_files(
            key,
            status="installed",
            source=f"hf://{repo}",
            expected_sha256=spec.get("sha256"),
            expected_size_bytes=spec.get("expected_size_bytes"),
            note="Snapshot indexed after download. Multi-file repositories use per-file local SHA-256 records.",
        )
        return verify(key)
    except Exception as exc:
        print(f"[err] {key}: {exc}")
        return False


def _pull_demucs(key: str) -> bool:
    spec = MODEL_REGISTRY[key]
    target_dir = _role_dir(key)
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        from demucs.pretrained import get_model

        print("[pull] stem_splitter <- demucs htdemucs")
        get_model("htdemucs")
        _write_manifest(
            key,
            status="installed_external_cache",
            source=f"demucs://{spec['hf_repo']}",
            files=[],
            note="Demucs API manages its own cache; cache location is library-controlled and is not copied blindly.",
        )
        print(f"[pull] {key}: demucs API cache prepared; manifest written")
        return True
    except Exception as exc:
        print(f"[err] {key}: {exc}")
        return False


def _record_non_download_role(key: str, status: str, note: str) -> bool:
    spec = MODEL_REGISTRY[key]
    path = _write_manifest(
        key,
        status=status,
        source=str(spec.get("hf_repo") or spec["engine"]),
        files=[],
        note=note,
    )
    print(f"[note] {key}: {note} ({path})")
    return True


def pull(key: str) -> bool:
    if key not in MODEL_REGISTRY:
        print(f"[err] unknown model role: {key}")
        return False
    spec = MODEL_REGISTRY[key]
    engine = spec["engine"]
    if engine == "llama_cpp":
        return _pull_gguf(key)
    if engine == "demucs":
        return _pull_demucs(key)
    if engine in {"audiocraft_musicgen", "xtts_v2", "faster_whisper", "clap", "diffusers"}:
        return _pull_hf_snapshot(key)
    if engine == "rvc":
        note = ("Provide a licensed user-trained model at models/rvc/my_voice/my_voice.pth; "
                "this downloader does not install or verify user voice models.")
        _record_non_download_role(key, "user_supplied", note)
        return False
    if engine in {"matchering_plus", "essentia_or_librosa"}:
        return _record_non_download_role(
            key,
            "pip_only",
            "No model weights are downloaded; install the named Python dependency from requirements_ai.txt.",
        )
    print(f"[err] {key}: unsupported engine {engine}")
    return False


def _print_list() -> None:
    for key, spec in MODEL_REGISTRY.items():
        manifest = _role_dir(key) / MANIFEST_NAME
        state = "MANIFEST" if manifest.exists() else "NOT_PULLED"
        source = spec.get("hf_repo") or spec["engine"]
        print(f"{key:20s} {state:11s} {spec['engine']:22s} {source}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--role", "--model", dest="role", help="AI role from app.ai.registry")
    group.add_argument("--all", action="store_true", help="Pull or record every registered role")
    group.add_argument("--list", action="store_true", help="List all roles and manifest state")
    parser.add_argument("--verify", action="store_true", help="Verify existing manifest instead of downloading")
    args = parser.parse_args(argv)

    if args.list:
        _print_list()
        return 0
    keys = list(MODEL_REGISTRY) if args.all else [args.role] if args.role else []
    if not keys:
        parser.print_help()
        return 2
    if args.verify:
        results = [verify(key) if key in MODEL_REGISTRY else False for key in keys]
        return 0 if all(results) else 1
    results = [pull(key) for key in keys]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

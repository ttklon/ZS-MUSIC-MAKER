"""Integrity-checked reuse of a finished mix for a new mastering revision.

Only the actual mix is reused as audio. Other earlier stage records remain
provenance, not newly executed stages; no source report is modified.
"""
from __future__ import annotations

import copy
import hashlib
import os
import shutil
import tempfile
from pathlib import Path

from app.core.pipeline_runtime import _output
from app.pipeline import StageResult, StageStatus

REUSED_FOR_MASTER = (
    "_stage_analyze", "_stage_groove", "_stage_arrangement", "_stage_beat",
    "_stage_texture", "_stage_lyrics", "_stage_voice_synth", "_stage_rvc",
    "_stage_vocal_fx", "_stage_mix_and_sidechain",
)


def _sha256(path: Path, checkpoint=None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            if checkpoint is not None:
                checkpoint()
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def add_mix_integrity(report: dict, stage: StageResult, out_root: Path, warnings: list[str]) -> None:
    """Record a local mix's hash; a later revision verifies the copied bytes again."""
    out = _output(stage)
    if out.get("reused_from_project"):
        report["revision"] = {"kind": "master", "source_project": out["reused_from_project"]}
    if not stage.succeeded or not out.get("out_wav"):
        return
    try:
        root = out_root.resolve()
        path = Path(out["out_wav"]).resolve(strict=True)
        relative = path.relative_to(root)
        if not path.is_file():
            raise ValueError("mix is not a regular file")
        report["artifact_integrity"] = {"mix": {
            "relative_path": relative.as_posix(), "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }}
    except Exception as exc:  # noqa: BLE001 - rendering succeeds, revision is unavailable
        warnings.append(f"mix integrity not recorded; revision unavailable: {type(exc).__name__}: {exc}")


def _checked_mix(source: Path, report: dict) -> tuple[Path, dict]:
    manifest = report.get("artifact_integrity")
    record = manifest.get("mix") if isinstance(manifest, dict) else None
    if not isinstance(record, dict):
        raise ValueError("source has no mix integrity manifest; run a new full render first")
    rel = Path(str(record.get("relative_path") or ""))
    if rel.is_absolute() or not rel.parts or ".." in rel.parts:
        raise ValueError("invalid mix path in source report")
    root = source.resolve(strict=True)
    candidate = root / rel
    if candidate.is_symlink():
        raise ValueError("source mix must not be a symlink")
    mix = candidate.resolve(strict=True)
    if not mix.is_relative_to(root) or not mix.is_file():
        raise ValueError("source mix is outside its project or is not a file")
    expected = record.get("sha256")
    if (not isinstance(expected, str) or len(expected) != 64
            or any(c not in "0123456789abcdef" for c in expected)):
        raise ValueError("invalid source mix checksum")
    if type(record.get("bytes")) is not int or record["bytes"] <= 0:
        raise ValueError("invalid source mix size")
    if mix.stat().st_size != record["bytes"] or _sha256(mix) != expected:
        raise ValueError("source mix failed integrity check; it was changed or damaged")
    import soundfile as sf
    info = sf.info(str(mix))
    if info.frames <= 0 or info.samplerate <= 0 or info.channels <= 0:
        raise ValueError("source mix is not readable audio")
    return mix, record


def validate_master_source(source: Path, report: dict) -> tuple[Path, dict, dict]:
    """Validate source status, paths and mix bytes without writing anything."""
    if (report.get("dry_run") is not False or report.get("resume") is not False
            or "only" not in report or report["only"] not in (None, [])):
        raise ValueError("master revision requires a full non-resumed source render")
    verdict = report.get("verdict")
    if not isinstance(verdict, str) or verdict not in {"PASS", "PASS_BLOCKED", "PASS_WITH_FALLBACK", "PARTIAL", "BLOCKED_SIMULATION"}:
        raise ValueError("source report has an invalid or failed verdict")
    if not isinstance(report.get("warnings"), list) or any(not isinstance(w, str) for w in report["warnings"]):
        raise ValueError("source report has invalid warnings")
    rows = report.get("stages")
    if not isinstance(rows, list):
        raise ValueError("source report has no stage records")
    if any(not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"] for row in rows):
        raise ValueError("source report has invalid stage names")
    by_name = {row["name"]: row for row in rows}
    if len(by_name) != len(rows) or any(name not in by_name for name in REUSED_FOR_MASTER):
        raise ValueError("source report has missing or duplicate stages")
    if by_name["_stage_mix_and_sidechain"].get("status") not in ("OK", "FALLBACK"):
        raise ValueError("source mix stage did not succeed")
    allowed = {status.value for status in StageStatus}
    for name in REUSED_FOR_MASTER:
        row = by_name[name]
        if not isinstance(row.get("status"), str) or row["status"] not in allowed:
            raise ValueError(f"invalid source status for {name}")
        if (not isinstance(row.get("output"), (dict, type(None)))
                or not isinstance(row.get("reason"), (str, type(None)))
                or not isinstance(row.get("attempts"), list)
                or any(not isinstance(a, str) for a in row["attempts"])):
            raise ValueError(f"invalid source stage data for {name}")
    mix, integrity = _checked_mix(source, report)
    mix_output = by_name["_stage_mix_and_sidechain"].get("output") or {}
    source_output = mix_output.get("out_wav") if isinstance(mix_output, dict) else None
    matched = bool(source_output and Path(str(source_output)).resolve() == mix)
    # New reports preserve the original root so a copied/moved project on the
    # same platform can still be opened without trusting stale absolute paths.
    old_root = report.get("project_root")
    if not matched and source_output and isinstance(old_root, str) and Path(old_root).is_absolute():
        try:
            old_rel = Path(str(source_output)).resolve().relative_to(Path(old_root).resolve())
            matched = old_rel == Path(integrity["relative_path"])
        except ValueError:
            matched = False
    if not matched:
        raise ValueError("source mix output does not match its integrity record")
    return mix, integrity, by_name


def prepare_master_revision(source: Path, destination: Path, report: dict) -> dict[str, StageResult]:
    """Freeze and verify the source mix into a separate destination, retaining statuses."""
    source, destination = Path(source), Path(destination)
    src_root, dst_root = source.resolve(), destination.resolve()
    if src_root == dst_root or dst_root.is_relative_to(src_root) or src_root.is_relative_to(dst_root):
        raise ValueError("revision must use a separate project directory")
    mix, integrity, by_name = validate_master_source(source, report)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / "reused_mix.wav"
    if target.exists():
        raise FileExistsError("revision destination already contains a reused mix")
    fd, name = tempfile.mkstemp(prefix=".mix-", suffix=".tmp", dir=destination)
    os.close(fd)
    temporary = Path(name)
    try:
        shutil.copyfile(mix, temporary)
        if temporary.stat().st_size != integrity["bytes"] or _sha256(temporary) != integrity["sha256"]:
            raise ValueError("copied mix failed integrity check")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    reused: dict[str, StageResult] = {}
    for name in REUSED_FOR_MASTER:
        row = by_name[name]
        try:
            status = StageStatus(row["status"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"invalid source status for {name}") from exc
        output = copy.deepcopy(row.get("output")) if isinstance(row.get("output"), dict) else {}
        output.update(reused=True, reused_from_project=str(report.get("project_id") or "unknown"))
        if name == "_stage_mix_and_sidechain":
            output["out_wav"] = str(target)
            output["reused_source_warnings"] = [str(w) for w in (report.get("warnings") or []) if isinstance(w, str)]
        reused[name] = StageResult(name=name, status=status, output=output,
                                   reason=row.get("reason"), attempts=list(row.get("attempts") or []))
    return reused

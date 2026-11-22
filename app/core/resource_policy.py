"""Resource provenance inventory. Code licenses never automatically license weights.

This is an engineering gate, not legal advice. Unreviewed terms fail commercial use.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def resource_inventory(root: Path = ROOT) -> dict:
    from app.ai.model_catalog import MODEL_REGISTRY

    resources = [{"id": "application_code", "kind": "code", "source": "LICENSE",
                  "declared_license": "MIT", "license_file_present": (root / 'LICENSE').is_file(), "terms_reviewed": False,
                  "commercial_use_verified": False}]
    for role, meta in MODEL_REGISTRY.items():
        source = meta.get('hf_repo') or ''
        resources.append({"id": role, "kind": "model_weights" if source else "runtime_dependency",
            "source": 'https://huggingface.co/' + source if source and source != 'user_supplied' else source,
            "declared_license": "not_verified", "terms_reviewed": False,
            "commercial_use_verified": False, "revision": None})
    for name, source in [('silero', 'https://github.com/snakers4/silero-models'),
                         ('ollama', 'https://github.com/ollama/ollama'),
                         ('bark', 'https://github.com/suno-ai/bark'),
                         ('agent_qwen3_4b', 'https://ollama.com/library/qwen3:4b'),
                         ('acestep_external', 'user_configured_local_server')]:
        resources.append({"id": name, "kind": "optional_engine_and_weights", "source": source,
                          "declared_license": "not_verified", "terms_reviewed": False,
                          "commercial_use_verified": False})
    manifest = json.loads((root / 'data/samples/manifest.json').read_text(encoding='utf-8'))
    for entries in manifest['instruments'].values():
        for item in entries:
            target = (root / 'data/samples' / item['file']).resolve()
            base = (root / 'data/samples').resolve()
            if not target.is_relative_to(base):
                raise ValueError('Sample manifest path escapes bank')
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            resources.append({"id": 'sample:' + item['file'], "kind": "bundled_sample",
                "source": item.get('source'), "origin": item.get('origin'),
                "declared_license": item.get('license', 'unknown'), "sha256": digest,
                "integrity_matches": digest == item.get('sha256'), "terms_reviewed": False,
                "commercial_use_verified": False})
    return {"schema": 1, "resources": resources, "coverage_complete": False,
            "gaps": ["Upstream terms/revisions not independently reviewed", "Python/npm bundled dependency notices incomplete",
                     "Actual used-resource manifest not yet enforced at export", "User voice permissions require explicit evidence"]}


def commercial_decision(resources: list[dict]) -> dict:
    reasons = []
    if not resources:
        reasons.append('No used-resource manifest')
    for resource in resources:
        allowed_licenses = {'MIT', 'Apache-2.0', 'CC0-1.0', 'CC-BY-4.0', 'BSD-2-Clause', 'BSD-3-Clause'}
        if (resource.get('terms_reviewed') is not True or resource.get('commercial_use_verified') is not True
                or not resource.get('source') or resource.get('declared_license') not in allowed_licenses
                or not re.fullmatch(r'[0-9a-f]{64}', str(resource.get('terms_sha256', '')))):
            reasons.append(str(resource.get('id', '?')) + ': commercial permission not verified')
        if resource.get('integrity_matches') is False:
            reasons.append(str(resource.get('id', '?')) + ': integrity mismatch')
    return {"allowed": not reasons, "reasons": reasons, "legal_advice": False}

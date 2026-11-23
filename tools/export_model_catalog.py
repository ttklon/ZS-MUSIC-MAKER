"""Generate the read-only desktop projection of the canonical Python catalogue."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.ai.model_catalog import MODEL_REGISTRY
from app.ai.engine_profiles import ENGINE_PROFILE, PROFILES, profile


def catalog():
    roles = []
    for key, spec in MODEL_REGISTRY.items():
        roles.append(dict(id=key, **spec, revision=spec.get('revision'),
                          profile=ENGINE_PROFILE[spec['engine']], inference_verified=False,
                          source_pinned=bool(spec.get('revision')), terms_reviewed=False))
    return dict(schema=1, roles=roles, profiles=[profile(name) for name in PROFILES])


def main():
    output = ROOT / 'data/desktop/model-catalog.json'
    text = json.dumps(catalog(), ensure_ascii=False, indent=2) + '\n'
    if '--check' in sys.argv:
        if not output.is_file() or output.read_text(encoding='utf-8') != text:
            raise SystemExit('Stale desktop model catalogue; run tools/export_model_catalog.py')
    else:
        output.write_text(text, encoding='utf-8')
    print('Model catalogue projection matches; inference and source revisions NOT verified')


if __name__ == '__main__':
    main()

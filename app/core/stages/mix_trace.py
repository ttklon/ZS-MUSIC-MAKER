"""File-identity trace around the actual mixer; not a hostile-filesystem sandbox."""
from pathlib import Path

from app.core.revision import _sha256


def fingerprint(path):
    candidate = Path(path).resolve(strict=True)
    return {'path': str(candidate), 'sha256': _sha256(candidate), 'bytes': candidate.stat().st_size}


def prepare_traced_mix(beat_wav, voice_wav, out_dir, *, vocal_offset_ms=0):
    from modules.mix.bus import prepare_mix
    before = fingerprint(beat_wav)
    result = prepare_mix(beat_wav, voice_wav, out_dir, vocal_offset_ms=vocal_offset_ms)
    if result.get('ok'):
        if fingerprint(beat_wav) != before:
            raise ValueError('Instrumental input changed during mixing')
        result['source_trace'] = {'schema': 1, 'beat': before,
                                  'mix': fingerprint(result['out_wav']),
                                  'vocal_requested': voice_wav is not None}
    return result

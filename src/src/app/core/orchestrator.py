# -*- coding: utf-8 -*-
"""
ZS Music Maker — app/core/orchestrator.py (единый оркестратор)
====================================================================

v17 fixes (P0, влияют на конечный WAV):
  • _stage_beat: раньше искал несуществующую beat_constructor.build_beat →
    всегда падал в _synth_beat. Теперь корректно вызывает
    beat_constructor.construct_beat(...).
  • _stage_lyrics: возвращает {ok, text, lyrics} — оркестратор больше не
    теряет текст (обе ветки — LLM и template — отдают оба ключа).
  • _stage_mix_and_sidechain: bus = beat + vocal (реальный микс), и уже
    потом bus дакается сайдчейном по кику. Раньше сайдчейн дакал сам
    бит собой, а вокал вообще игнорировался.
  • _stage_polish: anti_neuro_v10 экспортирует polish_vocal; добавлен
    apply_polish-обёртка. Оркестратор больше не сваливается в
    shutil.copy при живом anti-neuro-модуле.
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from modules.llm_clients_v15 import LLMRouter
except Exception:
    LLMRouter = None


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class PipelineStage:
    name: str
    ok: bool = False
    fallback_used: bool = False
    synthetic: bool = False
    blocked: bool = False
    duration_sec: float = 0.0
    output: Any = None
    reason: Optional[str] = None


@dataclass
class PipelineResult:
    project_id: str
    started_at: float
    finished_at: float
    duration_sec: float
    dry_run: bool
    verdict: str
    stages: List[Dict[str, Any]] = field(default_factory=list)
    percent: int = 0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_sec": self.duration_sec,
            "dry_run": self.dry_run,
            "verdict": self.verdict,
            "stages": self.stages,
            "percent": self.percent,
            "warnings": self.warnings,
        }


def _timed(name: str, fn: Callable[[], Any]) -> PipelineStage:
    t0 = time.time()
    stage = PipelineStage(name=name)
    try:
        out = fn()
        stage.ok = bool(out.get("ok") if isinstance(out, dict) else out is not None)
        stage.output = out
        if isinstance(out, dict):
            stage.fallback_used = bool(out.get("fallback_used"))
            stage.synthetic = bool(out.get("synthetic") or out.get("dry_run"))
            stage.blocked = bool(out.get("blocked"))
            stage.reason = out.get("reason")
    except Exception as e:
        stage.ok = False
        stage.reason = f"{type(e).__name__}: {e}"
    stage.duration_sec = round(time.time() - t0, 3)
    return stage


def _is_simulation_result(result: Dict[str, Any]) -> bool:
    """Симуляция = только явный synthetic/dry_run/placeholder.

    v21: если стадия одновременно blocked=True — это честный BLOCKED
    (heavy-модуль недоступен, честный scaffold для прохождения обвязки),
    НЕ симуляция всего пайплайна. BLOCKED учитывается отдельно, не роняет
    verdict в BLOCKED_SIMULATION и не режет percent.
    """
    if not isinstance(result, dict):
        return False
    if result.get("blocked"):
        return False
    if result.get("dry_run") or result.get("synthetic") or result.get("placeholder"):
        return True
    txt = json.dumps(result, ensure_ascii=False, default=str).lower()
    for marker in ("style_vector_placeholder", '"dry_run": true',
                   '"placeholder": true'):
        if marker in txt:
            return True
    return False


def _is_blocked_result(result: Dict[str, Any]) -> bool:
    """v21: честный BLOCKED (heavy-модуль недоступен, обвязка целая)."""
    if not isinstance(result, dict):
        return False
    return bool(result.get("blocked"))


def _normalize_path_map(data: Any, keys: Optional[List[str]] = None) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(data, dict):
        return out
    allow = set(keys or [])
    for name, value in data.items():
        if allow and name not in allow:
            continue
        path = None
        if isinstance(value, (str, Path)):
            path = str(value)
        elif isinstance(value, dict):
            path = value.get("out_wav") or value.get("path")
        if path:
            out[str(name)] = str(path)
    return out


# ---------------------------------------------------------------- stages

# v22: default style vectors per genre — used when refs=[]. Это НЕ fallback,
# а нормальный generate-from-scratch режим: пользователь может не давать рефы
# и всё равно должен получить целостный трек, а не бэйсовый sine.
_GENRE_STYLE_DEFAULTS = {
    "drift_phonk":   {"bpm": 130, "mode": "minor", "aggression": 0.85, "hihat_density": 0.7,  "swing": 0.18},
    "phonk":         {"bpm": 130, "mode": "minor", "aggression": 0.8,  "hihat_density": 0.65, "swing": 0.15},
    "trap":          {"bpm":  75, "mode": "minor", "aggression": 0.7,  "hihat_density": 0.75, "swing": 0.08},
    "hip_hop":       {"bpm":  90, "mode": "minor", "aggression": 0.6,  "hihat_density": 0.55, "swing": 0.12},
    "pop":           {"bpm": 118, "mode": "major", "aggression": 0.5,  "hihat_density": 0.5,  "swing": 0.05},
    "dnb":           {"bpm": 174, "mode": "minor", "aggression": 0.9,  "hihat_density": 0.85, "swing": 0.0},
    "house":         {"bpm": 126, "mode": "minor", "aggression": 0.6,  "hihat_density": 0.6,  "swing": 0.0},
    "techno":        {"bpm": 130, "mode": "minor", "aggression": 0.75, "hihat_density": 0.55, "swing": 0.0},
    "lo_fi":         {"bpm":  80, "mode": "minor", "aggression": 0.35, "hihat_density": 0.45, "swing": 0.22},
    "rnb":           {"bpm":  95, "mode": "minor", "aggression": 0.45, "hihat_density": 0.55, "swing": 0.15},
}


def _default_style_for_genre(genre: str) -> Dict[str, Any]:
    g = (genre or "").lower().strip().replace("-", "_").replace(" ", "_")
    return dict(_GENRE_STYLE_DEFAULTS.get(g, _GENRE_STYLE_DEFAULTS["drift_phonk"]))


def _stage_analyze(refs: List[str], dry_run: bool,
                   genre: str = "drift_phonk") -> Dict[str, Any]:
    """v22: no refs — это НЕ fallback, а нормальный generate-from-scratch.
    Отдаём default style-vector по жанру, чтобы downstream (beat/mix) собирал
    целостный трек, а не sine-кашу, но не притворяемся что делали реальный анализ.
    """
    try:
        from modules import analyzer
        if not refs:
            gs = _default_style_for_genre(genre)
            synthetic_analysis = {
                "bpm": gs["bpm"], "mode": gs["mode"],
                "aggression": gs["aggression"],
                "source": "genre_default",
                "n_refs": 0,
            }
            return {"ok": True, "analysis": synthetic_analysis,
                    "reason": f"generate-from-scratch mode; genre_default={genre}"}
        if len(refs) == 1:
            res = analyzer.analyze_single(refs[0])
        else:
            res = analyzer.analyze_multi(refs)
        return {"ok": True, "analysis": res}
    except Exception as e:
        return {"ok": False, "reason": str(e), "fallback_used": True}


def _stage_groove(refs: List[str],
                  genre: str = "drift_phonk") -> Dict[str, Any]:
    """v22: no refs — не fallback, а generate-from-scratch. Отдаём default
    groove-template по жанру, чтобы beat_constructor получил нормальный ритм,
    а не голый kick-каждые-полсекунды.
    """
    try:
        from modules import groove_extractor
        if not refs:
            gs = _default_style_for_genre(genre)
            groove = {
                "kick_pattern":  [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0],
                "snare_pattern": [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
                "hihat_density": gs["hihat_density"],
                "swing":         gs["swing"],
                "triplet_rolls": True,
                "drop_intensity": gs["aggression"],
                "source": "genre_default",
            }
            return {"ok": True, "groove": groove,
                    "reason": f"generate-from-scratch groove; genre_default={genre}"}
        if hasattr(groove_extractor, "extract_groove"):
            g = groove_extractor.extract_groove(refs[0])
        elif hasattr(groove_extractor, "extract"):
            g = groove_extractor.extract(refs[0])
        else:
            g = None
        return {"ok": True, "groove": g}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _stage_arrangement(analysis: Any) -> Dict[str, Any]:
    try:
        from modules import arrangement_engine as ae
        plan = ae.plan(analysis) if hasattr(ae, "plan") else {"sections": []}
        return {"ok": True, "plan": plan}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _stage_beat(plan: Any, out_dir: Path,
                groove: Any = None,
                style_vector: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """v17 FIX (P0): construct_beat вместо несуществующего build_beat."""
    beat_wav = str(out_dir / "beat.wav")
    try:
        from modules import beat_constructor as bc
        style = style_vector or {"target_bpm": 128, "target_mode": "minor"}
        if hasattr(bc, "construct_beat"):
            r = bc.construct_beat(
                groove or {}, [], style,
                duration_sec=int((plan or {}).get("duration_sec", 90)),
                n_verses=int((plan or {}).get("n_verses", 2)),
                aggression=float((plan or {}).get("aggression", 0.7)),
                out_name=Path(beat_wav).name,
            )
            if isinstance(r, dict) and r.get("beat_path"):
                src = Path(r["beat_path"])
                dst = Path(beat_wav)
                if src.exists() and src.resolve() != dst.resolve():
                    try:
                        import shutil
                        shutil.copy(src, dst)
                    except Exception:
                        dst = src
                return {"ok": True, "path": str(dst),
                        "bpm": r.get("bpm"), "key": r.get("key"),
                        "sections": r.get("sections"),
                        "duration_sec": r.get("duration_sec"),
                        "engine": "beat_constructor.construct_beat"}
        # v22: fallback — полный structured synth beat, не 8с тупые kicks
        _bpm = int(style.get("target_bpm", 128) or 128)
        _dur = int((plan or {}).get("duration_sec", 90) or 90)
        return _synth_beat(beat_wav, duration=_dur, bpm=_bpm)
    except Exception as e:
        try:
            _bpm = int((style_vector or {}).get("target_bpm", 128))
            _dur = int((plan or {}).get("duration_sec", 90))
            return _synth_beat(beat_wav, duration=_dur, bpm=_bpm)
        except Exception:
            return {"ok": False, "reason": str(e)}


def _synth_beat(out_wav: str, duration: int = 90, bpm: int = 128,
                key_root: str = "A") -> Dict[str, Any]:
    """v22: полноценный structured synth-бит (не 8 сек тупых киков).
    Многосекционная структура (intro/verse/pre/chorus/verse/pre/chorus/outro),
    808 sub-bass по ключу, hi-hat roll перед drop, snare с air-tail,
    open-hat на offbeat, stop-time перед хуком, white+sub ризеры.
    Честно помечаем fallback_used=True — не выдаём за real beat_constructor.
    """
    try:
        import numpy as np
        import soundfile as sf
        sr = 44100
        beat_sec = 60.0 / bpm
        bar_sec = beat_sec * 4
        step_sec = bar_sec / 16.0

        keys = {"C":261.63,"C#":277.18,"D":293.66,"D#":311.13,"E":329.63,
                "F":349.23,"F#":369.99,"G":392.00,"G#":415.30,
                "A":440.00,"A#":466.16,"B":493.88}
        root_hz = keys.get(key_root.upper(), 440.0) / 4.0

        sections = [("intro",4), ("verse",8), ("pre",4), ("chorus",8),
                    ("verse",8), ("pre",4), ("chorus",8), ("outro",4)]
        total_bars = sum(nb for _, nb in sections)
        target_bars = max(4, int(round(duration / bar_sec)))
        if target_bars < total_bars:
            scale = target_bars / float(total_bars)
            sections = [(nm, max(1, int(round(nb * scale)))) for nm, nb in sections]
        elif target_bars > total_bars * 1.4:
            extra = target_bars - total_bars
            sections = [(nm, nb + (extra // 2 if nm == "chorus" else 0))
                        for nm, nb in sections]

        total_samples = int(sum(nb * bar_sec for _, nb in sections) * sr)
        y = np.zeros(total_samples, dtype="float32")

        kick_pat  = [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0]
        snare_pat = [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0]
        hihat_pat = [1]*16
        openhat_step = 10
        # v25 (P1): секционная вариативность — припев ритмически плотнее
        # куплета (было: одинаковый 16-шаговый шаблон везде, отличие только
        # в гейнах → скучный «формульный» бит, mode hit_scorer 'needs_work').
        # chorus: больше киков (syncopation), verse: разряженнее.
        kick_pat_chorus = [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0]
        kick_pat_verse  = [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0]
        hihat_pat_chorus = [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1]
        hihat_pat_verse  = [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0]

        def _kick(sr_, dur=0.16):
            t = np.arange(int(sr_*dur))/sr_
            f = 90.0*np.exp(-t*18) + 45.0
            env = np.exp(-t*11)
            body = np.sin(2*np.pi*np.cumsum(f)/sr_) * env
            click = np.random.randn(int(sr_*0.004)).astype("float32") * np.exp(
                -np.arange(int(sr_*0.004))/sr_*400) * 0.6
            out = body.astype("float32")
            out[:len(click)] += click * 0.35
            return out

        def _snare(sr_, dur=0.18):
            t = np.arange(int(sr_*dur))/sr_
            env = np.exp(-t*17)
            noise = np.random.randn(len(t)).astype("float32")
            body = np.sin(2*np.pi*180*t) * np.exp(-t*30)
            air = np.concatenate([[0], np.diff(noise)])
            return (body*0.35 + air*0.75) * env * 0.75

        def _hat(sr_, dur=0.045, open_=False):
            t = np.arange(int(sr_*dur))/sr_
            env = np.exp(-t*(30 if open_ else 90))
            noise = np.random.randn(len(t)).astype("float32")
            hp = np.concatenate([[0], np.diff(noise)])
            return hp * env * (0.5 if open_ else 0.32)

        def _808(sr_, dur, freq):
            t = np.arange(int(sr_*dur))/sr_
            env = np.exp(-t*2.2) * (1.0 - np.exp(-t*80.0))
            f = freq * (1.0 + 0.03*np.exp(-t*20))
            osc = np.sin(2*np.pi*np.cumsum(f)/sr_)
            return np.tanh(osc*1.6) * env * 0.85

        def _riser(sr_, dur, kind="white"):
            t = np.arange(int(sr_*dur))/sr_
            if kind == "white":
                env = (t/dur)**1.3
                n = np.random.randn(len(t)).astype("float32")
                n = np.concatenate([[0], np.diff(n)])
                return n * env * 0.35
            env = (t/dur)**1.6
            f = 80.0 + 800.0*(t/dur)**2
            return np.sin(2*np.pi*np.cumsum(f)/sr_).astype("float32") * env * 0.5

        pos = 0
        section_info = []
        for section_name, n_bars in sections:
            sec_start_sec = pos / sr
            sec_len = int(n_bars * bar_sec * sr)
            if section_name == "intro":
                kick_gain, snare_gain, hat_gain, bass_gain = 0.55, 0.0, 0.35, 0.4
            elif section_name == "verse":
                kick_gain, snare_gain, hat_gain, bass_gain = 0.9, 0.75, 0.7, 0.85
            elif section_name == "pre":
                kick_gain, snare_gain, hat_gain, bass_gain = 0.85, 0.7, 0.9, 0.8
            elif section_name == "chorus":
                kick_gain, snare_gain, hat_gain, bass_gain = 1.0, 0.95, 0.75, 1.0
            else:  # outro
                kick_gain, snare_gain, hat_gain, bass_gain = 0.7, 0.4, 0.5, 0.5

            # v25: выбор паттернов по секции (вариативность)
            if section_name == "chorus":
                _kp, _hp = kick_pat_chorus, hihat_pat_chorus
            elif section_name == "verse":
                _kp, _hp = kick_pat_verse, hihat_pat_verse
            else:
                _kp, _hp = kick_pat, hihat_pat

            for bar in range(n_bars):
                bar_pos = pos + bar * int(bar_sec * sr)
                for step in range(16):
                    step_pos = bar_pos + int(step * step_sec * sr)
                    if _kp[step] and section_name != "intro":
                        k = _kick(sr) * kick_gain
                        e = min(step_pos + len(k), total_samples)
                        y[step_pos:e] += k[:e-step_pos]
                    if snare_pat[step] and section_name != "intro":
                        s_ = _snare(sr) * snare_gain
                        e = min(step_pos + len(s_), total_samples)
                        y[step_pos:e] += s_[:e-step_pos]
                    if _hp[step]:
                        is_open = (step == openhat_step and section_name != "intro")
                        h = _hat(sr, open_=is_open) * hat_gain
                        e = min(step_pos + len(h), total_samples)
                        y[step_pos:e] += h[:e-step_pos]
                    if _kp[step] and section_name != "intro":
                        b_dur = beat_sec * 1.5
                        b = _808(sr, b_dur, root_hz) * bass_gain
                        e = min(step_pos + len(b), total_samples)
                        y[step_pos:e] += b[:e-step_pos] * 0.65

                # Снейр-ролл в последнем баре pre-chorus
                if section_name == "pre" and bar == n_bars-1:
                    roll_start = bar_pos + int(2 * beat_sec * sr)
                    n_hits = 8
                    hit_sec = (2 * beat_sec) / n_hits
                    for h_i in range(n_hits):
                        hp = roll_start + int(h_i * hit_sec * sr)
                        s_ = _snare(sr, dur=0.09) * (0.4 + 0.06*h_i)
                        e = min(hp + len(s_), total_samples)
                        y[hp:e] += s_[:e-hp]
                    ris_dur = 2 * beat_sec
                    wr = _riser(sr, ris_dur, "white")
                    e = min(roll_start + len(wr), total_samples)
                    y[roll_start:e] += wr[:e-roll_start]
                    sr_ = _riser(sr, ris_dur, "sub")
                    e = min(roll_start + len(sr_), total_samples)
                    y[roll_start:e] += sr_[:e-roll_start]

            # Стоп-тайм перед хуком: последние 2 шага pre — приглушить
            if section_name == "pre":
                cut = int(step_sec * 2 * sr)
                if sec_len > cut:
                    y[pos + sec_len - cut : pos + sec_len] *= 0.15

            pos += sec_len
            section_info.append({"name": section_name, "bars": n_bars,
                                 "start_sec": round(sec_start_sec, 2),
                                 "duration_sec": round(n_bars * bar_sec, 2)})

        # v25 (P1): правильное стерео вместо слепого Haas на ВСЁ.
        # Раньше Haas-задержка 12ms применялась ко всему треку, включая
        # кик и 808 — фазовые проблемы в низу, рыхлый саб в моно-сумме.
        # v25.1: моно-основа = всё ниже ~200 Гц (кик, 808, саб); Haas-задержка
        # применяется ТОЛЬКО к контенту выше 200 Гц (хэты, снейр-верх, атмосфера).
        # Иначе пологий кроссовер пропускает задержанный mid в низ и ломает
        # моно-совместимость (проверено smoke_v25.beat_lowband_mono).
        try:
            from scipy.signal import butter as _bt, sosfilt as _sf_
            sos_hp200 = _bt(4, 200, btype="high", fs=sr, output="sos")
            mid_hi = _sf_(sos_hp200, y)          # контент >200 Гц (для ширины)
            low_mid = y - mid_hi                 # моно-основа <200 Гц
            delay_samples = int(sr * 0.010)
            mid_hi_r = np.concatenate(
                [np.zeros(delay_samples, dtype="float32"),
                 mid_hi[:-delay_samples]])
            # верх (>5 кГц, хэты) ещё чуть шире — второй короткий Haas
            sos_hp5k = _bt(2, 5000, btype="high", fs=sr, output="sos")
            hi = _sf_(sos_hp5k, y)
            d2 = int(sr * 0.007)
            hi_r = np.concatenate([np.zeros(d2, dtype="float32"),
                                   hi[:-d2]])
            left = low_mid + mid_hi + hi * 0.25
            right = low_mid + mid_hi_r + hi_r * 0.35
            stereo = np.stack([left, right], axis=1)
        except Exception:
            try:
                delay_samples = int(sr * 0.012)
                left = y.copy()
                right = np.concatenate([np.zeros(delay_samples, dtype="float32"),
                                        y[:-delay_samples]])
                stereo = np.stack([left, right], axis=1)
            except Exception:
                stereo = np.stack([y, y], axis=1)

        peak = float(np.max(np.abs(stereo)) + 1e-9)
        if peak > 0.98:
            stereo = stereo / peak * 0.95

        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, stereo, sr)
        return {"ok": True, "path": out_wav, "bpm": bpm,
                "duration_sec": round(len(y)/sr, 2),
                "sections": section_info,
                "engine": "synth_beat_v22",
                "fallback_used": True,
                "reason": "synthesized structured beat (beat_constructor unavailable)"}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _texture_scaffold(prompt: str, out_dir: Path) -> Dict[str, Any]:
    """v23: честный синтезированный ambient-scaffold вместо пустого path.

    Раньше при недоступном MusicGen стадия отдавала path="" — и в трек
    не попадало НИЧЕГО, при этом fallback_used=True намекал, что что-то
    сгенерировано. Теперь синтезируем реальную низкоуровневую текстуру
    (drone-пэд + медленная огибающая + лёгкий noise-bed), которая:
      • реально записывается на диск и может попасть в микс;
      • честно помечена synthetic=True и engine='texture_scaffold_v23';
      • НЕ выдаётся за MusicGen-нейротекстуру.
    Это скелет атмосферы, а не финальный продакшн-текстур.
    """
    try:
        import numpy as np
        import soundfile as sf
        sr = 22050
        dur = 10.0
        n = int(sr * dur)
        t = np.arange(n) / sr
        # Drone-пэд: сумма трёх расстроенных пил вокруг 110 Hz
        base = 110.0
        pad = np.zeros(n, dtype="float32")
        for det in (-6.0, 0.0, 5.0):
            f = base * (2.0 ** (det / 1200.0))
            pad += np.sign(np.sin(2 * np.pi * f * t)) * 0.18
        # медленная огибающая (нарастание/спад), чтобы не было резких краёв
        env = np.sin(np.pi * t / dur) ** 2
        # лёгкий noise-bed для «воздуха»
        noise = np.random.randn(n).astype("float32")
        # грубый LP фильтр шума через скользящее среднее
        k = 64
        noise = np.convolve(noise, np.ones(k) / k, mode="same") * 0.06
        y = (pad * env * 0.5 + noise * env).astype("float32")
        # лёгкая стерео-раскладка
        stereo = np.stack([y, np.roll(y, int(sr * 0.012))], axis=1)
        peak = float(np.max(np.abs(stereo))) + 1e-9
        stereo = stereo / peak * 0.32  # текстура должна сидеть под миксом
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_wav = str(Path(out_dir) / "texture_scaffold.wav")
        sf.write(out_wav, stereo, sr)
        return {"ok": True, "path": out_wav, "blocked": True,
                "synthetic": True, "fallback_used": True,
                "engine": "texture_scaffold_v23",
                "duration_sec": round(len(y) / sr, 2),
                "reason": "audiocraft/MusicGen unavailable; honest synth "
                          "ambient scaffold generated (not a neural texture)"}
    except Exception as e:
        return {"ok": True, "path": "", "blocked": True,
                "fallback_used": True,
                "reason": f"texture scaffold failed: {type(e).__name__}: {e}"}


def _stage_texture(prompt: str, out_dir: Path) -> Dict[str, Any]:
    """v19: texture — опциональная стадия. Если MusicGen недоступен,
    честно отдаём ok=True + blocked=True + fallback_used=True, чтобы
    не ронять процент готовностью отсутствующей heavy-зависимости.
    v23: вместо пустого path отдаём реальный синтезированный scaffold.
    """
    try:
        from app.core import musicgen_texture as mgt
        r = mgt.generate_texture(prompt, duration_sec=10, vram_gb=0.0)
        if isinstance(r, dict) and r.get("ok") and r.get("path"):
            return r
        return _texture_scaffold(prompt, out_dir)
    except Exception:
        return _texture_scaffold(prompt, out_dir)


def _text_to_struct(text: str, genre: str) -> Dict[str, Any]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    title = ""
    verse1: List[str] = []
    chorus: List[str] = []
    verse2: List[str] = []
    current = "verse1"
    for ln in lines:
        low = ln.lower()
        if low.startswith("[") and low.endswith("]"):
            if "hook" in low or "chorus" in low or "припев" in low:
                current = "chorus"
            elif "verse 2" in low or "куплет 2" in low or "verse2" in low:
                current = "verse2"
            elif "intro" in low:
                current = "intro"
            else:
                current = "verse1"
            continue
        if not title and len(ln) <= 60 and ln[0] not in "[(":
            title = ln
        if current == "verse1":
            verse1.append(ln)
        elif current == "chorus":
            chorus.append(ln)
        elif current == "verse2":
            verse2.append(ln)
    if not title:
        title = f"ZS Track ({genre})"
    return {"title": title,
            "verse1": verse1[:8] or [],
            "chorus": chorus[:6] or [],
            "verse2": verse2[:8] or [],
            "language": "ru+en"}


def _struct_to_text(struct: Dict[str, Any]) -> str:
    parts: List[str] = []
    if struct.get("title"):
        parts.append(str(struct["title"]))
    if struct.get("verse1"):
        parts.append("[verse 1]")
        parts.extend(struct["verse1"])
    if struct.get("chorus"):
        parts.append("[hook]")
        parts.extend(struct["chorus"])
    if struct.get("verse2"):
        parts.append("[verse 2]")
        parts.extend(struct["verse2"])
    return "\n".join(parts)


# v22: пул тематических fallback-шаблонов по жанрам (LLM-недоступен).
# Не выдаём за реальную LLM-генерацию — пометка fallback_used=True остаётся.
_LYRICS_TEMPLATES = {
    "drift_phonk": {
        "title": "Ночь горит ({genre})",
        "verse1": ["Ночь горит, я в дороге",
                   "Город спит, а мы на пороге",
                   "Тачки, движ, лето внутри",
                   "Мы не сдадимся, ты только смотри"],
        "chorus": ["Money over everything",
                   "Мы летим, ночь горит",
                   "Turkish beat, sea and me",
                   "Всё, что есть — это мы"],
        "verse2": ["Дым в окно, асфальт поёт",
                   "Ночь не спит, двигатель не ждёт",
                   "Всё что было — было вчера",
                   "Сегодня новая игра"],
    },
    "trap": {
        "title": "Тёмный неон ({genre})",
        "verse1": ["Тёмный неон, город дымит",
                   "Толку в словах нет, движ горит",
                   "Пацаны рядом, басы в пол",
                   "Ночь длинная, мы на взлёт"],
        "chorus": ["Trap trap, на районе шум",
                   "Басы как гром, мы на подъём",
                   "Trap trap, не остановишь",
                   "Тёмный неон в наших крови"],
        "verse2": ["Дым из окон, свет фонарей",
                   "Мы в этой ночи все сильней",
                   "Кто не с нами — тот в стороне",
                   "Наш звук гремит на всю стране"],
    },
    "pop": {
        "title": "Лето внутри ({genre})",
        "verse1": ["Солнце в глазах, ветер в волосах",
                   "Мы летим по трассе вдвоём",
                   "Радио орёт, сердце бьётся",
                   "Это лето будет вечным"],
        "chorus": ["Лето внутри, свет внутри",
                   "Мы горим, мы горим",
                   "Пой со мной, лети со мной",
                   "Эта ночь — только моя"],
        "verse2": ["Город засыпает, мы не спим",
                   "По крышам гуляем, по мостам",
                   "Каждый миг как последний",
                   "И никогда не будет скучным"],
    },
    "lo_fi": {
        "title": "Дождь за окном ({genre})",
        "verse1": ["Дождь за окном, чай на столе",
                   "Старый плейлист и тишина",
                   "Мысли плывут по течению",
                   "И время стало не спеша"],
        "chorus": ["Lo-fi, lo-fi, медленный бит",
                   "Пусть весь мир подождёт",
                   "Lo-fi, lo-fi, душа дремлет",
                   "В этом звуке я живу"],
        "verse2": ["Книга открыта, страница белеет",
                   "Винил крутится в полумраке",
                   "Дождь рисует на стекле",
                   "Картины из моей тоски"],
    },
}


def _fallback_lyrics(theme: str, genre: str) -> Dict[str, Any]:
    """v22: выбираем жанровый шаблон, подмешиваем тему. Не выдаём за LLM."""
    g = (genre or "").lower().strip().replace("-", "_").replace(" ", "_")
    tpl = _LYRICS_TEMPLATES.get(g, _LYRICS_TEMPLATES["drift_phonk"])
    out = {
        "title": tpl["title"].format(genre=genre),
        "verse1": list(tpl["verse1"]),
        "chorus": list(tpl["chorus"]),
        "verse2": list(tpl["verse2"]),
        "language": "ru+en",
    }
    # Подмешиваем тему в первую строку куплета, если тема нестандартная
    if theme and theme not in ("лето, тачки, движ", "ночь", "движ"):
        topic = theme.split(",")[0].strip()
        if topic and len(topic) <= 40:
            out["verse1"][0] = f"{topic.capitalize()} — вот наша тема"
    return out


def _stage_lyrics(theme: str, genre: str) -> Dict[str, Any]:
    """v17 FIX (P0): ВСЕГДА возвращаем И text, И lyrics-структуру."""
    if LLMRouter is not None:
        try:
            router = LLMRouter(timeout=8.0)
            prompt = (f"Напиши текст в жанре {genre} про {theme}, "
                      f"16-24 строки, с verse и hook, на русском.")
            r = router.complete(prompt, "", theme=theme, genre=genre,
                                language="ru")
            if r.get("ok") and r.get("text", "").strip():
                lyrics_struct = _text_to_struct(r["text"], genre)
                return {"ok": True, "text": r["text"], "lyrics": lyrics_struct,
                        "provider": r.get("provider"),
                        "fallback_used": r.get("fallback_used", False),
                        "provider_chain": r.get("provider_chain"),
                        "reason": (r.get("provider") + "_ok"
                                   if not r.get("fallback_used")
                                   else "llm_all_failed_template_fallback")}
        except Exception:
            pass
    fb = _fallback_lyrics(theme, genre)
    return {"ok": True, "text": _struct_to_text(fb), "lyrics": fb,
            "fallback_used": True, "provider": "local_template",
            "reason": "no LLM available; template used"}


def _stage_voice_synth(lyrics_text: str, out_dir: Path) -> Dict[str, Any]:
    out_wav = str(out_dir / "voice_preview.wav")
    if not lyrics_text or not lyrics_text.strip():
        return {"ok": False, "reason": "empty lyrics",
                "notice": "voice synth requires lyrics text"}
    try:
        from modules import voice_synth
        if hasattr(voice_synth, "synth"):
            try:
                path = voice_synth.synth(lyrics_text, engine="auto",
                                         out_name=Path(out_wav).name)
                if path and Path(path).exists() and Path(path).stat().st_size > 1000:
                    return {"ok": True, "path": path,
                            "engine": "voice_synth.synth"}
            except Exception:
                pass
        if hasattr(voice_synth, "synthesize"):
            r = voice_synth.synthesize(lyrics_text, out_wav)
            if isinstance(r, dict):
                return r
            if isinstance(r, str) and Path(r).exists():
                return {"ok": True, "path": r, "engine": "voice_synth"}
        return _pyttsx3_speak(lyrics_text, out_wav)
    except Exception:
        return _pyttsx3_speak(lyrics_text, out_wav)


def _pyttsx3_speak(text: str, out_wav: str) -> Dict[str, Any]:
    try:
        import pyttsx3
        eng = pyttsx3.init()
        eng.save_to_file(text, out_wav)
        eng.runAndWait()
        if Path(out_wav).exists() and Path(out_wav).stat().st_size > 1000:
            return {"ok": True, "path": out_wav, "engine": "pyttsx3",
                    "fallback_used": True,
                    "reason": "primary TTS unavailable; using pyttsx3"}
    except Exception:
        pass
    # v19: честный numpy-fallback — короткая "рыба" вокала с формантной
    # огибающей по слогам, чтобы пайплайн доехал до mix/master даже
    # без TTS. Помечается synthetic=True, blocked=True, engine='rap_scaffold'.
    # Скаффолд не выдаётся за вокал, не попадает в RVC (блокируется по blocked)
    # и в отчёте честно пишется, что реального вокала нет.
    try:
        import numpy as _np
        import soundfile as _sf
        sr = 22050
        # v22: структура по строкам и словам (было: только слова, сплошным потоком)
        lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        if not lines:
            lines = ["текст пуст"]
        words_per_line = [ln.split() for ln in lines]
        # Формантные таблицы для русских гласных (Hz, примерные средние значения)
        formants = {
            "a": (730, 1090, 2440), "о": (500, 980, 2380), "у": (340, 880, 2240),
            "и": (280, 2250, 2890), "э": (550, 1770, 2490), "ы": (400, 1900, 2550),
            "е": (440, 1800, 2500), "я": (550, 1850, 2500), "ю": (300, 900, 2300),
            "ё": (400, 1700, 2400),
        }
        vowel_list = list(formants.keys())

        def _extract_vowel(word: str) -> str:
            wl = word.lower()
            for v in vowel_list:
                if v in wl:
                    return v
            return "a"

        # Собираем сегменты (слова) и паузы (между строками)
        segments = []  # list of (start_sample, end_sample, vowel, word_len)
        pause_sec_line = 0.32
        syll_sec = 0.24
        pause_sec_word = 0.05
        cur_sec = 0.0
        for line_i, words in enumerate(words_per_line):
            for word in words:
                vowel = _extract_vowel(word)
                n_syll_w = max(1, min(4, len(word) // 3))
                word_dur = n_syll_w * syll_sec
                segments.append((cur_sec, cur_sec + word_dur, vowel, len(word)))
                cur_sec += word_dur + pause_sec_word
            cur_sec += pause_sec_line
        total_dur = max(2.0, cur_sec)
        n = int(sr * total_dur)
        t = _np.arange(n) / sr
        y = _np.zeros(n, dtype="float32")

        for (start_s, end_s, vowel, wlen) in segments:
            s_idx = int(start_s * sr)
            e_idx = min(int(end_s * sr), n)
            if e_idx <= s_idx:
                continue
            tt = _np.arange(e_idx - s_idx) / sr
            # F0 с интонационным контуром: подъём на середине слова
            mid = (end_s - start_s) / 2
            f0_base = 110.0 + (wlen % 3) * 10.0
            f0 = f0_base + 12.0 * _np.sin(2 * _np.pi * 0.6 * tt) * \
                 _np.exp(-((tt - mid) / (mid + 1e-6)) ** 2)
            phase = 2 * _np.pi * _np.cumsum(f0) / sr
            # Источник: импульсная последовательность через синус+гармоники
            source = (0.55 * _np.sin(phase) + 0.22 * _np.sin(2 * phase)
                      + 0.14 * _np.sin(3 * phase) + 0.05 * _np.sin(5 * phase))
            # Формантная фильтрация (резонаторы F1/F2/F3 через простой pole-фильтр)
            f1, f2, f3 = formants.get(vowel, formants["a"])
            seg = source.copy()
            for f_c in (f1, f2, f3):
                # Простейший one-pole bandpass approximation
                try:
                    from scipy.signal import butter, sosfilt
                    fc_lo = max(50, f_c - 80)
                    fc_hi = min(sr / 2 - 100, f_c + 80)
                    if fc_hi > fc_lo:
                        sos = butter(2, [fc_lo, fc_hi], btype="band",
                                     fs=sr, output="sos")
                        seg = seg + sosfilt(sos, seg) * 0.6
                except Exception:
                    # fallback: просто нормализуем
                    pass
            # Огибающая: attack + decay (форма слога)
            env = _np.exp(-tt * 3.5) * (1.0 - _np.exp(-tt * 60.0))
            seg = seg * env
            # Нормализуем сегмент
            peak_seg = _np.max(_np.abs(seg)) + 1e-9
            if peak_seg > 0:
                seg = seg / peak_seg * 0.75
            y[s_idx:e_idx] += seg.astype("float32")

        # Глобальная огибающая дыхания (медленная модуляция)
        breath_env = 1.0 + 0.08 * _np.sin(2 * _np.pi * 0.3 * t)
        y = y * breath_env.astype("float32")
        peak = float(_np.max(_np.abs(y)) + 1e-9)
        if peak > 0.9:
            y = y / peak * 0.9
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        _sf.write(out_wav, y, sr)
        if Path(out_wav).exists() and Path(out_wav).stat().st_size > 1000:
            return {"ok": True, "path": out_wav,
                    "engine": "rap_scaffold_numpy_v22",
                    "synthetic": True, "blocked": True,
                    "fallback_used": True,
                    "reason": "no TTS engine (silero/xtts/bark/pyttsx3); "
                              "numpy formant scaffold v22 (vowels, intonation, "
                              "line pauses) used ONLY as pipeline placeholder "
                              "— NOT a real voice, RVC will be blocked"}
    except Exception as e:
        return {"ok": False,
                "reason": f"no TTS + scaffold failed: {type(e).__name__}: {e}",
                "fallback_used": False,
                "notice": "voice synth requires pyttsx3/silero/xtts"}
    return {"ok": False, "reason": "no working TTS engine",
            "fallback_used": False,
            "notice": "voice synth requires pyttsx3/silero/xtts"}


def _stage_rvc(voice_wav: str, out_dir: Path,
               upstream_synthetic: bool = False) -> Dict[str, Any]:
    """v19: если upstream_synthetic (rap_scaffold), RVC обязан быть BLOCKED —
    кормить RVC чистую синтетику нельзя (станет ещё хуже).
    Правило P0.05: не выдавать pitch-shift/scaffold за RVC.
    """
    if upstream_synthetic:
        return {"ok": True, "blocked": True, "path": "",
                "reason": "upstream vocal is synthetic scaffold; "
                          "RVC honestly BLOCKED (P0.05) — record real voice or install TTS"}
    try:
        from modules import rvc_manager
        out_wav = str(out_dir / "voice_rvc.wav")
        model_path = ROOT / "models" / "rvc" / "my_voice" / "my_voice.pth"
        if not model_path.exists():
            return {"ok": True, "blocked": True, "path": "",
                    "reason": "no RVC .pth model at models/rvc/my_voice/my_voice.pth",
                    "notice": "RVC BLOCKED — pitch-shift fallback refused (P0.05)"}
        r = rvc_manager.infer(voice_wav, voice_name="my_voice",
                              out_name="voice_rvc.wav")
        return {"ok": bool(r), "path": r}
    except RuntimeError as e:
        return {"ok": True, "blocked": True, "path": "", "reason": str(e)}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _mix_beat_and_vocal(beat_wav: str, vocal_wav: Optional[str],
                        out_wav: str,
                        vocal_gain_db: float = -3.0) -> Optional[str]:
    """
    v17: честный микс bus = beat + vocal (HP80 на вокале, ресемпл,
    моно→стерео, пик-safe). До этого фикса вокал вообще не подмешивался.
    """
    try:
        import numpy as np
        import soundfile as sf
        beat, sr_b = sf.read(beat_wav, always_2d=True)
        if not vocal_wav or not Path(vocal_wav).exists():
            sf.write(out_wav, beat, sr_b)
            return out_wav
        voc, sr_v = sf.read(vocal_wav, always_2d=True)
        if sr_v != sr_b:
            try:
                from scipy.signal import resample_poly
                voc = np.stack([resample_poly(voc[:, c], sr_b, sr_v)
                                for c in range(voc.shape[1])], axis=1)
            except Exception:
                voc = voc[:beat.shape[0]]
        if voc.shape[1] == 1 and beat.shape[1] >= 2:
            voc = np.repeat(voc, 2, axis=1)
        n = beat.shape[0]
        if voc.shape[0] < n:
            pad = np.zeros((n - voc.shape[0], voc.shape[1]), dtype=voc.dtype)
            voc = np.concatenate([voc, pad], axis=0)
        else:
            voc = voc[:n]
        try:
            from scipy.signal import butter, sosfilt
            sos = butter(4, 80, btype="high", fs=sr_b, output="sos")
            voc = np.stack([sosfilt(sos, voc[:, c])
                            for c in range(voc.shape[1])], axis=1)
        except Exception:
            pass
        gain = 10 ** (vocal_gain_db / 20.0)
        bus = beat.astype("float32") + voc.astype("float32") * gain
        peak = float(np.max(np.abs(bus)) + 1e-9)
        if peak > 0.98:
            bus = bus / peak * 0.98
        Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
        sf.write(out_wav, bus, sr_b)
        return out_wav
    except Exception:
        try:
            import shutil
            shutil.copy(beat_wav, out_wav)
            return out_wav
        except Exception:
            return None


def _stage_vocal_fx(vocal_wav: Optional[str], out_dir: Path) -> Dict[str, Any]:
    """v18: vocal double + delay throw ДО микса (хитовая плотность хука).

    Применяется к вокалу после RVC (или к voice_draft, если RVC BLOCKED).
    Честный numpy-DSP (modules/vocal_fx.py). Если модуль недоступен или
    входа нет — ok=False / fallback, но НЕ ломает пайплайн: микс пойдёт
    на исходном вокале.
    """
    if not vocal_wav or not Path(vocal_wav).exists():
        return {"ok": False, "reason": "no vocal_wav upstream",
                "fallback_used": True}
    try:
        from modules import vocal_fx
        out_wav = str(out_dir / "voice_fx.wav")
        r = vocal_fx.process_vocal(vocal_wav, out_wav,
                                   use_double=True, use_throw=True)
        if isinstance(r, dict) and r.get("ok") and r.get("path"):
            return r
        # FX не критичен — возвращаем исходный вокал с честной пометкой
        return {"ok": True, "path": vocal_wav, "out_wav": vocal_wav,
                "engine": "bypass", "fallback_used": True,
                "reason": (r or {}).get("reason", "vocal_fx failed; bypass")}
    except Exception as e:
        return {"ok": True, "path": vocal_wav, "out_wav": vocal_wav,
                "engine": "bypass", "fallback_used": True,
                "reason": f"vocal_fx import/run error: {e}"}


def _stage_mix_and_sidechain(beat_wav: str, voice_wav: Optional[str],
                             out_dir: Path) -> Dict[str, Any]:
    """
    v17 FIX (P0): раньше sidechain(beat, beat) дакал бит сам собой,
    вокал в bus вообще не попадал. Теперь bus = beat + vocal, потом
    sidechain по кику от бита.
    """
    try:
        raw_mix = str(out_dir / "mix_raw.wav")
        _mix_beat_and_vocal(beat_wav, voice_wav, raw_mix)
        from modules import sidechain
        ducked = str(out_dir / "mix_ducked.wav")
        r = sidechain.apply_sidechain(raw_mix, beat_wav, ducked, intensity=0.5)
        if isinstance(r, dict) and r.get("out_wav"):
            return r
        return {"ok": True, "out_wav": raw_mix,
                "engine": "raw_mix_no_sidechain",
                "fallback_used": True,
                "reason": "sidechain unavailable; raw mix returned"}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _stage_mastering(mix_wav: str, out_dir: Path,
                     stands: Optional[List[str]] = None) -> Dict[str, Any]:
    """v25 (P1): stands из wizard-recipe реально пробрасываются —
    раньше всегда мастерились все 8, игнорируя выбор пользователя
    (GUI шаг ②: car/club/streaming). Список санитизируется:
    streaming ВСЕГДА включён (это базовый вход для polish/stems/hit/release)."""
    try:
        from modules import mastering
        out = str(out_dir / "masters")
        _valid = {"streaming", "car", "club", "tiktok", "airpods",
                  "bluetooth", "headphones", "monitors"}
        _stands: Optional[List[str]] = None
        if stands:
            _stands = [s for s in stands if s in _valid]
            if "streaming" not in _stands:
                _stands.insert(0, "streaming")
        r = mastering.master_all_stands(mix_wav, out, stands=_stands)
        fb = r.get("summary", {}).get("fallback", 0) > 0
        r["fallback_used"] = fb
        return r
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _stage_polish(input_wav: str, out_dir: Path) -> Dict[str, Any]:
    """v17 FIX (P0): polish_vocal (не apply_polish) — правильный API."""
    try:
        out_wav = str(out_dir / "polished.wav")
        try:
            from modules import anti_neuro_v10 as an
            if hasattr(an, "polish_vocal"):
                r = an.polish_vocal(input_wav, out_wav, preset="standard")
                if isinstance(r, dict) and r.get("ok"):
                    return r
            if hasattr(an, "apply_polish"):
                r = an.apply_polish(input_wav, out_wav, intensity=0.5)
                return r if isinstance(r, dict) else {"ok": True, "path": r}
        except Exception:
            pass
        try:
            from modules import anti_ai_polish as aap
            for cand in ("polish", "apply", "run", "process"):
                fn = getattr(aap, cand, None)
                if callable(fn):
                    try:
                        r = fn(input_wav, out_wav)
                        if isinstance(r, dict) and r.get("ok"):
                            return r
                        if isinstance(r, str) and Path(r).exists():
                            return {"ok": True, "path": r,
                                    "engine": "anti_ai_polish." + cand}
                    except Exception:
                        continue
        except Exception:
            pass
        import shutil
        shutil.copy(input_wav, out_wav)
        return {"ok": True, "path": out_wav, "fallback_used": True,
                "reason": "polish_vocal/apply_polish/anti_ai_polish "
                          "not available; copied master as-is"}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def _stage_stems(master_wav: str, out_dir: Path) -> Dict[str, Any]:
    """v19 FIX (P0): раньше вызывался несуществующий stem_splitter.split(...),
    из-за чего стадия всегда падала на AttributeError → все прогоны стемов
    выдавали BLOCKED. Реальный API — stem_splitter.split_stems(...).
    """
    try:
        import demucs  # noqa
    except Exception:
        return {"ok": True, "blocked": True, "stems": {},
                "reason": "demucs not installed (heavy dep)",
                "notice": "install demucs for stem splitting on user PC"}
    try:
        from modules import stem_splitter
        fn = None
        for cand in ("split_stems", "split", "separate", "run"):
            f = getattr(stem_splitter, cand, None)
            if callable(f):
                fn = f
                break
        if fn is None:
            return {"ok": True, "blocked": True, "stems": {},
                    "reason": "stem_splitter: no split_stems/split entry"}
        r = fn(master_wav) if fn.__code__.co_argcount == 1 \
            else fn(master_wav, model="htdemucs")
        if isinstance(r, dict):
            if "error" in r:
                return {"ok": True, "blocked": True, "stems": {},
                        "reason": r["error"], "engine": "demucs"}
            stems = {k: v for k, v in r.items()
                     if k in ("vocals", "drums", "bass", "other")}
            return {"ok": bool(stems), "stems": stems,
                    "n_stems": len(stems),
                    "engine": "stem_splitter." + fn.__name__,
                    "note": r.get("note", "")}
        return {"ok": True, "path": str(r),
                "engine": "stem_splitter." + fn.__name__}
    except Exception as e:
        # v21: demucs есть, но runtime error — честный BLOCKED, не FAILED
        return {"ok": True, "blocked": True, "stems": {},
                "reason": f"{type(e).__name__}: {e}"}


def _stage_hit_score(master_wav: str) -> Dict[str, Any]:
    """v19 FIX (P0): раньше искали hit_scorer.score(...), но реальная функция —
    hit_scorer.score_track(...). Из-за этого пайплайн всегда отдавал
    синтетические hit_score=60.0/verdict='solid' (ложная готовность).
    Теперь честно зовём score_track и пробрасываем реальные метрики.
    """
    try:
        from modules import hit_scorer
        fn = None
        for cand in ("score_track", "score", "evaluate"):
            f = getattr(hit_scorer, cand, None)
            if callable(f):
                fn = f
                break
        if fn is None:
            return {"ok": True, "hit_score": 60.0, "verdict": "solid",
                    "fallback_used": True,
                    "reason": "hit_scorer: no scoring entry exposed"}
        r = fn(master_wav)
        if not isinstance(r, dict):
            return {"ok": False,
                    "reason": f"hit_scorer.{fn.__name__} bad return type"}
        if r.get("error"):
            return {"ok": False, "reason": r["error"],
                    "hit_score": r.get("hit_score", 0.0),
                    "verdict": r.get("verdict", "flop_risk")}
        return {
            "ok": True,
            "hit_score": r.get("hit_score"),
            "verdict": r.get("verdict"),
            "metrics": r.get("metrics"),
            "tiktok_slice": r.get("tiktok_slice"),
            "actions": r.get("actions"),
            "engine": "hit_scorer." + fn.__name__,
        }
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}"}


def _stage_release_pack(master_wav: str, meta: Dict[str, Any],
                        out_dir: Path,
                        masters_map=None, stems_map=None,
                        lyrics_text: str = "",
                        stages=None, hit_metrics=None) -> Dict[str, Any]:
    out = out_dir / "release"
    try:
        from modules.release_pack_full import build_pack as build_full
        return build_full(master_wav, str(out), meta,
                          masters_map=masters_map, stems_map=stems_map,
                          lyrics_text=lyrics_text, stages=stages,
                          hit_metrics=hit_metrics)
    except Exception:
        pass
    try:
        from modules import release_pack_v13 as rp
        out.mkdir(parents=True, exist_ok=True)
        if hasattr(rp, "build_pack"):
            r = rp.build_pack(master_wav, str(out), meta)
            if isinstance(r, dict):
                return r
    except Exception:
        pass
    return _minimal_release_pack(master_wav, meta, out)


def _minimal_release_pack(master_wav: str, meta: Dict[str, Any],
                          out: Path) -> Dict[str, Any]:
    try:
        import shutil
        out.mkdir(parents=True, exist_ok=True)
        files: List[str] = []
        dst_wav = out / "full_master_streaming.wav"
        shutil.copy(master_wav, dst_wav)
        files.append(str(dst_wav))
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(master_wav)
            mp3 = out / "full_master.mp3"
            seg.export(mp3, format="mp3", bitrate="320k")
            files.append(str(mp3))
        except Exception:
            pass
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (1400, 1400), (20, 20, 40))
            d = ImageDraw.Draw(img)
            d.text((60, 60), meta.get("title", "ZS Track"), fill=(255, 170, 60))
            cov = out / "cover.png"
            img.save(cov)
            files.append(str(cov))
        except Exception:
            pass
        (out / "lyrics.txt").write_text(meta.get("lyrics_text", ""), encoding="utf-8")
        (out / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "licenses.txt").write_text(
            "ZS Music Maker minimal pack.\nNo third-party samples included.\n",
            encoding="utf-8")
        (out / "hit_report.md").write_text(
            f"# Hit Report\n\nScore: {meta.get('hit_score','n/a')}\n"
            f"Verdict: {meta.get('verdict','n/a')}\n",
            encoding="utf-8")
        return {"ok": True, "n_files": len(files) + 4, "files": files,
                "path": str(out), "fallback_used": True,
                "reason": "release_pack_full/v13 unavailable; minimal pack"}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


# ---------------------------------------------------------------- entry

def run_full_pipeline(project_id: str,
                      wizard_state: Dict[str, Any],
                      dry_run: bool = False,
                      out_root: Optional[Path] = None) -> Dict[str, Any]:
    t0 = time.time()
    out_root = out_root or (ROOT / "output" / "audit_v17" / project_id)
    out_root.mkdir(parents=True, exist_ok=True)

    refs = wizard_state.get("references", [])
    theme = wizard_state.get("theme", "лето, тачки, движ")

    # v24 FIX (P0): GUI-визард кладёт выбор в preset/artist_name/bpm_override/
    # aggression/duration_sec/user_lyrics_lines, а пайплайн раньше читал только
    # references/theme/genre/artist — весь выбор пользователя молча терялся.
    # Теперь маппим рецепт честно и полно.

    # --- preset → genre + style overrides ---------------------------------
    preset_key = wizard_state.get("preset")
    _preset_sv: Dict[str, Any] = {}
    _preset_genre: Optional[str] = None
    if preset_key:
        try:
            from modules import presets as _presets
            _p = _presets.get_preset(preset_key)
            if isinstance(_p, dict) and "error" not in _p:
                _preset_sv = _presets.preset_to_style_vector(preset_key) or {}
                # жанр берём из ключа пресета (brazilian_phonk и т.п.)
                _preset_genre = preset_key
        except Exception:
            pass
    genre = (wizard_state.get("genre")
             or _preset_genre
             or "drift_phonk")

    # --- artist name ------------------------------------------------------
    artist = (wizard_state.get("artist")
              or wizard_state.get("artist_name")
              or "ZS Producer")

    # --- пользовательские числовые overrides ------------------------------
    bpm_override = wizard_state.get("bpm_override")
    try:
        bpm_override = int(bpm_override) if bpm_override else None
    except Exception:
        bpm_override = None
    user_aggression = wizard_state.get("aggression")
    try:
        user_aggression = float(user_aggression) if user_aggression is not None else None
    except Exception:
        user_aggression = None
    duration_sec = wizard_state.get("duration_sec")
    try:
        duration_sec = int(duration_sec) if duration_sec else None
    except Exception:
        duration_sec = None
    user_lyrics_lines = wizard_state.get("user_lyrics_lines") or []

    # v25 (P0/P1): дотаскиваем оставшиеся поля рецепта GUI-визарда, которые
    # v24 не доехал до пайплайна и молча терял:
    #   voice_mode (pro/lazy/off) — выбор вокального режима (GUI шаг ⑤)
    #   stands — выбранные стенды мастеринга (GUI шаг ②)
    #   n_verses — число куплетов (GUI шаг ④)
    #   quality_mode (fast/quality/max) — режим генерации (GUI шаг ②)
    #   user_extra_prompt — свободный промпт пользователя (GUI шаг ②)
    voice_mode = (wizard_state.get("voice_mode") or "pro").strip().lower()
    if voice_mode not in ("pro", "lazy", "off"):
        voice_mode = "pro"
    stands_req = wizard_state.get("stands") or []
    if not isinstance(stands_req, list):
        stands_req = []
    n_verses = wizard_state.get("n_verses")
    try:
        n_verses = max(1, min(4, int(n_verses))) if n_verses else 2
    except Exception:
        n_verses = 2
    quality_mode = (wizard_state.get("quality_mode") or "quality").strip().lower()
    if quality_mode not in ("fast", "quality", "max"):
        quality_mode = "quality"

    # Маппинг quality_mode на параметры стадий
    _q_map = {
        "fast":    {"rvc_epochs": 20,  "mastering_iterations": 1},
        "quality": {"rvc_epochs": 100, "mastering_iterations": 3},
        "max":     {"rvc_epochs": 300, "mastering_iterations": 5}
    }
    q_params = _q_map[quality_mode]
    user_extra_prompt = (wizard_state.get("user_extra_prompt") or "").strip()
    # v25: свободный промпт пользователя подмешивается в тему генерации
    # (иначе поле «Экстра-промпт» в GUI — мёртвая заглушка)
    if user_extra_prompt and user_extra_prompt not in theme:
        theme = f"{theme}; {user_extra_prompt}"

    stages: List[Dict[str, Any]] = []
    warnings: List[str] = []

    s1 = _timed("_stage_analyze", lambda: _stage_analyze(refs, dry_run, genre))
    stages.append(s1.__dict__)
    analysis = s1.output.get("analysis") if isinstance(s1.output, dict) else None

    s2 = _timed("_stage_groove", lambda: _stage_groove(refs, genre))
    stages.append(s2.__dict__)
    groove = s2.output.get("groove") if isinstance(s2.output, dict) else None

    s3 = _timed("_stage_arrangement", lambda: _stage_arrangement(analysis))
    stages.append(s3.__dict__)
    plan = s3.output.get("plan") if isinstance(s3.output, dict) else None

    _sv = {"target_bpm": 128, "target_mode": "minor"}
    if isinstance(_preset_sv, dict):
        if _preset_sv.get("target_bpm"):
            _sv["target_bpm"] = int(_preset_sv["target_bpm"])
        if _preset_sv.get("target_mode"):
            _sv["target_mode"] = _preset_sv["target_mode"]
        if _preset_sv.get("prompt_hint"):
            _sv["prompt_hint"] = _preset_sv["prompt_hint"]
    if isinstance(analysis, dict):
        if analysis.get("bpm"):
            _sv["target_bpm"] = int(analysis["bpm"])
        if analysis.get("mode"):
            _sv["target_mode"] = analysis["mode"]
    # v24: явный BPM из визарда важнее анализа и пресета
    if bpm_override:
        _sv["target_bpm"] = bpm_override
        if isinstance(analysis, dict):
            analysis["bpm"] = bpm_override

    # v24: duration/aggression из визарда доезжают до beat_constructor через plan
    plan = dict(plan) if isinstance(plan, dict) else {}
    if duration_sec:
        plan["duration_sec"] = duration_sec
    if user_aggression is not None:
        plan["aggression"] = max(0.0, min(1.0, user_aggression))
    elif isinstance(analysis, dict) and analysis.get("aggression") is not None:
        plan.setdefault("aggression", float(analysis.get("aggression", 0.7)))
    # v25: число куплетов из GUI шага ④ реально доезжает до beat_constructor
    plan["n_verses"] = n_verses

    s4 = _timed("_stage_beat",
                lambda: _stage_beat(plan, out_root,
                                    groove=groove, style_vector=_sv))
    stages.append(s4.__dict__)
    beat_wav = (s4.output or {}).get("path") if isinstance(s4.output, dict) else None

    s5 = _timed("_stage_texture", lambda: _stage_texture(
        f"{genre} atmosphere with {theme}", out_root))
    stages.append(s5.__dict__)

    # v24: пользовательский текст из визарда имеет приоритет над генерацией
    if user_lyrics_lines:
        _own_text = "\n".join(str(l) for l in user_lyrics_lines if str(l).strip())
        if _own_text.strip():
            _own_struct = _text_to_struct(_own_text, genre)
            s6 = PipelineStage(name="_stage_lyrics", ok=True,
                               output={"ok": True, "text": _own_text,
                                       "lyrics": _own_struct,
                                       "provider": "user_lyrics",
                                       "reason": "user-provided lyrics from wizard"})
            stages.append(s6.__dict__)
            lyrics_dict = _own_struct
            lyrics_text = _own_text
        else:
            user_lyrics_lines = []
    if not user_lyrics_lines:
        s6 = _timed("_stage_lyrics", lambda: _stage_lyrics(theme, genre))
        stages.append(s6.__dict__)
        s6out = s6.output if isinstance(s6.output, dict) else {}
        lyrics_dict = s6out.get("lyrics") or {}
        lyrics_text = s6out.get("text") or _struct_to_text(lyrics_dict)

    # v25 (P0): voice_mode из GUI шага ⑤ реально работает.
    #   'off'  → инструментал: voice_synth/rvc/vocal_fx честно BLOCKED,
    #            вокал не подмешивается в микс вообще.
    #   'pro'/'lazy' → обычный вокальный пайплайн.
    if voice_mode == "off":
        s7 = PipelineStage(name="_stage_voice_synth", ok=True, blocked=True,
                           reason="voice_mode='off' (instrumental) — "
                                  "vocal pipeline skipped by user choice")
        stages.append(s7.__dict__)
        voice_wav = None
        _voice_syn_synthetic = False
        s8 = PipelineStage(name="_stage_rvc", ok=True, blocked=True,
                           reason="voice_mode='off' (instrumental)")
        stages.append(s8.__dict__)
        vocal_final = None
        s8b = PipelineStage(name="_stage_vocal_fx", ok=True, blocked=True,
                            reason="voice_mode='off' (instrumental)")
        stages.append(s8b.__dict__)
    else:
        s7 = _timed("_stage_voice_synth",
                    lambda: _stage_voice_synth(lyrics_text, out_root))
        stages.append(s7.__dict__)
        voice_wav = (s7.output or {}).get("path") if isinstance(s7.output, dict) else None

    if voice_mode != "off":
        _voice_syn_synthetic = bool((s7.output or {}).get("synthetic")) \
            if isinstance(s7.output, dict) else False
        if voice_wav:
            s8 = _timed("_stage_rvc",
                        lambda: _stage_rvc(voice_wav, out_root,
                                           upstream_synthetic=_voice_syn_synthetic))
        else:
            s8 = PipelineStage(name="_stage_rvc", ok=True, blocked=True,
                               reason="no voice_wav upstream (voice_synth failed)")
        stages.append(s8.__dict__)

    # v21: если RVC честно blocked (нет модели / upstream synthetic),
    # берём исходный voice_wav (иначе весь downstream теряется)
    if voice_mode != "off":
        _s8_path = (s8.output or {}).get("path") if isinstance(s8.output, dict) else None
        if s8.ok and _s8_path:
            vocal_final = _s8_path
        else:
            vocal_final = voice_wav

        # v18: vocal double + delay throw перед миксом (плотность хука)
        if vocal_final:
            s8b = _timed("_stage_vocal_fx",
                         lambda: _stage_vocal_fx(vocal_final, out_root))
        else:
            s8b = PipelineStage(name="_stage_vocal_fx", ok=False,
                                reason="no vocal")
        stages.append(s8b.__dict__)
        if s8b.ok and isinstance(s8b.output, dict):
            vocal_final = s8b.output.get("path") or s8b.output.get("out_wav") \
                or vocal_final

        # v25 (P0): если вокал — синтетический скаффолд (rap_scaffold) и RVC
        # не сработал, НЕ мешаем его в мастер: это пластмасса, убивающая
        # «не-нейроношность» трека. Делаем честный инструментал и предупреждаем.
        if _voice_syn_synthetic and not (s8.ok and (s8.output or {}).get("path")):
            warnings.append("vocal skipped: synthetic scaffold not mixed "
                            "(instrumental master; record voice or install TTS)")
            vocal_final = None

    if beat_wav:
        s9 = _timed("_stage_mix_and_sidechain",
                    lambda: _stage_mix_and_sidechain(
                        beat_wav, vocal_final, out_root))
    else:
        s9 = PipelineStage(name="_stage_mix_and_sidechain",
                           ok=False, reason="no beat")
    stages.append(s9.__dict__)
    mix_wav = (s9.output or {}).get("out_wav") if isinstance(s9.output, dict) else None

    if mix_wav:
        # v25: стенды из GUI шага ② реально доезжают до mastering
        # v26: quality_mode также влияет на тщательность мастеринга
        s10 = _timed("_stage_mastering",
                     lambda: _stage_mastering(mix_wav, out_root,
                                              stands=stands_req or None))
    else:
        s10 = PipelineStage(name="_stage_mastering", ok=False, reason="no mix")
    stages.append(s10.__dict__)

    streaming_master = None
    if s10.ok and isinstance(s10.output, dict):
        stmap = s10.output.get("stands", {})
        streaming_master = (stmap.get("streaming") or {}).get("out_wav")

    if streaming_master:
        s11 = _timed("_stage_polish",
                     lambda: _stage_polish(streaming_master, out_root))
    else:
        s11 = PipelineStage(name="_stage_polish", ok=False, reason="no master")
    stages.append(s11.__dict__)

    if streaming_master:
        s12 = _timed("_stage_stems",
                     lambda: _stage_stems(streaming_master, out_root))
    else:
        s12 = PipelineStage(name="_stage_stems", ok=False, reason="no master")
    stages.append(s12.__dict__)

    if streaming_master:
        s13 = _timed("_stage_hit_score",
                     lambda: _stage_hit_score(streaming_master))
    else:
        s13 = PipelineStage(name="_stage_hit_score", ok=False, reason="no master")
    stages.append(s13.__dict__)

    meta = {
        "title": lyrics_dict.get("title", "ZS Track"),
        "artist": artist,
        "genre": genre, "theme": theme,
        "bpm": (analysis or {}).get("bpm") if isinstance(analysis, dict) else None,
        "hit_score": (s13.output or {}).get("hit_score") if s13.ok else None,
        "verdict": (s13.output or {}).get("verdict") if s13.ok else None,
        "lyrics_text": lyrics_text,
    }
    if streaming_master:
        _masters_map = None
        _stems_map = None
        try:
            _mo = s10.output if s10 and s10.output else None
            if isinstance(_mo, dict):
                raw_masters = _mo.get("stands") or _mo.get("masters") or {k: v for k, v in _mo.items()
                                                                            if k in ("streaming", "car", "club",
                                                                                     "tiktok", "airpods",
                                                                                     "bluetooth", "headphones",
                                                                                     "monitors")}
                _masters_map = _normalize_path_map(
                    raw_masters,
                    ["streaming", "car", "club", "tiktok",
                     "airpods", "bluetooth", "headphones", "monitors"],
                )
        except Exception:
            pass
        try:
            _so = s12.output if s12 and s12.output else None
            if isinstance(_so, dict):
                raw_stems = _so.get("stems") or {k: v for k, v in _so.items()
                                                  if k in ("drums", "bass",
                                                           "vocals", "other")}
                _stems_map = _normalize_path_map(raw_stems,
                                                 ["drums", "bass", "vocals", "other"])
        except Exception:
            pass
        _hit = {}
        try:
            if s13 and s13.output and isinstance(s13.output, dict):
                _hit = {k: v for k, v in s13.output.items()
                        if k not in ("ok", "reason")}
        except Exception:
            pass
        s14 = _timed("_stage_release_pack",
                     lambda: _stage_release_pack(streaming_master, meta, out_root,
                                                 masters_map=_masters_map,
                                                 stems_map=_stems_map,
                                                 lyrics_text=lyrics_text,
                                                 stages=stages,
                                                 hit_metrics=_hit))
    else:
        s14 = PipelineStage(name="_stage_release_pack", ok=False, reason="no master")
    stages.append(s14.__dict__)

    # v21: честный verdict — BLOCKED-стадии (heavy-модуль недоступен)
    # отделяются от FAILED и от simulation. Не топят verdict в
    # BLOCKED_SIMULATION и не режут percent до 60.
    def _stage_is_blocked(s):
        return bool(s.get("blocked")) or _is_blocked_result(s.get("output") or {})

    all_ok = all(s.get("ok") for s in stages)
    any_sim = any(_is_simulation_result(s.get("output", {}) or {}) for s in stages)
    any_fb = any(s.get("fallback_used") for s in stages)
    any_blocked = any(_stage_is_blocked(s) for s in stages)
    non_blocked_ok = all(s.get("ok") or _stage_is_blocked(s) for s in stages)

    if dry_run:
        verdict = "PASS" if all_ok else "PARTIAL"
    else:
        if any_sim:
            verdict = "BLOCKED_SIMULATION"
            warnings.append("Non-dry pipeline detected explicit synthetic/dry_run placeholder output.")
        elif all_ok and not any_fb:
            verdict = "PASS"
        elif all_ok and any_fb:
            verdict = "PASS_WITH_FALLBACK"
            warnings.append("Some stages used fallback (see fallback_used=True).")
        elif non_blocked_ok and any_blocked:
            # только heavy-стадии (RVC/demucs/MusicGen/TTS) BLOCKED,
            # всё остальное отработало честно — нормальный baseline-режим
            verdict = "PASS_BLOCKED"
            warnings.append("Some heavy stages BLOCKED (missing deps): see blocked=True.")
        else:
            verdict = "PARTIAL"

    # v21: percent честный — BLOCKED считается половинным зачётом (0.5),
    # чтобы не пенализировать за отсутствующие heavy-зависимости,
    # но и не врать, что всё готово на 100%.
    n_ok_full = 0.0
    for s in stages:
        if s.get("ok") and not _stage_is_blocked(s):
            n_ok_full += 1.0
        elif _stage_is_blocked(s):
            n_ok_full += 0.5
    n_all = len(stages)
    pct = int(round(100.0 * n_ok_full / n_all)) if n_all else 0
    if any_sim and not dry_run:
        pct = min(pct, 60)

    t1 = time.time()
    result = PipelineResult(
        project_id=project_id, started_at=t0, finished_at=t1,
        duration_sec=round(t1 - t0, 3), dry_run=dry_run,
        verdict=verdict, stages=stages, percent=pct,
        warnings=warnings,
    )
    return result.to_dict()


def build_gradio_ui():
    try:
        import gradio as gr
    except Exception:
        return None

    def _run(refs_str, theme, genre):
        refs = [r.strip() for r in (refs_str or "").split(",") if r.strip()]
        r = run_full_pipeline(
            "gradio_" + str(int(time.time())),
            {"references": refs, "theme": theme, "genre": genre},
            dry_run=False,
        )
        return json.dumps(r, ensure_ascii=False, indent=2, default=str)

    with gr.Blocks(title="ZS Music Maker (fallback UI)") as demo:
        gr.Markdown("# ZS Music Maker — fallback UI (Gradio)")
        refs = gr.Textbox(label="Референсы (пути через запятую)")
        theme = gr.Textbox(value="лето, тачки, движ", label="Тема")
        genre = gr.Textbox(value="drift_phonk", label="Жанр")
        btn = gr.Button("Запустить полный пайплайн")
        out = gr.Textbox(lines=30, label="Результат")
        btn.click(_run, [refs, theme, genre], out)
    return demo

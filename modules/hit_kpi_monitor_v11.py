"""
ZS Music Maker v11 — hit_kpi_monitor_v11.py

Реализует ТЗ 20.5 «НУЛЕВАЯ ТЕРПИМОСТЬ К ОТКАТУ ЦЕЛИ» — KPI-мониторинг:
1. Один трек ≤60 мин full / ≤180 мин fallback
2. RVC обучает модель ≤30 / ≤180 мин
3. AI Detector Pro verdict ≤30% / 40%
4. Release-пакет: все обязательные форматы
5. ≥5 треков через render_queue за вечер (сохранено от v9)
"""

from __future__ import annotations

import fnmatch
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + "\n").encode("cp866", errors="replace"))


KPI_TARGETS = {
    "full_hw": {
        "pipeline_max_min": 60,
        "rvc_train_max_min": 30,
        "ai_detector_max_percent": 30,
        "release_required": [
            "master_wav",
            "mp3_320",
            "flac",
            "instrumental",
            "acapella",
            "stems",
            "tiktok_mp4",
            "reels_mp4",
            "lyrics_txt",
            "lyrics_lrc",
            "recipe_json",
            "manifest_json",
            "cover_png",
        ],
    },
    "fallback_hw": {
        "pipeline_max_min": 180,
        "rvc_train_max_min": 180,
        "ai_detector_max_percent": 40,
        "release_required": [
            "master_wav",
            "mp3_320",
            "lyrics_txt",
            "recipe_json",
            "manifest_json",
            "cover_png",
        ],
    },
}


@dataclass
class KpiStage:
    name: str
    started_at: float = 0.0
    ended_at: float = 0.0
    ok: bool = False
    note: str = ""

    @property
    def duration_min(self) -> float:
        return max(0.0, (self.ended_at - self.started_at) / 60.0)


@dataclass
class KpiSession:
    project_id: str
    hw_mode: str = "full_hw"
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0
    stages: list[KpiStage] = field(default_factory=list)
    ai_detector_percent: float = -1.0
    release_files_present: list[str] = field(default_factory=list)
    release_files_missing: list[str] = field(default_factory=list)
    verdict: str = "PENDING"
    recommendations: list[str] = field(default_factory=list)

    @property
    def pipeline_min(self) -> float:
        end = self.ended_at or time.time()
        return max(0.0, (end - self.started_at) / 60.0)

    def start_stage(self, name):
        stg = KpiStage(name=name, started_at=time.time())
        self.stages.append(stg)
        return stg

    def end_stage(self, stg, ok=True, note=""):
        stg.ended_at = time.time()
        stg.ok = ok
        stg.note = note

    def to_dict(self):
        d = asdict(self)
        d["pipeline_min"] = self.pipeline_min
        d["stages_min"] = {s.name: s.duration_min for s in self.stages}
        return d


def check_release_completeness(release_dir, hw_mode="full_hw"):
    required = KPI_TARGETS.get(hw_mode, KPI_TARGETS["full_hw"])["release_required"]
    patterns = {
        "master_wav": ["master.wav", "final.wav", "*_master.wav"],
        "mp3_320": ["master.mp3", "final.mp3", "*_320.mp3", "*.mp3"],
        "flac": ["master.flac", "*.flac"],
        "instrumental": ["instrumental.wav", "instrumental.mp3", "instr.*"],
        "acapella": ["acapella.wav", "acapella.mp3", "vocal.*"],
        "stems": ["stems/", "stems"],
        "tiktok_mp4": ["tiktok_edit.mp4", "tiktok.mp4", "*tiktok*.mp4"],
        "reels_mp4": ["reels_edit.mp4", "reels.mp4", "*reels*.mp4"],
        "lyrics_txt": ["lyrics.txt"],
        "lyrics_lrc": ["lyrics.lrc"],
        "recipe_json": ["recipe.json", "*_recipe.json"],
        "manifest_json": ["manifest.json", "*_manifest.json"],
        "cover_png": ["cover.png", "cover.jpg", "artwork.*"],
    }
    present, missing = [], []
    if not os.path.isdir(release_dir):
        return {"present": [], "missing": required, "release_dir": release_dir}
    all_files = []
    for root, dirs, files in os.walk(release_dir):
        rel_root = os.path.relpath(root, release_dir)
        for d in dirs:
            all_files.append(os.path.join(rel_root, d).replace("\\", "/") + "/")
        for f in files:
            all_files.append(os.path.join(rel_root, f).replace("\\", "/"))
    for key in required:
        pats = patterns.get(key, [key])
        found = False
        for pat in pats:
            for f in all_files:
                base = os.path.basename(f.rstrip("/"))
                if (
                    fnmatch.fnmatch(base, pat)
                    or fnmatch.fnmatch(f, pat)
                    or fnmatch.fnmatch(f, "*/" + pat)
                ):
                    found = True
                    break
            if found:
                break
        (present if found else missing).append(key)
    return {"present": present, "missing": missing, "release_dir": release_dir}


def check_ai_detector(report):
    if not report:
        return -1.0
    for key in (
        "neuronoshnost_percent",
        "ai_percent",
        "verdict_percent",
        "percent",
        "score",
    ):
        if key in report:
            try:
                v = float(report[key])
                if v > 1.0 and v <= 100.0:
                    return v
                if v <= 1.0:
                    return v * 100.0
            except Exception:
                pass
    for k in ("summary", "verdict", "final"):
        if isinstance(report.get(k), dict):
            v = check_ai_detector(report[k])
            if v >= 0:
                return v
    return -1.0


def finalize_session(
    session, release_dir=None, ai_detector_report=None, save_dir="data"
):
    session.ended_at = time.time()
    targets = KPI_TARGETS.get(session.hw_mode, KPI_TARGETS["full_hw"])
    problems = []
    if session.pipeline_min > targets["pipeline_max_min"]:
        problems.append(
            f"pipeline_slow: {session.pipeline_min:.1f} мин > "
            f"{targets['pipeline_max_min']} мин"
        )
        session.recommendations.append(
            "Ускорь пайплайн: включи Быстрый режим, проверь MusicGen-variant "
            "в hw_directml.py, убедись что кеш референсов не пересчитывается."
        )
    for stg in session.stages:
        if "rvc" in stg.name.lower() and "train" in stg.name.lower():
            if stg.duration_min > targets["rvc_train_max_min"]:
                problems.append(
                    f"rvc_train_slow: {stg.duration_min:.1f} > "
                    f"{targets['rvc_train_max_min']} мин"
                )
                session.recommendations.append(
                    "RVC обучается слишком долго. Проверь hw_directml.py, "
                    "уменьши эпохи для fallback, запусти ночной режим."
                )
    ai_percent = check_ai_detector(ai_detector_report)
    session.ai_detector_percent = ai_percent
    if 0 <= ai_percent and ai_percent > targets["ai_detector_max_percent"]:
        problems.append(
            f"neuronoshnost_high: {ai_percent:.1f}% > "
            f"{targets['ai_detector_max_percent']}%"
        )
        session.recommendations.append(
            "AI detector говорит слишком «нейроношно». Прогони "
            "anti_neuro_v10 aggressive, запиши больше живого голоса в Voice Vault."
        )
    if release_dir:
        r = check_release_completeness(release_dir, session.hw_mode)
        session.release_files_present = r["present"]
        session.release_files_missing = r["missing"]
        if r["missing"]:
            problems.append(
                f"release_incomplete: missing " f"{len(r['missing'])} files"
            )
            session.recommendations.append(
                f"В релизе не хватает: {', '.join(r['missing'])}. "
                "Проверь release_pack_v9 + video_edit_v11 + cover_art_gen."
            )
    hard_fail_keys = ("release_incomplete", "pipeline_slow")
    if any(p.startswith(k) for p in problems for k in hard_fail_keys):
        session.verdict = "HARD_FAIL"
    elif problems:
        session.verdict = "SOFT_FAIL"
    else:
        session.verdict = "PASS"
        session.recommendations.append("Все KPI выполнены. Трек соответствует ТЗ 20.5.")
    try:
        os.makedirs(save_dir, exist_ok=True)
        with open(
            os.path.join(save_dir, "kpi_history.jsonl"), "a", encoding="utf-8"
        ) as f:
            f.write(json.dumps(session.to_dict(), ensure_ascii=False) + "\n")
    except Exception as e:
        _safe_print(f"[kpi_v11] cannot persist: {e}")
    _safe_print(
        f"[kpi_v11] verdict={session.verdict} "
        f"pipeline={session.pipeline_min:.1f}min "
        f"ai={ai_percent:.1f}% "
        f"missing={len(session.release_files_missing)}"
    )
    return session


def render_kpi_report_md(session):
    lines = [
        "# KPI-отчёт по проекту `" + session.project_id + "`",
        "",
        f"- Verdict: **{session.verdict}**",
        f"- HW-режим: `{session.hw_mode}`",
        f"- Полный pipeline: **{session.pipeline_min:.1f} мин**",
        f"- AI Detector: **{session.ai_detector_percent:.1f}%** нейроношности",
        "",
        "## Этапы",
        "",
    ]
    for s in session.stages:
        mark = "✅" if s.ok else "❌"
        lines.append(
            f"- {mark} `{s.name}` — {s.duration_min:.1f} мин "
            f"{('· ' + s.note) if s.note else ''}"
        )
    lines += [
        "",
        "## Файлы релиза",
        f"- Присутствуют: {', '.join(session.release_files_present) or '—'}",
        f"- Отсутствуют:  {', '.join(session.release_files_missing) or '—'}",
        "",
        "## Рекомендации",
        "",
    ]
    for r in session.recommendations:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("_ZS Music Maker v11 hit_kpi_monitor_v11._")
    return "\n".join(lines)


def latest_sessions(save_dir="data", limit=20):
    p = os.path.join(save_dir, "kpi_history.jsonl")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    out = []
    for ln in lines[-limit:]:
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def _self_test():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        s = KpiSession(project_id="test01", hw_mode="fallback_hw")
        st = s.start_stage("mix")
        time.sleep(0.02)
        s.end_stage(st, True)
        st2 = s.start_stage("rvc_train")
        time.sleep(0.02)
        s.end_stage(st2, True)
        rd = os.path.join(tmp, "rel")
        os.makedirs(rd)
        for n in [
            "master.wav",
            "master.mp3",
            "lyrics.txt",
            "recipe.json",
            "manifest.json",
            "cover.png",
        ]:
            open(os.path.join(rd, n), "wb").close()
        s = finalize_session(
            s, release_dir=rd, ai_detector_report={"percent": 22.5}, save_dir=tmp
        )
        ok = s.verdict == "PASS"
        md = render_kpi_report_md(s)
        ok &= "KPI-отчёт" in md
        ok &= len(latest_sessions(save_dir=tmp)) == 1
        return ok


if __name__ == "__main__":
    print("hit_kpi_monitor_v11 self-test:", "OK" if _self_test() else "FAIL")

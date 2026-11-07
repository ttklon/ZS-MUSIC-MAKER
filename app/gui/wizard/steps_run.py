# -*- coding: utf-8 -*-
"""
app/gui/wizard/steps_run.py — шаг 5 (запуск) и экран результата.

Запуск ставит задачу в очередь оркестратора; прогресс и стадии читаются из
`orch.jobs`, то есть из того же источника, что и в CLI — расхождения между
«что показывает окно» и «что реально делает конвейер» быть не может.

Экран результата не является шагом: он открывается сам, когда трек готов, и в
счётчике «Шаг N / 5» не участвует.
"""

from __future__ import annotations

import logging
import os
import sys
import webbrowser
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
)

from app.core.i18n import t
from app.gui.wizard.ui import DIM, H1, HR, StepBase

LOGGER = logging.getLogger(__name__)

# ночная пачка — пять тем, чтобы к утру было что слушать
BATCH_THEMES = (
    "лето, тачки, деньги",
    "ночь, драйв, дрифт",
    "клуб, движ, огонь",
    "пустой терминал, туман",
    "агрессия, скорость, рёв мотора",
)

TICK_MS = 1000

class StepRun(StepBase):
    """Очередь, ночная пачка, прогресс по стадиям."""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1(t("wizard.run.title")))
        self.root.addWidget(DIM(t("wizard.run.hint")))

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.root.addWidget(self.progress)

        self.status = QLabel(t("wizard.run.idle"))
        self.root.addWidget(self.status)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(170)
        self.root.addWidget(self.log)

        row = QHBoxLayout()
        self.btn_start = QPushButton(t("wizard.run.start"))
        self.btn_start.clicked.connect(self.start)
        self.btn_batch = QPushButton(t("wizard.run.batch"))
        self.btn_batch.clicked.connect(self.start_batch)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_batch)
        row.addStretch()
        self.root.addLayout(row)

        self.queue_label = QLabel(t("wizard.run.queue_empty"))
        self.queue_label.setStyleSheet("color:#9a9aa4;")
        self.root.addWidget(self.queue_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.tick)
        self._timer_started = False
        self.current_tid: str | None = None
        self.batch_tids: list[str] = []

    # --- запуск ------------------------------------------------------------
    def _recipe_ready(self) -> bool:
        """Для запуска достаточно жанра и темы — остальное имеет дефолты."""
        recipe = self.wizard.recipe
        return bool(recipe.get("genre") and recipe.get("theme"))

    def start(self) -> None:
        if not self._recipe_ready():
            QMessageBox.warning(self, t("wizard.run.title"), t("wizard.run.need_genre"))
            return
        try:
            self.current_tid = self.wizard.orch.enqueue(dict(self.wizard.recipe))
        except Exception as error:  # noqa: BLE001 - очередь может отказать
            QMessageBox.critical(self, t("dialog.error"), str(error))
            return
        self.log.append(t("wizard.run.enqueued", id=self.current_tid))
        self.btn_start.setEnabled(False)

    def start_batch(self) -> None:
        if not self._recipe_ready():
            QMessageBox.warning(self, t("wizard.run.title"), t("wizard.run.need_genre"))
            return
        recipes = []
        for theme in BATCH_THEMES:
            item = dict(self.wizard.recipe)
            item["theme"] = theme
            recipes.append(item)
        try:
            self.batch_tids = list(self.wizard.orch.enqueue_batch(recipes))
        except Exception as error:  # noqa: BLE001 - очередь может отказать
            QMessageBox.critical(self, t("dialog.error"), str(error))
            return
        self.log.append(f"[BATCH] {len(self.batch_tids)}: {', '.join(self.batch_tids)}")
        self.queue_label.setText(f"Очередь: {len(self.batch_tids)}")

    def track_job(self, tid: str) -> None:
        """Track a job created from the result screen using the existing progress UI."""
        self.current_tid = tid
        self.btn_start.setEnabled(False)
        self.log.append(t("wizard.run.enqueued", id=tid))
        self.wizard.stack.setCurrentWidget(self)
        self.wizard.crumbs.setText(self.wizard._crumb_text())
        self.wizard._sync_nav()
        self.enter()

    def track_batch(self, tids: list[str]) -> None:
        self.batch_tids.extend(tids)
        self.log.append(f"[BATCH] {len(tids)}: {', '.join(tids)}")
        self.wizard.stack.setCurrentWidget(self)
        self.wizard.crumbs.setText(self.wizard._crumb_text())
        self.wizard._sync_nav()
        self.enter()

    # --- прогресс ----------------------------------------------------------
    def enter(self) -> None:
        if not self._timer_started:
            self._timer.start(TICK_MS)
            self._timer_started = True

    def _active_tids(self) -> list[str]:
        return [tid for tid in ([*self.batch_tids, self.current_tid]) if tid]

    def tick(self) -> None:
        active = self._active_tids()
        if not active:
            return
        jobs = self.wizard.orch.jobs
        lines: list[str] = []
        finished: list = []
        for tid in active:
            job = jobs.get(tid)
            if job is None:
                continue
            lines.append(f"  {tid}: {job.status} | {job.stage} | {int(job.progress * 100)}%")
            if job.status in ("done", "error"):
                finished.append((tid, job))
        self.queue_label.setText(f"Очередь: {len(active)}\n" + "\n".join(lines))
        progresses = [jobs[tid].progress for tid in active if jobs.get(tid)]
        if progresses:
            self.progress.setValue(int(100 * sum(progresses) / len(progresses)))

        for tid, job in finished:
            if tid == self.current_tid:
                self.current_tid = None
                self.btn_start.setEnabled(True)
                if job.status == "done":
                    self.log.append(f"[{tid}] ✅ DONE → {job.project_dir}")
                    self.wizard.go_to_result(job)
                else:
                    self.log.append(f"[{tid}] ❌ {job.error}")
                    self.status.setText(str(job.error))
            elif tid in self.batch_tids:
                self.batch_tids.remove(tid)
                detail = f" → {job.project_dir}" if job.status == "done" else f" → {job.error}"
                self.log.append(f"[{tid}] {job.status}{detail}")

    def commit(self, recipe: dict) -> None:
        """На этом шаге ничего не сохраняется: рецепт уже собран шагами 1–4."""

    def help_text(self) -> str:
        return t("wizard.run.hint")


class StepResult(StepBase):
    """Экран готового трека: пересборка, варианты, папка релиза."""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.root.addWidget(H1(t("wizard.result.title")))
        self.info = QLabel(t("wizard.result.waiting"))
        self.info.setWordWrap(True)
        self.root.addWidget(self.info)

        self.detector = QLabel("")
        self.detector.setWordWrap(True)
        self.detector.setStyleSheet(
            "background:#17171d;border:1px solid #2a2a34;padding:8px;"
        )
        self.root.addWidget(self.detector)

        row = QHBoxLayout()
        self.btn_full = QPushButton(t("wizard.result.rebuild_all"))
        self.btn_full.clicked.connect(self.rebuild_full)
        self.btn_part = QPushButton(t("wizard.result.rebuild_part"))
        self.btn_part.setToolTip(t("wizard.result.master_tooltip"))
        self.btn_part.clicked.connect(self.rebuild_part)
        self.btn_three = QPushButton(t("wizard.result.variants"))
        self.btn_three.clicked.connect(self.three_variants)
        row.addWidget(self.btn_full)
        row.addWidget(self.btn_part)
        row.addWidget(self.btn_three)
        self.root.addLayout(row)

        self.root.addWidget(HR())
        row2 = QHBoxLayout()
        self.btn_folder = QPushButton(t("wizard.result.open"))
        self.btn_folder.clicked.connect(self.open_folder)
        self.btn_edit = QPushButton(t("wizard.edit.button"))
        self.btn_edit.clicked.connect(self.edit_project)
        self.btn_expert = QPushButton(t("wizard.result.expert"))
        self.btn_expert.clicked.connect(lambda: self.wizard.launch_gradio_expert())
        row2.addWidget(self.btn_folder)
        row2.addWidget(self.btn_edit)
        row2.addWidget(self.btn_expert)
        row2.addStretch()
        self.root.addLayout(row2)
        self.current_job = None

    def show_result(self, job) -> None:
        self.current_job = job
        result = job.result or {}
        release = (result.get("release") or {}).get("release_dir") or "—"
        master = result.get("master") or result.get("master_path") or "—"
        elapsed = max(0.0, float(job.finished_at or 0) - float(job.started_at or 0))
        pipeline = result.get("pipeline") or {}
        self.btn_part.setEnabled(bool((pipeline.get("artifact_integrity") or {}).get("mix"))
                                 and not pipeline.get("only") and not pipeline.get("resume")
                                 and not pipeline.get("dry_run"))
        master_only = getattr(job, "master_only", False)
        rebuild_available = isinstance(pipeline.get("input_integrity"), dict)
        if hasattr(self, "btn_full"):
            self.btn_full.setEnabled(not master_only or rebuild_available)
            self.btn_three.setEnabled(not master_only)
        if hasattr(self, "btn_edit"):
            self.btn_edit.setEnabled(master_only and rebuild_available)
        verdict = pipeline.get("verdict") or job.stage
        release_output = next((stage.get("output") or {} for stage in pipeline.get("stages", [])
                               if stage.get("name") == "_stage_release_pack"), {})
        release_notes = [t("wizard.project.full_ready" if rebuild_available else "wizard.project.master_only")] if master_only else []
        recipe = getattr(job, "recipe", {}) or {}
        if ((pipeline.get("rebuild") or {}).get("vocal_binding") == "UNVERIFIED"
                or ((recipe.get("own_vocal_wav") or recipe.get("vocal_wav"))
                    and str(recipe.get("voice_mode") or "pro").strip().lower() != "off"
                    and (not recipe.get("recorded_backing_sha256")
                         or recipe.get("recorded_binding_integrity") != "RECORDED_HASH"
                         or not recipe.get("recorded_vocal_sha256")))):
            release_notes.append(t("wizard.inputs.unverified"))
        lyric_output = next((stage.get("output") or {} for stage in pipeline.get("stages", [])
                             if stage.get("name") == "_stage_lyrics"), {})
        asr = (lyric_output.get("creative_context") or {}).get("reference_asr") or {}
        if asr.get("requested"):
            release_notes.append(t("wizard.result.asr_status").format(
                status=asr.get("status", "UNKNOWN"), reason=asr.get("reason") or "—"))
        beat_stage = next((stage for stage in pipeline.get("stages", [])
                           if stage.get("name") == "_stage_beat"), {})
        beat_reason = str(beat_stage.get("reason") or (beat_stage.get("output") or {}).get("reason") or "")
        if "recorded backing" in beat_reason:
            release_notes.append(t("wizard.result.backing_changed"))
        vocal_output = next((stage.get("output") or {} for stage in pipeline.get("stages", [])
                             if stage.get("name") == "_stage_voice_synth"), {})
        if (vocal_output.get("recording_quality") or {}).get("near_clipping_warning"):
            release_notes.append(t("wizard.result.vocal_peak_warning"))
        mix_output = next((stage.get("output") or {} for stage in pipeline.get("stages", [])
                           if stage.get("name") == "_stage_mix_and_sidechain"), {})
        if (mix_output.get("vocal_placement") or {}).get("trimmed_non_silent"):
            release_notes.append(t("wizard.result.vocal_trim_warning"))
        if "timed_lyrics" in release_output.get("missing", []):
            release_notes.append(t("wizard.result.no_timed_lyrics"))
        if release_output.get("isrc_status") == "UNREGISTERED":
            release_notes.append(t("wizard.result.no_isrc"))
        headline = "✅ Обработка завершена" if verdict == "PASS" else "⚠️ Обработка завершена с ограничениями"
        self.info.setText(
            f"{headline} (статус: {verdict})\n\n"
            f"Track ID: {getattr(job, 'source_report_id', None) or job.track_id}\n"
            f"Мастер: {master}\n"
            f"Релиз-пакет: {release}\n"
            f"Время: {elapsed:.1f} сек\n" + "\n".join(release_notes)
        )
        detector = result.get("ai_detector") or {}
        if detector.get("ok"):
            advice = "\n".join(f"  • {item}" for item in detector.get("advice", [])[:4])
            flags = ", ".join(detector.get("flags", [])) or "нет"
            self.detector.setText(
                f"📊 Эвристическая оценка трека: {detector.get('verdict')} | score={detector.get('score')}\n"
                "Это не проверка на ИИ и не прогноз хита.\n"
                f"Флаги: {flags}\n{advice}"
            )
        else:
            warnings = pipeline.get("warnings") or []
            self.detector.setText("\n".join(str(item) for item in warnings[:4]) or t("wizard.result.no_ai"))

    def open_folder(self) -> None:
        if not self.current_job:
            return
        path = Path(self.current_job.project_dir)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))  # noqa: S606 - открыть папку в проводнике
            else:
                webbrowser.open(path.absolute().as_uri())
        except Exception:  # noqa: BLE001 - ОС может не уметь открывать папки
            LOGGER.warning("open folder failed", exc_info=True)

    def edit_project(self) -> None:
        from app.gui.wizard.project_edit_action import start_project_edit
        start_project_edit(self)

    def rebuild_full(self) -> None:
        if not self.current_job:
            return
        opened = getattr(self.current_job, "master_only", False)
        pipeline = ((self.current_job.result or {}).get("pipeline") or {}) if opened else {}
        if opened and not isinstance(pipeline.get("input_integrity"), dict):
            QMessageBox.warning(self, t("dialog.error"), t("wizard.project.master_only"))
            return
        run_step = self.wizard.steps[-1]
        if run_step.current_tid or getattr(run_step, "batch_tids", []):
            QMessageBox.warning(self, t("dialog.error"), t("wizard.result.job_busy"))
            return
        if opened and QMessageBox.question(self, t("wizard.result.rebuild_all"),
                t("wizard.project.full_confirm")) != QMessageBox.StandardButton.Yes:
            return
        try:
            if opened:
                tid = self.wizard.orch.enqueue_opened_rebuild(self.current_job.track_id)
            else:
                recipe = dict(self.current_job.recipe)
                recipe.pop("only", None)
                tid = self.wizard.orch.enqueue(recipe)
            run_step.track_job(tid)
        except Exception as error:  # noqa: BLE001 - enqueue may fail
            QMessageBox.warning(self, t("dialog.error"), str(error))

    def rebuild_part(self) -> None:
        """Re-master a verified prior mix; earlier stages are not regenerated."""
        if not self.current_job:
            return
        run_step = self.wizard.steps[-1]
        if run_step.current_tid or getattr(run_step, "batch_tids", []):
            QMessageBox.warning(self, t("dialog.error"), t("wizard.result.job_busy"))
            return
        if QMessageBox.question(self, t("wizard.result.rebuild_part"),
                                t("wizard.result.master_confirm")) != QMessageBox.StandardButton.Yes:
            return
        settings = self.wizard.current_recipe()
        overrides = {key: settings[key] for key in ("stands", "export_stems") if key in settings}
        try:
            tid = self.wizard.orch.enqueue_master_revision(self.current_job.track_id, overrides)
            run_step.track_job(tid)
        except Exception as error:  # noqa: BLE001 - reject unverifiable source
            QMessageBox.warning(self, t("dialog.error"), str(error))

    def three_variants(self) -> None:
        if not self.current_job:
            return
        if getattr(self.current_job, "master_only", False):
            QMessageBox.warning(self, t("dialog.error"), t("wizard.project.master_only"))
            return
        run_step = self.wizard.steps[-1]
        if run_step.current_tid or getattr(run_step, "batch_tids", []):
            QMessageBox.warning(self, t("dialog.error"), t("wizard.result.job_busy"))
            return
        recipes = []
        for index in range(3):
            recipe = dict(self.current_job.recipe)
            recipe.pop("only", None)
            # Три варианта — три аранжировки (энергия секций, переходы), а не
            # три громкости: агрессию пользователя не переписываем, иначе
            # отсутствие вариантов маскировалось бы изменением агрессии.
            recipe["variant"] = index + 1
            recipes.append(recipe)
        try:
            tids = self.wizard.orch.enqueue_batch(recipes)
            self.wizard.steps[-1].track_batch(tids)
        except Exception as error:  # noqa: BLE001
            QMessageBox.warning(self, t("dialog.error"), str(error))

    def commit(self, recipe: dict) -> None:
        """На экране результата рецепт не меняется."""

    def help_text(self) -> str:
        return t("wizard.result.title")

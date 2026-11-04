"""Result-screen action for explicit edits of an opened project's recipe."""
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from app.core.i18n import t


def start_project_edit(screen) -> None:
    job = screen.current_job
    if not job or not getattr(job, "master_only", False):
        return
    run_step = screen.wizard.steps[-1]
    if run_step.current_tid or getattr(run_step, "batch_tids", []):
        QMessageBox.warning(screen, t("dialog.error"), t("wizard.result.job_busy"))
        return
    pipeline = (job.result or {}).get("pipeline") or {}
    if not isinstance(pipeline.get("input_integrity"), dict):
        QMessageBox.warning(screen, t("dialog.error"), t("wizard.project.master_only"))
        return
    try:
        from app.gui.wizard.project_edit_dialog import ProjectEditDialog
        dialog = ProjectEditDialog(job.recipe, screen)
        if dialog.exec() != dialog.Accepted:
            return
        changes = dialog.changes()
        if not changes:
            return
        if QMessageBox.question(screen, t("wizard.edit.title"), t("wizard.edit.confirm")) != QMessageBox.StandardButton.Yes:
            return
        tid = screen.wizard.orch.enqueue_opened_rebuild(job.track_id, changes)
        run_step.track_job(tid)
    except Exception as error:  # noqa: BLE001 - invalid edits or queue failure must be shown
        QMessageBox.warning(screen, t("dialog.error"), str(error))

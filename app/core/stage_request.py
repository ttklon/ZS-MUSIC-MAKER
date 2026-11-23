"""Caller-owned classic request scope; never infer permissions from worker output."""


def disabled_stages(recipe):
    disabled = set()
    if recipe.get('voice_mode') == 'off':
        disabled.update(('_stage_voice_synth', '_stage_rvc', '_stage_vocal_fx'))
    if recipe.get('export_stems') is False:
        disabled.add('_stage_stems')
    if recipe.get('use_texture') is False:
        disabled.add('_stage_texture')
    return disabled


def attach_request_outcome(report, recipe, stages, quality_failures, dry_run, only):
    from app.pipeline.outcome import report_outcome
    from app.core.pipeline_runtime import STAGE_RECORDS
    disabled = disabled_stages(recipe)
    report['outcome'] = report_outcome(stages, quality_failures=quality_failures, dry_run=dry_run,
        only=only, required_names=set(STAGE_RECORDS) - disabled, not_requested_names=disabled)
    report['request_scope'] = {'not_requested': sorted(disabled), 'source': 'normalized_caller_recipe'}


def classic_execution_contract(wizard_state):
    """Only a caller's original request is authoritative, never report.recipe/scope."""
    from app.core.recipe import build_recipe
    from app.core.pipeline_runtime import STAGE_RECORDS
    disabled = disabled_stages(build_recipe(wizard_state))
    return {'required_names': set(STAGE_RECORDS) - disabled, 'not_requested_names': disabled}


def classic_outcome(report, wizard_state):
    from app.pipeline.outcome import outcome_from_report
    return outcome_from_report(report, **classic_execution_contract(wizard_state))


def classic_result(report, wizard_state, *, requested_kind):
    """Execution scope is caller-owned; content/hash/kind guards remain independent."""
    from app.pipeline.result import assess_result
    return assess_result(report, requested_kind=requested_kind, **classic_execution_contract(wizard_state))

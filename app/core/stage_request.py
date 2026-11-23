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

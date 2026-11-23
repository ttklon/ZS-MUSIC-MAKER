'use strict';
(function () {
  function transition(state = { phase: 'idle', setup: null }, event) {
    switch (event.type) {
      case 'prepare': return { phase: 'preparing', setup: null };
      case 'prepared': {
        const setup = event.result?.report?.setup;
        return { phase: event.result?.ok === true && setup?.schema === 1 && setup.ok === true ? 'ready' : 'blocked', setup: setup || null };
      }
      case 'generate':
        if (state.setup?.ok !== true || state.phase === 'preparing' || state.phase === 'running') return { ...state, phase: 'blocked' };
        return { ...state, phase: 'running' };
      case 'finished': return { ...state, phase: event.result?.ok === true ? 'done' : 'blocked' };
      case 'failed': return { ...state, phase: 'blocked' };
      default: throw new Error('Unknown creation transition');
    }
  }
  function isCompleteResult(report, taskOk, requestedKind = 'generated_singing') {
    const result = report?.result, artifact = result?.artifact;
    if (taskOk !== true || result?.schema !== 1 || result.status !== 'success' || result.succeeded !== true) return false;
    if (!['instrumental', 'speech_draft', 'own_vocal_song', 'generated_singing'].includes(requestedKind) ||
        result.kind !== requestedKind || result.requested_kind !== requestedKind) return false;
    if (!Array.isArray(result.reasons) || result.reasons.length || !artifact || artifact.valid !== true) return false;
    if (typeof report.master_path !== 'string' || !report.master_path || artifact.path !== report.master_path ||
        typeof artifact.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(artifact.sha256)) return false;
    if (report.blocked !== undefined && (!Array.isArray(report.blocked) || report.blocked.length)) return false;
    if (report.canceled || report.dry_run || (Array.isArray(report.only) ? report.only.length : report.only)) return false;
    if (report.quality_gate_failures !== undefined && (!Array.isArray(report.quality_gate_failures) || report.quality_gate_failures.length)) return false;
    if (report.outcome !== undefined && (report.outcome?.status !== 'success' || report.outcome?.succeeded !== true)) return false;
    return true;
  }
  const api = { transition, isCompleteResult };
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (typeof window === 'object') window.ZSMM_CREATION_STATE = api;
})();

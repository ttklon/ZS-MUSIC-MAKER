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
  const api = { transition };
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (typeof window === 'object') window.ZSMM_CREATION_STATE = api;
})();

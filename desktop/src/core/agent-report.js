'use strict';
/** Honest agent outcome rendering shared by the installed UI and tests. */
(function () {
  const root = typeof window === 'object' ? window : null;
  function parseLog(lines, parseEvent) {
    const result = { masterPath: null, verdict: null, blocked: [], steps: [],
      hardwarePreflight: null, typedResult: null };
    for (const raw of Array.isArray(lines) ? lines : []) {
      const line = String(raw || '');
      const event = typeof parseEvent === 'function' ? parseEvent(line) : null;
      if (event?.type === 'done') {
        const payload = event.report;
        result.masterPath = payload.master_path || null;
        result.verdict = payload.verdict || null;
        result.blocked = Array.isArray(payload.blocked) ? payload.blocked : [];
        result.hardwarePreflight = payload.hardware_preflight && typeof payload.hardware_preflight === 'object'
          ? payload.hardware_preflight : null;
        result.typedResult = payload.result && typeof payload.result === 'object' ? payload.result : null;
        continue;
      }
      if (line.includes('[agent-hit]')) result.steps.push(line.split('[agent-hit]')[1].trim());
      else if (line.trim()) result.steps.push(line.trim());
    }
    return result;
  }

  function reportText(result) {
    const lines = [];
    const complete = result.verdict === 'COMPLETE';
    if (result.verdict) lines.push(`Статус результата: ${result.verdict}`);
    lines.push(result.masterPath
      ? (complete ? `Мастер-файл: ${result.masterPath}`
        : `Создан промежуточный мастер-артефакт (полный результат не принят): ${result.masterPath}`)
      : 'Мастер-файл не создан — причина ниже.');

    const preflight = result.hardwarePreflight;
    if (preflight) {
      lines.push(`Аппаратный preflight: ${preflight.status || 'unknown'} · backend ${preflight.selected_backend || 'unknown'}.`);
      const inference = preflight.inference_verified === true ? 'подтверждён' : 'не подтверждён';
      const profile = preflight.product_profile_accepted === true ? 'принят' : 'не принят';
      lines.push(`Inference ${inference}; профиль продукта ${profile}.`);
      if (preflight.selected_backend === 'procedural_dsp' && preflight.inference_verified !== true) {
        lines.push('Процедурный DSP-рендер не подтверждает модельный inference.');
      }
    } else {
      lines.push('Запись hardware preflight отсутствует; inference и профиль продукта не подтверждены.');
    }
    for (const item of result.blocked) lines.push(`· ${item.stage}: ${item.reason}`);
    if (result.masterPath) lines.push('WAV можно открыть отдельно; наличие файла не означает принятие качества или полного сценария.');
    return lines.join('\n');
  }

  const api = { parseLog, reportText };
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.ZSMM_AGENT_REPORT = api;
})(typeof window === 'object' ? window : null);

'use strict';
/**
 * sections/beat.js — раздел «Бит»: рендер в окне, прогресс, отчёт, сохранение.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

const W = window.ZSMM_UI;
const { $, el, ask, showError, setStatus, card, statusTag, state } = W;

function reportLine(key, value) {
  return `${key}: ${value}`;
}

// -------------------------------------------------------------------- бит
// Рендер идёт внутри окна: `window.zsmm.renderBeat` в приложении уходит в
// главный процесс, в предпросмотре — в тот же `src/core/audio/engine.js`.
function beatOptions() {
  const durationSec = Number($('beat-duration').value);
  const bpm = Number($('beat-bpm').value);
  const seedText = ($('beat-seed').value || '').trim();
  if (!bpm || bpm < 40 || bpm > 220) throw new Error('BPM должен быть числом от 40 до 220');
  if (!durationSec || durationSec < 2 || durationSec > 600) {
    throw new Error('длительность должна быть от 2 до 600 секунд');
  }
  return {
    genre: ($('beat-genre').value || '').trim() || 'phonk',
    bpm,
    durationSec,
    seed: seedText === '' ? null : Number(seedText),
    useBank: Boolean($('beat-use-bank') && $('beat-use-bank').checked),
  };
}

function renderBeatReport(report) {
  const rows = report.sections.map((section) => {
    const tr = document.createElement('tr');
    tr.append(
      el('td', null, section.name),
      el('td', null, String(section.bars)),
      el('td', null, String(section.start_sec)),
      el('td', null, String(section.energy)),
      el('td', null, section.layers.join(', ')),
    );
    return tr;
  });
  $('beat-body').replaceChildren(...rows);

  const drift = (report.humanity || {}).tempo_drift || {};
  $('beat-report').textContent = [
    reportLine('жанр', `${report.genre} (семейство ${report.groove_family})`),
    reportLine('BPM / тональность', `${report.bpm} / ${report.key}`),
    reportLine('длительность', `${report.duration_sec} с, ${report.channels} канала, ${report.bits} бит`),
    reportLine('сид', report.seed === null ? 'нет (не детерминировано)' : report.seed),
    reportLine('движок ударных', `${report.drum_engine.status} — ${report.drum_engine.reason}`),
    reportLine(
      'банк сэмплов',
      report.drum_engine.sample_bank
        ? `${report.drum_engine.sample_bank.total_samples} one-shot, `
          + `${report.drum_engine.sample_bank.instruments_with_samples.join(', ')}`
        : 'не подключён',
    ),
    reportLine('секций / тактов', `${report.sections.length} / ${report.total_bars}`),
    reportLine('хук в первые 15 с', report.dramaturgy.hook_within_15s ? 'да' : 'нет'),
    reportLine('дрейф темпа', `${drift.drift_pct || 0} % (пик ${drift.peak_deviation_ms || 0} мс)`),
    reportLine(
      'формульность',
      report.repetition
        ? `${report.repetition.formulaic ? 'рисунок повторяется' : 'трек развивается'}`
          + ` (энтропия ${report.repetition.entropy_normalized}, сходство тактов `
          + `${report.repetition.bar_similarity}, тактов ${report.repetition.bars})`
        : 'не измерялась',
    ),
    reportLine(
      'измерено в миксе',
      report.measured_humanity
        ? `шумовой пол ${report.measured_humanity.noise_floor_dbfs} dBFS, `
          + `вариативность уровня ${report.measured_humanity.level_variation_db} дБ`
        : 'не измерялось',
    ),
    reportLine('пик', report.humanity.peak),
    reportLine('размер WAV', `${Math.round(report.bytes / 1024)} КБ`),
  ].join('\n');

  // Отчёт целиком, без сокращений: из него можно собрать баг-репорт, не
  // пересказывая цифры с экрана.
  state.beatReport = report;
}

/** Запомнить параметры бита, чтобы следующий запуск окна их не забыл. */
function rememberBeatOptions(options) {
  if (!window.zsmm || typeof window.zsmm.saveSettings !== 'function') return;
  window.clearTimeout(state.settingsTimer);
  // Пауза на складку: пользователь правит поля мышью, а не по буквам.
  state.settingsTimer = window.setTimeout(() => {
    window.zsmm.saveSettings(options).then((reply) => {
      if (reply && reply.ok !== true) showError(`Настройки не сохранены: ${(reply && reply.error) || 'нет ответа'}`);
    });
  }, 400);
}

/** Проставить сохранённые параметры в поля (если они есть в разметке). */
function applyBeatSettings(settings) {
  if (!settings) return;
  const map = {
    'beat-genre': 'genre',
    'beat-bpm': 'bpm',
    'beat-seed': 'seed',
    'beat-duration': 'durationSec',
  };
  for (const [id, key] of Object.entries(map)) {
    const field = $(id);
    if (field && settings[key] !== undefined && settings[key] !== null) field.value = String(settings[key]);
  }
  const bank = $('beat-use-bank');
  if (bank && typeof settings.useBank === 'boolean') bank.checked = settings.useBank;
}

async function loadBeat() {
  if (!window.zsmm || typeof window.zsmm.renderBeat !== 'function') {
    throw new Error('окно открыто вне Electron: рендер бита недоступен');
  }
  if (loadBeat.wired) return;
  loadBeat.wired = true;

  // Параметры прошлого запуска: приложение должно открываться там, где его
  // закрыли, а не с нуля.
  if (typeof window.zsmm.loadSettings === 'function') {
    try {
      const saved = await window.zsmm.loadSettings();
      if (saved && saved.ok === true) {
        applyBeatSettings(saved.data);
        if (saved.data.error) showError(saved.data.error);
      }
    } catch (err) {
      showError(`Настройки: ${err.message}`);
    }
  }

  // Что за банк подключён — видно до первого рендера, а не только в отчёте.
  try {
    const bankReply = await window.zsmm.beatBank();
    if (bankReply && bankReply.ok === true) {
      const data = bankReply.data;
      $('beat-bank-note').textContent = data.status === 'REAL_PASS'
        ? `Банк сэмплов подключён: ${data.total_samples} one-shot (${data.instruments_with_samples.join(', ')}). `
          + 'Ударные играют живые записи, синтез остаётся для импактов и FX.'
        : `Банк неполный (${data.status}): ${(data.warnings || []).join('; ') || 'часть инструментов синтезируется'}.`;
    }
  } catch (err) {
    showError(`Банк сэмплов: ${err.message}`);
  }

  $('beat-render').addEventListener('click', async () => {
    let options;
    try {
      options = beatOptions();
    } catch (err) {
      showError(err.message);
      return;
    }
    $('beat-render').disabled = true;
    $('beat-status').textContent = 'Собираю бит в окне…';
    // Прогресс по секциям: рендер длинного бита идёт десятки секунд, и без
    // этого счётчика окно выглядело бы зависшим.
    const unsubscribe = typeof window.zsmm.onBeatProgress === 'function'
      ? window.zsmm.onBeatProgress((progress) => {
        if (!progress || typeof progress.percent !== 'number') return;
        if (progress.phase === 'section') {
          $('beat-status').textContent =
            `Собираю бит: секция ${progress.section} (${progress.barsDone}/${progress.barsTotal} тактов) — ${progress.percent}%`;
        } else if (progress.phase === 'master') {
          $('beat-status').textContent = 'Собираю бит: мастеринг и замеры…';
        }
      })
      : () => {};
    try {
      const reply = await window.zsmm.renderBeat(options);
      if (!reply || reply.ok !== true) throw new Error((reply && reply.error) || 'рендер не удался');
      const { report, wavBase64 } = reply.data;
      renderBeatReport(report);
      state.beat = wavBase64;
      const audio = $('beat-audio');
      audio.src = `data:audio/wav;base64,${wavBase64}`;
      audio.classList.remove('is-hidden');
      $('beat-save').disabled = false;
      $('beat-copy').disabled = false;
      rememberBeatOptions(options);
      $('beat-status').textContent =
        `Готово: ${report.sections.length} секций, ${report.duration_sec} с. Можно слушать.`;
    } catch (err) {
      $('beat-status').textContent = 'Бит не собран';
      showError(err.message);
    } finally {
      unsubscribe();
      $('beat-render').disabled = false;
    }
  });

  $('beat-save').addEventListener('click', async () => {
    if (!state.beat) return;
    const reply = await window.zsmm.saveBeat(state.beat);
    if (!reply || reply.ok !== true) {
      showError(`Не удалось сохранить: ${(reply && reply.error) || 'нет ответа'}`);
      return;
    }
    $('beat-status').textContent = `WAV сохранён: ${reply.data.path}`;
  });

  $('beat-copy').addEventListener('click', async () => {
    if (!state.beatReport) return;
    const name = `beat_${state.beatReport.genre || 'beat'}_${state.beatReport.bpm || 0}.json`
      .replace(/\s+/g, '_');
    const reply = await window.zsmm.saveReport(name, `${JSON.stringify(state.beatReport, null, 2)}\n`);
    if (!reply || reply.ok !== true) {
      showError(`Отчёт не сохранён: ${(reply && reply.error) || 'нет ответа'}`);
      return;
    }
    $('beat-status').textContent = `Отчёт сохранён: ${reply.data.path}`;
  });
}

W.loadBeat = loadBeat;

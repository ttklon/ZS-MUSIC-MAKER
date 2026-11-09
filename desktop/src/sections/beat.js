'use strict';
/**
 * sections/beat.js — раздел «Бит»: рендер в окне, прогресс, отчёт, сохранение.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

const W = window.ZSMM_UI;
const { $, el, ask, showError, setStatus, card, statusTag, state } = W;

/**
 * Блок вокала живёт в `sections/vocal.js`: он отдаёт функцию настройки через
 * общий объект, чтобы `beat.js` не разрастался и не дублировал разметку.
 */
async function wireVocal() {
  if (typeof W.wireVocal === 'function') await W.wireVocal();
}

/** Параметры вокала: в режиме «запись» — байты WAV, записанные в окне. */
function vocalOptions() {
  if (typeof W.vocalOptions === 'function') return W.vocalOptions();
  return { mode: 'none' };
}

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
    vocal: vocalOptions(),
  };
}

function describeVocal(vocal) {
  if (!vocal) return 'не подключён';
  const source = vocal.simulated ? 'тестовый дубль (имитация, не микрофон)' : vocal.label;
  return `${source}; уровень ${vocal.gain}; в миксе ${vocal.mixed_seconds} с`
    + (vocal.starts_outside ? '; дубль длиннее трека и обрезан' : '');
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
    reportLine('вокал', describeVocal(report.vocal)),
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
    'vocal-mode': 'vocalMode',
    'vocal-text': 'vocalText',
    'vocal-gain': 'vocalGain',
  };
  for (const [id, key] of Object.entries(map)) {
    const field = $(id);
    if (field && settings[key] !== undefined && settings[key] !== null) field.value = String(settings[key]);
  }
  const bank = $('beat-use-bank');
  if (bank && typeof settings.useBank === 'boolean') bank.checked = settings.useBank;
  // Файл не запоминаем: путь мог исчезнуть, и молча рендерить «тишину»
  // хуже, чем попросить выбрать файл заново.
  // «Запись» между запусками не восстанавливаем: дубля в памяти уже нет,
  // и поле говорило бы о готовом вокале, которого не существует. Окно
  // возвращается к «без вокала» и объясняет это подписью.
  const mode = $('vocal-mode');
  if (mode && settings.vocalMode === 'record') mode.value = 'none';
  if (settings.vocalMode && settings.vocalMode !== 'file') updateVocalNote();
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

  await wireVocal();

  $('beat-render').addEventListener('click', async () => {
    let options;
    try {
      options = beatOptions();
    } catch (err) {
      showError(err.message);
      return;
    }
    $('beat-render').disabled = true;
    // Отмена доступна только во время рендера: кнопка, которая может ничего
    // не делать, вводит в заблуждение.
    const cancelButton = $('beat-cancel');
    cancelButton.disabled = !(window.zsmm && typeof window.zsmm.cancelBeat === 'function');
    $('beat-status').textContent = 'Собираю бит в окне…';
    $('vocal-save').disabled = true;
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
      // Отмена — не ошибка: иначе окно показывает «Бит не собран» с красной
      // плашкой там, где пользователь сам нажал «Отменить».
      if (reply && reply.cancelled) {
        $('beat-status').textContent = 'Рендер отменён — бит не сохранён';
        return;
      }
      if (!reply || reply.ok !== true) throw new Error((reply && reply.error) || 'рендер не удался');
      const { report, wavBase64 } = reply.data;
      renderBeatReport(report);
      state.beat = wavBase64;
      // Тот же дубль, что попал в микс: главный процесс отдаёт его отдельным
      // WAV. Сохранять «по описанию» нельзя — файл должен быть ровно тот.
      state.vocalTake = reply.data.vocalWavBase64 || null;
      state.vocalName = reply.data.vocalName || null;
      const audio = $('beat-audio');
      audio.src = `data:audio/wav;base64,${wavBase64}`;
      audio.classList.remove('is-hidden');
      $('beat-save').disabled = false;
      $('beat-open').disabled = false;
      $('beat-copy').disabled = false;
      $('vocal-save').disabled = !state.vocalTake;
      rememberBeatOptions(options);
      $('beat-status').textContent =
        `Готово: ${report.sections.length} секций, ${report.duration_sec} с. Можно слушать.`;
    } catch (err) {
      $('beat-status').textContent = 'Бит не собран';
      showError(err.message);
    } finally {
      unsubscribe();
      $('beat-render').disabled = false;
      $('beat-cancel').disabled = true;
    }
  });

  $('beat-cancel').addEventListener('click', async () => {
    if (typeof window.zsmm.cancelBeat !== 'function') return;
    $('beat-cancel').disabled = true;
    const reply = await window.zsmm.cancelBeat();
    if (!reply || reply.ok !== true) {
      showError(`Не удалось отменить: ${(reply && reply.error) || 'нет ответа'}`);
      return;
    }
    $('beat-status').textContent = reply.data && reply.data.cancelled
      ? 'Отменяю рендер…'
      : 'Нечего отменять: рендер уже завершился';
  });

  $('beat-open').addEventListener('click', async () => {
    if (!state.beat) return;
    if (typeof window.zsmm.openBeatExternal !== 'function') {
      showError('Открытие в плеере доступно только в приложении');
      return;
    }
    // Состояние кнопки говорит правду: пока плеер не ответил, второй щелчок
    // не должен открывать второй файл.
    $('beat-open').disabled = true;
    try {
      const reply = await window.zsmm.openBeatExternal(state.beat);
      if (!reply || reply.ok !== true) {
        showError(`Плеер не открылся: ${(reply && reply.error) || 'нет ответа'}`);
        return;
      }
      $('beat-status').textContent = reply.data.path
        ? `Открыто в системном плеере: ${reply.data.path}`
        : 'Системный плеер открыт';
    } finally {
      $('beat-open').disabled = false;
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

  $('vocal-save').addEventListener('click', async () => {
    if (!state.vocalTake) {
      showError('Сначала соберите трек с вокалом');
      return;
    }
    if (typeof window.zsmm.exportVocalTake !== 'function') {
      showError('Сохранение дубля доступно только в приложении');
      return;
    }
    const reply = await window.zsmm.exportVocalTake({
      wavBase64: state.vocalTake,
      name: state.vocalName || 'vocal-take',
    });
    if (!reply || reply.ok !== true) {
      showError(`Дубль не сохранён: ${(reply && reply.error) || 'нет ответа'}`);
      return;
    }
    if (!reply.data.path) {
      $('beat-status').textContent = 'Сохранение дубля отменено';
      return;
    }
    $('beat-status').textContent = `Вокальный дубль сохранён: ${reply.data.path}`;
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

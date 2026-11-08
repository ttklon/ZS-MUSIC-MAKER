'use strict';
/**
 * app.js — логика окна на чистом JS.
 *
 * Данные приходят из preload (`window.zsmm.*`), который спрашивает главный
 * процесс. Никаких сетевых запросов и никакого Python. Если раздела нет или
 * файл не прочитан — показывается причина из `error`, а не пустой экран.
 */

const state = {
  view: 'overview',
  genres: [],
  loaded: new Set(),
  tasks: [],
  taskRunning: false,
  taskLines: [],
  beat: null,
};

const $ = (id) => document.getElementById(id);

function showError(message) {
  const banner = $('error-banner');
  banner.textContent = message;
  banner.classList.remove('is-hidden');
  window.clearTimeout(showError._timer);
  showError._timer = window.setTimeout(() => banner.classList.add('is-hidden'), 9000);
}

function setStatus(ok, label) {
  const dot = $('backend-dot');
  dot.classList.toggle('is-ok', ok === true);
  dot.classList.toggle('is-bad', ok === false);
  $('backend-state').textContent = label;
}

const BRIDGE_MISSING = 'window.zsmm недоступен: окно открыто вне Electron';

/** Единая обёртка: успех → data, ошибка → исключение с текстом причины. */
async function ask(section) {
  if (!window.zsmm || typeof window.zsmm[section] !== 'function') {
    setStatus(false, 'мост не подключён');
    throw new Error(BRIDGE_MISSING);
  }
  const reply = await window.zsmm[section]();
  if (!reply || reply.ok !== true) {
    setStatus(false, 'ошибка');
    throw new Error((reply && reply.error) || 'нет ответа');
  }
  setStatus(true, 'проект открыт');
  return reply.data;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function card(label, value, hint) {
  const box = el('div', 'card');
  box.append(el('div', 'card-label', label), el('div', 'card-value', value), el('div', 'card-hint', hint));
  return box;
}

function statusTag(status) {
  const kind =
    status === 'REAL_PASS' ? 'ok' : status === 'DEPRECATED' || status === 'PLANNED' ? 'warn' : 'bad';
  return el('span', `tag ${kind}`, status);
}

// ------------------------------------------------------------------ обзор
async function loadOverview() {
  const [version, readiness, modules] = await Promise.all([ask('version'), ask('readiness'), ask('modules')]);

  $('version').textContent = version.version ? `v${version.version}` : 'версия неизвестна';
  if (version.error) showError(version.error);

  const caps = readiness.capsTriggered || [];
  const percent = readiness.percent === null || readiness.percent === undefined ? '—' : `${readiness.percent}%`;
  const inventory = readiness.moduleInventory || {};
  const cards = [
    card('Готовность', percent, readiness.stale ? `снимок ${readiness.ageDays} дн. назад` : 'по probes, с потолками'),
    card('Модулей', String(modules.total || 0), `${(modules.counts || {}).REAL_PASS || 0} достижимы`),
    card('Мёртвый код', String((modules.counts || {}).DEPRECATED || 0), 'не удалён, помечен в плане'),
    card('Потолки', String(caps.length), 'причины ниже 100 %'),
  ];
  $('overview-cards').replaceChildren(...cards);

  // причина отказа важнее любых цифр: сначала показываем её
  $('readiness-note').textContent = readiness.error
    ? readiness.error
    : caps.length
      ? 'Готовность ограничена потолками — они перечислены ниже, а не спрятаны.'
      : 'Потолков нет.';
  $('caps').replaceChildren(
    ...caps.map(([value, reason]) => {
      const item = el('li', null, `${value}% — ${reason}`);
      return item;
    }),
  );

  const stale = [];
  if (readiness.stale) stale.push(`снимок готовности сделан ${readiness.ageDays} дн. назад`);
  if (readiness.mismatch) stale.push('снимок расходится с пересчётом');
  if (stale.length) showError(`Данные устарели: ${stale.join('; ')}. Запустите node scripts/snapshot-readiness.js`);
  if (modules.error) showError(modules.error);
}

// ----------------------------------------------------------------- модули
async function loadModules() {
  const data = await ask('modules');
  if (data.error) showError(data.error);
  const counts = data.counts || {};
  $('modules-summary').textContent = data.total
    ? `${data.total} модулей: ` + Object.entries(counts).map(([k, v]) => `${k} — ${v}`).join(', ')
    : 'нет данных';

  const filter = ($('module-filter').value || '').trim().toLowerCase();
  const rows = (data.rows || [])
    .filter((row) => !filter || row.path.toLowerCase().includes(filter))
    .map((row) => {
      const tr = document.createElement('tr');
      const syntax = el('td', null, row.syntaxOk ? 'да' : 'нет');
      tr.append(
        el('td', null, row.path),
        (() => {
          const td = document.createElement('td');
          td.append(statusTag(row.status));
          return td;
        })(),
        el('td', null, row.reachable ? 'да' : 'нет'),
        el('td', null, String(row.productionReferences)),
        syntax,
      );
      return tr;
    });
  $('modules-body').replaceChildren(...rows);
}

// ------------------------------------------------------------------ жанры
function renderGenres() {
  const needle = ($('genre-filter').value || '').trim().toLowerCase();
  const list = state.genres.filter(
    (genre) => !needle || genre.name.toLowerCase().includes(needle)
      || genre.category.toLowerCase().includes(needle),
  );
  $('genre-list').replaceChildren(
    ...list.map((genre) => {
      const li = el('li', genre.hasPreset ? 'chip has-preset' : 'chip');
      li.append(el('span', 'chip-name', genre.name));
      const meta = genre.hasPreset
        ? `${genre.category} · ${genre.bpm ? genre.bpm.join('–') + ' BPM' : 'BPM нет'}`
        : `${genre.category} · без пресета`;
      li.append(el('span', 'chip-meta', meta));
      return li;
    }),
  );
  $('genre-count').textContent = `${list.length} из ${state.genres.length}`;
}

async function loadGenres() {
  const data = await ask('genres');
  state.genres = data.genres || [];
  for (const error of data.errors || []) showError(error);
  $('genres-summary').textContent =
    `каталог: ${state.genres.length} жанров, пресетов: ${data.presetCount || 0}`;
  renderGenres();
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

function reportLine(key, value) {
  return `${key}: ${value}`;
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
}

async function loadBeat() {
  if (!window.zsmm || typeof window.zsmm.renderBeat !== 'function') {
    throw new Error('окно открыто вне Electron: рендер бита недоступен');
  }
  if (loadBeat.wired) return;
  loadBeat.wired = true;

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
}

// ------------------------------------------------------------------ досье
async function loadDossiers() {
  const data = await ask('dossiers');
  if (data.error) showError(data.error);
  const artists = data.artists || [];
  $('dossier-empty').textContent = artists.length
    ? `${artists.length} артист(ов) в досье`
    : 'Досье пусто. Это не ошибка окна: артист добавляется командой python main.py --dossier-add.';
  $('dossier-list').replaceChildren(
    ...artists.map((artist) => {
      const state_ = artist.hasDossier ? 'досье собрано' : artist.deferred ? 'отложено' : 'не собрано';
      return el('li', null, `${artist.artist} — треков: ${artist.tracks}, ${state_}`);
    }),
  );
}

// ------------------------------------------------------------------ запуск
function renderTaskOutput() {
  // держим последние 2000 строк: полный вывод рендера может быть огромным
  const tail = state.taskLines.slice(-2000);
  const out = $('task-output');
  out.textContent = tail.join('\n');
  out.scrollTop = out.scrollHeight;
}

function setTaskStatus(text, running) {
  state.taskRunning = running;
  $('task-status').textContent = text;
  $('task-start').disabled = running;
  $('task-stop').disabled = !running;
}

function appendTaskLine(line) {
  state.taskLines.push(line);
  renderTaskOutput();
}

async function loadRun() {
  const tasks = await window.zsmm.listTasks();
  if (!tasks || tasks.ok === false) {
    throw new Error((tasks && tasks.error) || 'список задач недоступен');
  }
  state.tasks = tasks;
  $('task-select').replaceChildren(
    ...tasks.map((task) => {
      const option = document.createElement('option');
      option.value = task.key;
      option.textContent = task.label;
      return option;
    }),
  );
  setTaskStatus('Задача не запущена', false);

  if (!loadRun.wired) {
    loadRun.wired = true;
    $('task-start').addEventListener('click', startTask);
    $('task-stop').addEventListener('click', () => {
      window.zsmm.stopTask().then((reply) => {
        if (!reply || reply.ok !== true) showError((reply && reply.error) || 'не удалось остановить');
      });
    });
    window.zsmm.onTaskEvent((event) => {
      if (!event) return;
      if (event.type === 'start') {
        state.taskLines = [];
        setTaskStatus(`Выполняется: ${event.label} (${event.command.join(' ')})`, true);
      } else if (event.type === 'stdout') {
        appendTaskLine(event.line);
      } else if (event.type === 'stderr') {
        appendTaskLine(`[stderr] ${event.line}`);
      } else if (event.type === 'timeout') {
        appendTaskLine(`[таймаут] задача превысила ${Math.round(event.timeoutMs / 60000)} мин и остановлена`);
      }
    });
    window.zsmm.onTaskDone((result) => {
      if (!result) return;
      if (result.timedOut) {
        setTaskStatus('Остановлено по таймауту — это не успех', false);
      } else if (result.ok) {
        setTaskStatus('Завершено успешно', false);
      } else {
        setTaskStatus(`Завершено с ошибкой (код ${result.code}${result.signal ? `, сигнал ${result.signal}` : ''})`, false);
      }
    });
  }
}

async function startTask() {
  const key = $('task-select').value;
  const genre = ($('task-genre').value || '').trim();
  const seed = ($('task-seed').value || '').trim();
  const options = {};
  if (genre) options.genre = genre;
  if (seed) options.seed = seed;

  state.taskLines = [];
  renderTaskOutput();
  const reply = await window.zsmm.startTask(key, options);
  if (!reply || reply.ok !== true) {
    setTaskStatus('Не запущено', false);
    showError((reply && reply.error) || 'задача не запустилась');
    return;
  }
  setTaskStatus(`Запущено: ${reply.data.command.join(' ')} (pid ${reply.data.pid})`, true);
}

// ------------------------------------------------------------ диагностика
async function loadHealth() {
  const [system, readiness] = await Promise.all([ask('system'), ask('readiness')]);
  const rows = [
    ['корень проекта', system.root],
    ['платформа', system.platform],
    ['Node', system.node],
    ['Electron', system.electron || '—'],
    ['Chromium', system.chrome || '—'],
    ['снимок готовности', readiness.generatedAt || 'нет'],
  ];
  $('health-body').replaceChildren(
    ...rows.map(([key, value]) => {
      const tr = document.createElement('tr');
      tr.append(el('td', null, key), el('td', null, value));
      return tr;
    }),
  );
  $('health-blocks').textContent = JSON.stringify(readiness.blockScores || {}, null, 2);
  if (readiness.error) showError(readiness.error);
}

const LOADERS = {
  overview: loadOverview,
  modules: loadModules,
  genres: loadGenres,
  beat: loadBeat,
  dossiers: loadDossiers,
  run: loadRun,
  health: loadHealth,
};

const TITLES = {
  overview: 'Обзор',
  modules: 'Модули',
  genres: 'Жанры',
  beat: 'Бит',
  dossiers: 'Досье',
  run: 'Запуск',
  health: 'Диагностика',
};

async function switchView(view, { force = false } = {}) {
  if (!LOADERS[view]) return;
  state.view = view;
  $('view-title').textContent = TITLES[view];
  for (const button of document.querySelectorAll('.nav-item')) {
    button.classList.toggle('is-active', button.dataset.view === view);
  }
  for (const name of Object.keys(LOADERS)) {
    $(`view-${name}`).classList.toggle('is-hidden', name !== view);
  }
  if (force || !state.loaded.has(view)) {
    try {
      await LOADERS[view]();
      state.loaded.add(view);
    } catch (err) {
      showError(`${TITLES[view]}: ${err.message}`);
    }
  }
}

function wire() {
  for (const button of document.querySelectorAll('.nav-item')) {
    button.addEventListener('click', () => switchView(button.dataset.view));
  }
  $('refresh').addEventListener('click', async () => {
    state.loaded.clear();
    await switchView(state.view, { force: true });
  });
  $('genre-filter').addEventListener('input', renderGenres);
  $('module-filter').addEventListener('input', () => {
    if (state.loaded.has('modules')) loadModules().catch((err) => showError(err.message));
  });
  $('reveal').addEventListener('click', async () => {
    const result = await window.zsmm.revealRoot();
    if (!result || result.ok !== true) showError(`Не удалось открыть папку: ${result && result.error}`);
  });
}

if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    wire();
    switchView('overview');
  });
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { state, TITLES, LOADERS, beatOptions };
}

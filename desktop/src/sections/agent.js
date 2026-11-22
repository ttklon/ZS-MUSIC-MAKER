'use strict';
/**
 * sections/agent.js — ИИ-агентик-проводник: 4 вопроса → готовый трек.
 *
 * Зачем один экран вместо девяти вкладок: человек хочет спеть свою песню, а не
 * настроить пайплайн. Поэтому агент спрашивает четыре вещи (настроение, артист,
 * референсы, голос), сам выбирает жанр по трендам и делает трек целиком —
 * текст (локальная LLM), голос (запись → RVC-клон), бит (MusicGen/процедурный),
 * микс, мастеринг, релизный пакет.
 *
 * Что здесь честно:
 *  - кнопка запускает **настоящую** задачу Python (`zsmm.agentHit`), а не
 *    обещание: путь к мастеру окно читает из отчёта задачи;
 *  - каждая заблокированная ступень показывается с причиной и действием —
 *    «текст не готов, потому что Ollama не запущена», а не «что-то пошло не так»;
 *  - если Python недоступен, окно говорит это прямо и предлагает собрать бит
 *    движком окна — это не выдача процедурного бита за MusicGen.
 */

(function () {
const W = window.ZSMM_UI;
const { $, el, switchView, showError } = W;

/** Четыре вопроса. `id` совпадает с `id` поля в разметке — контракт с тестом. */
const QUESTIONS = [
  {
    id: 'agent-mood',
    key: 'mood',
    label: '1. Настроение / тема — что хочешь спеть?',
    placeholder: 'например: ночной город, тачки, любовь, деньги, движ',
    hint: 'пусто — агент возьмёт актуальную тему из трендов',
  },
  {
    id: 'agent-artist',
    key: 'artist',
    label: '2. Референс-артист — на кого равняться?',
    placeholder: 'например: ICEGERGERT, LIL PUMP, Скриптонит',
    hint: 'соберёт досье: почему популярен, биты, подача, темы',
  },
  {
    id: 'agent-refs',
    key: 'refs',
    label: '3. Референс-треки — ссылки или wav через запятую',
    placeholder: 'C:\\Music\\ref.wav или пусто',
    hint: 'анализ BPM/тональности — жанр выбирается сам',
  },
  {
    id: 'agent-voice',
    key: 'voice',
    label: '4. Голос — записать сейчас, файл или без вокала',
    placeholder: 'record / путь к wav / пусто',
    hint: 'record = микрофон в окне → RVC сделает клон твоего голоса',
  },
];

/** Метка строк отчёта: её печатает `app/cli/agent_task.py`. */
const REPORT_MARK = '[agent-hit]';

/** Ссылки на элементы раздела: пересоздать их по `id` было бы хрупко. */
const refs = { status: null, log: null, open: null, openNote: null };

function questionPanel(question) {
  const box = el('div', 'panel');
  const label = el('label', null, question.label);
  label.setAttribute('for', question.id);
  const input = el('input');
  input.id = question.id;
  input.placeholder = question.placeholder;
  input.setAttribute('aria-label', question.label);
  box.append(label, input, el('p', 'muted', question.hint));
  return box;
}

/** Прочитать ответы: пустая строка остаётся пустой — агент сам решит. */
function readAnswers() {
  const answers = {};
  for (const question of QUESTIONS) {
    const value = $(question.id);
    answers[question.key] = value ? String(value.value || '').trim() : '';
  }
  return answers;
}

/** Одна строка «что понял агент» — до запуска, чтобы человек проверил. */
function summary(answers) {
  const voice = answers.voice === 'record'
    ? 'микрофон → RVC'
    : answers.voice ? 'файл → RVC' : 'без вокала';
  const refCount = answers.refs
    ? answers.refs.split(',').filter((part) => part.trim()).length
    : 0;
  return `Агент понял: тема=${answers.mood || 'из трендов'} · артист=${answers.artist || 'из трендов'} · `
    + `референсы=${refCount} · голос=${voice}`;
}

/**
 * Разобрать лог задачи на прогресс и результат.
 *
 * Возвращает `{masterPath, verdict, blocked, steps}`. Строки с `[agent-hit]`
 * становятся шагами агента, остальные — обычным выводом Python: прятать их
 * нельзя, именно там видна причина отказа ступени.
 */
function parseLog(lines) {
  const result = { masterPath: null, verdict: null, blocked: [], steps: [] };
  for (const raw of lines) {
    const line = String(raw || '');
    const event = window.ZSMM_TASK_EVENTS?.parseEvent(line);
    if (event?.type === 'done') {
      const payload = event.report;
      result.masterPath = payload.master_path || null;
      result.verdict = payload.verdict || null;
      result.blocked = Array.isArray(payload.blocked) ? payload.blocked : [];
      continue;
    }
    if (line.includes(REPORT_MARK)) result.steps.push(line.split(REPORT_MARK)[1].trim());
    else if (line.trim()) result.steps.push(line.trim());
  }
  return result;
}

/** Итог прогона человеческим языком. */
function reportText(result) {
  const lines = [];
  if (result.verdict) lines.push(`Вердикт: ${result.verdict}`);
  lines.push(result.masterPath
    ? `Готовый трек: ${result.masterPath}`
    : 'Готового мастера нет — причина ниже.');
  for (const item of result.blocked) lines.push(`· ${item.stage}: ${item.reason}`);
  if (result.masterPath) lines.push('Плеер откроет тот же файл, что собрал пайплайн.');
  return lines.join('\n');
}

/** Кнопка «открыть в плеере» живёт в разметке раздела и включается по факту. */
function wireOpenButton() {
  refs.open.addEventListener('click', async () => {
    const master = refs.open.dataset.master || '';
    const reply = await window.zsmm.agentOpen(master);
    refs.openNote.textContent = reply && reply.ok
      ? `Открыл: ${reply.data.path}`
      : `Не открылось: ${(reply && reply.error) || 'нет ответа'}`;
  });
}

async function loadAgent() {
  const root = $('agent-body');
  if (!root) return;
  root.replaceChildren();

  root.append(el(
    'p',
    'muted',
    'Агент ведёт сам: ответь на 4 вопроса и нажми «Сделать хит». Жанр, тренды, досье, текст, '
    + 'голос, бит, микс и мастеринг он делает без тебя. Первый запуск может занять время: '
    + 'тяжёлые движки докачиваются один раз и дальше работают офлайн.',
  ));
  for (const question of QUESTIONS) root.append(questionPanel(question));
  const memory = el('p', 'muted', 'Тема и артист сохраняются только по кнопке. Файлы голоса и референсов не сохраняются.');
  const save = el('button', 'ghost', 'Запомнить тему и артиста');
  const clear = el('button', 'ghost', 'Забыть сохранённые ответы');
  save.id = 'agent-remember'; clear.id = 'agent-forget';
  save.addEventListener('click', () => storeAnswers(false, memory));
  clear.addEventListener('click', () => storeAnswers(true, memory));
  root.append(save, clear, memory);

  const row = el('div', null);
  row.style.display = 'flex';
  row.style.gap = '8px';
  row.style.flexWrap = 'wrap';
  row.style.marginTop = '12px';
  const btnHit = el('button', 'btn', 'Сделать хит — автономно');
  btnHit.id = 'agent-go';
  const btnRefs = el('button', 'btn', 'Показать референсы по категориям');
  btnRefs.id = 'agent-refs-open';
  row.append(btnHit, btnRefs);

  const preview = el('p', 'muted', '');
  refs.status = el('p', 'muted', '');
  refs.status.id = 'agent-status';
  refs.status.style.whiteSpace = 'pre-wrap';
  refs.status.style.marginTop = '8px';
  refs.log = el('pre', 'output', '');
  refs.open = el('button', 'ghost', 'Открыть трек в плеере');
  refs.open.disabled = true;
  refs.openNote = el('p', 'muted', '');
  const openRow = el('div', null);
  openRow.style.display = 'flex';
  openRow.style.gap = '8px';
  openRow.style.marginTop = '8px';
  openRow.append(refs.open, refs.openNote);

  // Предпросмотр обновляется на ввод: человек видит, что агент понял, до
  // нажатия кнопки, а не после десяти минут прогона.
  for (const question of QUESTIONS) {
    const field = $(question.id);
    if (field) field.addEventListener('input', () => { preview.textContent = summary(readAnswers()); });
  }
  preview.textContent = summary(readAnswers());

  btnRefs.addEventListener('click', () => {
    // Категории референсов живут в «Досье»: там же артисты и треки. Агент не
    // дублирует список, а ведёт к нему — одна база, а не две.
    switchView('dossiers', { user: true });
  });
  btnHit.addEventListener('click', () => runHit(btnHit));
  wireOpenButton();
  root.append(row, preview, refs.status, openRow, refs.log);
  await restoreAnswers(preview, memory);
}

/** Only explicit preferences survive restart; never stale media paths. */
async function storeAnswers(clear, note) {
  try {
    if (typeof window.zsmm?.saveSettings !== 'function') throw new Error('хранилище недоступно');
    const answers = readAnswers();
    const patch = { agentMood: clear ? '' : answers.mood, agentArtist: clear ? '' : answers.artist };
    const reply = await window.zsmm.saveSettings(patch);
    if (!reply?.ok) throw new Error(reply?.error || 'нет ответа');
    if (reply.data.agentMood !== patch.agentMood || reply.data.agentArtist !== patch.agentArtist) {
      throw new Error('тема или артист не прошли проверку: тема до 300 символов, имя артиста 2–80 букв/цифр');
    }
    note.textContent = clear ? 'Сохранённые ответы удалены. Текущие поля оставлены без изменений.'
      : 'Тема и артист сохранены локально. Новые ответы в форме имеют приоритет.';
  } catch (err) { note.textContent = 'Не сохранено: ' + err.message; }
}

async function restoreAnswers(preview, note) {
  try {
    if (typeof window.zsmm?.loadSettings !== 'function') return;
    const initial = readAnswers();
    const reply = await window.zsmm.loadSettings();
    if (!reply?.ok) throw new Error(reply?.error || 'нет ответа');
    for (const [key, setting] of [['mood', 'agentMood'], ['artist', 'agentArtist']]) {
      const field = $('agent-' + key);
      if (field && !initial[key] && !field.value) field.value = reply.data[setting] || '';
    }
    preview.textContent = summary(readAnswers());
    if (reply.data.error) note.textContent = 'Настройки: ' + reply.data.error;
  } catch (err) { note.textContent = 'Не удалось прочитать сохранённые ответы: ' + err.message; }
}

/** Подписки снимаются по завершении: иначе второй запуск дал бы два отчёта. */
function subscribe(onEvent, onDone) {
  const detach = [];
  const bridge = window.zsmm;
  if (typeof bridge.onTaskEvent === 'function') {
    const off = bridge.onTaskEvent(onEvent);
    if (typeof off === 'function') detach.push(off);
  }
  if (typeof bridge.onTaskDone === 'function') {
    const off = bridge.onTaskDone(onDone);
    if (typeof off === 'function') detach.push(off);
  }
  return () => detach.forEach((off) => off());
}

/** Запуск настоящей задачи и разбор её вывода. */
async function runHit(btnHit) {
  const bridge = window.zsmm;
  if (!bridge || typeof bridge.agentHit !== 'function') {
    refs.status.textContent = 'Мост не подключён: окно не может запустить сборку. Перезапусти приложение.';
    return;
  }
  const answers = readAnswers();
  const collected = [];
  btnHit.disabled = true;
  refs.log.textContent = '';
  refs.open.disabled = true;
  refs.open.dataset.master = '';
  refs.openNote.textContent = '';
  refs.status.textContent = `${summary(answers)}\nЗапускаю: докачка (если нужна) → текст → голос → бит → мастер…`;

  const onEvent = (event) => {
    if (!event) return;
    if (event.type === 'protocol') {
      collected.push(JSON.stringify(event.event));
      if (event.event?.message) refs.status.textContent = event.event.message;
    } else if (event.type === 'stdout' || event.type === 'stderr') {
      collected.push(event.line);
      refs.log.textContent = collected.slice(-400).join('\n');
      refs.log.scrollTop = refs.log.scrollHeight;
      if (event.type === 'stderr') showError(event.line);
    } else if (event.type === 'timeout') {
      refs.status.textContent = `Задача превысила ${Math.round(event.timeoutMs / 60000)} мин и была остановлена.`;
    }
  };
  const onDone = (done) => {
    btnHit.disabled = false;
    unsubscribe();
    if (done?.report) collected.push(JSON.stringify({ schema: 'zsmm.task', version: 1,
      task_id: done.taskId, seq: 1, type: 'done', ok: done.ok, report: done.report }));
    const result = parseLog(collected);
    refs.status.textContent = reportText(result);
    refs.open.disabled = !result.masterPath;
    refs.open.dataset.master = result.masterPath || '';
    if (!result.masterPath) {
      const timeout = done && done.timedOut ? '\nПрогон остановлен по таймауту — это не успех.' : '';
      refs.status.textContent += timeout;
      showError('Хит не собрался: причина в статусе агентика.');
    }
  };
  const unsubscribe = subscribe(onEvent, onDone);

  try {
    const reply = await bridge.agentHit(answers);
    if (!reply || reply.ok !== true) {
      btnHit.disabled = false;
      unsubscribe();
      refs.status.textContent = `Запуск не удался: ${(reply && reply.error) || 'нет ответа'}\n`
        + 'Если в сборке нет Python-пайплайна, собери бит в разделе «Бит» (движок окна): '
        + 'текст и клонированный голос требуют Python-версии.';
      return;
    }
    const command = (reply.data && reply.data.command) || [];
    refs.status.textContent = `${summary(answers)}\nВыполняется: ${command.join(' ')}`;
  } catch (err) {
    btnHit.disabled = false;
    unsubscribe();
    refs.status.textContent = `Ошибка запуска: ${err.message}`;
    showError(err.message);
  }
}

W.loadAgent = loadAgent;
window.ZSMM_SECTIONS.initAgent = function () { W.loadAgent = loadAgent; };
})();

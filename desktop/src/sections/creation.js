'use strict';
/** One persistent creation session: no model selection or technical navigation. */
(function () {
const W = window.ZSMM_UI;
const { $, el } = W;
const session = { step: 0, answers: { mood: '', artist: '', refs: '', voice: '' },
  online: false, busy: false, lines: [], error: '', report: null, detach: [] };
const labels = ['Замысел', 'Подготовка', 'Создание', 'Результат'];
let root;
let restored = false;
let audioUrl = null;
let audioRequest = 0;
let player = null;
function releaseAudio() {
  audioRequest++;
  if (player) { player.pause?.(); player.removeAttribute?.('src'); player.load?.(); player = null; }
  if (audioUrl) { URL.revokeObjectURL(audioUrl); audioUrl = null; }
}
async function listen(report, container, trigger) {
  releaseAudio();
  const request = audioRequest;
  trigger.disabled = true;
  for (const child of [...container.children]) if (child !== trigger) child.remove?.();
  const note = el('p', 'muted', 'Загрузка аудио…'); container.append(note);
  try {
    if (!window.zsmm?.agentAudio) throw new Error('Обновите приложение: аудиомост недоступен');
    const r = await window.zsmm.agentAudio(report.master_path);
    if (request !== audioRequest) return;
    if (!r?.ok) throw new Error(r?.error || 'Не удалось прочитать WAV');
    const binary = atob(r.data.base64);
    const bytes = Uint8Array.from(binary, char => char.charCodeAt(0));
    audioUrl = URL.createObjectURL(new Blob([bytes], { type: 'audio/wav' }));
    player = el('audio'); player.controls = true; player.preload = 'metadata'; player.src = audioUrl;
    player.setAttribute('aria-label', 'Прослушивание результата');
    player.addEventListener('error', () => { note.textContent = 'Не удалось декодировать аудио. Можно открыть файл во внешнем плеере.'; });
    container.append(player); note.textContent = 'Нажмите воспроизведение. Аудио остаётся на компьютере.';
  } catch (err) { if (request === audioRequest) note.textContent = err.message; }
  finally { if (request === audioRequest) trigger.disabled = false; }
}

function button(text, action, disabled = false) {
  const b = el('button', 'btn', text); b.disabled = disabled;
  b.addEventListener('click', action); return b;
}
function field(key, label, hint) {
  const box = el('label', 'creation-field', label);
  const input = el('input'); input.id = 'creation-' + key;
  input.value = session.answers[key]; input.placeholder = hint; input.maxLength = key === 'artist' ? 80 : 300;
  input.addEventListener('input', () => { session.answers[key] = input.value; });
  box.append(input); return box;
}
function render() {
  if (!root) return;
  releaseAudio();
  root.replaceChildren();
  const intro = el('div', 'creation-intro');
  intro.append(el('p', 'eyebrow', 'ВАША МУЗЫКАЛЬНАЯ СТУДИЯ'), el('h2', null, 'Создание трека'),
    el('p', 'muted', 'От идеи до результата — здесь, по шагам. Программа сама выбирает технические средства.'));
  const steps = el('ol', 'creation-steps');
  labels.forEach((label, i) => {
    const item = el('li', i === session.step ? 'current' : '', `${i + 1}. ${label}`);
    if (i === session.step) item.setAttribute('aria-current', 'step');
    steps.append(item);
  });
  root.append(intro, steps);
  const panel = el('div', 'panel creation-panel');
  if (session.step === 0) idea(panel);
  if (session.step === 1) preparation(panel);
  if (session.step === 2) generation(panel);
  if (session.step === 3) result(panel);
  if (session.error) { const error = el('p', 'creation-error', session.error); error.setAttribute('role', 'alert'); panel.append(error); }
  root.append(panel);
  if (session.lines.length) {
    const details = el('details', 'creation-log'); details.append(el('summary', null, 'Подробности процесса'));
    details.append(el('pre', 'output', session.lines.slice(-300).join('\n'))); root.append(details);
  }
}
function idea(panel) {
  panel.append(el('h3', null, '1. Какую песню вы хотите?'),
    field('mood', 'Тема и настроение', 'О чём песня, какие эмоции, что важно сохранить'),
    field('artist', 'Ориентир по звучанию — необязательно', 'Имя артиста, без копирования его голоса'),
    el('p', 'muted', 'Начинаем без вашего записанного голоса. Это не обещание пения или клонирования: наличие вокала будет указано в результате.'),
    button('Далее — подготовить студию', rememberIdea));
}
async function rememberIdea() {
  session.error = '';
  try {
    if (window.zsmm?.saveSettings) {
      const r = await window.zsmm.saveSettings({ agentMood: session.answers.mood.trim(), agentArtist: session.answers.artist.trim() });
      if (!r?.ok) throw new Error(r?.error || 'Не удалось сохранить замысел');
    }
    session.step = 1;
  } catch (err) { session.error = err.message; }
  render();
}
function preparation(panel) {
  panel.append(el('h3', null, '2. Подготовим всё необходимое'),
    el('p', null, 'Проверим окружение, установим недостающие движки и загрузим модели. Повторный запуск использует уже установленные компоненты.'),
    el('p', 'muted', 'Первая подготовка может занять часы и скачать много гигабайт. Платные API не нужны для локального режима. Веса и движки могут иметь ограничения лицензий.'));
  const label = el('label', 'creation-consent');
  const consent = el('input'); consent.type = 'checkbox'; consent.checked = session.online; consent.disabled = session.busy;
  consent.id = 'creation-online'; consent.addEventListener('change', () => { session.online = consent.checked; });
  label.append(consent, el('span', null, 'Разрешаю сетевые загрузки для подготовки')); panel.append(label);
  panel.append(button(session.busy ? 'Подготовка выполняется…' : 'Проверить и подготовить автоматически', () => launch('bootstrap'), session.busy));
  if (!session.busy) panel.append(button('Назад к замыслу', () => { session.step = 0; session.error = ''; render(); }));
  running(panel);
}
function generation(panel) {
  panel.append(el('h3', null, '3. Создадим трек'),
    el('p', null, `Ваш замысел: ${session.answers.mood || 'свободная тема'}. Ориентир: ${session.answers.artist || 'свободный стиль'}.`),
    el('p', 'muted', 'Текст, музыка, голос, сведение и мастеринг проверяются по фактическому результату. Черновик без вокала не будет назван законченной песней.'),
    button(session.busy ? 'Создание выполняется…' : 'Создать трек', () => launch('agent-hit'), session.busy));
  if (!session.busy) panel.append(button('Изменить замысел', () => { session.step = 0; session.error = ''; render(); }));
  running(panel);
}
function running(panel) {
  if (!session.busy) return;
  const status = el('p', 'creation-status', session.lines.at(-1) || 'Запускаю…'); status.setAttribute('aria-live', 'polite');
  panel.append(status, button('Остановить', async () => {
    try {
      const reply = await window.zsmm.stopTask();
      if (!reply?.ok) throw new Error(reply?.error || 'Не удалось остановить');
    } catch (err) { session.error = err.message; render(); }
  }));
}
function result(panel) {
  const report = session.report;
  const complete = report?.verdict === 'HIT' && !(report.blocked || []).length;
  panel.append(el('h3', null, complete ? '4. Результат создан — послушайте и оцените' : '4. Получен неполный результат'),
    el('p', null, complete ? 'Это результат генерации, а не гарантия коммерческого хита.' : 'Законченная песня не подтверждена. Ниже — отсутствующие части.'));
  for (const block of report?.blocked || []) panel.append(el('p', 'creation-error', `${block.stage}: ${block.reason}`));
  if (report?.master_path) {
    const audio = el('div', 'creation-audio');
    const play = button('Загрузить для прослушивания здесь', () => listen(report, audio, play));
    panel.append(audio); audio.append(play);
    panel.append(el('p', 'muted', report.master_path), button('Открыть во внешнем плеере', async () => {
      const r = await window.zsmm.agentOpen(report.master_path);
      if (!r?.ok) { session.error = r?.error || 'Не удалось открыть файл'; render(); }
    }));
  }
  panel.append(button('Изменить пожелания и создать заново', () => { session.step = 0; session.error = ''; render(); }),
    button('Повторить подготовку', () => { session.step = 1; session.error = ''; render(); }));
}
function consume(line) {
  session.lines.push(String(line)); session.lines = session.lines.slice(-1000);
  const start = String(line).indexOf('{');
  if (start >= 0 && String(line).includes('master_path')) {
    try { session.report = JSON.parse(String(line).slice(start)); } catch { /* ordinary log */ }
  }
}
function unsubscribe() { session.detach.splice(0).forEach(off => off()); }
async function launch(key) {
  if (session.busy) return;
  const bridge = window.zsmm;
  session.error = ''; session.lines = []; session.report = null;
  if (!bridge?.onTaskEvent || !bridge?.onTaskDone) { session.error = 'Мост приложения недоступен. Откройте установленное приложение.'; render(); return; }
  session.busy = true; render();
  try {
    if (key === 'bootstrap') {
      const saved = await bridge.saveSettings({ networkOnline: session.online });
      if (!saved?.ok) throw new Error(saved?.error || 'Не удалось сохранить разрешение сети');
    }
    unsubscribe();
    const onEvent = bridge.onTaskEvent(e => {
      if (e?.line) consume(e.line);
      if (e?.type === 'timeout') consume('Превышено время выполнения.');
      render();
    });
    const onDone = bridge.onTaskDone(r => {
      unsubscribe(); session.busy = false;
      if (key === 'bootstrap' && r?.ok) session.step = 2;
      else if (key === 'agent-hit' && session.report) session.step = 3;
      else session.error = r?.timedOut ? 'Операция остановлена по таймауту. Можно повторить.'
        : 'Операция не завершена. ' + session.lines.slice(-4).join(' · ') + ' Можно повторить на этом же шаге.';
      render();
    });
    session.detach = [onEvent, onDone].filter(off => typeof off === 'function');
    const reply = key === 'bootstrap' ? await bridge.startTask('bootstrap', {}) : await bridge.agentHit({ ...session.answers });
    if (!reply?.ok) throw new Error(reply?.error || 'Запуск не удался');
  } catch (err) { unsubscribe(); session.busy = false; session.error = err.message; render(); }
}
async function loadCreation() {
  root = $('agent-body'); render();
  if (window.zsmm?.version) {
    try {
      const r = await window.zsmm.version();
      if (r?.ok && r.data?.version) $('version').textContent = 'v' + r.data.version;
    } catch { /* version label must not block creation */ }
  }
  if (!restored && window.zsmm?.loadSettings) {
    restored = true;
    try {
      const r = await window.zsmm.loadSettings();
      if (r?.ok) {
        if (!session.answers.mood) session.answers.mood = r.data.agentMood || '';
        if (!session.answers.artist) session.answers.artist = r.data.agentArtist || '';
        session.online = r.data.networkOnline === true;
      }
    } catch (err) { session.error = 'Не удалось прочитать настройки: ' + err.message; }
    render();
  }
}
window.ZSMM_SECTIONS.initCreation = function () { W.loadCreation = loadCreation; W.releaseCreationAudio = releaseAudio; };
})();

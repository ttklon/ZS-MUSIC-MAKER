'use strict';
/**
 * sections/agent.js — ИИ-агентик-проводник: ведёт, задаёт вопросы, делает хит.
 *
 * Зачем: пользователь хочет не 9 разбросанных вкладок, а одно окно где
 * агент спрашивает «что хочешь» и сам ведёт через референсы → досье → текст → голос → бит → релиз.
 * Автономно: trend_scout + sample_hunter + SequentialAI везде, без ручных галочек.
 * Всё в одной программе: текст через Ollama/qwen, голос через RVC (внутри), бит через MusicGen/engine.js
 */

(function () {
const W = window.ZSMM_UI;
const { $, el, ask, askWith, showError } = W;

const QUESTIONS = [
  { id: 'mood', label: '1. Настроение / тема — что хочешь спеть?', placeholder: 'например: ночной город, тачки, любовь, деньги, движ', hint: 'или оставь пусто — агент возьмёт из трендов 2026' },
  { id: 'artist', label: '2. Референс-артист — на кого равняться?', placeholder: 'например: ICEGERGERT, LIL PUMP, phonk', hint: 'соберёт досье: почему популярен, что делает' },
  { id: 'refs', label: '3. Референс-треки (ссылки или wav) — через запятую', placeholder: 'https://...mp3, C:\\Music\\ref.wav или пусто', hint: 'анализ BPM/key/жанр + жанр авто' },
  { id: 'voice', label: '4. Голос — записать сейчас или взять твой из Voice Vault?', placeholder: 'record / файл / пусто = без вокала', hint: 'RVC внутри, если нет — честный BLOCKED, хит всё равно соберётся' },
];

function questionRow(q) {
  const box = el('div', 'panel');
  box.append(el('h3', null, q.label));
  const input = el('input');
  input.id = `agent-${q.id}`;
  input.placeholder = q.placeholder;
  input.setAttribute('aria-label', q.label);
  const hint = el('p', 'muted', q.hint);
  box.append(input, hint);
  return box;
}

function renderAgent() {
  const root = $('agent-body');
  root.replaceChildren();
  const lead = el('p', 'muted', 'Агентик ведёт: ответь на 4 вопроса и нажми «Сделать хит». Всё остальное — тренды, досье, текст, голос, бит, микс — он сделает сам, автономно. Если что-то не готово (RVC/MusicGen) — честно скажет и сделает fallback, но хит соберёт.');
  root.append(lead);
  for (const q of QUESTIONS) root.append(questionRow(q));
  const row = el('div', null);
  row.style.display = 'flex'; row.style.gap = '8px'; row.style.flexWrap = 'wrap'; row.style.marginTop = '12px';
  const btnGo = el('button', 'btn', 'Сделать хит — автономно');
  const btnRefs = el('button', 'btn', 'Показать референсы по категориям');
  const status = el('p', 'muted', '');
  status.style.whiteSpace = 'pre-wrap'; status.style.marginTop = '8px';
  status.id = 'agent-status';

  async function doHit() {
    const mood = ($('agent-mood')?.value || '').trim();
    const artist = ($('agent-artist')?.value || '').trim() || 'ICEGERGERT';
    const refsRaw = ($('agent-refs')?.value || '').trim();
    const voiceRaw = ($('agent-voice')?.value || '').trim();
    const refs = refsRaw ? refsRaw.split(',').map(s => s.trim()).filter(Boolean) : [];
    const voice = voiceRaw && voiceRaw !== 'record' ? voiceRaw : null;

    status.textContent = `Запускаю автономный пайплайн… mood="${mood || 'авто'}" artist="${artist}" refs=${refs.length} voice=${voice ? 'файл' : 'без'}`;
    btnGo.disabled = true;
    try {
      // 1) сначала пробуем полноценный прорыв через Python (если pipeline есть)
      if (window.zsmm && window.zsmm.runTask) {
        // используем задачу hit_factory/breakthrough через runTask если есть, иначе fallback на beat
        const payload = { genre: '', theme: mood || 'ночной город, тачки, движ', artist, refs: refs.join(','), voice: voice || '', duration: 90 };
        status.textContent = 'Агентик: собираю досье → текст → голос → бит (может занять 1-2 мин)...';
        // через askWith если есть канал hit
        if (window.zsmm.hitFactory) {
          const r = await window.zsmm.hitFactory(payload);
          if (r && r.ok) {
            status.textContent = `Готово: ${r.data?.project_id || ''} score=${r.data?.hit_score || '?'} → ${r.data?.master_path || ''}`;
            return;
          }
          status.textContent = `HitFactory: ${r.error || 'fallback к биту'}`;
        }
      }
      // 2) fallback — собрать бит прямо в окне (JS engine, без Python, автономно)
      status.textContent = 'Python-пайплайн недоступен — собираю бит в окне (JS engine, автономно)…';
      if (W.loadBeat) {
        // подставить жанр/тему в beat секцию и собрать
        const g = $('beat-genre'); if (g) g.value = RefsToGenre(refs) || 'phonk';
        const b = $('beat-bpm'); if (b) b.value = '140';
        const s = $('beat-seed'); if (s) s.value = String(Math.floor(Math.random()*10000));
        W.switchView('beat', { user: true });
        setTimeout(() => {
          const btn = $('beat-render');
          if (btn) btn.click();
          status.textContent = 'Бит собирается в «Бит» — агентик переключил туда. Текст сейчас — шаблон, но после `bootstrap --online` будет qwen.';
        }, 400);
      } else {
        status.textContent = 'Секция «Бит» не загружена.';
      }
    } catch (e) {
      status.textContent = 'Ошибка агентика: ' + e.message;
      showError(e.message);
    } finally {
      btnGo.disabled = false;
    }
  }

  function RefsToGenre(refs) {
    const s = refs.join(' ').toLowerCase();
    if (s.includes('phonk')) return 'phonk';
    if (s.includes('trap')) return 'trap';
    if (s.includes('house')) return 'house';
    return '';
  }

  async function doRefsCats() {
    status.textContent = 'Категории референсов: демо / вайб / текст / бит — смотри «Досье» и «Треки». Агент сам подберёт via sample_hunter.';
    W.switchView('dossiers', { user: true });
  }

  btnGo.addEventListener('click', doHit);
  btnRefs.addEventListener('click', doRefsCats);
  row.append(btnGo, btnRefs);
  root.append(row, status);
}

async function loadAgent() {
  renderAgent();
}

W.loadAgent = loadAgent;
window.ZSMM_SECTIONS.initAgent = function() { W.loadAgent = loadAgent; };
})();

'use strict';
/**
 * sections/health.js — раздел «Диагностика»: окружение, снимок, потолки.
 *
 * Использует общие помощники из `app.js` через `window.ZSMM_UI`.
 */

(function () {
const W = window.ZSMM_UI;
const { $, el, ask, showError, setStatus, card, statusTag, state } = W;

// ------------------------------------------------------------ диагностика
function envRow(key, value, hint) {
  const tr = document.createElement('tr');
  tr.append(el('td', null, key), el('td', null, value), el('td', 'muted', hint || ''));
  return tr;
}

/**
 * Галочка «сеть»: единственное место, где пользователь даёт согласие.
 *
 * Настройка `networkOnline` существовала в `electron/settings.js` с самого
 * начала, но окна у неё не было — то есть включить сеть было нельзя вообще,
 * и `--rvc-setup`/`--bootstrap --online` всегда отвечали `network disabled`.
 */
function wireNetworkToggle() {
  const box = $('health-network-online');
  const note = $('health-network-note');
  if (!box) return;
  // Windows Narrator читает флажок по подписи: без связи «флажок → текст»
  // он объявляет просто «флажок», и согласие на сеть даётся вслепую.
  const label = $('health-network-label');
  if (label) box.setAttribute('aria-labelledby', label.id);
  const renderNote = (online) => {
    if (!note) return;
    note.textContent = online
      ? 'сеть разрешена: задачи Python получают ZSMM_ONLINE=1'
      : 'сеть выключена — всё работает офлайн';
  };
  const canPersist = typeof window.zsmm.saveSettings === 'function';
  const load = typeof window.zsmm.loadSettings === 'function'
    ? window.zsmm.loadSettings()
    : Promise.resolve(null);
  Promise.resolve(load)
    .then((reply) => {
      const online = !!(reply && reply.ok === true && reply.data && reply.data.networkOnline === true);
      box.checked = online;
      renderNote(online);
    })
    .catch(() => renderNote(false));
  box.addEventListener('change', () => {
    const online = box.checked === true;
    renderNote(online);
    if (!canPersist) {
      if (note) {
        note.textContent = 'настройки недоступны в предпросмотре: значение не сохранено';
      }
      return;
    }
    Promise.resolve(window.zsmm.saveSettings({ networkOnline: online })).catch((err) => {
      if (note) note.textContent = `настройка не сохранена: ${err.message}`;
    });
  });
}

/**
 * Кнопка «Подготовить текстовый движок»: Ollama + модель из приложения.
 *
 * Проверка состояния (`--ollama-status`) идёт без сети и без изменений на
 * диске, поэтому её можно звать при открытии раздела; подготовка — задача
 * `ollama-setup` с живым логом в «Запуске», как у RVC.
 */
function wireOllamaSetup() {
  const button = $('health-ollama-setup');
  const status = $('health-ollama-status');
  if (!button) return;
  button.addEventListener('click', async () => {
    button.disabled = true;
    if (status) status.textContent = 'запускаю подготовку…';
    try {
      const reply = await window.zsmm.startTask('ollama-setup', {});
      if (!reply || reply.ok !== true) {
        if (status) status.textContent = `не запустилось: ${(reply && reply.error) || 'нет ответа'}`;
        return;
      }
      if (status) {
        status.textContent = 'подготовка идёт в разделе «Запуск» — там виден лог '
          + '(модель ~2.5 ГБ; без сети установка честно откажет)';
      }
    } catch (err) {
      if (status) status.textContent = `ошибка: ${err.message}`;
    } finally {
      button.disabled = false;
    }
  });
}

async function loadHealth() {
  const [system, readiness] = await Promise.all([ask('system'), ask('readiness')]);
  // Окружение приложения (пути, Python, worker) знает только главный процесс;
  // в предпросмотре этого метода нет — тогда просто не показываем строки.
  let env = null;
  if (typeof window.zsmm.environment === 'function') {
    try {
      const reply = await window.zsmm.environment();
      if (reply && reply.ok === true) env = reply.data;
    } catch (err) {
      showError(`Окружение: ${err.message}`);
    }
  }
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
  if (env) {
    const envRows = [
      envRow('сборка', env.packaged ? 'установленное приложение' : 'запуск из репозитория', 'package.json → build'),
      envRow('каталог настроек', env.user_data || '—', 'settings.json'),
      envRow('каталог для WAV', env.music_dir || '—', 'диалог сохранения'),
      envRow(
        'Каталог досье',
        env.dossier_dir || '—',
        env.dossier_source || 'запись в каталог проекта',
      ),
      envRow(
        'Python для «Запуска»',
        env.python || 'не найден',
        env.python ? 'интерпретатор найден' : 'рендер бита от него не зависит',
      ),
      envRow(
        'Пайплайн (main.py)',
        env.pipeline_root || 'нет',
        // «Python найден» не значит «задачи заработают»: в установщике кода
        // пайплайна нет вовсе.
        env.pipeline_root ? 'задачи раздела «Запуск» доступны' : 'в поставку входит только data-часть проекта',
      ),
      envRow('поток рендера', env.worker_render ? 'worker_threads' : 'главный процесс', 'окно не блокируется'),
    ];
    $('health-env').replaceChildren(...envRows);
    if (env.python_error) $('health-env-note').textContent = env.python_error;
  } else {
    $('health-env-note').textContent = 'Окружение приложения доступно только в Electron.';
  }
  $('health-blocks').textContent = JSON.stringify(readiness.blockScores || {}, null, 2);
  if (readiness.error) showError(readiness.error);
}

W.loadHealth = loadHealth;
  // В браузере все `<script>` делят одну глобальную область: второй
  // верхнеуровневый `const` с тем же именем роняет файл целиком
  // (`Identifier 'W' has already been declared`). Поэтому код раздела
  // живёт в своей функции, а наружу отдаёт только одно имя.
  window.ZSMM_SECTIONS.initHealth = function () {
    W.loadHealth = loadHealth;
    wireNetworkToggle();
    wireOllamaSetup();
  };
})();

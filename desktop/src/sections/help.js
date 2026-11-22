'use strict';
/**
 * sections/help.js — раздел «Справка»: что приложение умеет, чего не умеет
 * и где это проверить.
 *
 * Зачем отдельный раздел, а не только README: человек, поставивший
 * приложение на Windows 11, README не читает. Текст здесь — тот же, что в
 * `desktop/README.md` («Что действительно работает» и «Чего здесь нет»),
 * но короче и с путями к своим данным.
 */

(function () {
const W = window.ZSMM_UI;
const { $, el, showError } = W;

/** Contract failure must be visible, never replaced by optimistic capabilities. */
function productPanels() {
  const c = window.ZSMM_PRODUCT;
  if (!c || c.schema !== 1 || !Array.isArray(c.scenarios)) {
    return [section('Спецификация недоступна', [['Ошибка', 'Не удалось прочитать контракт продукта. Сохраните ошибки; готовность функций не подтверждена.']])];
  }
  const intro = section('Поддерживаемый продукт', [
    ['Приложение', c.name + ' · ' + c.platform], ['Основное окно', c.entry],
    ['Статус', c.state], ['Поставка', c.delivery], ['Сеть', c.network], ['Оборудование', c.hardware], ['Права ресурсов', c.rights]
  ]);
  intro.id = 'product-contract'; intro.setAttribute('data-product-id', c.id);
  return [intro,
    section('Что действительно работает — границы подтверждения', [
      ['Проверено отдельно', 'Сборка Windows, старт окна и навигация. Реальный Silero CPU проверен отдельным тестом, не как законченная песня.'],
      ['Восстановление после ошибки', c.recovery],
      ['Отмена рендера', 'Процедурный бит отменяется между секциями. Отмена тяжёлых задач проверяется отдельно.'],
      ['Одно окно', 'Повторный запуск активирует существующее окно.']
    ]),
    section('Обязательные сценарии — статус приёмки', c.scenarios.map(s => [s.name,
      (s.accepted ? 'Принят: ' : 'Не принят: ') + s.result + ' ' + s.blocker])),
    section('Чего здесь нет (честно)', [
      ['Мгновенная отмена', 'Не гарантируется: процедурный рендер ждёт границы секции.'],
      ['Гарантия готовности', c.releaseGate], ['Legacy входы', c.legacy],
      ['Подпись кода', 'Наличие сертификата не подтверждено этой спецификацией. Неподписанная сборка может вызвать SmartScreen.'],
      ...c.notEquivalent.map(text => ['Не путать', text])
    ])];
}

function createUpdatePanel() {
  const box = el('div', 'panel');
  box.append(el('h2', null, 'Обновления — один клик'));
  const info = el('p', 'muted', 'Текущая версия читается из version.json. Включите сеть в настройках. Кнопка скачивает Windows-установщик с GitHub и проверяет SHA-256. Затем приложение закрывается и открывается мастер установки. Данные в пользовательском каталоге сохраняются. Исходники ZIP не устанавливаются.');
  box.append(info);
  const row = el('div', null);
  row.style.display = 'flex'; row.style.gap = '8px'; row.style.flexWrap = 'wrap'; row.style.marginTop = '8px';
  const btnCheck = el('button', 'btn', 'Проверить обновления');
  const btnInstall = el('button', 'btn', 'Скачать и установить');
  btnInstall.disabled = true;
  const status = el('p', 'muted', '');
  status.style.marginTop = '8px'; status.style.whiteSpace = 'pre-wrap';
  let pending = null; // {url, name}
  async function doCheck() {
    pending = null; btnInstall.disabled = true;
    status.textContent = 'Проверяю GitHub…';
    btnCheck.disabled = true;
    try {
      if (!window.zsmm || !window.zsmm.updaterCheck) throw new Error('мост обновлений не подключён');
      const r = await window.zsmm.updaterCheck();
      if (!r || r.ok === false) throw new Error(r.error || 'нет ответа');
      if (r.offline) { status.textContent = 'Сеть запрещена: включи сеть в настройках или запусти с --online. Текущая: ' + (r.current || 'unknown'); btnInstall.disabled = true; return; }
      const ver = r.current || 'unknown';
      const latest = r.latest || r.tag || 'unknown';
      if (r.updateAvailable) {
        status.textContent = `Доступно обновление: ${ver} → ${latest}\n${(r.changelog || '').slice(0, 800)}${r.changelog && r.changelog.length>800?'…':''}\nРелиз: ${r.releaseUrl || ''}`;
        if (r.installer && r.installer.url) { pending = r.installer; btnInstall.disabled = false; }
        else { pending = null; btnInstall.disabled = true; status.textContent += '\n' + (r.unavailableReason || 'Установщик пока недоступен'); }
      } else {
        status.textContent = `Обновлений нет. Текущая ${ver}, последняя ${latest}. ${r.releaseUrl || ''}`;
        pending = null; btnInstall.disabled = true;
      }
    } catch (e) {
      status.textContent = 'Ошибка проверки: ' + e.message;
    } finally { btnCheck.disabled = false; }
  }
  async function doInstall() {
    if (!pending || !pending.url) { status.textContent = 'Нет установщика для установки'; return; }
    status.textContent = 'Скачиваю ' + pending.name + '…';
    btnInstall.disabled = true; btnCheck.disabled = true;
    try {
      const dl = await window.zsmm.updaterDownload(pending.url, pending.name);
      if (!dl || !dl.ok) throw new Error(dl.error || 'скачивание не удалось');
      status.textContent = `Скачано ${(dl.bytes/1e6).toFixed(1)} MB → устанавливаю… Требуется перезапуск.`;
      const res = await window.zsmm.updaterInstall(dl.path);
      if (res && res.ok) { status.textContent = 'Установщик запущен. Завершите установку в открывшемся мастере.'; }
      else { status.textContent = 'Ошибка установки: ' + (res.error || JSON.stringify(res).slice(0,500)); btnInstall.disabled = false; }
    } catch (e) {
      status.textContent = 'Ошибка: ' + e.message; btnInstall.disabled = false;
    } finally { btnCheck.disabled = false; }
  }
  btnCheck.addEventListener('click', doCheck);
  btnInstall.addEventListener('click', doInstall);
  row.append(btnCheck, btnInstall);
  box.append(row, status);
  // авто-проверка при открытии раздела, но тихо
  setTimeout(() => { if (window.zsmm && window.zsmm.updaterInfo) window.zsmm.updaterInfo().then(r=>{ if(r&&r.ok) status.textContent = 'Текущая версия: '+(r.current||'unknown')+' — нажми Проверить'; }); }, 300);
  return box;
}

function section(title, items) {
  const box = el('div', 'panel');
  box.append(el('h2', null, title));
  const list = el('ul', 'list');
  for (const [name, text] of items) {
    list.append(el('li', null, `${name} — ${text}`));
  }
  box.append(list);
  return box;
}

async function loadHelp() {
  const parts = [
    createUpdatePanel(),
    ...productPanels(),
  ];

  // Где приложение хранит своё состояние — единственное, что зависит от машины.
  let env = null;
  if (typeof window.zsmm?.environment === 'function') {
    try {
      const reply = await window.zsmm.environment();
      if (reply && reply.ok === true) env = reply.data;
    } catch (err) {
      showError(`Окружение: ${err.message}`);
    }
  }

  const where = el('div', 'panel');
  where.append(el('h2', null, 'Где что лежит'));
  const list = el('ul', 'list');
  list.append(el('li', null, `Настройки окна: ${(env && env.user_data) || 'каталог пользователя (settings.json)'}`));
  list.append(el('li', null, `Куда сохраняются WAV: ${(env && env.music_dir) || 'каталог «Музыка»'}`));
  list.append(el('li', null, `Данные проекта: ${(env && env.root) || 'resources/project'}`));
  where.append(list);
  const about = el('p', 'muted', 'Версия приложения и сборки — в разделе «Диагностика».');
  where.append(about);
  parts.push(where);

  $('help-body').replaceChildren(...parts);
}

W.loadHelp = loadHelp;
  // В браузере все `<script>` делят одну глобальную область: второй
  // верхнеуровневый `const` с тем же именем роняет файл целиком
  // (`Identifier 'W' has already been declared`). Поэтому код раздела
  // живёт в своей функции, а наружу отдаёт только одно имя.
  window.ZSMM_SECTIONS.initHelp = function () {
    W.loadHelp = loadHelp;
  };
})();

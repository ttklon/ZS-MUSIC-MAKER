'use strict';
/**
 * app-menu.js — меню приложения, отдельно от окна и IPC.
 *
 * В собранной Windows-сборке меню по умолчанию выглядит как меню браузера:
 * «Reload», «Toggle DevTools», «Zoom». Для приложения это лишнее и опасно
 * (перезагрузка сбрасывает собранный бит), поэтому меню своё: только то, что
 * действительно нужно.
 *
 * Шаблон строится здесь и не требует Electron — `Menu.buildFromTemplate`
 * вызывает `main.js`. Так шаблон проверяется обычным `node --test`, включая
 * главное правило: в сборке нет пунктов «Перезагрузить» и «Инструменты».
 */

/**
 * Шаблон меню.
 *
 * @param {object} params
 * @param {boolean} [params.isDev]   показывать пункты разработчика
 * @param {Function} [params.openRoot] открыть папку проекта
 * @param {Function} [params.showAbout] окно «О приложении»
 * @param {Function} [params.openDossier] открыть каталог, где лежит досье
 * @param {Function} [params.reloadView] перечитать данные текущего раздела
 * @returns {Array<object>} шаблон для `Menu.buildFromTemplate`
 */
function menuTemplate({
  isDev = false,
  openRoot = () => {},
  showAbout = () => {},
  openDossier = null,
  reloadView = null,
} = {}) {
  return [
    {
      label: 'Файл',
      submenu: [
        { label: 'Папка проекта', click: () => openRoot() },
        // В установленной сборке досье лежит не рядом с программой, а в
        // каталоге пользователя: без этого пункта его нечем открыть.
        ...(openDossier ? [{ label: 'Каталог досье', click: () => openDossier() }] : []),
        { type: 'separator' },
        { role: 'quit', label: 'Выход' },
      ],
    },
    {
      label: 'Вид',
      submenu: [
        { role: 'resetZoom', label: 'Обычный масштаб' },
        { role: 'zoomIn', label: 'Крупнее' },
        { role: 'zoomOut', label: 'Мельче' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Во весь экран' },
        // «Обновить раздел» есть и в релизной сборке: это не перезагрузка
        // страницы (она сбросила бы собранный бит), а повторное чтение данных
        // — то же, что кнопка «Обновить» в окне.
        ...(reloadView ? [{ label: 'Обновить раздел  F5', accelerator: 'F5', click: () => reloadView() }] : []),
        ...(isDev
          ? [
              { role: 'reload', label: 'Перезагрузить' },
              { role: 'toggleDevTools', label: 'Инструменты' },
            ]
          : []),
      ],
    },
    {
      label: 'Справка',
      submenu: [{ label: 'О приложении', click: () => showAbout() }],
    },
  ];
}

/**
 * Текст окна «О приложении».
 *
 * Пользователь должен видеть, что у него установлено: версия проекта,
 * корень данных, версии Electron/Node/Chromium — по ним понятно, какая
 * сборка упала, если что-то не работает.
 *
 * @param {object} params
 * @param {string|null} [params.version] версия проекта из `version.json`
 * @param {string|null} [params.root]
 * @param {string} [params.electron]
 * @param {string} [params.node]
 * @param {string} [params.chrome]
 * @param {string} [params.platform]
 * @param {string} [params.arch]
 * @returns {{title: string, message: string, detail: string}}
 */
function aboutText({
  version = null,
  root = null,
  electron = null,
  node = null,
  chrome = null,
  platform = process.platform,
  arch = process.arch,
} = {}) {
  return {
    title: 'ZS Music Maker',
    message: `ZS Music Maker ${version ? `v${version}` : ''}`.trim(),
    detail: [
      'Бит собирается внутри приложения: движок на JavaScript, без Python и сети.',
      root ? `Проект: ${root}` : 'Проект не найден — задайте ZSMM_ROOT.',
      `Electron ${electron || '—'}, Node ${node || '—'}, Chromium ${chrome || '—'}.`,
      `Платформа: ${platform} ${arch}.`,
    ].join('\n\n'),
  };
}

module.exports = { menuTemplate, aboutText };

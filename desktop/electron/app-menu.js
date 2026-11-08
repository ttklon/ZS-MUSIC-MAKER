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
 * @returns {Array<object>} шаблон для `Menu.buildFromTemplate`
 */
function menuTemplate({ isDev = false, openRoot = () => {}, showAbout = () => {} } = {}) {
  return [
    {
      label: 'Файл',
      submenu: [
        { label: 'Папка проекта', click: () => openRoot() },
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

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

const W = window.ZSMM_UI;
const { $, el, showError } = W;

/** Что работает — без обещаний, которые нечем проверить. */
const WORKS = [
  ['Бит', 'Движок на JavaScript внутри приложения: секции, гармония, «человечность», мастеринг. Python и сеть не нужны.'],
  ['Сэмпловый банк', '32 one-shot из data/samples (CC0). Если банк неполный, отчёт честно говорит FALLBACK и синтезирует ударные.'],
  ['Жанры и пресеты', '120 жанров из config/genres_100.json и пресеты из data/genre_presets.'],
  ['Досье', 'Артисты из data/artist_dossier — включая битые файлы: ошибка видна, а не спрятана.'],
  ['Диагностика', 'Пути, версия Electron, найден ли Python, каким путём идёт рендер (worker или главный процесс).'],
  ['Сохранение', 'WAV — в «Музыку» пользователя; отчёт — JSON с теми же числами, что на экране.'],
  ['Отмена рендера', 'Кнопка «Отменить» прерывает сборку между секциями: недосчитанный WAV на диск не попадает.'],
  ['Одно окно', 'Второй запуск открывает уже работающее окно и разворачивает его, если оно свёрнуто.'],
];

/** Чего нет — с причиной, а не с обещанием «скоро». */
const DOES_NOT = [
  ['Подпись кода', 'Установщик не подписан сертификатом: Windows покажет предупреждение SmartScreen при первом запуске.'],
  ['Запуск пайплайна без Python', 'Раздел «Запуск» вызывает python main.py …; в установленном приложении Python не поставляется.'],
  ['Облако и аккаунты', 'Сеть не используется вовсе — это свойство, а не недоделка.'],
  ['Свойства файла EXE', 'Версия и описание в свойствах файла не заполнены: для этого нужна правка ресурсов на Windows.'],
  ['Мгновенная отмена', 'Отмена срабатывает между секциями, поэтому посреди длинной секции ждёт её конца.'],
  ['Отдельный процесс для рендера', 'Рендер живёт в потоке (worker_threads): окно отвечает, но на слабых машинах возможны просадки анимаций.'],
];

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
    section('Что действительно работает', WORKS),
    section('Чего здесь нет (честно)', DOES_NOT),
  ];

  // Где приложение хранит своё состояние — единственное, что зависит от машины.
  let env = null;
  if (typeof window.zsmm.environment === 'function') {
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

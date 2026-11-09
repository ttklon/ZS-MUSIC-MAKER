'use strict';
/**
 * scripts/window-e2e.js — прогон окна в настоящем браузере: не «видно», а «работает».
 *
 * `screenshots.js` показывает, что разделы рисуются. Здесь проверяется то, что
 * делает человек: нажать «Собрать бит» и дождаться отчёта, завести артиста,
 * добавить трек с текстом, запустить задачу без Python, поймать отказ при
 * неверном вводе. Всё это идёт против `preview-server.js`, который отдаёт
 * настоящий `src/` и шим моста — тот же код разделов, что в Electron.
 *
 * Каталог правок подменяется копией (`ZSMM_PREVIEW_DATA`), поэтому прогон не
 * трогает данные проекта: проверка не должна оставлять после себя артистов.
 *
 * Запуск:
 *   node scripts/preview-server.js &
 *   ZSMM_CHROME=/путь/к/chromium node scripts/window-e2e.js [каталог для отчёта]
 *
 * Код возврата 0 — все сценарии прошли; 1 — есть провал (он назван); 2 — нет
 * браузера/puppeteer.
 */

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const OUT = path.resolve(process.argv[2] || path.join(os.tmpdir(), 'zsmm-e2e'));
const URL_BASE = process.env.ZSMM_PREVIEW_URL || 'http://127.0.0.1:4173/';
const CHROME = process.env.ZSMM_CHROME || '';

/** Подождать, пока функция в странице вернёт истину. */
async function waitFor(page, fn, { timeout = 60000, label = 'условие', arg = undefined } = {}) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await page.evaluate(fn, arg)) return true;
    await new Promise((resolve) => { setTimeout(resolve, 250); });
  }
  throw new Error(`не дождались: ${label}`);
}

/** Нажать по id и дать окну обработать нажатие. */
async function click(page, id) {
  await page.click(`#${id}`);
  await new Promise((resolve) => { setTimeout(resolve, 400); });
}

async function main() {
  if (!CHROME) {
    process.stderr.write('укажите браузер: ZSMM_CHROME=/путь/к/chromium node scripts/window-e2e.js\n');
    return 2;
  }
  let puppeteer;
  try {
    // eslint-disable-next-line global-require, import/no-unresolved
    puppeteer = require('puppeteer-core');
  } catch {
    process.stderr.write('нужен puppeteer-core\n');
    return 2;
  }

  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--single-process'],
    defaultViewport: { width: 1440, height: 1000 },
    timeout: 120000,
  });

  const page = await browser.newPage();
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(`pageerror: ${error.message}`));
  page.on('console', (message) => {
    if (message.type() === 'error') pageErrors.push(`console: ${message.text()}`);
  });

  const steps = [];
  const record = (name, ok, detail) => {
    steps.push({ name, ok: Boolean(ok), detail: String(detail ?? '') });
    process.stdout.write(`${ok ? 'ok  ' : 'FAIL'} ${name} — ${detail}\n`);
  };

  try {
    await page.goto(URL_BASE, { waitUntil: 'networkidle2', timeout: 60000 });
    await waitFor(page, () => document.getElementById('view-title') && document.getElementById('view-title').textContent === 'Обзор', { label: 'окно открылось' });
    record('окно открылось', true, 'раздел «Обзор»');

    // --- 1. Бит: рендер из окна, отчёт, кнопки результата
    await page.click('[data-view="beat"]');
    await page.evaluate(() => {
      document.getElementById('beat-duration').value = '4';
      document.getElementById('beat-bpm').value = '120';
      document.getElementById('beat-seed').value = '5';
    });
    await click(page, 'beat-render');
    await waitFor(
      page,
      () => /Готово|Ошибка|собран/i.test(document.getElementById('beat-status').textContent || ''),
      { timeout: 120000, label: 'бит собран' },
    );
    const beat = await page.evaluate(() => ({
      status: document.getElementById('beat-status').textContent,
      rows: document.querySelectorAll('#beat-body tr').length,
      // Отчёт целиком: обрезка до 400 символов оставляла проверку вокала
      // без самой строки про вокал, и она ложно падала.
      report: document.getElementById('beat-report').textContent.trim(),
      saveEnabled: !document.getElementById('beat-save').disabled,
      openEnabled: !document.getElementById('beat-open').disabled,
    }));
    record('бит собран в окне', /Готово/.test(beat.status) && beat.rows >= 3, `${beat.rows} секций, «${beat.status}»`);
    // Без включённого вокала отчёт обязан сказать «не подключён», а не молчать.
    record(
      'отчёт называет вокал',
      /вокал:\s*не подключён/.test(beat.report),
      beat.report.split('\n').find((line) => line.startsWith('вокал:')) || beat.report.slice(0, 80),
    );
    record('после рендера доступны сохранение и плеер', beat.saveEnabled && beat.openEnabled, `сохранить=${beat.saveEnabled}, плеер=${beat.openEnabled}`);
    // Плеер: настоящий Chromium применит CSP окна. С `data:`-адресом он
    // молчал, и это видел только браузер.
    const player = await page.evaluate(async () => {
      const audio = document.getElementById('beat-audio');
      const src = audio.getAttribute('src') || '';
      const loaded = await new Promise((resolve) => {
        if (audio.readyState >= 1) { resolve({ state: audio.readyState, duration: audio.duration }); return; }
        const done = () => resolve({ state: audio.readyState, duration: audio.duration });
        audio.addEventListener('loadedmetadata', done, { once: true });
        audio.addEventListener('error', () => resolve({ state: -1, duration: 0 }), { once: true });
        audio.load();
        setTimeout(() => resolve({ state: audio.readyState, duration: audio.duration }), 5000);
      });
      return { src: src.slice(0, 24), ...loaded };
    });
    record(
      'плеер принимает готовый WAV',
      player.state > 0 && player.duration > 1,
      `источник ${player.src}…, состояние ${player.state}, ${Number(player.duration).toFixed(1)} с`,
    );
    await page.screenshot({ path: path.join(OUT, 'beat-after-render.png') });

    // --- 2. Вокал: тестовый дубль в миксе и честная подпись
    await page.select('#vocal-mode', 'test');
    await new Promise((resolve) => { setTimeout(resolve, 300); });
    await click(page, 'beat-render');
    await waitFor(
      page,
      () => /Готово|Ошибка/i.test(document.getElementById('beat-status').textContent || ''),
      { timeout: 120000, label: 'бит с вокалом' },
    );
    const withVocal = await page.evaluate(() => document.getElementById('beat-report').textContent);
    record(
      'вокал размечен как имитация',
      /тестовый дубль \(имитация, не микрофон\)/.test(withVocal),
      withVocal.split('\n').find((line) => line.startsWith('вокал:')) || 'строки про вокал нет',
    );

    // --- 3. Ошибка ввода: причина, а не тишина
    await page.evaluate(() => { document.getElementById('beat-bpm').value = '999'; });
    await click(page, 'beat-render');
    const banner = await page.evaluate(() => document.getElementById('error-banner').innerText.trim());
    record('неверный BPM назван причиной', /BPM/.test(banner), banner.slice(0, 90));

    // --- 4. Досье: добавить и удалить артиста
    await page.click('[data-view="dossiers"]');
    await new Promise((resolve) => { setTimeout(resolve, 800); });
    const before = await page.$$eval('#dossier-list li', (items) => items.length);
    // Имя уникально для прогона: иначе повторный запуск на тех же данных
    // получит «артист уже есть» и проверка станет ложной.
    const artistName = `Проверка Окна ${Date.now().toString().slice(-6)}`;
    await page.type('#dossier-name', artistName);
    await click(page, 'dossier-add');
    await waitFor(
      page,
      (name) => [...document.querySelectorAll('#dossier-list li')].some((li) => li.textContent.includes(name)),
      { timeout: 20000, label: 'артист появился в списке', arg: artistName },
    );
    const after = await page.$$eval('#dossier-list li', (items) => items.length);
    record('артист добавлен из окна', after === before + 1, `было ${before}, стало ${after}`);
    await page.screenshot({ path: path.join(OUT, 'dossier-after-add.png') });

    // Удалить того же артиста: окно не должно оставлять за собой данных.
    const removed = await page.evaluate(async (name) => {
      const items = [...document.querySelectorAll('#dossier-list li')];
      const card = items.find((li) => li.textContent.includes(name));
      if (!card) return { ok: false, error: 'карточки нет' };
      const button = [...card.querySelectorAll('button')].find((b) => /Удалить/.test(b.textContent));
      if (!button) return { ok: false, error: 'кнопки «Удалить» нет' };
      button.click();
      return { ok: true };
    }, artistName);
    if (removed.ok) {
      await waitFor(
        page,
        (name) => ![...document.querySelectorAll('#dossier-list li')].some((li) => li.textContent.includes(name)),
        { timeout: 20000, label: 'артист удалён', arg: artistName },
      );
      record('артист удалён из окна', true, 'список вернулся к исходному');
    } else {
      record('артист удалён из окна', false, removed.error);
    }

    // --- 5. Треки: завести трек с текстом и увидеть его в списке
    await page.click('[data-view="tracks"]');
    await new Promise((resolve) => { setTimeout(resolve, 900); });
    const trackTitle = `Проверочный трек ${Date.now().toString().slice(-6)}`;
    await page.type('#tracks-title', trackTitle);
    await page.type('#tracks-lyrics', 'первая строка\nвторая строка');
    await click(page, 'tracks-add');
    await waitFor(
      page,
      (title) => document.getElementById('tracks-list').innerText.includes(title)
        || /ошибк/i.test(document.getElementById('error-banner').innerText || ''),
      { timeout: 20000, label: 'трек появился', arg: trackTitle },
    );
    const tracks = await page.evaluate(() => ({
      list: document.getElementById('tracks-list').innerText,
      status: document.getElementById('tracks-status').innerText,
      banner: document.getElementById('error-banner').innerText.trim(),
    }));
    record('трек заведён из окна', tracks.list.includes(trackTitle), tracks.status.slice(0, 80));
    record(
      'статус трека честный',
      /не разобран/.test(tracks.list),
      tracks.list.split('\n').find((line) => line.includes(trackTitle)) || tracks.list.slice(0, 80),
    );
    await page.screenshot({ path: path.join(OUT, 'tracks-after-add.png') });

    // --- 6. Задача без Python: живой вывод и итог
    await page.click('[data-view="run"]');
    await new Promise((resolve) => { setTimeout(resolve, 800); });
    await page.select('#task-select', 'native-files');
    await click(page, 'task-start');
    await waitFor(
      page,
      // Итог задачи — «Завершено успешно» / «Завершено с ошибкой»: слово
      // «готово» в нём не встречается, и проверка на него ждала вечно.
      () => /Завершено|Остановлено/i.test(document.getElementById('task-status').textContent || ''),
      { timeout: 60000, label: 'задача завершилась' },
    );
    const task = await page.evaluate(() => ({
      status: document.getElementById('task-status').textContent,
      output: document.getElementById('task-output').textContent.trim(),
    }));
    record(
      'задача без Python отработала',
      /Завершено успешно/.test(task.status) && task.output.length > 20,
      `${task.status} | ${task.output.split('\n')[0].slice(0, 70)}`,
    );
    await page.screenshot({ path: path.join(OUT, 'run-after-task.png') });
  } catch (error) {
    record('сценарии дошли до конца', false, error.message);
  }

  const report = {
    url: URL_BASE,
    steps,
    ok: steps.every((step) => step.ok) && pageErrors.length === 0,
    pageErrors,
  };
  fs.writeFileSync(path.join(OUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  await browser.close();

  const failed = steps.filter((step) => !step.ok);
  if (pageErrors.length) process.stderr.write(`ошибки страницы: ${pageErrors.slice(0, 5).join(' | ')}\n`);
  process.stdout.write(`\nитог: ${steps.length - failed.length}/${steps.length} шагов, ошибок страницы ${pageErrors.length}\n`);
  return failed.length === 0 && pageErrors.length === 0 ? 0 : 1;
}

if (require.main === module) {
  main().then((code) => { process.exitCode = code; }).catch((error) => {
    process.stderr.write(`прогон упал: ${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = { waitFor, main };

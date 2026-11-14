'use strict';
/**
 * scripts/screenshots.js — снять скриншоты окна в настоящем браузере.
 *
 * Зачем: окно — это страница Chromium. DOM-двойник (`test/fake-dom.js`)
 * ловит обращения к несуществующим id, но не видит ни вёрстки, ни глобальной
 * области видимости скриптов. Именно поэтому ошибка «Identifier 'W' has
 * already been declared» жила в коде: в двойнике каждый скрипт грузился
 * отдельной функцией, а в браузере все `<script>` делят одну область.
 * Этот скрипт гоняет страницу так, как её гоняет Electron.
 *
 * Что нужно:
 *   1) `node scripts/preview-server.js` — он отдаёт `src/` и шим моста;
 *   2) puppeteer-core и любой Chromium: `ZSMM_CHROME=/путь/к/chromium`.
 * В окружении разработки агента Chromium взят из пакета `@sparticuz/chromium`
 * (он же тянет libnspr4/libnss3 для Amazon Linux), в CI — обычный chromium.
 *
 * Запуск:
 *   ZSMM_CHROME=/tmp/chromium node scripts/screenshots.js [каталог]
 *
 * Результат: PNG по разделу + `report.json` с заголовком, длиной текста и
 * баннером ошибки для каждого раздела. Эти файлы лежат в `docs/screenshots/`
 * и проверяются тестом `test/screenshots.test.js`.
 */

const fs = require('node:fs');
const path = require('node:path');

const OUT = path.resolve(process.argv[2] || path.join(__dirname, '..', '..', 'docs', 'screenshots'));
const URL_BASE = process.env.ZSMM_PREVIEW_URL || 'http://127.0.0.1:4173/';
const CHROME = process.env.ZSMM_CHROME || '';

/** Подпись раздела в навигации → имя файла. */
const VIEWS = ['overview', 'modules', 'genres', 'beat', 'dossiers', 'tracks', 'run', 'health', 'help'];

async function main() {
  if (!CHROME) {
    process.stderr.write('укажите браузер: ZSMM_CHROME=/путь/к/chromium node scripts/screenshots.js\n');
    return 2;
  }
  let puppeteer;
  try {
    // Зависимость не входит в проект: без Chromium она бесполезна.
    // eslint-disable-next-line global-require, import/no-unresolved
    puppeteer = require('puppeteer-core');
  } catch {
    process.stderr.write('нужен puppeteer-core: npm i -g puppeteer-core (или локально в отдельном каталоге)\n');
    return 2;
  }

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    // `--single-process` нужен там, где песочница не даёт создавать zygote.
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--single-process'],
    defaultViewport: { width: 1440, height: 900 },
    timeout: 120000,
  });

  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });

  await page.goto(URL_BASE, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise((resolve) => { setTimeout(resolve, 2000); });
  fs.mkdirSync(OUT, { recursive: true });

  const found = await page.$$eval('[data-view]', (nodes) => nodes.map((node) => node.dataset.view));
  const views = found.length ? found : VIEWS;
  const report = { url: URL_BASE, viewport: '1440x900', views: {} };

  for (const view of views) {
    if (!VIEWS.includes(view)) continue;
    await page.click(`[data-view="${view}"]`);
    await new Promise((resolve) => { setTimeout(resolve, 1200); });
    const state = await page.evaluate((name) => {
      const title = document.getElementById('view-title');
      const panel = document.getElementById(`view-${name}`);
      // Текст ошибки живёт в своём узле внутри баннера: у баннера теперь
      // есть ещё и кнопка закрытия, и `innerText` баннера тянул бы «×».
      const banner = document.getElementById('error-text');
      return {
        title: title ? title.textContent : null,
        hasPanel: Boolean(panel),
        textLength: panel ? panel.innerText.trim().length : 0,
        sample: panel ? panel.innerText.replace(/\s+/g, ' ').trim().slice(0, 120) : '',
        errorBanner: banner && banner.textContent.trim() ? banner.textContent.trim() : null,
      };
    }, view);
    report.views[view] = state;
    await page.screenshot({ path: path.join(OUT, `${view}.png`) });
    process.stdout.write(`${view}: ${state.title}, ${state.textLength} симв.${state.errorBanner ? ` | БАННЕР: ${state.errorBanner}` : ''}\n`);
  }

  report.pageErrors = errors;
  fs.writeFileSync(path.join(OUT, 'report.json'), `${JSON.stringify(report, null, 2)}\n`);
  await browser.close();
  if (errors.length) {
    process.stderr.write(`ошибки страницы: ${errors.slice(0, 5).join(' | ')}\n`);
    return 1;
  }
  return 0;
}

if (require.main === module) {
  main().then((code) => { process.exitCode = code; }).catch((error) => {
    process.stderr.write(`не удалось снять скриншоты: ${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = { VIEWS, OUT };

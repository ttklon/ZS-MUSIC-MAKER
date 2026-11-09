'use strict';
/**
 * test/signing.test.js — подпись кода: конфигурация, проверка и честность.
 *
 * Подписать файл в CI нельзя без сертификата (§ «Подпись кода» в README).
 * Но всё остальное проверяемо:
 *  - конфигурация electron-builder читает подпись из переменных окружения,
 *    а не из закоммиченных путей и паролей;
 *  - проверка подписи (`verify-signature.js`) правильно разбирает ответ
 *    Windows и никогда не называет неподписанный файл подписанным;
 *  - workflow подписывает только при наличии секретов и всегда оставляет
 *    в отчёте фактическое состояние, а не обещание;
 *  - политика подписи (то, что требует SignPath) лежит в репозитории.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const DESKTOP = path.resolve(__dirname, '..');
const ROOT = path.resolve(DESKTOP, '..');
const pkg = JSON.parse(fs.readFileSync(path.join(DESKTOP, 'package.json'), 'utf8'));
const signature = require('../scripts/verify-signature');

const read = (...parts) => fs.readFileSync(path.join(ROOT, ...parts), 'utf8');

const buildConfig = require('../scripts/build-config');

/** Полный набор переменных Azure Trusted Signing — как в CI. */
const FULL_ENV = {
  AZURE_CODE_SIGNING_ENDPOINT: 'https://weu.codesigning.azure.net',
  AZURE_CODE_SIGNING_ACCOUNT_NAME: 'zsmm-signing',
  AZURE_CERTIFICATE_PROFILE_NAME: 'zsmm-profile',
  AZURE_CLIENT_ID: 'client-id',
  AZURE_TENANT_ID: 'tenant-id',
  AZURE_CLIENT_SECRET: 'secret',
};

test('без секретов блок подписи не появляется вовсе', () => {
  // electron-builder включает подпись по самому наличию `azureSignOptions`,
  // а не по флагу. Блок в package.json означал бы: «каждая сборка без
  // сертификата падает». Поэтому в описании сборки его нет.
  assert.equal(pkg.build.win.azureSignOptions, undefined, 'в package.json не должно быть блока подписи');
  assert.equal(pkg.build.win.sign, undefined);

  const { config, signing, missing } = buildConfig.buildConfig({ pkg, env: {} });
  assert.equal(signing, false);
  assert.equal(config.win.azureSignOptions, undefined, 'без секретов подпись не включается');
  assert.equal(missing.length, buildConfig.SIGNING_ENV.length);

  // И ни одного секрета в описании сборки.
  assert.doesNotMatch(JSON.stringify(pkg.build), /password|secret|token/i);
});

test('с секретами подпись включается ключами, которые читает electron-builder', () => {
  const { config, signing, missing } = buildConfig.buildConfig({ pkg, env: FULL_ENV });
  assert.equal(signing, true);
  assert.deepEqual(missing, []);
  const options = config.win.azureSignOptions;
  assert.ok(options, 'нужен azureSignOptions');
  // Ровно эти три ключа читает app-builder-lib 25
  // (out/codeSign/windowsSignAzureManager.js) — camelCase, иначе он получит
  // undefined и подпись молча не пройдёт.
  assert.equal(options.endpoint, FULL_ENV.AZURE_CODE_SIGNING_ENDPOINT);
  assert.equal(options.codeSigningAccountName, FULL_ENV.AZURE_CODE_SIGNING_ACCOUNT_NAME);
  assert.equal(options.certificateProfileName, FULL_ENV.AZURE_CERTIFICATE_PROFILE_NAME);
  assert.equal(options.FileDigest, 'SHA256');
  // Секрет в конфигурацию не попадает: он нужен только Entra ID.
  assert.doesNotMatch(JSON.stringify(options), /secret/);
});

test('неполный набор секретов не даёт «наполовину подписи»', () => {
  // Если задан только endpoint, electron-builder пошёл бы подписывать с
  // пустым профилем — это ошибка сборки на ровном месте.
  const partial = { ...FULL_ENV };
  delete partial.AZURE_CLIENT_SECRET;
  const { signing, missing, config } = buildConfig.buildConfig({ pkg, env: partial });
  assert.equal(signing, false);
  assert.deepEqual(missing, ['AZURE_CLIENT_SECRET']);
  assert.equal(config.win.azureSignOptions, undefined);

  // Пустые строки считаются отсутствием, а не «задано».
  const blank = { ...FULL_ENV, AZURE_CLIENT_SECRET: '   ' };
  assert.equal(buildConfig.signingStatus(blank).ready, false);
});

test('сгенерированная конфигурация сборки не версионируется', () => {
  const ignore = read('.gitignore');
  assert.match(ignore, /desktop\/build-config\.generated\.json/);
  // И сборка идёт именно через неё, а не напрямую из package.json.
  assert.match(pkg.scripts.dist, /build-config\.js/);
  assert.match(pkg.scripts.dist, /--config build-config\.generated\.json/);
  assert.match(pkg.scripts['dist:dir'], /build-config\.js/);
});

test('проверка подписи не называет неподписанный файл подписанным', () => {
  const unsigned = signature.parseSignature(JSON.stringify({
    Status: 'NotSigned',
    StatusMessage: 'The file is not digitally signed.',
    SignerCertificate: null,
    TimeStamperCertificate: null,
  }));
  assert.equal(unsigned.signed, false);
  assert.equal(unsigned.status, 'NotSigned');
  assert.match(unsigned.message, /not digitally signed/);

  const valid = signature.parseSignature(JSON.stringify({
    Status: 'Valid',
    StatusMessage: 'Signature verified.',
    SignerCertificate: { Subject: 'CN=ZS Music Maker, O=ZS Music Maker' },
    TimeStamperCertificate: { Subject: 'CN=Microsoft Time-Stamp Service' },
  }));
  assert.equal(valid.signed, true);
  assert.equal(valid.signer, 'CN=ZS Music Maker, O=ZS Music Maker');
  assert.equal(valid.timestamped, true);

  // Ошибка подписи (истёк сертификат, файл правили после подписи) — это не успех.
  const broken = signature.parseSignature(JSON.stringify({
    Status: 'HashMismatch',
    StatusMessage: 'Hash mismatch.',
    SignerCertificate: { Subject: 'CN=ZS Music Maker' },
  }));
  assert.equal(broken.signed, false);

  // Мусор на входе не должен превращаться в «подписано».
  for (const raw of ['', 'не json', '[]', 'null', '{']) {
    assert.equal(signature.parseSignature(raw).signed, false, `вход «${raw}» дал подпись`);
  }
});

test('сводка по нескольким файлам требует подписи у каждого', () => {
  const signedRow = { file: 'a.exe', applicable: true, status: 'Valid', signed: true, signer: 'CN=A' };
  const unsignedRow = { file: 'b.exe', applicable: true, status: 'NotSigned', signed: false, signer: null };

  assert.equal(signature.summarize([signedRow]).signed, true);
  const mixed = signature.summarize([signedRow, unsignedRow]);
  assert.equal(mixed.signed, false, 'один подписанный файл не делает подписанной сборку');
  assert.match(mixed.summary, /b\.exe/);

  const none = signature.summarize([unsignedRow]);
  assert.equal(none.signed, false);
  assert.equal(none.applicable, true);

  // Вне Windows проверка недоступна — это не «подписано».
  const unavailable = signature.summarize([{ file: 'c.exe', applicable: false, status: 'Unavailable', signed: false }]);
  assert.equal(unavailable.signed, false);
  assert.equal(unavailable.applicable, false);
  assert.match(unavailable.summary, /недоступна/);
});

test('коды возврата проверки подписи разные для трёх исходов', () => {
  // 2 — «проверить нечем» (не Windows), 1 — «не подписано», 0 — «подписано».
  // Если бы «не проверили» возвращало 1, CI падал бы на Linux-шагах; если бы
  // 0 — неподписанная сборка считалась бы подписанной.
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'zsmm-sign-'));
  const file = path.join(tmp, 'fake.exe');
  fs.writeFileSync(file, 'not really an exe');

  const report = signature.verifyFile(file);
  if (process.platform === 'win32') {
    assert.equal(report.applicable, true);
    assert.equal(report.signed, false, 'текстовый файл не может быть подписан');
  } else {
    assert.equal(report.applicable, false);
    assert.equal(report.signed, false);
    assert.match(report.message, /только на Windows/);
    assert.equal(signature.main(['node', 'verify', file]), 2);
  }

  // Отсутствующий файл — это провал, а не «нечего проверять».
  const missing = signature.verifyFile(path.join(tmp, 'nope.exe'));
  assert.equal(missing.signed, false);
  assert.equal(missing.status, 'Missing');

  // Без аргументов скрипт не падает, а объясняет, что нужно.
  assert.equal(signature.main(['node', 'verify']), 2);
  fs.rmSync(tmp, { recursive: true, force: true });
});

test('workflow определяет секреты, подписывает и проверяет результат', () => {
  const workflow = read('.github', 'workflows', 'build.yml');

  // Наличие секретов проверяется до сборки и попадает в окружение шага.
  assert.match(workflow, /AZURE_CODE_SIGNING_ENDPOINT/);
  assert.match(workflow, /secrets\.AZURE_CLIENT_SECRET/);
  assert.match(workflow, /ZSMM_CODE_SIGNING=1/);

  // Состояние подписи проверяется у готового файла, а не у переменных.
  assert.match(workflow, /verify-signature\.js/);
  assert.match(workflow, /signature\.json/);
  // Секреты есть, а подпись не встала — это провал, а не предупреждение.
  assert.match(workflow, /секреты заданы, но файлы не подписаны/);

  // Отчёт о подписи едет и в артефакты, и в релиз.
  const artifactBlocks = workflow.split('retention-days').length - 1;
  assert.ok(artifactBlocks >= 2);
  assert.match(workflow, /electron-win\/signature\.json/);

  // И текст релиза не утверждает подпись как факт — только относит к отчёту.
  assert.match(workflow, /Если она не настроена, Windows 11 покажет предупреждение/);
  assert.doesNotMatch(workflow, /Установщик подписан/);
});

test('политика подписи кода лежит в репозитории и называет роли', () => {
  const policy = read('CODE_SIGNING_POLICY.md');
  for (const needle of ['SignPath', 'Azure Trusted Signing', 'SmartScreen', 'приватност', 'Роли', 'проверить подпись']) {
    assert.match(policy, new RegExp(needle, 'i'), `в политике нет «${needle}»`);
  }
  // Политика обязана честно говорить, что подписи сейчас нет.
  assert.match(policy, /сейчас .*не подписан|подписи нет|не настроена/i);
});

test('скрипт проверки подписи не требует сети и синтаксически цел', () => {
  const source = fs.readFileSync(path.join(DESKTOP, 'scripts', 'verify-signature.js'), 'utf8');
  assert.doesNotMatch(source, /require\('node:https'\)|require\('node:http'\)|fetch\(/);
  assert.match(pkg.scripts.check, /scripts\/verify-signature\.js/);
});

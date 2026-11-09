'use strict';
/**
 * scripts/build-config.js — конфигурация electron-builder на время сборки.
 *
 * Зачем не хранить её в `package.json`: наличие `win.azureSignOptions`
 * **включает** подпись (так устроен electron-builder: он смотрит на сам блок,
 * а не на флаг). Если блок лежит в репозитории, то сборка без секретов
 * попытается подписать пустыми значениями и упадёт — отсутствие сертификата
 * сломало бы выпуск приложения.
 *
 * Поэтому конфигурация собирается из `package.json` и добавляет подпись
 * только тогда, когда в окружении есть **все** значения Azure Trusted
 * Signing. Файл `.generated` не версионируется: в нём нет секретов, но и
 * смысла хранить копию описания сборки нет.
 *
 * Запуск:
 *   node scripts/build-config.js           # собрать файл, напечатать путь
 *   node scripts/build-config.js --check   # только проверить окружение
 *
 * Ключи `azureSignOptions` — ровно те, что читает electron-builder 25
 * (`out/codeSign/windowsSignAzureManager.js`): `endpoint`,
 * `certificateProfileName`, `codeSigningAccountName`. Остальные поля он
 * передаёт в `Invoke-TrustedSigning` как есть.
 */

const fs = require('node:fs');
const path = require('node:path');

const DESKTOP = path.resolve(__dirname, '..');
const OUTPUT = path.join(DESKTOP, 'build-config.generated.json');

/** Какие переменные окружения нужны для Azure Trusted Signing. */
const SIGNING_ENV = [
  'AZURE_CODE_SIGNING_ENDPOINT',
  'AZURE_CODE_SIGNING_ACCOUNT_NAME',
  'AZURE_CERTIFICATE_PROFILE_NAME',
  'AZURE_CLIENT_ID',
  'AZURE_TENANT_ID',
  'AZURE_CLIENT_SECRET',
];

/**
 * Готово ли окружение к подписи.
 *
 * @param {object} [env]
 * @returns {{ready: boolean, missing: string[]}}
 */
function signingStatus(env = process.env) {
  const missing = SIGNING_ENV.filter((name) => !String(env[name] || '').trim());
  return { ready: missing.length === 0, missing };
}

/**
 * Собрать конфигурацию electron-builder.
 *
 * @param {object} params
 * @param {object} params.pkg   содержимое `desktop/package.json`
 * @param {object} [params.env]
 * @returns {{config: object, signing: boolean, missing: string[]}}
 */
function buildConfig({ pkg, env = process.env }) {
  const config = JSON.parse(JSON.stringify(pkg.build || {}));
  const status = signingStatus(env);
  if (!status.ready) {
    // Подписи нет — и блока нет: electron-builder не должен пытаться.
    if (config.win) delete config.win.azureSignOptions;
    return { config, signing: false, missing: status.missing };
  }
  config.win = config.win || {};
  config.win.azureSignOptions = {
    endpoint: env.AZURE_CODE_SIGNING_ENDPOINT,
    codeSigningAccountName: env.AZURE_CODE_SIGNING_ACCOUNT_NAME,
    certificateProfileName: env.AZURE_CERTIFICATE_PROFILE_NAME,
    // Необязательные аргументы передаются в Invoke-TrustedSigning дословно.
    FileDigest: 'SHA256',
  };
  return { config, signing: true, missing: [] };
}

/**
 * Записать собранную конфигурацию.
 *
 * @param {object} params
 * @returns {{path: string, signing: boolean, missing: string[]}}
 */
function writeConfig({ pkg, env = process.env, output = OUTPUT }) {
  const { config, signing, missing } = buildConfig({ pkg, env });
  // `directories.output` и прочие пути относительны каталога проекта
  // (desktop/), поэтому файл кладём именно туда.
  fs.writeFileSync(output, `${JSON.stringify(config, null, 2)}\n`);
  return { path: output, signing, missing };
}

function main(argv) {
  const pkg = JSON.parse(fs.readFileSync(path.join(DESKTOP, 'package.json'), 'utf8'));
  if (argv.includes('--check')) {
    const status = signingStatus();
    process.stdout.write(status.ready
      ? 'секреты подписи на месте: сборка будет подписана\n'
      : `секретов подписи нет (${status.missing.join(', ')}): сборка выйдет без подписи\n`);
    return 0;
  }
  const result = writeConfig({ pkg });
  process.stdout.write(`${result.path}\n`);
  process.stdout.write(result.signing
    ? 'подпись Azure Trusted Signing включена\n'
    : `подпись выключена: нет ${result.missing.join(', ')}\n`);
  return 0;
}

if (require.main === module) {
  process.exitCode = main(process.argv.slice(2));
}

module.exports = {
  SIGNING_ENV, signingStatus, buildConfig, writeConfig, main, OUTPUT,
};

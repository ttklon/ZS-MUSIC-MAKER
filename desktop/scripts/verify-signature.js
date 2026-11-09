'use strict';
/**
 * scripts/verify-signature.js — подписан ли EXE на самом деле.
 *
 * Зачем отдельным скриптом: «мы подписываем» и «файл подписан» — разные
 * утверждения. Проверка спрашивает у Windows (`Get-AuthenticodeSignature`),
 * а не у переменных окружения, поэтому её результат можно ставить в отчёт,
 * в релиз и в PR.
 *
 * Запуск:
 *   node scripts/verify-signature.js dist/ZS-Music-Maker-Setup-1.0.0.exe
 *   node scripts/verify-signature.js dist/*.exe --json
 *
 * Коды возврата:
 *   0 — подпись действительна (Status = Valid) у всех файлов;
 *   1 — файл не подписан или подпись недействительна;
 *   2 — проверить нечем (не Windows) — это не «подписано» и не «сломано».
 *
 * Скрипт ничего не подписывает: подпись требует сертификата, которого в
 * репозитории нет и быть не может.
 */

const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

/**
 * Разобрать вывод `Get-AuthenticodeSignature | ConvertTo-Json`.
 *
 * Вынесено отдельно, чтобы проверялось тестом: PowerShell в CI — не то
 * место, где удобно отлаживать парсинг.
 *
 * @param {string} raw
 * @returns {{status: string, signed: boolean, signer: string|null,
 *            timestamped: boolean, message: string|null}}
 */
function parseSignature(raw) {
  let data = null;
  try {
    data = JSON.parse(String(raw || '').trim() || 'null');
  } catch {
    return {
      status: 'Unparsed', signed: false, signer: null, timestamped: false,
      message: 'вывод PowerShell не разобран',
    };
  }
  if (!data || typeof data !== 'object') {
    return {
      status: 'Unparsed', signed: false, signer: null, timestamped: false,
      message: 'PowerShell вернул пустоту',
    };
  }
  // Один файл PowerShell отдаёт объектом, несколько — массивом.
  const item = Array.isArray(data) ? data[0] : data;
  if (!item || typeof item !== 'object') {
    return {
      status: 'Unparsed', signed: false, signer: null, timestamped: false,
      message: 'PowerShell не вернул подпись',
    };
  }
  const status = String(item.Status || 'Unknown');
  const signer = item.SignerCertificate && (item.SignerCertificate.Subject || null);
  return {
    status,
    signed: status === 'Valid',
    signer: signer || null,
    timestamped: Boolean(item.TimeStamperCertificate),
    message: item.StatusMessage ? String(item.StatusMessage) : null,
  };
}

/**
 * Спросить у Windows подпись файла.
 *
 * @param {string} file
 * @returns {{file: string, applicable: boolean, status: string, signed: boolean,
 *            signer: string|null, timestamped: boolean, message: string|null}}
 */
function verifyFile(file) {
  const target = path.resolve(file);
  if (!fs.existsSync(target)) {
    return {
      file: target, applicable: true, status: 'Missing', signed: false,
      signer: null, timestamped: false, message: 'файла нет',
    };
  }
  if (process.platform !== 'win32') {
    return {
      file: target,
      applicable: false,
      status: 'Unavailable',
      signed: false,
      signer: null,
      timestamped: false,
      message: 'проверка подписи Authenticode возможна только на Windows',
    };
  }
  const script = [
    '-NoProfile',
    '-NonInteractive',
    '-Command',
    `Get-AuthenticodeSignature -LiteralPath '${target.replace(/'/g, "''")}' | ConvertTo-Json -Depth 4`,
  ];
  let raw = '';
  try {
    raw = execFileSync('powershell.exe', script, { encoding: 'utf8', timeout: 60_000 });
  } catch (err) {
    return {
      file: target, applicable: true, status: 'Error', signed: false, signer: null,
      timestamped: false, message: `PowerShell: ${(err && err.message) || 'ошибка'}`,
    };
  }
  return { file: target, applicable: true, ...parseSignature(raw) };
}

/**
 * Свести результаты в один отчёт.
 *
 * `signed` здесь означает «все файлы подписаны и подпись действительна»,
 * а `applicable: false` — «проверить не смогли», не «подписано».
 *
 * @param {Array<object>} results
 * @returns {{signed: boolean, applicable: boolean, files: Array<object>, summary: string}}
 */
function summarize(results) {
  const applicable = results.some((row) => row.applicable);
  const signed = results.length > 0 && results.every((row) => row.signed);
  let summary;
  if (!applicable) summary = 'проверка подписи недоступна вне Windows';
  else if (signed) summary = 'подписано: подпись действительна';
  else summary = `не подписано: ${results.filter((row) => !row.signed).map((row) => path.basename(row.file)).join(', ')}`;
  return { signed, applicable, files: results, summary };
}

function main(argv) {
  const args = argv.slice(2);
  const json = args.includes('--json');
  const files = args.filter((arg) => !arg.startsWith('--'));
  if (!files.length) {
    process.stderr.write('укажите файл: node scripts/verify-signature.js <путь к .exe> [--json]\n');
    return 2;
  }
  const report = summarize(files.map((file) => verifyFile(file)));
  if (json) {
    process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  } else {
    for (const row of report.files) {
      const state = row.signed ? 'подписан' : row.applicable ? 'НЕ подписан' : 'не проверить';
      process.stdout.write(`${path.basename(row.file)}: ${state} (${row.status}${row.message ? `, ${row.message}` : ''})\n`);
      if (row.signer) process.stdout.write(`  подписал: ${row.signer}\n`);
    }
    process.stdout.write(`${report.summary}\n`);
  }
  if (!report.applicable) return 2;
  return report.signed ? 0 : 1;
}

if (require.main === module) {
  process.exitCode = main(process.argv);
}

module.exports = { parseSignature, verifyFile, summarize, main };

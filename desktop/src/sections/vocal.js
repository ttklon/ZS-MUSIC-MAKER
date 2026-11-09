'use strict';
/**
 * sections/vocal.js — блок вокала раздела «Бит»: режим, файл, запись, подписи.
 *
 * Вынесено из `beat.js` по той же причине, что и остальные разделы: файл не
 * должен разрастаться на несколько тем. Здесь только выбор источника дубля и
 * запись с микрофона; сам рендер и отчёт остаются в `beat.js`.
 *
 * Честность: подпись под блоком всегда называет источник, а «тестовый дубль»
 * ни при каких настройках не превращается в «запись с микрофона».
 */

const W = window.ZSMM_UI;
const { $, showError, state } = W;

/** Запись с микрофона: `sections/recorder.js` кладёт API в этот объект. */
const recorder = window.ZSMM_RECORDER;

// ---------------------------------------------------------------- вокал
// Режим задаёт пользователь, но подпись всегда называет источник честно:
// «тестовый дубль» не превращается в «запись с микрофона» ни при каких
// настройках.
let vocalFile = null;
/** Последняя запись с микрофона: `{wavBase64, seconds, sampleRate}`. */
let recordedTake = null;
/** Текущая сессия записи (`null`, когда не пишем). */
let recording = null;

function vocalOptions() {
  const mode = ($('vocal-mode') && $('vocal-mode').value) || 'none';
  if (mode === 'none') return { mode: 'none' };
  const text = ($('vocal-text') && $('vocal-text').value || '').trim();
  const gainRaw = Number(($('vocal-gain') && $('vocal-gain').value) || 0.5);
  const gain = Number.isFinite(gainRaw) ? Math.min(1, Math.max(0, gainRaw)) : 0.5;
  if (mode === 'file') {
    if (!vocalFile) throw new Error('сначала выберите WAV-файл с вокалом');
    return { mode, text, gain, file: vocalFile };
  }
  if (mode === 'record') {
    // Записанный дубль уезжает в главный процесс теми же байтами WAV: окно
    // не притворяется файлом на диске и не пишет во временный каталог.
    if (!recordedTake) throw new Error('сначала запишите дубль кнопкой «Записать дубль»');
    return {
      mode, text, gain, pcmBase64: recordedTake.pcmBase64,
      sampleRate: recordedTake.sampleRate, seconds: recordedTake.seconds,
    };
  }
  return { mode, text, gain };
}

const VOCAL_NOTES = {
  none: 'Вокал выключен: трек будет без голоса.',
  synth: 'Голос синтезируется формантным движком в окне — это не запись человека.',
  test: 'Тестовый дубль: имитация входа для проверки цепочки. Не микрофон и не запись.',
  file: 'Вокал берётся из выбранного WAV-файла.',
  record: 'Дубль записывается с микрофона в окне. Разрешение спрашивает Windows 11, '
    + 'звук остаётся в памяти приложения и никуда не отправляется.',
};

/**
 * Настроить блок вокала: режим, файл, запись с микрофона.
 *
 * Вызывается из `beat.js` один раз при открытии раздела — там же, где
 * настраиваются остальные кнопки.
 */
async function wireVocal() {
  const vocalMode = $('vocal-mode');
  if (!vocalMode) return;
  vocalMode.addEventListener('change', updateVocalNote);
  updateVocalNote();

  // Что известно про вход записи, говорит главный процесс: если захвата
  // нет, окно так и пишет, а не изображает микрофон.
  if (typeof window.zsmm.vocalInput === 'function') {
    try {
      const input = await window.zsmm.vocalInput();
      if (input && input.ok === true && input.data && !input.data.recording) {
        $('vocal-note').textContent += ` Микрофон: ${input.data.reason}.`;
      }
    } catch (err) {
      showError(`Вход записи: ${err.message}`);
    }
  }

  $('vocal-pick').addEventListener('click', async () => {
    if (typeof window.zsmm.pickVocalFile !== 'function') {
      showError('Выбор файла доступен только в приложении');
      return;
    }
    const reply = await window.zsmm.pickVocalFile();
    if (!reply || reply.ok !== true) {
      showError(`Файл не выбран: ${(reply && reply.error) || 'нет ответа'}`);
      return;
    }
    vocalFile = (reply.data && reply.data.path) || null;
    if (vocalFile) vocalMode.value = 'file';
    updateVocalNote();
  });

  const recordButton = $('vocal-record');
  const stopButton = $('vocal-stop');
  if (!recorder) {
    // Модуль записи не подключён — честно говорим это, а не прячем кнопки.
    if ($('vocal-record-status')) $('vocal-record-status').textContent = 'запись недоступна';
    if (recordButton) recordButton.disabled = true;
    return;
  }
  if (recordButton) recordButton.addEventListener('click', startVocalRecording);
  if (stopButton) stopButton.addEventListener('click', stopVocalRecording);
}

/** Начать запись: разрешение и устройства — у окна, а не у главного процесса. */
async function startVocalRecording() {
  const status = $('vocal-record-status');
  if (!recorder) {
    showError('Запись недоступна: модуль захвата не загружен');
    return;
  }
  if (recording) {
    showError('Запись уже идёт');
    return;
  }
  try {
    const session = await recorder.start({
      mediaDevices: navigator.mediaDevices,
      AudioContext: window.AudioContext || window.webkitAudioContext,
      seconds: 60,
      onTick: (left) => {
        if (status) status.textContent = left > 0 ? `идёт запись: осталось ${left} с` : 'запись завершается';
      },
    });
    recording = session;
    if (status) status.textContent = 'идёт запись: нажмите «Остановить запись»';
    updateVocalNote();
  } catch (err) {
    if (status) status.textContent = '';
    showError(`Микрофон: ${err.message}`);
  }
}

/** Остановить запись и оставить дубль в памяти окна. */
async function stopVocalRecording() {
  const status = $('vocal-record-status');
  if (!recording) return;
  const session = recording;
  recording = null;
  try {
    const take = await session.stop();
    if (!take) {
      if (status) status.textContent = '';
      updateVocalNote();
      return;
    }
    // Кодировать WAV будет главный процесс: в изолированной странице нет
    // ни `Buffer`, ни доступа к файлам движка.
    const payload = recorder.toPayload(take);
    recordedTake = {
      pcmBase64: payload.pcmBase64,
      sampleRate: payload.sampleRate,
      seconds: payload.seconds,
    };
    if (status) {
      status.textContent = `записано ${take.durationSec.toFixed(1)} с`;
    }
  } catch (err) {
    showError(`Запись не сохранена: ${err.message}`);
  }
  updateVocalNote();
}

/** Дубль записи для отчёта: источник назван, а не подразумевается. */
function describeRecording() {
  return recordedTake ? `запись с микрофона, ${recordedTake.seconds.toFixed(1)} с` : null;
}

function updateVocalNote() {
  const mode = ($('vocal-mode') && $('vocal-mode').value) || 'none';
  const note = $('vocal-note');
  if (!note) return;
  const pick = $('vocal-pick');
  if (pick) pick.disabled = mode !== 'file';
  const recordBtn = $('vocal-record');
  const stopBtn = $('vocal-stop');
  // Запись нужна модулю захвата: без него кнопка остаётся заблокированной, а
  // причина написана рядом, а не выясняется нажатием.
  if (recordBtn) recordBtn.disabled = mode !== 'record' || !recorder || Boolean(recording);
  if (stopBtn) stopBtn.disabled = !recording;
  const textField = $('vocal-text');
  if (textField) textField.disabled = mode === 'none' || mode === 'file';
  const gainField = $('vocal-gain');
  if (gainField) gainField.disabled = mode === 'none';
  if (mode === 'file' && vocalFile) {
    note.textContent = `${VOCAL_NOTES.file} Файл: ${vocalFile}`;
    return;
  }
  if (mode === 'record' && recordedTake) {
    note.textContent = `${VOCAL_NOTES.record} Записано ${recordedTake.seconds.toFixed(1)} с — `
      + 'этот дубль уйдёт в трек.';
    return;
  }
  note.textContent = VOCAL_NOTES[mode] || VOCAL_NOTES.none;
}

/** Одна строка про вокал: источник и что именно с ним сделали. */

W.vocalOptions = vocalOptions;
W.wireVocal = wireVocal;
W.describeRecording = describeRecording;

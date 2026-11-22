'use strict';
/** Canonical product specification; not a runtime capability probe. */
(function () {
  const contract = {
    "schema": 1,
    "id": "zsmm-windows-studio",
    "name": "ZS Music Maker",
    "channel": "development",
    "platform": "Windows 11 x64",
    "entry": "Electron → Создание трека",
    "installer": "ZS-Music-Maker-Setup-<version>.exe",
    "versionSource": "version.json",
    "state": "Полная сквозная готовность не подтверждена.",
    "delivery": "Установщик содержит код Python-пайплайна. Релизная сборка включает встроенный Python; тяжёлые движки и веса готовятся отдельно с разрешением сети.",
    "network": "Загрузки требуют явного согласия. Для всех backend офлайн-готовность ещё не подтверждена.",
    "hardware": "Поддержка CPU/GPU и минимальные ресурсы требуют измерений. Наличие Windows runner не подтверждает CUDA, AMD и физический микрофон.",
    "scenarios": [
      {"id":"instrumental","name":"Инструментал","required":true,"accepted":false,"result":"Музыка без вокала; реальный WAV, плеер и экспорт.","blocker":"Сквозная нейрогенерация из установленного приложения не принята."},
      {"id":"own-vocal","name":"Песня со своей записью","required":true,"accepted":false,"result":"Инструментал и собственная спетая запись в согласованном миксе.","blocker":"Передача рецепта и голоса в основной рендер требует исправления и проверки."},
      {"id":"singing","name":"Автоматически спетая песня","required":true,"accepted":false,"result":"Backend исполняет текст и мелодию; речь TTS не считается пением.","blocker":"Проверенный singing backend ещё не принят."},
      {"id":"revision","name":"Правка и восстановление проекта","required":true,"accepted":false,"result":"Изменение части, сохранение истории, открытие после перезапуска.","blocker":"Полный пользовательский сценарий ещё не принят."}
    ],
    "notEquivalent": ["Скачанный файл ≠ рабочая модель", "Открытое окно ≠ работающая генерация", "Речь Silero/XTTS ≠ пение", "RVC меняет тембр, но не создаёт пение из ничего", "Hit-score ≠ качество песни или коммерческий успех"],
    "legacy": "PySide, web UI и CLI — дополнительные/legacy входы. Их наличие не подтверждает основной сценарий Electron.",
    "recovery": "При сбое не удаляйте проекты и веса. Сохраните ошибки кнопкой в верхней панели; проверьте журнал в «Модели и загрузки». Не запускайте случайные команды pip.",
    "releaseGate": "Чистая установка, подготовка, настоящая музыка и пение, правка, экспорт, восстановление и прослушивание; без открытых P0/P1 согласованного объёма."
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = contract;
  if (typeof window !== 'undefined') window.ZSMM_PRODUCT = contract;
})();

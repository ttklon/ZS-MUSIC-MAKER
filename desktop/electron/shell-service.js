'use strict';
/**
 * shell-service.js — «О системе»-каналы: корень проекта, ссылки, настройки,
 * отчёт об окружении.
 *
 * Почему отдельным модулем: `registerIpc` в `main.js` должен оставаться
 * списком вызовов («задачи — сюда, бит — туда»), а правило проекта ограничивает
 * файл окна 400 строками (тест `ui-contract`). Здесь же собраны обработчики,
 * которые не зависят от Electron напрямую: всё приходит аргументами, поэтому
 * их можно проверить обычным `node --test`.
 *
 * Ничего не решает сам: пути считает `runtime.js`, политику ссылок —
 * `window-policy.js`, настройки — `settings.js`.
 */

/**
 * @param {object} params
 * @param {object} params.ipcMain               электронный ipcMain (или двойник)
 * @param {string|null} params.root             корень проекта
 * @param {object} params.rootInfo              `{root, candidates, error}` из runtime
 * @param {object} params.shell                 `{openPath, openExternal}`
 * @param {object} params.policy                `window-policy` (externalUrl)
 * @param {Function} params.settings            фабрика хранилища настроек
 * @param {Function} params.safeMusicDir        каталог «Музыка» или запасной
 * @param {Function} params.dossierPlan         `{dir, source}` — где живёт досье
 * @param {Function} params.resolvePython       поиск интерпретатора
 * @param {Function} params.resolvePipelineRoot поиск пайплайна
 * @param {object} [params.versions]            версии Electron/Node/Chrome
 * @returns {{handlers: string[]}}
 */
function registerShellIpc({
  ipcMain, root, rootInfo, shell, policy, settings, safeMusicDir,
  dossierPlan, resolvePython, resolvePipelineRoot, versions = {},
}) {
  ipcMain.handle('zsmm:reveal-root', async () => {
    if (!root) return { ok: false, error: rootInfo.error };
    const error = await shell.openPath(root);
    return { ok: error === '', error: error || null, root };
  });

  ipcMain.handle('zsmm:open-external', async (_event, url) => {
    const allowed = policy.externalUrl(url);
    if (!allowed) return { ok: false, error: 'разрешены только http(s)-ссылки' };
    await shell.openExternal(allowed);
    return { ok: true };
  });

  ipcMain.handle('zsmm:settings-load', () => {
    const { value, error, errors } = settings().load();
    return { ok: true, data: { ...value, error, invalid: errors } };
  });

  ipcMain.handle('zsmm:settings-save', (_event, patch) => {
    const { value, error } = settings().save(patch);
    return { ok: error === null, data: value, error };
  });

  // Всё, что отличает «работает в репозитории» от «работает на Windows после
  // установки»: пути, наличие Python, каталог настроек.
  ipcMain.handle('zsmm:environment', () => ({
    ok: true,
    data: environmentReport({
      root, rootInfo, safeMusicDir, dossierPlan, resolvePython, resolvePipelineRoot, versions,
    }),
  }));

  return {
    handlers: [
      'zsmm:reveal-root', 'zsmm:open-external',
      'zsmm:settings-load', 'zsmm:settings-save', 'zsmm:environment',
    ],
  };
}

/** Отчёт об окружении: то, что окно показывает в «Диагностике». */
function environmentReport({
  root, rootInfo, safeMusicDir, dossierPlan, resolvePython, resolvePipelineRoot, versions,
  getUserData = () => null,
  isPackaged = false,
  platform = process.platform,
  arch = process.arch,
}) {
  const python = resolvePython({ root, env: process.env });
  const pipeline = resolvePipelineRoot({ root });
  const dossier = dossierPlan();
  return {
    packaged: isPackaged,
    root,
    rootCandidates: rootInfo.candidates,
    rootError: rootInfo.error,
    user_data: getUserData(),
    music_dir: safeMusicDir(),
    // Где приложение ведёт досье и почему: в установленной сборке
    // `resources/project` только для чтения.
    dossier_dir: dossier.dir,
    dossier_source: dossier.source === 'user'
      ? 'каталог пользователя: каталог установки только для чтения'
      : 'каталог проекта: приложение запущено из репозитория',
    python: python.python,
    python_error: python.error,
    // Пайплайн — отдельная вещь от интерпретатора: «Python есть» не значит
    // «задачи раздела „Запуск“ заработают».
    pipeline_root: pipeline.root,
    model_storage: require('./model-storage').modelStorage({ root, pipelineRoot: pipeline.root, userData: getUserData() }),
    pipeline_error: pipeline.error,
    platform,
    arch,
    electron: versions.electron || null,
    node: versions.node,
    chrome: versions.chrome || null,
    worker_render: true,
  };
}

module.exports = { registerShellIpc, environmentReport };

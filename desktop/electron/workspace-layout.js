'use strict';
/** Mutable runtime directories live under workspace, not install/cwd. */
const path = require('node:path');
const fs = require('node:fs/promises');
function layout(root) {
  const base = path.resolve(root);
  return { workspace: base, projects: path.join(base, 'output'), models: path.join(base, 'models'),
    cache: path.join(base, 'cache'), temp: path.join(base, 'temp'), logs: path.join(base, 'logs') };
}
async function runtimeEnvironment(root) {
  const dirs = layout(root);
  for (const dir of Object.values(dirs)) {
    // Existing links are not trusted runtime destinations.
    await require('./pipeline-workspace').assertNoLinks(dir);
    await fs.mkdir(dir, { recursive: true });
    const probe = path.join(dir, '.write-probe-' + require('node:crypto').randomUUID());
    await fs.writeFile(probe, '', { flag: 'wx' }); await fs.unlink(probe);
  }
  return { ZSMM_WORKSPACE: dirs.workspace, ZSMM_LOG_DIR: dirs.logs,
    HF_HOME: path.join(dirs.cache, 'huggingface'), TORCH_HOME: path.join(dirs.cache, 'torch'),
    TMP: dirs.temp, TEMP: dirs.temp, TMPDIR: dirs.temp };
}
module.exports = { layout, runtimeEnvironment };

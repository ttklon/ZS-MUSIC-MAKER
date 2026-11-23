'use strict';
/** Bounded, read-only inventory. A file on disk is NOT proof of a working model. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

function scanDirectory(directory, limit = 250) {
  const files = [];
  const errors = [];
  let visited = 0;
  let truncated = false;
  function walk(dir, depth) {
    if (depth > 6 || visited >= limit) { truncated = true; return; }
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
    catch (error) { if (error.code !== 'ENOENT') errors.push(error.message); return; }
    for (const entry of entries) {
      if (++visited > limit) { truncated = true; break; }
      if (entry.isSymbolicLink()) continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full, depth + 1);
      else if (entry.isFile() && /\.(pt|pth|bin|safetensors|onnx|ckpt|gguf|part|incomplete)$/i.test(entry.name)) {
        try { const stat = fs.statSync(full); files.push({ path: full, bytes: stat.size }); }
        catch (error) { errors.push(error.message); }
      }
    }
  }
  walk(directory, 0);
  return { directory, files, errors, truncated };
}

function modelCatalog(root) {
  try {
    const data = JSON.parse(fs.readFileSync(path.join(root, 'data', 'desktop', 'model-catalog.json'), 'utf8'));
    if (data.schema !== 1 || !Array.isArray(data.roles)) throw new Error('Unsupported catalogue');
    return { ...data, available: true };
  } catch (error) { return { available: false, roles: [], error: error.message }; }
}
function modelStorage({ root, pipelineRoot, userData, home = os.homedir(), env = process.env }) {
  const hfHome = env.HF_HOME || path.join(home, '.cache', 'huggingface');
  const torchHome = env.TORCH_HOME || path.join(env.XDG_CACHE_HOME || path.join(home, '.cache'), 'torch');
  const locations = [root && path.join(root, 'models'), pipelineRoot && path.join(pipelineRoot, 'models'),
    userData && path.join(userData, 'workspace', 'models'),
    pipelineRoot && path.join(pipelineRoot, 'data', 'ai_models'),
    userData && path.join(userData, 'workspace', 'data', 'ai_models'),
    userData && path.join(userData, 'workspace', 'cache', 'huggingface'),
    userData && path.join(userData, 'workspace', 'cache', 'torch'),
    env.HF_HUB_CACHE || env.HUGGINGFACE_HUB_CACHE || path.join(hfHome, 'hub'), torchHome];
  return [...new Set(locations.filter(Boolean))].map(dir => scanDirectory(dir));
}
module.exports = { modelStorage, scanDirectory, modelCatalog };

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
      else if (entry.isFile() && /\.(pt|pth|bin|safetensors|onnx|ckpt|part|incomplete)$/i.test(entry.name)) {
        try { const stat = fs.statSync(full); files.push({ path: full, bytes: stat.size }); }
        catch (error) { errors.push(error.message); }
      }
    }
  }
  walk(directory, 0);
  return { directory, files, errors, truncated };
}

function modelStorage({ root, pipelineRoot, userData, home = os.homedir(), env = process.env }) {
  const hfHome = env.HF_HOME || path.join(home, '.cache', 'huggingface');
  const torchHome = env.TORCH_HOME || path.join(env.XDG_CACHE_HOME || path.join(home, '.cache'), 'torch');
  const locations = [root && path.join(root, 'models'), pipelineRoot && path.join(pipelineRoot, 'models'),
    userData && path.join(userData, 'workspace', 'models'),
    env.HF_HUB_CACHE || env.HUGGINGFACE_HUB_CACHE || path.join(hfHome, 'hub'), torchHome];
  return [...new Set(locations.filter(Boolean))].map(dir => scanDirectory(dir));
}
module.exports = { modelStorage, scanDirectory };

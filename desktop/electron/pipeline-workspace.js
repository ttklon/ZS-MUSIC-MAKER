'use strict';
/** Keep shipped code read-only and mutable Python state in the user's workspace.
 * Only a fixed list of shipped trees is copied. Models/output/.python are never
 * copied, removed, or replaced. Code updates overwrite code; defaults only seed.
 */
const fs = require('node:fs/promises');
const path = require('node:path');
const { constants } = require('node:fs');
const CODE_TREES = ['app', 'modules', 'agents', 'tools', 'config'];
const SEED_TREES = ['data', 'scripts'];

async function safeDirectory(dir) {
  await fs.mkdir(dir, { recursive: true });
  if ((await fs.lstat(dir)).isSymbolicLink()) throw new Error('Workspace directory cannot be a symbolic link: ' + dir);
}
async function copyTree(source, target, seed, onlyPython = false) {
  let entries;
  try { entries = await fs.readdir(source, { withFileTypes: true }); }
  catch (err) { if (err.code === 'ENOENT') return; throw err; }
  await safeDirectory(target);
  for (const entry of entries) {
    if (entry.name === '__pycache__' || entry.name.startsWith('.')) continue;
    const from = path.join(source, entry.name), to = path.join(target, entry.name);
    if (entry.isSymbolicLink()) throw new Error('Unexpected symbolic link in shipped project');
    if (entry.isDirectory()) await copyTree(from, to, seed, onlyPython);
    else if (entry.isFile() && (!onlyPython || entry.name.endsWith('.py'))) await copyFile(from, to, seed);
  }
}
async function copyFile(from, to, seed) {
  try { if ((await fs.lstat(to)).isSymbolicLink()) throw new Error('Workspace file cannot be a symbolic link: ' + to); }
  catch (err) { if (err.code !== 'ENOENT') throw err; }
  try { await fs.copyFile(from, to, seed ? constants.COPYFILE_EXCL : 0); }
  catch (err) { if (!(seed && err.code === 'EEXIST')) throw err; }
}
async function prepareWorkspace(source, target) {
  source = path.resolve(source); target = path.resolve(target);
  const rel = path.relative(source, target);
  if (!rel || (!rel.startsWith('..' + path.sep) && rel !== '..' && !path.isAbsolute(rel))) {
    throw new Error('Workspace must be outside the shipped project');
  }
  await safeDirectory(target);
  for (const name of CODE_TREES) await copyTree(path.join(source, name), path.join(target, name), false, true);
  // config JSON defaults do not overwrite user choices.
  await copyTree(path.join(source, 'config'), path.join(target, 'config'), true);
  for (const name of SEED_TREES) await copyTree(path.join(source, name), path.join(target, name), true);
  for (const name of ['main.py', 'version.json', 'VERSION', 'requirements.txt', 'requirements_ai.txt']) {
    const from = path.join(source, name);
    try { await fs.access(from); } catch (err) { if (err.code === 'ENOENT') continue; throw err; }
    await copyFile(from, path.join(target, name), false);
  }
  if (!(await fs.stat(path.join(target, 'main.py'))).isFile()) throw new Error('Workspace has no main.py');
  return target;
}
module.exports = { prepareWorkspace };

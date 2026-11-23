'use strict';
/**
 * Opt-in installed-NSIS UI → IPC → shared task runner → bundled Python probe.
 * Synthetic hardware scenarios are injected only into child processes through
 * a temporary sitecustomize; the retry uses the real measured inventory.
 */
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { fileURLToPath } = require('node:url');

const { INJECTOR, prepareCreationUi, runAgentFromInstalledUi } = require('./agent-preflight-ui');

function sha256File(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function samePath(left, right) {
  return typeof left === 'string' && path.resolve(left) === path.resolve(right);
}

function isWithinPath(candidate, root) {
  if (typeof candidate !== 'string' || typeof root !== 'string' || !candidate || !root) return false;
  const relative = path.relative(path.resolve(root), path.resolve(candidate));
  return relative === '' || (relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative));
}

function snapshotFiles(root) {
  const result = {};
  function visit(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      const rel = path.relative(root, full).split(path.sep).join('/');
      if (entry.isSymbolicLink()) throw new Error(`Unexpected link in acceptance workspace: ${rel}`);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile()) result[rel] = sha256File(full);
    }
  }
  visit(root);
  return result;
}

function preservesSnapshot(before, after) {
  return Object.entries(before).every(([name, hash]) => after[name] === hash);
}

function unchangedSnapshot(before, after) {
  return Object.keys(before).length === Object.keys(after).length && preservesSnapshot(before, after);
}

function refusalOutcome(run, expectedReason) {
  const report = run?.done?.report;
  const preflight = report?.hardware_preflight;
  const reasons = Array.isArray(preflight?.reasons) ? preflight.reasons.map(String) : [];
  const noHeavyStages = !run.events.some((event) =>
    /Жанр выбран сам|HitFactory:/.test(JSON.stringify(event)));
  return {
    ok: run?.done?.ok === false && report?.result?.succeeded === false
      && preflight?.status === 'blocked' && preflight?.decision === 'refuse'
      && preflight?.can_attempt === false && preflight?.inference_verified === false
      && preflight?.product_profile_accepted === false
      && reasons.some((reason) => reason.toLowerCase().includes(expectedReason.toLowerCase()))
      && noHeavyStages,
    taskDone: Boolean(run?.done),
    taskOk: run?.done?.ok === true,
    resultStatus: report?.result?.status || null,
    selectedBackend: preflight?.selected_backend || null,
    reasons,
    noHeavyStages,
  };
}


async function runDenialCase({ window, scenario, name, expectedReason, voicePath, hits, before, sentinel }) {
  process.env.ZSMM_AGENT_TEST_SCENARIO = scenario;
  const run = await runAgentFromInstalledUi(window, voicePath || '');
  const result = refusalOutcome(run, expectedReason);
  result.scenario = name;
  result.runError = run?.error || null;
  result.startCommand = run?.startCommand || null;
  result.installedUiRecipePath = Array.isArray(run?.startCommand)
    && run.startCommand[0] === 'main.py' && run.startCommand.includes('--agent-hit')
    && run.startCommand.includes('--agent-mood');
  result.voiceArgumentForwarded = !voicePath || (Array.isArray(run?.startCommand)
    && run.startCommand.includes('--agent-voice') && run.startCommand.includes(voicePath));
  result.taskError = run?.done?.error || null;
  result.protocolError = run?.done?.protocolError || null;
  result.reportKeys = Object.keys(run?.done?.report || {});
  result.reportError = run?.done?.report?.error || null;
  const after = snapshotFiles(hits);
  result.filesUnchanged = unchangedSnapshot(before, after);
  result.sentinelSha256 = sha256File(sentinel);
  result.uiHonest = /Inference не подтверждён; профиль продукта не принят/.test(run.status || '');
  result.uiShowsReason = String(run.status || '').toLowerCase().includes(expectedReason.toLowerCase());
  result.ok = result.ok && result.installedUiRecipePath && result.voiceArgumentForwarded
    && result.filesUnchanged && result.uiHonest && result.uiShowsReason
    && result.sentinelSha256 === before[path.basename(sentinel)];
  result.uiStatus = run.status || null;
  return result;
}

async function checkAgentPreflight(window, app) {
  const report = {
    schema: 1,
    scope: 'installed NSIS UI click → agent IPC → shared task runner → bundled Python',
    sourceSha: process.env.GITHUB_SHA || null,
    platform: process.platform,
    architecture: process.arch,
    acceptanceMet: false,
    limitations: ['Synthetic deny cases verify installed-path enforcement, not physical low-resource hardware.',
      'A test-only bootstrap response unlocks the current creation UI; it installs no engine and does not participate in agent-hit tasks.',
      'Retry uses measured CPU/DSP inventory; inference, product profile, CUDA/AMD support and song quality remain unverified.'],
    checks: {},
  };
  const project = path.resolve(process.resourcesPath, 'project');
  const python = path.join(project, '.python', 'python.exe');
  const workspace = path.join(app.getPath('userData'), 'workspace');
  const hits = path.join(workspace, 'output', 'hits');
  const sentinel = path.join(hits, `agent-preflight-preservation-${process.pid}.txt`);
  const rvcInput = path.join(workspace, `agent-preflight-rvc-input-${process.pid}.wav`);
  const injection = fs.mkdtempSync(path.join(os.tmpdir(), 'zsmm-agent-preflight-'));
  const injector = path.join(injection, 'sitecustomize.py');
  fs.writeFileSync(injector, INJECTOR, 'utf8');
  fs.mkdirSync(hits, { recursive: true });
  if (!fs.existsSync(path.join(project, 'main.py')) || !fs.existsSync(python)) {
    fs.rmSync(injection, { recursive: true, force: true });
    throw new Error('Installed project or bundled Python is missing');
  }
  const sentinelBytes = Buffer.from('existing user result must survive hardware denial and retry\n');
  fs.writeFileSync(sentinel, sentinelBytes, { flag: 'wx' });
  fs.writeFileSync(rvcInput, 'preflight-only placeholder; no RVC inference is executed\n', { flag: 'wx' });
  const before = snapshotFiles(hits);
  const environmentKeys = ['PYTHONPATH', 'ZSMM_AGENT_TEST_SCENARIO', 'ZSMM_ONLINE', 'ZSMM_PROBE_LOCAL_SERVICES'];
  const oldEnvironment = Object.fromEntries(environmentKeys.map((key) => [key, process.env[key]]));
  const pythonPath = injection; // test hook only; never inherit a checkout PYTHONPATH
  let installedRuntime = null;

  try {
    const environmentReply = await window.webContents.executeJavaScript("window.zsmm.environment()");
    const environment = environmentReply?.data || {};
    const rendererUrl = window.webContents.getURL();
    const appPath = app.getAppPath();
    let rendererProtocol = null;
    let rendererPath = null;
    try {
      const parsedUrl = new URL(rendererUrl);
      rendererProtocol = parsedUrl.protocol;
      if (rendererProtocol === 'file:') rendererPath = fileURLToPath(parsedUrl);
    } catch { /* invalid renderer URL is reported as a failed runtime path */ }
    const rendererRelativePath = rendererPath ? path.relative(appPath, rendererPath) : null;
    const rendererInsideApp = rendererRelativePath === '' || (typeof rendererRelativePath === 'string'
      && rendererRelativePath !== '..' && !rendererRelativePath.startsWith(`..${path.sep}`)
      && !path.isAbsolute(rendererRelativePath));
    const noDevServer = environment.packaged === true && rendererProtocol === 'file:' && rendererInsideApp;
    const checkoutRoot = process.env.GITHUB_WORKSPACE || process.env.RUNNER_WORKSPACE || '';
    const checkoutPathEntries = String(process.env.PATH || '').split(path.delimiter)
      .filter((entry) => isWithinPath(entry, checkoutRoot));
    const pythonPathEntries = String(process.env.PYTHONPATH || '').split(path.delimiter).filter(Boolean);
    const pythonPathContainsCheckout = pythonPathEntries.some((entry) => isWithinPath(entry, checkoutRoot));
    const runtimeCheck = {
      ok: environmentReply?.ok === true && environment.packaged === true
        && samePath(environment.root, project) && samePath(environment.pipeline_root, project)
        && samePath(environment.python, python) && noDevServer
        && checkoutPathEntries.length === 0 && !pythonPathContainsCheckout,
      packaged: environment.packaged === true,
      root: environment.root || null,
      pipelineRoot: environment.pipeline_root || null,
      python: environment.python || null,
      expectedProject: project,
      expectedBundledPython: python,
      rendererUrl,
      rendererProtocol,
      rendererPath,
      appPath,
      noDevServer,
      checkoutRoot: checkoutRoot || null,
      checkoutPathEntries,
      pythonPathPresentBeforeInstrumentation: Boolean(process.env.PYTHONPATH),
      pythonPathContainsCheckout,
    };
    report.checks.canonicalRuntimePath = runtimeCheck;
    if (!runtimeCheck.ok) throw new Error('Installed UI runtime did not resolve to resources/project and its bundled Python');
    installedRuntime = { root: runtimeCheck.root, pipelineRoot: runtimeCheck.pipelineRoot, python: runtimeCheck.python };

    const offlineSettings = await window.webContents.executeJavaScript(
      "window.zsmm.saveSettings({ networkOnline: false })",
    );
    if (!offlineSettings?.ok || offlineSettings.data?.networkOnline !== false) {
      throw new Error('Installed settings could not enforce offline agent execution');
    }
    report.networkOnline = offlineSettings.data.networkOnline;
    report.pythonPathInstrumentation = 'temporary test hook only; inherited checkout PYTHONPATH is not used';
    process.env.PYTHONPATH = pythonPath;
    process.env.ZSMM_ONLINE = '0';
    process.env.ZSMM_PROBE_LOCAL_SERVICES = '0';

    // Drive the active creation UI's own prepare button, but stub only the
    // expensive bootstrap result so the installed agent-hit preflight can be
    // reached without downloading engines or models in this acceptance lane.
    process.env.ZSMM_AGENT_TEST_SCENARIO = 'acceptance_setup_ready';
    const setupRun = await prepareCreationUi(window);
    process.env.ZSMM_AGENT_TEST_SCENARIO = '';
    const setupReport = setupRun.done?.report?.setup;
    const syntheticSetupOnly = setupReport?.acceptance_fixture === 'setup gate only; no engine or model is installed'
      && setupReport?.inference_verified === false;
    report.checks.creationPreparationGate = {
      taskDone: Boolean(setupRun.done),
      taskOk: setupRun.done?.ok === true,
      setupReady: setupRun.setupReady === true,
      generationButtonEnabled: setupRun.generationButtonEnabled === true,
      startCommand: setupRun.startCommand,
      uiStatus: setupRun.status || null,
      syntheticSetupOnly,
      realSetupAcceptance: false,
      setupAccepted: false,
      ok: setupRun.done?.ok === true && setupRun.setupReady === true
        && setupRun.generationButtonEnabled === true && syntheticSetupOnly
        && Array.isArray(setupRun.startCommand) && setupRun.startCommand.includes('--bootstrap'),
    };
    if (!report.checks.creationPreparationGate.ok)
      throw new Error('Installed creation UI did not reach generation after test-only bootstrap setup');

    const denialCases = [
      ['unknownRamDenial', 'unknown_ram', 'unknown RAM', 'ram_available_gib'],
      ['insufficientRamDenial', 'insufficient_ram', 'insufficient RAM', 'ram_available_gib'],
      ['unknownDiskDenial', 'unknown_disk', 'unknown free disk', 'disk_free_gib'],
      ['insufficientDiskDenial', 'insufficient_disk', 'insufficient free disk', 'disk_free_gib'],
      ['unknownVramDenial', 'unknown_vram', 'unknown GPU VRAM', 'unknown or invalid', rvcInput],
      ['insufficientVramDenial', 'insufficient_vram', 'insufficient GPU VRAM', 'below the 4 GiB safety floor', rvcInput],
      ['unbudgetedHeavyEngineDenial', 'unbudgeted_musicgen', 'unbudgeted MusicGen', 'budget'],
    ];
    for (const [key, scenario, name, expectedReason, voicePath] of denialCases) {
      report.checks[key] = await runDenialCase({ window, scenario, name, expectedReason,
        voicePath, hits, before, sentinel });
    }
    report.checks.unbudgetedHeavyEngineDenial.expectedBackend = 'musicgen';
    report.checks.unbudgetedHeavyEngineDenial.backendMatches =
      report.checks.unbudgetedHeavyEngineDenial.selectedBackend === 'musicgen';
    report.checks.unbudgetedHeavyEngineDenial.ok = report.checks.unbudgetedHeavyEngineDenial.ok
      && report.checks.unbudgetedHeavyEngineDenial.backendMatches;

    process.env.ZSMM_AGENT_TEST_SCENARIO = '';
    const retryRun = await runAgentFromInstalledUi(window, '');
    const retry = retryRun.done?.report;
    const preflight = retry?.hardware_preflight;
    const terminal = retryRun.done;
    const masterPath = retry?.master_path
      ? (path.isAbsolute(retry.master_path) ? retry.master_path : path.resolve(workspace, retry.master_path))
      : null;
    const retryReport = {
      taskDone: Boolean(terminal),
      taskOk: terminal?.ok === true,
      taskError: terminal?.error || null,
      protocolError: terminal?.protocolError || null,
      runError: retryRun.error || null,
      startCommand: retryRun.startCommand || null,
      installedUiRecipePath: Array.isArray(retryRun.startCommand)
        && retryRun.startCommand[0] === 'main.py' && retryRun.startCommand.includes('--agent-hit')
        && retryRun.startCommand.includes('--agent-mood'),
      reportError: retry?.error || null,
      reportKeys: Object.keys(retry || {}),
      resultStatus: retry?.result?.status || null,
      resultSucceeded: retry?.result?.succeeded === true,
      qualityAccepted: retry?.result?.quality_accepted === true,
      masterPath,
      masterSha256: masterPath && fs.existsSync(masterPath) ? sha256File(masterPath) : null,
      backend: preflight?.selected_backend || null,
      measuredInventory: preflight?.inventory || null,
      preflightStatus: preflight?.status || null,
      preflightDecision: preflight?.decision || null,
      inferenceVerified: preflight?.inference_verified === true,
      productProfileAccepted: preflight?.product_profile_accepted === true,
      previousFilesPreserved: preservesSnapshot(before, snapshotFiles(hits)),
      sentinelSha256: sha256File(sentinel),
      noFalseInferenceSuccess: retry?.result?.succeeded !== true
        || (preflight?.inference_verified === true && preflight?.product_profile_accepted === true),
      taskOutcomeMatchesTypedResult: terminal?.ok === (retry?.result?.succeeded === true),
      uiHonest: /Inference не подтверждён; профиль продукта не принят/.test(retryRun.status || ''),
      pipelineReached: retryRun.events.some((event) => /HitFactory:/.test(JSON.stringify(event))),
      uiStatus: retryRun.status || null,
    };
    retryReport.ok = retryReport.taskDone
      && retryReport.installedUiRecipePath
      && preflight?.inference_verified === false
      && preflight?.product_profile_accepted === false
      && retryReport.previousFilesPreserved
      && retryReport.noFalseInferenceSuccess
      && retryReport.taskOutcomeMatchesTypedResult
      && retryReport.uiHonest
      && retryReport.qualityAccepted === false
      && preflight?.status === 'inventory_only'
      && preflight?.decision === 'continue_unverified'
      && preflight?.selected_backend === 'procedural_dsp'
      && retryReport.pipelineReached;
    report.checks.measuredRetry = retryReport;
    report.installed = {
      ...installedRuntime,
      bundledPython: python,
      pythonSha256: sha256File(python),
      mainSha256: sha256File(path.join(project, 'main.py')),
      executable: app.getPath('exe'),
      executableSha256: sha256File(app.getPath('exe')),
      workspace,
      sentinelSha256: sha256File(sentinel),
    };
    report.ok = Object.values(report.checks).every((check) => check.ok === true)
      && /^[0-9a-f]{40}$/i.test(report.sourceSha || '');
  } catch (error) {
    report.ok = false;
    report.error = `${error.name}: ${error.message}`;
    report.stack = String(error.stack || '').split('\n').slice(0, 8).join('\n');
  } finally {
    for (const key of environmentKeys) {
      if (oldEnvironment[key] === undefined) delete process.env[key];
      else process.env[key] = oldEnvironment[key];
    }
    fs.rmSync(injection, { recursive: true, force: true });
  }
  const runtime = report.checks.canonicalRuntimePath || {};
  const retry = report.checks.measuredRetry || {};
  const denialNames = ['unknownRamDenial', 'insufficientRamDenial', 'unknownDiskDenial',
    'insufficientDiskDenial', 'unknownVramDenial', 'insufficientVramDenial', 'unbudgetedHeavyEngineDenial'];
  const denials = Object.fromEntries(denialNames.map(name => [name, report.checks[name] || { ok: false, notRun: true }]));
  const artifacts = {
    installerSha256: null,
    installedExecutableSha256: report.installed?.executableSha256 || null,
    installedPythonSha256: report.installed?.pythonSha256 || null,
    installedMainSha256: report.installed?.mainSha256 || null,
    retryMasterSha256: retry.masterSha256 || null,
    preservationSentinelSha256: report.installed?.sentinelSha256 || retry.sentinelSha256 || null,
  };
  const environment = {
    platform: report.platform,
    architecture: report.architecture,
    osRelease: os.release(),
    osVersion: os.version(),
    packagedRoot: runtime.root || null,
    bundledPython: runtime.python || null,
    rendererUrl: runtime.rendererUrl || null,
    noDevServer: runtime.noDevServer === true,
    checkoutPathEntries: runtime.checkoutPathEntries || null,
    checkoutPathContainsPython: runtime.pythonPathContainsCheckout ?? null,
    pythonPathInstrumentation: report.pythonPathInstrumentation || null,
    measuredInventory: retry.measuredInventory || null,
  };
  const technicalDecision = report.ok === true
    ? 'technical_pass_pending_independent_owner_acceptance' : 'not_accepted';
  const owner = 'Arena engineering agent (implementation); independent acceptance owner not assigned';
  report.acceptanceRecords = {
    A0003: {
      owner, sourceSha: report.sourceSha, relatedTIds: ['T0025'],
      requirement: 'Installed UI resolves to packaged project and bundled Python without checkout PATH/PYTHONPATH or a development server.',
      scenario: 'Clean NSIS install; run the active creation screen through preparation gate and generation button; observe the agent-hit task start and typed completion.',
      environment,
      positiveResults: { creationPreparationGate: report.checks.creationPreparationGate || null,
        realSetupAcceptance: false,
        setupAcceptanceNote: 'The synthetic bootstrap response only unlocks the current UI; setup/install acceptance is not exercised.',
        measuredRetry: retry },
      negativeResults: { packagedRendererAndPathIsolation: {
        ok: runtime.ok === true && runtime.noDevServer === true && runtime.checkoutPathEntries?.length === 0
          && runtime.pythonPathContainsCheckout === false,
        noDevServer: runtime.noDevServer ?? null,
        checkoutPathEntries: runtime.checkoutPathEntries || null,
        pythonPathContainsCheckout: runtime.pythonPathContainsCheckout ?? null,
      } },
      recoveryResults: { status: retry.taskDone ? 'measured_retry_completed' : 'not_completed',
        priorFilesPreserved: retry.previousFilesPreserved ?? false },
      artifactHashes: artifacts,
      limitations: [...report.limitations, 'The preparation-gate response is synthetic and only unlocks the current UI; agent-hit itself uses the installed shared runner and real bundled Python.'],
      decision: technicalDecision,
    },
    A0004: {
      owner, sourceSha: report.sourceSha, relatedTIds: ['T0025', 'T0026', 'T0027', 'T0028'],
      requirement: 'Unknown or insufficient RAM/VRAM/disk refuses before heavy work; the subsequent recovery attempt preserves prior user files.',
      scenario: 'Installed current creation UI → agent-hit IPC/shared task runner → bundled Python; injected unknown/low resource measurements for deny cases; then retry on measured Windows runner inventory.',
      environment,
      positiveResults: { measuredRetry: retry },
      negativeResults: denials,
      recoveryResults: { afterNegativeMatrix: retry.taskDone ? 'measured_retry_completed' : 'not_completed',
        priorFilesPreserved: retry.previousFilesPreserved ?? false,
        sentinelSha256: retry.sentinelSha256 || null },
      artifactHashes: artifacts,
      limitations: [...report.limitations, 'The runner has no CUDA/AMD inference verification; VRAM denial cases use synthetic device measurements and a placeholder user WAV.'],
      decision: technicalDecision,
    },
  };
  return report;
}

module.exports = { checkAgentPreflight, refusalOutcome, snapshotFiles, preservesSnapshot, unchangedSnapshot };

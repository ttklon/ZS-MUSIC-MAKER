'use strict';
const INJECTOR = String.raw`import os, sys
root = os.getcwd()
if root not in sys.path:
    sys.path.insert(0, root)
scenario = os.environ.get("ZSMM_AGENT_TEST_SCENARIO", "")
resource_scenarios = {"unknown_ram", "insufficient_ram", "unknown_disk", "insufficient_disk",
                      "unknown_vram", "insufficient_vram"}
if scenario in resource_scenarios:
    from app.ai import profiles
    original = profiles.measure_profile
    def measure_profile(directory):
        inventory = original(directory)
        measurements = inventory.setdefault("measurements", {})
        system = inventory.setdefault("system", {})
        if scenario in ("unknown_ram", "insufficient_ram"):
            value = None if scenario == "unknown_ram" else 1.0
            measurements["ram_available_gib"] = value
            system["ram_available_gib"] = value
        elif scenario in ("unknown_disk", "insufficient_disk"):
            value = None if scenario == "unknown_disk" else 0.25
            measurements["disk_free_gib"] = value
            system["disk_free_gib"] = value
        else:
            free = None if scenario == "unknown_vram" else 1.0
            device = {"backend": "cuda", "vendor": "nvidia", "name": "synthetic acceptance device",
                      "total_vram_gib": 8.0, "free_vram_gib": free}
            system["pytorch_device"] = device
            system["gpus"] = [{"name": device["name"], "vendor": "nvidia", "vram_total_gib": 8.0}]
            gpu = measurements.get("gpu")
            if not isinstance(gpu, dict):
                gpu = {}
            gpu.update(adapters=system["gpus"], pytorch_device=device)
            measurements["gpu"] = gpu
        return inventory
    profiles.measure_profile = measure_profile
elif scenario == "unbudgeted_musicgen":
    from modules.hit_factory import adaptive
    original = adaptive.get_adaptive_config
    def select_unbudgeted_musicgen(*args, **kwargs):
        config = original(*args, **kwargs)
        config["use_acestep"] = False
        config["use_musicgen"] = True
        config["use_texture"] = False
        return config
    adaptive.get_adaptive_config = select_unbudgeted_musicgen
elif scenario == "acceptance_setup_ready":
    from app.cli import commands
    def acceptance_setup(*args, **kwargs):
        from app.cli.task_events import TaskEvents
        events = TaskEvents()
        events.emit("done", ok=True, report={"setup": {
            "schema": 1, "ok": True, "blockers": [], "inference_verified": False,
            "acceptance_fixture": "setup gate only; no engine or model is installed"}})
        return 0
    commands.run_bootstrap = acceptance_setup
elif scenario == "cancel_model_worker":
    from modules.agent_guide import runner as agent_runner
    def cancellation_probe(answers, preflight, adaptive_config, output_root, started, say):
        import json
        import os
        import time
        from pathlib import Path
        from app.ai.sequential_runner import AIStage, SequentialAIRunner
        marker = Path(os.environ["ZSMM_CANCEL_TEST_MARKER"])
        lock_path = Path(os.environ["ZSMM_CANCEL_TEST_LOCK"])
        def hold_stage_worker(_handle, _context):
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("w+b") as lock:
                lock.write(b"x")
                lock.flush()
                lock.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                metadata = {"schema": 1, "stage": "installed_cancel_probe",
                            "pid": os.getpid(), "parent_pid": os.getppid()}
                temporary = marker.with_name(marker.name + ".tmp")
                temporary.write_text(json.dumps(metadata), encoding="utf-8")
                os.replace(temporary, marker)
                while True:
                    time.sleep(0.1)
        worker_runner = SequentialAIRunner(vram_budget_gb=0, vram_probe=lambda: 0)
        worker_runner.add(AIStage("installed_cancel_probe", None, hold_stage_worker, timeout_sec=600))
        worker_runner.run()
        raise RuntimeError("installed cancellation probe returned without cancellation")
    agent_runner._agent_stages = cancellation_probe
`;

async function runCreationTaskFromInstalledUi(window, { stage, voicePath = '', timeoutMs = 9 * 60 * 1000 }) {
  const options = JSON.stringify({ stage, voicePath, timeoutMs });
  return window.webContents.executeJavaScript(`(async () => {
    const options = ${options};
    const root = document.getElementById('agent-body');
    const buttons = () => root ? [...root.querySelectorAll('button')] : [];
    const findButton = text => buttons().find(button => button.textContent.trim() === text);
    const waitFor = async (find, timeout = 20000) => {
      const deadline = Date.now() + timeout;
      while (Date.now() < deadline) {
        const value = find();
        if (value) return value;
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      return null;
    };
    if (!root || !window.zsmm?.onTaskDone || !window.zsmm?.onTaskEvent)
      return { error: 'installed creation UI or task bridge is unavailable', events: [] };

    let button;
    if (options.stage === 'prepare') {
      const fields = {
        'creation-mood': 'installed acceptance probe',
        'creation-artist': 'Acceptance Test',
        'creation-refs': '',
        'creation-voice': '',
      };
      for (const [id, value] of Object.entries(fields)) {
        const field = document.getElementById(id);
        if (!field) return { error: 'missing installed creation UI field: ' + id, events: [] };
        field.value = value;
        field.dispatchEvent(new Event('input', { bubbles: true }));
      }
      const next = findButton('Далее — подготовить студию');
      if (!next) return { error: 'installed creation idea step is unavailable', events: [] };
      next.click();
      button = await waitFor(() => findButton('Проверить и подготовить автоматически'));
    } else if (options.stage === 'generate') {
      button = findButton('Создать трек');
      if (!button) {
        const generationStep = [...root.querySelectorAll('.creation-steps button')][2];
        if (!generationStep || generationStep.disabled)
          return { error: 'installed creation generation step is unavailable', events: [] };
        generationStep.click();
        button = await waitFor(() => findButton('Создать трек'));
      }
      const voice = document.getElementById('creation-voice');
      if (!voice) return { error: 'missing installed creation UI field: creation-voice', events: [] };
      voice.value = options.voicePath || '';
      voice.dispatchEvent(new Event('input', { bubbles: true }));
      button = findButton('Создать трек');
    } else {
      return { error: 'unknown installed UI task stage', events: [] };
    }
    if (!button) return { error: 'installed creation action did not render', events: [] };
    if (button.disabled) return { error: 'installed creation action is disabled', events: [] };

    const events = [];
    let taskId = null;
    let pendingDone = null;
    let clicked = false;
    let finish;
    let timer;
    let offEvent = () => {};
    let offDone = () => {};
    const completion = new Promise(resolve => {
      let settled = false;
      finish = value => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(value);
      };
      offEvent = window.zsmm.onTaskEvent(event => {
        if (events.length < 500) events.push(event);
        if (event?.type === 'start' && typeof event.taskId === 'string') {
          taskId = event.taskId;
          if (pendingDone?.taskId === taskId) finish({ done: pendingDone });
        }
      });
      offDone = window.zsmm.onTaskDone(done => {
        if (taskId && done?.taskId === taskId) finish({ done });
        else if (!taskId && clicked) pendingDone = done;
      });
      timer = setTimeout(() => finish({ error: 'installed UI task timed out' }), options.timeoutMs);
    });
    try {
      clicked = true;
      button.click();
      const result = await completion;
      if (result.error) {
        try { await window.zsmm.stopTask(); } catch { /* timeout report remains primary */ }
      }
      await new Promise(resolve => setTimeout(resolve, 50));
      const status = root.textContent || '';
      const setup = result.done?.report?.setup || null;
      return {
        ...result, status, events, taskId: taskId || result.done?.taskId || null,
        startCommand: events.find(event => event?.type === 'start')?.command || null,
        setupReady: setup?.schema === 1 && setup?.ok === true,
        generationButtonEnabled: Boolean(findButton('Создать трек') && !findButton('Создать трек').disabled),
      };
    } finally {
      clearTimeout(timer);
      offDone();
      offEvent();
    }
  })()`);
}

async function prepareCreationUi(window) {
  return runCreationTaskFromInstalledUi(window, { stage: 'prepare', timeoutMs: 90 * 1000 });
}

async function runAgentFromInstalledUi(window, voicePath = '') {
  return runCreationTaskFromInstalledUi(window, { stage: 'generate', voicePath, timeoutMs: 9 * 60 * 1000 });
}


module.exports = { INJECTOR, runCreationTaskFromInstalledUi, prepareCreationUi, runAgentFromInstalledUi };

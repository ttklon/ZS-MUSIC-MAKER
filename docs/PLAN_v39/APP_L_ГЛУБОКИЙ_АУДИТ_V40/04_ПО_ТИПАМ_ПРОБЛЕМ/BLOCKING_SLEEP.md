# BLOCKING_SLEEP — time.sleep() без комментария/аргументации

**Severity:** 🟢 LOW
**Всего:** 12
**Как чинить:** Комментарий или await asyncio.sleep().

## Все вхождения

### `app/gui/wizard.py` — 1 шт.
- **строка 1041** — time.sleep(...) без пояснения
  ```
       1039 | 
       1040 |         threading.Thread(target=_run, daemon=True).start()
  >>>  1041 |         time.sleep(2)
       1042 |         webbrowser.open("http://127.0.0.1:7860")
  ```

### `app/runtime_orchestrator.py` — 1 шт.
- **строка 76** — time.sleep(...) без пояснения
  ```
         74 |                     tid = self._queue.pop(0)
         75 |             if not tid:
  >>>    76 |                 time.sleep(0.2)
         77 |                 continue
         78 |             job = self.jobs.get(tid)
  ```

### `modules/hit_kpi_monitor_v11.py` — 2 шт.
- **строка 322** — time.sleep(...) без пояснения
  ```
        320 |         s = KpiSession(project_id="test01", hw_mode="fallback_hw")
        321 |         st = s.start_stage("mix")
  >>>   322 |         time.sleep(0.02)
        323 |         s.end_stage(st, True)
        324 |         st2 = s.start_stage("rvc_train")
  ```
- **строка 325** — time.sleep(...) без пояснения
  ```
        323 |         s.end_stage(st, True)
        324 |         st2 = s.start_stage("rvc_train")
  >>>   325 |         time.sleep(0.02)
        326 |         s.end_stage(st2, True)
        327 |         rd = os.path.join(tmp, "rel")
  ```

### `modules/karaoke_engine.py` — 2 шт.
- **строка 93** — time.sleep(...) без пояснения
  ```
         91 |         for i in range(self.count_in_beats):
         92 |             self._fire("on_beat", {"beat": i + 1, "is_count_in": True})
  >>>    93 |             time.sleep(self.beat_ms / 1000.0)
         94 |             if self._stop.is_set():
         95 |                 return
  ```
- **строка 121** — time.sleep(...) без пояснения
  ```
        119 |                     last_word_idx = idx
        120 |                     break
  >>>   121 |             time.sleep(0.02)
        122 |         self.state = "finished"
        123 |         self._fire("on_end", {"duration_ms": self.elapsed_ms()})
  ```

### `modules/render_queue.py` — 1 шт.
- **строка 139** — time.sleep(...) без пояснения
  ```
        137 |             next_item = self._pick_next()
        138 |             if not next_item:
  >>>   139 |                 time.sleep(3)
        140 |                 continue
        141 |             self._process(next_item)
  ```

### `modules/rvc_trainer_v9.py` — 2 шт.
- **строка 122** — time.sleep(...) без пояснения
  ```
        120 |             if hasattr(rvc_py, "train"):
        121 |                 for e in range(1, total + 1):
  >>>   122 |                     time.sleep(0.05)
        123 |                     job["progress"] = e / total
        124 |                     job["current_epoch"] = e
  ```
- **строка 136** — time.sleep(...) без пояснения
  ```
        134 |     # DRY: симулируем прогон эпох с обновлением прогресса (для CI/UI)
        135 |     for e in range(1, total + 1):
  >>>   136 |         time.sleep(0.001)
        137 |         job["progress"] = e / total
        138 |         job["current_epoch"] = e
  ```

### `modules/voice_onboarding.py` — 1 шт.
- **строка 195** — time.sleep(...) без пояснения
  ```
        193 |         info = rec.start()
        194 |         if info.get("ok"):
  >>>   195 |             time.sleep(step.target_sec)
        196 |             out = rec.stop()
        197 |             if out.get("ok"):
  ```

### `tools/deep_audit_v40.py` — 2 шт.
- **строка 17** — time.sleep(...) без пояснения
  ```
         15 |   • сложность (упрощённо: количество if/for/while/try)
         16 |   • голые print (не через logger)
  >>>    17 |   • голые time.sleep() без комментария
         18 |   • assert в production-коде
         19 |   • риски безопасности: eval/exec/os.system/subprocess.shell=True
  ```
- **строка 249** — time.sleep(...) без пояснения
  ```
        247 |             report["issues"].append(
        248 |                 {"line": i, "kind": "BLOCKING_SLEEP",
  >>>   249 |                  "msg": "time.sleep(...) без пояснения"}
        250 |             )
        251 |         if re.match(r"^\s*global\s+\w", line):
  ```

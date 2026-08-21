# HARDCODED_POSIX_PATH — Захардкоженный POSIX-путь (/home/... /Users/...)

**Severity:** 🟠 HIGH
**Всего:** 4
**Как чинить:** Path из config.settings/tempfile.gettempdir().

## Все вхождения

### `modules/release_pack_v9.py` — 1 шт.
- **строка 178** — /tmp/none.wav
  ```
        176 |             "duration_s": 150,
        177 |         },
  >>>   178 |         master_wav="/tmp/none.wav",
        179 |     )
        180 |     print(json.dumps(r, indent=2))
  ```

### `modules/video_edit_v11.py` — 1 шт.
- **строка 453** — /tmp/_v11_lrc_test.lrc
  ```
        451 | 
        452 | def _self_test() -> bool:
  >>>   453 |     tmp = "/tmp/_v11_lrc_test.lrc"
        454 |     with open(tmp, "w", encoding="utf-8") as f:
        455 |         f.write("[00:01.00]hello\n[00:02.50]world\n[bad]skip\n")
  ```

### `tests/test_ai_layer.py` — 1 шт.
- **строка 447** — /tmp/unused.txt
  ```
        445 |             raise RuntimeError("model load failed")
        446 | 
  >>>   447 |     result = transcribe_reference_audio(FailingASR(), "reference.wav", "/tmp/unused.txt")
        448 | 
        449 |     assert result["ok"] is False
  ```

### `tests/test_settings.py` — 1 шт.
- **строка 52** — /tmp/custom_beats
  ```
         50 |     s = S.Settings.load(env_path=env_file)
         51 |     assert s.vram_gb == 20.0
  >>>    52 |     assert str(s.beats_dir) == "/tmp/custom_beats"
         53 | 
         54 | 
  ```

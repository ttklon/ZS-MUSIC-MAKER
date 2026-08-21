# SILENT_EXCEPT_PASS — 'except ...: pass' — тихое поглощение ошибок

**Severity:** 🟡 MEDIUM
**Всего:** 120
**Как чинить:** `pass` → `logger.debug('reason=..., exc=%r', exc)`.

## Все вхождения

### `agents/sample_hunter.py` — 1 шт.
- **строка 159** — except: pass — тихое подавление ошибок
  ```
        157 |                 s for s in online if is_free_commercial(s.get("license", "unknown"))
        158 |             ]
  >>>   159 |         except Exception:
        160 |             pass
        161 | 
  ```

### `agents/trend_scout.py` — 3 шт.
- **строка 40** — except: pass — тихое подавление ошибок
  ```
         38 |     try:
         39 |         trends.extend(_duckduckgo_search(f"{query} тренд сленг 2026"))
  >>>    40 |     except Exception:
         41 |         pass
         42 | 
  ```
- **строка 48** — except: pass — тихое подавление ошибок
  ```
         46 | 
         47 |         trends.extend(load_slang_dictionary()[:10])
  >>>    48 |     except Exception:
         49 |         pass
         50 | 
  ```
- **строка 147** — except: pass — тихое подавление ошибок
  ```
        145 |         if online:
        146 |             topics = online[:4] + topics
  >>>   147 |     except Exception:
        148 |         pass
        149 | 
  ```

### `app/ai/registry.py` — 8 шт.
- **строка 235** — except: pass — тихое подавление ошибок
  ```
        233 |                 if need <= self.hw.vram_gb:
        234 |                     return "cuda"
  >>>   235 |         except Exception:
        236 |             pass
        237 |         try:
  ```
- **строка 241** — except: pass — тихое подавление ошибок
  ```
        239 |             if pref in ("dml", "auto") and need <= self.hw.vram_gb:
        240 |                 return "dml"
  >>>   241 |         except Exception:
        242 |             pass
        243 |         return "cpu"
  ```
- **строка 196** — except: pass — тихое подавление ошибок
  ```
        194 |             try:
        195 |                 del self._current.handle
  >>>   196 |             except Exception:
        197 |                 pass
        198 |             self._current = None
  ```
- **строка 205** — except: pass — тихое подавление ошибок
  ```
        203 |                     torch.cuda.empty_cache()
        204 |                     torch.cuda.ipc_collect()
  >>>   205 |             except Exception:
        206 |                 pass
        207 | 
  ```
- **строка 288** — except: pass — тихое подавление ошибок
  ```
        286 |                 try:
        287 |                     t.to("cuda")
  >>>   288 |                 except Exception:
        289 |                     pass
        290 |             return t, device
  ```
- **строка 307** — except: pass — тихое подавление ошибок
  ```
        305 |                 try:
        306 |                     m.to("cuda")
  >>>   307 |                 except Exception:
        308 |                     pass
        309 |             return m, device
  ```
- **строка 331** — except: pass — тихое подавление ошибок
  ```
        329 |                 try:
        330 |                     m = m.to("cuda")
  >>>   331 |                 except Exception:
        332 |                     pass
        333 |             return (m, p), device
  ```
- **строка 354** — except: pass — тихое подавление ошибок
  ```
        352 |                     pipe.enable_attention_slicing()
        353 |                     pipe.enable_vae_tiling()
  >>>   354 |                 except Exception:
        355 |                     pass
        356 |             return pipe, device
  ```

### `app/core/hw_autodetect.py` — 5 шт.
- **строка 59** — except: pass — тихое подавление ошибок
  ```
         57 |             )
         58 |             return g
  >>>    59 |     except Exception:
         60 |         pass
         61 |     # DirectML (AMD/Intel iGPU на Windows)
  ```
- **строка 96** — except: pass — тихое подавление ошибок
  ```
         94 |             g["vram_gb"] = 4.0  # осторожная оценка для RX 580
         95 |         return g
  >>>    96 |     except Exception:
         97 |         pass
         98 |     # ROCm (Linux)
  ```
- **строка 105** — except: pass — тихое подавление ошибок
  ```
        103 |             g["vram_gb"] = 8.0
        104 |             return g
  >>>   105 |     except Exception:
        106 |         pass
        107 |     return g
  ```
- **строка 154** — except: pass — тихое подавление ошибок
  ```
        152 |             json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
        153 |         )
  >>>   154 |     except Exception:
        155 |         pass
        156 |     return profile
  ```
- **строка 117** — except: pass — тихое подавление ошибок
  ```
        115 |             if time.time() - cached.get("ts", 0) < 86400:
        116 |                 return cached
  >>>   117 |         except Exception:
        118 |             pass
        119 | 
  ```

### `app/core/musicgen_texture.py` — 1 шт.
- **строка 71** — except: pass — тихое подавление ошибок
  ```
         69 | 
         70 |         torch.cuda.empty_cache()
  >>>    71 |     except Exception:
         72 |         pass
         73 | 
  ```

### `app/core/orchestrator.py` — 15 шт.
- **строка 951** — except: pass — тихое подавление ошибок
  ```
        949 |                 "reason": "primary TTS unavailable; using pyttsx3",
        950 |             }
  >>>   951 |     except Exception:
        952 |         pass
        953 |     # v19: честный numpy-fallback — короткая "рыба" вокала с формантной
  ```
- **строка 1494** — except: pass — тихое подавление ошибок
  ```
       1492 |             hit_metrics=hit_metrics,
       1493 |         )
  >>>  1494 |     except Exception:
       1495 |         pass
       1496 |     try:
  ```
- **строка 1504** — except: pass — тихое подавление ошибок
  ```
       1502 |             if isinstance(r, dict):
       1503 |                 return r
  >>>  1504 |     except Exception:
       1505 |         pass
       1506 |     return _minimal_release_pack(master_wav, meta, out)
  ```
- **строка 892** — except: pass — тихое подавление ошибок
  ```
        890 |                     ),
        891 |                 }
  >>>   892 |         except Exception:
        893 |             pass
        894 |     fb = _fallback_lyrics(theme, genre)
  ```
- **строка 1171** — except: pass — тихое подавление ошибок
  ```
       1169 |                 [sosfilt(sos, voc[:, c]) for c in range(voc.shape[1])], axis=1
       1170 |             )
  >>>  1171 |         except Exception:
       1172 |             pass
       1173 |         gain = 10 ** (vocal_gain_db / 20.0)
  ```
- **строка 1311** — except: pass — тихое подавление ошибок
  ```
       1309 |                     legacy_attempt,
       1310 |                 )
  >>>  1311 |         except Exception:
       1312 |             # Для надежного fallback сохраняем имя attempted legacy-ветки,
       1313 |             # но не помечаем результат LEGACY, если её обработка не удалась.
  ```
- **строка 1339** — except: pass — тихое подавление ошибок
  ```
       1337 |                     except Exception:
       1338 |                         continue
  >>>  1339 |         except Exception:
       1340 |             pass
       1341 |         import shutil
  ```
- **строка 1527** — except: pass — тихое подавление ошибок
  ```
       1525 |             seg.export(mp3, format="mp3", bitrate="320k")
       1526 |             files.append(str(mp3))
  >>>  1527 |         except Exception:
       1528 |             pass
       1529 |         try:
  ```
- **строка 1538** — except: pass — тихое подавление ошибок
  ```
       1536 |             img.save(cov)
       1537 |             files.append(str(cov))
  >>>  1538 |         except Exception:
       1539 |             pass
       1540 |         (out / "lyrics.txt").write_text(meta.get("lyrics_text", ""), encoding="utf-8")
  ```
- **строка 1599** — except: pass — тихое подавление ошибок
  ```
       1597 |                 # жанр берём из ключа пресета (brazilian_phonk и т.п.)
       1598 |                 _preset_genre = preset_key
  >>>  1599 |         except Exception:
       1600 |             pass
       1601 |     genre = wizard_state.get("genre") or _preset_genre or "drift_phonk"
  ```
- **строка 1937** — except: pass — тихое подавление ошибок
  ```
       1935 |                     ],
       1936 |                 )
  >>>  1937 |         except Exception:
       1938 |             pass
       1939 |         try:
  ```
- **строка 1950** — except: pass — тихое подавление ошибок
  ```
       1948 |                     raw_stems, ["drums", "bass", "vocals", "other"]
       1949 |                 )
  >>>  1950 |         except Exception:
       1951 |             pass
       1952 |         _hit = {}
  ```
- **строка 1958** — except: pass — тихое подавление ошибок
  ```
       1956 |                     k: v for k, v in s13.output.items() if k not in ("ok", "reason")
       1957 |                 }
  >>>  1958 |         except Exception:
       1959 |             pass
       1960 |         s14 = _timed(
  ```
- **строка 923** — except: pass — тихое подавление ошибок
  ```
        921 |                 if path and Path(path).exists() and Path(path).stat().st_size > 1000:
        922 |                     return {"ok": True, "path": path, "engine": "voice_synth.synth"}
  >>>   923 |             except Exception:
        924 |                 pass
        925 |         if hasattr(voice_synth, "synthesize"):
  ```
- **строка 1044** — except: pass — тихое подавление ошибок
  ```
       1042 |                         )
       1043 |                         seg = seg + sosfilt(sos, seg) * 0.6
  >>>  1044 |                 except Exception:
       1045 |                     # fallback: просто нормализуем
       1046 |                     pass
  ```

### `app/core/orchestrator_ai.py` — 1 шт.
- **строка 265** — except: pass — тихое подавление ошибок
  ```
        263 |         try:
        264 |             model.set_generation_params(duration=20, top_k=250, temperature=1.0, cfg_coef=3.0)
  >>>   265 |         except Exception:
        266 |             pass
        267 |         n_chunks = max(1, math.ceil(ws["duration_sec"] / 20))
  ```

### `app/core/orchestrator_god.py` — 1 шт.
- **строка 37** — except: pass — тихое подавление ошибок
  ```
         35 |         if isinstance(obj, _np.generic):
         36 |             return obj.item()
  >>>    37 |     except ImportError:
         38 |         pass
         39 |     if isinstance(obj, dict):
  ```

### `app/core/orchestrator_v11_patch.py` — 2 шт.
- **строка 339** — except: pass — тихое подавление ошибок
  ```
        337 |                 wf.setframerate(44100)
        338 |                 wf.writeframes(struct.pack("<" + "h" * 44100, *([0] * 44100)))
  >>>   339 |         except Exception:
        340 |             pass
        341 |     lp = os.path.join(release_dir, "lyrics.txt")
  ```
- **строка 65** — except: pass — тихое подавление ошибок
  ```
         63 |             try:
         64 |                 progress_cb(stage, pct, msg)
  >>>    65 |             except Exception:
         66 |                 pass
         67 | 
  ```

### `app/core/orchestrator_v8_patch.py` — 1 шт.
- **строка 26** — except: pass — тихое подавление ошибок
  ```
         24 |         if callable(hook):
         25 |             hook(name, progress)
  >>>    26 |     except Exception:
         27 |         pass
         28 | 
  ```

### `app/core/orchestrator_v9_patch.py` — 2 шт.
- **строка 34** — except: pass — тихое подавление ошибок
  ```
         32 |         if callable(hook):
         33 |             hook(name, progress)
  >>>    34 |     except Exception:
         35 |         pass
         36 | 
  ```
- **строка 222** — except: pass — тихое подавление ошибок
  ```
        220 |             )
        221 |             voice_manifest = json.loads(Path(vm_path).read_text(encoding="utf-8"))
  >>>   222 |         except Exception:
        223 |             pass
        224 | 
  ```

### `app/gui/theme_v12.py` — 1 шт.
- **строка 251** — except: pass — тихое подавление ошибок
  ```
        249 |     try:
        250 |         app.setStyleSheet(qss())
  >>>   251 |     except Exception:
        252 |         pass
        253 | 
  ```

### `app/gui/wizard.py` — 4 шт.
- **строка 134** — except: pass — тихое подавление ошибок
  ```
        132 | 
        133 |             self.name.setText(get_artist_name())
  >>>   134 |         except Exception:
        135 |             pass
        136 | 
  ```
- **строка 142** — except: pass — тихое подавление ошибок
  ```
        140 | 
        141 |             set_artist_name(self.name.text().strip() or "ZSMM Artist")
  >>>   142 |         except Exception:
        143 |             pass
        144 |         recipe["artist_name"] = self.name.text().strip() or "ZSMM Artist"
  ```
- **строка 553** — except: pass — тихое подавление ошибок
  ```
        551 |                     f"[RVC training] {st}  |  {stage}  |  {int(prog*100)}%"
        552 |                 )
  >>>   553 |         except Exception:
        554 |             pass
        555 | 
  ```
- **строка 829** — except: pass — тихое подавление ошибок
  ```
        827 |                 from pathlib import Path
        828 |                 webbrowser.open(Path(p).absolute().as_uri())
  >>>   829 |         except Exception:
        830 |             pass
        831 | 
  ```

### `app/hw_probe.py` — 2 шт.
- **строка 40** — except: pass — тихое подавление ошибок
  ```
         38 |             )
         39 |             hw.backend = "cuda"
  >>>    40 |     except Exception:
         41 |         pass
         42 | 
  ```
- **строка 53** — except: pass — тихое подавление ошибок
  ```
         51 |             hw.vram_gb = 4.0  # оценочно — уточняется через DXGI
         52 |             hw.backend = "directml"
  >>>    53 |         except Exception:
         54 |             pass
         55 | 
  ```

### `app/logger.py` — 1 шт.
- **строка 24** — except: pass — тихое подавление ошибок
  ```
         22 |         try:
         23 |             self.s.flush()
  >>>    24 |         except Exception:
         25 |             pass
         26 | 
  ```

### `app/runtime_orchestrator.py` — 1 шт.
- **строка 45** — except: pass — тихое подавление ошибок
  ```
         43 |             else:
         44 |                 print(msg)
  >>>    45 |         except Exception:
         46 |             pass
         47 | 
  ```

### `main.py` — 7 шт.
- **строка 45** — except: pass — тихое подавление ошибок
  ```
         43 |                 str(data.get("build", default_b)),
         44 |             )
  >>>    45 |     except Exception:
         46 |         pass
         47 |     return default_v, default_b
  ```
- **строка 116** — except: pass — тихое подавление ошибок
  ```
        114 |             except Exception:
        115 |                 pass
  >>>   116 |     except Exception:
        117 |         pass
        118 | 
  ```
- **строка 173** — except: pass — тихое подавление ошибок
  ```
        171 |     try:
        172 |         theme_v12.apply(app)
  >>>   173 |     except Exception:
        174 |         pass
        175 |     try:
  ```
- **строка 85** — except: pass — тихое подавление ошибок
  ```
         83 |                 sys.stderr.reconfigure(encoding="utf-8", errors="replace")
         84 |                 return
  >>>    85 |         except Exception:
         86 |             pass
         87 |         try:
  ```
- **строка 372** — except: pass — тихое подавление ошибок
  ```
        370 |                 _safe_print("  full list: python main.py --list-genres")
        371 |                 return 2
  >>>   372 |         except ImportError:
        373 |             pass  # движок жанров недоступен — пусть пайплайн сам решит
        374 | 
  ```
- **строка 126** — except: pass — тихое подавление ошибок
  ```
        124 |         try:
        125 |             sys.stdout.buffer.write((msg + "\n").encode("utf-8", "replace"))
  >>>   126 |         except Exception:
        127 |             pass
        128 | 
  ```
- **строка 114** — except: pass — тихое подавление ошибок
  ```
        112 |                     line_buffering=True,
        113 |                 )
  >>>   114 |             except Exception:
        115 |                 pass
        116 |     except Exception:
  ```

### `modules/analyzer.py` — 1 шт.
- **строка 86** — except: pass — тихое подавление ошибок
  ```
         84 |         danceability = estd.Danceability()(audio)
         85 |         essentia_desc["danceability"] = round(float(danceability[0]), 3)
  >>>    86 |     except Exception:
         87 |         pass
         88 | 
  ```

### `modules/artist_dossier/manager.py` — 1 шт.
- **строка 145** — except: pass — тихое подавление ошибок
  ```
        143 |                 shutil.copy2(audio_path, dst)
        144 |                 entry.audio_path = str(dst)
  >>>   145 |             except Exception:
        146 |                 pass
        147 |         if lyrics:
  ```

### `modules/beat_constructor.py` — 3 шт.
- **строка 468** — except: pass — тихое подавление ошибок
  ```
        466 |                     ]
        467 |                     full_track[_idx - _fade : _idx] *= _env
  >>>   468 |         except Exception:
        469 |             pass
        470 | 
  ```
- **строка 526** — except: pass — тихое подавление ошибок
  ```
        524 |                     _pos += _ns
        525 |                     _mi += 1
  >>>   526 |         except Exception:
        527 |             pass
        528 | 
  ```
- **строка 599** — except: pass — тихое подавление ошибок
  ```
        597 |                 # Стерео запись через wavfile
        598 |                 wavfile.write(out_path, self.sr, (stereo * 32767).astype(np.int16))
  >>>   599 |             except Exception:
        600 |                 pass
        601 | 
  ```

### `modules/beat_gen.py` — 1 шт.
- **строка 28** — except: pass — тихое подавление ошибок
  ```
         26 | 
         27 |             return "dml"
  >>>    28 |         except ImportError:
         29 |             pass
         30 |         return "cpu"
  ```

### `modules/beat_gen_ai.py` — 1 шт.
- **строка 23** — except: pass — тихое подавление ошибок
  ```
         21 |             model.set_generation_params(duration=min(chunk_sec, 30), top_k=250,
         22 |                                         top_p=0.0, temperature=1.0, cfg_coef=3.0)
  >>>    23 |         except Exception:
         24 |             pass
         25 |         sr = getattr(model, "sample_rate", 32000)
  ```

### `modules/chanson_engine.py` — 2 шт.
- **строка 95** — except: pass — тихое подавление ошибок
  ```
         93 |                 ])
         94 |                 chord_signal = board(chord_signal, self.sr)
  >>>    95 |             except Exception:
         96 |                 pass
         97 | 
  ```
- **строка 182** — except: pass — тихое подавление ошибок
  ```
        180 |                 ])
        181 |                 stereo_mix = master_board(stereo_mix, self.sr)
  >>>   182 |             except Exception:
        183 |                 pass
        184 | 
  ```

### `modules/cyber_synth.py` — 2 шт.
- **строка 71** — except: pass — тихое подавление ошибок
  ```
         69 |                 ])
         70 |                 lead = board(lead, self.sr)
  >>>    71 |             except Exception:
         72 |                 pass
         73 | 
  ```
- **строка 112** — except: pass — тихое подавление ошибок
  ```
        110 |                 ])
        111 |                 stereo_mix = master_board(stereo_mix, self.sr)
  >>>   112 |             except Exception:
        113 |                 pass
        114 | 
  ```

### `modules/distribution_export_v11.py` — 1 шт.
- **строка 70** — except: pass — тихое подавление ошибок
  ```
         68 |                 if gen:
         69 |                     self.isrc = gen
  >>>    70 |         except ImportError:
         71 |             pass
         72 | 
  ```

### `modules/female_backing.py` — 4 шт.
- **строка 131** — except: pass — тихое подавление ошибок
  ```
        129 |             )  # noqa: ZSMM_NOT_RVC
        130 |             y = np.stack([shifted, shifted], axis=-1)
  >>>   131 |         except Exception:
        132 |             pass
        133 | 
  ```
- **строка 141** — except: pass — тихое подавление ошибок
  ```
        139 |             for ch in range(y.shape[1]):
        140 |                 y[:, ch] = sosfilt(sos, y[:, ch])
  >>>   141 |         except Exception:
        142 |             pass
        143 | 
  ```
- **строка 40** — except: pass — тихое подавление ошибок
  ```
         38 |             try:
         39 |                 torch.save(model, model_path)
  >>>    40 |             except Exception:
         41 |                 pass
         42 |         else:
  ```
- **строка 211** — except: pass — тихое подавление ошибок
  ```
        209 | 
        210 |                 b = librosa.resample(b.T, orig_sr=sr2, target_sr=sr).T
  >>>   211 |             except Exception:
        212 |                 pass
        213 |         n = max(len(v), len(b))
  ```

### `modules/hit_kpi_monitor_v11.py` — 1 шт.
- **строка 183** — except: pass — тихое подавление ошибок
  ```
        181 |                 if v <= 1.0:
        182 |                     return v * 100.0
  >>>   183 |             except Exception:
        184 |                 pass
        185 |     for k in ("summary", "verdict", "final"):
  ```

### `modules/hit_scorer.py` — 1 шт.
- **строка 282** — except: pass — тихое подавление ошибок
  ```
        280 |                 score = 50.0
        281 |             return score, lufs
  >>>   282 |         except Exception:
        283 |             pass
        284 | 
  ```

### `modules/hw_directml.py` — 1 шт.
- **строка 52** — except: pass — тихое подавление ошибок
  ```
         50 |                 out["vram_mb"] = int(props.total_memory / (1024 * 1024))
         51 |                 out["gpu_name"] = props.name
  >>>    52 |             except Exception:
         53 |                 pass
         54 |     except Exception as e:
  ```

### `modules/kpi_dashboard_v12.py` — 1 шт.
- **строка 346** — except: pass — тихое подавление ошибок
  ```
        344 |                 render_markdown(dash), encoding="utf-8"
        345 |             )
  >>>   346 |         except Exception:
        347 |             pass
        348 |     return dash
  ```

### `modules/llm_clients_v15.py` — 3 шт.
- **строка 286** — except: pass — тихое подавление ошибок
  ```
        284 |         try:
        285 |             text = j["candidates"][0]["content"]["parts"][0]["text"]
  >>>   286 |         except Exception:
        287 |             pass
        288 |         return ProviderResult(
  ```
- **строка 395** — except: pass — тихое подавление ошибок
  ```
        393 |             s.close()
        394 |             out["internet"] = True
  >>>   395 |         except Exception:
        396 |             pass
        397 |         try:
  ```
- **строка 406** — except: pass — тихое подавление ошибок
  ```
        404 |             s.close()
        405 |             out["ollama"] = True
  >>>   406 |         except Exception:
        407 |             pass
        408 |         LLMRouter._preflight_cache = out
  ```

### `modules/lyrics_gen.py` — 2 шт.
- **строка 170** — except: pass — тихое подавление ошибок
  ```
        168 |         if r.status_code == 200:
        169 |             return r.json().get("response", "").strip()
  >>>   170 |     except Exception:
        171 |         pass
        172 |     return None
  ```
- **строка 117** — except: pass — тихое подавление ошибок
  ```
        115 |             try:
        116 |                 out.append(json.loads(line))
  >>>   117 |             except Exception:
        118 |                 pass
        119 |     return out
  ```

### `modules/master_pipeline_v12.py` — 1 шт.
- **строка 73** — except: pass — тихое подавление ошибок
  ```
         71 |             import sys as _s
         72 |             _s.stderr.write(f"[master_pipeline_v12] log-write failed: {e}\n")
  >>>    73 |         except Exception:
         74 |             pass
         75 | 
  ```

### `modules/mastering.py` — 1 шт.
- **строка 114** — except: pass — тихое подавление ошибок
  ```
        112 |             mono = y.mean(axis=1) if y.ndim > 1 else y
        113 |             return float(meter.integrated_loudness(mono))
  >>>   114 |         except Exception:
        115 |             pass
        116 |     return _loudness_dbfs(y) - 3.0
  ```

### `modules/mixdown.py` — 1 шт.
- **строка 130** — except: pass — тихое подавление ошибок
  ```
        128 |             out.replace(".wav", ".mp3"), format="mp3", bitrate="320k"
        129 |         )
  >>>   130 |     except Exception:
        131 |         pass
        132 | 
  ```

### `modules/onboarding_tour.py` — 1 шт.
- **строка 166** — except: pass — тихое подавление ошибок
  ```
        164 |         try:
        165 |             return json.loads(TOUR_STATE.read_text(encoding="utf-8"))
  >>>   166 |         except Exception:
        167 |             pass
        168 |     return {"tour_done": False, "last_step": 0}
  ```

### `modules/phoneme_coverage.py` — 2 шт.
- **строка 53** — except: pass — тихое подавление ошибок
  ```
         51 |         try:
         52 |             texts.append(p.read_text(encoding="utf-8"))
  >>>    53 |         except Exception:
         54 |             pass
         55 |     for p in VAULT_DIR.rglob("*.json"):
  ```
- **строка 64** — except: pass — тихое подавление ошибок
  ```
         62 |                     if isinstance(item, dict) and "transcript" in item:
         63 |                         texts.append(str(item["transcript"]))
  >>>    64 |         except Exception:
         65 |             pass
         66 |     return texts
  ```

### `modules/release_pack_full.py` — 1 шт.
- **строка 906** — except: pass — тихое подавление ошибок
  ```
        904 |             import sys as _s
        905 |             _s.stderr.write(f"[release_pack_full] ID3/cover embed failed: {e}\n")
  >>>   906 |         except Exception:
        907 |             pass
        908 |     id3.save(str(mp3_path))
  ```

### `modules/rvc_manager.py` — 6 шт.
- **строка 84** — except: pass — тихое подавление ошибок
  ```
         82 |             b.reason = "CUDA available"
         83 |             return b
  >>>    84 |     except Exception:
         85 |         pass
         86 |     # 2) DirectML (AMD/Intel iGPU на Windows)
  ```
- **строка 99** — except: pass — тихое подавление ошибок
  ```
         97 |         b.reason = "DirectML available"
         98 |         return b
  >>>    99 |     except Exception:
        100 |         pass
        101 |     # 3) ROCm (Linux, редко)
  ```
- **строка 113** — except: pass — тихое подавление ошибок
  ```
        111 |             b.reason = "ROCm available"
        112 |             return b
  >>>   113 |     except Exception:
        114 |         pass
        115 |     # 4) CPU fallback
  ```
- **строка 216** — except: pass — тихое подавление ошибок
  ```
        214 |             try:
        215 |                 cb(self.job)
  >>>   216 |             except Exception:
        217 |                 pass
        218 | 
  ```
- **строка 233** — except: pass — тихое подавление ошибок
  ```
        231 |                     shutil.copy(src, ds / Path(src).name)
        232 |                     n += 1
  >>>   233 |                 except Exception:
        234 |                     pass
        235 |         return ds
  ```
- **строка 360** — except: pass — тихое подавление ошибок
  ```
        358 |                         job.stage = f"epoch {ep}/{job.epochs}"
        359 |                         self._emit()
  >>>   360 |                     except Exception:
        361 |                         pass
        362 |         ret = proc.wait()
  ```

### `modules/video_edit_v11.py` — 2 шт.
- **строка 352** — except: pass — тихое подавление ошибок
  ```
        350 |             final.close()
        351 |             audio.close()
  >>>   352 |         except Exception:
        353 |             pass
        354 |     return VideoEditResult(
  ```
- **строка 194** — except: pass — тихое подавление ошибок
  ```
        192 |                                 secs = float(m) * 60 + float(s)
        193 |                                 out.append((secs, text))
  >>>   194 |                             except Exception:
        195 |                                 pass
        196 |                         i = j + 1
  ```

### `modules/vocal_fx.py` — 2 шт.
- **строка 346** — except: pass — тихое подавление ошибок
  ```
        344 |         if p.exists() and cur != tmp_double:
        345 |             p.unlink()
  >>>   346 |     except Exception:
        347 |         pass
        348 | 
  ```
- **строка 334** — except: pass — тихое подавление ошибок
  ```
        332 |                 shutil.copy(cur, out_wav)
        333 |                 cur = out_wav
  >>>   334 |             except Exception:
        335 |                 pass
        336 | 
  ```

### `modules/voice_onboarding.py` — 1 шт.
- **строка 174** — except: pass — тихое подавление ошибок
  ```
        172 |         try:
        173 |             return json.loads(MANIFEST.read_text(encoding="utf-8"))
  >>>   174 |         except Exception:
        175 |             pass
        176 |     return {"steps": [], "started_at": None, "completed_at": None}
  ```

### `modules/voice_recording.py` — 5 шт.
- **строка 367** — except: pass — тихое подавление ошибок
  ```
        365 |             encoding="utf-8",
        366 |         )
  >>>   367 |     except Exception:
        368 |         pass
        369 | 
  ```
- **строка 105** — except: pass — тихое подавление ошибок
  ```
        103 |             self._buf.append(chunk)
        104 |             self._emit_metrics(chunk)
  >>>   105 |         except Exception:
        106 |             pass
        107 | 
  ```
- **строка 139** — except: pass — тихое подавление ошибок
  ```
        137 |                 )
        138 |             )
  >>>   139 |         except Exception:
        140 |             pass
        141 | 
  ```
- **строка 181** — except: pass — тихое подавление ошибок
  ```
        179 |             self._stream.stop()
        180 |             self._stream.close()
  >>>   181 |         except Exception:
        182 |             pass
        183 |         self._active = False
  ```
- **строка 383** — except: pass — тихое подавление ошибок
  ```
        381 |                 if d.get("max_input_channels", 0) > 0
        382 |             ]
  >>>   383 |         except Exception:
        384 |             pass
        385 |     return {
  ```

### `modules/voice_synth.py` — 1 шт.
- **строка 130** — except: pass — тихое подавление ошибок
  ```
        128 |     try:
        129 |         OUT_DIR.mkdir(parents=True, exist_ok=True)
  >>>   130 |     except Exception:
        131 |         pass
        132 |     # v33 FIX (P0, SESSION_LOG v32.4): дефолтное имя draft.wav молча
  ```

### `modules/voice_vault_v9.py` — 2 шт.
- **строка 135** — except: pass — тихое подавление ошибок
  ```
        133 |         segs, _ = m.transcribe(str(path))
        134 |         return " ".join(s.text.strip() for s in segs)[:500]
  >>>   135 |     except Exception:
        136 |         pass
        137 |     try:
  ```
- **строка 142** — except: pass — тихое подавление ошибок
  ```
        140 |         m = whisper.load_model("tiny")
        141 |         return (m.transcribe(str(path)).get("text") or "")[:500]
  >>>   142 |     except Exception:
        143 |         pass
        144 |     return None
  ```

### `modules/wizard_v12_integration.py` — 2 шт.
- **строка 47** — except: pass — тихое подавление ошибок
  ```
         45 |     try:
         46 |         (LOGS / "app.log").open("a", encoding="utf-8").write(line + "\n")
  >>>    47 |     except Exception:
         48 |         pass
         49 | 
  ```
- **строка 143** — except: pass — тихое подавление ошибок
  ```
        141 |                     "health_v12", 0.05, f"стек: {hr.verdict}, {hr.percent_ready}% готов"
        142 |                 )
  >>>   143 |             except Exception:
        144 |                 pass
        145 |     except Exception as e:  # noqa: BLE001
  ```

### `tools/smoke_v26.py` — 1 шт.
- **строка 212** — except: pass — тихое подавление ошибок
  ```
        210 |             encoding="utf-8",
        211 |         )
  >>>   212 |     except Exception:
        213 |         pass  # отчёт — nice-to-have, не должен валить smoke
        214 | 
  ```

### `tools/smoke_v29.py` — 1 шт.
- **строка 183** — except: pass — тихое подавление ошибок
  ```
        181 |             encoding="utf-8",
        182 |         )
  >>>   183 |     except Exception:
        184 |         pass  # отчёт — nice-to-have, не должен валить smoke
        185 | 
  ```

### `ui/karaoke_recorder.py` — 1 шт.
- **строка 118** — except: pass — тихое подавление ошибок
  ```
        116 |             },
        117 |         )
  >>>   118 |     except Exception:
        119 |         pass
        120 | 
  ```

### `ui/tutorial.py` — 1 шт.
- **строка 25** — except: pass — тихое подавление ошибок
  ```
         23 |             with open(new, "w", encoding="utf-8") as f:
         24 |                 f.write(payload)
  >>>    25 |     except Exception:
         26 |         pass
         27 |     return new
  ```

### `updater/updater.py` — 7 шт.
- **строка 394** — except: pass — тихое подавление ошибок
  ```
        392 |                 "version", "unknown"
        393 |             )
  >>>   394 |     except Exception:
        395 |         pass
        396 |     return {"ok": True, "version": ver, "backup": str(bak)}
  ```
- **строка 117** — except: pass — тихое подавление ошибок
  ```
        115 |             shutil.move(str(src), str(dst))
        116 |             moved[rel] = dst
  >>>   117 |         except Exception:
        118 |             # не смогли переместить — оставляем на месте (не валим установку)
        119 |             pass
  ```
- **строка 148** — except: pass — тихое подавление ошибок
  ```
        146 |                 shutil.move(str(stash), str(dst))
        147 |             restored.append(rel)
  >>>   148 |         except Exception:
        149 |             pass
        150 |     return restored
  ```
- **строка 255** — except: pass — тихое подавление ошибок
  ```
        253 |             old.unlink()
        254 |             removed.append(old)
  >>>   255 |         except Exception:
        256 |             pass
        257 |     return removed
  ```
- **строка 384** — except: pass — тихое подавление ошибок
  ```
        382 |                 "backup": str(bak),
        383 |             }
  >>>   384 |         except Exception:
        385 |             pass
        386 | 
  ```
- **строка 424** — except: pass — тихое подавление ошибок
  ```
        422 |                 shutil.move(str(src), str(dst))
        423 |                 moved[rel] = dst
  >>>   424 |             except Exception:
        425 |                 pass
        426 |         for item in prog.iterdir():
  ```
- **строка 239** — except: pass — тихое подавление ошибок
  ```
        237 |                 try:
        238 |                     z.write(str(fp), fp.relative_to(src))
  >>>   239 |                 except Exception:
        240 |                     pass
        241 |     prune_old_backups(keep=3)
  ```

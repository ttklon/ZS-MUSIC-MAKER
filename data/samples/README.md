# Сэмпловый банк (data/samples)

Банк — фундамент «живого» звука: пока он пуст, `modules/beat/drums.py`
синтезирует барабаны и честно отчитывается `drum_engine.status = FALLBACK`.

## Как добавить сэмплы

1. Кладите файлы по папкам инструментов: `kick/`, `snare/`, `clap/`, `hat/`,
   `open_hat/`, `808/`, `bass/`, `melody/`, `fx/`, `foley/`.
2. Только **лицензионно чистые** источники: CC0-1.0, public domain,
   CC-BY (с указанием автора). Всё остальное банк отвергнет.
3. На каждый файл — запись в `manifest.json`:

```json
{"file": "kick/kick_01.wav", "license": "CC0-1.0",
 "source": "https://example.org/pack", "sha256": "<sha256 файла>",
 "velocity": 0.9, "round_robin": 0, "tuning_hz": 55.0}
```

* `velocity` — слой громкости (0.3 … 1.0): на каждый инструмент полезно 3 слоя;
* `round_robin` — номер варианта: один и тот же удар не должен звучать дважды;
* `tuning_hz` — основной тон (для кика/808), чтобы бит попадал в тональность.

## Проверка

```bash
python tools/samples_audit.py          # лицензии, sha256, покрытие инструментов
python -m app.audio.samples            # краткий отчёт возможностей
```

Аудит пишет отчёт в `output/samples_audit.json`; для релиза — `release/licenses.txt`.

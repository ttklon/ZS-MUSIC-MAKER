# Сэмпловый банк (data/samples)

Банк — фундамент «живого» звука. Здесь лежат 32 CC0 one-shot'а: реальные удары
Roland TR-808 (набор Майкла Фишера) и три набора BOOCHI44 (hard trap / bounce /
vintage). Движок бита берёт их напрямую, поэтому в отчёте стоит
`drum_engine = sample_bank+procedural` / `REAL_PASS`; синтез также используется
для басовых нот, саб-хвостов, импактов и перкуссии.

| Инструмент | Файлов | Что внутри |
|---|---:|---|
| `kick` | 8 | TR-808 (3 настройки) + hard trap ×2, bounce ×2, vintage ×2 |
| `snare` | 9 | TR-808 ×3 + hard trap ×2, bounce ×2, vintage ×2 |
| `clap` | 3 | TR-808, hard trap, vintage |
| `hat` | 2 | TR-808 closed, vintage closed |
| `open_hat` | 4 | TR-808 ×3 (короткий/средний/длинный), bounce |
| `808` | 6 | TR-808 бас ×2, hard trap sub/dist, bounce, vintage lofi |

Полный список файлов с источниками — в [ATTRIBUTION.md](ATTRIBUTION.md),
машиночитаемое описание — в `manifest.json`.

## Пересборка банка

Банк собирается скриптом, а не руками: так он воспроизводим и проверяем.

```bash
# 1. скачать паки (в любой каталог вне репозитория, например output/_samples_src)
#    github.com/tidalcycles/sounds-tr808-fischer  (CC0-1.0)
#    github.com/Boochi44/free-drum-samples        (CC0-1.0)
python tools/import_samples.py --source output/_samples_src --dry-run
python tools/import_samples.py --source output/_samples_src
python tools/samples_audit.py          # лицензии, sha256, покрытие
```

Импорт детерминированный: моно, 44.1 кГц, PCM-16, нормализация до −1 dBFS,
обрезанный шумовой хвост, дубли по SHA-256 выбрасываются, для `kick`/`808`
измеряется основной тон (`tuning_hz`) — по нему движок подстраивает удар в
тональность трека.

## Как добавить свои сэмплы

1. Файлы — по папкам инструментов: `kick/`, `snare/`, `clap/`, `hat/`,
   `open_hat/`, `808/`, `bass/`, `melody/`, `fx/`, `foley/`.
2. Только **лицензионно чистые** источники: CC0-1.0, public domain, CC-BY
   (с указанием автора). Всё остальное банк отвергнет и напишет в аудите.
3. Запись в `manifest.json`:

```json
{"file": "kick/kick_01.wav", "license": "CC0-1.0",
 "source": "https://example.org/pack", "sha256": "<sha256 файла>",
 "velocity": 0.9, "round_robin": 0, "tuning_hz": 55.0}
```

* `velocity` — слой громкости (0.3 … 1.0), нужен для акустических записей;
* `round_robin` — номер варианта; при случайном выборе повторы возможны;
* `tuning_hz` — основной тон (кик/808), чтобы низ не «спорил» с тональностью.

### Про velocity-слои

У драм-машины громкость удара — это линейный гейн, отдельных записей на каждый
уровень не существует. Такой банк объявляет `"velocity_mode": "engine-gain"`
(громкость применяет `modules/beat/voices.py`), и аудит не требует от него
трёх слоёв — иначе он заставлял бы делать фальшивые дубли одного и того же
удара. Для акустических записей (`"velocity_mode": "layers"`, значение по
умолчанию) требование ≥3 слоёв и ≥2 вариантов остаётся в силе.

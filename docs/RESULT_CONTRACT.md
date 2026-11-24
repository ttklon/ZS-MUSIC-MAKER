# Результат, стадия и аппаратная готовность: разные контракты

Пакеты T0011–T0040. Эти изменения не создают singing backend и не исправляют
передачу рецепта в HitFactory. Они запрещают называть доказанным то, что не проверено.

## 1. Типы содержимого

`app/pipeline/result.py` различает:

| kind | Что означает | Минимальное происхождение |
|---|---|---|
| instrumental | инструментал | music_present |
| speech_draft | речевой черновик | speech_present |
| own_vocal_song | музыка со своей спетой записью | music_present, vocal_mixed, own_recording, timing_checked и vocal_method=recorded_singing |
| generated_singing | автоматически спетая песня | music_present, vocal_mixed, lyrics_applied, pitch_text_aligned и vocal_method=singing |
| unverified_audio | валидный файл неизвестного состава | нет достаточных сведений о содержимом |

`requested_kind` должен совпасть с полученным kind. Agent-hit, обещающий песню, передаёт
`requested_kind="generated_singing"` в проверку явно. Producer не может
переопределить этот запрос своим requested_kind и понизить его до «успешного
инструментала». Другие технические клиенты могут явно запросить иной тип. Интерфейс выбора режима — отдельная задача.

### Артефакт

Проверяется настоящий файл через soundfile: декодирование блоками, длительность
0.1–1800 с, 1–2 канала, конечные значения, ненулевая амплитуда, отсутствие выхода
за цифровой диапазон, SHA-256 и размер. Это техническая валидация, не распознавание
музыки/пения. Более длинные и многоканальные проекты этим контрактом пока не приняты.
Валидация потоковая, но не является защитой от произвольного недоверенного декодера
или одновременно изменяемого файла; безопасный импорт/изоляция остаются в плане.

### Происхождение

`render_evidence`: schema=1, kind, master_sha256, engine, revision, checks и для
пения vocal_method. Хэш должен совпасть с реально прочитанным мастером. Это
заявление доверенного producer о сделанных проверках, **не независимое прослушивание,
не криптографическая подпись и не автоматическое доказательство качества**.
Текущие музыкальные producer ещё не выдают принятый manifest. Поэтому существующий
WAV без происхождения остаётся degraded/unverified_audio, даже при hit_score=100.
Не добавлять фиктивные checks=true ради зелёного результата.

`quality_accepted` всегда false на этом этапе. Принятие качества и прослушивание —
отдельные пакеты. Тестовые WAV — синусоидальные PCM-фикстуры, не демо нейромузыки.

## 2. Статус результата

- failed: нет корректного аудиофайла;
- canceled: отменённый результат не принимается, даже если файл остался;
- degraded: аудио читается, но тип, происхождение или обязательные части не подтверждены;
- success: технический контракт типа и происхождения выполнен, обязательных блокировок нет.

success не означает коммерческий HIT или хорошее звучание. Agent CLI отдаёт result
в JSON и ненулевой код для непринятого результата. Renderer читает schema/status/
succeeded, а не старое слово HIT. narrate больше не пишет «Трек готов» только по пути.

### Приоритет исполнения над manifest

Даже полный manifest с текущим хэшем не отменяет failed/canceled/blocked/degraded
outcome, провал обязательной стадии, QA failure, dry-run/only, synthetic/placeholder
или явный отказ producer. Проверяются также сведения вложенного hit. Отмена
завершает проверку без открытия оставшегося аудио. Явные voice.ok=false,
empty/silent и речевой источник TTS/Silero/XTTS не могут противоречить заявленному
пению; для осознанного инструментала вокал не требуется.

schema provenance — целое 1 (не true), engine/revision — непустые строки.
Неверный явный render_evidence не заменяется молча вложенным manifest.

Окно дополнительно требует совпадения requested_kind/kind с собственным запросом,
valid=true артефакта, совпадающего пути и SHA-256, пустых reasons/blocked и успешной
задачи. Agent producer различает master_reported (заявлен путь), artifact_available
(файл действительно прошёл проверку) и ok (принят весь запрошенный результат).
Строка прогресса «Прогон завершён» не обещает готовую песню.

Renderer не декодирует и не прослушивает файл независимо: он проверяет
согласованность типизированного отчёта, а не доказывает музыку по JSON.

## 3. Статус задачи/стадии

`app/pipeline/outcome.py`: success, degraded, blocked, failed, canceled.
Старые StageStatus OK/FALLBACK/BLOCKED/FAILED сохраняются; добавлен CANCELED.

- required по умолчанию true;
- failed обязательной стадии сильнее canceled, затем blocked, degraded, success;
- провал необязательной обложки даёт degraded, а не успех всего прогона;
- пустой список не даёт success;
- required_names позволяет явно перечислить ожидаемые стадии: пропущенная становится blocked;
- placeholder/synthetic/dry_run не становятся каноническим success;
- `required_names`/`not_requested_names` и контейнер стадий проверяются как входной
  контракт: повреждённый список или пустое/нестроковое имя даёт `failed`, а не
  исключение или успех;
- malformed declared outcome/reason list также fail-closed; отменённая повторная
  попытка получает `canceled`, не читает stale master и сохраняет предыдущий файл;
  повторный stage outcome также не мутирует предыдущую запись стадий;
- QA failure делает report outcome failed, частичный/пробный прогон — degraded.

Legacy StageResult.ok означает «не FAILED и не CANCELED»; BLOCKED может иметь ok=true.
Потребитель не должен трактовать это как готовый продукт. Сохраняется старый percent
с меткой percent_kind=legacy_stage_accounting_not_product_readiness и старый verdict
для совместимости. Канонический outcome добавлен в summarize и finalize_report.

### Вход/выход и пример обязательной стадии (T0031)

Вход `stage_outcome(stages, required_names=..., not_requested_names=...)` — список
результатов с именем, статусом исполнителя и необязательными `required`/`reason`;
список `required_names` задаёт ожидания вызывающей стороны и сильнее флага стадии.
Выход schema 1 — типизированный общий статус, `succeeded`, причины и нормализованный
список стадий. Пропущенное имя из `required_names` создаётся как `blocked`; пустой
список не даёт успеха. Это stage contract, а не доказательство наличия или качества
песни.

```python
from app.pipeline.outcome import stage_outcome

result = stage_outcome(
    [{"name": "music", "status": "OK"}],
    required_names=["music", "voice"],
)
# result['status'] == 'blocked'; result['succeeded'] is False
# result['stages'] содержит music: success и voice: blocked.
```

Канонический фрагмент результата:

```json
{
  "schema": 1,
  "status": "blocked",
  "succeeded": false,
  "reasons": ["voice: Обязательная стадия не выполнена"],
  "stages": [
    {"name": "music", "status": "success", "required": true, "reason": ""},
    {"name": "voice", "status": "blocked", "required": true,
     "reason": "Обязательная стадия не выполнена"}
  ],
  "song_verified": false
}
```

Старый `ok`/`verdict`/`percent` продолжает сериализоваться для миграции потребителей,
но не может повысить этот результат до успеха. Проверка автоматизируется в
`tests/test_task_outcome_contract.py::test_missing_required_stage_is_explicitly_blocked`.

### Решение и откат (T0033)

**Выбор:** schema-1 `outcome` добавляется как канонический результат рядом со
старыми полями. Он строится из явных статусов стадий; список `required_names`
принадлежит вызывающему сценарию и не может быть ослаблен исполнителем. Legacy
`ok`/`verdict`/`percent` сохраняются только как совместимые projections.

Рассмотренные альтернативы:

- Переопределить старое `StageResult.ok`, чтобы `BLOCKED` стал `False`: не выбрано,
  потому что `ok` исторически означает отсутствие аварийного завершения и его
  потребляют legacy-клиенты; это смешало бы «не упало» с «результат готов».
- Решать готовность по `verdict` или `percent`: отклонено — `PASS_BLOCKED` остаётся
  legacy-меткой, а процент отражает выполненные стадии, не готовность продукта.
- Создать отдельный второй формат результата в CLI и UI: отклонено — копии
  разойдутся; все новые потребители должны читать общий typed outcome.
- Автоматически делать отсутствующую стадию необязательной: отклонено — ожидания
  сценария задаёт `required_names`, неизвестность или пропуск не дают успеха.

**Совместимость и зависимости:** формат аддитивный; старые поля и verdict пока
сериализуются. Основные точки интеграции — `app/pipeline/stage.py`,
`app/pipeline/outcome.py`, `app/core/report_finalize.py` и публичные CLI/UI
адаптеры. Миграция всех legacy AI/God/async entrypoints остаётся отдельным
приёмочным остатком T0039–T0040; наличие общей функции не значит, что все клиенты
уже используют её.

**План отката:** если новый сериализатор ломает конкретный старый потребитель,
откатывать только его адаптер на совместимые поля и сохранять typed outcome в
отчёте. Пока потребитель не мигрирован, он не может объявлять полный продукт по
`ok`, `PASS_BLOCKED` или проценту; при конфликте/неизвестном outcome новый путь
должен вернуть failed/blocked, а не успешный результат. Не удалять required-stage
guards и отрицательную регрессию; повторно включать адаптер только после теста
пропущенной обязательной стадии и его Windows проверки.

### Интеграция в общие входы (T0035)

- Classic runner: `app/core/orchestrator.py` собирает общий `summarize`; финализация
  добавляет `outcome` через `app/core/stage_request.py::attach_request_outcome`,
  где `required_names`/`not_requested_names` выводятся из нормализованного recipe,
  а не из отчёта исполнителя.
- Classic CLI: `app/cli/pipeline.py` принимает код возврата только из канонического
  `outcome.succeeded`; при старом `PASS_BLOCKED` или отсутствующем вердикте без
  outcome возвращается ненулевой код.
- Agent CLI: `app/cli/agent_task.py` применяет `assess_result` к исходному запросу,
  публикует typed `done.ok` и возвращает 0 только для принятого результата; одного
  `master_path` недостаточно.
- God/async adapters формируют общий outcome; их полная миграция и аудит остальных
  публичных путей всё ещё проверяются T0039–T0040.

Регрессия без model claims:
`tests/test_classic_request_scope.py`, `tests/test_cli_pipeline_handlers.py`,
`tests/test_orchestrator_adapters.py`, `tests/test_result_acceptance_contract.py`,
`tests/test_agent_guide.py` и `tests/test_runtime_orchestrator_result_summary.py`.
Фикстуры проверяют статус/код возврата, а не настоящий render или Windows installer.

### Незавершённая миграция

Классический CLI --run использует outcome, если он предоставлен; legacy-ответы
без нового поля пока читаются прежним путём. AI/God/async, их CLI и классический finalizer уже переведены на общий outcome
в повторном проходе; приёмка остальных публичных границ остаётся предметом T0039–T0040. Поэтому общая приёмка пакета статусов T0039–
T0040 пока заблокирована: нельзя заявлять единый результат для всех входов.

## 4. Аппаратная матрица

`app/ai/profiles.py`, `tools/measure_hardware_profile.py` измеряют потоки CPU,
общую/доступную RAM и свободное место. GPU — not_measured; ноль не выдаётся за
подтверждённое отсутствие GPU. Недоступные измерения — null + ошибка.

Профили windows_cpu/windows_cuda/windows_amd пока unverified, ни одного полного
профиля продукта не принято. Это не новая рекомендация «достаточно X ГБ».

`preflight_resources` сравнивает доступные ресурсы с явно переданным бюджетом
конкретного backend. Нет бюджета/измерения, NaN/Inf, отрицательные значения и
недостаток ресурсов дают allowed=false. Достаток RAM/диска не доказывает inference,
не гарантирует отсутствие OOM и не проверяет GPU. Старые аппаратные эвристики
движков не заменены этим диагностическим API.

Инвентарь включён в CLI health и отдельный read-only инструмент. Ничего не
скачивается и не удаляется. GPU, микрофон, реальные время/RAM/VRAM inference и
минимальные требования ещё не приняты — T0029–T0030 остаются blocked.

## 5. Проверки и воспроизведение

```sh
python -m pytest tests/test_result_acceptance_contract.py tests/test_task_outcome_contract.py tests/test_hardware_profiles_contract.py -q
python tools/measure_hardware_profile.py --out output/contracts/hardware.json
node --test desktop/test/creation.test.js
```

Windows workflow product-plan.yml запускает эти проверки на настоящих PCM WAV,
измеряет runner и отдельно проверяет упакованное окно. На текущем source
`8160085c9b362112ac14ff47323ddeb27bd00a60` Product plan run
[45310945889](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45310945889)
завершился SUCCESS всеми 3 jobs (включая clean NSIS install и
`result-outcome-hardware-contracts`); [Windows neural run
45310945817](https://github.com/ttklon/ZS-MUSIC-MAKER/actions/runs/45310945817)
тоже завершился SUCCESS, 120 hardware/preflight/RVC tests passed. Ни один из этих
тестов не является генерацией песни или прослушиванием и они не принимают полный
CPU/CUDA/AMD product profile. Измерения и границы зафиксированы в
`docs/plan/evidence/restart-windows-current-head-8160085-20261124.json`.

## Узкий live producer инструментала

`app/core/instrumental_evidence.py` выдаёт `render_evidence.kind=instrumental`
только из canonical finalization для явного procedural / voice off / texture off /
stems off запроса с успешным caller-scoped outcome. Legacy report автоматически
не дообогащается; generic validator по-прежнему не доверяет producer request_scope.

Подтверждение — **provenance доверенного исполнителя**, не независимое
распознавание музыки. Проверяются уникальные успешные live stage outputs,
structured beat constructor, instrumental mix без вокала с пройденными mix gates,
master/polish, валидные локальные stereo WAV, согласованная длительность.
Микшер записывает fingerprint beat до/после обработки и своего выхода; producer
сверяет их с текущими beat/mix и integrity hash финального master. Подмена файла,
отсутствующий/некорректный hash, fallback/reuse/ошибка не дают нового manifest.
При повторной неуспешной проверке старый manifest этого producer удаляется.

В manifest: engine `classic_procedural_instrumental`, revision
`classic-procedural-chain-v1`, `checks={music_present:true}`, master SHA и
SHA-256 трёх assets. Запрошенный процедурный синтез — настоящий результат
синтезатора, не заглушка neural backend. Он не получает vocal_method/singing
checks. `quality_accepted=false` сохраняется, включая случай рекомендаций QA
по доработке музыки. Нет заявления о лицензии, качестве, пении или GPU.

Хеши не являются подписью и не защищают от недоверенного производителя,
вредоносного изменения кода или враждебных одновременных замен файлов.
Независимая аттестация/изоляция — отдельная работа.

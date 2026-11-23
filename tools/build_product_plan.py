"""Build a reproducible 1000-task backlog from 100 domain-specific workpackages.

Does not execute tasks or claim completion. Uses only the Python standard library.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'plan'
PHASES = [
    ('Входной контракт', 'Зафиксировать входы, выходы, границы ответственности и совместимость',
     'Спецификация с примерами валидного запроса и ожидаемого результата'),
    ('Воспроизведение текущего разрыва', 'Построить минимальный сценарий, показывающий текущее ограничение; записать baseline без исправлений',
     'Воспроизводимый сценарий с версиями, входами и наблюдаемым исходом'),
    ('Проектирование решения', 'Выбрать минимальный поддерживаемый способ реализации, перечислить альтернативы, зависимости и план отката',
     'Техническое решение с обоснованием и закрытыми вопросами совместимости'),
    ('Основная реализация', 'Реализовать целевой результат в каноническом слое, не создавая параллельный несовместимый путь',
     'Изменение кода или нормативного документа с прослеживаемыми входами и выходами'),
    ('Интеграция в продукт', 'Подключить результат к установленному приложению и общему рецепту; убрать недостижимые действия и дублирование',
     'Проверяемый пользовательский путь до результата через поддерживаемую точку входа'),
    ('Отказы и восстановление', 'Обработать конкретный риск пакета, отмену операции и повтор без потери предыдущих данных',
     'Негативные сценарии с наблюдаемой причиной отказа и проверенным восстановлением'),
    ('Автоматическая регрессия', 'Добавить позитивную и негативную регрессию на правильном уровне; отличать двойники от реального backend',
     'Исполняемые тесты с проверкой содержимого результата, а не только отсутствия исключения'),
    ('Проверка на целевой платформе', 'Проверить изменение на Windows через runner; для документов проверить соответствие установленному продукту',
     'Ссылка на job и отчёт; для недоступного железа отдельная незакрытая проверка'),
    ('Приёмка по наблюдаемому результату', 'Проверить доменный критерий пакета независимо от реализации; сохранить измерения и исключить ложный успех',
     'Протокол приёмки с входами, версиями, фактическим результатом и ограничениями'),
    ('Закрытие и сопровождение', 'Обновить инструкции, миграции и реестр возможностей; закрыть пакет только после всех доказательств',
     'Связанные изменения, тесты и отчёты; согласованный статус поддержки без открытого блокера'),
]
GROUP_DEPS = {0: [], 1: [1, 4, 10], 2: [17, 19, 20], 3: [21, 22, 26, 27, 30],
              4: [11, 12, 13, 14, 17, 18, 21], 5: [11, 20, 32, 33],
              6: [11, 20, 31, 35], 7: [11, 20, 51, 65],
              8: [11, 12, 17, 18], 9: [10, 19, 30, 40, 50, 60, 70, 80, 90]}
P0 = {1, 2, 4, 5, 8, 10, 11, 12, 13, 14, 15, 17, 19, 20, 21, 22,
      24, 26, 27, 28, 30, 32, 33, 40, 41, 42, 43, 45, 46, 47, 48,
      50, 61, 62, 65, 69, 71, 72, 74, 75, 80, 81, 82, 85, 91, 92, 95, 96, 100}


def workpackages() -> list[dict]:
    rows = [line.split('|') for line in (BASE / 'workpackages.tsv').read_text(encoding='utf-8').splitlines()
            if line and not line.startswith('#')]
    assert len(rows) == 100 and all(len(row) == 6 for row in rows)
    result = []
    for number, (group, title, paths, target, acceptance, failure) in enumerate(rows, 1):
        deps = GROUP_DEPS[(number - 1) // 10].copy()
        if number == 100:
            deps += list(range(91, 100))
        result.append(dict(number=number, group=group, title=title, paths=paths.split(';'),
                           target=target, acceptance=acceptance, failure=failure,
                           depends_on_packages=deps, priority='P0' if number in P0 else 'P1', status='planned'))
    return result


def tasks_for(packages: list[dict]) -> list[dict]:
    tasks = []
    for package in packages:
        first = (package['number'] - 1) * 10 + 1
        for offset, (phase, action, artifact) in enumerate(PHASES):
            number = first + offset
            deps = [f'T{number - 1:04}'] if offset else [f'T{p * 10:04}' for p in package['depends_on_packages']]
            tasks.append(dict(id=f'T{number:04}', package=package['number'], phase=phase,
                title=f"{package['title']}: {phase.lower()}", status='planned',
                priority=package['priority'], depends_on=deps, paths=package['paths'],
                action=f"{action}. Предмет работы: {package['target']}.",
                artifact=artifact, acceptance=package['acceptance'], risk=package['failure'],
                evidence=[], completion_rule='Изменение + проверка + сохранённое доказательство; наличие файла или зелёный import недостаточны.'))
    return tasks


def render(packages: list[dict], tasks: list[dict]) -> str:
    lines = ['# План доведения продукта: 1000 проверяемых шагов', '',
        '> Статус: план, а не выполненная работа. Основание: аудит bc60d9b (42.0.39).',
        '> Ровно 100 предметных пакетов по 10 стадий выполнения. Каждый шаг имеет самостоятельный результат.',
        '> Все задачи первоначально planned; существующие функции не считаются принятыми без повторной проверки.', '',
        '## Как читать и выполнять', '',
        '- Обзор, доказанные разрывы и границы аудита: [AUDIT.md](AUDIT.md).',
        '- Порядок, определение готовности и ворота: [EXECUTION.md](EXECUTION.md).',
        '- Машиночитаемый реестр: [backlog.json](backlog.json). При выполнении статус и evidence меняются в нём.',
        '- P0 означает блокер целевого продукта, P1 — обязательную полноту согласованного объёма, не косметику.',
        '- Пакеты опциональных движков допускают решение об исключении из обещаний, но не фиктивное done.',
        '- Шаги 8–9 требуют настоящего оборудования/прослушивания там, где Windows CPU runner недостаточен.',
        '- Генератор создаёт первоначальный план; после начала выполнения не перезапускать его поверх статусов.', '',
        '## Карта волн', '', '| Волна | Шаги | Область |', '|---|---|---|']
    for g in range(10):
        lines.append(f"| {g+1} | T{g*100+1:04}–T{(g+1)*100:04} | {packages[g*10]['group']} |")
    for package in packages:
        n = package['number']
        lines += ['', f"## Пакет {n:03}. {package['title']} [{package['priority']}]", '',
            f"**Область:** {package['group']}. **Целевой результат:** {package['target']}.",
            '**Файлы/подсистемы:** ' + ', '.join('`' + p + '`' for p in package['paths']) + '.',
            '**Предшествующие пакеты:** ' + (', '.join(str(p) for p in package['depends_on_packages']) or 'нет') + '.', '']
        for task in tasks[(n-1)*10:n*10]:
            lines += [f"### {task['id']}. {task['title']}", '', f"- **Действие:** {task['action']}",
                f"- **Выход:** {task['artifact']}; привязать к `{task['id']}`.",
                f"- **Критерий предметной приёмки:** {task['acceptance']}.",
                f"- **Обязательный риск для проверки:** {task['risk']}.",
                '- **Зависимости:** ' + (', '.join(task['depends_on']) or 'нет') + '.',
                '- **Статус:** planned. **Доказательства:** ещё не приложены.', '']
    return '\n'.join(lines).rstrip() + '\n'


def validate(data: dict) -> None:
    tasks = data['tasks']
    assert len(data['packages']) == 100 and len(tasks) == 1000
    ids = {task['id']: i for i, task in enumerate(tasks)}
    assert len(ids) == 1000
    for i, task in enumerate(tasks):
        assert task['id'] == f'T{i+1:04}'
        assert task['status'] in {'planned', 'in_progress', 'blocked', 'verified', 'out_of_scope'}
        assert all(dep in ids and ids[dep] < i for dep in task['depends_on'])
        if task['status'] == 'verified':
            assert task['evidence'], f"Missing evidence: {task['id']}"
    assert all((ROOT / path).exists() for p in data['packages'] for path in p['paths'])


def main() -> None:
    import sys
    if '--check' in sys.argv:
        data = json.loads((BASE / 'backlog.json').read_text(encoding='utf-8'))
        validate(data)
        assert (BASE / 'PLAN_1000.md').read_text(encoding='utf-8').count('\n### T') == 1000
        print('OK: 100 packages, 1000 unique ordered tasks, valid paths and acyclic dependencies')
        return
    if (BASE / 'backlog.json').exists():
        raise SystemExit('Backlog exists; refusing to overwrite task statuses. Use --check.')
    packages = workpackages()
    data = dict(schema_version=1, baseline_commit='bc60d9bda47c30fab5c8a2c38cbe84930a075095',
                baseline_version='42.0.39', packages=packages, tasks=tasks_for(packages))
    validate(data)
    (BASE / 'backlog.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (BASE / 'PLAN_1000.md').write_text(render(packages, data['tasks']), encoding='utf-8')
    print('Created 1000 planned tasks; none marked complete.')


if __name__ == '__main__':
    main()

# Идентификаторы `tests/test_ast_dead_imports.py`

## Имена (ast.Name) (уникальных: 14)

| Имя | Использований |
|-----|--------------:|
| `f` | 12 |
| `dead` | 8 |
| `names` | 8 |
| `n` | 6 |
| `tmp_path` | 4 |
| `scan_file` | 4 |
| `report` | 3 |
| `_` | 3 |
| `str` | 1 |
| `scan_all` | 1 |
| `DEFAULT_DIRS` | 1 |
| `sys` | 1 |
| `Path` | 1 |
| `__file__` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 7)

| Имя | Использований |
|-----|--------------:|
| `write_text` | 4 |
| `scan_file` | 4 |
| `insert` | 1 |
| `str` | 1 |
| `scan_all` | 1 |
| `resolve` | 1 |
| `Path` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 5)

| Имя | Использований |
|-----|--------------:|
| `write_text` | 4 |
| `insert` | 1 |
| `path` | 1 |
| `parents` | 1 |
| `resolve` | 1 |

## Строковые литералы (уникальных: 11)

| Имя | Использований |
|-----|--------------:|
| `m.py` | 4 |
| `utf-8` | 4 |
| `os` | 3 |
| `json` | 2 |
| `ZS Music Maker — AST dead-imports аудит (ШАГ 010).` | 1 |
| `import os\nimport json\nx = json.dumps({})\n` | 1 |
| `import os  # noqa: F401\nx = 1\n` | 1 |
| `import os\np = os.path.join('a', 'b')\nimport json\n` | 1 |
| `import os, sys\nx = 1\n` | 1 |
| `dead imports found: ` | 1 |
| `sys` | 1 |

## Числовые литералы (уникальных: 2)

| Имя | Использований |
|-----|--------------:|
| `0` | 1 |
| `1` | 1 |
# Идентификаторы `app/core/isrc.py`

## Имена (ast.Name) (уникальных: 36)

| Имя | Использований |
|-----|--------------:|
| `str` | 22 |
| `s` | 13 |
| `isrc` | 10 |
| `meta` | 8 |
| `core` | 4 |
| `existing` | 4 |
| `reg` | 4 |
| `seq` | 4 |
| `nnnnn` | 4 |
| `int` | 4 |
| `title` | 3 |
| `is_valid_isrc` | 3 |
| `yy` | 3 |
| `Optional` | 3 |
| `_ISRC_RE` | 2 |
| `bool` | 2 |
| `h` | 2 |
| `n` | 2 |
| `cc` | 2 |
| `yy_source` | 2 |
| `re` | 2 |
| `base_title` | 2 |
| `base_artist` | 2 |
| `dict` | 2 |
| `year` | 2 |
| `TypeError` | 2 |
| `ValueError` | 2 |
| `_short_seq_from_title` | 2 |
| `Any` | 2 |
| `time` | 2 |
| `generate_isrc` | 1 |
| `fallback` | 1 |
| `_normalize_existing` | 1 |
| `hashlib` | 1 |
| `registrant` | 1 |
| `country_code` | 1 |

## Вызванные функции/методы (ast.Call) (уникальных: 20)

| Имя | Использований |
|-----|--------------:|
| `str` | 9 |
| `get` | 7 |
| `upper` | 5 |
| `replace` | 4 |
| `is_valid_isrc` | 3 |
| `int` | 3 |
| `ljust` | 2 |
| `startswith` | 2 |
| `_short_seq_from_title` | 2 |
| `endswith` | 2 |
| `gmtime` | 2 |
| `compile` | 1 |
| `strip` | 1 |
| `hexdigest` | 1 |
| `generate_isrc` | 1 |
| `match` | 1 |
| `_normalize_existing` | 1 |
| `sha256` | 1 |
| `encode` | 1 |
| `sub` | 1 |

## Обращения к атрибутам (.attr) (уникальных: 15)

| Имя | Использований |
|-----|--------------:|
| `get` | 7 |
| `upper` | 5 |
| `replace` | 4 |
| `ljust` | 2 |
| `startswith` | 2 |
| `tm_year` | 2 |
| `endswith` | 2 |
| `gmtime` | 2 |
| `compile` | 1 |
| `strip` | 1 |
| `hexdigest` | 1 |
| `match` | 1 |
| `sha256` | 1 |
| `encode` | 1 |
| `sub` | 1 |

## Строковые литералы (уникальных: 30)

| Имя | Использований |
|-----|--------------:|
| `` | 10 |
| `-` | 9 |
| `XX` | 2 |
| `00000` | 2 |
| `00` | 2 |
| `05d` | 2 |
| `^[A-Z]{2}-?[A-Z0-9]{3}-?\d{2}-?\d{5}$` | 1 |
| `True если строка — валидный ISRC по ISO 3901.` | 1 |
| `True если это XX-XXX-00-00000 / пусто / любой очевидный placeholder.` | 1 |
| `5-значный детерминированный NNNNN из sha256(title\|artist).` | 1 |
| `RU` | 1 |
| `ZSM` | 1 |
| `\n    Возвращает валидный ISRC или fallback.\n    fallback по-умолчанию — пустая строка (никогда не XX-XXX-00-00000).\n ` | 1 |
| ` ` | 1 |
| `zs_untitled` | 1 |
| `X` | 1 |
| `Z` | 1 |
| `release_seq` | 1 |
| `XXXXX` | 1 |
| `isrc` | 1 |
| `year` | 1 |
| `\|` | 1 |
| `02d` | 1 |
| `utf-8` | 1 |
| `[^A-Z0-9]` | 1 |
| `title` | 1 |
| `artist` | 1 |
| `replace` | 1 |
| `label_isrc_code` | 1 |
| `country` | 1 |

## Числовые литералы (уникальных: 11)

| Имя | Использований |
|-----|--------------:|
| `2` | 4 |
| `5` | 4 |
| `7` | 4 |
| `False` | 3 |
| `True` | 2 |
| `100000` | 2 |
| `3` | 2 |
| `100` | 2 |
| `16` | 1 |
| `6` | 1 |
| `12` | 1 |
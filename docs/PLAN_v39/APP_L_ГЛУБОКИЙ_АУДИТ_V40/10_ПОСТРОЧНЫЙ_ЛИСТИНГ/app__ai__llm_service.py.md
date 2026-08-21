# ПОСТРОЧНЫЙ ЛИСТИНГ: `app/ai/llm_service.py`

**Всего строк:** 45

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 14 | 31.1 |
| return | 9 | 20.0 |
| try_block | 8 | 17.8 |
| blank | 4 | 8.9 |
| import | 3 | 6.7 |
| branch | 3 | 6.7 |
| def | 2 | 4.4 |
| comment | 1 | 2.2 |
| docstring | 1 | 2.2 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """ZS Music Maker - app/ai/llm_service.py (v38): обёртка над llama-cpp."""
    3 [import    ] from __future__ import annotations
    4 [import    ] import json
    5 [import    ] from typing import Any, Optional
    6 [blank     ] 
    7 [blank     ] 
    8 [def       ] def complete(handle: Any, system: str, user: str, max_tokens: int = 1024,
    9 [code      ]              temperature: float = 0.85, top_p: float = 0.95,
   10 [code      ]              repeat_penalty: float = 1.1) -> str:
   11 [branch    ]     if handle is None:
   12 [return    ]         return ""
   13 [try_block ]     try:
   14 [code      ]         res = handle.create_chat_completion(
   15 [code      ]             messages=[{"role": "system", "content": system},
   16 [code      ]                       {"role": "user", "content": user}],
   17 [code      ]             max_tokens=max_tokens, temperature=temperature, top_p=top_p,
   18 [code      ]             repeat_penalty=repeat_penalty)
   19 [return    ]         return res["choices"][0]["message"]["content"].strip()
   20 [try_block ]     except Exception:
   21 [try_block ]         try:
   22 [code      ]             prompt = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"
   23 [code      ]             res = handle(prompt, max_tokens=max_tokens, temperature=temperature,
   24 [code      ]                          top_p=top_p, repeat_penalty=repeat_penalty,
   25 [code      ]                          stop=["<|user|>", "<|system|>"])
   26 [return    ]             return res["choices"][0]["text"].strip()
   27 [try_block ]         except Exception:
   28 [return    ]             return ""
   29 [blank     ] 
   30 [blank     ] 
   31 [def       ] def complete_json(handle: Any, system: str, user: str, max_tokens: int = 2048,
   32 [code      ]                   temperature: float = 0.4) -> Optional[dict]:
   33 [code      ]     txt = complete(handle, system, user, max_tokens=max_tokens, temperature=temperature)
   34 [branch    ]     if not txt:
   35 [return    ]         return None
   36 [code      ]     s, e = txt.find("{"), txt.rfind("}")
   37 [branch    ]     if s < 0 or e <= s:
   38 [return    ]         return None
   39 [try_block ]     try:
   40 [return    ]         return json.loads(txt[s:e + 1])
   41 [try_block ]     except Exception:
   42 [try_block ]         try:
   43 [return    ]             return json.loads(txt[s:e + 1].replace("'", '"'))
   44 [try_block ]         except Exception:
   45 [return    ]             return None
```
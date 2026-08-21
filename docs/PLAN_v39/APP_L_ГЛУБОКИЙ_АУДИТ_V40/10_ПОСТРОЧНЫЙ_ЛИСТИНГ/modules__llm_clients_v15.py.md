# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/llm_clients_v15.py`

**Всего строк:** 580

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 356 | 61.4 |
| blank | 63 | 10.9 |
| return | 37 | 6.4 |
| branch | 32 | 5.5 |
| try_block | 21 | 3.6 |
| docstring | 17 | 2.9 |
| comment | 16 | 2.8 |
| def | 16 | 2.8 |
| import | 14 | 2.4 |
| loop | 5 | 0.9 |
| class | 2 | 0.3 |
| raise | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v15 — modules/llm_clients_v15.py
    3 [docstring ] ==============================================================
    4 [docstring ] Единая точка для LLM-провайдеров: Ollama (локально) → OpenRouter →
    5 [docstring ] Grok (xAI) → Gemini → LOCAL_FALLBACK (шаблоны + punch-lib).
    6 [blank     ] 
    7 [docstring ] TZ раздел 9 (LLM модуль) и раздел 13 (fallback).
    8 [blank     ] 
    9 [docstring ] Ключи шифруются `cryptography.fernet` мастер-паролем; хранятся в
   10 [docstring ] `data/secrets.enc`. Ключи никогда не попадают в лог.
   11 [blank     ] 
   12 [docstring ] Публичное API:
   13 [docstring ]     LLMRouter().complete(prompt: str, system: str = "",
   14 [docstring ]                          max_tokens=512, temperature=0.8) -> dict
   15 [docstring ]         Возвращает {ok, text, provider, model, tokens, fallback_used,
   16 [docstring ]                     provider_chain: [...], error?}
   17 [docstring ] """
   18 [blank     ] 
   19 [import    ] from __future__ import annotations
   20 [blank     ] 
   21 [import    ] import base64
   22 [import    ] import json
   23 [import    ] import os
   24 [import    ] import time
   25 [import    ] from pathlib import Path
   26 [import    ] from typing import Any
   27 [blank     ] 
   28 [try_block ] try:
   29 [import    ]     import requests
   30 [blank     ] 
   31 [code      ]     HAS_REQ = True
   32 [try_block ] except Exception:
   33 [code      ]     HAS_REQ = False
   34 [blank     ] 
   35 [try_block ] try:
   36 [import    ]     from cryptography.fernet import Fernet
   37 [import    ]     from cryptography.hazmat.primitives import hashes
   38 [import    ]     from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
   39 [blank     ] 
   40 [code      ]     HAS_CRYPTO = True
   41 [try_block ] except Exception:
   42 [code      ]     HAS_CRYPTO = False
   43 [blank     ] 
   44 [blank     ] 
   45 [code      ] ROOT = Path(__file__).resolve().parents[1]
   46 [code      ] SECRETS_FILE = ROOT / "data" / "secrets.enc"
   47 [comment   ] # v22: ленивое создание (не при импорте)
   48 [blank     ] 
   49 [comment   ] # ------------------------------------------------------------ secret store
   50 [blank     ] 
   51 [blank     ] 
   52 [def       ] def _derive_key(master_password: str, salt: bytes = b"zsmm-v15-salt") -> bytes:
   53 [branch    ]     if not HAS_CRYPTO:
   54 [raise     ]         raise RuntimeError("cryptography not installed")
   55 [code      ]     kdf = PBKDF2HMAC(
   56 [code      ]         algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000
   57 [code      ]     )
   58 [return    ]     return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
   59 [blank     ] 
   60 [blank     ] 
   61 [def       ] def save_secrets(secrets: dict[str, str], master_password: str) -> bool:
   62 [branch    ]     if not HAS_CRYPTO:
   63 [return    ]         return False
   64 [code      ]     key = _derive_key(master_password)
   65 [code      ]     f = Fernet(key)
   66 [code      ]     data = f.encrypt(json.dumps(secrets, ensure_ascii=False).encode())
   67 [code      ]     SECRETS_FILE.write_bytes(data)
   68 [return    ]     return True
   69 [blank     ] 
   70 [blank     ] 
   71 [def       ] def load_secrets(master_password: str) -> dict[str, str] | None:
   72 [branch    ]     if not HAS_CRYPTO or not SECRETS_FILE.exists():
   73 [return    ]         return None
   74 [try_block ]     try:
   75 [code      ]         key = _derive_key(master_password)
   76 [code      ]         f = Fernet(key)
   77 [code      ]         data = f.decrypt(SECRETS_FILE.read_bytes())
   78 [return    ]         return json.loads(data.decode())
   79 [try_block ]     except Exception:
   80 [return    ]         return None
   81 [blank     ] 
   82 [blank     ] 
   83 [def       ] def get_keys_from_env() -> dict[str, str]:
   84 [docstring ]     """Собирает ключи из ENV (для CI / автотестов, не для UI)."""
   85 [code      ]     keys = {}
   86 [loop      ]     for env_name, key_name in (
   87 [code      ]         ("OPENROUTER_API_KEY", "openrouter"),
   88 [code      ]         ("XAI_API_KEY", "grok"),
   89 [code      ]         ("GROK_API_KEY", "grok"),
   90 [code      ]         ("GEMINI_API_KEY", "gemini"),
   91 [code      ]         ("GOOGLE_API_KEY", "gemini"),
   92 [code      ]     ):
   93 [code      ]         v = os.environ.get(env_name)
   94 [branch    ]         if v:
   95 [code      ]             keys[key_name] = v
   96 [return    ]     return keys
   97 [blank     ] 
   98 [blank     ] 
   99 [comment   ] # ----------------------------------------------------------- providers
  100 [blank     ] 
  101 [blank     ] 
  102 [class     ] class ProviderResult:
  103 [code      ]     __slots__ = ("error", "model", "ok", "provider", "raw", "text", "tokens")
  104 [blank     ] 
  105 [def       ]     def __init__(
  106 [code      ]         self, ok, text="", model="", tokens=0, provider="", error=None, raw=None
  107 [code      ]     ):
  108 [code      ]         self.ok = ok
  109 [code      ]         self.text = text
  110 [code      ]         self.model = model
  111 [code      ]         self.tokens = tokens
  112 [code      ]         self.provider = provider
  113 [code      ]         self.error = error
  114 [code      ]         self.raw = raw
  115 [blank     ] 
  116 [def       ]     def to_dict(self):
  117 [return    ]         return {
  118 [code      ]             "ok": self.ok,
  119 [code      ]             "text": self.text,
  120 [code      ]             "model": self.model,
  121 [code      ]             "tokens": self.tokens,
  122 [code      ]             "provider": self.provider,
  123 [code      ]             "error": self.error,
  124 [code      ]         }
  125 [blank     ] 
  126 [blank     ] 
  127 [def       ] def call_ollama(
  128 [code      ]     prompt: str,
  129 [code      ]     system: str = "",
  130 [code      ]     model: str = "llama3.2:3b",
  131 [code      ]     base_url: str = "http://127.0.0.1:11434",
  132 [code      ]     timeout: float = 60.0,
  133 [code      ] ) -> ProviderResult:
  134 [branch    ]     if not HAS_REQ:
  135 [return    ]         return ProviderResult(False, provider="ollama", error="requests_missing")
  136 [try_block ]     try:
  137 [code      ]         r = requests.post(
  138 [code      ]             f"{base_url}/api/generate",
  139 [code      ]             json={
  140 [code      ]                 "model": model,
  141 [code      ]                 "prompt": (system + "\n\n" + prompt).strip(),
  142 [code      ]                 "stream": False,
  143 [code      ]             },
  144 [code      ]             timeout=timeout,
  145 [code      ]         )
  146 [branch    ]         if r.status_code != 200:
  147 [return    ]             return ProviderResult(
  148 [code      ]                 False, provider="ollama", model=model, error=f"http_{r.status_code}"
  149 [code      ]             )
  150 [code      ]         j = r.json()
  151 [return    ]         return ProviderResult(
  152 [code      ]             True,
  153 [code      ]             text=j.get("response", ""),
  154 [code      ]             model=model,
  155 [code      ]             tokens=j.get("eval_count", 0),
  156 [code      ]             provider="ollama",
  157 [code      ]             raw=j,
  158 [code      ]         )
  159 [try_block ]     except requests.exceptions.ConnectionError:
  160 [return    ]         return ProviderResult(
  161 [code      ]             False, provider="ollama", model=model, error="connection_refused"
  162 [code      ]         )
  163 [try_block ]     except Exception as e:
  164 [return    ]         return ProviderResult(
  165 [code      ]             False, provider="ollama", model=model, error=type(e).__name__
  166 [code      ]         )
  167 [blank     ] 
  168 [blank     ] 
  169 [def       ] def call_openrouter(
  170 [code      ]     prompt: str,
  171 [code      ]     system: str = "",
  172 [code      ]     api_key: str = "",
  173 [code      ]     model: str = "meta-llama/llama-3.1-70b-instruct:free",
  174 [code      ]     timeout: float = 60.0,
  175 [code      ] ) -> ProviderResult:
  176 [branch    ]     if not HAS_REQ:
  177 [return    ]         return ProviderResult(False, provider="openrouter", error="requests_missing")
  178 [branch    ]     if not api_key:
  179 [return    ]         return ProviderResult(
  180 [code      ]             False, provider="openrouter", model=model, error="no_api_key"
  181 [code      ]         )
  182 [try_block ]     try:
  183 [code      ]         r = requests.post(
  184 [code      ]             "https://openrouter.ai/api/v1/chat/completions",
  185 [code      ]             headers={
  186 [code      ]                 "Authorization": f"Bearer {api_key}",
  187 [code      ]                 "Content-Type": "application/json",
  188 [code      ]             },
  189 [code      ]             json={
  190 [code      ]                 "model": model,
  191 [code      ]                 "messages": ([{"role": "system", "content": system}] if system else [])
  192 [code      ]                 + [{"role": "user", "content": prompt}],
  193 [code      ]             },
  194 [code      ]             timeout=timeout,
  195 [code      ]         )
  196 [branch    ]         if r.status_code != 200:
  197 [return    ]             return ProviderResult(
  198 [code      ]                 False, provider="openrouter", model=model, error=f"http_{r.status_code}"
  199 [code      ]             )
  200 [code      ]         j = r.json()
  201 [code      ]         text = j["choices"][0]["message"]["content"]
  202 [code      ]         tokens = j.get("usage", {}).get("total_tokens", 0)
  203 [return    ]         return ProviderResult(
  204 [code      ]             True, text=text, model=model, tokens=tokens, provider="openrouter", raw=j
  205 [code      ]         )
  206 [try_block ]     except Exception as e:
  207 [return    ]         return ProviderResult(
  208 [code      ]             False, provider="openrouter", model=model, error=type(e).__name__
  209 [code      ]         )
  210 [blank     ] 
  211 [blank     ] 
  212 [def       ] def call_grok(
  213 [code      ]     prompt: str,
  214 [code      ]     system: str = "",
  215 [code      ]     api_key: str = "",
  216 [code      ]     model: str = "grok-2-latest",
  217 [code      ]     timeout: float = 60.0,
  218 [code      ] ) -> ProviderResult:
  219 [branch    ]     if not HAS_REQ:
  220 [return    ]         return ProviderResult(False, provider="grok", error="requests_missing")
  221 [branch    ]     if not api_key:
  222 [return    ]         return ProviderResult(False, provider="grok", model=model, error="no_api_key")
  223 [try_block ]     try:
  224 [code      ]         r = requests.post(
  225 [code      ]             "https://api.x.ai/v1/chat/completions",
  226 [code      ]             headers={
  227 [code      ]                 "Authorization": f"Bearer {api_key}",
  228 [code      ]                 "Content-Type": "application/json",
  229 [code      ]             },
  230 [code      ]             json={
  231 [code      ]                 "model": model,
  232 [code      ]                 "messages": ([{"role": "system", "content": system}] if system else [])
  233 [code      ]                 + [{"role": "user", "content": prompt}],
  234 [code      ]             },
  235 [code      ]             timeout=timeout,
  236 [code      ]         )
  237 [branch    ]         if r.status_code != 200:
  238 [return    ]             return ProviderResult(
  239 [code      ]                 False, provider="grok", model=model, error=f"http_{r.status_code}"
  240 [code      ]             )
  241 [code      ]         j = r.json()
  242 [code      ]         text = j["choices"][0]["message"]["content"]
  243 [code      ]         tokens = j.get("usage", {}).get("total_tokens", 0)
  244 [return    ]         return ProviderResult(
  245 [code      ]             True, text=text, model=model, tokens=tokens, provider="grok", raw=j
  246 [code      ]         )
  247 [try_block ]     except Exception as e:
  248 [return    ]         return ProviderResult(
  249 [code      ]             False, provider="grok", model=model, error=type(e).__name__
  250 [code      ]         )
  251 [blank     ] 
  252 [blank     ] 
  253 [def       ] def call_gemini(
  254 [code      ]     prompt: str,
  255 [code      ]     system: str = "",
  256 [code      ]     api_key: str = "",
  257 [code      ]     model: str = "gemini-1.5-flash",
  258 [code      ]     timeout: float = 60.0,
  259 [code      ] ) -> ProviderResult:
  260 [branch    ]     if not HAS_REQ:
  261 [return    ]         return ProviderResult(False, provider="gemini", error="requests_missing")
  262 [branch    ]     if not api_key:
  263 [return    ]         return ProviderResult(False, provider="gemini", model=model, error="no_api_key")
  264 [try_block ]     try:
  265 [code      ]         url = (
  266 [code      ]             f"https://generativelanguage.googleapis.com/v1beta/models/"
  267 [code      ]             f"{model}:generateContent?key={api_key}"
  268 [code      ]         )
  269 [code      ]         body = {
  270 [code      ]             "contents": [
  271 [code      ]                 {
  272 [code      ]                     "role": "user",
  273 [code      ]                     "parts": [{"text": (system + "\n\n" + prompt).strip()}],
  274 [code      ]                 }
  275 [code      ]             ]
  276 [code      ]         }
  277 [code      ]         r = requests.post(url, json=body, timeout=timeout)
  278 [branch    ]         if r.status_code != 200:
  279 [return    ]             return ProviderResult(
  280 [code      ]                 False, provider="gemini", model=model, error=f"http_{r.status_code}"
  281 [code      ]             )
  282 [code      ]         j = r.json()
  283 [code      ]         text = ""
  284 [try_block ]         try:
  285 [code      ]             text = j["candidates"][0]["content"]["parts"][0]["text"]
  286 [try_block ]         except Exception:
  287 [code      ]             pass
  288 [return    ]         return ProviderResult(
  289 [code      ]             True,
  290 [code      ]             text=text,
  291 [code      ]             model=model,
  292 [code      ]             tokens=len(text.split()),
  293 [code      ]             provider="gemini",
  294 [code      ]             raw=j,
  295 [code      ]         )
  296 [try_block ]     except Exception as e:
  297 [return    ]         return ProviderResult(
  298 [code      ]             False, provider="gemini", model=model, error=type(e).__name__
  299 [code      ]         )
  300 [blank     ] 
  301 [blank     ] 
  302 [comment   ] # --------------------------------------------------------- local fallback
  303 [blank     ] 
  304 [code      ] PUNCHLINES_RU = [
  305 [code      ]     "Ночь, движ, тачка — вот моя жизнь",
  306 [code      ]     "Мы летим по трассе, город спит",
  307 [code      ]     "Клуб гудит, басы качают",
  308 [code      ]     "Танцпол горит, мы на волне",
  309 [code      ]     "Огни фар режут темноту",
  310 [code      ]     "Я не остановлюсь, пока не взорву",
  311 [code      ]     "Ставки высоки, но мы играем в свою игру",
  312 [code      ]     "Каждый удар кика — как выстрел в грудь",
  313 [code      ]     "Мы пишем историю каждой ночью",
  314 [code      ]     "Скорость — это свобода, ты чувствуешь",
  315 [code      ] ]
  316 [blank     ] 
  317 [code      ] PUNCHLINES_EN = [
  318 [code      ]     "Neon dreams and midnight lights",
  319 [code      ]     "Speeding through the empty streets",
  320 [code      ]     "Bass drops harder than my heart",
  321 [code      ]     "Dance floor's alive tonight",
  322 [code      ]     "We ride the wave until sunrise",
  323 [code      ] ]
  324 [blank     ] 
  325 [blank     ] 
  326 [def       ] def local_fallback_lyrics(
  327 [code      ]     theme: str, genre: str, language: str = "ru", n_lines: int = 16
  328 [code      ] ) -> str:
  329 [docstring ]     """Собирает шаблонный текст из punch-lib + темы + жанра."""
  330 [code      ]     pool = PUNCHLINES_RU if language == "ru" else PUNCHLINES_EN
  331 [code      ]     lines: list[str] = []
  332 [code      ]     lines.append("[intro]")
  333 [code      ]     lines.append(
  334 [code      ]         f"{theme}, {genre}, время идёт"
  335 [branch    ]         if language == "ru"
  336 [code      ]         else f"{theme}, {genre}, we're on"
  337 [code      ]     )
  338 [code      ]     lines.append("")
  339 [code      ]     lines.append("[verse 1]")
  340 [import    ]     import random
  341 [blank     ] 
  342 [code      ]     r = random.Random(hash((theme, genre, language)) & 0xFFFF)
  343 [loop      ]     for _ in range(4):
  344 [code      ]         lines.append(r.choice(pool))
  345 [code      ]     lines.append("")
  346 [code      ]     lines.append("[hook]")
  347 [loop      ]     for _ in range(4):
  348 [code      ]         lines.append(r.choice(pool))
  349 [code      ]     lines.append("")
  350 [code      ]     lines.append("[verse 2]")
  351 [loop      ]     for _ in range(4):
  352 [code      ]         lines.append(r.choice(pool))
  353 [code      ]     lines.append("")
  354 [code      ]     lines.append("[hook]")
  355 [loop      ]     for _ in range(4):
  356 [code      ]         lines.append(r.choice(pool))
  357 [return    ]     return "\n".join(lines[: n_lines + 8])
  358 [blank     ] 
  359 [blank     ] 
  360 [comment   ] # -------------------------------------------------------------- Router
  361 [blank     ] 
  362 [blank     ] 
  363 [class     ] class LLMRouter:
  364 [docstring ]     """Роутер по ТЗ 9.3: OpenRouter → Grok → Gemini → Ollama → local."""
  365 [blank     ] 
  366 [def       ]     def __init__(
  367 [code      ]         self,
  368 [code      ]         keys: dict[str, str] | None = None,
  369 [code      ]         ollama_url: str = "http://127.0.0.1:11434",
  370 [code      ]         timeout: float = 60.0,
  371 [code      ]     ):
  372 [code      ]         self.keys = keys or get_keys_from_env()
  373 [code      ]         self.ollama_url = ollama_url
  374 [code      ]         self.timeout = timeout
  375 [code      ]         self.log: list[dict[str, Any]] = []
  376 [blank     ] 
  377 [comment   ]     # v25 (P1): быстрый preflight (<1с). Раньше 4 провайдера по 8с таймауту
  378 [comment   ]     # = до 32с мёртвого простоя, если сети нет / ключей нет. Теперь один
  379 [comment   ]     # socket.connect() решает, стоит ли вообще звонить в облака / локальный
  380 [comment   ]     # Ollama. Кэшируется на уровне класса.
  381 [code      ]     _preflight_cache: dict[str, bool] | None = None
  382 [blank     ] 
  383 [def       ]     def _preflight(self) -> dict[str, bool]:
  384 [branch    ]         if LLMRouter._preflight_cache is not None:
  385 [return    ]             return LLMRouter._preflight_cache
  386 [code      ]         out = {"internet": False, "ollama": False}
  387 [import    ]         import socket
  388 [blank     ] 
  389 [try_block ]         try:
  390 [code      ]             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  391 [code      ]             s.settimeout(0.4)
  392 [code      ]             s.connect(("8.8.8.8", 53))
  393 [code      ]             s.close()
  394 [code      ]             out["internet"] = True
  395 [try_block ]         except Exception:
  396 [code      ]             pass
  397 [try_block ]         try:
  398 [code      ]             parts = self.ollama_url.split("://", 1)[-1].split(":")
  399 [code      ]             host = parts[0]
  400 [code      ]             port = int(parts[1].split("/")[0]) if len(parts) > 1 else 11434
  401 [code      ]             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  402 [code      ]             s.settimeout(0.4)
  403 [code      ]             s.connect((host, port))
  404 [code      ]             s.close()
  405 [code      ]             out["ollama"] = True
  406 [try_block ]         except Exception:
  407 [code      ]             pass
  408 [code      ]         LLMRouter._preflight_cache = out
  409 [return    ]         return out
  410 [blank     ] 
  411 [def       ]     def _try_provider(self, name: str, fn):
  412 [code      ]         t0 = time.time()
  413 [code      ]         r = fn()
  414 [code      ]         dt = round(time.time() - t0, 3)
  415 [code      ]         entry = {
  416 [code      ]             "provider": name,
  417 [code      ]             "ok": r.ok,
  418 [code      ]             "error": r.error,
  419 [code      ]             "model": r.model,
  420 [code      ]             "duration_sec": dt,
  421 [code      ]         }
  422 [code      ]         self.log.append(entry)
  423 [return    ]         return r
  424 [blank     ] 
  425 [def       ]     def complete(
  426 [code      ]         self,
  427 [code      ]         prompt: str,
  428 [code      ]         system: str = "",
  429 [code      ]         max_tokens: int = 512,
  430 [code      ]         temperature: float = 0.8,
  431 [code      ]         theme: str = "",
  432 [code      ]         genre: str = "phonk",
  433 [code      ]         language: str = "ru",
  434 [code      ]     ) -> dict[str, Any]:
  435 [code      ]         chain = []
  436 [comment   ]         # v25 (P1): preflight — не звоним куда не надо
  437 [code      ]         pre = self._preflight()
  438 [code      ]         errs = {"openrouter": None, "grok": None, "gemini": None, "ollama": None}
  439 [blank     ] 
  440 [branch    ]         if pre.get("internet"):
  441 [comment   ]             # 1. OpenRouter (только если есть ключ)
  442 [branch    ]             if self.keys.get("openrouter"):
  443 [code      ]                 r1 = self._try_provider(
  444 [code      ]                     "openrouter",
  445 [code      ]                     lambda: call_openrouter(
  446 [code      ]                         prompt,
  447 [code      ]                         system,
  448 [code      ]                         self.keys.get("openrouter", ""),
  449 [code      ]                         timeout=self.timeout,
  450 [code      ]                     ),
  451 [code      ]                 )
  452 [code      ]                 chain.append("openrouter")
  453 [branch    ]                 if r1.ok and r1.text.strip():
  454 [code      ]                     d = r1.to_dict()
  455 [code      ]                     d["provider_chain"] = chain
  456 [code      ]                     d["fallback_used"] = False
  457 [return    ]                     return d
  458 [code      ]                 errs["openrouter"] = r1.error
  459 [branch    ]             else:
  460 [code      ]                 chain.append("openrouter_skipped_no_key")
  461 [code      ]                 errs["openrouter"] = "no_api_key"
  462 [blank     ] 
  463 [comment   ]             # 2. Grok
  464 [branch    ]             if self.keys.get("grok"):
  465 [code      ]                 r2 = self._try_provider(
  466 [code      ]                     "grok",
  467 [code      ]                     lambda: call_grok(
  468 [code      ]                         prompt, system, self.keys.get("grok", ""), timeout=self.timeout
  469 [code      ]                     ),
  470 [code      ]                 )
  471 [code      ]                 chain.append("grok")
  472 [branch    ]                 if r2.ok and r2.text.strip():
  473 [code      ]                     d = r2.to_dict()
  474 [code      ]                     d["provider_chain"] = chain
  475 [code      ]                     d["fallback_used"] = False
  476 [return    ]                     return d
  477 [code      ]                 errs["grok"] = r2.error
  478 [branch    ]             else:
  479 [code      ]                 chain.append("grok_skipped_no_key")
  480 [code      ]                 errs["grok"] = "no_api_key"
  481 [blank     ] 
  482 [comment   ]             # 3. Gemini
  483 [branch    ]             if self.keys.get("gemini"):
  484 [code      ]                 r3 = self._try_provider(
  485 [code      ]                     "gemini",
  486 [code      ]                     lambda: call_gemini(
  487 [code      ]                         prompt,
  488 [code      ]                         system,
  489 [code      ]                         self.keys.get("gemini", ""),
  490 [code      ]                         timeout=self.timeout,
  491 [code      ]                     ),
  492 [code      ]                 )
  493 [code      ]                 chain.append("gemini")
  494 [branch    ]                 if r3.ok and r3.text.strip():
  495 [code      ]                     d = r3.to_dict()
  496 [code      ]                     d["provider_chain"] = chain
  497 [code      ]                     d["fallback_used"] = False
  498 [return    ]                     return d
  499 [code      ]                 errs["gemini"] = r3.error
  500 [branch    ]             else:
  501 [code      ]                 chain.append("gemini_skipped_no_key")
  502 [code      ]                 errs["gemini"] = "no_api_key"
  503 [branch    ]         else:
  504 [code      ]             chain.append("cloud_skipped_no_internet")
  505 [code      ]             errs["openrouter"] = errs["grok"] = errs["gemini"] = "no_internet"
  506 [blank     ] 
  507 [comment   ]         # 4. Ollama (локально) — только если порт живёт
  508 [branch    ]         if pre.get("ollama"):
  509 [code      ]             r4 = self._try_provider(
  510 [code      ]                 "ollama",
  511 [code      ]                 lambda: call_ollama(
  512 [code      ]                     prompt, system, base_url=self.ollama_url, timeout=self.timeout
  513 [code      ]                 ),
  514 [code      ]             )
  515 [code      ]             chain.append("ollama")
  516 [branch    ]             if r4.ok and r4.text.strip():
  517 [code      ]                 d = r4.to_dict()
  518 [code      ]                 d["provider_chain"] = chain
  519 [code      ]                 d["fallback_used"] = False
  520 [return    ]                 return d
  521 [code      ]             errs["ollama"] = r4.error
  522 [branch    ]         else:
  523 [code      ]             chain.append("ollama_skipped_no_local_daemon")
  524 [code      ]             errs["ollama"] = "no_local_daemon"
  525 [blank     ] 
  526 [comment   ]         # 5. LOCAL FALLBACK (template)
  527 [code      ]         text = local_fallback_lyrics(theme or "движение", genre, language)
  528 [code      ]         chain.append("local_template")
  529 [return    ]         return {
  530 [code      ]             "ok": True,
  531 [code      ]             "text": text,
  532 [code      ]             "provider": "local_template",
  533 [code      ]             "model": "punch_lib_v1",
  534 [code      ]             "tokens": len(text.split()),
  535 [code      ]             "provider_chain": chain,
  536 [code      ]             "fallback_used": True,
  537 [code      ]             "error": errs,
  538 [code      ]         }
  539 [blank     ] 
  540 [blank     ] 
  541 [comment   ] # -------------------------------------------------------------- CLI
  542 [blank     ] 
  543 [blank     ] 
  544 [def       ] def _cli():
  545 [import    ]     import argparse
  546 [blank     ] 
  547 [code      ]     p = argparse.ArgumentParser()
  548 [code      ]     p.add_argument(
  549 [code      ]         "--prompt", default="Напиши текст в жанре phonk про ночь и тачки, 16 строк"
  550 [code      ]     )
  551 [code      ]     p.add_argument(
  552 [code      ]         "--system", default="Ты — генератор текстов для программы ZS Music Maker."
  553 [code      ]     )
  554 [code      ]     p.add_argument("--theme", default="ночь")
  555 [code      ]     p.add_argument("--genre", default="phonk")
  556 [code      ]     p.add_argument("--language", default="ru")
  557 [code      ]     p.add_argument("--timeout", type=float, default=15.0)
  558 [code      ]     a = p.parse_args()
  559 [code      ]     router = LLMRouter(timeout=a.timeout)
  560 [code      ]     r = router.complete(
  561 [code      ]         a.prompt, a.system, theme=a.theme, genre=a.genre, language=a.language
  562 [code      ]     )
  563 [code      ]     print(
  564 [code      ]         json.dumps(
  565 [code      ]             {
  566 [code      ]                 "provider": r.get("provider"),
  567 [code      ]                 "model": r.get("model"),
  568 [code      ]                 "fallback_used": r.get("fallback_used"),
  569 [code      ]                 "chain": r.get("provider_chain"),
  570 [code      ]                 "text_preview": r.get("text", "")[:300],
  571 [code      ]                 "log": router.log,
  572 [code      ]             },
  573 [code      ]             ensure_ascii=False,
  574 [code      ]             indent=2,
  575 [code      ]         )
  576 [code      ]     )
  577 [blank     ] 
  578 [blank     ] 
  579 [branch    ] if __name__ == "__main__":
  580 [code      ]     _cli()
```
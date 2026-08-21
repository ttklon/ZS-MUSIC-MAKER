# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/fallback_audit.py`

**Всего строк:** 171

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 86 | 50.3 |
| blank | 21 | 12.3 |
| comment | 15 | 8.8 |
| branch | 12 | 7.0 |
| docstring | 10 | 5.8 |
| return | 8 | 4.7 |
| loop | 7 | 4.1 |
| import | 5 | 2.9 |
| def | 4 | 2.3 |
| try_block | 2 | 1.2 |
| raise | 1 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] ZS Music Maker v14 — tools/fallback_audit.py (P0.15)
    3 [blank     ] 
    4 [docstring ] Сканирует modules/, app/, agents/, tools/, updater/ и ищет fallback-пути:
    5 [docstring ]   — pitch_shift, apply_gain, silence_stub, pink_noise, sine_stub;
    6 [docstring ]   — dry_run, placeholder, FALLBACK_USED, shutil.copy.
    7 [blank     ] 
    8 [docstring ] Формирует отчёт output/audit_v14/fallback_report.json.
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] from __future__ import annotations
   12 [blank     ] 
   13 [import    ] import json
   14 [import    ] import re
   15 [import    ] from pathlib import Path
   16 [import    ] from typing import Any
   17 [blank     ] 
   18 [code      ] ROOT = Path(__file__).resolve().parents[1]
   19 [blank     ] 
   20 [code      ] SCAN_DIRS = ["modules", "app", "agents", "tools", "updater"]
   21 [code      ] BAD_PATTERNS = {
   22 [code      ]     "pitch_shift_as_rvc": r"librosa\.effects\.pitch_shift",
   23 [code      ]     "apply_gain_as_master": r"\.apply_gain\s*\(",
   24 [code      ]     "silence_stub": r"silence_stub|_silence_stub",
   25 [code      ]     "pink_noise": r"pink_noise|_pink_noise",
   26 [code      ]     "sine_stub": r"synthesize_sine|_sine_stub",
   27 [code      ]     "dry_run": r"dry_run\s*=\s*True|\"dry_run\":\s*True",
   28 [code      ]     "placeholder": r"placeholder|style_vector_placeholder",
   29 [code      ]     "fallback_var": r"FALLBACK_USED|fallback_used",
   30 [code      ]     "shutil_copy_master": r"shutil\.copy.*master",
   31 [comment   ]     # v18: регресс-страж бага v16, когда бит дакался сам собой
   32 [comment   ]     # (apply_sidechain(beat, beat)) вместо bus по кику
   33 [code      ]     "sidechain_self_duck": r"apply_sidechain\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*\1\s*,",
   34 [code      ] }
   35 [blank     ] 
   36 [comment   ] # v18: сниппеты с этой меткой — осознанный, задокументированный DSP
   37 [comment   ] # (например pitch-shift для бэкинг-гармонии), а НЕ подмена RVC.
   38 [code      ] LEGIT_MARKERS = ("ZSMM_NOT_RVC", "ZSMM_LEGIT", "noqa: ZSMM")
   39 [blank     ] 
   40 [blank     ] 
   41 [code      ] SELF_SKIP = {"tools/fallback_audit.py"}
   42 [blank     ] 
   43 [blank     ] 
   44 [def       ] def _is_hard_refusal(text: str, def_line: str) -> bool:
   45 [docstring ]     """v18: deprecated-функция, которая сразу бросает RuntimeError
   46 [docstring ]     и НЕ вызывается в пайплайне — честный отказ, а не скрытый fallback.
   47 [docstring ]     Пример: _pink_noise_fallback в musicgen_texture (P0.06)."""
   48 [code      ]     name = def_line.split("def ", 1)[1].split("(", 1)[0].strip()
   49 [comment   ]     # тело функции должно содержать raise RuntimeError
   50 [code      ]     m = re.search(
   51 [code      ]         r"def\s+" + re.escape(name) + r"\s*\(.*?\n(.*?)(?=\ndef\s|\Z)", text, re.DOTALL
   52 [code      ]     )
   53 [branch    ]     if not m:
   54 [return    ]         return False
   55 [code      ]     body = m.group(1)
   56 [branch    ]     if "raise RuntimeError" not in body:
   57 [return    ]         return False
   58 [comment   ]     # функция не должна вызываться нигде, кроме собственного объявления
   59 [code      ]     calls = re.findall(re.escape(name) + r"\s*\(", text)
   60 [return    ]     return len(calls) <= 1  # только само объявление
   61 [blank     ] 
   62 [blank     ] 
   63 [def       ] def scan_file(path: Path) -> dict[str, list[dict[str, Any]]]:
   64 [code      ]     rel = str(path.relative_to(ROOT))
   65 [branch    ]     if rel in SELF_SKIP:
   66 [return    ]         return {}
   67 [code      ]     hits: dict[str, list[dict[str, Any]]] = {}
   68 [try_block ]     try:
   69 [code      ]         text = path.read_text(encoding="utf-8", errors="replace")
   70 [try_block ]     except Exception:
   71 [return    ]         return hits
   72 [code      ]     lines = text.splitlines()
   73 [loop      ]     for tag, pat in BAD_PATTERNS.items():
   74 [loop      ]         for m in re.finditer(pat, text):
   75 [code      ]             line_no = text[: m.start()].count("\n") + 1
   76 [code      ]             snippet = (
   77 [code      ]                 lines[line_no - 1].strip()
   78 [branch    ]                 if line_no - 1 < len(lines)
   79 [code      ]                 else ""
   80 [code      ]             )
   81 [comment   ]             # v18: явно помеченные легитимные применения — не флаг.
   82 [comment   ]             # v33 FIX (P1, SESSION_LOG v31.4): маркер `# noqa: ZSMM_NOT_RVC`
   83 [comment   ]             # часто стоит на ЗАКРЫВАЮЩЕЙ строке многострочного вызова
   84 [comment   ]             # (`pitch_shift(\n mono, sr=sr, n_steps=...\n )  # noqa: ...`),
   85 [comment   ]             # а детектор смотрел только первую строку совпадения — это давало
   86 [comment   ]             # ложные red_flags (female_backing.py:127, anti_neuro_v10.py:363).
   87 [comment   ]             # Теперь ищем маркер в окне ±4 строк вокруг совпадения.
   88 [code      ]             lo = max(0, line_no - 5)
   89 [code      ]             hi = min(len(lines), line_no + 4)
   90 [code      ]             window = "\n".join(lines[lo:hi])
   91 [branch    ]             if any(mk in window for mk in LEGIT_MARKERS):
   92 [code      ]                 continue
   93 [comment   ]             # v18: hard-refusal (raise RuntimeError / deprecated-stub,
   94 [comment   ]             # который НЕ вызывается в пайплайне) — честный отказ, не флаг
   95 [branch    ]             if snippet.startswith("def ") and _is_hard_refusal(text, snippet):
   96 [code      ]                 continue
   97 [code      ]             hits.setdefault(tag, []).append(
   98 [code      ]                 {
   99 [code      ]                     "file": str(path.relative_to(ROOT)),
  100 [code      ]                     "line": line_no,
  101 [code      ]                     "snippet": snippet[:140],
  102 [code      ]                 }
  103 [code      ]             )
  104 [return    ]     return hits
  105 [blank     ] 
  106 [blank     ] 
  107 [def       ] def scan_all() -> dict[str, Any]:
  108 [code      ]     all_hits: dict[str, list[dict[str, Any]]] = {}
  109 [code      ]     files_scanned = 0
  110 [loop      ]     for d in SCAN_DIRS:
  111 [code      ]         base = ROOT / d
  112 [branch    ]         if not base.exists():
  113 [code      ]             continue
  114 [loop      ]         for p in base.rglob("*.py"):
  115 [branch    ]             if "__pycache__" in str(p):
  116 [code      ]                 continue
  117 [code      ]             files_scanned += 1
  118 [code      ]             h = scan_file(p)
  119 [loop      ]             for tag, entries in h.items():
  120 [code      ]                 all_hits.setdefault(tag, []).extend(entries)
  121 [blank     ] 
  122 [code      ]     summary = {tag: len(entries) for tag, entries in all_hits.items()}
  123 [code      ]     red_flags = {}
  124 [loop      ]     for tag in (
  125 [code      ]         "pitch_shift_as_rvc",
  126 [code      ]         "pink_noise",
  127 [code      ]         "sine_stub",
  128 [code      ]         "silence_stub",
  129 [code      ]         "sidechain_self_duck",
  130 [code      ]     ):
  131 [branch    ]         if tag in all_hits:
  132 [code      ]             real = [
  133 [code      ]                 e
  134 [loop      ]                 for e in all_hits[tag]
  135 [branch    ]                 if "legacy/" not in e["file"]
  136 [code      ]                 and not e["snippet"].lstrip().startswith("#")
  137 [code      ]             ]
  138 [branch    ]             if real:
  139 [code      ]                 red_flags[tag] = real
  140 [blank     ] 
  141 [return    ]     return {
  142 [code      ]         "files_scanned": files_scanned,
  143 [code      ]         "summary": summary,
  144 [code      ]         "red_flags": red_flags,
  145 [code      ]         "all_hits": all_hits,
  146 [code      ]     }
  147 [blank     ] 
  148 [blank     ] 
  149 [def       ] def main() -> int:
  150 [code      ]     r = scan_all()
  151 [code      ]     out_dir = ROOT / "output" / "audit_v14"
  152 [code      ]     out_dir.mkdir(parents=True, exist_ok=True)
  153 [code      ]     out = out_dir / "fallback_report.json"
  154 [code      ]     out.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
  155 [code      ]     print(
  156 [code      ]         json.dumps(
  157 [code      ]             {
  158 [code      ]                 "files_scanned": r["files_scanned"],
  159 [code      ]                 "summary": r["summary"],
  160 [code      ]                 "red_flags_count": {k: len(v) for k, v in r["red_flags"].items()},
  161 [code      ]                 "report": str(out),
  162 [code      ]             },
  163 [code      ]             ensure_ascii=False,
  164 [code      ]             indent=2,
  165 [code      ]         )
  166 [code      ]     )
  167 [return    ]     return 0 if not r["red_flags"] else 1
  168 [blank     ] 
  169 [blank     ] 
  170 [branch    ] if __name__ == "__main__":
  171 [raise     ]     raise SystemExit(main())
```
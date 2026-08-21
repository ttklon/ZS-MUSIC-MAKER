# ПОСТРОЧНЫЙ ЛИСТИНГ: `tools/lazy_dirs_patch.py`

**Всего строк:** 174

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 146 | 83.9 |
| blank | 9 | 5.2 |
| docstring | 7 | 4.0 |
| branch | 4 | 2.3 |
| import | 2 | 1.1 |
| loop | 2 | 1.1 |
| comment | 1 | 0.6 |
| def | 1 | 0.6 |
| return | 1 | 0.6 |
| raise | 1 | 0.6 |

## Полный листинг с классификацией
```
    1 [docstring ] """v22: одноразовый скрипт — заменить top-level mkdir() на ленивое создание.
    2 [blank     ] 
    3 [docstring ] Стратегия:
    4 [docstring ]   • если top-level `X.mkdir(...)` или `os.makedirs(X, ...)` — убираем;
    5 [docstring ]   • перед первой записью в X добавляем `X.mkdir(parents=True, exist_ok=True)`;
    6 [docstring ]   • для модулей с простым `OUTPUT_DIR` — оставляем константу, убираем side-effect.
    7 [blank     ] 
    8 [docstring ] Скрипт работает по whitelist модулей, чтобы не сломать остальное.
    9 [docstring ] """
   10 [blank     ] 
   11 [import    ] import re
   12 [import    ] from pathlib import Path
   13 [blank     ] 
   14 [code      ] ROOT = Path(__file__).resolve().parents[1]
   15 [code      ] MODS = ROOT / "modules"
   16 [blank     ] 
   17 [comment   ] # whitelist модулей и их паттернов (regex → replacement)
   18 [code      ] PATCHES = {
   19 [code      ]     "mixdown.py": [
   20 [code      ]         (
   21 [code      ]             r"^os\.makedirs\(OUTPUT_DIR, exist_ok=True\)\s*$",
   22 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   23 [code      ]         ),
   24 [code      ]     ],
   25 [code      ]     "beat_gen.py": [
   26 [code      ]         (
   27 [code      ]             r"^os\.makedirs\(OUTPUT_DIR, exist_ok=True\)\s*$",
   28 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   29 [code      ]         ),
   30 [code      ]     ],
   31 [code      ]     "humanization.py": [
   32 [code      ]         (
   33 [code      ]             r"^os\.makedirs\(OUTPUT_DIR, exist_ok=True\)\s*$",
   34 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   35 [code      ]         ),
   36 [code      ]     ],
   37 [code      ]     "provenance.py": [
   38 [code      ]         (
   39 [code      ]             r"^os\.makedirs\(os\.path\.dirname\(VAULT\), exist_ok=True\)\s*$",
   40 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   41 [code      ]         ),
   42 [code      ]     ],
   43 [code      ]     "release_export.py": [
   44 [code      ]         (
   45 [code      ]             r"^RELEASES_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
   46 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   47 [code      ]         ),
   48 [code      ]     ],
   49 [code      ]     "track_templates.py": [
   50 [code      ]         (
   51 [code      ]             r"^TPL_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
   52 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   53 [code      ]         ),
   54 [code      ]         (
   55 [code      ]             r"^HIST_FILE\.parent\.mkdir\(parents=True, exist_ok=True\)\s*$",
   56 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   57 [code      ]         ),
   58 [code      ]     ],
   59 [code      ]     "render_queue.py": [
   60 [code      ]         (
   61 [code      ]             r"^QUEUE_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
   62 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   63 [code      ]         ),
   64 [code      ]     ],
   65 [code      ]     "lyrics_gen.py": [
   66 [code      ]         (
   67 [code      ]             r"^VAULT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
   68 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   69 [code      ]         ),
   70 [code      ]     ],
   71 [code      ]     "female_backing.py": [
   72 [code      ]         (
   73 [code      ]             r"^BACK_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
   74 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   75 [code      ]         ),
   76 [code      ]     ],
   77 [code      ]     "user_profile.py": [
   78 [code      ]         (
   79 [code      ]             r"^PROFILE_FILE\.parent\.mkdir\(parents=True, exist_ok=True\)\s*$",
   80 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   81 [code      ]         ),
   82 [code      ]     ],
   83 [code      ]     "voice_recording.py": [
   84 [code      ]         (
   85 [code      ]             r"^VAULT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
   86 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   87 [code      ]         ),
   88 [code      ]     ],
   89 [code      ]     "voice_onboarding.py": [
   90 [code      ]         (
   91 [code      ]             r"^VAULT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
   92 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   93 [code      ]         ),
   94 [code      ]     ],
   95 [code      ]     "voice_vault_v9.py": [
   96 [code      ]         (
   97 [code      ]             r"^VAULT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
   98 [code      ]             "# v22: ленивое создание (не при импорте)\n",
   99 [code      ]         ),
  100 [code      ]     ],
  101 [code      ]     "rvc_trainer_v9.py": [
  102 [code      ]         (
  103 [code      ]             r"^JOBS_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
  104 [code      ]             "# v22: ленивое создание (не при импорте)\n",
  105 [code      ]         ),
  106 [code      ]     ],
  107 [code      ]     "reference_ingest.py": [
  108 [code      ]         (
  109 [code      ]             r"^CACHE_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
  110 [code      ]             "# v22: ленивое создание (не при импорте)\n",
  111 [code      ]         ),
  112 [code      ]     ],
  113 [code      ]     "auto_qa.py": [
  114 [code      ]         (
  115 [code      ]             r"^QA_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
  116 [code      ]             "# v22: ленивое создание (не при импорте)\n",
  117 [code      ]         ),
  118 [code      ]     ],
  119 [code      ]     "self_diag_v13.py": [
  120 [code      ]         (
  121 [code      ]             r"^LOGS\.mkdir\(exist_ok=True\)\s*$",
  122 [code      ]             "# v22: ленивое создание (не при импорте)\n",
  123 [code      ]         ),
  124 [code      ]     ],
  125 [code      ]     "wizard_v12_integration.py": [
  126 [code      ]         (
  127 [code      ]             r"^LOGS\.mkdir\(exist_ok=True\)\s*$",
  128 [code      ]             "# v22: ленивое создание (не при импорте)\n",
  129 [code      ]         ),
  130 [code      ]     ],
  131 [code      ]     "master_pipeline_v12.py": [
  132 [code      ]         (
  133 [code      ]             r"^LOGS\.mkdir\(exist_ok=True\)\s*$",
  134 [code      ]             "# v22: ленивое создание (не при импорте)\n",
  135 [code      ]         ),
  136 [code      ]     ],
  137 [code      ]     "llm_clients_v15.py": [
  138 [code      ]         (
  139 [code      ]             r"^SECRETS_FILE\.parent\.mkdir\(parents=True, exist_ok=True\)\s*$",
  140 [code      ]             "# v22: ленивое создание (не при импорте)\n",
  141 [code      ]         ),
  142 [code      ]     ],
  143 [code      ]     "voice_synth.py": [
  144 [code      ]         (
  145 [code      ]             r"^OUT_DIR\.mkdir\(parents=True, exist_ok=True\)\s*$",
  146 [code      ]             "# v22: ленивое создание (не при импорте)\n",
  147 [code      ]         ),
  148 [code      ]     ],
  149 [code      ] }
  150 [blank     ] 
  151 [blank     ] 
  152 [def       ] def main():
  153 [code      ]     modified = []
  154 [loop      ]     for fname, rules in PATCHES.items():
  155 [code      ]         p = MODS / fname
  156 [branch    ]         if not p.exists():
  157 [code      ]             print(f"  [SKIP] {fname} not found")
  158 [code      ]             continue
  159 [code      ]         src = p.read_text(encoding="utf-8")
  160 [code      ]         orig = src
  161 [loop      ]         for pattern, replacement in rules:
  162 [code      ]             src = re.sub(pattern, replacement, src, count=1, flags=re.MULTILINE)
  163 [branch    ]         if src != orig:
  164 [code      ]             p.write_text(src, encoding="utf-8")
  165 [code      ]             modified.append(fname)
  166 [code      ]             print(f"  [OK] {fname}")
  167 [branch    ]         else:
  168 [code      ]             print(f"  [NOOP] {fname}")
  169 [code      ]     print(f"\nTotal modified: {len(modified)}")
  170 [return    ]     return 0
  171 [blank     ] 
  172 [blank     ] 
  173 [branch    ] if __name__ == "__main__":
  174 [raise     ]     raise SystemExit(main())
```
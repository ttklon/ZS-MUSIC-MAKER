# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/beat_constructor.py`

**Всего строк:** 658

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 370 | 56.2 |
| blank | 78 | 11.9 |
| comment | 55 | 8.4 |
| branch | 51 | 7.8 |
| docstring | 31 | 4.7 |
| return | 24 | 3.6 |
| def | 13 | 2.0 |
| loop | 13 | 2.0 |
| try_block | 12 | 1.8 |
| import | 10 | 1.5 |
| class | 1 | 0.2 |

## Полный листинг с классификацией
```
    1 [docstring ] """
    2 [docstring ] [3] beat_constructor.py — Sample-based Beat Constructor / Arrangement Engine v2 (НОВЫЙ - ЯДРО)
    3 [docstring ] Это реальное ядро приложения для текущего железа (AMD RX 580 4GB).
    4 [docstring ] Не зависит от тяжёлой text-to-music нейронки.
    5 [blank     ] 
    6 [docstring ] Берёт:
    7 [docstring ]   • groove_template (из groove_extractor)
    8 [docstring ]   • набор выбранных/найденных сэмплов
    9 [docstring ]   • тональность/диапазон
   10 [docstring ]   • длину трека
   11 [docstring ]   • количество куплетов/припевов
   12 [docstring ]   • желаемую степень агрессии/качёвости
   13 [blank     ] 
   14 [docstring ] Собирает новую аранжировку из 4-, 8-, 16-тактовых блоков.
   15 [docstring ] Делает вариации: смена хэта, фильтр перед дропом, стоп-таймы, райзеры,
   16 [docstring ] брейки, микро-мутации 808.
   17 [docstring ] """
   18 [blank     ] 
   19 [import    ] import json
   20 [import    ] import math
   21 [import    ] import os
   22 [import    ] import random
   23 [blank     ] 
   24 [import    ] import numpy as np
   25 [blank     ] 
   26 [comment   ] # v21: не создаём каталог на импорте (паразитная запись в modules/../output).
   27 [comment   ] # Создаём лениво перед записью. Каталог можно переопределить
   28 [comment   ] # через env ZSMM_BEAT_OUTPUT_DIR (для тестов и CI).
   29 [code      ] OUTPUT_DIR = os.environ.get(
   30 [code      ]     "ZSMM_BEAT_OUTPUT_DIR",
   31 [code      ]     os.path.join(os.path.dirname(__file__), "..", "output", "beats"),
   32 [code      ] )
   33 [blank     ] 
   34 [blank     ] 
   35 [class     ] class BeatConstructor:
   36 [docstring ]     """Конструктор оригинального бита из сэмплов + groove template."""
   37 [blank     ] 
   38 [def       ]     def __init__(
   39 [code      ]         self,
   40 [code      ]         bpm: int = 128,
   41 [code      ]         key: str = "A minor",
   42 [code      ]         groove: dict = None,
   43 [code      ]         samples: list = None,
   44 [code      ]     ):
   45 [code      ]         self.bpm = bpm
   46 [code      ]         self.key = key
   47 [code      ]         self.groove = groove or {}
   48 [code      ]         self.samples = samples or []  # список путей к wav-файлам сэмплов
   49 [code      ]         self.sr = 44100
   50 [blank     ] 
   51 [comment   ]         # Классифицируем сэмплы по типу
   52 [code      ]         self.kick_samples = []
   53 [code      ]         self.snare_samples = []
   54 [code      ]         self.hihat_samples = []
   55 [code      ]         self.bass_samples = []
   56 [code      ]         self.melody_samples = []
   57 [code      ]         self.fx_samples = []
   58 [code      ]         self._classify_samples()
   59 [blank     ] 
   60 [def       ]     def _classify_samples(self):
   61 [docstring ]         """Грубо классифицирует сэмплы по имени файла."""
   62 [loop      ]         for s in self.samples:
   63 [code      ]             name = os.path.basename(s).lower()
   64 [branch    ]             if any(k in name for k in ["kick", "bd", "bass_drum", "808"]):
   65 [code      ]                 self.kick_samples.append(s)
   66 [branch    ]             elif any(k in name for k in ["snare", "sd", "clap", "rim"]):
   67 [code      ]                 self.snare_samples.append(s)
   68 [branch    ]             elif any(
   69 [code      ]                 k in name for k in ["hihat", "hat", "hh", "cymbal", "ride", "crash"]
   70 [code      ]             ):
   71 [code      ]                 self.hihat_samples.append(s)
   72 [branch    ]             elif any(k in name for k in ["bass", "sub", "808_bass", "reese"]):
   73 [code      ]                 self.bass_samples.append(s)
   74 [branch    ]             elif any(
   75 [code      ]                 k in name
   76 [loop      ]                 for k in [
   77 [code      ]                     "melody",
   78 [code      ]                     "lead",
   79 [code      ]                     "saz",
   80 [code      ]                     "sitar",
   81 [code      ]                     "plucks",
   82 [code      ]                     "synth",
   83 [code      ]                     "arp",
   84 [code      ]                     "chord",
   85 [code      ]                     "pad",
   86 [code      ]                 ]
   87 [code      ]             ):
   88 [code      ]                 self.melody_samples.append(s)
   89 [branch    ]             elif any(
   90 [code      ]                 k in name
   91 [loop      ]                 for k in ["fx", "rise", "riser", "sweep", "impact", "sfx", "noise"]
   92 [code      ]             ):
   93 [code      ]                 self.fx_samples.append(s)
   94 [branch    ]             else:
   95 [comment   ]                 # Если не классифицировано — кладём в melody как fallback
   96 [code      ]                 self.melody_samples.append(s)
   97 [blank     ] 
   98 [def       ]     def _load_audio(self, path: str) -> np.ndarray:
   99 [docstring ]         """Загружает wav/mp3 в numpy массив (mono)."""
  100 [try_block ]         try:
  101 [import    ]             from pydub import AudioSegment
  102 [blank     ] 
  103 [code      ]             seg = AudioSegment.from_file(path)
  104 [branch    ]             if seg.channels > 1:
  105 [code      ]                 seg = seg.set_channels(1)
  106 [code      ]             seg = seg.set_frame_rate(self.sr)
  107 [code      ]             samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
  108 [code      ]             samples = samples / (2**15)  # normalize to -1..1
  109 [return    ]             return samples
  110 [try_block ]         except Exception as e:
  111 [code      ]             print(f"[beat_constructor] load fail {path}: {e}")
  112 [return    ]             return np.zeros(self.sr, dtype=np.float32)
  113 [blank     ] 
  114 [def       ]     def _generate_kick(self, step: int, bar: int) -> np.ndarray:
  115 [docstring ]         """Возвращает кик для данного шага с учетом акцентов и вариаций."""
  116 [comment   ]         # Базовый паттерн
  117 [code      ]         kick_pattern = self.groove.get(
  118 [code      ]             "kick_pattern", [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
  119 [code      ]         )
  120 [blank     ] 
  121 [comment   ]         # Вариация каждые 4 такта
  122 [branch    ]         if bar % 4 == 3 and step >= 12:
  123 [comment   ]             # Добавляем сбивку в конце 4-го такта
  124 [branch    ]             if step in [12, 14, 15]:
  125 [code      ]                 kick_pattern = [0] * 12 + [1, 0, 1, 1]
  126 [blank     ] 
  127 [code      ]         idx = step % len(kick_pattern)
  128 [branch    ]         if kick_pattern[idx] == 0:
  129 [return    ]             return np.zeros(1, dtype=np.float32)
  130 [blank     ] 
  131 [comment   ]         # Акценты: первый удар сильнее, офф-биты слабее
  132 [code      ]         velocity = 1.0
  133 [branch    ]         if step == 0:
  134 [code      ]             velocity = 1.05
  135 [branch    ]         elif step % 4 != 0:
  136 [code      ]             velocity = 0.85
  137 [blank     ] 
  138 [comment   ]         # Если есть реальный сэмпл кика — используем его
  139 [branch    ]         if self.kick_samples:
  140 [code      ]             kick_path = random.choice(self.kick_samples)
  141 [return    ]             return self._load_audio(kick_path) * velocity
  142 [blank     ] 
  143 [comment   ]         # Иначе синтезируем простой кик
  144 [code      ]         dur = 0.15  # 150ms
  145 [code      ]         t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
  146 [code      ]         env = np.exp(-t * 30)
  147 [code      ]         freq = 60 * np.exp(-t * 100) + 40  # pitch sweep
  148 [code      ]         kick = 0.8 * env * np.sin(2 * np.pi * freq * t)
  149 [return    ]         return kick
  150 [blank     ] 
  151 [def       ]     def _generate_snare(self, step: int, bar: int) -> np.ndarray:
  152 [docstring ]         """Возвращает снейр/клэп для данного шага с учетом акцентов."""
  153 [code      ]         snare_pattern = self.groove.get(
  154 [code      ]             "snare_pattern", [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
  155 [code      ]         )
  156 [blank     ] 
  157 [comment   ]         # Ghost notes (призрачные ноты) для живости
  158 [code      ]         is_ghost = False
  159 [branch    ]         if snare_pattern[step % 16] == 0:
  160 [branch    ]             if step % 16 in [3, 6, 11, 14] and random.random() < 0.2:
  161 [code      ]                 is_ghost = True
  162 [branch    ]             else:
  163 [return    ]                 return np.zeros(1, dtype=np.float32)
  164 [blank     ] 
  165 [code      ]         velocity = 0.3 if is_ghost else (0.9 + random.random() * 0.15)
  166 [blank     ] 
  167 [branch    ]         if self.snare_samples:
  168 [code      ]             snare_path = random.choice(self.snare_samples)
  169 [return    ]             return self._load_audio(snare_path) * velocity
  170 [blank     ] 
  171 [comment   ]         # Синтез снейра: шум + тон
  172 [code      ]         dur = 0.12
  173 [code      ]         t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
  174 [code      ]         env = np.exp(-t * 25)
  175 [code      ]         noise = np.random.randn(len(t)) * 0.5
  176 [code      ]         tone = 0.3 * np.sin(2 * np.pi * 200 * t)
  177 [code      ]         snare = 0.6 * env * (noise + tone)
  178 [return    ]         return snare
  179 [blank     ] 
  180 [def       ]     def _generate_hihat(self, step: int, bar: int) -> np.ndarray:
  181 [docstring ]         """Возвращает хэт для данного шага."""
  182 [code      ]         density = self.groove.get("hihat_density", 0.5)
  183 [code      ]         swing = self.groove.get("swing", 0.0)
  184 [blank     ] 
  185 [comment   ]         # На нечётных шагах добавляем свинг (смещение)
  186 [code      ]         play = random.random() < density
  187 [branch    ]         if step % 2 == 1 and random.random() < swing * 0.5:
  188 [code      ]             play = True  # свинг добавляет доп. удары
  189 [blank     ] 
  190 [branch    ]         if not play:
  191 [return    ]             return np.zeros(1, dtype=np.float32)
  192 [blank     ] 
  193 [branch    ]         if self.hihat_samples:
  194 [code      ]             hh_path = random.choice(self.hihat_samples)
  195 [return    ]             return self._load_audio(hh_path) * 0.5  # хэт тише
  196 [blank     ] 
  197 [comment   ]         # Синтез хэта: высокочастотный шум
  198 [code      ]         dur = 0.05
  199 [code      ]         t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
  200 [code      ]         env = np.exp(-t * 80)
  201 [code      ]         noise = np.random.randn(len(t))
  202 [comment   ]         # High-pass (простая реализация: вычитаем скользящее среднее)
  203 [branch    ]         if len(noise) > 10:
  204 [code      ]             noise = noise - np.convolve(noise, np.ones(10) / 10, mode="same")
  205 [code      ]         hihat = 0.3 * env * noise
  206 [return    ]         return hihat
  207 [blank     ] 
  208 [def       ]     def _generate_bass_line(self, bar: int, bar_samples: int) -> np.ndarray:
  209 [docstring ]         """Генерирует басовую линию для такта."""
  210 [branch    ]         if self.bass_samples:
  211 [code      ]             bass_path = random.choice(self.bass_samples)
  212 [code      ]             bass = self._load_audio(bass_path)
  213 [branch    ]             if len(bass) < bar_samples:
  214 [code      ]                 bass = np.pad(bass, (0, bar_samples - len(bass)))
  215 [return    ]             return bass[:bar_samples] * 0.8
  216 [blank     ] 
  217 [comment   ]         # Синтез 808 баса
  218 [comment   ]         # Ноты в миноре: I, III, V, VII (для phonk/трэпа)
  219 [code      ]         root_freqs = {
  220 [code      ]             "C": 261.63,
  221 [code      ]             "C#": 277.18,
  222 [code      ]             "D": 293.66,
  223 [code      ]             "D#": 311.13,
  224 [code      ]             "E": 329.63,
  225 [code      ]             "F": 349.23,
  226 [code      ]             "F#": 369.99,
  227 [code      ]             "G": 392.00,
  228 [code      ]             "G#": 415.30,
  229 [code      ]             "A": 440.00,
  230 [code      ]             "A#": 466.16,
  231 [code      ]             "B": 493.88,
  232 [code      ]         }
  233 [code      ]         root = self.key.split()[0] if " " in self.key else "A"
  234 [code      ]         base_freq = root_freqs.get(root, 440.0) / 2  # на октаву ниже
  235 [blank     ] 
  236 [comment   ]         # Простой паттерн: I на 1 и 9 шагах
  237 [code      ]         kick_pattern = self.groove.get(
  238 [code      ]             "kick_pattern", [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
  239 [code      ]         )
  240 [code      ]         bass = np.zeros(bar_samples, dtype=np.float32)
  241 [blank     ] 
  242 [code      ]         step_len = bar_samples // 16
  243 [loop      ]         for i, play in enumerate(kick_pattern):
  244 [branch    ]             if play:
  245 [code      ]                 start = i * step_len
  246 [code      ]                 end = min(start + step_len * 2, bar_samples)
  247 [code      ]                 dur_t = np.linspace(
  248 [code      ]                     0, (end - start) / self.sr, end - start, endpoint=False
  249 [code      ]                 )
  250 [code      ]                 env = np.exp(-dur_t * 5)
  251 [code      ]                 bass[start:end] += 0.7 * env * np.sin(2 * np.pi * base_freq * dur_t)
  252 [blank     ] 
  253 [return    ]         return bass
  254 [blank     ] 
  255 [def       ]     def _generate_melody(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
  256 [docstring ]         """Генерирует мелодический слой для такта."""
  257 [comment   ]         # В брейках/интро мелодия плотнее, в дропе — реже
  258 [branch    ]         if section in ("intro", "breakdown", "outro") and self.melody_samples:
  259 [code      ]             mel_path = random.choice(self.melody_samples)
  260 [code      ]             mel = self._load_audio(mel_path)
  261 [branch    ]             if len(mel) < bar_samples:
  262 [code      ]                 mel = np.pad(mel, (0, bar_samples - len(mel)))
  263 [return    ]             return mel[:bar_samples] * 0.4
  264 [blank     ] 
  265 [branch    ]         if section == "verse" and self.melody_samples and bar % 2 == 0:
  266 [code      ]             mel_path = random.choice(self.melody_samples)
  267 [code      ]             mel = self._load_audio(mel_path) * 0.25
  268 [branch    ]             if len(mel) < bar_samples:
  269 [code      ]                 mel = np.pad(mel, (0, bar_samples - len(mel)))
  270 [return    ]             return mel[:bar_samples]
  271 [blank     ] 
  272 [return    ]         return np.zeros(bar_samples, dtype=np.float32)
  273 [blank     ] 
  274 [def       ]     def _generate_fx(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
  275 [docstring ]         """Генерирует FX (райзеры, импакты) в переходах."""
  276 [comment   ]         # Райзер перед дропом
  277 [branch    ]         if section == "pre_chorus" and self.fx_samples:
  278 [code      ]             fx_path = random.choice(self.fx_samples)
  279 [code      ]             fx = self._load_audio(fx_path)
  280 [branch    ]             if len(fx) < bar_samples:
  281 [code      ]                 fx = np.pad(fx, (0, bar_samples - len(fx)))
  282 [return    ]             return fx[:bar_samples] * 0.5
  283 [blank     ] 
  284 [comment   ]         # Стоп-тайм (тишина перед хуком) — 1 шаг тишины в конце такта
  285 [branch    ]         if section == "hook" and bar % 4 == 3:
  286 [code      ]             stop_samples = bar_samples // 16 * 2
  287 [code      ]             fx = np.ones(stop_samples, dtype=np.float32) * 0.001
  288 [return    ]             return np.pad(fx, (bar_samples - stop_samples, 0))
  289 [blank     ] 
  290 [return    ]         return np.zeros(bar_samples, dtype=np.float32)
  291 [blank     ] 
  292 [def       ]     def _pan_audio(self, audio: np.ndarray, pan: float) -> np.ndarray:
  293 [docstring ]         """Панорамирует моно-сигнал. pan: -1 (L) .. 1 (R)."""
  294 [branch    ]         if audio.ndim > 1:
  295 [return    ]             return audio  # уже стерео
  296 [comment   ]         # Constant power panning
  297 [code      ]         angle = (pan + 1.0) * (math.pi / 4.0)
  298 [code      ]         left = math.cos(angle)
  299 [code      ]         right = math.sin(angle)
  300 [return    ]         return np.stack([audio * left, audio * right], axis=1).astype(np.float32)
  301 [blank     ] 
  302 [def       ]     def _build_section(
  303 [code      ]         self, section: str, n_bars: int, aggression: float = 0.7
  304 [code      ]     ) -> np.ndarray:
  305 [docstring ]         """Строит секцию трека из нескольких тактов (СТЕРЕО)."""
  306 [code      ]         beat_sec = 60.0 / self.bpm
  307 [code      ]         bar_sec = beat_sec * 4
  308 [code      ]         bar_samples = int(self.sr * bar_sec)
  309 [code      ]         step_samples = bar_samples // 16
  310 [blank     ] 
  311 [code      ]         section_audio = np.zeros((bar_samples * n_bars, 2), dtype=np.float32)
  312 [blank     ] 
  313 [loop      ]         for bar in range(n_bars):
  314 [code      ]             bar_start = bar * bar_samples
  315 [code      ]             bar_audio = np.zeros((bar_samples, 2), dtype=np.float32)
  316 [blank     ] 
  317 [comment   ]             # Басовая линия (центр)
  318 [branch    ]             if section not in ("intro_pad", "breakdown_silent", "outro_fade"):
  319 [code      ]                 bass = self._generate_bass_line(bar, bar_samples)
  320 [code      ]                 bar_audio += self._pan_audio(bass, 0.0)
  321 [blank     ] 
  322 [comment   ]             # Драм-паттерн
  323 [branch    ]             if section not in ("intro_pad", "breakdown_silent"):
  324 [loop      ]                 for step in range(16):
  325 [code      ]                     step_start = step * step_samples
  326 [blank     ] 
  327 [comment   ]                     # Кик всегда в центре
  328 [code      ]                     kick = self._generate_kick(step, bar)
  329 [code      ]                     kick_end = min(step_start + len(kick), bar_samples)
  330 [code      ]                     bar_audio[step_start:kick_end] += self._pan_audio(
  331 [code      ]                         kick[: kick_end - step_start], 0.0
  332 [code      ]                     )
  333 [blank     ] 
  334 [comment   ]                     # Снейр/клэп почти в центре
  335 [code      ]                     snare = self._generate_snare(step, bar)
  336 [code      ]                     snare_end = min(step_start + len(snare), bar_samples)
  337 [code      ]                     bar_audio[step_start:snare_end] += self._pan_audio(
  338 [code      ]                         snare[: snare_end - step_start], random.uniform(-0.05, 0.05)
  339 [code      ]                     )
  340 [blank     ] 
  341 [comment   ]                     # Хэты панорамируем (шире для стерео-поля)
  342 [code      ]                     hh = self._generate_hihat(step, bar)
  343 [code      ]                     hh_end = min(step_start + len(hh), bar_samples)
  344 [code      ]                     hh_pan = 0.45 if step % 2 == 0 else -0.45
  345 [code      ]                     bar_audio[step_start:hh_end] += self._pan_audio(
  346 [code      ]                         hh[: hh_end - step_start], hh_pan
  347 [code      ]                     )
  348 [blank     ] 
  349 [comment   ]             # Мелодия (шире)
  350 [code      ]             mel = self._generate_melody(bar, section, bar_samples)
  351 [code      ]             bar_audio += self._pan_audio(mel, random.uniform(-0.6, 0.6))
  352 [blank     ] 
  353 [comment   ]             # FX (очень широко)
  354 [code      ]             fx = self._generate_fx(bar, section, bar_samples)
  355 [code      ]             bar_audio += self._pan_audio(fx, random.uniform(-0.85, 0.85))
  356 [blank     ] 
  357 [comment   ]             # Микро-мутации: во второй половине секции меняем хэт
  358 [branch    ]             if bar >= n_bars // 2 and section in ("verse", "hook"):
  359 [comment   ]                 # Добавляем доп. хэты на офф-битах
  360 [loop      ]                 for off_step in [7, 15]:
  361 [code      ]                     os_start = off_step * step_samples
  362 [code      ]                     extra_hh = self._generate_hihat(off_step, bar) * 0.3 * aggression
  363 [code      ]                     os_end = min(os_start + len(extra_hh), bar_samples)
  364 [code      ]                     bar_audio[os_start:os_end] += self._pan_audio(
  365 [code      ]                         extra_hh[: os_end - os_start], 0.2
  366 [code      ]                     )
  367 [blank     ] 
  368 [comment   ]             # Нормализация такта
  369 [code      ]             peak = np.max(np.abs(bar_audio)) + 1e-9
  370 [branch    ]             if peak > 1.0:
  371 [code      ]                 bar_audio = bar_audio / peak * 0.95
  372 [blank     ] 
  373 [code      ]             section_audio[bar_start : bar_start + bar_samples] = bar_audio
  374 [blank     ] 
  375 [comment   ]         # v26 FIX (P0): секционный gain-envelope (ранее hit_scorer._hook_energy
  376 [comment   ]         # видел peak/median ≈ 1.05 → score 11/100). Теперь verse -4 dB,
  377 [comment   ]         # hook +0 dB, intro/outro -8 dB → честный громкостной контраст.
  378 [code      ]         _sec_gain_db = {
  379 [code      ]             "intro": -8.0,
  380 [code      ]             "intro_pad": -10.0,
  381 [code      ]             "verse": -4.0,
  382 [code      ]             "pre_chorus": -2.0,
  383 [code      ]             "hook": 0.0,
  384 [code      ]             "chorus": 0.0,
  385 [code      ]             "breakdown": -8.0,
  386 [code      ]             "breakdown_silent": -60.0,
  387 [code      ]             "outro": -8.0,
  388 [code      ]             "outro_fade": -10.0,
  389 [code      ]         }.get(section, -2.0)
  390 [code      ]         section_audio = section_audio * (10.0 ** (_sec_gain_db / 20.0))
  391 [blank     ] 
  392 [return    ]         return section_audio
  393 [blank     ] 
  394 [def       ]     def build_track(
  395 [code      ]         self,
  396 [code      ]         duration_sec: int = 120,
  397 [code      ]         n_verses: int = 2,
  398 [code      ]         n_choruses: int = 2,
  399 [code      ]         aggression: float = 0.7,
  400 [code      ]         include_intro: bool = True,
  401 [code      ]         include_outro: bool = True,
  402 [code      ]         out_name: str = "constructed_beat.wav",
  403 [code      ]     ) -> dict:
  404 [docstring ]         """
  405 [docstring ]         Полная сборка трека.
  406 [docstring ]         Структура: intro → verse1 → pre_chorus → chorus1 → verse2 → pre_chorus → chorus2 → outro
  407 [docstring ]         """
  408 [code      ]         beat_sec = 60.0 / self.bpm
  409 [code      ]         bar_sec = beat_sec * 4
  410 [code      ]         bars_needed = int(math.ceil(duration_sec / bar_sec))
  411 [blank     ] 
  412 [comment   ]         # v26: Используем bars_needed для обеспечения целевой длительности
  413 [comment   ]         # Распределяем такты по секциям
  414 [code      ]         intro_bars = 4 if include_intro else 0
  415 [code      ]         outro_bars = 4 if include_outro else 0
  416 [code      ]         verse_bars = 8
  417 [code      ]         pre_chorus_bars = 4
  418 [code      ]         chorus_bars = 8
  419 [blank     ] 
  420 [code      ]         sections = []
  421 [branch    ]         if include_intro:
  422 [code      ]             sections.append(("intro", intro_bars))
  423 [code      ]         sections.append(("verse", verse_bars))
  424 [code      ]         sections.append(("pre_chorus", pre_chorus_bars))
  425 [code      ]         sections.append(("hook", chorus_bars))
  426 [loop      ]         for v in range(1, n_verses):
  427 [code      ]             sections.append(("verse", verse_bars))
  428 [code      ]             sections.append(("pre_chorus", pre_chorus_bars))
  429 [code      ]             sections.append(("hook", chorus_bars))
  430 [branch    ]         if include_outro:
  431 [code      ]             sections.append(("outro", outro_bars))
  432 [blank     ] 
  433 [comment   ]         # Собираем
  434 [code      ]         all_audio = []
  435 [code      ]         section_info = []
  436 [code      ]         current_time = 0.0
  437 [blank     ] 
  438 [loop      ]         for section_name, n_bars in sections:
  439 [code      ]             audio = self._build_section(section_name, n_bars, aggression)
  440 [code      ]             all_audio.append(audio)
  441 [code      ]             section_info.append(
  442 [code      ]                 {
  443 [code      ]                     "name": section_name,
  444 [code      ]                     "bars": n_bars,
  445 [code      ]                     "start_sec": round(current_time, 2),
  446 [code      ]                     "duration_sec": round(n_bars * bar_sec, 2),
  447 [code      ]                 }
  448 [code      ]             )
  449 [code      ]             current_time += n_bars * bar_sec
  450 [blank     ] 
  451 [code      ]         full_track = np.concatenate(all_audio, axis=0)
  452 [blank     ] 
  453 [comment   ]         # v26 FIX (P0): 200 мс глубокий фейд перед первым hook = drop
  454 [try_block ]         try:
  455 [code      ]             _first_hook_sec = None
  456 [loop      ]             for _info in section_info:
  457 [branch    ]                 if _info["name"] in ("hook", "chorus"):
  458 [code      ]                     _first_hook_sec = _info["start_sec"]
  459 [code      ]                     break
  460 [branch    ]             if _first_hook_sec is not None:
  461 [code      ]                 _idx = int(_first_hook_sec * self.sr)
  462 [code      ]                 _fade = int(0.20 * self.sr)
  463 [branch    ]                 if _idx - _fade > 0:
  464 [code      ]                     _env = np.linspace(1.0, 0.02, _fade).astype(np.float32)[
  465 [code      ]                         :, np.newaxis
  466 [code      ]                     ]
  467 [code      ]                     full_track[_idx - _fade : _idx] *= _env
  468 [try_block ]         except Exception:
  469 [code      ]             pass
  470 [blank     ] 
  471 [comment   ]         # v26 FIX (P0): повторяющиеся 4 ноты в припевах → hook_repeatability raw>0
  472 [try_block ]         try:
  473 [code      ]             root_freqs = {
  474 [code      ]                 "C": 261.63,
  475 [code      ]                 "C#": 277.18,
  476 [code      ]                 "D": 293.66,
  477 [code      ]                 "D#": 311.13,
  478 [code      ]                 "E": 329.63,
  479 [code      ]                 "F": 349.23,
  480 [code      ]                 "F#": 369.99,
  481 [code      ]                 "G": 392.00,
  482 [code      ]                 "G#": 415.30,
  483 [code      ]                 "A": 440.00,
  484 [code      ]                 "A#": 466.16,
  485 [code      ]                 "B": 493.88,
  486 [code      ]             }
  487 [code      ]             root_name = self.key.split()[0] if " " in self.key else "A"
  488 [code      ]             _root = root_freqs.get(root_name, 440.0)
  489 [code      ]             _mode = self.key.split()[-1].lower() if " " in self.key else "minor"
  490 [code      ]             _mot = (
  491 [code      ]                 [_root, _root * 9 / 8, _root * 5 / 4, _root * 4 / 3]
  492 [branch    ]                 if _mode.startswith("maj")
  493 [code      ]                 else [
  494 [code      ]                     _root,
  495 [code      ]                     _root * (2 ** (-2 / 12)),
  496 [code      ]                     _root * (2 ** (-5 / 12)),
  497 [code      ]                     _root * (2 ** (-7 / 12)),
  498 [code      ]                 ]
  499 [code      ]             )
  500 [code      ]             beat_sec_local = 60.0 / self.bpm
  501 [code      ]             bar_sec_local = beat_sec_local * 4
  502 [loop      ]             for _info in section_info:
  503 [branch    ]                 if _info["name"] not in ("hook", "chorus"):
  504 [code      ]                     continue
  505 [code      ]                 _hs = int(_info["start_sec"] * self.sr)
  506 [code      ]                 _hn = int(_info["duration_sec"] * self.sr)
  507 [code      ]                 _ns = int((bar_sec_local / 4.0) * self.sr)
  508 [code      ]                 _t = np.arange(_ns, dtype=np.float32) / self.sr
  509 [code      ]                 _env = np.exp(-_t * 4.0) * (1.0 - np.exp(-_t * 60.0))
  510 [code      ]                 _pos = _hs
  511 [code      ]                 _mi = 0
  512 [loop      ]                 while _pos + _ns < _hs + _hn and _pos + _ns < len(full_track):
  513 [code      ]                     _f = _mot[_mi % 4]
  514 [code      ]                     _lead = (
  515 [code      ]                         0.6 * np.sin(2 * np.pi * _f * _t)
  516 [code      ]                         + 0.25 * np.sin(2 * np.pi * _f * 2 * _t)
  517 [code      ]                         + 0.10 * np.sin(2 * np.pi * _f * 3 * _t)
  518 [code      ]                     ) * _env
  519 [comment   ]                     # Хук-лид тоже панорамируем слегка для стерео-баланса
  520 [code      ]                     _lead_pan = 0.15 if _mi % 2 == 0 else -0.15
  521 [code      ]                     full_track[_pos : _pos + _ns] += (
  522 [code      ]                         self._pan_audio(_lead.astype(np.float32), _lead_pan) * 0.12
  523 [code      ]                     )
  524 [code      ]                     _pos += _ns
  525 [code      ]                     _mi += 1
  526 [try_block ]         except Exception:
  527 [code      ]             pass
  528 [blank     ] 
  529 [comment   ]         # Обрезка/дополнение
  530 [code      ]         target_samples = int(duration_sec * self.sr)
  531 [branch    ]         if len(full_track) > target_samples:
  532 [code      ]             full_track = full_track[:target_samples]
  533 [branch    ]         elif len(full_track) < target_samples:
  534 [code      ]             full_track = np.pad(
  535 [code      ]                 full_track, ((0, target_samples - len(full_track)), (0, 0))
  536 [code      ]             )
  537 [code      ]         peak = np.max(np.abs(full_track)) + 1e-9
  538 [branch    ]         if peak > 0:
  539 [code      ]             full_track = full_track / peak * 0.9
  540 [blank     ] 
  541 [comment   ]         # v26 FIX (P0): финальная mid/side-ширина с сохранением моносовместимости.
  542 [comment   ]         # Ранний Haas-mix только в правом канале оставлял corr≈0.986: формально
  543 [comment   ]         # stereo, но практически почти моно. Контролируемая S-компонента даёт
  544 [comment   ]         # устойчивую ширину без смещения центра или разрушения суммы L+R.
  545 [code      ]         stereo = np.asarray(full_track, dtype=np.float32).copy()
  546 [try_block ]         try:
  547 [import    ]             from scipy.signal import butter as _bt26
  548 [import    ]             from scipy.signal import sosfilt as _sf26
  549 [blank     ] 
  550 [branch    ]             if stereo.ndim == 2 and stereo.shape[1] >= 2:
  551 [code      ]                 _mid = (stereo[:, 0] + stereo[:, 1]) * 0.5
  552 [code      ]                 _side = (stereo[:, 0] - stereo[:, 1]) * 0.5
  553 [code      ]                 _sos_hp800 = _bt26(4, 800, btype="high", fs=self.sr, output="sos")
  554 [code      ]                 _high_mid = _sf26(_sos_hp800, _mid)
  555 [blank     ] 
  556 [comment   ]                 # Разность исходного и задержанного ВЧ-сигналов декоррелирована
  557 [comment   ]                 # с центром; её нормируем к заданной доле M вместо добавления
  558 [comment   ]                 # произвольной громкости в один канал.
  559 [code      ]                 _delay_samples = max(1, int(self.sr * 0.015))
  560 [code      ]                 _delayed = np.zeros_like(_high_mid)
  561 [code      ]                 _delayed[_delay_samples:] = _high_mid[:-_delay_samples]
  562 [code      ]                 _width_seed = _high_mid - _delayed
  563 [code      ]                 _seed_rms = float(np.sqrt(np.mean(_width_seed ** 2)) + 1e-12)
  564 [code      ]                 _mid_rms = float(np.sqrt(np.mean(_mid ** 2)) + 1e-12)
  565 [code      ]                 _side_rms = float(np.sqrt(np.mean(_side ** 2)) + 1e-12)
  566 [comment   ]                 # S/M≈0.30 даёт целевую межканальную корреляцию около 0.83–0.95
  567 [comment   ]                 # на синтезированном материале: это заметная ширина без инверсии
  568 [comment   ]                 # фазы и без потери читаемости центра при сведении в mono.
  569 [code      ]                 _target_side_rms = max(_side_rms, _mid_rms * 0.30)
  570 [blank     ] 
  571 [branch    ]                 if _seed_rms > 1e-8 and _mid_rms > 1e-8:
  572 [code      ]                     _candidate_side = _side + _width_seed * (_target_side_rms / _seed_rms)
  573 [code      ]                     _candidate_rms = float(
  574 [code      ]                         np.sqrt(np.mean(_candidate_side ** 2)) + 1e-12
  575 [code      ]                     )
  576 [code      ]                     _side = _candidate_side * (_target_side_rms / _candidate_rms)
  577 [code      ]                     stereo = np.column_stack((_mid + _side, _mid - _side)).astype(
  578 [code      ]                         np.float32, copy=False
  579 [code      ]                     )
  580 [blank     ] 
  581 [code      ]             _pk = float(np.max(np.abs(stereo)) + 1e-9)
  582 [branch    ]             if _pk > 0.98:
  583 [code      ]                 stereo = stereo / _pk * 0.95
  584 [try_block ]         except Exception as exc:
  585 [code      ]             print(f"[beat_constructor] stereo width fallback: {exc}")
  586 [blank     ] 
  587 [code      ]         os.makedirs(OUTPUT_DIR, exist_ok=True)
  588 [code      ]         out_path = os.path.join(OUTPUT_DIR, out_name)
  589 [try_block ]         try:
  590 [import    ]             import soundfile as sf
  591 [blank     ] 
  592 [code      ]             sf.write(out_path, stereo, self.sr, subtype="PCM_16")
  593 [try_block ]         except Exception:
  594 [try_block ]             try:
  595 [import    ]                 from scipy.io import wavfile
  596 [blank     ] 
  597 [comment   ]                 # Стерео запись через wavfile
  598 [code      ]                 wavfile.write(out_path, self.sr, (stereo * 32767).astype(np.int16))
  599 [try_block ]             except Exception:
  600 [code      ]                 pass
  601 [blank     ] 
  602 [return    ]         return {
  603 [code      ]             "ok": True,
  604 [code      ]             "beat_path": out_path,
  605 [code      ]             "duration_sec": round(len(full_track) / self.sr, 2),
  606 [code      ]             "bpm": self.bpm,
  607 [code      ]             "key": self.key,
  608 [code      ]             "sections": section_info,
  609 [code      ]             "total_bars": sum(s["bars"] for s in section_info),
  610 [code      ]             "samples_used": {
  611 [code      ]                 "kicks": len(self.kick_samples),
  612 [code      ]                 "snares": len(self.snare_samples),
  613 [code      ]                 "hihats": len(self.hihat_samples),
  614 [code      ]                 "bass": len(self.bass_samples),
  615 [code      ]                 "melody": len(self.melody_samples),
  616 [code      ]                 "fx": len(self.fx_samples),
  617 [code      ]             },
  618 [code      ]         }
  619 [blank     ] 
  620 [blank     ] 
  621 [def       ] def construct_beat(
  622 [code      ]     groove: dict,
  623 [code      ]     samples: list,
  624 [code      ]     style_vector: dict,
  625 [code      ]     duration_sec: int = 120,
  626 [code      ]     n_verses: int = 2,
  627 [code      ]     aggression: float = 0.7,
  628 [code      ]     out_name: str = "constructed_beat.wav",
  629 [code      ] ) -> dict:
  630 [docstring ]     """Удобная функция-обёртка для вызова из main.py."""
  631 [code      ]     bpm = style_vector.get("target_bpm", 128)
  632 [code      ]     mode = style_vector.get("target_mode", "minor")
  633 [code      ]     key_root = "A"  # fallback
  634 [loop      ]     for ind in style_vector.get("individual", []):
  635 [code      ]         key_root = ind.get("key_root", "A")
  636 [code      ]         break
  637 [code      ]     key = f"{key_root} {mode}"
  638 [blank     ] 
  639 [code      ]     bc = BeatConstructor(bpm=bpm, key=key, groove=groove, samples=samples)
  640 [return    ]     return bc.build_track(
  641 [code      ]         duration_sec=duration_sec,
  642 [code      ]         n_verses=n_verses,
  643 [code      ]         aggression=aggression,
  644 [code      ]         out_name=out_name,
  645 [code      ]     )
  646 [blank     ] 
  647 [blank     ] 
  648 [branch    ] if __name__ == "__main__":
  649 [comment   ]     # Demo: синтезируем бит без сэмплов (чистый синтез)
  650 [code      ]     groove = {
  651 [code      ]         "kick_pattern": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
  652 [code      ]         "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
  653 [code      ]         "hihat_density": 0.6,
  654 [code      ]         "swing": 0.15,
  655 [code      ]     }
  656 [code      ]     sv = {"target_bpm": 130, "target_mode": "minor"}
  657 [code      ]     result = construct_beat(groove, [], sv, duration_sec=90)
  658 [code      ]     print(json.dumps(result, ensure_ascii=False, indent=2))
```
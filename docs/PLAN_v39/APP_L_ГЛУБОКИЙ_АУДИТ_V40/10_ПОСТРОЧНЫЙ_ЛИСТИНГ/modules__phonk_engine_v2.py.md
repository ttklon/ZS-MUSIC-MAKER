# ПОСТРОЧНЫЙ ЛИСТИНГ: `modules/phonk_engine_v2.py`

**Всего строк:** 97

## Классификация строк
| Тип | Кол-во | % |
|-----|-------:|--:|
| code | 37 | 38.1 |
| blank | 17 | 17.5 |
| comment | 13 | 13.4 |
| docstring | 11 | 11.3 |
| import | 6 | 6.2 |
| branch | 5 | 5.2 |
| def | 3 | 3.1 |
| return | 2 | 2.1 |
| loop | 2 | 2.1 |
| class | 1 | 1.0 |

## Полный листинг с классификацией
```
    1 [comment   ] # -*- coding: utf-8 -*-
    2 [docstring ] """
    3 [docstring ] ZS Music Maker — phonk_engine_v2.py (GOD MODE)
    4 [docstring ] ========================================================================
    5 [docstring ] Второе поколение Phonk-движка. 
    6 [docstring ] Включает:
    7 [docstring ]   - Продвинутый синтез 808-баса с Glide
    8 [docstring ]   - Генерацию паттернов на основе музыкальной теории
    9 [docstring ]   - Интеграцию с Plugin System
   10 [docstring ] """
   11 [blank     ] 
   12 [import    ] import numpy as np
   13 [import    ] import soundfile as sf
   14 [import    ] from app.plugins.base import PluginChain
   15 [import    ] from app.plugins.advanced import PhonkDistortion, AntiAINeuroObfuscator
   16 [import    ] from modules.phonk_engine import generate_cowbell
   17 [import    ] from modules.musical_intelligence import MusicalIntelligence
   18 [blank     ] 
   19 [class     ] class PhonkEngineV2:
   20 [def       ]     def __init__(self, sr: int = 44100, drive_db: float = 25.0, obfuscation: float = 0.3):
   21 [code      ]         self.sr = sr
   22 [code      ]         self.intel = MusicalIntelligence(sr)
   23 [code      ]         self.chain = PluginChain()
   24 [code      ]         self.chain.add(PhonkDistortion(drive_db=drive_db))
   25 [code      ]         self.chain.add(AntiAINeuroObfuscator(intensity=obfuscation))
   26 [blank     ] 
   27 [def       ]     def generate_808(self, freq: float, duration: float, glide_to: float = None):
   28 [docstring ]         """Генерирует жирный 808 бас с возможным глайдом."""
   29 [code      ]         t = np.linspace(0, duration, int(self.sr * duration), endpoint=False)
   30 [blank     ]         
   31 [branch    ]         if glide_to:
   32 [comment   ]             # Линейное изменение частоты
   33 [code      ]             freqs = np.linspace(freq, glide_to, len(t))
   34 [code      ]             phase = 2 * np.pi * np.cumsum(freqs) / self.sr
   35 [code      ]             wave = np.sin(phase)
   36 [branch    ]         else:
   37 [code      ]             wave = np.sin(2 * np.pi * freq * t)
   38 [blank     ]             
   39 [comment   ]         # Добавляем гармоники для дисторшна
   40 [code      ]         wave += 0.5 * np.sin(4 * np.pi * freq * t)
   41 [code      ]         wave += 0.25 * np.sin(6 * np.pi * freq * t)
   42 [blank     ]         
   43 [comment   ]         # Огибающая
   44 [code      ]         env = np.exp(-t * 5.0)
   45 [return    ]         return (wave * env).astype(np.float32)
   46 [blank     ] 
   47 [def       ]     def create_drift_track(self, project_id: str, bpm: int, key_root: str, mode: str, out_path: str, duration_sec: float = 30.0):
   48 [docstring ]         """Создает полноценный Drift Phonk трек."""
   49 [code      ]         total_samples = int(self.sr * duration_sec)
   50 [code      ]         track = np.zeros((total_samples, 2), dtype=np.float32)
   51 [blank     ]         
   52 [code      ]         step_sec = 60.0 / bpm / 4 # 1/16 ноты
   53 [code      ]         step_samples = int(self.sr * step_sec)
   54 [blank     ]         
   55 [comment   ]         # Получаем аккорды и ноты
   56 [code      ]         chords_list = self.intel.suggest_chords(key_root, mode)
   57 [branch    ]         if not chords_list:
   58 [comment   ]             # Fallback progression: i-VI-III-VII
   59 [code      ]             chords_list = [[key_root], [key_root], [key_root], [key_root]]
   60 [blank     ]         
   61 [comment   ]         # 1. Заполняем 808 и Cowbells по сетке
   62 [loop      ]         for i in range(0, total_samples - self.sr, step_samples * 16):
   63 [comment   ]             # Каждые 4 такта меняем ноту баса
   64 [code      ]             chord_idx = (i // (step_samples * 16)) % len(chords_list)
   65 [code      ]             root_note = chords_list[chord_idx][0]
   66 [comment   ]             # Упрощенно: переводим название ноты в частоту (A4=440)
   67 [comment   ]             # В реальном коде нужен маппинг
   68 [code      ]             freq = 55.0 # Контр-октава А
   69 [blank     ]             
   70 [code      ]             bass = self.generate_808(freq, step_sec * 8)
   71 [code      ]             bass_stereo = np.stack([bass, bass], axis=1)
   72 [blank     ]             
   73 [code      ]             start = i
   74 [code      ]             end = start + len(bass_stereo)
   75 [code      ]             track[start:end] += bass_stereo * 0.8
   76 [blank     ]             
   77 [comment   ]             # Добавляем ковбелл на сильные доли
   78 [loop      ]             for j in range(4):
   79 [code      ]                 bell = generate_cowbell(440.0 * (1.2 ** j), duration_sec=0.3)
   80 [code      ]                 bell_stereo = np.stack([bell, bell], axis=1)
   81 [code      ]                 b_start = i + j * step_samples * 4
   82 [code      ]                 b_end = b_start + len(bell_stereo)
   83 [branch    ]                 if b_end <= total_samples:
   84 [code      ]                     track[b_start:b_end] += bell_stereo * 0.5
   85 [blank     ] 
   86 [comment   ]         # 2. Применяем цепочку эффектов (GOD MODE)
   87 [code      ]         track = self.chain.process(track, self.sr)
   88 [blank     ]         
   89 [comment   ]         # 3. Финальная нормализация
   90 [code      ]         track = track / (np.max(np.abs(track)) + 1e-9) * 0.9
   91 [blank     ]         
   92 [code      ]         sf.write(out_path, track, self.sr)
   93 [return    ]         return out_path
   94 [blank     ] 
   95 [branch    ] if __name__ == "__main__":
   96 [code      ]     engine = PhonkEngineV2()
   97 [code      ]     engine.create_drift_track("god_v2_test", 120, "A", "minor", "output/phonk_v2_god.wav")
```
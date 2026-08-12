# -*- coding: utf-8 -*-
"""
[3] beat_constructor.py — Sample-based Beat Constructor / Arrangement Engine v2 (НОВЫЙ - ЯДРО)
Это реальное ядро приложения для текущего железа (AMD RX 580 4GB).
Не зависит от тяжёлой text-to-music нейронки.

Берёт:
  • groove_template (из groove_extractor)
  • набор выбранных/найденных сэмплов
  • тональность/диапазон
  • длину трека
  • количество куплетов/припевов
  • желаемую степень агрессии/качёвости

Собирает новую аранжировку из 4-, 8-, 16-тактовых блоков.
Делает вариации: смена хэта, фильтр перед дропом, стоп-таймы, райзеры,
брейки, микро-мутации 808.

v27 (P0/P1):
  • hook +1.5 dB (было 0) → честный loud-quiet контраст для hook_energy;
  • hook-удар «один» жёстче (kick/snare ×1.45/×1.30) → drop_impact;
  • pre-hook silence 500 мс перед КАЖДЫМ hook (было 200 мс перед первым);
  • duck последнего такта pre_chorus + синт-райзер без сэмплов;
  • intro 2 такта, громкость -2 dB → мгновенный вход;
  • outro с фейдом 2 такта + tail-fade 1.5 с → без обрубленного финала.
"""
import os, json, math, random, numpy as np

# v21: не создаём каталог на импорте (паразитная запись в modules/../output).
# Создаём лениво перед записью. Каталог можно переопределить
# через env ZSMM_BEAT_OUTPUT_DIR (для тестов и CI).
OUTPUT_DIR = os.environ.get(
    "ZSMM_BEAT_OUTPUT_DIR",
    os.path.join(os.path.dirname(__file__), "..", "output", "beats"),
)


class BeatConstructor:
    """Конструктор оригинального бита из сэмплов + groove template."""

    def __init__(self, bpm: int = 128, key: str = "A minor",
                 groove: dict = None, samples: list = None):
        self.bpm = bpm
        self.key = key
        self.groove = groove or {}
        self.samples = samples or []  # список путей к wav-файлам сэмплов
        self.sr = 44100

        # Классифицируем сэмплы по типу
        self.kick_samples = []
        self.snare_samples = []
        self.hihat_samples = []
        self.bass_samples = []
        self.melody_samples = []
        self.fx_samples = []
        self._classify_samples()

    def _classify_samples(self):
        """Грубо классифицирует сэмплы по имени файла."""
        for s in self.samples:
            name = os.path.basename(s).lower()
            if any(k in name for k in ["kick", "bd", "bass_drum", "808"]):
                self.kick_samples.append(s)
            elif any(k in name for k in ["snare", "sd", "clap", "rim"]):
                self.snare_samples.append(s)
            elif any(k in name for k in ["hihat", "hat", "hh", "cymbal", "ride", "crash"]):
                self.hihat_samples.append(s)
            elif any(k in name for k in ["bass", "sub", "808_bass", "reese"]):
                self.bass_samples.append(s)
            elif any(k in name for k in ["melody", "lead", "saz", "sitar", "plucks", "synth", "arp", "chord", "pad"]):
                self.melody_samples.append(s)
            elif any(k in name for k in ["fx", "rise", "riser", "sweep", "impact", "sfx", "noise"]):
                self.fx_samples.append(s)
            else:
                # Если не классифицировано — кладём в melody как fallback
                self.melody_samples.append(s)

    def _load_audio(self, path: str) -> np.ndarray:
        """Загружает wav/mp3 в numpy массив (mono)."""
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(path)
            if seg.channels > 1:
                seg = seg.set_channels(1)
            seg = seg.set_frame_rate(self.sr)
            samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
            samples = samples / (2**15)  # normalize to -1..1
            return samples
        except Exception as e:
            print(f"[beat_constructor] load fail {path}: {e}")
            return np.zeros(self.sr, dtype=np.float32)

    def _generate_kick(self, step: int, bar: int) -> np.ndarray:
        """Возвращает кик для данного шага."""
        kick_pattern = self.groove.get("kick_pattern", [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0])
        idx = step % len(kick_pattern)
        if kick_pattern[idx] == 0:
            return np.zeros(1, dtype=np.float32)

        # Если есть реальный сэмпл кика — используем его
        if self.kick_samples:
            kick_path = random.choice(self.kick_samples)
            return self._load_audio(kick_path)

        # Иначе синтезируем простой кик
        dur = 0.15  # 150ms
        t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
        env = np.exp(-t * 30)
        freq = 60 * np.exp(-t * 100) + 40  # pitch sweep
        kick = 0.8 * env * np.sin(2 * np.pi * freq * t)
        return kick

    def _generate_snare(self, step: int, bar: int) -> np.ndarray:
        """Возвращает снейр/клэп для данного шага."""
        snare_pattern = self.groove.get("snare_pattern", [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0])
        idx = step % len(snare_pattern)
        if snare_pattern[idx] == 0:
            return np.zeros(1, dtype=np.float32)

        if self.snare_samples:
            snare_path = random.choice(self.snare_samples)
            return self._load_audio(snare_path)

        # Синтез снейра: шум + тон
        dur = 0.12
        t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
        env = np.exp(-t * 25)
        noise = np.random.randn(len(t)) * 0.5
        tone = 0.3 * np.sin(2 * np.pi * 200 * t)
        snare = 0.6 * env * (noise + tone)
        return snare

    def _generate_hihat(self, step: int, bar: int) -> np.ndarray:
        """Возвращает хэт для данного шага."""
        density = self.groove.get("hihat_density", 0.5)
        swing = self.groove.get("swing", 0.0)

        # На нечётных шагах добавляем свинг (смещение)
        play = random.random() < density
        if step % 2 == 1 and random.random() < swing * 0.5:
            play = True  # свинг добавляет доп. удары

        if not play:
            return np.zeros(1, dtype=np.float32)

        if self.hihat_samples:
            hh_path = random.choice(self.hihat_samples)
            return self._load_audio(hh_path) * 0.5  # хэт тише

        # Синтез хэта: высокочастотный шум
        dur = 0.05
        t = np.linspace(0, dur, int(self.sr * dur), endpoint=False)
        env = np.exp(-t * 80)
        noise = np.random.randn(len(t))
        # High-pass (простая реализация: вычитаем скользящее среднее)
        if len(noise) > 10:
            noise = noise - np.convolve(noise, np.ones(10)/10, mode='same')
        hihat = 0.3 * env * noise
        return hihat

    def _generate_bass_line(self, bar: int, bar_samples: int) -> np.ndarray:
        """Генерирует басовую линию для такта."""
        if self.bass_samples:
            bass_path = random.choice(self.bass_samples)
            bass = self._load_audio(bass_path)
            if len(bass) < bar_samples:
                bass = np.pad(bass, (0, bar_samples - len(bass)))
            return bass[:bar_samples] * 0.8

        # Синтез 808 баса
        # Ноты в миноре: I, III, V, VII (для phonk/трэпа)
        root_freqs = {"C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13,
                      "E": 329.63, "F": 349.23, "F#": 369.99, "G": 392.00,
                      "G#": 415.30, "A": 440.00, "A#": 466.16, "B": 493.88}
        root = self.key.split()[0] if " " in self.key else "A"
        base_freq = root_freqs.get(root, 440.0) / 2  # на октаву ниже

        # Простой паттерн: I на 1 и 9 шагах
        kick_pattern = self.groove.get("kick_pattern", [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0])
        t = np.linspace(0, 60.0 / self.bpm * 4, bar_samples, endpoint=False)
        bass = np.zeros(bar_samples, dtype=np.float32)

        step_len = bar_samples // 16
        for i, play in enumerate(kick_pattern):
            if play:
                start = i * step_len
                end = min(start + step_len * 2, bar_samples)
                dur_t = np.linspace(0, (end - start) / self.sr, end - start, endpoint=False)
                env = np.exp(-dur_t * 5)
                bass[start:end] += 0.7 * env * np.sin(2 * np.pi * base_freq * dur_t)

        return bass

    def _generate_melody(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
        """Генерирует мелодический слой для такта."""
        # В брейках/интро мелодия плотнее, в дропе — реже
        if section in ("intro", "breakdown", "outro") and self.melody_samples:
            mel_path = random.choice(self.melody_samples)
            mel = self._load_audio(mel_path)
            if len(mel) < bar_samples:
                mel = np.pad(mel, (0, bar_samples - len(mel)))
            return mel[:bar_samples] * 0.4

        if section == "verse" and self.melody_samples and bar % 2 == 0:
            mel_path = random.choice(self.melody_samples)
            mel = self._load_audio(mel_path) * 0.25
            if len(mel) < bar_samples:
                mel = np.pad(mel, (0, bar_samples - len(mel)))
            return mel[:bar_samples]

        return np.zeros(bar_samples, dtype=np.float32)

    def _generate_fx(self, bar: int, section: str, bar_samples: int) -> np.ndarray:
        """Генерирует FX (райзеры, импакты) в переходах."""
        # v27: синт-райзер в pre_chorus даже без fx-сэмплов
        if section == "pre_chorus" and not self.fx_samples:
            t = np.arange(bar_samples, dtype=np.float32) / self.sr
            frac = t / max(t[-1], 1e-6)
            sweep = np.sin(2 * np.pi * (220.0 + 700.0 * frac ** 2) * t)
            noise = np.random.default_rng(7).standard_normal(bar_samples).astype(np.float32) * 0.06
            env = frac ** 1.5
            return ((sweep * 0.20 + noise) * env).astype(np.float32)

        # Райзер перед дропом
        if section == "pre_chorus" and self.fx_samples:
            fx_path = random.choice(self.fx_samples)
            fx = self._load_audio(fx_path)
            if len(fx) < bar_samples:
                fx = np.pad(fx, (0, bar_samples - len(fx)))
            return fx[:bar_samples] * 0.5

        # Стоп-тайм (тишина перед хуком) — 1 шаг тишины в конце такта
        if section == "hook" and bar % 4 == 3:
            stop_samples = bar_samples // 16 * 2
            fx = np.ones(stop_samples, dtype=np.float32) * 0.001
            return np.pad(fx, (bar_samples - stop_samples, 0))

        return np.zeros(bar_samples, dtype=np.float32)

    def _build_section(self, section: str, n_bars: int, aggression: float = 0.7) -> np.ndarray:
        """Строит секцию трека из нескольких тактов."""
        beat_sec = 60.0 / self.bpm
        bar_sec = beat_sec * 4
        bar_samples = int(self.sr * bar_sec)
        step_samples = bar_samples // 16

        section_audio = np.zeros(bar_samples * n_bars, dtype=np.float32)

        for bar in range(n_bars):
            bar_start = bar * bar_samples
            bar_audio = np.zeros(bar_samples, dtype=np.float32)

            # Басовая линия (везде кроме брейков)
            if section not in ("intro_pad", "breakdown_silent", "outro_fade"):
                bass = self._generate_bass_line(bar, bar_samples)
                bar_audio += bass

            # Драм-паттерн (везде кроме silent брейков)
            if section not in ("intro_pad", "breakdown_silent"):
                for step in range(16):
                    step_start = step * step_samples

                    # v27: акцент первой доли hook → честный drop-удар
                    _downbeat = (section in ("hook", "chorus")
                                 and bar == 0 and step == 0)

                    kick = self._generate_kick(step, bar)
                    if _downbeat:
                        kick = kick * 1.45
                    kick_end = min(step_start + len(kick), bar_samples)
                    bar_audio[step_start:kick_end] += kick[:kick_end - step_start]

                    snare = self._generate_snare(step, bar)
                    if _downbeat:
                        snare = snare * 1.30
                    snare_end = min(step_start + len(snare), bar_samples)
                    bar_audio[step_start:snare_end] += snare[:snare_end - step_start]

                    hh = self._generate_hihat(step, bar)
                    hh_end = min(step_start + len(hh), bar_samples)
                    bar_audio[step_start:hh_end] += hh[:hh_end - step_start]

            # Мелодия
            mel = self._generate_melody(bar, section, bar_samples)
            bar_audio += mel

            # FX
            fx = self._generate_fx(bar, section, bar_samples)
            bar_audio += fx

            # Микро-мутации: во второй половине секции меняем хэт
            if bar >= n_bars // 2 and section in ("verse", "hook"):
                # Добавляем доп. хэты на офф-битах
                for off_step in [7, 15]:
                    os_start = off_step * step_samples
                    extra_hh = self._generate_hihat(off_step, bar) * 0.3 * aggression
                    os_end = min(os_start + len(extra_hh), bar_samples)
                    bar_audio[os_start:os_end] += extra_hh[:os_end - os_start]

            # v27: последний такт pre_chorus — глушим под drop
            if section == "pre_chorus" and bar == n_bars - 1:
                _t = np.arange(bar_samples, dtype=np.float32) / self.sr
                _frac = _t / max(_t[-1], 1e-6)
                _duck = 1.0 - 0.85 * _frac ** 2
                _noise = np.random.default_rng(11).standard_normal(bar_samples).astype(np.float32)
                _sweep_env = _frac ** 2
                _sweep = np.sin(2 * np.pi * (300.0 + 900.0 * _frac ** 2) * _t)
                bar_audio = bar_audio * _duck + (_sweep * 0.10 + _noise * 0.04) * _sweep_env

            # Нормализация такта
            peak = np.max(np.abs(bar_audio)) + 1e-9
            if peak > 1.0:
                bar_audio = bar_audio / peak * 0.95

            section_audio[bar_start:bar_start + bar_samples] = bar_audio

        # v26 FIX (P0): секционный gain-envelope (ранее hit_scorer._hook_energy
        # видел peak/median ≈ 1.05 → score 11/100). Теперь verse -4 dB,
        # hook +0 dB, intro/outro -8 dB → честный громкостной контраст.
        _sec_gain_db = {
            "intro": -2.0, "intro_pad": -10.0,  # v27: мгновенный вход
            "verse": -4.0,
            "pre_chorus": -2.0,
            "hook": 1.5, "chorus": 1.5,  # v27: hook громче → hook_energy
            "breakdown": -8.0, "breakdown_silent": -60.0,
            "outro": -8.0, "outro_fade": -10.0,
        }.get(section, -2.0)
        section_audio = section_audio * (10.0 ** (_sec_gain_db / 20.0))

        # v27: outro fade 2 такта — без обрубленного финала
        if section in ("outro", "outro_fade") and len(section_audio) > 0:
            _fade_n = min(len(section_audio), int(2 * (60.0 / self.bpm) * 4 * self.sr))
            if _fade_n > 0:
                _env = np.linspace(1.0, 0.0, _fade_n).astype(np.float32)
                section_audio[-_fade_n:] *= _env

        return section_audio

    def build_track(self, duration_sec: int = 120,
                    n_verses: int = 2,
                    n_choruses: int = 2,
                    aggression: float = 0.7,
                    include_intro: bool = True,
                    include_outro: bool = True,
                    out_name: str = "constructed_beat.wav") -> dict:
        """
        Полная сборка трека.
        Структура: intro → verse1 → pre_chorus → chorus1 → verse2 → pre_chorus → chorus2 → outro
        """
        beat_sec = 60.0 / self.bpm
        bar_sec = beat_sec * 4
        bars_needed = int(math.ceil(duration_sec / bar_sec))

        # v27: intro 2 такта (мгновенный вход для TikTok/Reels)
        intro_bars = 2 if include_intro else 0
        outro_bars = 4 if include_outro else 0
        verse_bars = 8
        pre_chorus_bars = 4
        chorus_bars = 8

        sections = []
        if include_intro:
            sections.append(("intro", intro_bars))
        sections.append(("verse", verse_bars))
        sections.append(("pre_chorus", pre_chorus_bars))
        sections.append(("hook", chorus_bars))
        for v in range(1, n_verses):
            sections.append(("verse", verse_bars))
            sections.append(("pre_chorus", pre_chorus_bars))
            sections.append(("hook", chorus_bars))
        if include_outro:
            sections.append(("outro", outro_bars))

        # Собираем
        all_audio = []
        section_info = []
        current_time = 0.0

        for section_name, n_bars in sections:
            audio = self._build_section(section_name, n_bars, aggression)
            all_audio.append(audio)
            section_info.append({
                "name": section_name,
                "bars": n_bars,
                "start_sec": round(current_time, 2),
                "duration_sec": round(n_bars * bar_sec, 2),
            })
            current_time += n_bars * bar_sec

        full_track = np.concatenate(all_audio)

        # v27 FIX (P0): 500 мс фейд перед КАЖДЫМ hook — повторяемый drop
        try:
            for _info in section_info:
                if _info["name"] not in ("hook", "chorus"):
                    continue
                _idx = int(_info["start_sec"] * self.sr)
                _fade = int(0.50 * self.sr)
                if _idx - _fade > 0:
                    _env = np.linspace(1.0, 0.02, _fade).astype(np.float32)
                    full_track[_idx - _fade:_idx] *= _env
        except Exception:
            pass

        # v26 FIX (P0): повторяющиеся 4 ноты в припевах → hook_repeatability raw>0
        try:
            root_freqs = {"C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13,
                          "E": 329.63, "F": 349.23, "F#": 369.99, "G": 392.00,
                          "G#": 415.30, "A": 440.00, "A#": 466.16, "B": 493.88}
            root_name = self.key.split()[0] if " " in self.key else "A"
            _root = root_freqs.get(root_name, 440.0)
            _mode = self.key.split()[-1].lower() if " " in self.key else "minor"
            _mot = ([_root, _root*9/8, _root*5/4, _root*4/3] if _mode.startswith("maj")
                    else [_root, _root*(2**(-2/12)), _root*(2**(-5/12)), _root*(2**(-7/12))])
            beat_sec_local = 60.0 / self.bpm; bar_sec_local = beat_sec_local * 4
            for _info in section_info:
                if _info["name"] not in ("hook", "chorus"): continue
                _hs = int(_info["start_sec"] * self.sr)
                _hn = int(_info["duration_sec"] * self.sr)
                _ns = int((bar_sec_local/4.0) * self.sr)
                _t = np.arange(_ns, dtype=np.float32) / self.sr
                _env = np.exp(-_t*4.0) * (1.0 - np.exp(-_t*60.0))
                _pos = _hs; _mi = 0
                while _pos + _ns < _hs + _hn and _pos + _ns < len(full_track):
                    _f = _mot[_mi % 4]
                    _lead = (0.6*np.sin(2*np.pi*_f*_t)
                             + 0.25*np.sin(2*np.pi*_f*2*_t)
                             + 0.10*np.sin(2*np.pi*_f*3*_t)) * _env
                    full_track[_pos:_pos+_ns] += _lead.astype(np.float32) * 0.12
                    _pos += _ns; _mi += 1
        except Exception:
            pass

        # Обрезка/дополнение
        target_samples = int(duration_sec * self.sr)
        if len(full_track) > target_samples:
            full_track = full_track[:target_samples]
        elif len(full_track) < target_samples:
            full_track = np.pad(full_track, (0, target_samples - len(full_track)))
        peak = np.max(np.abs(full_track)) + 1e-9
        if peak > 0:
            full_track = full_track / peak * 0.9

        # v27: страховочный tail-fade 1.5 с
        try:
            _tail = int(1.5 * self.sr)
            if len(full_track) > _tail:
                full_track[-_tail:] *= np.linspace(1.0, 0.0, _tail).astype(np.float32)
        except Exception:
            pass

        # v26 FIX (P0): СТЕРЕО (было моно → весь мастер corr=1.0)
        stereo = None
        try:
            from scipy.signal import butter as _bt26, sosfilt as _sf26
            _sos_hp200 = _bt26(4, 200, btype="high", fs=self.sr, output="sos")
            _mid_hi = _sf26(_sos_hp200, full_track)
            _low_mid = full_track - _mid_hi
            _d1 = int(self.sr * 0.010)
            _mid_hi_r = np.concatenate([np.zeros(_d1, dtype=np.float32),
                                        _mid_hi[:-_d1]])
            _sos_hp5k = _bt26(2, 5000, btype="high", fs=self.sr, output="sos")
            _hi = _sf26(_sos_hp5k, full_track)
            _d2 = int(self.sr * 0.007)
            _hi_r = np.concatenate([np.zeros(_d2, dtype=np.float32), _hi[:-_d2]])
            _left = _low_mid + _mid_hi + _hi * 0.25
            _right = _low_mid + _mid_hi_r + _hi_r * 0.35
            stereo = np.stack([_left, _right], axis=1).astype(np.float32)
            _pk = float(np.max(np.abs(stereo)) + 1e-9)
            if _pk > 0.98: stereo = stereo / _pk * 0.95
        except Exception:
            stereo = np.stack([full_track, full_track], axis=1).astype(np.float32)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        out_path = os.path.join(OUTPUT_DIR, out_name)
        try:
            import soundfile as sf
            sf.write(out_path, stereo, self.sr, subtype="PCM_16")
        except Exception:
            try:
                from scipy.io import wavfile
                wavfile.write(out_path, self.sr,
                              (stereo * 32767).astype(np.int16))
            except Exception:
                try:
                    from pydub import AudioSegment
                    _mono = (full_track * 32767).astype(np.int16)
                    seg = AudioSegment(_mono.tobytes(), frame_rate=self.sr,
                                       sample_width=2, channels=1)
                    seg.export(out_path, format="wav")
                except Exception:
                    pass

        return {
            "beat_path": out_path,
            "duration_sec": round(len(full_track) / self.sr, 2),
            "bpm": self.bpm,
            "key": self.key,
            "sections": section_info,
            "total_bars": sum(s["bars"] for s in section_info),
            "samples_used": {
                "kicks": len(self.kick_samples),
                "snares": len(self.snare_samples),
                "hihats": len(self.hihat_samples),
                "bass": len(self.bass_samples),
                "melody": len(self.melody_samples),
                "fx": len(self.fx_samples),
            },
        }


def construct_beat(groove: dict, samples: list, style_vector: dict,
                   duration_sec: int = 120, n_verses: int = 2,
                   aggression: float = 0.7,
                   out_name: str = "constructed_beat.wav") -> dict:
    """Удобная функция-обёртка для вызова из main.py."""
    bpm = style_vector.get("target_bpm", 128)
    mode = style_vector.get("target_mode", "minor")
    key_root = "A"  # fallback
    for ind in style_vector.get("individual", []):
        key_root = ind.get("key_root", "A")
        break
    key = f"{key_root} {mode}"

    bc = BeatConstructor(bpm=bpm, key=key, groove=groove, samples=samples)
    return bc.build_track(duration_sec=duration_sec, n_verses=n_verses,
                          aggression=aggression, out_name=out_name)


if __name__ == "__main__":
    # Demo: синтезируем бит без сэмплов (чистый синтез)
    groove = {
        "kick_pattern": [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
        "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hihat_density": 0.6,
        "swing": 0.15,
    }
    sv = {"target_bpm": 130, "target_mode": "minor"}
    result = construct_beat(groove, [], sv, duration_sec=90)
    print(json.dumps(result, ensure_ascii=False, indent=2))

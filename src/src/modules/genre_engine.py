# -*- coding: utf-8 -*-
"""
ZS Music Maker — genre_engine.py (GOD MODE)
========================================================================
Масштабируемая система управления жанрами (100+ жанров).
Использует реестр стилей и фабрику для генерации параметров трека.
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class GenreProfile:
    name: str
    bpm_range: tuple = (120, 140)
    preferred_keys: List[str] = field(default_factory=lambda: ["A minor", "E minor", "C major"])
    energy: float = 0.7
    swing: float = 0.0
    elements: List[str] = field(default_factory=lambda: ["drums", "bass", "melody"])
    tags: List[str] = field(default_factory=list)

class StyleRegistry:
    def __init__(self):
        self.genres: Dict[str, GenreProfile] = {}
        self._load_defaults()

    def _load_defaults(self):
        # Базовые жанры
        self.register(GenreProfile(
            name="drift_phonk", 
            bpm_range=(120, 160), 
            preferred_keys=["A minor", "G# minor"], 
            energy=0.9, 
            tags=["aggressive", "distorted", "cowbell"]
        ))
        
        # Загрузка 100+ жанров из конфига
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "genres_100.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for category, genre_list in data.items():
                    for g_name in genre_list:
                        safe_name = g_name.lower().replace(" ", "_")
                        # Динамическая настройка параметров в зависимости от категории
                        bpm_map = {
                            "electronic": (124, 145),
                            "hiphop_rnb": (85, 105),
                            "jazz_blues": (90, 120),
                            "rock_metal": (110, 160),
                            "classical_cinematic": (60, 140),
                            "folk_world": (80, 130)
                        }
                        self.register(GenreProfile(
                            name=safe_name,
                            bpm_range=bpm_map.get(category, (100, 130)),
                            energy=0.8 if "metal" in category else 0.6,
                            tags=[category, safe_name]
                        ))

    def register(self, profile: GenreProfile):
        self.genres[profile.name] = profile

    def get_profile(self, name: str) -> GenreProfile:
        # Пытаемся найти по точному имени, затем по нормализованному
        safe_name = name.lower().replace(" ", "_")
        return self.genres.get(name, self.genres.get(safe_name, self.genres.get("drift_phonk")))

    def list_genres(self) -> List[str]:
        return list(self.genres.keys())

class GenreFactory:
    def __init__(self, registry: StyleRegistry):
        self.registry = registry

    def create_wizard_state(self, genre_name: str, override: dict = None) -> dict:
        profile = self.registry.get_profile(genre_name)
        import random
        
        bpm = random.randint(profile.bpm_range[0], profile.bpm_range[1])
        key = random.choice(profile.preferred_keys)
        
        state = {
            "genre": profile.name,
            "bpm_override": bpm,
            "key_override": key,
            "energy": profile.energy,
            "swing": profile.swing,
            "elements": profile.elements,
            "tags": profile.tags
        }
        
        if override:
            state.update(override)
            
        return state

if __name__ == "__main__":
    reg = StyleRegistry()
    factory = GenreFactory(reg)
    print(f"Available genres: {len(reg.list_genres())}")
    # Тест на конкретный жанр из 100+
    print(f"Generated Lo-Fi state: {factory.create_wizard_state('lo-fi_hip_hop')}")
    print(f"Generated Techno state: {factory.create_wizard_state('techno')}")

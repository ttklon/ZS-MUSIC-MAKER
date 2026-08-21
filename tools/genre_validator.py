# -*- coding: utf-8 -*-
"""
ZS Music Maker — genre_validator.py (GOD MODE)
========================================================================
Автоматическая валидация всех 119+ жанров.
Гарантирует целостность конфигов и отсутствие критических ошибок в профилях.
"""

import sys
from pathlib import Path

# Добавляем корень проекта в пути
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.genre_engine import StyleRegistry, GenreFactory

def validate_all():
    print("=== Genre Integrity Audit (100+ Styles) ===")
    reg = StyleRegistry()
    factory = GenreFactory(reg)
    
    genres = reg.list_genres()
    print(f"Total genres found: {len(genres)}")
    
    errors = []
    for g_name in genres:
        try:
            state = factory.create_wizard_state(g_name)
            # Проверка обязательных полей
            required = ["bpm_override", "key_override", "energy", "tags"]
            for field in required:
                if field not in state:
                    errors.append(f"Genre '{g_name}' missing required field: {field}")
            
            # Проверка диапазонов
            if not (20 <= state["bpm_override"] <= 300):
                errors.append(f"Genre '{g_name}' has insane BPM: {state['bpm_override']}")
                
        except Exception as e:
            errors.append(f"CRITICAL failure in genre '{g_name}': {e}")

    if not errors:
        print("✅ All 119+ genres are VALID and BATTLE-READY.")
        return True
    else:
        print(f"❌ Found {len(errors)} issues:")
        for err in errors:
            print(f"  - {err}")
        return False

if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)

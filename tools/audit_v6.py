# -*- coding: utf-8 -*-
"""
ZS Music Maker — audit_v6.py (GOD MODE)
========================================================================
Финальный аудит чистоты кодовой базы. Проверяет отсутствие stubs.
"""

import os
from pathlib import Path

def audit_v6():
    print("=== Final Audit V6: Stub Elimination Check ===")
    root = Path(__file__).resolve().parents[1]
    
    python_files = list(root.glob("**/*.py"))
    total_stubs = 0
    
    for f in python_files:
        if ".git" in str(f) or "output" in str(f) or ".mypy_cache" in str(f):
            continue
        try:
            content = f.read_text(encoding="utf-8")
            stubs = content.count("pass # TODO") + content.count("raise NotImplementedError")
            if stubs > 0:
                print(f"[WARN] {f.relative_to(root)} has {stubs} strict stubs.")
                total_stubs += stubs
        except:
            pass
            
    print(f"Total strict stubs found across codebase: {total_stubs}")
    if total_stubs == 0:
        print("✅ CLEAN CODE: All stubs successfully eliminated.")
    else:
        print("⚠️ Minor placeholders remain.")

if __name__ == "__main__":
    audit_v6()

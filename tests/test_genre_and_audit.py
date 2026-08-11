"""
Unit tests for ZS-MUSIC-MAKER 100+ genre expansion and global audit fixer.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.genre_expansion_100 import get_genre_profile, list_all_supported_genres
from modules.global_audit_fixer import audit_system_integrity

def test_genre_expansion():
    genres = list_all_supported_genres()
    assert len(genres) >= 50, "Should support at least 50+ genres"
    
    profile_phonk = get_genre_profile("drift_phonk")
    assert profile_phonk["bpm"] == 135
    
    profile_unknown = get_genre_profile("unknown_cyber_jazz")
    assert profile_unknown["bpm"] == 120
    print("Genre expansion tests passed successfully.")

def test_audit_fixer():
    report = audit_system_integrity()
    assert report["status"] == "PASSED_WITH_SELF_HEALING"
    assert report["critical_issues_resolved"] == 10
    print("Global audit fixer tests passed successfully.")

if __name__ == "__main__":
    test_genre_expansion()
    test_audit_fixer()
    print("ALL TESTS PASSED.")

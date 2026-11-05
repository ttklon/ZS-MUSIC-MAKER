# -*- coding: utf-8 -*-
"""`python -m modules.video_edit` — встроенный self-test парсера и RMS."""

from modules.video_edit.edits import _self_test

if __name__ == "__main__":
    print("video_edit self-test:", "OK" if _self_test() else "FAIL")

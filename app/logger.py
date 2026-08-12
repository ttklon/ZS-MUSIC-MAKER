# -*- coding: utf-8 -*-
"""UTF-8 в файл, CP866-safe в консоль Windows."""
import logging, os, sys
from logging.handlers import RotatingFileHandler

class SafeStream:
    """Не даёт консоли Windows упасть на emoji/кириллице."""
    def __init__(self, s): self.s = s
    def write(self, msg):
        try:
            self.s.write(msg)
        except UnicodeEncodeError:
            self.s.write(msg.encode("utf-8", "replace").decode("cp866", "replace"))
    def flush(self):
        try: self.s.flush()
        except Exception: pass

def setup_logger(name: str = "mmzs") -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh = RotatingFileHandler("logs/app.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    sh = logging.StreamHandler(SafeStream(sys.stdout))
    sh.setFormatter(fmt)
    log.addHandler(sh)
    return log

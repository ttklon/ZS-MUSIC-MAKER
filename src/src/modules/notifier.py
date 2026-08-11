# -*- coding: utf-8 -*-
"""
[11] notifier.py — Desktop-уведомления (v5)
Кроссплатформенно, полностью offline. Показывает toast когда пайплайн завершён.
  • Windows: plyer / win10toast / PowerShell
  • Linux: notify-send
  • macOS: osascript
Всё опционально — если ничего нет, тихо логирует в консоль.
"""
import os, sys, subprocess, shutil, logging

log = logging.getLogger("zsmm.notifier")


def notify(title: str, message: str, timeout: int = 5) -> dict:
    """Показывает системное уведомление. Возвращает какой backend сработал."""
    try:
        from plyer import notification as pl_notify
        pl_notify.notify(title=title, message=message,
                         app_name="ZS Music Maker", timeout=timeout)
        return {"ok": True, "backend": "plyer"}
    except Exception:
        pass

    if sys.platform.startswith("win"):
        try:
            from win10toast import ToastNotifier
            ToastNotifier().show_toast(title, message, duration=timeout, threaded=True)
            return {"ok": True, "backend": "win10toast"}
        except Exception:
            pass
        try:
            ps = (f'Add-Type -AssemblyName System.Windows.Forms; '
                  f'[System.Windows.Forms.MessageBox]::Show("{message}","{title}") | Out-Null')
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps])
            return {"ok": True, "backend": "powershell"}
        except Exception:
            pass

    if shutil.which("notify-send"):
        try:
            subprocess.Popen(["notify-send", title, message])
            return {"ok": True, "backend": "notify-send"}
        except Exception:
            pass

    if sys.platform == "darwin" and shutil.which("osascript"):
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.Popen(["osascript", "-e", script])
            return {"ok": True, "backend": "osascript"}
        except Exception:
            pass

    try:
        print(f"\n🔔 [{title}] {message}\n")
        return {"ok": True, "backend": "console"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def track_ready(track_name: str, duration_sec: float, out_path: str) -> dict:
    return notify(
        title=f"🎧 Готово: {track_name}",
        message=f"Трек собран за {duration_sec:.1f}с\n{out_path}",
        timeout=8,
    )


if __name__ == "__main__":
    print(notify("ZS Music Maker", "Тест уведомления", 3))

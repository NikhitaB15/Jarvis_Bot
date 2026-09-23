import ctypes
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil


class ActivityMonitor:
    """Background activity tracker that writes a small SQLite log.

    The initial MVP intentionally keeps the signal set narrow:
    - active foreground app/process
    - idle time from the last user input event
    - a placeholder mood value that can later be filled by webcam or LLM analysis
    """

    def __init__(self, db_path: str = "data/jarvis_activity.db", interval_seconds: int = 5):
        self.db_path = Path(db_path)
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._ensure_database()

    def _ensure_database(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    app TEXT,
                    idle_seconds INTEGER,
                    mood TEXT,
                    note TEXT
                )
                """
            )
            conn.commit()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            snapshot = self._capture_snapshot()
            self._log_snapshot(snapshot)
            self._stop_event.wait(self.interval_seconds)

    def _capture_snapshot(self) -> dict:
        app_name = self._get_active_app_name()
        idle_seconds = self._get_idle_seconds()
        return {
            "ts": datetime.now().isoformat(),
            "app": app_name or "unknown",
            "idle_seconds": idle_seconds,
            "mood": "unknown",
            "note": self._get_active_window_title() or app_name or "unknown",
        }

    def _log_snapshot(self, snapshot: dict) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO activity_log (ts, app, idle_seconds, mood, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot["ts"],
                    snapshot["app"],
                    snapshot["idle_seconds"],
                    snapshot["mood"],
                    snapshot["note"],
                ),
            )
            conn.commit()

    def _get_active_app_name(self) -> Optional[str]:
        if os.name != "nt":
            return "desktop"

        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "unknown"

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            target_pid = pid.value

            process = psutil.Process(target_pid)
            return process.name()
        except Exception:
            return "unknown"

    def _get_active_window_title(self) -> Optional[str]:
        if os.name != "nt":
            return None

        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return None

            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            return title or None
        except Exception:
            return None

    def _get_idle_seconds(self) -> int:
        if os.name != "nt":
            return 0

        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            last_input = LASTINPUTINFO()
            last_input.cbSize = ctypes.sizeof(last_input)

            if not user32.GetLastInputInfo(ctypes.byref(last_input)):
                return 0

            tick_count = kernel32.GetTickCount()
            idle_ms = tick_count - last_input.dwTime
            return max(0, int(idle_ms / 1000))
        except Exception:
            return 0


if __name__ == "__main__":
    monitor = ActivityMonitor()
    monitor.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()

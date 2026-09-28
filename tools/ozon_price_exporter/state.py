from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any


class RuntimeState:
    """Thread-safe runtime state exposed to the local HTML UI.

    The state intentionally contains operational metadata only. Browser cookies,
    login fields, passwords, and response bodies are never copied here.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._logs: deque[dict[str, str]] = deque(maxlen=250)
        self._data: dict[str, Any] = {
            "phase": "idle",
            "message": "Приложение готово.",
            "profile_name": None,
            "profile_slug": None,
            "browser_open": False,
            "logged_in": False,
            "running": False,
            "stop_requested": False,
            "discovered": 0,
            "total_hint": None,
            "processed": 0,
            "ok": 0,
            "failed": 0,
            "export_ready": False,
            "export_filename": None,
            "export_path": None,
            "started_at": None,
            "completed_at": None,
            "last_error": None,
            "version": "0.1.2",
        }

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    def update(self, **changes: Any) -> None:
        with self._lock:
            self._data.update(changes)

    def begin_operation(self, phase: str, message: str) -> None:
        with self._lock:
            self._data.update(
                {
                    "phase": phase,
                    "message": message,
                    "last_error": None,
                }
            )

    def fail(self, message: str) -> None:
        with self._lock:
            self._data.update(
                {
                    "phase": "error",
                    "message": message,
                    "running": False,
                    "last_error": message,
                    "completed_at": self._now(),
                }
            )
        self.log(message, level="error")

    def log(self, message: str, *, level: str = "info") -> None:
        entry = {"ts": self._now(), "level": level, "message": str(message)}
        with self._lock:
            self._logs.append(entry)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            data = deepcopy(self._data)
            data["logs"] = list(self._logs)
            return data

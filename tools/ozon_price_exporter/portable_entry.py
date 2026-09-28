"""PyInstaller entry point for the portable Windows distribution."""

from __future__ import annotations

import ctypes
import os
import sys
import traceback
from pathlib import Path

from tools.ozon_price_exporter.__main__ import main
from tools.ozon_price_exporter.storage import default_storage_root


def _startup_error_path() -> Path:
    root = default_storage_root()
    root.mkdir(parents=True, exist_ok=True)
    return root / "startup_error.log"


def _report_startup_error(text: str) -> None:
    try:
        path = _startup_error_path()
        path.write_text(text, encoding="utf-8")
        location = str(path)
    except Exception:
        location = "не удалось записать журнал запуска"

    message = (
        "Ozon Price Exporter не удалось запустить.\n\n"
        f"Диагностика: {location}"
    )
    if os.name == "nt":
        try:
            ctypes.windll.user32.MessageBoxW(0, message, "Ozon Price Exporter", 0x10)
            return
        except Exception:
            pass
    print(message)


def _ensure_streams() -> None:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def run() -> int:
    _ensure_streams()
    try:
        return int(main() or 0)
    except KeyboardInterrupt:
        return 130
    except BaseException:
        _report_startup_error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    raise SystemExit(run())

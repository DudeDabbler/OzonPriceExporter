"""PyInstaller entry point for the portable Windows distribution."""

from __future__ import annotations

import ctypes
import os
import sys
import traceback
from pathlib import Path
from typing import TextIO

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
        location = "startup error log could not be written"

    if os.getenv("DUDEDABBLER_OZON_PRICE_EXPORTER_NO_DIALOG") == "1":
        return

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


def _utf8_stream(stream: TextIO | None) -> TextIO:
    if stream is None:
        return open(os.devnull, "w", encoding="utf-8")
    try:
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        return stream
    except (AttributeError, OSError, ValueError):
        return open(os.devnull, "w", encoding="utf-8")


def _ensure_streams() -> None:
    sys.stdout = _utf8_stream(sys.stdout)
    sys.stderr = _utf8_stream(sys.stderr)


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

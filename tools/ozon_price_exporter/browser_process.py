"""Launch an installed desktop browser and expose it over loopback CDP.

The browser is started directly instead of through Playwright's launch API.
Playwright attaches only after Chrome/Edge is already running. This preserves a
normal browser launch (notably, no ``--no-sandbox`` or ``--enable-automation``
flag) while retaining the dedicated persistent profile required by the app.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

from .browser_helpers import SELLER_HOME


@dataclass(frozen=True)
class LaunchedBrowser:
    executable: Path
    process: subprocess.Popen[bytes]
    port: int
    endpoint: str
    command: tuple[str, ...]


def _deduplicate(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            resolved = path.expanduser().absolute()
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        result.append(resolved)
    return result


def browser_candidates() -> list[Path]:
    """Return installed Chrome/Edge candidates in preference order."""
    candidates: list[Path] = []

    override = (
        os.environ.get("DUDEDABBLER_OZON_BROWSER_EXECUTABLE", "").strip()
        or os.environ.get("IFOAM_OZON_BROWSER_EXECUTABLE", "").strip()
    )
    if override:
        candidates.append(Path(override))

    for binary in (
        "chrome.exe",
        "chrome",
        "google-chrome",
        "google-chrome-stable",
        "msedge.exe",
        "msedge",
        "microsoft-edge",
    ):
        found = shutil.which(binary)
        if found:
            candidates.append(Path(found))

    local_app_data = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("PROGRAMFILES")
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)")

    roots = [Path(value) for value in (local_app_data, program_files, program_files_x86) if value]
    for root in roots:
        candidates.extend(
            (
                root / "Google" / "Chrome" / "Application" / "chrome.exe",
                root / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            )
        )

    return [path for path in _deduplicate(candidates) if path.is_file()]


def find_browser_executable() -> Path:
    candidates = browser_candidates()
    if candidates:
        return candidates[0]
    raise RuntimeError(
        "Не найден установленный Google Chrome или Microsoft Edge. "
        "Установите один из них либо задайте DUDEDABBLER_OZON_BROWSER_EXECUTABLE."
    )


def reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def build_browser_command(
    executable: Path,
    user_data_dir: Path,
    port: int,
    *,
    start_url: str = SELLER_HOME,
) -> list[str]:
    """Build the normal browser command used by the application.

    Keep this list intentionally small. In particular, do not add Chromium
    sandbox-disabling or automation-identifying flags.
    """
    return [
        str(executable),
        f"--remote-debugging-port={int(port)}",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
        start_url,
    ]


def _wait_for_cdp(
    endpoint: str,
    process: subprocess.Popen[bytes],
    *,
    timeout_seconds: float = 20.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    version_url = f"{endpoint}/json/version"
    last_error = ""
    while time.monotonic() < deadline:
        try:
            request = Request(
                version_url,
                headers={"User-Agent": "DudeDabbler-Ozon-Price-Exporter/0.1.2"},
            )
            with urlopen(request, timeout=0.8) as response:  # noqa: S310 - fixed loopback URL
                payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, dict) and payload.get("webSocketDebuggerUrl"):
                return
        except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)

        return_code = process.poll()
        if return_code not in (None, 0):
            raise RuntimeError(f"Браузер завершился при запуске, код {return_code}.")
        time.sleep(0.2)

    return_code = process.poll()
    hint = (
        " Возможно, окно этого профиля уже открыто — закройте его и повторите запуск."
        if return_code == 0
        else ""
    )
    detail = f" Последняя ошибка: {last_error}" if last_error else ""
    raise RuntimeError(f"Браузер не открыл локальный CDP-порт за {timeout_seconds:.0f} секунд.{hint}{detail}")


def launch_system_browser(user_data_dir: Path) -> LaunchedBrowser:
    executable = find_browser_executable()
    user_data_dir = user_data_dir.expanduser().resolve()
    user_data_dir.mkdir(parents=True, exist_ok=True)
    port = reserve_loopback_port()
    endpoint = f"http://127.0.0.1:{port}"
    command = build_browser_command(executable, user_data_dir, port)

    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        process: subprocess.Popen[bytes] = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            creationflags=creation_flags,
        )
    except OSError as exc:
        raise RuntimeError(f"Не удалось запустить {executable.name}: {exc}") from exc

    try:
        _wait_for_cdp(endpoint, process)
    except Exception:
        terminate_browser_process(process)
        raise

    return LaunchedBrowser(
        executable=executable,
        process=process,
        port=port,
        endpoint=endpoint,
        command=tuple(command),
    )


def terminate_browser_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass

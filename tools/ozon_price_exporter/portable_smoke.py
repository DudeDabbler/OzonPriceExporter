"""Post-build smoke test for the portable executable."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_json(
    url: str,
    *,
    method: str = "GET",
    token: str | None = None,
    payload: dict | None = None,
    timeout: float = 2.0,
) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["X-App-Token"] = token
        headers["Origin"] = url.split("/api/", 1)[0]
    request = Request(url, data=data, method=method, headers=headers)
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed loopback URL
        return json.loads(response.read().decode("utf-8"))


def wait_for_bootstrap(base_url: str, process: subprocess.Popen, timeout: float = 35.0) -> dict:
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Portable EXE завершился при запуске, код {process.returncode}.")
        try:
            return request_json(f"{base_url}/api/bootstrap", timeout=1.0)
        except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            time.sleep(0.25)
    raise RuntimeError(f"Portable EXE не открыл локальный HTTP-порт. Последняя ошибка: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()

    executable = args.executable.resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)

    port = reserve_port()
    base_url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="dudedabbler-ozon-portable-smoke-") as home:
        env = os.environ.copy()
        env["DUDEDABBLER_OZON_PRICE_EXPORTER_HOME"] = home
        process = subprocess.Popen(
            [
                str(executable),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-open",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            shell=False,
        )
        try:
            bootstrap = wait_for_bootstrap(base_url, process)
            if bootstrap.get("version") != args.expected_version:
                raise RuntimeError(
                    f"Версия portable EXE {bootstrap.get('version')!r}, "
                    f"ожидалась {args.expected_version!r}."
                )
            token = str(bootstrap.get("token") or "")
            if not token:
                raise RuntimeError("Bootstrap не вернул локальный токен.")

            for path in ("/", "/static/app.js", "/static/style.css"):
                with urlopen(f"{base_url}{path}", timeout=3.0) as response:  # noqa: S310
                    if response.status != 200 or not response.read(32):
                        raise RuntimeError(f"Статический ресурс не прошёл smoke-test: {path}")

            status = request_json(f"{base_url}/api/status")
            if status.get("status", {}).get("version") != args.expected_version:
                raise RuntimeError("Runtime state содержит неверную версию.")

            request_json(
                f"{base_url}/api/app/shutdown",
                method="POST",
                token=token,
                payload={},
            )
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

    print(f"PORTABLE_SMOKE_PASS version={args.expected_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

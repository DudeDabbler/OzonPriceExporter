from __future__ import annotations

import json
import mimetypes
import secrets
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .browser import BrowserWorker
from .state import RuntimeState
from .storage import ProfileStore


_STATIC_DIR = Path(__file__).resolve().parent / "static"
_MAX_BODY_BYTES = 64 * 1024
_VERSION = "0.1.3"


class LocalApplication:
    def __init__(self, *, host: str = "127.0.0.1", port: int = 0, open_ui: bool = True) -> None:
        self.host = host
        self.port = port
        self.open_ui = open_ui
        self.token = secrets.token_urlsafe(32)
        self.state = RuntimeState()
        self.store = ProfileStore()
        self.worker = BrowserWorker(self.state, self.store)
        self.httpd: ThreadingHTTPServer | None = None

    def serve(self) -> None:
        app = self

        class Handler(BaseHTTPRequestHandler):
            server_version = f"DudeDabblerOzonPriceExporter/{_VERSION}"

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

            def _allowed_origin(self) -> bool:
                origin = self.headers.get("Origin")
                if not origin:
                    return True
                parsed = urlparse(origin)
                return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}

            def _token_ok(self) -> bool:
                return secrets.compare_digest(self.headers.get("X-App-Token", ""), app.token)

            def _send_headers(self, status: int, content_type: str, length: int | None = None) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
                )
                if length is not None:
                    self.send_header("Content-Length", str(length))
                self.end_headers()

            def _json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self._send_headers(status, "application/json; charset=utf-8", len(body))
                self.wfile.write(body)

            def _error(self, message: str, status: int = HTTPStatus.BAD_REQUEST) -> None:
                self._json({"ok": False, "error": message}, status)

            def _read_json(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length") or 0)
                if length < 0 or length > _MAX_BODY_BYTES:
                    raise ValueError("Слишком большой запрос.")
                if length == 0:
                    return {}
                raw = self.rfile.read(length)
                payload = json.loads(raw.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("Ожидался JSON-объект.")
                return payload

            def do_GET(self) -> None:  # noqa: N802
                path = urlparse(self.path).path
                if path == "/api/bootstrap":
                    self._json({"ok": True, "token": app.token, "version": _VERSION})
                    return
                if path == "/api/status":
                    self._json({"ok": True, "status": app.state.snapshot()})
                    return
                if path == "/api/profiles":
                    self._json({"ok": True, "profiles": app.store.list_profiles()})
                    return
                if path == "/api/export":
                    if not self._allowed_origin() or not self._token_ok():
                        self._error("Недействительный локальный токен.", HTTPStatus.FORBIDDEN)
                        return
                    status = app.state.snapshot()
                    export_path = status.get("export_path")
                    if not status.get("export_ready") or not export_path:
                        self._error("Готового Excel пока нет.", HTTPStatus.NOT_FOUND)
                        return
                    file_path = Path(str(export_path)).resolve()
                    try:
                        file_path.relative_to(app.store.exports_dir.resolve())
                    except ValueError:
                        self._error("Недопустимый путь экспорта.", HTTPStatus.FORBIDDEN)
                        return
                    if not file_path.exists() or not file_path.is_file():
                        self._error("Файл экспорта не найден.", HTTPStatus.NOT_FOUND)
                        return
                    payload = file_path.read_bytes()
                    self.send_response(HTTPStatus.OK)
                    self.send_header(
                        "Content-Type",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
                    self.end_headers()
                    self.wfile.write(payload)
                    return
                self._serve_static(path)

            def _serve_static(self, path: str) -> None:
                relative = "index.html" if path in {"", "/"} else path.lstrip("/")
                if not relative.startswith("static/") and relative != "index.html":
                    self._error("Не найдено.", HTTPStatus.NOT_FOUND)
                    return
                if relative.startswith("static/"):
                    relative = relative[len("static/") :]
                file_path = (_STATIC_DIR / relative).resolve()
                try:
                    file_path.relative_to(_STATIC_DIR.resolve())
                except ValueError:
                    self._error("Недопустимый путь.", HTTPStatus.FORBIDDEN)
                    return
                if not file_path.exists() or not file_path.is_file():
                    self._error("Не найдено.", HTTPStatus.NOT_FOUND)
                    return
                payload = file_path.read_bytes()
                content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
                if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
                    content_type += "; charset=utf-8"
                self._send_headers(HTTPStatus.OK, content_type, len(payload))
                self.wfile.write(payload)

            def do_POST(self) -> None:  # noqa: N802
                if not self._allowed_origin() or not self._token_ok():
                    self._error("Недействительный локальный токен.", HTTPStatus.FORBIDDEN)
                    return
                try:
                    payload = self._read_json()
                except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                    self._error(str(exc))
                    return
                path = urlparse(self.path).path
                try:
                    if path == "/api/browser/open":
                        app.worker.open_profile(str(payload.get("profile_name") or ""))
                        self._json({"ok": True, "accepted": True}, HTTPStatus.ACCEPTED)
                    elif path == "/api/session/check":
                        app.worker.check_login()
                        self._json({"ok": True, "accepted": True}, HTTPStatus.ACCEPTED)
                    elif path == "/api/collect/start":
                        app.worker.start_collection()
                        self._json({"ok": True, "accepted": True}, HTTPStatus.ACCEPTED)
                    elif path == "/api/collect/stop":
                        app.worker.request_stop()
                        self._json({"ok": True, "accepted": True}, HTTPStatus.ACCEPTED)
                    elif path == "/api/browser/close":
                        app.worker.close_browser()
                        self._json({"ok": True, "accepted": True}, HTTPStatus.ACCEPTED)
                    elif path == "/api/app/shutdown":
                        self._json({"ok": True})
                        threading.Thread(target=app.stop, daemon=True).start()
                    else:
                        self._error("Неизвестный метод.", HTTPStatus.NOT_FOUND)
                except ValueError as exc:
                    self._error(str(exc))

        self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self.httpd.daemon_threads = True
        actual_port = self.httpd.server_address[1]
        url = f"http://{self.host}:{actual_port}/"
        print(f"Ozon Price Exporter: {url}")
        print("Для остановки нажмите Ctrl+C или кнопку «Закрыть приложение» в интерфейсе.")
        if self.open_ui:
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        try:
            self.httpd.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        self.worker.shutdown()
        if self.httpd is not None:
            try:
                self.httpd.shutdown()
            except Exception:
                pass
            try:
                self.httpd.server_close()
            except Exception:
                pass
            self.httpd = None

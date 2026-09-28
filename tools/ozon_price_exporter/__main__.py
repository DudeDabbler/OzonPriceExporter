from __future__ import annotations

import argparse

from .server import LocalApplication


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Локальное HTML-приложение для выгрузки цен клиента Ozon из авторизованного браузера."
    )
    parser.add_argument("--host", default="127.0.0.1", help="адрес локального сервера")
    parser.add_argument("--port", type=int, default=0, help="порт; 0 = выбрать свободный автоматически")
    parser.add_argument("--no-open", action="store_true", help="не открывать интерфейс автоматически")
    args = parser.parse_args()

    app = LocalApplication(host=args.host, port=args.port, open_ui=not args.no_open)
    app.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Playwright worker that owns one persistent, user-visible Ozon browser."""

from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Any

from .browser_collection import collect_prices
from .browser_helpers import PRICE_MANAGER_URLS, SELLER_HOME, looks_logged_in
from .browser_process import LaunchedBrowser, launch_system_browser, terminate_browser_process
from .state import RuntimeState
from .storage import ProfileStore


class BrowserWorker:
    """Own Playwright and all browser operations on one dedicated thread."""

    def __init__(self, state: RuntimeState, store: ProfileStore) -> None:
        self.state = state
        self.store = store
        self._commands: queue.Queue[tuple[str, dict[str, Any]]] = queue.Queue()
        self._thread = threading.Thread(target=self._run, name="ozon-price-browser", daemon=True)
        self._shutdown = threading.Event()
        self._stop = threading.Event()
        self._context: Any | None = None
        self._browser: Any | None = None
        self._launched_browser: LaunchedBrowser | None = None
        self._page: Any | None = None
        self._playwright: Any | None = None
        self._profile: dict[str, str] | None = None
        self._thread.start()

    def submit(self, action: str, **payload: Any) -> None:
        self._commands.put((action, payload))

    def open_profile(self, profile_name: str) -> None:
        self.submit("open", profile_name=profile_name)

    def check_login(self) -> None:
        self.submit("check_login")

    def start_collection(self) -> None:
        self.submit("collect")

    def request_stop(self) -> None:
        self._stop.set()
        self.state.update(stop_requested=True, message="Запрошена остановка после текущего товара.")
        self.state.log("Пользователь запросил остановку.", level="warning")

    def close_browser(self) -> None:
        self.submit("close")

    def shutdown(self) -> None:
        self._shutdown.set()
        self._stop.set()
        self.submit("shutdown")

    def _run(self) -> None:
        while not self._shutdown.is_set():
            try:
                action, payload = self._commands.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                if action == "open":
                    self._open(payload["profile_name"])
                elif action == "check_login":
                    self._check_login()
                elif action == "collect":
                    self._collect()
                elif action == "close":
                    self._close_context()
                elif action == "shutdown":
                    break
            except Exception as exc:
                self.state.fail(f"Ошибка браузерного контура: {exc}")
        self._close_context()
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass

    def _ensure_playwright(self) -> Any:
        if self._playwright is not None:
            return self._playwright
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright не установлен. Запустите tools\\ozon_price_exporter\\install.bat."
            ) from exc
        self._playwright = sync_playwright().start()
        return self._playwright

    def _launch_context(self, browser_dir: Path) -> Any:
        """Launch ordinary installed Chrome/Edge, then attach over loopback CDP."""
        playwright = self._ensure_playwright()
        launched = launch_system_browser(browser_dir)
        browser: Any | None = None
        try:
            browser = playwright.chromium.connect_over_cdp(launched.endpoint)
            if not browser.contexts:
                raise RuntimeError("Обычный браузер открыт, но CDP-контекст не найден.")
            self._browser = browser
            self._launched_browser = launched
            self.state.log(
                f"Запущен обычный {launched.executable.name} через локальный CDP-порт {launched.port}; "
                "небезопасный флаг --no-sandbox не используется."
            )
            return browser.contexts[0]
        except Exception:
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass
            terminate_browser_process(launched.process)
            raise

    def _open(self, profile_name: str) -> None:
        if self.state.snapshot().get("running"):
            raise RuntimeError("Сначала остановите текущий сбор.")
        profile = self.store.ensure_profile(profile_name)
        if self._context is not None and self._profile and self._profile["slug"] == profile["slug"]:
            self.state.update(phase="waiting_login", message="Браузер уже открыт.")
            try:
                self._page.bring_to_front()
            except Exception:
                pass
            return

        self._close_context()
        self.state.begin_operation("opening_browser", "Открываю отдельный обычный браузерный профиль…")
        self.state.log(f"Открывается профиль «{profile['name']}».")
        self._context = self._launch_context(Path(profile["browser_dir"]))
        self._profile = profile
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self._page.set_default_timeout(30_000)
        try:
            self._page.goto(SELLER_HOME, wait_until="domcontentloaded", timeout=60_000)
        except Exception:
            pass
        self.state.update(
            phase="waiting_login",
            message="Войдите в Ozon в открытом окне, затем нажмите «Проверить вход».",
            profile_name=profile["name"],
            profile_slug=profile["slug"],
            browser_open=True,
            logged_in=looks_logged_in(self._page),
            running=False,
            stop_requested=False,
            export_ready=False,
            export_filename=None,
            export_path=None,
        )

    def _check_login(self) -> None:
        if self._page is None:
            raise RuntimeError("Сначала откройте браузер.")
        self.state.begin_operation("checking_login", "Проверяю авторизацию в кабинете Ozon…")
        try:
            self._page.goto(PRICE_MANAGER_URLS[0], wait_until="domcontentloaded", timeout=60_000)
            self._page.wait_for_timeout(1_500)
        except Exception:
            pass
        logged_in = looks_logged_in(self._page)
        if logged_in:
            self.state.update(
                phase="ready",
                message="Вход подтверждён. Можно начинать сбор.",
                logged_in=True,
                browser_open=True,
            )
            self.state.log("Авторизация в Ozon подтверждена.")
        else:
            self.state.update(
                phase="waiting_login",
                message="Вход пока не подтверждён. Завершите авторизацию в окне Ozon.",
                logged_in=False,
                browser_open=True,
            )
            self.state.log("Авторизация пока не подтверждена.", level="warning")

    def _collect(self) -> None:
        if self._page is None or self._context is None or self._profile is None:
            raise RuntimeError("Сначала откройте браузер и войдите в Ozon.")
        if not looks_logged_in(self._page):
            self._check_login()
        if not self.state.snapshot().get("logged_in"):
            raise RuntimeError("Авторизация в кабинете Ozon не подтверждена.")
        collect_prices(
            context=self._context,
            page=self._page,
            profile=self._profile,
            state=self.state,
            stop_event=self._stop,
        )

    def _close_context(self) -> None:
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
        elif self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
        if self._launched_browser is not None:
            terminate_browser_process(self._launched_browser.process)
        self._context = None
        self._browser = None
        self._launched_browser = None
        self._page = None
        self._profile = None
        self.state.update(
            phase="idle",
            message="Браузер закрыт.",
            browser_open=False,
            logged_in=False,
            running=False,
        )

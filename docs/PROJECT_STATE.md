# OzonPriceExporter — Project State

**Статус:** CURRENT  
**Обновлено:** 2026-09-28  
**Канонический репозиторий:** `DudeDabbler/OzonPriceExporter`

## Текущее опубликованное состояние

- версия: `0.1.2`;
- каноническая ветка: `main`;
- exact release source SHA: `cbcd90a8375a01420a341e963db6d2b8ded6d03b`;
- GitHub Release: `v0.1.2`;
- portable ZIP: `OzonPriceExporter-0.1.2-win-x64.zip`;
- ZIP size: `51 593 011` bytes;
- ZIP SHA-256: `98d861a050298bd02179d9558a867f44e0ad79095ed4880d2823c72783e2d37c`;
- release workflow run: `36399490982`;
- marketplace writes: `0`.

## Функциональный контракт

- приложение работает только на чтение;
- основной сценарий не требует Premium Pro, API-ключей или импорта SKU;
- пользователь входит в любой кабинет Ozon в обычном Chrome/Edge;
- ассортимент обнаруживается автоматически из DOM и JSON/XHR кабинета;
- результат публикуется в XLSX;
- Windows portable-дистрибутив поставляется как one-folder ZIP;
- пользовательский заголовок: `DudeDabbler · локальный инструмент`;
- совместимый путь существующих профилей: `%LOCALAPPDATA%\IFOAM\OzonPriceExporter`;
- новая переменная хранилища: `DUDEDABBLER_OZON_PRICE_EXPORTER_HOME`;
- `IFOAM_OZON_PRICE_EXPORTER_HOME` остаётся fallback для обратной совместимости.

## Верификация релиза `v0.1.2`

GitHub Actions на exact release source SHA подтвердил:

```text
focused regression suite: 16 passed
Python compile: PASS
PyInstaller one-folder build: PASS
packaged EXE bootstrap/static/version/shutdown smoke: PASS
workflow artifact upload: PASS
GitHub Release publication: PASS
```

Сборка выполнена на Windows Server 2025, Python `3.12.10` x64, Playwright `1.63.0`, openpyxl `3.1.5`, PyInstaller `6.22.3`.

Авторизованный live-сценарий Ozon был подтверждён на предшествующей `0.1.1`. В `0.1.2` marketplace/browser collection contract не менялся; изменения относятся к самостоятельному репозиторию, брендингу, совместимости путей и воспроизводимой GitHub-сборке. Повторный вход в пользовательский кабинет не выполнялся и не требовался для переноса исходников и публикации чистого release ZIP.

## Завершённая миграция

Источник:

- repository: `DudeDabbler/analytics-v2`;
- branch: `feat/ozon-customer-price-exporter-v1-20260925`;
- exact source SHA: `a368768bcd565e0ab4488545d665e5729f9f3e46`;
- source PR: `analytics-v2#25`.

Результат:

- standalone migration PR `OzonPriceExporter#2` — merged;
- release/hardening PRs `#3`, `#4`, `#5`, `#6` — merged;
- old `analytics-v2#25` — `SUPERSEDED/HISTORICAL`, closed without merge;
- `DudeDabbler/OzonPriceExporter/main` — единственный CURRENT-источник кода, документации, issues, builds и releases.

## Контракты, которые нельзя ослаблять

- marketplace writes: `0`;
- отсутствие `--no-sandbox` и `--enable-automation`;
- loopback-only HTTP/CDP;
- отдельный browser profile для каждого магазина;
- fail-visible строки `PARTIAL`/`ERROR`;
- секреты, cookies и выгрузки не входят в Git или release ZIP;
- portable build должен завершать tests, EXE smoke, ZIP и SHA-256 до публикации.

## Итоговый gate

```text
STANDALONE_MIGRATION_COMPLETE
PORTABLE_RELEASE_V0_1_2_PUBLISHED
OLD_CONTOUR_SUPERSEDED
```

Незакрытых blocker по задаче переноса приложения в отдельный GitHub-репозиторий нет.

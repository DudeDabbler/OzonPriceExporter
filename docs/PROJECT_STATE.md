# OzonPriceExporter — Project State

**Статус:** CURRENT  
**Обновлено:** 2026-09-28  
**Канонический репозиторий:** `DudeDabbler/OzonPriceExporter`

## Текущее состояние

- приложение работает только на чтение;
- основной сценарий не требует Premium Pro, API-ключей или импорта SKU;
- пользователь входит в любой кабинет Ozon в обычном Chrome/Edge;
- ассортимент обнаруживается автоматически из DOM и JSON/XHR кабинета;
- результат публикуется в XLSX;
- Windows portable-дистрибутив собирается как one-folder ZIP;
- пользовательский заголовок: `DudeDabbler · локальный инструмент`;
- совместимый путь профилей: `%LOCALAPPDATA%\IFOAM\OzonPriceExporter`.

## Подтверждённая база миграции

- источник: `DudeDabbler/analytics-v2`;
- source branch: `feat/ozon-customer-price-exporter-v1-20260925`;
- exact source SHA: `a368768bcd565e0ab4488545d665e5729f9f3e46`;
- source PR: `analytics-v2#25`;
- migration issue: `OzonPriceExporter#1`.

## Acceptance

Исходный runtime и portable EXE ранее прошли live end-to-end проверку на реальном авторизованном кабинете Ozon. После standalone-миграции обязательны:

1. focused regression suite;
2. GitHub read-back полного дерева;
3. portable build из exact standalone SHA;
4. packaged EXE smoke-test;
5. release ZIP и SHA-256;
6. маркировка старого контура как `SUPERSEDED/HISTORICAL`.

## Контракты, которые нельзя ослаблять

- marketplace writes: `0`;
- отсутствие `--no-sandbox` и `--enable-automation`;
- loopback-only HTTP/CDP;
- отдельный browser profile для каждого магазина;
- fail-visible строки `PARTIAL`/`ERROR`;
- секреты, cookies и выгрузки не входят в Git или release ZIP.

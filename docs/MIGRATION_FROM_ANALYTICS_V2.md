# Migration from analytics-v2

**Статус:** COMPLETE  
**Дата:** 2026-09-28

## Источник

Приложение выделено из:

```text
repository: DudeDabbler/analytics-v2
branch: feat/ozon-customer-price-exporter-v1-20260925
exact SHA: a368768bcd565e0ab4488545d665e5729f9f3e46
source PR: #25
```

Exact набор исходных путей зафиксирован в issue `DudeDabbler/OzonPriceExporter#1`.

## Граница миграции

Перенесены только:

- runtime `tools/ozon_price_exporter`;
- два focused test-модуля;
- Windows launch/build scripts;
- архитектурная документация;
- standalone CI/release workflow.

Не переносились бизнес-данные, `.env`, API-ключи, browser profiles, cookies, Excel/CSV/Parquet и прочие контуры `analytics-v2`.

## Результат

```text
standalone migration PR: OzonPriceExporter#2 — merged
release/hardening PRs: #3, #4, #5, #6 — merged
release source SHA: cbcd90a8375a01420a341e963db6d2b8ded6d03b
release: v0.1.2
portable ZIP SHA-256: 98d861a050298bd02179d9558a867f44e0ad79095ed4880d2823c72783e2d37c
old source PR: analytics-v2#25 — SUPERSEDED/HISTORICAL, closed without merge
```

Перенос исходников, CI, portable build и публикация релиза выполнены через GitHub. Локальные данные, пользовательский компьютер, browser profiles и cookies для миграции не использовались.

## Каноничность

После завершения миграции:

- `DudeDabbler/OzonPriceExporter/main` — единственный CURRENT источник кода и документации;
- `DudeDabbler/OzonPriceExporter/releases/tag/v0.1.2` — опубликованный portable release;
- реализация в `analytics-v2` — SUPERSEDED/HISTORICAL;
- новые изменения запрещено вести параллельно в двух репозиториях.

## Совместимость

Путь `%LOCALAPPDATA%\IFOAM\OzonPriceExporter` и переменная `IFOAM_OZON_PRICE_EXPORTER_HOME` сохраняются как совместимые, чтобы не потерять существующие авторизованные профили. Новая переменная `DUDEDABBLER_OZON_PRICE_EXPORTER_HOME` имеет приоритет.

## Проверка

```text
focused tests: 16 passed
PyInstaller build: PASS
packaged EXE loopback smoke: PASS
ZIP + SHA-256 publication: PASS
marketplace writes: 0
```

Миграция закрыта без незавершённых blocker.

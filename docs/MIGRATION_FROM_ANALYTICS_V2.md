# Migration from analytics-v2

**Статус:** CURRENT  
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

Переносятся только:

- runtime `tools/ozon_price_exporter`;
- два focused test-модуля;
- Windows launch/build scripts;
- архитектурная документация;
- standalone CI/release workflow.

Не переносятся бизнес-данные, `.env`, API-ключи, browser profiles, cookies, Excel/CSV/Parquet и прочие контуры `analytics-v2`.

## Каноничность

После merge миграционного PR:

- `DudeDabbler/OzonPriceExporter/main` — CURRENT источник кода и документации;
- реализация в `analytics-v2` — SUPERSEDED/HISTORICAL;
- новые изменения запрещено вести параллельно в двух репозиториях.

## Совместимость

Путь `%LOCALAPPDATA%\IFOAM\OzonPriceExporter` и переменная `IFOAM_OZON_PRICE_EXPORTER_HOME` сохраняются как совместимые, чтобы не потерять существующие авторизованные профили. Новая переменная `DUDEDABBLER_OZON_PRICE_EXPORTER_HOME` имеет приоритет.

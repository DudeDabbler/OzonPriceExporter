# OzonPriceExporter

**Статус:** CURRENT  
**Версия:** 0.1.2  
**Режим:** локальное read-only приложение для Windows x64

OzonPriceExporter получает цены из авторизованного кабинета продавца Ozon без Premium Pro:

```text
запуск приложения
→ обычный Chrome или Edge
→ ручной вход пользователя в любой магазин
→ автоматическое обнаружение ассортимента
→ read-only сбор цен
→ Excel
```

Приложение не требует предварительного каталога SKU и не изменяет цены, акции или карточки.

## Portable-запуск

1. Скачайте ZIP из GitHub Releases.
2. Полностью распакуйте архив.
3. Запустите `OzonPriceExporter.exe`.

Python, pip, venv, установщик и административные права конечному пользователю не требуются. На компьютере должен быть установлен Google Chrome или Microsoft Edge.

Профили магазинов и Excel по умолчанию хранятся вне portable-папки:

```text
%LOCALAPPDATA%\IFOAM\OzonPriceExporter\
```

Старый путь сохранён для совместимости с уже созданными профилями и авторизацией. Новая переменная `DUDEDABBLER_OZON_PRICE_EXPORTER_HOME` может переопределить место хранения; прежняя `IFOAM_OZON_PRICE_EXPORTER_HOME` остаётся совместимым fallback.

## Запуск из исходников

```powershell
.\tools\ozon_price_exporter\install.bat
.\run_ozon_price_exporter.bat
```

## Сборка portable

```powershell
.\build_ozon_price_exporter_portable.bat
```

Сборка создаёт:

```text
dist\OzonPriceExporter-<version>-win-x64.zip
dist\OzonPriceExporter-<version>-win-x64.zip.sha256
```

## Проверка

```powershell
python -m pytest -q tests\test_ozon_price_exporter.py tests\test_ozon_price_exporter_portable.py
```

## Документация

- [`docs/ADR_ozon_customer_price_exporter_2026-09-25.md`](docs/ADR_ozon_customer_price_exporter_2026-09-25.md) — архитектура и подтверждённые решения;
- [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) — текущее состояние проекта;
- [`docs/MIGRATION_FROM_ANALYTICS_V2.md`](docs/MIGRATION_FROM_ANALYTICS_V2.md) — происхождение и граница миграции.

## Происхождение

Канонический код перенесён из `DudeDabbler/analytics-v2`, ветка `feat/ozon-customer-price-exporter-v1-20260925`, exact source SHA `a368768bcd565e0ab4488545d665e5729f9f3e46`.

После завершения миграции этот репозиторий является единственным CURRENT-источником приложения.

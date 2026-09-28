# OzonPriceExporter

**Статус:** CURRENT  
**Версия:** `0.1.3`  
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

## Актуальный portable-релиз

- release: [`v0.1.3`](https://github.com/DudeDabbler/OzonPriceExporter/releases/tag/v0.1.3);
- exact release source SHA: `a66fd5b7a5ffdbd1fdd79b74110c5a8f1d05777a`;
- файл: `OzonPriceExporter-0.1.3-win-x64.zip`;
- размер: `51 595 412` байт;
- SHA-256: `98e6049df5b935e77ef643570fbe4a26fa077d365843e50b0f5479b85e94dfc7`;
- tests, compile, PyInstaller build и packaged EXE smoke: `PASS`;
- marketplace writes: `0`.

## Portable-запуск

1. Скачайте ZIP из GitHub Release `v0.1.3`.
2. Полностью распакуйте архив.
3. Запустите `OzonPriceExporter.exe`.

Python, pip, venv, установщик и административные права конечному пользователю не требуются. На компьютере должен быть установлен Google Chrome или Microsoft Edge.

Профили магазинов и Excel по умолчанию хранятся вне portable-папки:

```text
%LOCALAPPDATA%\IFOAM\OzonPriceExporter\
```

Старый путь сохранён для совместимости с уже созданными профилями и авторизацией. Новая переменная `DUDEDABBLER_OZON_PRICE_EXPORTER_HOME` может переопределить место хранения; прежняя `IFOAM_OZON_PRICE_EXPORTER_HOME` остаётся совместимым fallback.

## Коммерческая версия

Коммерческая редакция добавляет полный обход всех страниц каталога Ozon, сохранённые фильтры для каждого магазина, выбор категорий из фактического ассортимента и расширенный аудит Excel.

```text
12 900 ₽ — бессрочная лицензия
```

Доступны варианты с желаемыми доработками, интеграциями и дополнительными функциями. Стоимость обсуждается отдельно.

## Разработчик и другие мини-приложения

**Елсуков Сергей** разрабатывает и другие локальные мини-приложения для работы с личными кабинетами Ozon и Wildberries: сбор данных, отчёты, контроль цен и автоматизацию повторяющихся операций.

- E-mail: `ratatos692@gmail.com`;
- Telegram: `@seryozha_human`;
- телефон: `+7 (961) 668-19-41`;
- обычный срок ответа: в течение 24 часов.

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

Канонический release workflow выполняет focused tests, compile, PyInstaller build, packaged EXE loopback smoke, ZIP/SHA-256 и публикацию GitHub Release из exact `main` SHA.

## Проверка

```powershell
python -m pytest -q tests\test_ozon_price_exporter.py tests\test_ozon_price_exporter_portable.py
```

## Документация

- [`docs/ADR_ozon_customer_price_exporter_2026-09-25.md`](docs/ADR_ozon_customer_price_exporter_2026-09-25.md) — архитектура и подтверждённые решения;
- [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) — текущее состояние проекта;
- [`docs/MIGRATION_FROM_ANALYTICS_V2.md`](docs/MIGRATION_FROM_ANALYTICS_V2.md) — завершённая миграция и границы исторического источника.

## Происхождение и каноничность

Код перенесён из `DudeDabbler/analytics-v2`, ветка `feat/ozon-customer-price-exporter-v1-20260925`, exact source SHA `a368768bcd565e0ab4488545d665e5729f9f3e46`.

`DudeDabbler/OzonPriceExporter` является единственным CURRENT-источником бесплатной версии. Исторический PR `analytics-v2#25` помечен `SUPERSEDED/HISTORICAL` и закрыт без merge.

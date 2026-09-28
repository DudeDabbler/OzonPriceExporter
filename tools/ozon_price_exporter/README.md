# Ozon Customer Price Exporter

**Статус:** CURRENT, версия `0.1.2`  
**Режим:** локальное HTML-приложение, только чтение  
**Канонический репозиторий:** `DudeDabbler/OzonPriceExporter`  
**Каноническое решение:** [`../../docs/ADR_ozon_customer_price_exporter_2026-09-25.md`](../../docs/ADR_ozon_customer_price_exporter_2026-09-25.md)

## Назначение

Приложение позволяет пользователю без Premium Pro:

1. запустить локальный HTML-интерфейс;
2. открыть отдельный обычный браузер;
3. самостоятельно войти в любой кабинет Ozon;
4. автоматически получить ассортимент авторизованного магазина;
5. собрать цены клиента и связанные ценовые поля;
6. скачать результат в формате Excel.

Предварительная регистрация магазина, импорт SKU и API-ключи для основного сценария не требуются.

## Portable Windows x64

```text
GitHub Release ZIP
→ полностью распаковать
→ OzonPriceExporter.exe
```

Python, pip, venv и административные права конечному пользователю не нужны. Требуется установленный Google Chrome или Microsoft Edge.

## Запуск из исходников

```text
tools\ozon_price_exporter\install.bat
run_ozon_price_exporter.bat
```

## Сборка portable

```text
build_ozon_price_exporter_portable.bat
```

Сборка допускается только из чистого exact Git HEAD, совпадающего с upstream. В ZIP включается `BUILD_MANIFEST.json` с repository, commit и версиями зависимостей.

## Пользовательский сценарий

1. Введите название профиля магазина.
2. Нажмите **«Открыть Ozon»**.
3. Войдите в кабинет Ozon обычным способом.
4. Нажмите **«Проверить вход»**.
5. Нажмите **«Собрать цены»**.
6. После завершения нажмите **«Скачать Excel»**.

## Хранение данных

Для совместимости с ранее созданными профилями по умолчанию используется:

```text
%LOCALAPPDATA%\IFOAM\OzonPriceExporter
```

Новая переменная `DUDEDABBLER_OZON_PRICE_EXPORTER_HOME` имеет приоритет. Старый alias `IFOAM_OZON_PRICE_EXPORTER_HOME` остаётся fallback.

## Безопасность

- marketplace writes: `0`;
- HTTP и CDP слушают только `127.0.0.1`;
- команда Chrome/Edge не содержит `--no-sandbox` и `--enable-automation`;
- логин и пароль вводятся только на странице Ozon;
- cookies, `.env`, API-ключи и пользовательские выгрузки не входят в Git или portable ZIP;
- ошибки отдельных товаров остаются видимыми как `PARTIAL`/`ERROR`.

## Проверка

```bash
python -m pytest -q tests/test_ozon_price_exporter.py tests/test_ozon_price_exporter_portable.py
```

Полная проверка с действующим кабинетом выполняется локально, поскольку CI не содержит пользовательскую Ozon-сессию.

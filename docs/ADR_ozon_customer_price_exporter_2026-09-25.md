# ADR — Ozon Customer Price Exporter через авторизованный браузер

**Статус:** CURRENT  
**Дата решения:** 2026-09-25  
**Актуализировано:** 2026-09-28  
**Канонический репозиторий:** `DudeDabbler/OzonPriceExporter`  
**Область:** Ozon / browser collection / Excel / portable Windows distribution

## Контекст

У продавца нет Premium Pro, поэтому официальный метод `/v1/product/prices/details` с полной клиентской ценой недоступен. При этом цена клиента видна в авторизованном кабинете Ozon и используется самим интерфейсом кабинета.

Исторически в `DudeDabbler/analytics-wb-continent` уже был подтверждён read-only подход чтения `__MODULE_STATE__.prices`, DOM и ответа `get-common-prices`, но старый collector зависел от заранее подготовленного внутреннего каталога `offer_id + product_id`.

Пользовательский контракт нового приложения строже:

```text
запуск
→ обычный браузер
→ пользователь входит в любой, включая новый, магазин
→ приложение само получает ассортимент
→ собирает цены без записи в Ozon
→ формирует Excel
```

После успешного live acceptance приложение выделено из `DudeDabbler/analytics-v2` в отдельный репозиторий.

## Решение

Создать самостоятельное локальное HTML-приложение с таким потоком:

```text
loopback HTML UI
→ отдельный persistent browser profile магазина
→ системный Chrome/Edge
→ ручная авторизация пользователя
→ Playwright connect_over_cdp
→ автообнаружение ассортимента из DOM и JSON/XHR
→ read-only обход страниц цен
→ нормализация источников цены
→ XLSX
```

## Обязательные инварианты

1. **Новый магазин без предварительной регистрации.** Профиль создаётся по введённому названию.
2. **Импорт SKU не является обязательным сценарием.** Изменение интерфейса Ozon должно давать явную диагностическую ошибку.
3. **Marketplace writes = 0.** Код не меняет цены, акции, карточки или остатки.
4. **Учётные данные не перехватываются.** Логин, пароль и второй фактор вводятся только на странице Ozon.
5. **Изоляция магазинов.** Каждый магазин использует отдельный `user_data_dir`.
6. **Прозрачная семантика цены.** В Excel сохраняются значение и конкретный `customer_price_source`; цена с Ozon Картой хранится отдельно.
7. **Loopback only.** HTTP и CDP слушают только `127.0.0.1` на свободных локальных портах.
8. **Fail-visible.** Ошибка одного товара не останавливает весь сбор и отражается как `PARTIAL` или `ERROR`.
9. **Обычный sandboxed browser.** Запрещены `--no-sandbox` и `--enable-automation`.
10. **Секреты и cookies не входят в Git и release ZIP.**
11. **Portable без установки runtime.** Конечному пользователю не нужны Python, pip, venv и административные права.
12. **Build привязан к exact Git SHA.** В portable кладётся `BUILD_MANIFEST.json`.

## Почему системный Chrome/Edge, а не Playwright launch

Первоначальный запуск через `playwright.chromium.launch_persistent_context` добавлял Chromium-флаг `--no-sandbox`. Ozon отвечал синтетической страницей «Похоже, нет соединения», хотя интернет и VPN были исправны.

Принято:

```text
найти установленный Chrome/Edge
→ запустить напрямую с отдельным user-data-dir
→ открыть loopback remote-debugging-port
→ подключить Playwright через CDP
```

Это сохраняет обычный sandbox, сетевые настройки пользователя и отдельную авторизованную сессию.

## Источники данных

### Ассортимент

Основной фактический контракт кабинета:

```text
POST https://seller.ozon.ru/api/v1/products/list-by-filter
```

Поддерживается актуальная вложенная структура:

- `part_item`;
- `part_status`;
- `part_category`;
- `part_price`;
- `part_marketing_price`;
- `part_price_indexes_full`;
- `part_stocks`.

### Цена клиента

Приоритет источников:

```text
get-common-prices.marketing_oa_price
→ get-common-prices.marketing_price
→ __MODULE_STATE__.price.marketingPrice
→ DOM FBO/FBS
```

Цена с Ozon Картой не подменяет молча общую цену клиента и хранится отдельной колонкой.

## Выходной контракт

Excel содержит:

- `Цены` — одна строка на товар;
- `Сводка` — профиль, версия, время и результат запуска;
- `Ошибки` — неполные и неуспешные строки.

Обязательные идентификаторы: `offer_id`, `product_id`, `sku`. Обязательные поля аудита: время сбора, профиль, `customer_price_source`, статус строки и ссылка на страницу цен.

## Хранение профилей

Исторический путь сохраняется для обратной совместимости:

```text
%LOCALAPPDATA%\IFOAM\OzonPriceExporter
```

Новая переменная имеет приоритет:

```text
DUDEDABBLER_OZON_PRICE_EXPORTER_HOME
```

Прежняя `IFOAM_OZON_PRICE_EXPORTER_HOME` остаётся fallback. Изменение дефолтного каталога без миграции запрещено, потому что привело бы к потере сохранённой авторизации пользователей.

## Portable-дистрибутив

Принят формат one-folder ZIP:

```text
OzonPriceExporter-<version>-win-x64.zip
└── OzonPriceExporter\
    ├── OzonPriceExporter.exe
    ├── _internal\
    ├── README.txt
    └── BUILD_MANIFEST.json
```

One-folder выбран вместо one-file, потому что:

- runtime не распаковывается заново при каждом запуске;
- состав проще проверять и диагностировать;
- Playwright driver и Node runtime видимы в `_internal`;
- обновление программы не смешивается с browser profiles.

## Верификация

Автоматически проверяются:

- старый и актуальный JSON-контракт Ozon;
- преобразование `{units, nanos}`;
- приоритет источников цены клиента;
- изоляция профилей и path safety;
- Excel-листы и защита от formula injection;
- отсутствие небезопасных Chrome-флагов;
- DudeDabbler branding;
- единая версия runtime;
- наличие build/docs/workflow контрактов;
- smoke-test уже собранного EXE.

Live acceptance требует Windows-компьютер с авторизованным кабинетом и выполняется только после публикации exact standalone SHA.

## История и миграция

Исторический источник:

```text
repository: DudeDabbler/analytics-v2
branch: feat/ozon-customer-price-exporter-v1-20260925
exact SHA: a368768bcd565e0ab4488545d665e5729f9f3e46
source PR: #25
```

Исходная версия и portable EXE прошли live end-to-end проверку:

```text
обычный Chrome
→ авторизация
→ автообнаружение
→ read-only сбор
→ Excel
```

После merge миграционного PR единственным CURRENT-источником становится `DudeDabbler/OzonPriceExporter/main`. Старый контур должен быть помечен `SUPERSEDED/HISTORICAL`, чтобы изменения не велись параллельно в двух репозиториях.

## Влияние

- production pricing и marketplace write routes не затрагиваются;
- Chrome/Edge остаётся обязательной внешней предпосылкой;
- unsigned EXE может вызвать SmartScreen;
- совместимость зависит от текущего DOM/XHR Ozon и требует проверки после значимого изменения кабинета.

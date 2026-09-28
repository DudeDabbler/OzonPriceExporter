# OzonPriceExporter — Project State

**Статус:** CURRENT / `0.1.3` PUBLISHED  
**Обновлено:** 2026-09-28  
**Канонический репозиторий:** `DudeDabbler/OzonPriceExporter`

## Текущее опубликованное состояние

- версия: `0.1.3`;
- exact release source SHA: `a66fd5b7a5ffdbd1fdd79b74110c5a8f1d05777a`;
- GitHub Release: `v0.1.3`;
- portable ZIP: `OzonPriceExporter-0.1.3-win-x64.zip`;
- ZIP size: `51 595 412` bytes;
- ZIP SHA-256: `98e6049df5b935e77ef643570fbe4a26fa077d365843e50b0f5479b85e94dfc7`;
- release workflow run: `36422989434`;
- marketplace writes: `0`.

## Изменения `0.1.3`

Добавлены пользовательские блоки, построенные по композиции последних страниц презентации Price Tracker:

- цена `12 900 ₽`;
- формулировка `бессрочная лицензия`;
- указание, что желаемые доработки, интеграции и отдельные функции оцениваются отдельно;
- информация о разработчике Елсукове Сергее;
- E-mail, Telegram и телефон как кликабельные контактные карточки;
- упоминание других мини-приложений для работы с ЛК Ozon/Wildberries;
- responsive price/contact layout;
- regression-контракт текста, контактов и ссылок.

Browser collection, parser, Excel-контракт, storage и marketplace safety не менялись.

## Коммерческое предложение

```text
12 900 ₽ — бессрочная лицензия
```

Коммерческая редакция включает полный обход всех страниц каталога, сохранённые фильтры, удобный выбор категорий и расширенный аудит Excel.

Доступны варианты с желаемыми доработками, интеграциями и дополнительными функциями. Цена обсуждается отдельно.

## Разработчик и контакты

```text
Елсуков Сергей
E-mail: ratatos692@gmail.com
Telegram: @seryozha_human
Телефон: +7 (961) 668-19-41
```

Разрабатываются и другие локальные мини-приложения для работы с личными кабинетами Ozon и Wildberries: сбор данных, отчёты, контроль цен и автоматизация повторяющихся операций.

## Функциональный контракт

- приложение работает только на чтение;
- основной сценарий не требует Premium Pro, API-ключей или импорта SKU;
- пользователь входит в любой кабинет Ozon в обычном Chrome/Edge;
- ассортимент обнаруживается автоматически из DOM и JSON/XHR кабинета;
- результат публикуется в XLSX;
- Windows portable-дистрибутив поставляется как one-folder ZIP;
- совместимый путь существующих профилей: `%LOCALAPPDATA%\IFOAM\OzonPriceExporter`;
- новая переменная хранилища: `DUDEDABBLER_OZON_PRICE_EXPORTER_HOME`;
- `IFOAM_OZON_PRICE_EXPORTER_HOME` остаётся fallback для обратной совместимости.

## Верификация `v0.1.3`

```text
focused tests: PASS
Python compile: PASS
PyInstaller one-folder build: PASS
packaged EXE bootstrap/static/version/shutdown smoke: PASS
workflow artifact upload: PASS
GitHub Release publication: PASS
marketplace writes: 0
```

## Контракты, которые нельзя ослаблять

- marketplace writes: `0`;
- отсутствие `--no-sandbox` и `--enable-automation`;
- loopback-only HTTP/CDP;
- отдельный browser profile для каждого магазина;
- fail-visible строки `PARTIAL`/`ERROR`;
- секреты, cookies и выгрузки не входят в Git или release ZIP;
- portable build должен завершать tests, EXE smoke, ZIP и SHA-256 до публикации.

## Текущий gate

```text
COMMERCIAL_CONTACT_PANEL_PUBLISHED
CONTACTS_DOCUMENTED
PORTABLE_RELEASE_V0_1_3_PUBLISHED
MARKETPLACE_WRITES_0
```

Незакрытых blocker по patch-релизу `0.1.3` нет.

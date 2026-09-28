# OzonPriceExporter — Project State

**Статус:** CURRENT / PATCH `0.1.3` PREPARED  
**Обновлено:** 2026-09-28  
**Канонический репозиторий:** `DudeDabbler/OzonPriceExporter`  
**Текущий change:** issue `#8`, branch `feat/commercial-contact-panel-20260928`

## Текущее опубликованное состояние

Последний опубликованный стабильный релиз до merge и сборки patch:

- версия: `0.1.2`;
- exact release source SHA: `cbcd90a8375a01420a341e963db6d2b8ded6d03b`;
- GitHub Release: `v0.1.2`;
- portable ZIP: `OzonPriceExporter-0.1.2-win-x64.zip`;
- ZIP size: `51 593 011` bytes;
- ZIP SHA-256: `98d861a050298bd02179d9558a867f44e0ad79095ed4880d2823c72783e2d37c`;
- marketplace writes: `0`.

## Patch `0.1.3`

Реализовано в исходниках:

- пользовательский блок коммерческой версии;
- цена `12 900 ₽`;
- формулировка `бессрочная лицензия`;
- отдельное указание, что желаемые доработки и интеграции оцениваются отдельно;
- информация о разработчике Елсукове Сергее;
- контакты: e-mail, Telegram и телефон;
- упоминание других мини-приложений для работы с ЛК Ozon/Wildberries;
- responsive price/contact layout по композиции последних страниц презентации Price Tracker;
- regression-контракт пользовательских формулировок и ссылок.

Patch не меняет browser collection, парсинг, Excel-контракт, storage или marketplace safety.

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

Предлагаются и другие локальные мини-приложения для работы с личными кабинетами Ozon и Wildberries: сбор данных, отчёты, контроль цен и автоматизация повторяющихся операций.

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

## Верификация `v0.1.2`

```text
focused regression suite: 16 passed
Python compile: PASS
PyInstaller one-folder build: PASS
packaged EXE bootstrap/static/version/shutdown smoke: PASS
GitHub Release publication: PASS
```

## Verification gate `0.1.3`

До публикации требуется:

```text
focused tests PASS
compileall PASS
GitHub tree read-back
PyInstaller one-folder build PASS
packaged EXE smoke PASS
ZIP + SHA-256 PASS
GitHub Release v0.1.3 publication
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
COMMERCIAL_CONTACT_PANEL_IMPLEMENTED
CONTACTS_DOCUMENTED
PATCH_0_1_3_SOURCE_READY
TEST_AND_RELEASE_PENDING
MARKETPLACE_WRITES_0
```

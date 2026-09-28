"""Read-only detail collection and Excel publication for discovered Ozon products."""

from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from threading import Event
from typing import Any

from .browser_discovery import attach_response_capture, discover_products
from .browser_helpers import DETAIL_URL, looks_logged_in, now_iso
from .exporter import write_workbook
from .parser import choose_customer_price, extract_common_price_fields, parse_html
from .state import RuntimeState


def collect_prices(
    *,
    context: Any,
    page: Any,
    profile: dict[str, str],
    state: RuntimeState,
    stop_event: Event,
) -> None:
    if not looks_logged_in(page):
        raise RuntimeError("Авторизация в кабинете Ozon не подтверждена.")

    stop_event.clear()
    started_at = now_iso()
    state.update(
        phase="discovering",
        message="Автоматически получаю ассортимент магазина…",
        running=True,
        stop_requested=False,
        discovered=0,
        total_hint=None,
        processed=0,
        ok=0,
        failed=0,
        export_ready=False,
        export_filename=None,
        export_path=None,
        started_at=started_at,
        completed_at=None,
        last_error=None,
    )
    state.log("Начат read-only сбор цен Ozon.")

    products, common_cache, total_hint = discover_products(page, state, stop_event)
    if stop_event.is_set() and not products:
        state.update(phase="stopped", message="Сбор остановлен до обнаружения товаров.", running=False)
        return
    if not products:
        raise RuntimeError(
            "Не удалось автоматически обнаружить товары в разделе цен Ozon. "
            "Интерфейс кабинета мог измениться; обязательный импорт SKU не включается."
        )

    ordered = sorted(
        products.values(),
        key=lambda item: (
            str(item.get("offer_id") or ""),
            str(item.get("sku") or ""),
            str(item.get("product_id") or ""),
        ),
    )
    state.update(
        phase="collecting",
        message=f"Обнаружено {len(ordered)} товаров. Собираю цены…",
        discovered=len(ordered),
        total_hint=total_hint,
    )
    state.log(f"Автоматически обнаружено товаров: {len(ordered)}.")

    detail_page = context.new_page()
    detail_page.set_default_timeout(30_000)
    detail_total: dict[str, int | None] = {"value": total_hint}
    capture = attach_response_capture(detail_page, products, common_cache, detail_total)
    rows: list[dict[str, Any]] = []
    ok = 0
    failed = 0
    try:
        for index, candidate in enumerate(ordered, 1):
            if stop_event.is_set():
                break
            product_id = str(candidate["product_id"])
            product_url = DETAIL_URL.format(product_id=product_id)
            row: dict[str, Any] = {
                "profile_name": profile["name"],
                "product_id": product_id,
                "offer_id": candidate.get("offer_id"),
                "sku": candidate.get("sku"),
                "name": candidate.get("name"),
                "status": candidate.get("status"),
                "product_url": product_url,
                "collected_at": now_iso(),
            }
            try:
                detail_page.goto(product_url, wait_until="domcontentloaded", timeout=60_000)
                detail_page.wait_for_timeout(2_000)
                parsed = parse_html(detail_page.content(), want_offer_id=candidate.get("offer_id"))
                row.update({key: value for key, value in parsed.items() if value not in (None, "")})
                for _ in range(8):
                    if product_id in common_cache:
                        break
                    detail_page.wait_for_timeout(350)
                row.update(extract_common_price_fields(common_cache.get(product_id)))
                customer_price, source = choose_customer_price(row)
                row["customer_price"] = customer_price
                row["customer_price_source"] = source or row.get("customer_price_source")
                parse_error = row.pop("_parse_error", None)
                incomplete = bool(row.pop("_incomplete", False))
                if parse_error or incomplete or customer_price is None:
                    row["collection_status"] = "PARTIAL"
                    problems = [str(parse_error)] if parse_error else []
                    if customer_price is None:
                        problems.append("Цена клиента не найдена")
                    if incomplete:
                        problems.append("Неполный state страницы")
                    row["error"] = "; ".join(problems)
                    failed += 1
                else:
                    row["collection_status"] = "OK"
                    row["error"] = None
                    ok += 1
            except Exception as exc:
                row["collection_status"] = "ERROR"
                row["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
                failed += 1
            rows.append(row)
            state.update(
                processed=index,
                ok=ok,
                failed=failed,
                message=f"Обработано {index}/{len(ordered)} · успешно {ok} · с замечаниями {failed}",
            )
            state.log(f"[{index}/{len(ordered)}] {row.get('offer_id') or product_id}: {row['collection_status']}")
            detail_page.wait_for_timeout(450 + random.randint(0, 350))
    finally:
        try:
            detail_page.remove_listener("response", capture)
        except Exception:
            pass
        try:
            detail_page.close()
        except Exception:
            pass

    completed_at = now_iso()
    stopped = stop_event.is_set()
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    filename = f"ozon_customer_prices_{profile['slug']}_{timestamp}.xlsx"
    export_path = Path(profile["export_dir"]) / filename
    metadata = {
        "version": state.snapshot().get("version"),
        "profile_name": profile["name"],
        "started_at": started_at,
        "completed_at": completed_at,
        "discovered": len(ordered),
        "processed": len(rows),
        "ok": ok,
        "failed": failed,
        "stopped": stopped,
    }
    write_workbook(export_path, rows, metadata)
    export_path.with_suffix(".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    phase = "stopped" if stopped else "complete"
    message = (
        f"Сбор остановлен. Сохранён частичный Excel: {len(rows)}/{len(ordered)} товаров."
        if stopped
        else f"Готово: {ok} успешно, {failed} с замечаниями. Excel можно скачать."
    )
    state.update(
        phase=phase,
        message=message,
        running=False,
        stop_requested=False,
        processed=len(rows),
        ok=ok,
        failed=failed,
        export_ready=True,
        export_filename=filename,
        export_path=str(export_path),
        completed_at=completed_at,
    )
    state.log(message)
    stop_event.clear()

"""Automatic assortment discovery in an already-authorized Ozon seller session."""

from __future__ import annotations

from threading import Event
from typing import Any, Callable

from .browser_helpers import (
    PRICE_MANAGER_URLS,
    click_next_page,
    extract_dom_links,
    has_common_price_fields,
    is_login_page,
    merge_products,
    product_id_from_mapping,
    products_from_html_links,
    safe_json_response,
    scroll_discovery_surfaces,
    walk_dicts,
)
from .parser import extract_products_from_payload, extract_total_hint
from .state import RuntimeState


def attach_response_capture(
    page: Any,
    products: dict[str, dict[str, Any]],
    common_cache: dict[str, dict[str, Any]],
    total_box: dict[str, int | None],
) -> Callable[[Any], None]:
    """Observe read responses used by the Ozon UI; never intercept or mutate requests."""

    def capture(response: Any) -> None:
        url = str(response.url or "").lower()
        if not any(hint in url for hint in ("get-common-prices", "price", "product", "catalog", "item")):
            return
        payload = safe_json_response(response)
        if payload is None:
            return
        merge_products(products, extract_products_from_payload(payload))
        hint = extract_total_hint(payload)
        current = total_box.get("value")
        if hint and (current is None or hint > int(current or 0)):
            total_box["value"] = hint
        if "get-common-prices" not in url:
            return
        for mapping in walk_dicts(payload):
            product_id = product_id_from_mapping(mapping)
            if product_id and has_common_price_fields(mapping):
                common_cache[product_id] = mapping

    page.on("response", capture)
    return capture


def discover_products(
    page: Any,
    state: RuntimeState,
    stop_event: Event,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], int | None]:
    products: dict[str, dict[str, Any]] = {}
    common_cache: dict[str, dict[str, Any]] = {}
    total_box: dict[str, int | None] = {"value": None}
    capture = attach_response_capture(page, products, common_cache, total_box)
    try:
        for route_index, route in enumerate(PRICE_MANAGER_URLS, 1):
            if stop_event.is_set():
                break
            state.update(
                phase="discovering",
                message=f"Ищу ассортимент в кабинете: маршрут {route_index}/{len(PRICE_MANAGER_URLS)}…",
                discovered=len(products),
                total_hint=total_box["value"],
            )
            try:
                page.goto(route, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(2_500)
            except Exception as exc:
                state.log(
                    f"Маршрут {route} открылся с предупреждением: {str(exc)[:140]}",
                    level="warning",
                )
            if is_login_page(page):
                raise RuntimeError("Сессия Ozon не авторизована или истекла.")

            stable_rounds = 0
            previous_count = len(products)
            for _ in range(80):
                if stop_event.is_set():
                    break
                merge_products(products, extract_dom_links(page))
                try:
                    merge_products(products, products_from_html_links(page.content()))
                except Exception:
                    pass
                total_hint = total_box["value"]
                state.update(discovered=len(products), total_hint=total_hint)
                if total_hint and len(products) >= total_hint:
                    break
                if len(products) == previous_count:
                    stable_rounds += 1
                else:
                    stable_rounds = 0
                    previous_count = len(products)
                scroll_discovery_surfaces(page)
                page.wait_for_timeout(700)
                if stable_rounds >= 5:
                    if click_next_page(page):
                        page.wait_for_timeout(1_800)
                        stable_rounds = 0
                        continue
                    break
            if products and (not total_box["value"] or len(products) >= int(total_box["value"] or 0)):
                break
    finally:
        try:
            page.remove_listener("response", capture)
        except Exception:
            pass
    return products, common_cache, total_box["value"]

"""Small, read-only browser helpers for the Ozon price exporter."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from .parser import merge_candidate


SELLER_HOME = "https://seller.ozon.ru/"
PRICE_MANAGER_URLS = (
    "https://seller.ozon.ru/app/prices/manager",
    "https://seller.ozon.ru/app/products/prices",
    "https://seller.ozon.ru/app/products",
)
DETAIL_URL = "https://seller.ozon.ru/app/prices/manager/{product_id}/prices"

_RESPONSE_URL_HINTS = ("get-common-prices", "price", "product", "catalog", "item")
_LOGIN_URL_HINTS = ("login", "signin", "auth", "id.ozon")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def safe_json_response(response: Any) -> Any | None:
    """Return a bounded JSON response body without exposing it outside memory."""
    try:
        headers = response.headers
        content_type = str(headers.get("content-type", "")).lower()
        content_length = int(headers.get("content-length") or 0)
        if content_length > 12_000_000:
            return None
        url = str(response.url or "").lower()
        if "json" not in content_type and not any(hint in url for hint in _RESPONSE_URL_HINTS):
            return None
        return response.json()
    except Exception:
        return None


def is_login_page(page: Any) -> bool:
    url = str(getattr(page, "url", "") or "").lower()
    if any(hint in url for hint in _LOGIN_URL_HINTS):
        return True
    try:
        return page.locator('input[type="password"]').count() > 0
    except Exception:
        return False


def looks_logged_in(page: Any) -> bool:
    url = str(getattr(page, "url", "") or "").lower()
    return "seller.ozon.ru" in url and "/app/" in url and not is_login_page(page)


def merge_products(
    target: dict[str, dict[str, Any]], incoming: dict[str, dict[str, Any]]
) -> int:
    before = len(target)
    for product_id, candidate in incoming.items():
        current = target.setdefault(product_id, {"product_id": product_id})
        merge_candidate(current, candidate)
    return len(target) - before


def extract_dom_links(page: Any) -> dict[str, dict[str, Any]]:
    try:
        links = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href || '',
                text: (a.innerText || a.textContent || '').trim()
            }))
            """
        )
    except Exception:
        return {}
    products: dict[str, dict[str, Any]] = {}
    for item in links or []:
        href = str((item or {}).get("href") or "")
        match = re.search(r"/app/prices/manager/(\d+)/prices", href)
        if not match:
            continue
        product_id = match.group(1)
        record = products.setdefault(product_id, {"product_id": product_id})
        text = str((item or {}).get("text") or "").strip()
        if text and not record.get("name"):
            record["name"] = text[:500]
    return products


def products_from_html_links(html: str) -> dict[str, dict[str, Any]]:
    products: dict[str, dict[str, Any]] = {}
    for product_id in re.findall(r"/app/prices/manager/(\d+)/prices", html):
        products.setdefault(product_id, {"product_id": product_id})
    return products


def scroll_discovery_surfaces(page: Any) -> None:
    try:
        page.evaluate(
            """
            () => {
              const surfaces = new Set([document.scrollingElement, document.documentElement, document.body]);
              document.querySelectorAll('main,[role="grid"],[role="table"],[data-scroll-container]').forEach(el => surfaces.add(el));
              document.querySelectorAll('div').forEach(el => {
                const style = getComputedStyle(el);
                if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 200) {
                  surfaces.add(el);
                }
              });
              surfaces.forEach(el => {
                if (!el) return;
                try { el.scrollTop = el.scrollHeight; } catch (_) {}
              });
              window.scrollTo(0, Math.max(document.body.scrollHeight, document.documentElement.scrollHeight));
            }
            """
        )
    except Exception:
        return


def click_next_page(page: Any) -> bool:
    """Click only an explicit visible pagination control, never an action button."""
    try:
        return bool(
            page.evaluate(
                """
                () => {
                  const exact = /^(следующая|следующий|вперёд|вперед|далее|next)$/i;
                  const selector = 'nav button, nav a, [role="navigation"] button, [role="navigation"] a, [class*="pagination"] button, [class*="pagination"] a, a[rel="next"]';
                  for (const el of Array.from(document.querySelectorAll(selector))) {
                    const label = ((el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || '') + '').trim();
                    const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true' || el.classList.contains('disabled');
                    const rect = el.getBoundingClientRect();
                    if (!disabled && rect.width > 0 && rect.height > 0 && (el.getAttribute('rel') === 'next' || exact.test(label))) {
                      el.click();
                      return true;
                    }
                  }
                  return false;
                }
                """
            )
        )
    except Exception:
        return False


def walk_dicts(value: Any):
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            yield current
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)


def product_id_from_mapping(mapping: dict[str, Any]) -> str | None:
    for key in ("item_id", "itemId", "product_id", "productId"):
        value = mapping.get(key)
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str) and value.isdigit():
            return value
    return None


def has_common_price_fields(mapping: dict[str, Any]) -> bool:
    return any(
        key in mapping
        for key in (
            "marketing_oa_price",
            "marketingOaPrice",
            "marketing_price",
            "marketingPrice",
            "marketing_actions",
            "marketingActions",
        )
    )

"""Public parser facade for the Ozon customer-price exporter."""

from __future__ import annotations

from typing import Any

from .parser_html import parse_html
from .parser_payload import (
    extract_common_price_fields,
    extract_products_from_payload,
    extract_total_hint,
    iter_mappings,
    merge_candidate,
    to_float,
)


def choose_customer_price(row: dict[str, Any]) -> tuple[float | None, str | None]:
    precedence = (
        ("customer_price", "get-common-prices.marketing_oa_price"),
        ("promo_effective_price", "get-common-prices.marketing_price"),
        ("marketing_price", "__MODULE_STATE__.price.marketingPrice"),
        ("fbo_customer_price", "DOM: Цена по FBO"),
        ("fbs_customer_price", "DOM: Цена по FBS"),
    )
    for key, default_source in precedence:
        value = to_float(row.get(key))
        if value is not None:
            source = row.get("customer_price_source") if key == "customer_price" else None
            return value, str(source or default_source)
    return None, None


__all__ = [
    "choose_customer_price",
    "extract_common_price_fields",
    "extract_products_from_payload",
    "extract_total_hint",
    "iter_mappings",
    "merge_candidate",
    "parse_html",
]

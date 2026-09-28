"""Generic extraction of Ozon product and price candidates from JSON payloads."""

from __future__ import annotations

import re
from typing import Any, Iterable, Iterator


PRODUCT_ID_KEYS = ("item_id", "itemId", "product_id", "productId", "itemID")
OFFER_ID_KEYS = ("offer_id", "offerId", "seller_sku", "sellerSku", "offer")
SKU_KEYS = ("sku", "ozonSku", "ozon_sku", "fboSku", "fbsSku")
TOTAL_KEYS = (
    "total",
    "total_count",
    "totalCount",
    "total_items",
    "totalItems",
    "items_total",
    "itemsTotal",
)


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def money_to_float(value: Any) -> float | None:
    """Convert Ozon scalar or protobuf-style money object to rubles."""
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        if "units" in value or "nanos" in value:
            units = to_float(value.get("units")) or 0.0
            nanos = to_float(value.get("nanos")) or 0.0
            if units < 0 < nanos:
                return units - nanos / 1_000_000_000
            return units + nanos / 1_000_000_000
        for key in ("amount", "value", "price"):
            if key in value:
                converted = money_to_float(value.get(key))
                if converted is not None:
                    return converted
        return None
    return to_float(value)


def to_int_string(value: Any) -> str | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if re.fullmatch(r"\d+", text):
        return text
    if re.fullmatch(r"\d+\.0+", text):
        return text.split(".", 1)[0]
    return None


def first_value(mapping: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def iter_mappings(value: Any) -> Iterator[dict[str, Any]]:
    stack = [value]
    seen: set[int] = set()
    while stack:
        current = stack.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if isinstance(current, dict):
            yield current
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _sku_from_parts(mapping: dict[str, Any]) -> str | None:
    direct = first_value(mapping, SKU_KEYS)
    if direct not in (None, ""):
        return str(direct)

    price_indexes = _as_dict(mapping.get("part_price_indexes_full"))
    for item in _as_list(price_indexes.get("price_indexes")):
        if isinstance(item, dict) and item.get("sku") not in (None, ""):
            return str(item["sku"])

    for part_name, list_name in (
        ("part_sources", "sources"),
        ("part_stocks", "stocks"),
        ("part_availability", "availabilities"),
    ):
        part = _as_dict(mapping.get(part_name))
        for item in _as_list(part.get(list_name)):
            if isinstance(item, dict) and item.get("sku") not in (None, ""):
                return str(item["sku"])
    return None


def _normalize_current_product(mapping: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize the current `/api/v1/products/list-by-filter` response shape."""
    product_id = to_int_string(first_value(mapping, PRODUCT_ID_KEYS))
    if product_id is None or not any(key.startswith("part_") for key in mapping):
        return None

    part_item = _as_dict(mapping.get("part_item"))
    part_status = _as_dict(mapping.get("part_status"))
    status_texts = _as_dict(part_status.get("texts"))
    part_category = _as_dict(mapping.get("part_category"))
    category_texts = _as_dict(part_category.get("texts"))
    part_price = _as_dict(mapping.get("part_price"))
    part_marketing = _as_dict(mapping.get("part_marketing_price"))

    candidate: dict[str, Any] = {
        "product_id": product_id,
        "offer_id": None if part_item.get("offer_id") in (None, "") else str(part_item.get("offer_id")),
        "sku": _sku_from_parts(mapping),
        "name": part_item.get("name") or part_item.get("title"),
        "status": status_texts.get("state_name") or part_status.get("state") or part_status.get("state_name"),
        "category": (
            category_texts.get("category_name")
            or category_texts.get("category_name_3_lvl")
            or category_texts.get("category_name_2_lvl")
        ),
        "price": money_to_float(part_price.get("price")),
        "old_price": money_to_float(part_price.get("old_price")),
        "min_price": money_to_float(part_price.get("min_price")),
        "net_price": money_to_float(part_price.get("net_price")),
        "marketing_price": money_to_float(part_marketing.get("price")),
        "promo_effective_price": money_to_float(part_marketing.get("price")),
        "marketing_seller_price": money_to_float(part_marketing.get("seller_price")),
        "customer_price": money_to_float(part_marketing.get("oa_price")),
        "customer_price_source": "list-by-filter.part_marketing_price.oa_price",
        "ozon_card_price": money_to_float(part_marketing.get("oa_price")),
        "currency": (
            _as_dict(part_price.get("price")).get("currencyCode")
            or part_price.get("currency")
            or _as_dict(part_marketing.get("price")).get("currencyCode")
        ),
    }

    stocks = _as_dict(mapping.get("part_stocks"))
    for stock in _as_list(stocks.get("stocks")):
        if not isinstance(stock, dict):
            continue
        source = str(stock.get("source") or "").lower()
        if source == "fbo":
            candidate["fbo_stock"] = stock.get("present")
            candidate["fbo_reserved"] = stock.get("reserved")
        elif source == "fbs":
            candidate["fbs_stock"] = stock.get("present")
            candidate["fbs_reserved"] = stock.get("reserved")

    return {key: value for key, value in candidate.items() if value not in (None, "", [], {})}


def _looks_like_product(mapping: dict[str, Any]) -> bool:
    if _normalize_current_product(mapping) is not None:
        return True
    product_id = first_value(mapping, PRODUCT_ID_KEYS)
    offer_id = first_value(mapping, OFFER_ID_KEYS)
    sku = first_value(mapping, SKU_KEYS)
    price_keys = {
        "price",
        "old_price",
        "oldPrice",
        "marketing_price",
        "marketingPrice",
        "marketing_oa_price",
        "marketingOaPrice",
    }
    if product_id is not None:
        identity = offer_id is not None or sku is not None
        descriptive = any(mapping.get(key) not in (None, "") for key in ("title", "name", "product_name"))
        priced = bool(price_keys.intersection(mapping.keys())) or isinstance(mapping.get("price"), dict)
        return identity or descriptive or priced
    return (offer_id is not None or sku is not None) and bool(price_keys.intersection(mapping.keys()))


def normalize_product_candidate(mapping: dict[str, Any]) -> dict[str, Any] | None:
    current = _normalize_current_product(mapping)
    if current is not None:
        return current
    if not _looks_like_product(mapping):
        return None
    product_id = to_int_string(first_value(mapping, PRODUCT_ID_KEYS))
    if product_id is None:
        return None
    offer_raw = first_value(mapping, OFFER_ID_KEYS)
    sku_raw = first_value(mapping, SKU_KEYS)
    price_obj = mapping.get("price") if isinstance(mapping.get("price"), dict) else {}
    status_obj = mapping.get("status") if isinstance(mapping.get("status"), dict) else {}
    candidate: dict[str, Any] = {
        "product_id": product_id,
        "offer_id": None if offer_raw in (None, "") else str(offer_raw),
        "sku": None if sku_raw in (None, "") else str(sku_raw),
        "name": mapping.get("title") or mapping.get("name") or mapping.get("product_name"),
        "status": status_obj.get("stateName") or mapping.get("status_name") or mapping.get("stateName"),
    }
    aliases = {
        "price": ("price",),
        "old_price": ("old_price", "oldPrice"),
        "min_price": ("min_price", "minPrice", "minAutoPrice"),
        "marketing_price": ("marketing_price", "marketingPrice"),
        "customer_price": ("marketing_oa_price", "marketingOaPrice", "customer_price", "customerPrice"),
    }
    for output_key, keys in aliases.items():
        direct = first_value(mapping, keys)
        nested = first_value(price_obj, keys)
        if isinstance(direct, list):
            direct = None
        value = direct if direct not in (None, "") else nested
        converted = money_to_float(value)
        if converted is not None:
            candidate[output_key] = converted
    return candidate


def merge_candidate(target: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    replaceable_keys = {
        "customer_price",
        "customer_price_source",
        "ozon_card_price",
        "promo_effective_price",
        "marketing_price",
        "marketing_seller_price",
        "price",
        "old_price",
        "min_price",
        "net_price",
        "fbo_stock",
        "fbo_reserved",
        "fbs_stock",
        "fbs_reserved",
    }
    for key, value in incoming.items():
        if value in (None, "", [], {}):
            continue
        if target.get(key) in (None, "", [], {}) or key in replaceable_keys:
            target[key] = value
    return target


def extract_products_from_payload(payload: Any) -> dict[str, dict[str, Any]]:
    products: dict[str, dict[str, Any]] = {}
    for mapping in iter_mappings(payload):
        candidate = normalize_product_candidate(mapping)
        if not candidate:
            continue
        product_id = candidate["product_id"]
        merge_candidate(products.setdefault(product_id, {"product_id": product_id}), candidate)
    return products


def extract_total_hint(payload: Any) -> int | None:
    values: list[int] = []
    for mapping in iter_mappings(payload):
        for key in TOTAL_KEYS:
            value = mapping.get(key)
            if isinstance(value, bool):
                continue
            try:
                number = int(value)
            except (TypeError, ValueError):
                continue
            if 0 < number < 5_000_000:
                values.append(number)
    return max(values) if values else None


def extract_common_price_fields(item: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {
            "promo_effective_price": None,
            "customer_price": None,
            "customer_price_source": None,
            "ozon_card_price": None,
            "actions_count": None,
            "actions_titles": None,
            "actions_dates": None,
        }
    customer_aliases = (
        "marketing_oa_price",
        "marketingOaPrice",
        "customer_price",
        "customerPrice",
        "oa_price",
        "oaPrice",
    )
    customer_key = next((key for key in customer_aliases if item.get(key) not in (None, "")), None)
    marketing = first_value(item, ("marketing_price", "marketingPrice"))
    actions_raw = item.get("marketing_actions") or item.get("marketingActions") or []
    actions = [entry for entry in actions_raw if isinstance(entry, dict)]
    seller_actions = [entry for entry in actions if entry.get("is_seller_action", entry.get("isSellerAction", True))]
    titles = [str(entry.get("name") or entry.get("title") or "").strip() for entry in seller_actions]
    dates = [str(entry.get("date_to") or entry.get("dateTo") or "")[:10] for entry in seller_actions]
    customer_price = money_to_float(item.get(customer_key)) if customer_key else None
    return {
        "promo_effective_price": money_to_float(marketing),
        "customer_price": customer_price,
        "customer_price_source": f"get-common-prices.{customer_key}" if customer_key else None,
        "ozon_card_price": customer_price,
        "actions_count": len(seller_actions),
        "actions_titles": "; ".join(value for value in titles if value),
        "actions_dates": "; ".join(value for value in dates if value),
    }

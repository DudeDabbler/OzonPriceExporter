"""Parse confirmed Ozon seller price fields from __MODULE_STATE__ and visible DOM.

Adapted from analytics-wb-continent blob bab985081919493d1c4f0d242029745ae96a5761.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any

from .parser_payload import OFFER_ID_KEYS, SKU_KEYS, first_value, iter_mappings, to_float

_WS = {"\u2009": " ", "\u202f": " ", "\u00a0": " ", "\u200b": ""}


def _balanced_json(source: str, start: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise ValueError("unbalanced JSON object")


def extract_module_state_prices(html: str) -> dict[str, Any] | None:
    patterns = (
        r'\(\s*window\.__MODULE_STATE__\s*=\s*window\.__MODULE_STATE__\s*\|\|\s*\{\}\s*\)\s*\[\s*["\']prices["\']\s*\]\s*=\s*\{',
        r'window\.__MODULE_STATE__\s*\[\s*["\']prices["\']\s*\]\s*=\s*\{',
        r'["\']prices["\']\s*:\s*\{',
    )
    for pattern in patterns:
        match = re.search(pattern, html)
        if not match:
            continue
        brace = match.end() - 1
        if brace < 0 or html[brace] != "{":
            brace = html.find("{", match.end())
        if brace < 0:
            continue
        try:
            value = json.loads(_balanced_json(html, brace))
        except (ValueError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def _is_canonical(mapping: dict[str, Any], want_offer_id: str | None) -> bool:
    offer = first_value(mapping, OFFER_ID_KEYS)
    if offer in (None, "") or (want_offer_id is not None and str(offer) != str(want_offer_id)):
        return False
    price_obj = mapping.get("price")
    return isinstance(price_obj, dict) and any(
        key in price_obj for key in ("minAutoPrice", "price", "oldPrice", "marketingPrice")
    )


def first_product(state: dict[str, Any], want_offer_id: str | None = None) -> dict[str, Any] | None:
    fallback = None
    for mapping in iter_mappings(state):
        if _is_canonical(mapping, want_offer_id):
            return mapping
        if fallback is None and _is_canonical(mapping, None):
            fallback = mapping
    return fallback if want_offer_id is None else None


def product_json_fields(product: dict[str, Any]) -> dict[str, Any]:
    price = product.get("price") if isinstance(product.get("price"), dict) else {}
    indexes = product.get("priceIndexes") if isinstance(product.get("priceIndexes"), dict) else {}
    external = indexes.get("externalIndexData") if isinstance(indexes.get("externalIndexData"), dict) else {}
    stock = product.get("stock") if isinstance(product.get("stock"), dict) else {}
    seller_stock = product.get("sellerStock") if isinstance(product.get("sellerStock"), dict) else {}
    status = product.get("status") if isinstance(product.get("status"), dict) else {}
    offer = first_value(product, OFFER_ID_KEYS)
    sku = first_value(product, SKU_KEYS)
    return {
        "offer_id": None if offer in (None, "") else str(offer),
        "sku": None if sku in (None, "") else str(sku),
        "name": product.get("title") or product.get("name"),
        "status": status.get("stateName") or product.get("stateName"),
        "category": product.get("descriptionCategoryName3Lvl") or product.get("descriptionCategoryName"),
        "price": to_float(price.get("price")),
        "old_price": to_float(price.get("oldPrice")),
        "min_price": to_float(price.get("minAutoPrice")),
        "net_price": to_float(price.get("netPrice")),
        "marketing_seller_price": to_float(price.get("marketingSellerPrice")),
        "marketing_price": to_float(price.get("marketingPrice")),
        "currency": price.get("currency"),
        "auto_action_enabled": price.get("autoActionEnabled"),
        "auto_add_to_ozon_actions": price.get("autoAddToOzonActions"),
        "color_index": indexes.get("priceColorIndex"),
        "external_index_value": to_float(external.get("priceIndexValue")),
        "external_competitor_min_price": to_float(external.get("minPrice")),
        "external_competitor_url": external.get("canonicalUrl"),
        "fbo_stock": stock.get("present"),
        "fbo_reserved": stock.get("reserved"),
        "fbs_stock": seller_stock.get("present"),
        "fbs_reserved": seller_stock.get("reserved"),
    }


class _VisibleTextParser(HTMLParser):
    _SKIP = frozenset({"script", "style", "svg"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._SKIP:
            self._skip_depth += 1
        elif self._skip_depth == 0:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif self._skip_depth == 0:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def visible_lines(html: str) -> list[str]:
    parser = _VisibleTextParser()
    try:
        parser.feed(html)
        text = parser.text()
    except Exception:
        text = re.sub(r"<(script|style|svg)\b[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
        text = re.sub(r"<[^>]+>", "\n", text)
    for source, replacement in _WS.items():
        text = text.replace(source, replacement)
    return [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]


def _money_values(text: str) -> list[float]:
    values: list[float] = []
    for raw in re.findall(r"(\d[\d\s\u00a0\u202f]*(?:[.,]\d+)?)\s*₽", text):
        value = to_float(raw)
        if value is not None:
            values.append(value)
    return values


def _price_before_label(lines: list[str], labels: tuple[str, ...]) -> float | None:
    normalized_labels = {re.sub(r"\s+", " ", label.casefold()).strip() for label in labels}
    for index, line in enumerate(lines):
        normalized = re.sub(r"\s+", " ", line.casefold()).strip()
        if normalized not in normalized_labels or index == 0:
            continue
        values = _money_values(lines[index - 1])
        if values:
            return values[0]
    return None


def parse_html(html: str, want_offer_id: str | None = None) -> dict[str, Any]:
    state = extract_module_state_prices(html)
    if not state:
        return {"offer_id": want_offer_id, "_parse_error": "state __MODULE_STATE__.prices не найден", "_incomplete": True}
    product = first_product(state, want_offer_id)
    if not product:
        return {"offer_id": want_offer_id, "_parse_error": "каноничный товар не найден в state", "_incomplete": True}
    row = product_json_fields(product)
    lines = visible_lines(html)
    row.update(
        {
            "ozon_card_price": _price_before_label(lines, ("Цена с картой", "Цена по карте")),
            "fbo_customer_price": _price_before_label(lines, ("Цена по FBO",)),
            "fbs_customer_price": _price_before_label(lines, ("Цена по FBS",)),
            "_parse_error": None,
        }
    )
    row["_incomplete"] = row.get("price") is None and row.get("marketing_price") is None
    return row

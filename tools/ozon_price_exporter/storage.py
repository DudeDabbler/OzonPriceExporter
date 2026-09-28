from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


_MAX_PROFILE_NAME = 80


def default_storage_root() -> Path:
    override = (
        os.getenv("DUDEDABBLER_OZON_PRICE_EXPORTER_HOME")
        or os.getenv("IFOAM_OZON_PRICE_EXPORTER_HOME")
    )
    if override:
        return Path(override).expanduser().resolve()
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        # Keep the historical path so existing authorized profiles remain usable.
        return Path(local_app_data) / "IFOAM" / "OzonPriceExporter"
    return Path.home() / ".dudedabbler" / "ozon-price-exporter"


def normalize_profile_name(value: str) -> str:
    name = re.sub(r"\s+", " ", str(value or "").strip())
    if not name:
        raise ValueError("Укажите название магазина.")
    if len(name) > _MAX_PROFILE_NAME:
        raise ValueError(f"Название магазина не должно быть длиннее {_MAX_PROFILE_NAME} символов.")
    if any(ord(ch) < 32 for ch in name):
        raise ValueError("Название магазина содержит недопустимые управляющие символы.")
    return name


def profile_slug(name: str) -> str:
    normalized = normalize_profile_name(name)
    ascii_part = normalized.lower().encode("ascii", "ignore").decode("ascii")
    ascii_part = re.sub(r"[^a-z0-9]+", "-", ascii_part).strip("-")[:36]
    digest = hashlib.sha256(normalized.casefold().encode("utf-8")).hexdigest()[:10]
    return f"{ascii_part or 'shop'}-{digest}"


class ProfileStore:
    """Local profile registry.

    Only a display name and filesystem slug are stored in JSON. Ozon session
    cookies remain inside the Playwright browser profile directory.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or default_storage_root()).resolve()
        self.profiles_dir = self.root / "profiles"
        self.exports_dir = self.root / "exports"
        self.registry_path = self.root / "profiles.json"
        self._lock = RLock()
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    def _load_registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"schema_version": 1, "profiles": []}
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": 1, "profiles": []}
        if not isinstance(payload, dict) or not isinstance(payload.get("profiles"), list):
            return {"schema_version": 1, "profiles": []}
        return payload

    def _save_registry(self, payload: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temp = self.registry_path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.registry_path)

    def ensure_profile(self, display_name: str) -> dict[str, str]:
        name = normalize_profile_name(display_name)
        slug = profile_slug(name)
        with self._lock:
            registry = self._load_registry()
            profiles = registry["profiles"]
            record = next((p for p in profiles if p.get("slug") == slug), None)
            if record is None:
                record = {
                    "name": name,
                    "slug": slug,
                    "created_at": self._now(),
                    "last_used_at": self._now(),
                }
                profiles.append(record)
            else:
                record["name"] = name
                record["last_used_at"] = self._now()
            profiles.sort(key=lambda p: str(p.get("last_used_at", "")), reverse=True)
            self._save_registry(registry)

        browser_dir = self.profiles_dir / slug / "browser"
        export_dir = self.exports_dir / slug
        browser_dir.mkdir(parents=True, exist_ok=True)
        export_dir.mkdir(parents=True, exist_ok=True)
        return {
            "name": name,
            "slug": slug,
            "browser_dir": str(browser_dir),
            "export_dir": str(export_dir),
        }

    def list_profiles(self) -> list[dict[str, str]]:
        with self._lock:
            registry = self._load_registry()
            return [
                {
                    "name": str(item.get("name", "")),
                    "slug": str(item.get("slug", "")),
                    "last_used_at": str(item.get("last_used_at", "")),
                }
                for item in registry.get("profiles", [])
                if item.get("name") and item.get("slug")
            ]

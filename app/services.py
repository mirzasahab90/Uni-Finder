"""University search: Hipolabs primary API + official GitHub JSON fallback."""

from __future__ import annotations

import time
from typing import Any

import httpx

PRIMARY_URL = "http://universities.hipolabs.com/search"
BACKUP_URL = (
    "https://raw.githubusercontent.com/Hipo/university-domains-list/"
    "master/world_universities_and_domains.json"
)
PRIMARY_TIMEOUT = 8.0
BACKUP_TIMEOUT = 20.0
BACKUP_CACHE_TTL = 60 * 60 * 24  # 24 hours
MAX_RESULTS = 50

_backup_cache: list[dict[str, Any]] | None = None
_backup_cached_at: float = 0.0


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": item.get("name") or "",
        "country": item.get("country") or "",
        "alpha_two_code": item.get("alpha_two_code"),
        "state-province": item.get("state-province"),
        "domains": item.get("domains") or [],
        "web_pages": item.get("web_pages") or [],
    }


def _haystack(item: dict[str, Any]) -> str:
    parts = [
        item.get("name") or "",
        " ".join(item.get("domains") or []),
        " ".join(item.get("web_pages") or []),
    ]
    return " ".join(parts).lower()


def _name_matches(item: dict[str, Any], name_q: str) -> bool:
    if not name_q:
        return True

    text = _haystack(item)
    if name_q in text:
        return True

    words = [w for w in name_q.split() if len(w) > 1]
    if words and all(w in text for w in words):
        return True

    return False


def _country_matches(item: dict[str, Any], country_q: str) -> bool:
    if not country_q:
        return True
    uni_country = (item.get("country") or "").lower()
    code = (item.get("alpha_two_code") or "").lower()
    return country_q in uni_country or country_q == code


def _filter_local(
    data: list[dict[str, Any]],
    name: str | None,
    country: str | None,
) -> list[dict[str, Any]]:
    name_q = (name or "").strip().lower()
    country_q = (country or "").strip().lower()
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in data:
        if not _name_matches(item, name_q):
            continue
        if not _country_matches(item, country_q):
            continue

        key = f"{(item.get('name') or '').lower()}|{(item.get('country') or '').lower()}"
        if key in seen:
            continue
        seen.add(key)

        results.append(_normalize(item))
        if len(results) >= MAX_RESULTS:
            break

    return results


async def _fetch_primary(
    name: str | None,
    country: str | None,
    *,
    use_contains: bool = False,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {}
    cleaned_name = name.strip() if name and name.strip() else ""
    cleaned_country = country.strip() if country and country.strip() else ""

    if cleaned_name:
        # Hipolabs `name` is prefix-based; `name_contains` matches inside the name.
        if use_contains:
            params["name_contains"] = cleaned_name
        else:
            params["name"] = cleaned_name
    if cleaned_country:
        params["country"] = cleaned_country

    async with httpx.AsyncClient(timeout=PRIMARY_TIMEOUT, follow_redirects=True) as client:
        response = await client.get(PRIMARY_URL, params=params)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected primary API response")

    return [_normalize(item) for item in data[:MAX_RESULTS]]


async def _load_backup() -> list[dict[str, Any]]:
    global _backup_cache, _backup_cached_at

    now = time.time()
    if _backup_cache is not None and (now - _backup_cached_at) < BACKUP_CACHE_TTL:
        return _backup_cache

    async with httpx.AsyncClient(timeout=BACKUP_TIMEOUT, follow_redirects=True) as client:
        response = await client.get(BACKUP_URL)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected backup data format")

    _backup_cache = data
    _backup_cached_at = now
    return data


async def search_universities(
    name: str | None = None,
    country: str | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """
    Search by name and/or country.
    Returns only Hipolabs API data (or the same official GitHub list as backup).
    """
    if not (name and name.strip()) and not (country and country.strip()):
        return [], "none"

    # 1) Hipolabs live API
    try:
        results = await _fetch_primary(name, country, use_contains=False)

        if not results and name and name.strip():
            results = await _fetch_primary(name, country, use_contains=True)

        if (
            not results
            and name
            and name.strip()
            and country
            and country.strip()
        ):
            name_only = await _fetch_primary(name, None, use_contains=True)
            results = [
                item
                for item in name_only
                if _country_matches(item, country.strip().lower())
            ][:MAX_RESULTS]

        if results:
            return results, "primary"
    except Exception:
        pass

    # 2) Same official dataset from GitHub (only when API fails / empty for acronyms)
    backup = await _load_backup()
    return _filter_local(backup, name, country), "backup"

"""Helpers for posting Rolimon's trade advertisements.

This module intentionally avoids importing the bot's runtime modules so the local
web dashboard can use it without starting any trading loops.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import requests

CREATE_TRADE_AD_API = "https://api.rolimons.com/tradeads/v1/createad"
RECENT_TRADE_ADS_API = "https://api.rolimons.com/tradeads/v1/getrecentads"

REQUEST_TAGS = {
    "any": 4,
    "demand": 1,
    "rares": 2,
    "robux": 3,
    "upgrade": 5,
    "downgrade": 6,
    "rap": 7,
    "wishlist": 8,
    "projecteds": 9,
    "adds": 10,
}


class TradeAdError(RuntimeError):
    """Raised when the ROLI trade-ad API rejects a request."""


@dataclass(frozen=True)
class TradeAdPayload:
    """Normalized payload for the ROLI create trade ad endpoint."""

    player_id: int
    offer_item_ids: list[int]
    request_item_ids: list[int]
    request_tags: list[str]

    def as_api_payload(self) -> dict[str, object]:
        return {
            "player_id": self.player_id,
            "offer_item_ids": self.offer_item_ids,
            "request_item_ids": self.request_item_ids,
            "request_tags": [REQUEST_TAGS[tag] for tag in self.request_tags],
        }


def parse_id_list(raw_value: str) -> list[int]:
    """Parse a comma/space/newline separated list of Roblox item ids."""

    if not raw_value.strip():
        return []

    normalized = raw_value.replace("\n", ",").replace(" ", ",")
    item_ids: list[int] = []
    for part in normalized.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            item_ids.append(int(part))
        except ValueError as exc:
            raise ValueError(f"Invalid item id: {part}") from exc
    return item_ids


def normalize_tags(tags: Iterable[str]) -> list[str]:
    normalized_tags: list[str] = []
    for tag in tags:
        clean_tag = tag.strip().lower()
        if not clean_tag:
            continue
        if clean_tag not in REQUEST_TAGS:
            raise ValueError(f"Unsupported request tag: {tag}")
        if clean_tag not in normalized_tags:
            normalized_tags.append(clean_tag)
    return normalized_tags


def create_payload(
    player_id: str | int,
    offer_item_ids: str,
    request_item_ids: str,
    request_tags: Iterable[str],
) -> TradeAdPayload:
    """Validate dashboard form data and produce a ROLI API payload."""

    try:
        normalized_player_id = int(player_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("Player ID must be a number.") from exc

    offer_ids = parse_id_list(offer_item_ids)
    request_ids = parse_id_list(request_item_ids)
    tags = normalize_tags(request_tags)

    if not offer_ids:
        raise ValueError("Add at least one item ID to offer.")
    if not request_ids and not tags:
        raise ValueError("Add at least one requested item ID or request tag.")

    return TradeAdPayload(
        player_id=normalized_player_id,
        offer_item_ids=offer_ids,
        request_item_ids=request_ids,
        request_tags=tags,
    )


def post_trade_ad(
    roli_verification: str,
    payload: TradeAdPayload,
    timeout: int = 20,
) -> dict[str, object]:
    """Post a trade ad through Rolimon's create-ad endpoint."""

    if not roli_verification.strip():
        raise ValueError("ROLI verification cookie is required to post trade ads.")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=utf-8",
        "Cookie": f"_RoliVerification={roli_verification.strip()}",
    }
    response = requests.post(
        CREATE_TRADE_AD_API,
        headers=headers,
        json=payload.as_api_payload(),
        timeout=timeout,
    )

    if response.status_code == 201:
        return {"ok": True, "status_code": response.status_code, "message": "Trade ad posted."}

    status_messages = {
        400: "The ROLI trade-ad cooldown has not expired, or the request was invalid.",
        422: "The ROLI verification cookie is invalid or expired.",
        429: "ROLI is rate limiting trade-ad requests.",
    }
    detail = status_messages.get(response.status_code, "Unexpected response from ROLI.")
    raise TradeAdError(f"{detail} Status {response.status_code}: {response.text[:500]}")

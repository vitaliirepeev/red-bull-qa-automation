from __future__ import annotations

import math
from typing import Any

import allure

from clients.devices_client import DevicesClient


def fetch_all_devices(
    devices_client: DevicesClient, token: str, page_size: int = 15
) -> list[dict[str, Any]]:
    with allure.step("Fetch the complete Devices inventory"):
        first = devices_client.list_devices(token, page=1, page_size=page_size)
        assert first.status_code == 200
        assert isinstance(first.response_body, dict)

        items = list(first.response_body["items"])
        total = int(first.response_body["total"])
        pages = math.ceil(total / page_size)

        for page in range(2, pages + 1):
            exchange = devices_client.list_devices(
                token, page=page, page_size=page_size
            )
            assert exchange.status_code == 200
            items.extend(exchange.response_body["items"])

        return items


def find_device(
    inventory: list[dict[str, Any]], device_id: str
) -> dict[str, Any] | None:
    return next(
        (device for device in inventory if device.get("device_id") == device_id),
        None,
    )

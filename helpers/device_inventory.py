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


def core_service_versions(device: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return every core service and its current/latest versions from the API."""
    raw_versions = device.get("core_services_versions")
    assert isinstance(raw_versions, dict) and raw_versions, (
        "Device response must contain a non-empty core_services_versions object"
    )

    versions: dict[str, dict[str, Any]] = {}
    for service_name, service_versions in raw_versions.items():
        assert isinstance(service_versions, dict), (
            f"Core service {service_name!r} must contain a version object"
        )
        versions[str(service_name)] = {
            "current": service_versions.get("current"),
            "latest": service_versions.get("latest"),
        }
    return versions


def services_not_at_latest(
    versions: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        service_name: service_versions
        for service_name, service_versions in versions.items()
        if service_versions.get("latest")
        and service_versions.get("current") != service_versions.get("latest")
    }

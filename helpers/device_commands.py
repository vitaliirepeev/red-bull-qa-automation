from __future__ import annotations

from typing import Any


def update_core_services_body(
    devices: list[str | int], command_version: str
) -> dict[str, Any]:
    return {
        "devices": devices,
        "command_name": "update_core_services",
        "params": {"command_version": command_version},
    }


def accounted_targets(response_body: object) -> set[str]:
    """Return targets explicitly accounted for by a partial-result response."""
    if not isinstance(response_body, dict):
        return set()
    targets: set[str] = set()
    for key in ("updated", "failed", "skipped", "unknown"):
        values = response_body.get(key, [])
        if isinstance(values, list):
            for value in values:
                if isinstance(value, dict):
                    value = value.get("device") or value.get("device_id")
                if value is not None:
                    targets.add(str(value))
    return targets

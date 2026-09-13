from __future__ import annotations

from typing import Any

from clients.request_wrapper import ApiRequestWrapper
from models.api_exchange import ApiExchange


class DevicesClient:
    def __init__(self, api: ApiRequestWrapper) -> None:
        self.api = api

    def list_devices(
        self, token: str | None = None, page: int = 1, page_size: int = 15
    ) -> ApiExchange:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.api.send(
            "GET",
            "/api/devices",
            headers=headers,
            params={"page": page, "pageSize": page_size},
        )

    def send_command(
        self, body: dict[str, Any], token: str | None = None
    ) -> ApiExchange:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.api.send(
            "POST", "/api/devices/command", headers=headers, json=body
        )

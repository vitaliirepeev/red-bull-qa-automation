"""Custom HTTP request wrapper with debug history and Allure reporting."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import allure
import requests

from models.api_exchange import ApiExchange


SENSITIVE_KEYS = {"authorization", "password", "token", "access_token", "cookie"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<redacted>" if key.lower() in SENSITIVE_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class ApiRequestWrapper:
    """Send HTTP requests and retain sanitized, timed exchanges for debugging."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.exchange_history: list[ApiExchange] = []

    def send(self, method: str, path: str, **kwargs: Any) -> ApiExchange:
        method = method.upper()
        url = urljoin(self.base_url, path.lstrip("/"))

        with allure.step(f"HTTP {method} {path}"):
            sent_at_utc = _utc_now()
            started = time.perf_counter()
            response = self.session.request(
                method, url, timeout=self.timeout_seconds, **kwargs
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            received_at_utc = _utc_now()

            try:
                response_body: Any = response.json()
            except ValueError:
                response_body = response.text

            exchange = ApiExchange(
                method=method,
                url=str(response.request.url or url),
                sent_at_utc=sent_at_utc,
                received_at_utc=received_at_utc,
                request_params=kwargs.get("params"),
                request_body=kwargs.get("json"),
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                response_body=response_body,
            )
            self.exchange_history.append(exchange)
            self._attach_exchange(exchange, kwargs.get("headers", {}))
            return exchange

    @staticmethod
    def _attach_exchange(exchange: ApiExchange, headers: dict[str, str]) -> None:
        payload = {
            "request": {
                "sent_at_utc": exchange.sent_at_utc,
                "method": exchange.method,
                "url": exchange.url,
                "headers": _redact(headers),
                "query": _redact(exchange.request_params),
                "body": _redact(exchange.request_body),
            },
            "response": {
                "received_at_utc": exchange.received_at_utc,
                "status": exchange.status_code,
                "elapsed_ms": exchange.elapsed_ms,
                "body": _redact(exchange.response_body),
            },
        }
        allure.attach(
            json.dumps(payload, indent=2, default=str),
            name="Sanitized HTTP exchange",
            attachment_type=allure.attachment_type.JSON,
        )

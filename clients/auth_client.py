from __future__ import annotations

import allure

from clients.request_wrapper import ApiRequestWrapper
from models.secrets import BearerToken


class AuthClient:
    def __init__(self, api: ApiRequestWrapper) -> None:
        self.api = api

    def sign_in(self, email: str, password: str) -> BearerToken:
        with allure.step("Authenticate the configured QA account"):
            exchange = self.api.send(
                "POST",
                "/api/auth/signin",
                json={"email": email, "password": password},
            )
            assert exchange.status_code == 200, exchange.response_body
            assert isinstance(exchange.response_body, dict)
            token = next(
                (
                    exchange.response_body.get(key)
                    for key in ("token", "access_token", "accessToken")
                    if exchange.response_body.get(key)
                ),
                None,
            )
            assert isinstance(token, str), "Sign-in response has no supported token field"
            return BearerToken(token)

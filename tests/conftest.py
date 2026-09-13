from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import requests

from clients.auth_client import AuthClient
from clients.request_wrapper import ApiRequestWrapper
from clients.devices_client import DevicesClient
from configs.env_config import Settings
from models.account import AuthenticatedAccount, DemoAccount


def pytest_sessionfinish(session, exitstatus) -> None:
    """Copy the human-readable failure categories into each Allure result set."""
    report_dir = session.config.option.allure_report_dir
    if not report_dir:
        return
    source = Path(__file__).parents[1] / "allure" / "categories.json"
    destination = Path(report_dir)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination / "categories.json")


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def api(settings: Settings) -> ApiRequestWrapper:
    session = requests.Session()
    client = ApiRequestWrapper(settings.base_url, settings.timeout_seconds, session)
    yield client
    session.close()


@pytest.fixture(scope="session")
def devices(api: ApiRequestWrapper) -> DevicesClient:
    return DevicesClient(api)


@pytest.fixture(scope="session")
def bearer_token(api: ApiRequestWrapper, settings: Settings) -> str:
    if not settings.email or not settings.password:
        pytest.skip("QA_EMAIL and QA_PASSWORD are required")
    return AuthClient(api).sign_in(settings.email, settings.password)


@pytest.fixture(params=("qa", "admin"), ids=("regular-user", "admin"))
def demo_account(request, settings: Settings) -> DemoAccount:
    credentials = {
        "qa": ("regular user", settings.email, settings.password),
        "admin": ("administrator", settings.admin_email, settings.admin_password),
    }
    role, email, password = credentials[request.param]
    if not email or not password:
        pytest.skip(f"Credentials are required for the {request.param} account")
    return DemoAccount(role=role, email=email, password=password)


@pytest.fixture
def authenticated_account(
    api: ApiRequestWrapper, demo_account: DemoAccount
) -> AuthenticatedAccount:
    token = AuthClient(api).sign_in(demo_account.email, demo_account.password)
    return AuthenticatedAccount(
        role=demo_account.role, email=demo_account.email, token=token
    )


@pytest.fixture(scope="session")
def database(settings: Settings):
    if not settings.database_url:
        pytest.skip("DATABASE_URL is required for database checks")
    client = DatabaseClient(settings.database_url)
    yield client
    client.close()

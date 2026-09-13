from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv(
        "BASE_URL", "https://qa-sample-vitaliirepeev.up.railway.app"
    ).rstrip("/")
    email: str | None = os.getenv("QA_EMAIL")
    password: str | None = field(default=os.getenv("QA_PASSWORD"), repr=False)
    admin_email: str | None = os.getenv("ADMIN_EMAIL")
    admin_password: str | None = field(
        default=os.getenv("ADMIN_PASSWORD"), repr=False
    )
    timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "25"))
    database_url: str | None = os.getenv("DATABASE_URL") or None
    allow_state_changing_tests: bool = _as_bool(
        os.getenv("ALLOW_STATE_CHANGING_TESTS")
    )
    mutable_device_id: str | None = os.getenv("QA_MUTABLE_DEVICE_ID")
    command_version: str = os.getenv("QA_COMMAND_VERSION", "6.4.10")
    up_to_date_device_id: str | None = (
        os.getenv("QA_UP_TO_DATE_DEVICE_ID") or mutable_device_id
    )
    outdated_device_id: str | None = os.getenv("QA_OUTDATED_DEVICE_ID")
    downgrade_command_version: str | None = (
        os.getenv("QA_DOWNGRADE_COMMAND_VERSION") or None
    )
    current_command_version: str | None = (
        os.getenv("QA_CURRENT_COMMAND_VERSION") or None
    )
    upgrade_command_version: str | None = (
        os.getenv("QA_UPGRADE_COMMAND_VERSION") or None
    )
    unknown_device_id: str = os.getenv(
        "QA_UNKNOWN_DEVICE_ID", "DOES-NOT-EXIST"
    )

from __future__ import annotations

import json
import time
from dataclasses import dataclass

import allure
import pytest

from helpers.device_commands import update_core_services_body
from helpers.device_inventory import (
    core_service_versions,
    fetch_all_devices,
    find_device,
    services_not_at_latest,
)
from helpers.retry import retry


VERSION_CASES = (
    pytest.param(
        "downgrade", "downgrade_command_version", False, id="downgrade-no-op"
    ),
    pytest.param(
        "current", "current_command_version", False, id="current-version-no-op"
    ),
    pytest.param("upgrade", "upgrade_command_version", True, id="upgrade-changes"),
)


@dataclass(frozen=True)
class TargetDevice:
    device_id: str
    record_id: int


def _load_target_device(
    devices,
    bearer_token: str,
    configured_device_id: str | None,
    expected_initial_state: str,
) -> TargetDevice:
    if not configured_device_id:
        pytest.skip(
            f"A dedicated {expected_initial_state} device ID is not configured"
        )

    inventory = fetch_all_devices(devices, bearer_token)
    candidate = find_device(inventory, configured_device_id)

    with allure.step(f"Select the dedicated {expected_initial_state} Online device"):
        assert candidate is not None, (
            f"Configured device {configured_device_id} was not returned by the API"
        )
        assert str(candidate.get("presence_status", "")).lower() == "online"
        record_id = candidate.get("id")
        assert isinstance(record_id, int), (
            "The Devices API must provide the numeric record id required by "
            "GET /api/devices/{id}"
        )

    detail = devices.get_device(record_id, bearer_token)
    with allure.step("Verify the device's initial core-services state"):
        assert detail.status_code == 200
        assert isinstance(detail.response_body, dict)
        versions = core_service_versions(detail.response_body)
        outdated_services = services_not_at_latest(versions)
        if expected_initial_state == "up-to-date":
            assert not outdated_services, (
                f"Configured device {configured_device_id} is not up-to-date: "
                f"{sorted(outdated_services)}"
            )
        else:
            assert outdated_services, (
                f"Configured device {configured_device_id} has no service below "
                "its API-reported latest version"
            )
        allure.attach(
            json.dumps(versions, indent=2, sort_keys=True),
            name=f"Initial {expected_initial_state} core-service versions",
            attachment_type=allure.attachment_type.JSON,
        )

    return TargetDevice(device_id=configured_device_id, record_id=record_id)


@pytest.fixture(scope="module")
def up_to_date_target(devices, bearer_token, settings) -> TargetDevice:
    if not settings.allow_state_changing_tests:
        pytest.skip("Set ALLOW_STATE_CHANGING_TESTS=true only with explicit approval")
    return _load_target_device(
        devices,
        bearer_token,
        settings.up_to_date_device_id,
        "up-to-date",
    )


@pytest.fixture(scope="module")
def outdated_target(devices, bearer_token, settings) -> TargetDevice:
    if not settings.allow_state_changing_tests:
        pytest.skip("Set ALLOW_STATE_CHANGING_TESTS=true only with explicit approval")
    return _load_target_device(
        devices,
        bearer_token,
        settings.outdated_device_id,
        "outdated",
    )


def _current_versions(versions: dict[str, dict]) -> dict[str, object]:
    return {
        service_name: service_versions.get("current")
        for service_name, service_versions in versions.items()
    }


def _assert_command_version_outcome(
    devices,
    bearer_token: str,
    target: TargetDevice,
    command_version: str,
    should_change: bool,
) -> None:
    before_detail = devices.get_device(target.record_id, bearer_token)
    with allure.step("Retrieve every core-service version immediately before command"):
        assert before_detail.status_code == 200
        assert isinstance(before_detail.response_body, dict)
        before_versions = core_service_versions(before_detail.response_body)
        allure.attach(
            json.dumps(before_versions, indent=2, sort_keys=True),
            name="All core-service versions before command",
            attachment_type=allure.attachment_type.JSON,
        )

    command = devices.send_command(
        update_core_services_body([target.device_id], command_version),
        bearer_token,
    )
    with allure.step("Verify the command response reports the selected device"):
        assert command.status_code == 200
        assert isinstance(command.response_body, dict)
        assert target.device_id in command.response_body.get("updated", [])

    def retrieve_after_versions(attempt: int) -> dict[str, dict]:
        after_detail = devices.get_device(target.record_id, bearer_token)
        assert after_detail.status_code == 200
        assert isinstance(after_detail.response_body, dict)
        after_versions = core_service_versions(after_detail.response_body)
        missing_services = sorted(set(before_versions) - set(after_versions))
        assert not missing_services, (
            "Core services disappeared after the command: "
            f"{missing_services}"
        )
        allure.attach(
            json.dumps(after_versions, indent=2, sort_keys=True),
            name=f"Core-service versions after command — check {attempt}",
            attachment_type=allure.attachment_type.JSON,
        )
        return after_versions

    if not should_change:
        with allure.step("Confirm versions remain unchanged across three checks"):
            expected_currents = _current_versions(before_versions)
            for attempt in range(1, 4):
                if attempt > 1:
                    time.sleep(3)
                after_versions = retrieve_after_versions(attempt)
                assert _current_versions(after_versions) == expected_currents, (
                    f"{target.device_id} changed after a command expected to be "
                    f"a no-op; command_version={command_version}"
                )
        return

    @retry(attempts=3, wait_seconds=3, exceptions=(AssertionError,))
    def wait_for_a_core_service_version_change() -> None:
        after_versions = retrieve_after_versions(attempt=1)
        changed_services = {
            service_name: {
                "before_current": before_versions[service_name].get("current"),
                "after_current": after_versions[service_name].get("current"),
            }
            for service_name in before_versions
            if after_versions[service_name].get("current")
            != before_versions[service_name].get("current")
        }
        allure.attach(
            json.dumps(changed_services, indent=2, sort_keys=True),
            name="Changed core-service versions",
            attachment_type=allure.attachment_type.JSON,
        )
        assert changed_services, (
            f"Command reported {target.device_id} as updated, but no API-reported "
            "core-service current version changed"
        )

    with allure.step("Retry until an observable core-service version changes"):
        wait_for_a_core_service_version_change()


def _run_version_case(
    devices,
    bearer_token: str,
    settings,
    target: TargetDevice,
    initial_state: str,
    version_case: str,
    setting_name: str,
    should_change: bool,
) -> None:
    command_version = getattr(settings, setting_name)
    if not command_version:
        pytest.skip(f"Configure QA_{setting_name.upper()} for this transition case")

    allure.dynamic.title(
        f"{version_case.title()} command "
        f"{'changes a core-service version' if should_change else 'is a no-op'} "
        f"on an {initial_state} device"
    )
    allure.dynamic.parameter("version_case", version_case)
    allure.dynamic.parameter("command_version", command_version)
    allure.dynamic.parameter("selected_device_id", target.device_id)

    # Current working contract: downgrade and current-version commands are
    # successful no-ops; an upgrade must change at least one API-reported
    # current core-service version. Product/Development should still confirm it.
    _assert_command_version_outcome(
        devices, bearer_token, target, command_version, should_change
    )


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices Command API")
@allure.sub_suite("Version transitions")
@allure.feature("Devices Command API")
@allure.story("Up-to-date device")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("version_case,setting_name,should_change", VERSION_CASES)
@pytest.mark.api
@pytest.mark.state_changing
@pytest.mark.serial
@pytest.mark.known_defect
def test_update_core_services_versions_for_up_to_date_device(
    devices,
    bearer_token,
    settings,
    up_to_date_target,
    version_case,
    setting_name,
    should_change,
):
    _run_version_case(
        devices,
        bearer_token,
        settings,
        up_to_date_target,
        "up-to-date",
        version_case,
        setting_name,
        should_change,
    )


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices Command API")
@allure.sub_suite("Version transitions")
@allure.feature("Devices Command API")
@allure.story("Outdated device")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("version_case,setting_name,should_change", VERSION_CASES)
@pytest.mark.api
@pytest.mark.state_changing
@pytest.mark.serial
@pytest.mark.known_defect
def test_update_core_services_versions_for_outdated_device(
    devices,
    bearer_token,
    settings,
    outdated_target,
    version_case,
    setting_name,
    should_change,
):
    _run_version_case(
        devices,
        bearer_token,
        settings,
        outdated_target,
        "outdated",
        version_case,
        setting_name,
        should_change,
    )

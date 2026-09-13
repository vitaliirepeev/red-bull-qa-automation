import allure
import pytest

from helpers.device_commands import update_core_services_body
from helpers.device_inventory import fetch_all_devices, find_device


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices Command API")
@allure.sub_suite("State consistency")
@allure.feature("Devices Command API")
@allure.story("Core-services update")
@allure.title("Update the selected device to the requested core-services version")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.state_changing
@pytest.mark.known_defect
def test_update_core_services_changes_selected_device_state(
    devices, bearer_token, settings
):
    if not settings.allow_state_changing_tests:
        pytest.skip("Set ALLOW_STATE_CHANGING_TESTS=true only with explicit approval")

    before_inventory = fetch_all_devices(devices, bearer_token)
    candidate = next(
        (
            device
            for device in before_inventory
            if str(device.get("presence_status", "")).lower() == "online"
            and settings.command_version
            not in str(
                (device.get("core_services_versions") or {})
                .get("adsync_version", {})
                .get("current", "")
            )
            and (device.get("core_services_versions") or {})
            .get("adsync_version", {})
            .get("current")
        ),
        None,
    )

    with allure.step("Select an Online device below the requested adsync version"):
        assert candidate is not None, (
            "No Online device with an older observable adsync version is available"
        )
        device_id = candidate["device_id"]
        before_version = candidate["core_services_versions"]["adsync_version"][
            "current"
        ]
        allure.dynamic.parameter("selected_device_id", device_id)
        allure.attach(
            str(before_version),
            name="Adsync version before command",
            attachment_type=allure.attachment_type.TEXT,
        )

    command = devices.send_command(
        update_core_services_body([device_id], settings.command_version),
        bearer_token,
    )

    with allure.step("Verify the command response reports the selected device"):
        assert command.status_code == 200
        assert isinstance(command.response_body, dict)
        assert device_id in command.response_body.get("updated", [])

    after_inventory = fetch_all_devices(devices, bearer_token)
    after_device = find_device(after_inventory, device_id)

    with allure.step("Compare the device state before and after the command"):
        assert after_device is not None
        after_version = after_device["core_services_versions"]["adsync_version"][
            "current"
        ]
        allure.attach(
            str(after_version),
            name="Adsync version after command",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert after_version != before_version, (
            f"Command reported {device_id} as updated, but adsync version "
            f"remained {after_version!r}"
        )
        assert settings.command_version in after_version, (
            f"Expected adsync version containing {settings.command_version!r}, "
            f"but received {after_version!r}"
        )

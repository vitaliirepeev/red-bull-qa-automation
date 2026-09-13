import allure
import pytest

from helpers.device_commands import accounted_targets, update_core_services_body


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices Command API")
@allure.sub_suite("Target validation")
@allure.feature("Devices Command API")
@allure.story("Target reconciliation")
@allure.title("Return an explicit outcome for an unknown device")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
@pytest.mark.contract
@pytest.mark.known_defect
def test_unknown_target_is_explicitly_accounted_for(
    devices, bearer_token, settings
):
    target = settings.unknown_device_id
    exchange = devices.send_command(
        update_core_services_body([target], settings.command_version),
        bearer_token,
    )

    with allure.step("Verify that every requested target has an explicit outcome"):
        if 400 <= exchange.status_code < 500:
            assert target in str(exchange.response_body)
        else:
            assert exchange.status_code == 200
            assert target in accounted_targets(exchange.response_body)


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices Command API")
@allure.sub_suite("Request validation")
@allure.feature("Devices Command API")
@allure.story("Request validation")
@allure.title("Reject a missing command version before dispatch")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
@pytest.mark.contract
@pytest.mark.state_changing
@pytest.mark.known_defect
def test_missing_command_version_is_rejected_before_dispatch(
    devices, bearer_token, settings
):
    if not settings.allow_state_changing_tests or not settings.mutable_device_id:
        pytest.skip("Requires explicit approval and QA_MUTABLE_DEVICE_ID")

    body = {
        "devices": [settings.mutable_device_id],
        "command_name": "update_core_services",
        "params": {},
    }
    exchange = devices.send_command(body, bearer_token)

    with allure.step("Verify validation fails before command dispatch"):
        assert 400 <= exchange.status_code < 500

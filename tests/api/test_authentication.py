import allure
import pytest


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices API")
@allure.sub_suite("Authentication and authorization")
@allure.feature("Devices API")
@allure.story("Authentication")
@allure.title("Reject Devices access without authentication")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_devices_rejects_missing_authorization(devices):
    exchange = devices.list_devices()

    with allure.step("Verify that missing authorization is rejected"):
        assert exchange.status_code == 401
        assert exchange.elapsed_ms < 25_000
        assert exchange.sent_at_utc

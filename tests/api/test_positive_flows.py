import allure
import pytest

from clients.auth_client import AuthClient


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Authentication API")
@allure.sub_suite("Positive access")
@allure.feature("Authentication")
@allure.story("Demo accounts")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_demo_account_can_sign_in(api, demo_account):
    allure.dynamic.title(f"Sign in successfully as {demo_account.role}")
    token = AuthClient(api).sign_in(demo_account.email, demo_account.password)

    with allure.step(f"Verify the {demo_account.role} account receives a token"):
        assert isinstance(token, str)
        assert token


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices API")
@allure.sub_suite("Role access")
@allure.feature("Devices API")
@allure.story("Role access")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.api
def test_demo_account_can_list_devices(devices, authenticated_account):
    allure.dynamic.title(
        f"Allow {authenticated_account.role} to access the Devices list"
    )
    exchange = devices.list_devices(authenticated_account.token)

    with allure.step(
        f"Verify the {authenticated_account.role} account can access Devices"
    ):
        assert exchange.status_code == 200


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices API")
@allure.sub_suite("Response contract")
@allure.feature("Devices API")
@allure.story("Response contract")
@allure.title("Return a consistent Devices page structure")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_device_list_has_consistent_page_shape(devices, bearer_token):
    exchange = devices.list_devices(bearer_token)

    with allure.step("Verify successful page metadata and collection shape"):
        assert exchange.status_code == 200
        assert isinstance(exchange.response_body, dict)
        assert set(("items", "page", "pageSize", "total")) <= set(
            exchange.response_body
        )
        assert isinstance(exchange.response_body["items"], list)
        assert exchange.response_body["page"] == 1
        assert exchange.response_body["pageSize"] == 15
        assert exchange.response_body["total"] >= len(
            exchange.response_body["items"]
        )


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices API")
@allure.sub_suite("Response contract")
@allure.feature("Devices API")
@allure.story("Response contract")
@allure.title("Expose required identity and operational fields for each device")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
def test_device_items_expose_required_operational_fields(devices, bearer_token):
    exchange = devices.list_devices(bearer_token)

    with allure.step("Verify each returned device has core identity and state fields"):
        assert exchange.status_code == 200
        items = exchange.response_body["items"]
        assert items, "The QA data set should contain at least one device"
        required = {
            "id",
            "device_id",
            "name",
            "presence_status",
            "core_services_status",
            "orientation",
        }
        for device in items:
            assert required <= set(device)
            assert device["id"] is not None
            assert isinstance(device["device_id"], str) and device["device_id"]


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Devices API")
@allure.sub_suite("Pagination")
@allure.feature("Devices API")
@allure.story("Pagination")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.api
@pytest.mark.parametrize("page", (1, 2), ids=("first-page", "second-page"))
def test_valid_device_page_is_returned(devices, bearer_token, page):
    allure.dynamic.title(f"Return requested Devices page {page}")
    exchange = devices.list_devices(bearer_token, page=page, page_size=15)

    with allure.step(f"Verify requested page {page} is returned consistently"):
        assert exchange.status_code == 200
        assert exchange.response_body["page"] == page
        assert exchange.response_body["pageSize"] == 15
        assert 0 < len(exchange.response_body["items"]) <= 15

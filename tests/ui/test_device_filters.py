import allure
import pytest
from playwright.sync_api import Page

from pages.devices_page import DevicesPage
from pages.login_page import LoginPage


@allure.parent_suite("Digital Poster Frontend")
@allure.suite("Devices Dashboard")
@allure.sub_suite("Filters")
@allure.feature("Device filters")
@allure.story("Filter devices by status")
@allure.title("Status filter shows only Online and Offline devices")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_status_filter_shows_only_online_and_offline_devices(
    page: Page, settings
):
    if not settings.email or not settings.password:
        pytest.skip("QA_EMAIL and QA_PASSWORD are required")

    login = LoginPage(page, settings.base_url)
    devices = DevicesPage(page)

    login.open()
    login.sign_in(settings.email, settings.password)
    devices.verify_loaded()

    for status in ("Online", "Offline"):
        devices.verify_status_filter(status)

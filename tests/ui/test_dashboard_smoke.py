import allure
import pytest
from playwright.sync_api import Page

from pages.devices_page import DevicesPage
from pages.login_page import LoginPage


@allure.parent_suite("Digital Poster Frontend")
@allure.suite("Authentication and Devices")
@allure.sub_suite("Smoke")
@allure.feature("Frontend smoke")
@allure.story("Successful sign-in")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.ui
def test_demo_account_opens_devices_dashboard(page: Page, settings, demo_account):
    allure.dynamic.title(
        f"Open the Devices dashboard as {demo_account.role}"
    )
    login = LoginPage(page, settings.base_url)
    devices = DevicesPage(page)

    login.open()
    login.sign_in(demo_account.email, demo_account.password)
    devices.verify_loaded()

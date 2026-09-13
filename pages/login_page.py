from __future__ import annotations

import allure
from playwright.sync_api import Page

from pages.login_locators import LoginLocators


class LoginPage:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url
        self.email_input = page.get_by_label(LoginLocators.EMAIL).or_(
            page.get_by_placeholder(LoginLocators.EMAIL_PLACEHOLDER)
        ).first
        self.password_input = page.get_by_label(LoginLocators.PASSWORD).or_(
            page.locator('input[type="password"]')
        ).first
        self.sign_in_button = page.get_by_role(
            "button", name=LoginLocators.SIGN_IN
        ).first

    def open(self) -> None:
        with allure.step("Open the Digital Poster sign-in page"):
            self.page.goto(self.base_url)

    def sign_in(self, email: str, password: str) -> None:
        with allure.step("Sign in through the user interface"):
            self.email_input.fill(email)
            self.password_input.fill(password)
            self.sign_in_button.click()

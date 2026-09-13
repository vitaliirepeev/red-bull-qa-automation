from __future__ import annotations

import re

import allure
from playwright.sync_api import Page, expect

from pages.devices_locators import DevicesLocators


class DevicesPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.dashboard_title = page.get_by_role(
            "heading", name=DevicesLocators.DASHBOARD_TITLE
        )
        self.devices_heading = page.get_by_role(
            "heading", name=DevicesLocators.DEVICES_HEADING
        )
        self.devices_table = page.get_by_role("table")
        self.device_rows = self.devices_table.locator(DevicesLocators.TABLE_ROWS)
        self.status_filter = page.get_by_test_id(
            DevicesLocators.STATUS_FILTER_TEST_ID
        )
        self.status_cells = self.devices_table.locator(
            DevicesLocators.STATUS_CELLS
        )

    def verify_loaded(self) -> None:
        with allure.step("Verify the Devices dashboard title and table"):
            expect(self.dashboard_title).to_be_visible()
            expect(self.devices_heading).to_be_visible()
            expect(self.devices_table).to_be_visible()
            expect(self.device_rows.first).to_be_visible()

    def verify_status_filter(self, status: str) -> None:
        with allure.step(f"Filter the Devices table by {status} status"):
            with self.page.expect_response(
                lambda response: "/api/devices" in response.url
                and status.lower() in response.url.lower()
                and response.status == 200
            ):
                self.status_filter.select_option(label=status)

        with allure.step(f"Verify every displayed device is {status}"):
            expect(self.status_filter).to_have_value(status.lower())
            expect(self.status_cells.first).to_be_visible()
            expect(self.status_cells.first).to_have_text(
                re.compile(rf"^{re.escape(status)}$", re.IGNORECASE)
            )
            displayed_statuses = [
                value.strip() for value in self.status_cells.all_text_contents()
            ]
            allure.attach(
                "\n".join(displayed_statuses),
                name=f"Displayed statuses after selecting {status}",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert displayed_statuses, f"No devices were shown for {status}"
            assert all(
                value.casefold() == status.casefold()
                for value in displayed_statuses
            ), (
                f"Expected only {status} devices, got {displayed_statuses}"
            )

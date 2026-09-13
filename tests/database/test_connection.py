import allure
import pytest


@allure.parent_suite("Digital Poster Backend")
@allure.suite("Test Infrastructure")
@allure.sub_suite("Database")
@allure.feature("Test infrastructure")
@allure.story("Database connectivity")
@allure.title("Connect to the QA database with read-only access")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.database
def test_read_only_database_connection(database):
    row = database.fetch_one("SELECT 1 AS healthy")

    assert row == {"healthy": 1}

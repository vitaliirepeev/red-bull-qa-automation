# Tiny Python API automation example

This is a small, runnable framework example—not a full production suite. It talks to the live QA service with no mocks of application code.

## Why this shape

```text
pytest -m api
       │
       ▼
tests/ ──► helpers/ ──► clients/ ──► live QA API
                 │            │
                 │            └──► sanitized timed exchanges ──► Allure
                 └──► database/ (optional read-only SQLAlchemy checks)
```

- `clients/request_wrapper.py` contains the custom `ApiRequestWrapper`; endpoint clients call its `send()` method instead of calling `requests` directly.
- `helpers/` contains reusable business-shaped payloads and assertions.
- `tests/database/` is deliberately read-only and schema-neutral until the real schema is reviewed.
- `configs/` derives the environment from variables.
- `tests/` stays short and expresses behavior.
- Every HTTP exchange is an `allure.step` and records UTC send/receive timestamps, method, URL, sanitized body, status, response, and elapsed milliseconds in an attached JSON document.
- `ApiRequestWrapper.exchange_history` also retains in-process exchanges for debugging or later assertions.
- Allure uses human-readable titles and the hierarchy `Digital Poster Backend → API area → test category`, with Feature/Story and severity labels retained for alternate report views.
- `allure/categories.json` classifies failed results as known product defects, authentication/authorization failures, API contract/schema failures, or environment/precondition problems. The pytest hook copies it into every generated Allure result directory.

## Run

From the repository root:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
pytest -m api --alluredir=allure-results
```

When using the project virtual environment without activating it, use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe -m pytest -m "api and not state_changing" -q --alluredir=allure-results
```

Add approved QA credentials to `.env` to run authenticated examples. Do not commit that file.

In CI, provide `QA_EMAIL`, `QA_PASSWORD`, and any admin credentials through the platform's masked/protected secret store. Do not place credential values in repository variables, workflow YAML, command output, or Allure attachments.

`allure-pytest` from `requirements.txt` is only the pytest adapter that creates `allure-results`. The `allure` command is a separate Java-based Allure Report CLI and is not installed by pip. After installing the Allure CLI and adding its `bin` directory to `PATH`, view the report with:

```powershell
allure serve allure-results
```

On Windows, follow the official installation guide: <https://allurereport.org/docs/v2/install-for-windows/>. Java 8 or newer and `JAVA_HOME` are required. Do not run `pip install allure`; no such Python package provides the report CLI.

Useful small runs:

```powershell
.\.venv\Scripts\python.exe .\scripts\run_api_tests.py
pytest -n 5 -m "api and not state_changing" --alluredir=allure-results
pytest -n 5 -m "ui and not state_changing" --alluredir=allure-results-ui
pytest -m contract --alluredir=allure-results
pytest -m database --alluredir=allure-results
pytest -m known_defect --alluredir=allure-results
```

The single `run_api_tests.py` command runs the complete API suite in two phases: tests without `pytest.mark.serial` first use five workers, then tests marked `pytest.mark.serial` use one worker. Both phases write into the same Allure results directory, and the serial phase still runs when the parallel phase finds a failure. The script returns a failing exit code when either phase fails. Running it through the virtual-environment Python avoids Windows PowerShell execution-policy restrictions.

`pytest-xdist` provides `-n 5`, which distributes parallel-safe tests across five worker processes. To run only the ordered tests manually, use:

```powershell
pytest -n 0 -m "api and serial" --alluredir=allure-results-state
```

The missing-authorization test is read-only. Known regressions use the `known_defect` marker but remain ordinary failing tests, so current QA defects make the run visibly red. The missing-version and command-state examples are skipped unless state-changing tests are explicitly enabled.

The command-state coverage is split into two parameterized tests: one starts with a dedicated up-to-date Online device and one with a dedicated outdated Online device. Each test runs the cases in downgrade, current-version, then upgrade order. Immediately before every command, it retrieves `GET /api/devices/{id}` and discovers the complete `core_services_versions` map instead of hard-coding service names. The current working expectation is that downgrade and current-version commands leave every reported `current` version unchanged across three checks, three seconds apart. The upgrade case retries up to three times, waiting three seconds between attempts, and passes when at least one reported `current` version differs from its immediate before-command value. It does not assume that the resulting versions equal the API's `latest` values.

Configure `QA_UP_TO_DATE_DEVICE_ID`, `QA_OUTDATED_DEVICE_ID`, `QA_DOWNGRADE_COMMAND_VERSION`, `QA_CURRENT_COMMAND_VERSION`, and `QA_UPGRADE_COMMAND_VERSION` with dedicated, approved QA fixtures and versions. The cases carry the `serial` marker and must not run concurrently because their state transitions are ordered. Restore the fixtures before rerunning a complete sequence. Product/Development should confirm the working no-op contract for downgrade and current-version commands. These tests change QA state and must run only with explicit approval.

Positive coverage also parameterizes the regular QA and admin demo accounts. It verifies successful authentication and protected Devices access for both roles, then checks the list response shape, required device fields, and valid first/second-page behavior. Passwords and tokens are hidden from object representations and Allure attachments.

## Minimal frontend smoke layer

The frontend example follows Playwright's Page Object Model without adding a large framework:

```text
pages/
├── login_locators.py       visible labels/placeholders and roles
├── login_page.py           open and sign-in actions
├── devices_locators.py     dashboard/table selectors
└── devices_page.py         dashboard assertions

tests/ui/
├── test_dashboard_smoke.py user-visible login scenario
└── test_device_filters.py  status-filter regression scenario
```

Tests use page objects; page objects use the separate locator files. This keeps selectors out of test scenarios while preserving readable business actions. The login scenario is parameterized for the regular and administrator accounts and verifies successful sign-in, the `Digital Poster Dashboard` title, the Devices heading, and at least one visible table row. The focused ticket regression signs in as the regular QA user, selects Online and Offline in the Status filter, waits for each matching Devices API response, and verifies that every rendered result row has the selected status.

Run headlessly:

```powershell
.\.venv\Scripts\python.exe -m pytest -m ui -q --browser chromium --alluredir=allure-results-ui --clean-alluredir
```

Run with the browser visible:

```powershell
.\.venv\Scripts\python.exe -m pytest -m ui -q --browser chromium --headed --slowmo 300
```

The Email text in the current UI is not programmatically associated with its input. The page object therefore prefers the accessible label but uses the visible `you@example.com` placeholder as a fallback. That markup detail is kept in the locator layer rather than leaking into the test.

## Where to expand next

1. Replace generic dictionaries with Pydantic request/response models after the API contract is approved.
2. Add domain-specific SQLAlchemy models only after inspecting the real schema; keep DB assertions read-only where possible.
3. Add command lifecycle helpers once a disposable device, observable before/after state, and cleanup path exist.
4. Add response-schema validation and per-device batch-result assertions after Product/Development answers the open questions.
5. Keep stand-global or ordered state-changing tests marked `serial` and outside distributed runs.
6. Add CI and Allure history only after this local example is stable.
7. Expand the small Playwright smoke layer only after backend behavior is reliable and stable enough to support broader end-to-end coverage.

## Intentional omissions

- No Kafka or Kubernetes clients: the supplied system does not expose enough information to implement them honestly.
- No ORM device table: inventing a production schema would make the example misleading.
- No automatic mutation or cleanup: the current environment has no approved mutable fixture.
- No large base-class hierarchy: introduce domain bases only when repeated setup/assertions justify them.


.\.venv\Scripts\python.exe -m pytest -n 5 -m "api and not state_changing" -q --alluredir=allure-results --clean-alluredir
.\.venv\Scripts\python.exe -m pytest -n 5 -m ui -q --browser chromium --alluredir=allure-results --clean-alluredir
.\.venv\Scripts\python.exe -m pytest -m ui -q --browser chromium --headed --slowmo 300 --alluredir=allure-results --clean-alluredir
allure serve

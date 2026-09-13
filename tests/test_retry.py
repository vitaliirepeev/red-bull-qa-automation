from helpers import retry as retry_module
from helpers.retry import retry


def test_retry_makes_three_attempts_with_three_second_waits(monkeypatch):
    calls = 0
    waits: list[float] = []

    monkeypatch.setattr(retry_module.time, "sleep", waits.append)

    @retry(attempts=3, wait_seconds=3)
    def eventually_succeeds() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise AssertionError("state has not converged")
        return "updated"

    assert eventually_succeeds() == "updated"
    assert calls == 3
    assert waits == [3, 3]

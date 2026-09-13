from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import allure


P = ParamSpec("P")
R = TypeVar("R")


def retry(
    *,
    attempts: int,
    wait_seconds: float,
    exceptions: tuple[type[Exception], ...] = (AssertionError,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry a verification after selected exceptions.

    ``attempts`` includes the initial call. A wait occurs only when another
    attempt remains.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if wait_seconds < 0:
        raise ValueError("wait_seconds cannot be negative")

    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, attempts + 1):
                try:
                    with allure.step(
                        f"Verification attempt {attempt} of {attempts}"
                    ):
                        return function(*args, **kwargs)
                except exceptions:
                    if attempt == attempts:
                        raise
                    with allure.step(
                        f"Wait {wait_seconds:g} seconds before the next attempt"
                    ):
                        time.sleep(wait_seconds)

            raise RuntimeError("Retry loop completed without returning")

        return wrapped

    return decorator

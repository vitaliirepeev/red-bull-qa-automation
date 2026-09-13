from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApiExchange:
    method: str
    url: str
    sent_at_utc: str
    received_at_utc: str
    request_params: Any
    request_body: Any
    status_code: int
    elapsed_ms: float
    response_body: Any

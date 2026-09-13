from dataclasses import dataclass, field


@dataclass(frozen=True)
class DemoAccount:
    role: str
    email: str
    password: str = field(repr=False)


@dataclass(frozen=True)
class AuthenticatedAccount:
    role: str
    email: str
    token: str = field(repr=False)

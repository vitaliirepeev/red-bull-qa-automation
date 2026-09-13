class BearerToken(str):
    """A string token whose pytest/debug representation never reveals its value."""

    def __repr__(self) -> str:
        return "<redacted bearer token>"

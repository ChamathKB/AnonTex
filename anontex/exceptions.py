class RedisConnectionError(Exception):
    """Raised when there's an issue connecting to Redis."""

    pass


class RequestIDError(Exception):
    """Raised when there's an issue generating a request ID."""

    pass

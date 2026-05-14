"""Official Python client for the twtapi.io HTTP API.

Quickstart:

    from twtapi import TwtAPI

    client = TwtAPI(api_key="tw_...")
    user = client.users.get("elonmusk")
    print(user["screen_name"], user["followers"])

Get an API key at https://twtapi.io/dashboard.
Full reference at https://twtapi.io/docs.
"""

from twtapi.async_client import TwtAPIAsync
from twtapi.client import TwtAPI
from twtapi.errors import (
    AuthenticationError,
    BadRequestError,
    BillingError,
    DuplicateTweetError,
    InternalError,
    NetworkError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ServiceUnavailableError,
    TimeoutError,
    TweetTooLongError,
    TwtAPIError,
    UpstreamError,
    ValidationError,
)
from twtapi.rate_limit import RateLimit

__all__ = [
    # Clients
    "TwtAPI",
    "TwtAPIAsync",
    # Exception base
    "TwtAPIError",
    # Per-status exceptions
    "BadRequestError",
    "AuthenticationError",
    "BillingError",
    "PermissionError",
    "NotFoundError",
    "TimeoutError",
    "ValidationError",
    "DuplicateTweetError",
    "TweetTooLongError",
    "RateLimitError",
    "InternalError",
    "UpstreamError",
    "ServiceUnavailableError",
    "NetworkError",
    # Rate-limit snapshot
    "RateLimit",
]

__version__ = "0.1.0"

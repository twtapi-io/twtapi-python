"""Typed exception hierarchy for the twtapi SDK.

Every error from the API surfaces as a `TwtAPIError` subclass carrying the
HTTP status, the server's `error` code, the human `message`, and the raw
response body. Specific subclasses are raised for each documented status:

    400 BadRequestError    402 BillingError      403 PermissionError
    401 AuthenticationError                      404 NotFoundError
    408 TimeoutError       422 ValidationError   429 RateLimitError
    500 InternalError      502 UpstreamError     503 ServiceUnavailableError

Catch `TwtAPIError` to handle anything from this SDK; catch a subclass to
react to a specific failure mode.
"""

from __future__ import annotations

from typing import Any


class TwtAPIError(Exception):
    """Base class for every error raised by the SDK."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        error: str | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.error = error
        self.body = body

    def __repr__(self) -> str:
        return f"{type(self).__name__}(status={self.status}, error={self.error!r})"


class BadRequestError(TwtAPIError):
    """400 — your request was malformed (missing param, wrong type, bad JSON)."""


class AuthenticationError(TwtAPIError):
    """401 — `X-API-Key` is missing or invalid."""


class BillingError(TwtAPIError):
    """402 — your plan does not cover this endpoint, or billing is past due."""


class PermissionError(TwtAPIError):  # noqa: A001 — users always import from twtapi
    """403 — `engagement_cookies_required`, `account_not_activated`, etc."""


class NotFoundError(TwtAPIError):
    """404 — the target resource does not exist or is not visible."""


class TimeoutError(TwtAPIError):  # noqa: A001 — domain-specific shadow of builtin
    """408 — the upstream did not respond in time. Safe to retry."""


class ValidationError(TwtAPIError):
    """422 — the upstream rejected the request as semantically invalid."""


class DuplicateTweetError(ValidationError):
    """422 with `duplicate_tweet` or `tweet_silently_dropped_likely_duplicate`."""


class TweetTooLongError(ValidationError):
    """422 with `tweet_too_long`."""


class RateLimitError(TwtAPIError):
    """429 — rate-limited. Inspect `retry_after` (seconds) and `scope` (`plan` / `account`)."""

    def __init__(
        self,
        *args: Any,
        retry_after: float | None = None,
        scope: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after
        self.scope = scope


class InternalError(TwtAPIError):
    """500 — unexpected server-side failure. Safe to retry with backoff."""


class UpstreamError(TwtAPIError):
    """502 — upstream gateway error. Safe to retry with backoff."""


class ServiceUnavailableError(TwtAPIError):
    """503 — planned or unplanned outage."""


class NetworkError(TwtAPIError):
    """Connectivity failure (DNS, TCP, TLS, read timeout) before a response was received."""


_REASON_TO_EXCEPTION: dict[str, type[TwtAPIError]] = {
    "duplicate_tweet": DuplicateTweetError,
    "tweet_silently_dropped_likely_duplicate": DuplicateTweetError,
    "tweet_too_long": TweetTooLongError,
}

_STATUS_TO_EXCEPTION: dict[int, type[TwtAPIError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: BillingError,
    403: PermissionError,
    404: NotFoundError,
    408: TimeoutError,
    500: InternalError,
    502: UpstreamError,
    503: ServiceUnavailableError,
}


def from_response(
    *,
    status: int,
    body: Any,
    retry_after_header: float | None = None,
) -> TwtAPIError:
    """Build the right exception subclass from an HTTP status + JSON body.

    The server returns `{"error": "<reason>", "message": "<text>", ...}` on
    failure. We map status → class, then refine 422s by `error` reason.
    `retry_after_header` is the parsed `Retry-After` HTTP header value, used
    as a fallback when the JSON body omits `retry_after`.
    """
    if not isinstance(body, dict):
        body = {}

    reason = body.get("error")
    message = body.get("message") or _fallback_message(status, reason)

    if status == 429:
        retry_after = body.get("retry_after")
        if retry_after is None:
            retry_after = retry_after_header
        return RateLimitError(
            message,
            status=status,
            error=reason,
            body=body,
            retry_after=_coerce_float(retry_after),
            scope=body.get("scope"),
        )

    if status == 422:
        cls = _REASON_TO_EXCEPTION.get(reason or "", ValidationError)
        return cls(message, status=status, error=reason, body=body)

    cls = _STATUS_TO_EXCEPTION.get(status, TwtAPIError)
    return cls(message, status=status, error=reason, body=body)


def _fallback_message(status: int, reason: str | None) -> str:
    if reason:
        return f"HTTP {status}: {reason}"
    return f"HTTP {status}"


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

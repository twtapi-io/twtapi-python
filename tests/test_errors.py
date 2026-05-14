"""Error mapping: status → typed exception."""

from __future__ import annotations

import httpx
import pytest
import respx

from twtapi import (
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
    TwtAPI,
    TwtAPIError,
    UpstreamError,
    ValidationError,
)


@pytest.mark.parametrize(
    ("status", "reason", "exc_type"),
    [
        (400, "invalid_request", BadRequestError),
        (401, "unauthorized", AuthenticationError),
        (402, "billing_past_due", BillingError),
        (403, "engagement_cookies_required", PermissionError),
        (404, "not_found", NotFoundError),
        (408, "upstream_timeout", TimeoutError),
        (422, "some_random_validation", ValidationError),
        (422, "duplicate_tweet", DuplicateTweetError),
        (422, "tweet_silently_dropped_likely_duplicate", DuplicateTweetError),
        (422, "tweet_too_long", TweetTooLongError),
        (500, "internal", InternalError),
        (502, "upstream_unavailable", UpstreamError),
        (503, "outage", ServiceUnavailableError),
    ],
)
@respx.mock
def test_status_maps_to_exception(
    client: TwtAPI, status: int, reason: str, exc_type: type[TwtAPIError]
) -> None:
    respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(status, json={"error": reason, "message": "boom"})
    )
    with pytest.raises(exc_type) as info:
        client.users.get("anyone")
    assert info.value.status == status
    assert info.value.error == reason
    assert isinstance(info.value, TwtAPIError)


@respx.mock
def test_rate_limit_carries_retry_after_and_scope(client: TwtAPI) -> None:
    respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(
            429,
            json={
                "error": "rate_limited",
                "message": "Rate limit exceeded",
                "retry_after": 12,
                "scope": "plan",
            },
        )
    )
    with pytest.raises(RateLimitError) as info:
        client.users.get("anyone")
    assert info.value.retry_after == 12.0
    assert info.value.scope == "plan"


@respx.mock
def test_rate_limit_falls_back_to_retry_after_header(client: TwtAPI) -> None:
    respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(
            429,
            headers={"Retry-After": "7"},
            json={"error": "rate_limited", "message": "throttled"},
        )
    )
    with pytest.raises(RateLimitError) as info:
        client.users.get("anyone")
    assert info.value.retry_after == 7.0


@respx.mock
def test_unknown_status_is_base_twtapi_error(client: TwtAPI) -> None:
    respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(418, json={"error": "i_am_a_teapot", "message": "no"})
    )
    with pytest.raises(TwtAPIError) as info:
        client.users.get("anyone")
    assert type(info.value) is TwtAPIError
    assert info.value.status == 418
    assert info.value.error == "i_am_a_teapot"


@respx.mock
def test_network_failure_becomes_network_error(client: TwtAPI) -> None:
    respx.get("https://api.twtapi.io/user").mock(
        side_effect=httpx.ConnectError("dns lookup failed")
    )
    with pytest.raises(NetworkError):
        client.users.get("anyone")

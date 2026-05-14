"""Transport-level invariants: headers, retry policy, rate-limit tracking."""

from __future__ import annotations

import httpx
import pytest
import respx

from twtapi import (
    InternalError,
    RateLimit,
    RateLimitError,
    ServiceUnavailableError,
    TwtAPI,
    UpstreamError,
)


@respx.mock
def test_api_key_header_on_every_request(client: TwtAPI) -> None:
    route = respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(200, json={"screen_name": "x"})
    )
    client.users.get("elonmusk")
    assert route.calls.last.request.headers["X-API-Key"] == "tw_test_key"


@respx.mock
def test_proxy_header_when_configured() -> None:
    client = TwtAPI(api_key="tw_test_key", proxy="http://p:1234", retries=0)
    route = respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(200, json={"screen_name": "x"})
    )
    client.users.get("elonmusk")
    assert route.calls.last.request.headers["X-Proxy"] == "http://p:1234"


@respx.mock
def test_rate_limit_snapshot_captured(client: TwtAPI) -> None:
    respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(
            200,
            headers={
                "X-RateLimit-Limit": "30",
                "X-RateLimit-Remaining": "29",
                "X-RateLimit-Reset": "1715703012",
            },
            json={"screen_name": "x"},
        )
    )
    client.users.get("elonmusk")
    snapshot = client.last_rate_limit
    assert snapshot == RateLimit(limit=30, remaining=29, reset=1715703012)


@respx.mock
def test_rate_limit_snapshot_tolerates_missing_headers(client: TwtAPI) -> None:
    respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(
            200,
            headers={"X-RateLimit-Remaining": "0"},
            json={"screen_name": "x"},
        )
    )
    client.users.get("elonmusk")
    assert client.last_rate_limit == RateLimit(limit=None, remaining=0, reset=None)


@respx.mock
def test_idempotent_get_retries_on_503() -> None:
    client = TwtAPI(api_key="tw_test_key", retries=2)
    route = respx.get("https://api.twtapi.io/user").mock(
        side_effect=[
            httpx.Response(503, json={"error": "outage", "message": "down"}),
            httpx.Response(200, json={"screen_name": "x"}),
        ]
    )
    client.users.get("elonmusk")
    assert route.call_count == 2


@respx.mock
def test_post_tweet_never_retries_on_5xx() -> None:
    """POST /tweet creates new content — must never retry on 5xx (double-post risk)."""
    client = TwtAPI(api_key="tw_test_key", auth_token="a", ct0="b", retries=3)
    route = respx.post("https://api.twtapi.io/tweet").mock(
        return_value=httpx.Response(502, json={"error": "upstream_unavailable", "message": "x"})
    )
    with pytest.raises(UpstreamError):
        client.tweets.create("hello")
    assert route.call_count == 1


@respx.mock
def test_post_comment_never_retries_on_5xx() -> None:
    client = TwtAPI(api_key="tw_test_key", auth_token="a", ct0="b", retries=3)
    route = respx.post("https://api.twtapi.io/comment").mock(
        return_value=httpx.Response(500, json={"error": "internal", "message": "x"})
    )
    with pytest.raises(InternalError):
        client.tweets.comment("123", "hi")
    assert route.call_count == 1


@respx.mock
def test_post_like_retries_on_5xx() -> None:
    """POST /like is idempotent — safe to retry on 5xx."""
    client = TwtAPI(api_key="tw_test_key", auth_token="a", ct0="b", retries=2)
    route = respx.post("https://api.twtapi.io/like").mock(
        side_effect=[
            httpx.Response(500, json={"error": "internal", "message": "x"}),
            httpx.Response(200, json={"status": "ok"}),
        ]
    )
    client.tweets.like("123")
    assert route.call_count == 2


@respx.mock
def test_retries_zero_disables_retry() -> None:
    client = TwtAPI(api_key="tw_test_key", retries=0)
    route = respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(503, json={"error": "outage", "message": "down"})
    )
    with pytest.raises(ServiceUnavailableError):
        client.users.get("elonmusk")
    assert route.call_count == 1


@respx.mock
def test_429_retries_once_then_raises() -> None:
    client = TwtAPI(api_key="tw_test_key", retries=2)
    route = respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(
            429,
            json={"error": "rate_limited", "message": "x", "retry_after": 0.01, "scope": "plan"},
        )
    )
    with pytest.raises(RateLimitError):
        client.users.get("elonmusk")
    assert route.call_count >= 2


@respx.mock
def test_drops_none_params(client: TwtAPI) -> None:
    """Optional params with None values must not show up in the query string."""
    route = respx.get("https://api.twtapi.io/followers").mock(
        return_value=httpx.Response(200, json={"count": 0, "followers": []})
    )
    client.users.followers("44196397", count=None, cursor=None)
    sent_url = str(route.calls.last.request.url)
    assert "count" not in sent_url
    assert "cursor" not in sent_url
    assert "user_id=44196397" in sent_url

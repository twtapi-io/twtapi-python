"""Cookie state + automatic ct0 rotation."""

from __future__ import annotations

import httpx
import respx

from twtapi import TwtAPI


@respx.mock
def test_ct0_rotates_on_response_header(client: TwtAPI) -> None:
    client.set_cookies(auth_token="old_auth_token", ct0="old_ct0")
    respx.post("https://api.twtapi.io/like").mock(
        return_value=httpx.Response(
            200,
            headers={"X-Twitter-New-Ct0": "fresh_ct0_value"},
            json={"status": "ok"},
        )
    )

    client.tweets.like("123")

    assert client.cookies.ct0 == "fresh_ct0_value"
    assert client.cookies.auth_token == "old_auth_token"


@respx.mock
def test_no_rotation_when_header_absent(client: TwtAPI) -> None:
    client.set_cookies(auth_token="a", ct0="original")
    respx.post("https://api.twtapi.io/like").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.tweets.like("123")
    assert client.cookies.ct0 == "original"


@respx.mock
def test_on_ct0_rotated_callback_fires(client: TwtAPI) -> None:
    received: list[str] = []
    client.on_ct0_rotated(received.append)
    client.set_cookies(auth_token="a", ct0="before")

    respx.post("https://api.twtapi.io/like").mock(
        return_value=httpx.Response(
            200, headers={"X-Twitter-New-Ct0": "after"}, json={"status": "ok"}
        )
    )
    client.tweets.like("1")
    assert received == ["after"]


@respx.mock
def test_engagement_sends_cookies(client: TwtAPI) -> None:
    client.set_cookies(auth_token="my_auth", ct0="my_ct0")
    route = respx.post("https://api.twtapi.io/like").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.tweets.like("123")
    sent = route.calls.last.request.headers
    assert sent["X-Twitter-Auth-Token"] == "my_auth"
    assert sent["X-Twitter-Ct0"] == "my_ct0"


@respx.mock
def test_read_endpoint_does_not_send_cookies(client: TwtAPI) -> None:
    client.set_cookies(auth_token="my_auth", ct0="my_ct0")
    route = respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(200, json={"screen_name": "elonmusk"})
    )
    client.users.get("elonmusk")
    sent = route.calls.last.request.headers
    assert "X-Twitter-Auth-Token" not in sent
    assert "X-Twitter-Ct0" not in sent

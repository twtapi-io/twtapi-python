"""Smoke tests for the async client — same surface as sync."""

from __future__ import annotations

import httpx
import respx

from twtapi import TwtAPIAsync


@respx.mock
async def test_async_users_get(async_client: TwtAPIAsync) -> None:
    respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(200, json={"screen_name": "elonmusk"})
    )
    user = await async_client.users.get("elonmusk")
    assert user["screen_name"] == "elonmusk"
    await async_client.aclose()


@respx.mock
async def test_async_followers_iter_walks_pages(async_client: TwtAPIAsync) -> None:
    respx.get("https://api.twtapi.io/followers").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"count": 1, "followers": [{"screen_name": "a"}], "cursor_bottom": "p2"},
            ),
            httpx.Response(
                200,
                json={"count": 1, "followers": [{"screen_name": "b"}], "cursor_bottom": ""},
            ),
        ]
    )
    seen: list[str] = []
    async for follower in async_client.users.followers_iter("44196397"):
        seen.append(follower["screen_name"])
    assert seen == ["a", "b"]
    await async_client.aclose()


@respx.mock
async def test_async_ct0_rotation(async_client: TwtAPIAsync) -> None:
    async_client.set_cookies("a", "before")
    respx.post("https://api.twtapi.io/like").mock(
        return_value=httpx.Response(
            200, headers={"X-Twitter-New-Ct0": "after"}, json={"status": "ok"}
        )
    )
    await async_client.tweets.like("1")
    assert async_client.cookies.ct0 == "after"
    await async_client.aclose()

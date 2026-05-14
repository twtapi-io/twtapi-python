"""Pagination iterators: cursor_bottom / next_cursor + max caps."""

from __future__ import annotations

import httpx
import respx

from twtapi import TwtAPI


@respx.mock
def test_followers_iter_walks_pages(client: TwtAPI) -> None:
    page1 = {
        "count": 2,
        "followers": [{"screen_name": "a"}, {"screen_name": "b"}],
        "cursor_bottom": "p2",
    }
    page2 = {
        "count": 1,
        "followers": [{"screen_name": "c"}],
        "cursor_bottom": "",
    }
    route = respx.get("https://api.twtapi.io/followers").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )

    handles = [u["screen_name"] for u in client.users.followers_iter("44196397")]
    assert handles == ["a", "b", "c"]
    assert route.call_count == 2


@respx.mock
def test_iter_respects_max_items(client: TwtAPI) -> None:
    respx.get("https://api.twtapi.io/followers").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 5,
                "followers": [{"screen_name": f"u{i}"} for i in range(5)],
                "cursor_bottom": "next",
            },
        )
    )
    out = list(client.users.followers_iter("44196397", max_items=3))
    assert len(out) == 3


@respx.mock
def test_iter_respects_max_pages(client: TwtAPI) -> None:
    route = respx.get("https://api.twtapi.io/followers").mock(
        return_value=httpx.Response(
            200,
            json={"count": 1, "followers": [{"screen_name": "x"}], "cursor_bottom": "more"},
        )
    )
    list(client.users.followers_iter("44196397", max_pages=2))
    assert route.call_count == 2


@respx.mock
def test_community_members_iter_flattens_roles(client: TwtAPI) -> None:
    respx.get("https://api.twtapi.io/community_members").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 3,
                "members_by_role": {
                    "Admin": [{"screen_name": "admin1"}],
                    "Member": [{"screen_name": "member1"}, {"screen_name": "member2"}],
                },
                "next_cursor": "",
            },
        )
    )
    out = list(client.communities.members_iter("c123"))
    assert len(out) == 3
    # Each yielded user is tagged with the role bucket it came from
    roles = sorted(u["role"] for u in out)
    assert roles == ["Admin", "Member", "Member"]
    assert {u["screen_name"] for u in out} == {"admin1", "member1", "member2"}


@respx.mock
def test_community_members_iter_uses_next_cursor(client: TwtAPI) -> None:
    page1 = {
        "count": 1,
        "members_by_role": {"Member": [{"screen_name": "a"}]},
        "next_cursor": "page2",
    }
    page2 = {
        "count": 1,
        "members_by_role": {"Member": [{"screen_name": "b"}]},
        "next_cursor": "",
    }
    route = respx.get("https://api.twtapi.io/community_members").mock(
        side_effect=[httpx.Response(200, json=page1), httpx.Response(200, json=page2)]
    )
    out = [u["screen_name"] for u in client.communities.members_iter("c1")]
    assert out == ["a", "b"]
    assert route.call_count == 2

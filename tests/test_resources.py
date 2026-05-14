"""Resource-level method contracts (URLs, params, bodies)."""

from __future__ import annotations

import json

import httpx
import respx

from twtapi import TwtAPI


@respx.mock
def test_users_get_hits_user_path(client: TwtAPI) -> None:
    route = respx.get("https://api.twtapi.io/user").mock(
        return_value=httpx.Response(200, json={"screen_name": "elonmusk"})
    )
    client.users.get("elonmusk")
    assert "username=elonmusk" in str(route.calls.last.request.url)


@respx.mock
def test_by_username_hits_id_by_username(client: TwtAPI) -> None:
    route = respx.get("https://api.twtapi.io/id_by_username").mock(
        return_value=httpx.Response(200, json={"user_id": "1"})
    )
    client.users.by_username("elonmusk")
    assert "username=elonmusk" in str(route.calls.last.request.url)


@respx.mock
def test_search_passes_product_and_query(client: TwtAPI) -> None:
    route = respx.get("https://api.twtapi.io/search").mock(
        return_value=httpx.Response(200, json={"count": 0, "tweets": []})
    )
    client.search("starship", product="Latest", count=5)
    url = str(route.calls.last.request.url)
    assert "q=starship" in url
    assert "product=Latest" in url
    assert "count=5" in url


@respx.mock
def test_tweets_create_sends_media_id(client: TwtAPI) -> None:
    client.set_cookies(auth_token="a", ct0="b")
    route = respx.post("https://api.twtapi.io/tweet").mock(
        return_value=httpx.Response(200, json={"status": "ok", "tweet_id": "1"})
    )
    client.tweets.create("hi", media_id="m1")
    body = json.loads(route.calls.last.request.content)
    assert body == {"text": "hi", "media_id": "m1"}


@respx.mock
def test_tweets_create_sends_media_ids_array(client: TwtAPI) -> None:
    client.set_cookies(auth_token="a", ct0="b")
    route = respx.post("https://api.twtapi.io/tweet").mock(
        return_value=httpx.Response(200, json={"status": "ok", "tweet_id": "1"})
    )
    client.tweets.create("hi", media_ids=["m1", "m2"])
    body = json.loads(route.calls.last.request.content)
    assert body == {"text": "hi", "media_ids": ["m1", "m2"]}


@respx.mock
def test_tweets_comment_excludes_attachment_url(client: TwtAPI) -> None:
    """attachment_url is a /tweet param, not a /comment param."""
    client.set_cookies(auth_token="a", ct0="b")
    route = respx.post("https://api.twtapi.io/comment").mock(
        return_value=httpx.Response(200, json={"status": "ok", "tweet_id": "1"})
    )
    client.tweets.comment("123", "thanks")
    body = json.loads(route.calls.last.request.content)
    assert body == {"tweet_id": "123", "text": "thanks"}
    assert "attachment_url" not in body


@respx.mock
def test_media_upload_sends_url_body(client: TwtAPI) -> None:
    client.set_cookies(auth_token="a", ct0="b")
    route = respx.post("https://api.twtapi.io/upload_media").mock(
        return_value=httpx.Response(200, json={"status": "ok", "media_id": "m1"})
    )
    client.media.upload("https://example.com/photo.png")
    body = json.loads(route.calls.last.request.content)
    assert body == {"media_url": "https://example.com/photo.png"}


@respx.mock
def test_change_password_auto_rotates_cookies(client: TwtAPI) -> None:
    client.set_cookies(auth_token="old_at", ct0="old_ct0")
    respx.post("https://api.twtapi.io/change_password").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "ok",
                "password": "new",
                "generated": False,
                "new_auth_token": "fresh_at",
                "new_ct0": "fresh_ct0",
            },
        )
    )
    client.account.change_password("old_pwd", "new_pwd")
    assert client.cookies.auth_token == "fresh_at"
    assert client.cookies.ct0 == "fresh_ct0"


@respx.mock
def test_csrf_token_sends_only_auth_token_header(client: TwtAPI) -> None:
    client.set_cookies(auth_token="held_a", ct0="held_c")
    route = respx.get("https://api.twtapi.io/csrf_token").mock(
        return_value=httpx.Response(200, json={"status": "ok", "ct0": "minted"})
    )
    client.auth.csrf_token("explicit_token")
    sent = route.calls.last.request.headers
    assert sent["X-Twitter-Auth-Token"] == "explicit_token"
    # /csrf_token does NOT need ct0 — and the explicit headers must not be
    # supplemented by the held cookie pair
    assert "X-Twitter-Ct0" not in sent


@respx.mock
def test_communities_check_member_takes_only_community_id(client: TwtAPI) -> None:
    client.set_cookies(auth_token="a", ct0="b")
    route = respx.get("https://api.twtapi.io/community_check_member").mock(
        return_value=httpx.Response(200, json={"status": "ok", "is_member": True})
    )
    client.communities.check_member("c123")
    url = str(route.calls.last.request.url)
    assert "community_id=c123" in url
    assert "user_id" not in url


@respx.mock
def test_communities_request_join_includes_optional_answer(client: TwtAPI) -> None:
    client.set_cookies(auth_token="a", ct0="b")
    route = respx.post("https://api.twtapi.io/community_request_join").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.communities.request_join("c1", answer="why I want in")
    body = json.loads(route.calls.last.request.content)
    assert body == {"community_id": "c1", "answer": "why I want in"}


@respx.mock
def test_login_flow_passes_state_between_steps(client: TwtAPI) -> None:
    respx.post("https://api.twtapi.io/login/2fa").mock(
        return_value=httpx.Response(
            200, json={"status": "ok", "auth_token": "a", "ct0": "b"}
        )
    )
    route = respx.post("https://api.twtapi.io/login/2fa")
    client.auth.submit_2fa("state_blob", "123456")
    body = json.loads(route.calls.last.request.content)
    assert body == {"state": "state_blob", "code": "123456"}

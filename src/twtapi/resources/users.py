"""User profile, lookup, followers, tweets, and follow action."""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator, Optional

from twtapi._async_transport import AsyncTransport
from twtapi._transport import Transport
from twtapi.pagination import aiter_items, iter_items


class Users:
    """Sync user operations."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    # ---------------------------------------------------------------- lookup

    def get(self, username: str) -> dict[str, Any]:
        """Fetch a user's full profile by screen name. `GET /user`"""
        return self._t.request("GET", "/user", params={"username": username})

    def by_username(self, username: str) -> dict[str, Any]:
        """Resolve a screen name to a numeric user_id. `GET /id_by_username`"""
        return self._t.request("GET", "/id_by_username", params={"username": username})

    def by_id(self, user_id: str) -> dict[str, Any]:
        """Resolve a numeric user_id to a screen name. `GET /username_by_id`"""
        return self._t.request("GET", "/username_by_id", params={"user_id": user_id})

    # ---------------------------------------------------------- collections

    def followers(
        self,
        user_id: str,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """One page of followers. `GET /followers`

        Response: `{count, followers[], cursor_bottom}`.
        """
        return self._t.request(
            "GET",
            "/followers",
            params={"user_id": user_id, "count": count, "cursor": cursor},
        )

    def followers_iter(
        self,
        user_id: str,
        *,
        count: Optional[int] = None,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterate every follower across pages."""
        return iter_items(
            lambda cur: self.followers(user_id, count=count, cursor=cur),
            items_field="followers",
            max_pages=max_pages,
            max_items=max_items,
        )

    def tweets(
        self,
        user_id: str,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """One page of a user's tweets. `GET /user_tweets`

        Response: `{count, tweets[], cursor_top, cursor_bottom}`.
        """
        return self._t.request(
            "GET",
            "/user_tweets",
            params={"user_id": user_id, "count": count, "cursor": cursor},
        )

    def tweets_iter(
        self,
        user_id: str,
        *,
        count: Optional[int] = None,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> Iterator[dict[str, Any]]:
        return iter_items(
            lambda cur: self.tweets(user_id, count=count, cursor=cur),
            items_field="tweets",
            max_pages=max_pages,
            max_items=max_items,
        )

    # ---------------------------------------------------------------- action

    def follow(self, user_id: str) -> dict[str, Any]:
        """Follow a user. Requires engagement cookies. `POST /follow`"""
        return self._t.request("POST", "/follow", json={"user_id": user_id}, send_cookies=True)


class AsyncUsers:
    """Async user operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def get(self, username: str) -> dict[str, Any]:
        return await self._t.request("GET", "/user", params={"username": username})

    async def by_username(self, username: str) -> dict[str, Any]:
        return await self._t.request("GET", "/id_by_username", params={"username": username})

    async def by_id(self, user_id: str) -> dict[str, Any]:
        return await self._t.request("GET", "/username_by_id", params={"user_id": user_id})

    async def followers(
        self,
        user_id: str,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/followers",
            params={"user_id": user_id, "count": count, "cursor": cursor},
        )

    def followers_iter(
        self,
        user_id: str,
        *,
        count: Optional[int] = None,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        return aiter_items(
            lambda cur: self.followers(user_id, count=count, cursor=cur),
            items_field="followers",
            max_pages=max_pages,
            max_items=max_items,
        )

    async def tweets(
        self,
        user_id: str,
        *,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/user_tweets",
            params={"user_id": user_id, "count": count, "cursor": cursor},
        )

    def tweets_iter(
        self,
        user_id: str,
        *,
        count: Optional[int] = None,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        return aiter_items(
            lambda cur: self.tweets(user_id, count=count, cursor=cur),
            items_field="tweets",
            max_pages=max_pages,
            max_items=max_items,
        )

    async def follow(self, user_id: str) -> dict[str, Any]:
        return await self._t.request(
            "POST", "/follow", json={"user_id": user_id}, send_cookies=True
        )

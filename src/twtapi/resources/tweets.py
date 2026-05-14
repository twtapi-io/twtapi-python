"""Tweet reads (retweets / quotes / comments / reply_ids) and mutations.

Per the public spec:
- `retweets` returns compact `User[]` under the `users` field.
- `quotes`, `comments`, `user_tweets`, `search` return `Tweet[]` under `tweets`.
- `reply_ids` returns `string[]` under `reply_ids`.
- `POST /tweet` and `POST /comment` accept either `media_id` (single) or
  `media_ids` (array, up to 4) for image / video attachments.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

from twtapi._async_transport import AsyncTransport
from twtapi._transport import Transport
from twtapi.pagination import aiter_items, iter_items


def _attach_media(payload: dict[str, Any], media_id: str | None, media_ids: list[str] | None) -> None:
    if media_id is not None:
        payload["media_id"] = media_id
    if media_ids:
        payload["media_ids"] = media_ids


class Tweets:
    """Sync tweet operations."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    # -------------------------------------------------------- read endpoints

    def retweets(
        self,
        tweet_id: str,
        *,
        count: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Users that retweeted a tweet. `GET /retweets`

        Response: `{count, users[], cursor_top, cursor_bottom}`.
        """
        return self._t.request(
            "GET",
            "/retweets",
            params={"tweet_id": tweet_id, "count": count, "cursor": cursor},
        )

    def retweets_iter(
        self,
        tweet_id: str,
        *,
        count: int | None = None,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        return iter_items(
            lambda cur: self.retweets(tweet_id, count=count, cursor=cur),
            items_field="users",
            max_pages=max_pages,
            max_items=max_items,
        )

    def quotes(
        self,
        tweet_id: str,
        *,
        count: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Quote-tweets of a given tweet. `GET /quotes`"""
        return self._t.request(
            "GET",
            "/quotes",
            params={"tweet_id": tweet_id, "count": count, "cursor": cursor},
        )

    def quotes_iter(
        self,
        tweet_id: str,
        *,
        count: int | None = None,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        return iter_items(
            lambda cur: self.quotes(tweet_id, count=count, cursor=cur),
            items_field="tweets",
            max_pages=max_pages,
            max_items=max_items,
        )

    def comments(
        self,
        tweet_id: str,
        *,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Replies (full content) to a tweet. `GET /comments`"""
        return self._t.request(
            "GET",
            "/comments",
            params={"tweet_id": tweet_id, "cursor": cursor},
        )

    def comments_iter(
        self,
        tweet_id: str,
        *,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        return iter_items(
            lambda cur: self.comments(tweet_id, cursor=cur),
            items_field="comments",
            max_pages=max_pages,
            max_items=max_items,
        )

    def reply_ids(
        self,
        tweet_id: str,
        *,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Just the IDs of replies to a tweet (cheaper than `comments`).
        `GET /reply_ids`"""
        return self._t.request(
            "GET",
            "/reply_ids",
            params={"tweet_id": tweet_id, "cursor": cursor},
        )

    def reply_ids_iter(
        self,
        tweet_id: str,
        *,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> Iterator[str]:
        return iter_items(
            lambda cur: self.reply_ids(tweet_id, cursor=cur),
            items_field="reply_ids",
            max_pages=max_pages,
            max_items=max_items,
        )

    # ----------------------------------------------------- write endpoints

    def create(
        self,
        text: str,
        *,
        in_reply_to: str | None = None,
        attachment_url: str | None = None,
        media_id: str | None = None,
        media_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Post a new tweet. Requires engagement cookies. `POST /tweet`

        `in_reply_to` and `attachment_url` are mutually exclusive.
        Use either `media_id` (single) or `media_ids` (up to 4) to attach
        media uploaded via `media.upload`.
        """
        payload: dict[str, Any] = {"text": text}
        if in_reply_to is not None:
            payload["in_reply_to"] = in_reply_to
        if attachment_url is not None:
            payload["attachment_url"] = attachment_url
        _attach_media(payload, media_id, media_ids)
        return self._t.request("POST", "/tweet", json=payload, send_cookies=True)

    def comment(
        self,
        tweet_id: str,
        text: str,
        *,
        media_id: str | None = None,
        media_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Reply to a tweet. `POST /comment`"""
        payload: dict[str, Any] = {"tweet_id": tweet_id, "text": text}
        _attach_media(payload, media_id, media_ids)
        return self._t.request("POST", "/comment", json=payload, send_cookies=True)

    def like(self, tweet_id: str) -> dict[str, Any]:
        return self._t.request("POST", "/like", json={"tweet_id": tweet_id}, send_cookies=True)

    def retweet(self, tweet_id: str) -> dict[str, Any]:
        return self._t.request("POST", "/retweet", json={"tweet_id": tweet_id}, send_cookies=True)

    def bookmark(self, tweet_id: str) -> dict[str, Any]:
        return self._t.request("POST", "/bookmark", json={"tweet_id": tweet_id}, send_cookies=True)

    def delete(self, tweet_id: str) -> dict[str, Any]:
        return self._t.request(
            "POST", "/delete_tweet", json={"tweet_id": tweet_id}, send_cookies=True
        )


class AsyncTweets:
    """Async tweet operations."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def retweets(
        self,
        tweet_id: str,
        *,
        count: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/retweets",
            params={"tweet_id": tweet_id, "count": count, "cursor": cursor},
        )

    def retweets_iter(
        self,
        tweet_id: str,
        *,
        count: int | None = None,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        return aiter_items(
            lambda cur: self.retweets(tweet_id, count=count, cursor=cur),
            items_field="users",
            max_pages=max_pages,
            max_items=max_items,
        )

    async def quotes(
        self,
        tweet_id: str,
        *,
        count: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/quotes",
            params={"tweet_id": tweet_id, "count": count, "cursor": cursor},
        )

    def quotes_iter(
        self,
        tweet_id: str,
        *,
        count: int | None = None,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        return aiter_items(
            lambda cur: self.quotes(tweet_id, count=count, cursor=cur),
            items_field="tweets",
            max_pages=max_pages,
            max_items=max_items,
        )

    async def comments(
        self,
        tweet_id: str,
        *,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/comments",
            params={"tweet_id": tweet_id, "cursor": cursor},
        )

    def comments_iter(
        self,
        tweet_id: str,
        *,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        return aiter_items(
            lambda cur: self.comments(tweet_id, cursor=cur),
            items_field="comments",
            max_pages=max_pages,
            max_items=max_items,
        )

    async def reply_ids(
        self,
        tweet_id: str,
        *,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/reply_ids",
            params={"tweet_id": tweet_id, "cursor": cursor},
        )

    def reply_ids_iter(
        self,
        tweet_id: str,
        *,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> AsyncIterator[str]:
        return aiter_items(
            lambda cur: self.reply_ids(tweet_id, cursor=cur),
            items_field="reply_ids",
            max_pages=max_pages,
            max_items=max_items,
        )

    async def create(
        self,
        text: str,
        *,
        in_reply_to: str | None = None,
        attachment_url: str | None = None,
        media_id: str | None = None,
        media_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"text": text}
        if in_reply_to is not None:
            payload["in_reply_to"] = in_reply_to
        if attachment_url is not None:
            payload["attachment_url"] = attachment_url
        _attach_media(payload, media_id, media_ids)
        return await self._t.request("POST", "/tweet", json=payload, send_cookies=True)

    async def comment(
        self,
        tweet_id: str,
        text: str,
        *,
        media_id: str | None = None,
        media_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"tweet_id": tweet_id, "text": text}
        _attach_media(payload, media_id, media_ids)
        return await self._t.request("POST", "/comment", json=payload, send_cookies=True)

    async def like(self, tweet_id: str) -> dict[str, Any]:
        return await self._t.request(
            "POST", "/like", json={"tweet_id": tweet_id}, send_cookies=True
        )

    async def retweet(self, tweet_id: str) -> dict[str, Any]:
        return await self._t.request(
            "POST", "/retweet", json={"tweet_id": tweet_id}, send_cookies=True
        )

    async def bookmark(self, tweet_id: str) -> dict[str, Any]:
        return await self._t.request(
            "POST", "/bookmark", json={"tweet_id": tweet_id}, send_cookies=True
        )

    async def delete(self, tweet_id: str) -> dict[str, Any]:
        return await self._t.request(
            "POST", "/delete_tweet", json={"tweet_id": tweet_id}, send_cookies=True
        )

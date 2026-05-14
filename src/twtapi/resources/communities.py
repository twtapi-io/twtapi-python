"""Community lookup, membership checks, and join / leave actions.

Every community endpoint is viewer-scoped — it reflects the caller's
relationship with the community, not a global truth. `info`, `check_member`,
and the three write actions require engagement cookies; `members` (the list
endpoint) does not.

`members` paginates with `next_cursor` (not `cursor_bottom`) and returns
members grouped by role under `members_by_role` (e.g. `Admin`, `Member`).
The `members_iter` helper flattens this into a single stream of users,
each annotated with a `role` field.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator, Optional

from twtapi._async_transport import AsyncTransport
from twtapi._transport import Transport
from twtapi.pagination import aiter_pages, iter_pages


class Communities:
    """Sync community operations."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    # -------------------------------------------------------------- reads

    def info(self, community_id: str) -> dict[str, Any]:
        """Viewer-scoped community info. `GET /community_info`. Needs cookies."""
        return self._t.request(
            "GET",
            "/community_info",
            params={"community_id": community_id},
            send_cookies=True,
        )

    def check_member(self, community_id: str) -> dict[str, Any]:
        """Tight wrapper around `info` — just the membership-state fields.
        `GET /community_check_member`. Needs cookies."""
        return self._t.request(
            "GET",
            "/community_check_member",
            params={"community_id": community_id},
            send_cookies=True,
        )

    def members(
        self,
        community_id: str,
        *,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """One page of community members. `GET /community_members`.

        Pagination uses `next_cursor`, not `cursor_bottom`.
        """
        return self._t.request(
            "GET",
            "/community_members",
            params={"community_id": community_id, "cursor": cursor},
        )

    def members_iter(
        self,
        community_id: str,
        *,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> Iterator[dict[str, Any]]:
        """Flat stream of members across all pages and roles.

        Each yielded user dict carries an extra `role` key (e.g. `Admin`,
        `Member`) reflecting which bucket of `members_by_role` it came
        from.
        """
        yielded = 0
        for page in iter_pages(
            lambda cur: self.members(community_id, cursor=cur),
            cursor_field="next_cursor",
            max_pages=max_pages,
        ):
            for user in _flatten_members(page):
                yield user
                yielded += 1
                if max_items is not None and yielded >= max_items:
                    return

    # ------------------------------------------------------------- writes

    def join(self, community_id: str) -> dict[str, Any]:
        """`POST /community_join`. Idempotent. May return `needs_request`
        (HTTP 409 surfaces as `TwtAPIError`; for approval-gated communities
        the SDK lets you branch to `request_join`)."""
        return self._t.request(
            "POST", "/community_join", json={"community_id": community_id}, send_cookies=True
        )

    def leave(self, community_id: str) -> dict[str, Any]:
        """`POST /community_leave`. Idempotent."""
        return self._t.request(
            "POST", "/community_leave", json={"community_id": community_id}, send_cookies=True
        )

    def request_join(
        self,
        community_id: str,
        *,
        answer: Optional[str] = None,
    ) -> dict[str, Any]:
        """`POST /community_request_join`. For approval-gated communities.

        `answer` is optional free text. Most communities don't enforce one.
        """
        payload: dict[str, Any] = {"community_id": community_id}
        if answer is not None:
            payload["answer"] = answer
        return self._t.request(
            "POST",
            "/community_request_join",
            json=payload,
            send_cookies=True,
        )


class AsyncCommunities:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def info(self, community_id: str) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/community_info",
            params={"community_id": community_id},
            send_cookies=True,
        )

    async def check_member(self, community_id: str) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/community_check_member",
            params={"community_id": community_id},
            send_cookies=True,
        )

    async def members(
        self,
        community_id: str,
        *,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/community_members",
            params={"community_id": community_id, "cursor": cursor},
        )

    async def members_iter(
        self,
        community_id: str,
        *,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        yielded = 0
        async for page in aiter_pages(
            lambda cur: self.members(community_id, cursor=cur),
            cursor_field="next_cursor",
            max_pages=max_pages,
        ):
            for user in _flatten_members(page):
                yield user
                yielded += 1
                if max_items is not None and yielded >= max_items:
                    return

    async def join(self, community_id: str) -> dict[str, Any]:
        return await self._t.request(
            "POST", "/community_join", json={"community_id": community_id}, send_cookies=True
        )

    async def leave(self, community_id: str) -> dict[str, Any]:
        return await self._t.request(
            "POST", "/community_leave", json={"community_id": community_id}, send_cookies=True
        )

    async def request_join(
        self,
        community_id: str,
        *,
        answer: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"community_id": community_id}
        if answer is not None:
            payload["answer"] = answer
        return await self._t.request(
            "POST",
            "/community_request_join",
            json=payload,
            send_cookies=True,
        )


def _flatten_members(page: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Iterate `members_by_role: {role: [user, ...]}` as `[{**user, role}, ...]`."""
    by_role = page.get("members_by_role")
    if not isinstance(by_role, dict):
        return
    for role, users in by_role.items():
        if not isinstance(users, list):
            continue
        for user in users:
            if isinstance(user, dict):
                yield {**user, "role": role}

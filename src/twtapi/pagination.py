"""Pagination helpers for cursor-based list endpoints.

Most read endpoints return an object shaped like:

    {
        "count": 20,
        "cursor_top": "...",
        "cursor_bottom": "...",
        "<items_key>": [ ... ]
    }

`iter_pages` walks pages by calling a fetcher with the cursor; `iter_items`
flattens them into the individual items. Both honour `max_pages` and
`max_items` caps so callers can bound long walks.

`community_members` uses `next_cursor` instead of `cursor_bottom` — pass
`cursor_field="next_cursor"` for that endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import (
    Any,
)

PageFetcher = Callable[[str | None], dict[str, Any]]
AsyncPageFetcher = Callable[[str | None], Awaitable[dict[str, Any]]]


def iter_pages(
    fetch: PageFetcher,
    *,
    cursor_field: str = "cursor_bottom",
    max_pages: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield raw page dicts until the API stops returning a cursor."""
    cursor: str | None = None
    seen = 0
    while True:
        page = fetch(cursor)
        yield page
        seen += 1
        if max_pages is not None and seen >= max_pages:
            return
        next_cursor = page.get(cursor_field)
        if not next_cursor or next_cursor == cursor:
            return
        cursor = next_cursor


def iter_items(
    fetch: PageFetcher,
    *,
    items_field: str,
    cursor_field: str = "cursor_bottom",
    max_pages: int | None = None,
    max_items: int | None = None,
) -> Iterator[Any]:
    """Yield individual items across all pages."""
    yielded = 0
    for page in iter_pages(fetch, cursor_field=cursor_field, max_pages=max_pages):
        for item in page.get(items_field, []) or []:
            yield item
            yielded += 1
            if max_items is not None and yielded >= max_items:
                return


async def aiter_pages(
    fetch: AsyncPageFetcher,
    *,
    cursor_field: str = "cursor_bottom",
    max_pages: int | None = None,
) -> AsyncIterator[dict[str, Any]]:
    cursor: str | None = None
    seen = 0
    while True:
        page = await fetch(cursor)
        yield page
        seen += 1
        if max_pages is not None and seen >= max_pages:
            return
        next_cursor = page.get(cursor_field)
        if not next_cursor or next_cursor == cursor:
            return
        cursor = next_cursor


async def aiter_items(
    fetch: AsyncPageFetcher,
    *,
    items_field: str,
    cursor_field: str = "cursor_bottom",
    max_pages: int | None = None,
    max_items: int | None = None,
) -> AsyncIterator[Any]:
    yielded = 0
    async for page in aiter_pages(fetch, cursor_field=cursor_field, max_pages=max_pages):
        for item in page.get(items_field, []) or []:
            yield item
            yielded += 1
            if max_items is not None and yielded >= max_items:
                return

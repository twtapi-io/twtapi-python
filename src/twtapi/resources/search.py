"""Search endpoint — `GET /search`."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any, Literal

from twtapi._async_transport import AsyncTransport
from twtapi._transport import Transport
from twtapi.pagination import aiter_items, iter_items

SearchProduct = Literal["Top", "Latest", "People", "Photos", "Videos"]


def _params(
    q: str,
    product: SearchProduct | None,
    count: int | None,
    cursor: str | None,
) -> dict[str, Any]:
    return {"q": q, "product": product, "count": count, "cursor": cursor}


class Search:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def __call__(
        self,
        q: str,
        *,
        product: SearchProduct | None = None,
        count: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """One page of search results.

        `product` is one of "Top", "Latest", "People", "Media".
        """
        return self._t.request("GET", "/search", params=_params(q, product, count, cursor))

    def iter(  # noqa: A003 — `iter` is the most natural name here
        self,
        q: str,
        *,
        product: SearchProduct | None = None,
        count: int | None = None,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        return iter_items(
            lambda cur: self(q, product=product, count=count, cursor=cur),
            items_field="tweets",
            max_pages=max_pages,
            max_items=max_items,
        )


class AsyncSearch:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def __call__(
        self,
        q: str,
        *,
        product: SearchProduct | None = None,
        count: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return await self._t.request("GET", "/search", params=_params(q, product, count, cursor))

    def iter(  # noqa: A003
        self,
        q: str,
        *,
        product: SearchProduct | None = None,
        count: int | None = None,
        max_pages: int | None = None,
        max_items: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        return aiter_items(
            lambda cur: self(q, product=product, count=count, cursor=cur),
            items_field="tweets",
            max_pages=max_pages,
            max_items=max_items,
        )

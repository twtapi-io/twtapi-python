"""Search endpoint — `GET /search`."""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator, Literal, Optional

from twtapi._async_transport import AsyncTransport
from twtapi._transport import Transport
from twtapi.pagination import aiter_items, iter_items

SearchProduct = Literal["Top", "Latest", "People", "Photos", "Videos"]


def _params(
    q: str,
    product: Optional[SearchProduct],
    count: Optional[int],
    cursor: Optional[str],
) -> dict[str, Any]:
    return {"q": q, "product": product, "count": count, "cursor": cursor}


class Search:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def __call__(
        self,
        q: str,
        *,
        product: Optional[SearchProduct] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """One page of search results.

        `product` is one of "Top", "Latest", "People", "Media".
        """
        return self._t.request("GET", "/search", params=_params(q, product, count, cursor))

    def iter(  # noqa: A003 — `iter` is the most natural name here
        self,
        q: str,
        *,
        product: Optional[SearchProduct] = None,
        count: Optional[int] = None,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
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
        product: Optional[SearchProduct] = None,
        count: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        return await self._t.request("GET", "/search", params=_params(q, product, count, cursor))

    def iter(  # noqa: A003
        self,
        q: str,
        *,
        product: Optional[SearchProduct] = None,
        count: Optional[int] = None,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        return aiter_items(
            lambda cur: self(q, product=product, count=count, cursor=cur),
            items_field="tweets",
            max_pages=max_pages,
            max_items=max_items,
        )

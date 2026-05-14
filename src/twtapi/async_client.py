"""Async entry point: `TwtAPIAsync`."""

from __future__ import annotations

import logging
from types import TracebackType

from twtapi._async_transport import AsyncTransport
from twtapi._cookies import CookieRotatedCallback, CookieState
from twtapi._transport import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from twtapi.rate_limit import RateLimit
from twtapi.resources.account import AsyncAccount
from twtapi.resources.auth import AsyncAuth
from twtapi.resources.communities import AsyncCommunities
from twtapi.resources.media import AsyncMedia
from twtapi.resources.search import AsyncSearch
from twtapi.resources.tweets import AsyncTweets
from twtapi.resources.users import AsyncUsers


class TwtAPIAsync:
    """Async client for the twtapi.io HTTP API.

    Example:

        async with TwtAPIAsync(api_key="tw_...") as client:
            user = await client.users.get("elonmusk")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        proxy: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = 2,
        logger: logging.Logger | None = None,
        on_ct0_rotated: CookieRotatedCallback | None = None,
        auth_token: str | None = None,
        ct0: str | None = None,
    ) -> None:
        self._cookies = CookieState(
            auth_token=auth_token, ct0=ct0, on_ct0_rotated=on_ct0_rotated
        )
        self._transport = AsyncTransport(
            api_key=api_key,
            base_url=base_url,
            proxy=proxy,
            timeout=timeout,
            retries=retries,
            cookies=self._cookies,
            logger=logger,
        )
        self.users = AsyncUsers(self._transport)
        self.tweets = AsyncTweets(self._transport)
        self.search = AsyncSearch(self._transport)
        self.auth = AsyncAuth(self._transport)
        self.media = AsyncMedia(self._transport)
        self.account = AsyncAccount(self._transport)
        self.communities = AsyncCommunities(self._transport)

    @property
    def cookies(self) -> CookieState:
        return self._cookies

    @property
    def last_rate_limit(self) -> RateLimit | None:
        """Snapshot of `X-RateLimit-*` headers from the most recent response."""
        return self._transport.last_rate_limit

    def set_cookies(self, auth_token: str, ct0: str) -> None:
        self._cookies.set(auth_token, ct0)

    def on_ct0_rotated(self, callback: CookieRotatedCallback | None) -> None:
        self._cookies.set_on_rotated(callback)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> TwtAPIAsync:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

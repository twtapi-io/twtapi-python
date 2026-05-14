"""Sync entry point: `TwtAPI`."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Optional, Type

from twtapi._cookies import CookieRotatedCallback, CookieState
from twtapi._transport import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, Transport
from twtapi.rate_limit import RateLimit
from twtapi.resources.account import Account
from twtapi.resources.auth import Auth
from twtapi.resources.communities import Communities
from twtapi.resources.media import Media
from twtapi.resources.search import Search
from twtapi.resources.tweets import Tweets
from twtapi.resources.users import Users


class TwtAPI:
    """Synchronous client for the twtapi.io HTTP API.

    Example:

        client = TwtAPI(api_key="tw_...")
        user = client.users.get("elonmusk")

    For engagement endpoints, supply X cookies once and the SDK attaches
    them (and auto-rotates ct0) for every subsequent call:

        client.set_cookies(auth_token="...", ct0="...")
        client.tweets.like(tweet_id="123")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        proxy: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = 2,
        logger: Optional[logging.Logger] = None,
        on_ct0_rotated: Optional[CookieRotatedCallback] = None,
        auth_token: Optional[str] = None,
        ct0: Optional[str] = None,
    ) -> None:
        self._cookies = CookieState(
            auth_token=auth_token, ct0=ct0, on_ct0_rotated=on_ct0_rotated
        )
        self._transport = Transport(
            api_key=api_key,
            base_url=base_url,
            proxy=proxy,
            timeout=timeout,
            retries=retries,
            cookies=self._cookies,
            logger=logger,
        )
        self.users = Users(self._transport)
        self.tweets = Tweets(self._transport)
        self.search = Search(self._transport)
        self.auth = Auth(self._transport)
        self.media = Media(self._transport)
        self.account = Account(self._transport)
        self.communities = Communities(self._transport)

    # --------------------------------------------------------- cookie state

    @property
    def cookies(self) -> CookieState:
        """The held cookie state. Use `cookies.ct0` to persist after rotation."""
        return self._cookies

    @property
    def last_rate_limit(self) -> Optional[RateLimit]:
        """Snapshot of `X-RateLimit-*` headers from the most recent response.
        `None` until the first successful call."""
        return self._transport.last_rate_limit

    def set_cookies(self, auth_token: str, ct0: str) -> None:
        """Set the engagement cookies attached to every authenticated call."""
        self._cookies.set(auth_token, ct0)

    def on_ct0_rotated(self, callback: Optional[CookieRotatedCallback]) -> None:
        """Register a callback fired whenever the server returns a fresh ct0."""
        self._cookies.set_on_rotated(callback)

    # --------------------------------------------------------- lifecycle

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "TwtAPI":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

"""Login flow + cookie helpers.

The login flow is multi-step. `start` returns one of:
  - `{"status": "ok", "auth_token": "...", "ct0": "..."}` — login succeeded
  - `{"status": "challenge", "type": "2fa" | "email_code", "state": "..."}`
    — pass the `state` (encrypted server-side token) to `submit_2fa` or
    `submit_email_code` along with the user-supplied code.
"""

from __future__ import annotations

from typing import Any, Optional

from twtapi._async_transport import AsyncTransport
from twtapi._transport import Transport


class Auth:
    """Sync login + cookie helpers."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def login(
        self,
        username: str,
        password: str,
        *,
        proxy: Optional[str] = None,
    ) -> dict[str, Any]:
        """Start a login. `POST /login/start`"""
        payload: dict[str, Any] = {"username": username, "password": password}
        if proxy:
            payload["proxy"] = proxy
        return self._t.request("POST", "/login/start", json=payload)

    def submit_2fa(self, challenge_token: str, code: str) -> dict[str, Any]:
        """`POST /login/2fa`. `challenge_token` is the `state` from `login()`."""
        return self._t.request(
            "POST",
            "/login/2fa",
            json={"state": challenge_token, "code": code},
        )

    def submit_email_code(
        self,
        challenge_token: str,
        code: str,
        *,
        alternate_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """`POST /login/email_code`."""
        payload: dict[str, Any] = {"state": challenge_token, "code": code}
        if alternate_id is not None:
            payload["alternate_id"] = alternate_id
        return self._t.request("POST", "/login/email_code", json=payload)

    def csrf_token(self, auth_token: str) -> dict[str, Any]:
        """Mint a fresh ct0 from an auth_token. `GET /csrf_token`"""
        return self._t.request(
            "GET",
            "/csrf_token",
            extra_headers={"X-Twitter-Auth-Token": auth_token},
        )

    def whoami(self, auth_token: str, ct0: str) -> dict[str, Any]:
        """Return the screen name behind a cookie pair.
        `GET /screen_name_from_token`"""
        return self._t.request(
            "GET",
            "/screen_name_from_token",
            extra_headers={
                "X-Twitter-Auth-Token": auth_token,
                "X-Twitter-Ct0": ct0,
            },
        )


class AsyncAuth:
    """Async login + cookie helpers."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def login(
        self,
        username: str,
        password: str,
        *,
        proxy: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"username": username, "password": password}
        if proxy:
            payload["proxy"] = proxy
        return await self._t.request("POST", "/login/start", json=payload)

    async def submit_2fa(self, challenge_token: str, code: str) -> dict[str, Any]:
        return await self._t.request(
            "POST",
            "/login/2fa",
            json={"state": challenge_token, "code": code},
        )

    async def submit_email_code(
        self,
        challenge_token: str,
        code: str,
        *,
        alternate_id: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"state": challenge_token, "code": code}
        if alternate_id is not None:
            payload["alternate_id"] = alternate_id
        return await self._t.request("POST", "/login/email_code", json=payload)

    async def csrf_token(self, auth_token: str) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/csrf_token",
            extra_headers={"X-Twitter-Auth-Token": auth_token},
        )

    async def whoami(self, auth_token: str, ct0: str) -> dict[str, Any]:
        return await self._t.request(
            "GET",
            "/screen_name_from_token",
            extra_headers={
                "X-Twitter-Auth-Token": auth_token,
                "X-Twitter-Ct0": ct0,
            },
        )

"""Account-level mutations (currently: password change)."""

from __future__ import annotations

from typing import Any, Optional

from twtapi._async_transport import AsyncTransport
from twtapi._cookies import CookieState
from twtapi._transport import Transport


def _apply_new_cookies(cookies: CookieState, response: dict[str, Any]) -> None:
    """Password change invalidates the previous session. Auto-rotate the
    held cookie pair so subsequent calls keep working."""
    new_auth = response.get("new_auth_token")
    new_ct0 = response.get("new_ct0")
    if new_auth and new_ct0:
        cookies.set(new_auth, new_ct0)


class Account:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def change_password(
        self,
        current: str,
        new: Optional[str] = None,
    ) -> dict[str, Any]:
        """`POST /change_password`. Requires engagement cookies.

        Pass `new=None` (or empty) to have a 16-char password generated for
        you. The response carries `new_auth_token` + `new_ct0` (the prior
        session is invalidated) — the SDK auto-rotates the held cookies.
        """
        payload: dict[str, Any] = {"current_password": current}
        if new:
            payload["password"] = new
        response = self._t.request(
            "POST", "/change_password", json=payload, send_cookies=True
        )
        _apply_new_cookies(self._t.cookies, response)
        return response


class AsyncAccount:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def change_password(
        self,
        current: str,
        new: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"current_password": current}
        if new:
            payload["password"] = new
        response = await self._t.request(
            "POST", "/change_password", json=payload, send_cookies=True
        )
        _apply_new_cookies(self._t.cookies, response)
        return response

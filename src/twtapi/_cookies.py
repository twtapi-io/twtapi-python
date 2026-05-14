"""Engagement cookie state holder.

Holds `auth_token` + `ct0`, exposes them to every engagement call, and
auto-rotates `ct0` when the server returns a fresh value in the
`X-Twitter-New-Ct0` response header.
"""

from __future__ import annotations

from threading import Lock
from typing import Callable, Optional

CookieRotatedCallback = Callable[[str], None]


class CookieState:
    """Thread-safe holder for the X auth_token / ct0 pair."""

    def __init__(
        self,
        auth_token: Optional[str] = None,
        ct0: Optional[str] = None,
        on_ct0_rotated: Optional[CookieRotatedCallback] = None,
    ) -> None:
        self._lock = Lock()
        self._auth_token = auth_token
        self._ct0 = ct0
        self._on_rotated = on_ct0_rotated

    @property
    def auth_token(self) -> Optional[str]:
        with self._lock:
            return self._auth_token

    @property
    def ct0(self) -> Optional[str]:
        with self._lock:
            return self._ct0

    def set(self, auth_token: Optional[str], ct0: Optional[str]) -> None:
        with self._lock:
            self._auth_token = auth_token
            self._ct0 = ct0

    def set_on_rotated(self, callback: Optional[CookieRotatedCallback]) -> None:
        with self._lock:
            self._on_rotated = callback

    def snapshot(self) -> tuple[Optional[str], Optional[str]]:
        with self._lock:
            return self._auth_token, self._ct0

    def rotate_ct0(self, new_ct0: str) -> bool:
        """Update ct0 in-place and fire the optional callback.

        Returns True if the value actually changed.
        """
        with self._lock:
            if not new_ct0 or new_ct0 == self._ct0:
                return False
            self._ct0 = new_ct0
            cb = self._on_rotated
        if cb is not None:
            try:
                cb(new_ct0)
            except Exception:  # noqa: BLE001 — user callback must not break the SDK
                pass
        return True

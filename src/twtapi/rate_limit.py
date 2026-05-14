"""Snapshot of the most recently seen rate-limit headers.

Per the spec, every successful response carries:
    X-RateLimit-Limit       steady-state RPS for the matched bucket
    X-RateLimit-Remaining   requests left in the current window
    X-RateLimit-Reset       Unix timestamp when the window resets

`client.last_rate_limit` returns the last snapshot the SDK saw. None until
the first successful response.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RateLimit:
    """Latest rate-limit snapshot from a response."""

    limit: int | None
    remaining: int | None
    reset: int | None

    @classmethod
    def from_headers(cls, headers: Mapping[str, Any]) -> RateLimit | None:
        limit = _int(headers.get("X-RateLimit-Limit"))
        remaining = _int(headers.get("X-RateLimit-Remaining"))
        reset = _int(headers.get("X-RateLimit-Reset"))
        if limit is None and remaining is None and reset is None:
            return None
        return cls(limit=limit, remaining=remaining, reset=reset)


def _int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

"""Sync HTTP transport for the twtapi SDK.

Owns: header injection (X-API-Key + optional engagement cookies + optional
proxy), JSON encode/decode, error mapping, ct0 auto-rotation, retry policy,
rate-limit tracking, and optional structured logging with secret masking.

Everything above this layer just calls `Transport.request(method, path, ...)`
and gets back a parsed JSON dict (or raises a TwtAPIError).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Mapping, Optional, Union

import httpx

from twtapi._cookies import CookieState
from twtapi.errors import NetworkError, from_response
from twtapi.rate_limit import RateLimit

DEFAULT_BASE_URL = "https://api.twtapi.io"
DEFAULT_TIMEOUT = 30.0
DEFAULT_USER_AGENT = "twtapi-python/0.1.0"

_NEW_CT0_HEADER = "X-Twitter-New-Ct0"
_RETRY_STATUSES = {408, 429, 500, 502, 503}
_NON_IDEMPOTENT_PATHS = frozenset({"/tweet", "/comment"})

JSONBody = Union[Mapping[str, Any], list[Any], None]


class Transport:
    """Sync HTTP transport. Wraps a single `httpx.Client`."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        proxy: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = 2,
        cookies: Optional[CookieState] = None,
        logger: Optional[logging.Logger] = None,
        user_agent: str = DEFAULT_USER_AGENT,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._proxy = proxy
        self._retries = max(0, retries)
        self._cookies = cookies or CookieState()
        self._logger = logger
        self._user_agent = user_agent
        self._last_rate_limit: Optional[RateLimit] = None

        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": user_agent, "Accept": "application/json"},
        )

    # ----------------------------------------------------------------- props

    @property
    def cookies(self) -> CookieState:
        return self._cookies

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def last_rate_limit(self) -> Optional[RateLimit]:
        return self._last_rate_limit

    # ----------------------------------------------------------- public API

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: JSONBody = None,
        data: Optional[Mapping[str, Any]] = None,
        files: Optional[Mapping[str, Any]] = None,
        send_cookies: bool = False,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> dict[str, Any]:
        """Issue one HTTP request and return parsed JSON.

        `send_cookies=True` attaches the held X auth_token + ct0 to the
        request (required for engagement / community / helper endpoints
        that act on a specific 𝕏 account).
        """
        url = self._build_url(path)
        headers = self._build_headers(send_cookies=send_cookies, extra=extra_headers)
        clean_params = _drop_none(params) if params else None
        retryable = _is_retryable(method, path)

        attempt = 0
        while True:
            attempt += 1
            t0 = time.monotonic()
            try:
                response = self._client.request(
                    method,
                    url,
                    params=clean_params,
                    json=json,
                    data=data,
                    files=files,
                    headers=headers,
                )
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
                self._log_failed(method, path, str(exc), time.monotonic() - t0)
                if attempt > self._retries:
                    raise NetworkError(f"{type(exc).__name__}: {exc}") from exc
                time.sleep(_backoff(attempt))
                continue
            except httpx.HTTPError as exc:
                raise NetworkError(f"{type(exc).__name__}: {exc}") from exc

            self._capture_ct0_rotation(response)
            self._capture_rate_limit(response)
            duration = time.monotonic() - t0
            self._log_completed(method, path, response.status_code, duration)

            status = response.status_code
            if status in _RETRY_STATUSES and retryable and attempt <= self._retries:
                wait = self._wait_for_retry(status, response)
                time.sleep(wait)
                continue

            return self._handle_response(response)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    # --------------------------------------------------------------- helpers

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._base_url}{path}"

    def _build_headers(
        self,
        *,
        send_cookies: bool,
        extra: Optional[Mapping[str, str]],
    ) -> dict[str, str]:
        headers: dict[str, str] = {"X-API-Key": self._api_key}
        if self._proxy:
            headers["X-Proxy"] = self._proxy
        if send_cookies:
            auth_token, ct0 = self._cookies.snapshot()
            if auth_token:
                headers["X-Twitter-Auth-Token"] = auth_token
            if ct0:
                headers["X-Twitter-Ct0"] = ct0
        if extra:
            headers.update(extra)
        return headers

    def _capture_ct0_rotation(self, response: httpx.Response) -> None:
        new_ct0 = response.headers.get(_NEW_CT0_HEADER)
        if new_ct0:
            self._cookies.rotate_ct0(new_ct0)

    def _capture_rate_limit(self, response: httpx.Response) -> None:
        snapshot = RateLimit.from_headers(response.headers)
        if snapshot is not None:
            self._last_rate_limit = snapshot

    def _wait_for_retry(self, status: int, response: httpx.Response) -> float:
        if status == 429:
            body = _safe_json(response)
            from_body = (
                _coerce_float(body.get("retry_after")) if isinstance(body, dict) else None
            )
            from_header = _parse_retry_after(response.headers.get("Retry-After"))
            wait = from_body if from_body is not None else from_header
            return min(wait or 1.0, 60.0)
        # 408 / 5xx: exponential backoff capped at 8s
        return 1.0

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        status = response.status_code
        body = _safe_json(response)
        if 200 <= status < 300:
            return body if isinstance(body, dict) else {"data": body}
        retry_after_header = _parse_retry_after(response.headers.get("Retry-After"))
        raise from_response(status=status, body=body, retry_after_header=retry_after_header)

    # ---------------------------------------------------------------- logging

    def _log_completed(self, method: str, path: str, status: int, duration: float) -> None:
        if self._logger is None:
            return
        self._logger.info(
            "twtapi request",
            extra={
                "method": method,
                "path": path,
                "status": status,
                "duration_ms": round(duration * 1000, 2),
                "api_key": _mask(self._api_key),
            },
        )

    def _log_failed(self, method: str, path: str, reason: str, duration: float) -> None:
        if self._logger is None:
            return
        self._logger.warning(
            "twtapi request failed",
            extra={
                "method": method,
                "path": path,
                "error": reason,
                "duration_ms": round(duration * 1000, 2),
                "api_key": _mask(self._api_key),
            },
        )


# --------------------------------------------------------------- module utils


def _is_retryable(method: str, path: str) -> bool:
    """Per spec §4.3 / §8.5: every endpoint is safe to retry on 5xx/408/429
    except `POST /tweet` and `POST /comment`, which create new content."""
    if method.upper() != "POST":
        return True
    base_path = path.split("?", 1)[0]
    if not base_path.startswith("/"):
        base_path = "/" + base_path
    return base_path not in _NON_IDEMPOTENT_PATHS


def _backoff(attempt: int) -> float:
    """Exponential backoff (0.5, 1, 2, 4, 8) capped at 8s."""
    return min(0.5 * (2 ** (attempt - 1)), 8.0)


def _drop_none(params: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:  # noqa: BLE001 — server may return plain text on infra errors
        text = response.text
        return {"error": "invalid_json", "message": text[:500]} if text else {}


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mask(secret: str) -> str:
    if not secret:
        return ""
    return secret[:8] + "…"

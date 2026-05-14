"""Async HTTP transport for the twtapi SDK.

Mirrors `_transport.Transport` but uses `httpx.AsyncClient` + `asyncio.sleep`
so the same retry / rotation / error-mapping / rate-limit semantics apply
in async code.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Mapping
from typing import Any

import httpx

from twtapi._cookies import CookieState
from twtapi._transport import (
    _NEW_CT0_HEADER,
    _RETRY_STATUSES,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    JSONBody,
    _backoff,
    _coerce_float,
    _drop_none,
    _is_retryable,
    _mask,
    _parse_retry_after,
    _safe_json,
)
from twtapi.errors import NetworkError, from_response
from twtapi.rate_limit import RateLimit


class AsyncTransport:
    """Async HTTP transport. Wraps a single `httpx.AsyncClient`."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        proxy: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = 2,
        cookies: CookieState | None = None,
        logger: logging.Logger | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
        http_client: httpx.AsyncClient | None = None,
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
        self._last_rate_limit: RateLimit | None = None

        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": user_agent, "Accept": "application/json"},
        )

    @property
    def cookies(self) -> CookieState:
        return self._cookies

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def last_rate_limit(self) -> RateLimit | None:
        return self._last_rate_limit

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: JSONBody = None,
        data: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        send_cookies: bool = False,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        url = self._build_url(path)
        headers = self._build_headers(send_cookies=send_cookies, extra=extra_headers)
        clean_params = _drop_none(params) if params else None
        retryable = _is_retryable(method, path)

        attempt = 0
        while True:
            attempt += 1
            t0 = time.monotonic()
            try:
                response = await self._client.request(
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
                await asyncio.sleep(_backoff(attempt))
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
                await asyncio.sleep(wait)
                continue

            return self._handle_response(response)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

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
        extra: Mapping[str, str] | None,
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
        return 1.0

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        status = response.status_code
        body = _safe_json(response)
        if 200 <= status < 300:
            return body if isinstance(body, dict) else {"data": body}
        retry_after_header = _parse_retry_after(response.headers.get("Retry-After"))
        raise from_response(status=status, body=body, retry_after_header=retry_after_header)

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

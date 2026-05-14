"""Media upload — `POST /upload_media`.

Per the public spec, the API uploads media on your behalf by downloading
from a public URL. Pass an `https://` URL; the server fetches, follows up
to 5 redirects, refuses private / loopback hosts, then registers the file
upstream and returns a `media_id` you can pass to `tweets.create` or
`tweets.comment`.

Limits: 16 MiB. Supported types: jpg, png, gif, webp, bmp, mp4, mov, webm.
`media_id` expires within ~15 minutes if not consumed.
"""

from __future__ import annotations

from typing import Any

from twtapi._async_transport import AsyncTransport
from twtapi._transport import Transport


class Media:
    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def upload(self, media_url: str) -> dict[str, Any]:
        """Upload media from a public URL.

        Returns `{"status": "ok", "media_id": "...", "size": ..., "media_type": "..."}`.
        """
        return self._t.request(
            "POST", "/upload_media", json={"media_url": media_url}, send_cookies=True
        )


class AsyncMedia:
    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    async def upload(self, media_url: str) -> dict[str, Any]:
        return await self._t.request(
            "POST", "/upload_media", json={"media_url": media_url}, send_cookies=True
        )

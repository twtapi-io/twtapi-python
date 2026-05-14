"""Upload media from a public URL, attach it to a tweet.

`media.upload(media_url)` downloads the URL server-side and returns a
`media_id` you pass to `tweets.create`. The id expires within ~15 minutes
if not consumed.

Supported types: jpg, png, gif, webp, bmp, mp4, mov, webm. Max 16 MiB.

    export TWTAPI_KEY="tw_..."
    export X_AUTH_TOKEN="..."
    export X_CT0="..."
    python examples/upload_media_and_tweet.py
"""

from __future__ import annotations

import os

from twtapi import TwtAPI


def main() -> None:
    api_key = os.environ.get("TWTAPI_KEY")
    auth_token = os.environ.get("X_AUTH_TOKEN")
    ct0 = os.environ.get("X_CT0")
    if not (api_key and auth_token and ct0):
        raise SystemExit("Set TWTAPI_KEY, X_AUTH_TOKEN, X_CT0 in the environment.")

    image_url = "https://placehold.co/600x400/png?text=twtapi"

    with TwtAPI(api_key=api_key, auth_token=auth_token, ct0=ct0) as client:
        upload = client.media.upload(image_url)
        media_id = upload["media_id"]
        print(f"Uploaded: media_id={media_id} size={upload['size']:,}B type={upload['media_type']}")

        result = client.tweets.create("hello from twtapi 🐍", media_id=media_id)
        print(f"Tweeted: tweet_id={result['tweet_id']}")


if __name__ == "__main__":
    main()

"""Post a tweet — the simplest engagement flow.

Requires cookies (auth_token + ct0) of the account that will post. Get
them by running examples/login_with_2fa.py first, then persist the pair
somewhere safe.

    export TWTAPI_KEY="tw_..."
    export X_AUTH_TOKEN="..."
    export X_CT0="..."
    python examples/post_a_tweet.py
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from twtapi import DuplicateTweetError, RateLimitError, TwtAPI


def main() -> None:
    api_key = os.environ.get("TWTAPI_KEY")
    auth_token = os.environ.get("X_AUTH_TOKEN")
    ct0 = os.environ.get("X_CT0")
    if not (api_key and auth_token and ct0):
        raise SystemExit(
            "Set TWTAPI_KEY, X_AUTH_TOKEN, X_CT0 in the environment."
        )

    text = f"Posted from the twtapi Python SDK at {datetime.now(timezone.utc).isoformat()}"

    with TwtAPI(api_key=api_key, auth_token=auth_token, ct0=ct0) as client:
        # Persist the rotated ct0 whenever the server hands us a fresh one
        client.on_ct0_rotated(lambda new_ct0: print(f"ct0 rotated → {new_ct0[:8]}…"))

        try:
            result = client.tweets.create(text)
        except DuplicateTweetError:
            print("Skipped: already posted that exact text recently.")
            return
        except RateLimitError as e:
            print(f"Rate-limited (scope={e.scope}). Retry after {e.retry_after}s.")
            return

        tweet_id = result["tweet_id"]
        print(f"Posted: tweet_id={tweet_id}")

        # Like our own tweet to demonstrate a second chained call
        client.tweets.like(tweet_id)
        print("Liked it.")


if __name__ == "__main__":
    main()

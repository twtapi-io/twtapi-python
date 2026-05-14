"""Walk followers with pagination.

Bounded by `max_items` so the script always terminates — top-tier accounts
may have hundreds of millions of followers and depth-truncate at ~200k.

    export TWTAPI_KEY="tw_..."
    python examples/walk_followers.py
"""

from __future__ import annotations

import os

from twtapi import TwtAPI


def main() -> None:
    key = os.environ.get("TWTAPI_KEY")
    if not key:
        raise SystemExit("Set TWTAPI_KEY in the environment.")

    handle = "elonmusk"
    sample_size = 20

    with TwtAPI(api_key=key) as client:
        user_id = client.users.by_username(handle)["user_id"]
        print(f"Walking first {sample_size} followers of @{handle} ({user_id})")
        print("-" * 70)

        for i, follower in enumerate(
            client.users.followers_iter(user_id, count=200, max_items=sample_size),
            start=1,
        ):
            print(
                f"{i:>3}. @{follower['screen_name']:<20} "
                f"{follower['followers_count']:>12,} followers"
            )

        print("-" * 70)
        print(f"Rate limit snapshot: {client.last_rate_limit}")


if __name__ == "__main__":
    main()

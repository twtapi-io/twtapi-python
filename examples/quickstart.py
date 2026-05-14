"""Quickstart: fetch a public profile.

    pip install twtapi
    export TWTAPI_KEY="tw_..."
    python examples/quickstart.py
"""

from __future__ import annotations

import os

from twtapi import TwtAPI


def main() -> None:
    key = os.environ.get("TWTAPI_KEY")
    if not key:
        raise SystemExit("Set TWTAPI_KEY in the environment. Get one at https://twtapi.io/dashboard")

    with TwtAPI(api_key=key) as client:
        user = client.users.get("elonmusk")
        print(f"@{user['screen_name']} — {user['name']}")
        print(f"  followers: {user['followers_count']:,}")
        print(f"  following: {user['friends_count']:,}")
        print(f"  tweets:    {user['statuses_count']:,}")
        print(f"  bio:       {user.get('description', '')[:80]}")


if __name__ == "__main__":
    main()

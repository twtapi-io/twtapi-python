"""Search tweets with the `product` selector.

`product` is one of: Top, Latest, People, Photos, Videos.

    export TWTAPI_KEY="tw_..."
    python examples/search.py
"""

from __future__ import annotations

import os

from twtapi import TwtAPI


def main() -> None:
    key = os.environ.get("TWTAPI_KEY")
    if not key:
        raise SystemExit("Set TWTAPI_KEY in the environment.")

    query = "starship launch"

    with TwtAPI(api_key=key) as client:
        print(f"Top results for: {query!r}")
        print("=" * 70)
        for tweet in client.search.iter(query, product="Top", max_items=5):
            author = tweet.get("user", {}).get("screen_name", "?")
            print(f"@{author}: {tweet['text'][:120]}…")
            print(
                f"  {tweet.get('favorite_count', 0):,} likes | "
                f"{tweet.get('retweet_count', 0):,} retweets"
            )
            print("-" * 70)


if __name__ == "__main__":
    main()

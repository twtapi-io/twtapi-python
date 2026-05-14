# twtapi — official Python client

[![PyPI](https://img.shields.io/pypi/v/twtapi.svg)](https://pypi.org/project/twtapi/)
[![Python](https://img.shields.io/pypi/pyversions/twtapi.svg)](https://pypi.org/project/twtapi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Programmatic access to 𝕏 (Twitter) data and actions, built on the
[twtapi.io](https://twtapi.io) HTTP API. Sync + async, typed errors,
built-in pagination, automatic cookie rotation.

```python
from twtapi import TwtAPI

client = TwtAPI(api_key="tw_...")
user = client.users.get("elonmusk")
print(user["screen_name"], user["followers_count"])
```

---

## Install

```bash
pip install twtapi
```

Requires Python 3.9+. The only runtime dependency is [`httpx`](https://www.python-httpx.org/).

Get an API key at <https://twtapi.io/dashboard>. Full method reference and
Try-It panels at <https://twtapi.io/docs>.

---

## Quickstart

```python
from twtapi import TwtAPI

client = TwtAPI(api_key="tw_...")

# Read public profile
user = client.users.get("elonmusk")
print(f"{user['screen_name']} — {user['followers_count']:,} followers")

# Paginate followers
for follower in client.users.followers_iter(user["user_id"], max_items=100):
    print(f"  @{follower['screen_name']}")

# Search recent tweets
for tweet in client.search.iter("starship", product="Latest", max_items=10):
    print(tweet["text"])

client.close()
```

Use `with` for automatic cleanup:

```python
with TwtAPI(api_key="tw_...") as client:
    user = client.users.get("elonmusk")
```

---

## Features

- **Sync + async** clients in one package: `TwtAPI`, `TwtAPIAsync`
- **Typed exceptions** for every documented status code
- **Built-in pagination iterators** with `max_pages` / `max_items` caps
- **Automatic `ct0` cookie rotation** on engagement endpoints
- **Login flow** with 2FA and email-code challenge support
- **Engagement**: post, like, retweet, follow, bookmark, delete
- **Media upload** from a public URL
- **Communities**: info, members, join, leave, request-join
- **Rate-limit tracking** via `client.last_rate_limit`
- **Optional structured logging** with API-key / cookie masking
- **Outbound proxy** support via the `proxy=` constructor argument
- Type-checked (`py.typed` ships with the package)

---

## Authentication

### API key

Every call carries your `X-API-Key` header. Pass it once at construction:

```python
client = TwtAPI(api_key="tw_...")
```

You can also pass `base_url=`, `proxy=`, `timeout=`, and `retries=`:

```python
client = TwtAPI(
    api_key="tw_...",
    base_url="https://api.twtapi.io",   # default
    proxy="http://user:pass@host:port",  # optional
    timeout=30.0,                        # seconds
    retries=2,                           # set to 0 to disable
)
```

### Engagement cookies

Engagement endpoints (post a tweet, like, follow, etc.) act on a real 𝕏
account. The SDK forwards the account's `auth_token` and `ct0` cookies to
the API. Two ways to supply them:

**Per-client** (recommended):

```python
client = TwtAPI(api_key="tw_...", auth_token="...", ct0="...")
# or set later
client.set_cookies(auth_token="...", ct0="...")

client.tweets.like("1812256370960879853")
```

**Read the current values back** (cookies may rotate mid-flight):

```python
print(client.cookies.auth_token)
print(client.cookies.ct0)
```

### Automatic `ct0` rotation

The API rotates `ct0` mid-flight whenever the upstream returns a fresh
value. The SDK detects the rotation, updates its internal state, and lets
you observe the new value:

```python
# Persist the new ct0 every time it rotates
client.on_ct0_rotated(lambda new_ct0: db.save_ct0(new_ct0))
```

Without this handling chained calls would fail with an auth error. The
SDK takes care of it automatically.

---

## Method reference

Every method maps 1:1 to one HTTP endpoint. Responses come back as plain
`dict`s — inspect them with `.keys()` or read the
[full schema reference](https://twtapi.io/docs).

### Users

| Method | Endpoint | Notes |
|---|---|---|
| `client.users.get(username)` | `GET /user` | Full public profile |
| `client.users.by_username(username)` | `GET /id_by_username` | Resolve handle → `user_id` |
| `client.users.by_id(user_id)` | `GET /username_by_id` | Resolve `user_id` → handle |
| `client.users.followers(user_id, *, count=None, cursor=None)` | `GET /followers` | One page |
| `client.users.followers_iter(user_id, *, count=None, max_pages=None, max_items=None)` | — | Iterator |
| `client.users.tweets(user_id, *, count=None, cursor=None)` | `GET /user_tweets` | One page |
| `client.users.tweets_iter(user_id, ...)` | — | Iterator |
| `client.users.follow(user_id)` | `POST /follow` | Needs cookies |

### Tweets

| Method | Endpoint | Notes |
|---|---|---|
| `client.tweets.retweets(tweet_id, *, count=None, cursor=None)` | `GET /retweets` | Users who retweeted |
| `client.tweets.quotes(tweet_id, *, count=None, cursor=None)` | `GET /quotes` | Quote-tweets |
| `client.tweets.comments(tweet_id, *, cursor=None)` | `GET /comments` | Hydrated replies |
| `client.tweets.reply_ids(tweet_id, *, cursor=None)` | `GET /reply_ids` | Reply IDs only |
| `client.tweets.create(text, *, in_reply_to=None, attachment_url=None, media_id=None, media_ids=None)` | `POST /tweet` | Needs cookies |
| `client.tweets.comment(tweet_id, text, *, media_id=None, media_ids=None)` | `POST /comment` | Needs cookies |
| `client.tweets.like(tweet_id)` | `POST /like` | Needs cookies |
| `client.tweets.retweet(tweet_id)` | `POST /retweet` | Needs cookies |
| `client.tweets.bookmark(tweet_id)` | `POST /bookmark` | Needs cookies |
| `client.tweets.delete(tweet_id)` | `POST /delete_tweet` | Needs cookies |

Every paginated method has a matching `*_iter` companion that walks pages
until exhaustion or until `max_pages` / `max_items` is hit.

### Search

```python
for tweet in client.search.iter("from:elonmusk", product="Latest", max_items=50):
    print(tweet["text"])
```

`product` is one of `"Top"`, `"Latest"`, `"People"`, `"Photos"`, `"Videos"`.

### Auth (login flow)

| Method | Endpoint |
|---|---|
| `client.auth.login(username, password, *, proxy=None)` | `POST /login/start` |
| `client.auth.submit_2fa(challenge_token, code)` | `POST /login/2fa` |
| `client.auth.submit_email_code(challenge_token, code, *, alternate_id=None)` | `POST /login/email_code` |
| `client.auth.csrf_token(auth_token)` | `GET /csrf_token` |
| `client.auth.whoami(auth_token, ct0)` | `GET /screen_name_from_token` |

```python
result = client.auth.login("yourhandle", "your_password")
if result["status"] == "ok":
    client.set_cookies(result["auth_token"], result["ct0"])
elif result.get("type") == "two_factor":
    code = input("2FA code: ")
    result = client.auth.submit_2fa(result["state"], code)
    client.set_cookies(result["auth_token"], result["ct0"])
```

### Media

```python
media = client.media.upload("https://placehold.co/600x400/png")
client.tweets.create("hello with image", media_id=media["media_id"])
```

The `media_id` expires within ~15 minutes. Upload and consume in the
same workflow.

### Communities

| Method | Endpoint | Notes |
|---|---|---|
| `client.communities.info(community_id)` | `GET /community_info` | Needs cookies |
| `client.communities.check_member(community_id)` | `GET /community_check_member` | Needs cookies |
| `client.communities.members(community_id, *, cursor=None)` | `GET /community_members` | Returns `{members_by_role: ...}` |
| `client.communities.members_iter(community_id, ...)` | — | Flattens roles, adds `role` field |
| `client.communities.join(community_id)` | `POST /community_join` | Needs cookies |
| `client.communities.leave(community_id)` | `POST /community_leave` | Needs cookies |
| `client.communities.request_join(community_id, *, answer=None)` | `POST /community_request_join` | Needs cookies |

### Account

```python
result = client.account.change_password(current="OldPassw0rd!", new="NewPassw0rd!")
# Or generate one for you:
result = client.account.change_password(current="OldPassw0rd!")
print(result["password"], result["generated"])
```

The SDK auto-rotates the held cookie pair using `new_auth_token` /
`new_ct0` from the response — the previous session is invalidated by 𝕏.

---

## Pagination

Every paginated read endpoint ships with both a raw page method and an
iterator. The iterator walks cursors until empty (or until your cap):

```python
# Raw — one page
page = client.users.followers("44196397", count=200)
print(page["count"], page["cursor_bottom"])

# Iterator — walks pages
for follower in client.users.followers_iter("44196397", max_items=1000):
    process(follower)
```

The iterator accepts `max_pages` and/or `max_items`. Use them whenever
the upstream list could be huge (a top-tier account may have hundreds of
millions of followers).

---

## Error handling

Every failure surfaces as a `TwtAPIError` subclass. Catch the base for
"anything went wrong" or a specific subclass to react to one mode:

```python
from twtapi import (
    TwtAPI,
    TwtAPIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    DuplicateTweetError,
    NetworkError,
)

client = TwtAPI(api_key="tw_...")
client.set_cookies(auth_token="...", ct0="...")

try:
    client.tweets.create("hello world")
except DuplicateTweetError as e:
    print("already posted recently")
except RateLimitError as e:
    print(f"rate-limited, retry after {e.retry_after}s (scope: {e.scope})")
except AuthenticationError:
    print("bad API key")
except NotFoundError:
    print("target doesn't exist")
except NetworkError as e:
    print(f"network failure: {e}")
except TwtAPIError as e:
    print(f"other error: {e.status} {e.error} — {e}")
```

The full exception hierarchy:

| HTTP | Exception | Common `error` codes |
|---|---|---|
| 400 | `BadRequestError` | `invalid_request`, `invalid_json` |
| 401 | `AuthenticationError` | `unauthorized` |
| 402 | `BillingError` | plan / billing issues |
| 403 | `PermissionError` | `engagement_cookies_required`, `account_not_activated` |
| 404 | `NotFoundError` | `user_not_found`, `not_found` |
| 408 | `TimeoutError` | upstream timeout |
| 422 | `ValidationError` (with `DuplicateTweetError`, `TweetTooLongError` subclasses) | `duplicate_tweet`, `tweet_too_long`, `tweet_silently_dropped_likely_duplicate` |
| 429 | `RateLimitError` (carries `retry_after`, `scope`) | `rate_limited` |
| 500 | `InternalError` | `internal` |
| 502 | `UpstreamError` | `upstream_unavailable`, `twitter_call_failed` |
| 503 | `ServiceUnavailableError` | outage |
| — | `NetworkError` | DNS / TCP / TLS / read timeout |

Every exception carries `status`, `error`, the original `message`, and
the raw `body`.

---

## Rate limits

Read the latest snapshot of the API's `X-RateLimit-*` headers via
`client.last_rate_limit`:

```python
client.users.get("elonmusk")
print(client.last_rate_limit)
# RateLimit(limit=30, remaining=29, reset=1715703012)
```

The SDK doesn't actively throttle — that's your call. When the server
returns 429 the SDK retries once after `retry_after` seconds (cap 60),
unless you disabled retries with `retries=0`.

---

## Async

Same surface, `await` everywhere:

```python
import asyncio
from twtapi import TwtAPIAsync

async def main():
    async with TwtAPIAsync(api_key="tw_...") as client:
        user = await client.users.get("elonmusk")
        async for follower in client.users.followers_iter(user["user_id"], max_items=10):
            print(follower["screen_name"])

asyncio.run(main())
```

---

## Logging

Off by default. Pass a `logging.Logger` and the SDK records one record
per request with method, path, status, duration, and a masked API key:

```python
import logging
logging.basicConfig(level=logging.INFO)
client = TwtAPI(api_key="tw_...", logger=logging.getLogger("twtapi"))
```

Cookie and API-key values are masked to the first 8 characters in log
output. Request and response bodies are never logged.

---

## Troubleshooting

**`AuthenticationError(status=401, error='unauthorized')`** — your
`X-API-Key` is missing or invalid. Double-check it in the dashboard.

**`PermissionError(status=403, error='engagement_cookies_required')`** —
you called an engagement endpoint without supplying `auth_token` + `ct0`.
Use `client.set_cookies(...)` or pass them at construction.

**`RateLimitError(scope='plan')`** — you hit your plan's RPS ceiling.
Look at `e.retry_after`.

**`RateLimitError(scope='account')`** — the underlying 𝕏 account budget
was hit. Either wait, or rotate to a fresh cookie pair.

**Cookies stopped working after one call** — make sure you're reading
`client.cookies.ct0` after every chained operation, or register an
`on_ct0_rotated` callback to persist it.

---

## Examples

Runnable scripts in [`examples/`](examples/):

- `quickstart.py` — fetch a public profile
- `walk_followers.py` — pagination with caps
- `search.py` — search with `product` modes
- `login_with_2fa.py` — full login flow
- `post_a_tweet.py` — engagement
- `upload_media_and_tweet.py` — media flow

---

## License

[MIT](LICENSE).

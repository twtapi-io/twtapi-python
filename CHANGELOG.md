# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-05-14

Initial release.

### Added
- Sync `TwtAPI` and async `TwtAPIAsync` clients with the same surface.
- Read endpoints: `users.get`, `users.by_username`, `users.by_id`,
  `users.followers`, `users.tweets`, `tweets.retweets`, `tweets.quotes`,
  `tweets.comments`, `tweets.reply_ids`, `search`,
  `communities.info`, `communities.members`, `communities.check_member`.
- Engagement endpoints: `tweets.create`, `tweets.comment`, `tweets.like`,
  `tweets.retweet`, `tweets.bookmark`, `tweets.delete`,
  `users.follow`, `communities.join`, `communities.leave`,
  `communities.request_join`, `account.change_password`.
- Login flow: `auth.login`, `auth.submit_2fa`, `auth.submit_email_code`,
  `auth.csrf_token`, `auth.whoami`.
- Media upload: `media.upload(media_url)`.
- Pagination iterators (`*_iter`) for every paginated endpoint, with
  `max_pages` / `max_items` caps.
- Automatic `X-Twitter-New-Ct0` rotation with optional
  `on_ct0_rotated(new_ct0)` callback.
- Automatic cookie rotation on `account.change_password`.
- Typed exception hierarchy mapped to HTTP status: `BadRequestError`,
  `AuthenticationError`, `BillingError`, `PermissionError`,
  `NotFoundError`, `TimeoutError`, `ValidationError`
  (with `DuplicateTweetError`, `TweetTooLongError` subclasses),
  `RateLimitError` (with `retry_after` + `scope`), `InternalError`,
  `UpstreamError`, `ServiceUnavailableError`, `NetworkError`.
- Rate-limit tracking via `client.last_rate_limit`.
- Retry policy: 408 / 429 / 5xx on idempotent endpoints with exponential
  backoff. `POST /tweet` and `POST /comment` never retry on 5xx
  (double-post risk). `retries=0` disables all retries.
- Optional structured logging with API-key / cookie masking.
- Outbound proxy support via `proxy=` constructor arg.
- PEP 561 typed marker (`py.typed`).

[0.1.0]: https://github.com/twtapi/twtapi-python/releases/tag/v0.1.0

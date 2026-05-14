# Examples

Set your API key once, then run any script:

```bash
export TWTAPI_KEY="tw_..."
python examples/quickstart.py
```

| Script | What it shows | Cookies needed? |
|---|---|---|
| `quickstart.py` | Single profile fetch | No |
| `walk_followers.py` | Cursor-based pagination with `max_items` | No |
| `search.py` | `search.iter` with `product=Top` | No |
| `login_with_2fa.py` | Full login flow incl. 2FA / email challenges | No |
| `post_a_tweet.py` | Engagement + rotated `ct0` callback | Yes |
| `upload_media_and_tweet.py` | Media upload from URL → attach to tweet | Yes |

The engagement scripts read cookies from environment variables
(`X_AUTH_TOKEN`, `X_CT0`). Get them by running `login_with_2fa.py` once
and persisting the returned pair.

Get an API key at <https://twtapi.io/dashboard>.

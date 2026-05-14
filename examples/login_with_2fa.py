"""Full login flow with optional 2FA / email-code challenges.

The login flow is stateless on the server. `auth.login` returns either:
  - {status: "ok", auth_token, ct0}              — success, done
  - {status: "challenge", type, state}           — submit follow-up code

Set the credentials in environment variables; never hard-code them:

    export TWTAPI_KEY="tw_..."
    export X_USERNAME="yourhandle"
    export X_PASSWORD="..."
    python examples/login_with_2fa.py
"""

from __future__ import annotations

import os

from twtapi import TwtAPI


def main() -> None:
    api_key = os.environ.get("TWTAPI_KEY")
    username = os.environ.get("X_USERNAME")
    password = os.environ.get("X_PASSWORD")
    if not (api_key and username and password):
        raise SystemExit("Set TWTAPI_KEY, X_USERNAME, X_PASSWORD in the environment.")

    with TwtAPI(api_key=api_key) as client:
        result = client.auth.login(username, password)

        while result.get("status") == "challenge":
            kind = result.get("type")
            if kind in ("two_factor", "2fa"):
                code = input("2FA authenticator code: ").strip()
                result = client.auth.submit_2fa(result["state"], code)
            elif kind in ("email_code", "login_acid"):
                code = input("Email / SMS code: ").strip()
                result = client.auth.submit_email_code(result["state"], code)
            else:
                raise SystemExit(f"Unknown challenge type: {kind}")

        if result.get("status") != "ok":
            raise SystemExit(f"Login failed: {result}")

        auth_token = result["auth_token"]
        ct0 = result["ct0"]
        print("Login OK.")
        print(f"  auth_token: {auth_token[:8]}…")
        print(f"  ct0:        {ct0[:8]}…")

        # Use the new cookies to identify the account
        client.set_cookies(auth_token, ct0)
        me = client.auth.whoami(auth_token, ct0)
        print(f"  logged in as @{me['screen_name']}")


if __name__ == "__main__":
    main()

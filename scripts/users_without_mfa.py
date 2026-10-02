"""List Okta users who have no MFA factor enrolled.

Reads the org URL and an API token from environment variables so no secret is
ever stored in code:

    OKTA_ORG_URL    e.g. https://<your-org>.okta.com
    OKTA_API_TOKEN  an SSWS API token (read-only admin is enough)
"""
import os
import sys

import requests

ORG = os.environ.get("OKTA_ORG_URL", "").rstrip("/")
TOKEN = os.environ.get("OKTA_API_TOKEN", "")
if not ORG or not TOKEN:
    sys.exit("Set OKTA_ORG_URL and OKTA_API_TOKEN first.")

HEADERS = {"Authorization": f"SSWS {TOKEN}", "Accept": "application/json"}


def paged(url):
    """Yield every item from an Okta list endpoint, following Link headers."""
    while url:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        yield from resp.json()
        url = resp.links.get("next", {}).get("url")


def main():
    total = 0
    without_mfa = []
    for user in paged(f"{ORG}/api/v1/users?limit=200"):
        if user["status"] == "DEPROVISIONED":
            continue
        total += 1
        factors = list(paged(f"{ORG}/api/v1/users/{user['id']}/factors"))
        if not factors:
            without_mfa.append(user)

    print(f"Checked {total} active/pending users")
    if not without_mfa:
        print("Every user has at least one MFA factor enrolled.")
        return
    print(f"{len(without_mfa)} user(s) with NO MFA enrolled:")
    for user in without_mfa:
        print(f"  - {user['profile']['login']}  (status: {user['status']})")


if __name__ == "__main__":
    main()

"""HTTP client for Atlassian Cloud REST APIs."""

from __future__ import annotations

import sys
from typing import Any

import httpx

from atlassian_cli.config import Config, Profile


def _build_client(profile: Profile) -> httpx.Client:
    return httpx.Client(
        base_url=profile.site,
        auth=(profile.email, profile.get_token()),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def get_client(profile_name: str | None = None) -> httpx.Client:
    """Build an authenticated httpx client from the named profile."""
    cfg = Config.load()
    profile = cfg.get_profile(profile_name)
    return _build_client(profile)


# ── Jira REST API v3 helpers ────────────────────────────────────────────


def jira_get(client: httpx.Client, path: str, **params: Any) -> Any:
    return _request(client, "GET", f"/rest/api/3/{path}", params=params)


def jira_post(client: httpx.Client, path: str, json: Any = None) -> Any:
    return _request(client, "POST", f"/rest/api/3/{path}", json=json)


def jira_put(client: httpx.Client, path: str, json: Any = None) -> Any:
    return _request(client, "PUT", f"/rest/api/3/{path}", json=json)


def jira_delete(client: httpx.Client, path: str) -> Any:
    return _request(client, "DELETE", f"/rest/api/3/{path}")


# ── Jira Agile API 1.0 helpers ──────────────────────────────────────────


def agile_get(client: httpx.Client, path: str, **params: Any) -> Any:
    return _request(client, "GET", f"/rest/agile/1.0/{path}", params=params)


def agile_post(client: httpx.Client, path: str, json: Any = None) -> Any:
    return _request(client, "POST", f"/rest/agile/1.0/{path}", json=json)


def agile_put(client: httpx.Client, path: str, json: Any = None) -> Any:
    return _request(client, "PUT", f"/rest/agile/1.0/{path}", json=json)


def agile_delete(client: httpx.Client, path: str) -> Any:
    return _request(client, "DELETE", f"/rest/agile/1.0/{path}")


# ── Confluence REST API v2 helpers ───────────────────────────────────────


def confluence_get(client: httpx.Client, path: str, **params: Any) -> Any:
    return _request(client, "GET", f"/wiki/api/v2/{path}", params=params)


def confluence_post(client: httpx.Client, path: str, json: Any = None) -> Any:
    return _request(client, "POST", f"/wiki/api/v2/{path}", json=json)


def confluence_put(client: httpx.Client, path: str, json: Any = None) -> Any:
    return _request(client, "PUT", f"/wiki/api/v2/{path}", json=json)


def confluence_delete(client: httpx.Client, path: str) -> Any:
    return _request(client, "DELETE", f"/wiki/api/v2/{path}")


# ── Confluence REST API v1 helpers (wiki format, search) ────────────────


def confluence_v1_get(client: httpx.Client, path: str, **params: Any) -> Any:
    return _request(client, "GET", f"/wiki/rest/api/{path}", params=params)


def confluence_v1_post(client: httpx.Client, path: str, json: Any = None) -> Any:
    return _request(client, "POST", f"/wiki/rest/api/{path}", json=json)


def confluence_v1_put(client: httpx.Client, path: str, json: Any = None) -> Any:
    return _request(client, "PUT", f"/wiki/rest/api/{path}", json=json)


def confluence_search(client: httpx.Client, **params: Any) -> Any:
    return _request(client, "GET", "/wiki/rest/api/search", params=params)


# ── Internal ─────────────────────────────────────────────────────────────


def _request(
    client: httpx.Client,
    method: str,
    url: str,
    params: dict | None = None,
    json: Any = None,
) -> Any:
    # Strip None values from params
    if params:
        params = {k: v for k, v in params.items() if v is not None}

    resp = client.request(method, url, params=params, json=json)

    if resp.status_code == 204:
        return None

    if resp.is_error:
        _handle_error(resp)

    if not resp.content:
        return None
    return resp.json()


def _handle_error(resp: httpx.Response) -> None:
    """Print a helpful error message and exit."""
    try:
        body = resp.json()
        messages = body.get("errorMessages", [])
        errors = body.get("errors", {})
        detail = "; ".join(messages) if messages else str(errors) if errors else resp.text
    except Exception:
        detail = resp.text[:500] if resp.text else "(no body)"

    status = resp.status_code
    hints = {
        401: "Check your API token and email. Run: atlassian-cli auth login",
        403: "You don't have permission for this action.",
        404: "Resource not found. Check the key/ID.",
        429: "Rate limited. Wait a moment and try again.",
    }
    hint = hints.get(status, "")

    print(f"Error {status}: {detail}", file=sys.stderr)
    if hint:
        print(f"Hint: {hint}", file=sys.stderr)
    raise SystemExit(1)

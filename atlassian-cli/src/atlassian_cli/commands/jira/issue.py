"""Jira issue commands: search, view, create, edit, delete, transition, assign."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from atlassian_cli.client import get_client, jira_get, jira_post, jira_put, jira_delete
from atlassian_cli.output import render, render_single, render_message

app = typer.Typer(help="Issue commands.")


# ── helpers ──────────────────────────────────────────────────────────────


def _extract_issue_row(issue: dict) -> dict:
    f = issue.get("fields", {})
    return {
        "key": issue.get("key", ""),
        "summary": f.get("summary", ""),
        "status": (f.get("status") or {}).get("name", ""),
        "assignee": (f.get("assignee") or {}).get("displayName", "Unassigned"),
        "priority": (f.get("priority") or {}).get("name", ""),
        "type": (f.get("issuetype") or {}).get("name", ""),
    }


ISSUE_COLUMNS = ["key", "type", "status", "priority", "assignee", "summary"]


def _extract_issue_detail(issue: dict) -> dict:
    f = issue.get("fields", {})
    desc = f.get("description")
    # ADF description — extract text content
    if isinstance(desc, dict):
        desc = _adf_to_text(desc)
    return {
        "Key": issue.get("key", ""),
        "Summary": f.get("summary", ""),
        "Status": (f.get("status") or {}).get("name", ""),
        "Type": (f.get("issuetype") or {}).get("name", ""),
        "Priority": (f.get("priority") or {}).get("name", ""),
        "Assignee": (f.get("assignee") or {}).get("displayName", "Unassigned"),
        "Reporter": (f.get("reporter") or {}).get("displayName", ""),
        "Labels": ", ".join(f.get("labels", [])),
        "Created": f.get("created", ""),
        "Updated": f.get("updated", ""),
        "Description": desc or "",
    }


def _adf_to_text(adf: dict) -> str:
    """Recursively extract plain text from ADF JSON."""
    if adf.get("type") == "text":
        return adf.get("text", "")
    parts = []
    for child in adf.get("content", []):
        parts.append(_adf_to_text(child))
    return "\n".join(filter(None, parts))


# ── commands ─────────────────────────────────────────────────────────────


@app.command()
def search(
    jql: str = typer.Option(..., "--jql", "-j", help="JQL query string"),
    fields: str = typer.Option("key,summary,status,assignee,priority,issuetype", "--fields", "-f", help="Comma-separated fields"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
    count: bool = typer.Option(False, "--count", help="Only print the count"),
    output: str = typer.Option("table", "--output", "-o", help="table, json, or csv"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Auth profile"),
) -> None:
    """Search issues with JQL."""
    client = get_client(profile)
    data = jira_post(client, "search/jql", json={
        "jql": jql,
        "fields": [f.strip() for f in fields.split(",")],
        "maxResults": limit,
    })
    if count:
        print(data.get("total", 0))
        return

    issues = data.get("issues", [])
    rows = [_extract_issue_row(i) for i in issues]
    total = data.get("total", len(rows))
    title = f"Results ({len(rows)} of {total})"
    render(rows, ISSUE_COLUMNS, output=output, title=title)


@app.command()
def view(
    key: str = typer.Argument(help="Issue key (e.g. PROJ-123)"),
    fields: str = typer.Option("*navigable", "--fields", "-f", help="Fields to fetch"),
    output: str = typer.Option("table", "--output", "-o", help="table, json, or csv"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """View an issue by key."""
    client = get_client(profile)
    params = {}
    if fields != "*all":
        params["fields"] = fields
    issue = jira_get(client, f"issue/{key}", **params)
    if output == "json":
        print(json.dumps(issue, indent=2))
    else:
        render_single(_extract_issue_detail(issue), output=output)


@app.command()
def create(
    project: str = typer.Option(..., "--project", "-P", help="Project key"),
    type: str = typer.Option("Task", "--type", "-t", help="Issue type"),
    summary: str = typer.Option(..., "--summary", "-s", help="Issue summary"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Plain text description"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee email or @me"),
    labels: Optional[str] = typer.Option(None, "--labels", help="Comma-separated labels"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Priority name"),
    parent: Optional[str] = typer.Option(None, "--parent", help="Parent issue key (for sub-tasks)"),
    from_json: Optional[Path] = typer.Option(None, "--from-json", help="Create from JSON file"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Create a new issue."""
    client = get_client(profile)

    if from_json:
        payload = json.loads(from_json.read_text())
    else:
        fields_dict: dict = {
            "project": {"key": project},
            "issuetype": {"name": type},
            "summary": summary,
        }
        if description:
            fields_dict["description"] = _text_to_adf(description)
        if assignee:
            if assignee == "@me":
                fields_dict["assignee"] = {"id": _get_myself(client)}
            else:
                fields_dict["assignee"] = {"id": _find_user(client, assignee)}
        if labels:
            fields_dict["labels"] = [l.strip() for l in labels.split(",")]
        if priority:
            fields_dict["priority"] = {"name": priority}
        if parent:
            fields_dict["parent"] = {"key": parent}
        payload = {"fields": fields_dict}

    result = jira_post(client, "issue", json=payload)
    key = result.get("key", "")
    render_message(f"[green]Created {key}[/green]")


@app.command()
def edit(
    key: str = typer.Argument(help="Issue key"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a"),
    unassign: bool = typer.Option(False, "--unassign", help="Remove assignee"),
    labels: Optional[str] = typer.Option(None, "--labels", help="Set labels (comma-separated)"),
    priority: Optional[str] = typer.Option(None, "--priority"),
    from_json: Optional[Path] = typer.Option(None, "--from-json"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Edit an existing issue."""
    client = get_client(profile)

    if from_json:
        payload = json.loads(from_json.read_text())
    else:
        fields_dict: dict = {}
        if summary:
            fields_dict["summary"] = summary
        if description:
            fields_dict["description"] = _text_to_adf(description)
        if unassign:
            fields_dict["assignee"] = None
        elif assignee:
            if assignee == "@me":
                fields_dict["assignee"] = {"id": _get_myself(client)}
            else:
                fields_dict["assignee"] = {"id": _find_user(client, assignee)}
        if labels:
            fields_dict["labels"] = [l.strip() for l in labels.split(",")]
        if priority:
            fields_dict["priority"] = {"name": priority}
        if not fields_dict:
            print("Nothing to update. Specify at least one field.", file=sys.stderr)
            raise SystemExit(1)
        payload = {"fields": fields_dict}

    jira_put(client, f"issue/{key}", json=payload)
    render_message(f"[green]Updated {key}[/green]")


@app.command()
def delete(
    key: str = typer.Argument(help="Issue key"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Delete an issue."""
    if not yes:
        typer.confirm(f"Delete {key}?", abort=True)
    client = get_client(profile)
    jira_delete(client, f"issue/{key}")
    render_message(f"[yellow]Deleted {key}[/yellow]")


@app.command()
def transition(
    key: str = typer.Argument(help="Issue key"),
    status: str = typer.Option(..., "--status", "-s", help="Target status name"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Transition an issue to a new status."""
    client = get_client(profile)

    # Get available transitions
    data = jira_get(client, f"issue/{key}/transitions")
    transitions = data.get("transitions", [])

    # Find matching transition (case-insensitive)
    match = None
    for t in transitions:
        if t["name"].lower() == status.lower() or t.get("to", {}).get("name", "").lower() == status.lower():
            match = t
            break

    if not match:
        available = ", ".join(
            f"{t['name']} → {t.get('to', {}).get('name', '?')}" for t in transitions
        )
        print(f"No transition to '{status}'. Available: {available}", file=sys.stderr)
        raise SystemExit(1)

    jira_post(client, f"issue/{key}/transitions", json={"transition": {"id": match["id"]}})
    render_message(f"[green]{key} → {match.get('to', {}).get('name', status)}[/green]")


@app.command()
def assign(
    key: str = typer.Argument(help="Issue key"),
    user: str = typer.Option(None, "--user", "-u", help="Assignee email or @me"),
    unassign: bool = typer.Option(False, "--unassign", help="Remove assignee"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Assign or unassign an issue."""
    client = get_client(profile)

    if unassign:
        jira_put(client, f"issue/{key}/assignee", json={"accountId": None})
        render_message(f"[green]Unassigned {key}[/green]")
        return

    if not user:
        print("Specify --user or --unassign.", file=sys.stderr)
        raise SystemExit(1)

    if user == "@me":
        account_id = _get_myself(client)
    else:
        account_id = _find_user(client, user)

    jira_put(client, f"issue/{key}/assignee", json={"accountId": account_id})
    render_message(f"[green]Assigned {key} to {user}[/green]")


# ── user lookup helpers ──────────────────────────────────────────────────


def _get_myself(client) -> str:
    data = jira_get(client, "myself")
    return data["accountId"]


def _find_user(client, query: str) -> str:
    users = jira_get(client, "user/search", query=query)
    if not users:
        print(f"No user found for '{query}'", file=sys.stderr)
        raise SystemExit(1)
    return users[0]["accountId"]


def _text_to_adf(text: str) -> dict:
    """Convert plain text to minimal ADF JSON."""
    paragraphs = []
    for line in text.split("\n"):
        paragraphs.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": line}] if line else [],
        })
    return {"version": 1, "type": "doc", "content": paragraphs}

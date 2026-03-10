"""Jira issue link commands."""

from __future__ import annotations

from typing import Optional

import typer

from atlassian_cli.client import get_client, jira_get, jira_post
from atlassian_cli.output import render, render_message

app = typer.Typer(help="Issue link commands.")


@app.command("add")
def add_link(
    key: str = typer.Argument(help="Source issue key"),
    target: str = typer.Option(..., "--target", "-t", help="Target issue key"),
    type: str = typer.Option("Relates", "--type", help="Link type name (e.g. Blocks, Relates)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Create a link between two issues."""
    client = get_client(profile)
    jira_post(client, "issueLink", json={
        "type": {"name": type},
        "inwardIssue": {"key": target},
        "outwardIssue": {"key": key},
    })
    render_message(f"[green]Linked {key} → {target} ({type})[/green]")


@app.command("list")
def list_links(
    key: str = typer.Argument(help="Issue key"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List links on an issue."""
    client = get_client(profile)
    issue = jira_get(client, f"issue/{key}", fields="issuelinks")
    links = issue.get("fields", {}).get("issuelinks", [])

    rows = []
    for link in links:
        link_type = link.get("type", {}).get("name", "")
        if "outwardIssue" in link:
            direction = link["type"].get("outward", "relates to")
            other = link["outwardIssue"]
        else:
            direction = link["type"].get("inward", "is related to")
            other = link.get("inwardIssue", {})
        rows.append({
            "type": link_type,
            "direction": direction,
            "key": other.get("key", ""),
            "summary": (other.get("fields") or {}).get("summary", ""),
            "status": ((other.get("fields") or {}).get("status") or {}).get("name", ""),
        })

    render(rows, ["type", "direction", "key", "status", "summary"], output=output, title=f"Links on {key}")


@app.command("types")
def link_types(
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List available link types."""
    client = get_client(profile)
    data = jira_get(client, "issueLinkType")
    link_types_list = data.get("issueLinkTypes", [])
    rows = [
        {
            "name": lt.get("name", ""),
            "inward": lt.get("inward", ""),
            "outward": lt.get("outward", ""),
        }
        for lt in link_types_list
    ]
    render(rows, ["name", "inward", "outward"], output=output)

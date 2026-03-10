"""Confluence space commands."""

from __future__ import annotations

import json
from typing import Optional

import typer

from atlassian_cli.client import get_client, confluence_get, confluence_post
from atlassian_cli.output import render, render_single, render_message

app = typer.Typer(help="Space commands.")


@app.command("list")
def list_spaces(
    type: Optional[str] = typer.Option(None, "--type", "-t", help="global or personal"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="current or archived"),
    limit: int = typer.Option(25, "--limit", "-l"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List Confluence spaces."""
    client = get_client(profile)
    params = {"limit": limit}
    if type:
        params["type"] = type
    if status:
        params["status"] = status

    data = confluence_get(client, "spaces", **params)
    spaces = data.get("results", [])
    rows = [
        {
            "id": str(s.get("id", "")),
            "key": s.get("key", ""),
            "name": s.get("name", ""),
            "type": s.get("type", ""),
            "status": s.get("status", ""),
        }
        for s in spaces
    ]
    render(rows, ["id", "key", "name", "type", "status"], output=output, title="Spaces")


@app.command("view")
def view_space(
    id: str = typer.Argument(help="Space ID"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """View a Confluence space by ID."""
    client = get_client(profile)
    space = confluence_get(client, f"spaces/{id}")
    if output == "json":
        print(json.dumps(space, indent=2))
        return
    detail = {
        "ID": str(space.get("id", "")),
        "Key": space.get("key", ""),
        "Name": space.get("name", ""),
        "Type": space.get("type", ""),
        "Status": space.get("status", ""),
        "Description": (space.get("description") or {}).get("plain", {}).get("value", ""),
    }
    render_single(detail, output=output)


@app.command("create")
def create_space(
    key: str = typer.Option(..., "--key", "-k", help="Space key"),
    name: str = typer.Option(..., "--name", "-n", help="Space name"),
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Create a new Confluence space."""
    client = get_client(profile)
    payload: dict = {"key": key, "name": name}
    if description:
        payload["description"] = {
            "plain": {"value": description, "representation": "plain"},
        }

    result = confluence_post(client, "spaces", json=payload)
    render_message(f"[green]Created space '{name}' (key: {result.get('key')})[/green]")

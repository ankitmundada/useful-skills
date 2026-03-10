"""Jira board commands."""

from __future__ import annotations

from typing import Optional

import typer

from atlassian_cli.client import get_client, agile_get
from atlassian_cli.output import render, render_single

app = typer.Typer(help="Board commands.")


@app.command("list")
def list_boards(
    project: Optional[str] = typer.Option(None, "--project", "-P", help="Filter by project key"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="scrum, kanban, or simple"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter by board name"),
    limit: int = typer.Option(10, "--limit", "-l"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List boards."""
    client = get_client(profile)
    params = {"maxResults": limit}
    if project:
        params["projectKeyOrId"] = project
    if type:
        params["type"] = type
    if name:
        params["name"] = name

    data = agile_get(client, "board", **params)
    boards = data.get("values", [])
    rows = [
        {
            "id": str(b.get("id", "")),
            "name": b.get("name", ""),
            "type": b.get("type", ""),
        }
        for b in boards
    ]
    render(rows, ["id", "name", "type"], output=output, title="Boards")


@app.command("view")
def view_board(
    id: int = typer.Argument(help="Board ID"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """View a board by ID."""
    client = get_client(profile)
    board = agile_get(client, f"board/{id}")
    detail = {
        "ID": str(board.get("id", "")),
        "Name": board.get("name", ""),
        "Type": board.get("type", ""),
        "Project": (board.get("location") or {}).get("projectKey", ""),
    }
    render_single(detail, output=output)


@app.command("sprints")
def board_sprints(
    id: int = typer.Argument(help="Board ID"),
    state: str = typer.Option("active", "--state", "-s", help="active, closed, future (comma-separated)"),
    limit: int = typer.Option(10, "--limit", "-l"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List sprints for a board."""
    client = get_client(profile)
    data = agile_get(client, f"board/{id}/sprint", state=state, maxResults=limit)
    sprints = data.get("values", [])
    rows = [
        {
            "id": str(s.get("id", "")),
            "name": s.get("name", ""),
            "state": s.get("state", ""),
            "start": (s.get("startDate") or "")[:10],
            "end": (s.get("endDate") or "")[:10],
            "goal": s.get("goal", ""),
        }
        for s in sprints
    ]
    render(rows, ["id", "name", "state", "start", "end", "goal"], output=output, title="Sprints")

"""Jira sprint commands."""

from __future__ import annotations

from typing import Optional

import typer

from atlassian_cli.client import (
    get_client, agile_get, agile_post, agile_put, agile_delete,
)
from atlassian_cli.output import render, render_single, render_message

app = typer.Typer(help="Sprint commands.")


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


@app.command("view")
def view_sprint(
    id: int = typer.Argument(help="Sprint ID"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """View a sprint by ID."""
    client = get_client(profile)
    sprint = agile_get(client, f"sprint/{id}")
    detail = {
        "ID": str(sprint.get("id", "")),
        "Name": sprint.get("name", ""),
        "State": sprint.get("state", ""),
        "Start": (sprint.get("startDate") or "")[:10],
        "End": (sprint.get("endDate") or "")[:10],
        "Goal": sprint.get("goal", ""),
        "Board": str(sprint.get("originBoardId", "")),
    }
    render_single(detail, output=output)


@app.command("issues")
def sprint_issues(
    id: int = typer.Argument(help="Sprint ID"),
    jql: Optional[str] = typer.Option(None, "--jql", "-j", help="Additional JQL filter"),
    limit: int = typer.Option(50, "--limit", "-l"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List issues in a sprint."""
    client = get_client(profile)
    params = {"maxResults": limit}
    if jql:
        params["jql"] = jql
    data = agile_get(client, f"sprint/{id}/issue", **params)
    issues = data.get("issues", [])
    rows = [_extract_issue_row(i) for i in issues]
    render(rows, ISSUE_COLUMNS, output=output, title=f"Sprint {id} Issues")


@app.command("create")
def create_sprint(
    board: int = typer.Option(..., "--board", "-b", help="Board ID"),
    name: str = typer.Option(..., "--name", "-n", help="Sprint name"),
    goal: Optional[str] = typer.Option(None, "--goal", "-g", help="Sprint goal"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Create a new sprint."""
    client = get_client(profile)
    payload: dict = {"name": name, "originBoardId": board}
    if goal:
        payload["goal"] = goal
    if start:
        payload["startDate"] = start
    if end:
        payload["endDate"] = end

    result = agile_post(client, "sprint", json=payload)
    render_message(f"[green]Created sprint '{name}' (id: {result.get('id')})[/green]")


@app.command("update")
def update_sprint(
    id: int = typer.Argument(help="Sprint ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n"),
    goal: Optional[str] = typer.Option(None, "--goal", "-g"),
    state: Optional[str] = typer.Option(None, "--state", "-s", help="active, closed, or future"),
    start: Optional[str] = typer.Option(None, "--start"),
    end: Optional[str] = typer.Option(None, "--end"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Update a sprint (name, goal, state, dates)."""
    client = get_client(profile)
    payload: dict = {}
    if name:
        payload["name"] = name
    if goal:
        payload["goal"] = goal
    if state:
        payload["state"] = state
    if start:
        payload["startDate"] = start
    if end:
        payload["endDate"] = end

    if not payload:
        render_message("[yellow]Nothing to update.[/yellow]")
        return

    agile_put(client, f"sprint/{id}", json=payload)
    render_message(f"[green]Updated sprint {id}[/green]")


@app.command("delete")
def delete_sprint(
    id: int = typer.Argument(help="Sprint ID"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Delete a sprint."""
    if not yes:
        typer.confirm(f"Delete sprint {id}?", abort=True)
    client = get_client(profile)
    agile_delete(client, f"sprint/{id}")
    render_message(f"[yellow]Deleted sprint {id}[/yellow]")


@app.command("move")
def move_issues(
    id: int = typer.Argument(help="Target sprint ID"),
    keys: str = typer.Option(..., "--keys", "-k", help="Issue keys (comma-separated)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Move issues into a sprint."""
    client = get_client(profile)
    issue_keys = [k.strip() for k in keys.split(",")]
    agile_post(client, f"sprint/{id}/issue", json={"issues": issue_keys})
    render_message(f"[green]Moved {len(issue_keys)} issue(s) to sprint {id}[/green]")

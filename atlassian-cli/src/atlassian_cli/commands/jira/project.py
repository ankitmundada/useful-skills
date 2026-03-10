"""Jira project commands."""

from __future__ import annotations

import json
from typing import Optional

import typer

from atlassian_cli.client import get_client, jira_get
from atlassian_cli.output import render, render_single

app = typer.Typer(help="Project commands.")


@app.command("list")
def list_projects(
    recent: int = typer.Option(0, "--recent", "-r", help="Show N recently viewed projects"),
    limit: int = typer.Option(20, "--limit", "-l"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List projects."""
    client = get_client(profile)
    params = {"maxResults": limit}
    if recent:
        params["recent"] = recent
        params["maxResults"] = recent
    data = jira_get(client, "project/search", **params)
    projects = data.get("values", [])
    rows = [
        {
            "key": p.get("key", ""),
            "name": p.get("name", ""),
            "type": p.get("projectTypeKey", ""),
            "lead": (p.get("lead") or {}).get("displayName", ""),
        }
        for p in projects
    ]
    render(rows, ["key", "name", "type", "lead"], output=output, title="Projects")


@app.command("view")
def view_project(
    key: str = typer.Argument(help="Project key"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """View a project by key."""
    client = get_client(profile)
    project = jira_get(client, f"project/{key}")
    if output == "json":
        print(json.dumps(project, indent=2))
        return
    detail = {
        "Key": project.get("key", ""),
        "Name": project.get("name", ""),
        "Type": project.get("projectTypeKey", ""),
        "Lead": (project.get("lead") or {}).get("displayName", ""),
        "Description": project.get("description", "") or "",
        "URL": project.get("self", ""),
    }
    render_single(detail, output=output)

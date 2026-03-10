"""Confluence blog post commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from atlassian_cli.client import get_client, confluence_get, confluence_post
from atlassian_cli.output import render, render_single, render_message

app = typer.Typer(help="Blog post commands.")


@app.command("list")
def list_blogs(
    space_id: Optional[str] = typer.Option(None, "--space", "-s", help="Space ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Filter by title"),
    limit: int = typer.Option(10, "--limit", "-l"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List blog posts."""
    client = get_client(profile)
    params = {"limit": limit}
    if space_id:
        params["space-id"] = space_id
    if title:
        params["title"] = title

    data = confluence_get(client, "blogposts", **params)
    posts = data.get("results", [])
    rows = [
        {
            "id": str(b.get("id", "")),
            "title": b.get("title", ""),
            "status": b.get("status", ""),
            "created": (b.get("createdAt") or "")[:10],
        }
        for b in posts
    ]
    render(rows, ["id", "title", "status", "created"], output=output, title="Blog Posts")


@app.command("view")
def view_blog(
    id: str = typer.Argument(help="Blog post ID"),
    body_format: str = typer.Option("storage", "--body-format", help="storage, atlas_doc_format, or view"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """View a blog post by ID."""
    client = get_client(profile)
    post = confluence_get(client, f"blogposts/{id}", **{"body-format": body_format})
    if output == "json":
        print(json.dumps(post, indent=2))
        return
    body_content = ""
    body = post.get("body", {})
    if body_format in body:
        body_content = body[body_format].get("value", "")
    detail = {
        "ID": post.get("id", ""),
        "Title": post.get("title", ""),
        "Status": post.get("status", ""),
        "Space ID": str(post.get("spaceId", "")),
        "Created": post.get("createdAt", ""),
        "Body": body_content[:500] if body_content else "(empty)",
    }
    render_single(detail, output=output)


@app.command("create")
def create_blog(
    space_id: str = typer.Option(..., "--space", "-s", help="Space ID"),
    title: str = typer.Option(..., "--title", "-t", help="Blog post title"),
    body: Optional[str] = typer.Option(None, "--body", "-b", help="Body (HTML/storage format)"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", help="Read body from file"),
    status: str = typer.Option("current", "--status", help="current or draft"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Create a new blog post."""
    client = get_client(profile)
    content = body or ""
    if body_file:
        content = body_file.read_text()

    payload: dict = {
        "spaceId": space_id,
        "title": title,
        "status": status,
        "body": {
            "representation": "storage",
            "value": content,
        },
    }

    result = confluence_post(client, "blogposts", json=payload)
    render_message(f"[green]Created blog post '{title}' (id: {result.get('id')})[/green]")

"""Confluence page commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from atlassian_cli.client import (
    get_client,
    confluence_get,
    confluence_post,
    confluence_put,
    confluence_v1_post,
    confluence_v1_put,
    confluence_search,
)
from atlassian_cli.output import render, render_single, render_message, html_to_markdown

app = typer.Typer(help="Page commands.")


@app.command("view")
def view_page(
    id: str = typer.Argument(help="Page ID"),
    body_format: str = typer.Option("markdown", "--body-format", help="markdown (default), storage, atlas_doc_format, or view"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """View a Confluence page by ID."""
    client = get_client(profile)

    # For markdown output, fetch the rendered HTML view and convert
    api_format = "view" if body_format == "markdown" else body_format
    page = confluence_get(client, f"pages/{id}", **{"body-format": api_format})

    if output == "json":
        print(json.dumps(page, indent=2))
        return

    body_content = ""
    body = page.get("body", {})
    if api_format in body:
        raw = body[api_format].get("value", "")
        body_content = html_to_markdown(raw) if body_format == "markdown" else raw

    detail = {
        "ID": page.get("id", ""),
        "Title": page.get("title", ""),
        "Status": page.get("status", ""),
        "Space ID": (page.get("spaceId") or ""),
        "Version": str((page.get("version") or {}).get("number", "")),
        "Body": body_content[:500] if body_content else "(empty)",
    }
    render_single(detail, output=output)


@app.command("create")
def create_page(
    space_id: str = typer.Option(..., "--space", "-s", help="Space ID"),
    title: str = typer.Option(..., "--title", "-t", help="Page title"),
    body: Optional[str] = typer.Option(None, "--body", "-b", help="Page body content"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", help="Read body from file"),
    parent_id: Optional[str] = typer.Option(None, "--parent", help="Parent page ID"),
    format: str = typer.Option("wiki", "--format", "-f", help="Body format: wiki (default), storage, or atlas_doc_format"),
    status: str = typer.Option("current", "--status", help="current or draft"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Create a new Confluence page."""
    client = get_client(profile)
    content = body or ""
    if body_file:
        content = body_file.read_text()

    if format == "wiki":
        # v1 API properly converts wiki markup to storage format
        payload: dict = {
            "type": "page",
            "title": title,
            "space": {"id": space_id},
            "status": status,
            "body": {
                "wiki": {
                    "value": content,
                    "representation": "wiki",
                },
            },
        }
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
        result = confluence_v1_post(client, "content", json=payload)
    else:
        payload = {
            "spaceId": space_id,
            "title": title,
            "status": status,
            "body": {
                "representation": format,
                "value": content,
            },
        }
        if parent_id:
            payload["parentId"] = parent_id
        result = confluence_post(client, "pages", json=payload)

    render_message(f"[green]Created page '{title}' (id: {result.get('id')})[/green]")


@app.command("edit")
def edit_page(
    id: str = typer.Argument(help="Page ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    body: Optional[str] = typer.Option(None, "--body", "-b"),
    body_file: Optional[Path] = typer.Option(None, "--body-file"),
    format: str = typer.Option("wiki", "--format", "-f", help="Body format: wiki (default), storage, or atlas_doc_format"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Edit an existing Confluence page."""
    client = get_client(profile)

    # Fetch current page to get version number and title
    current = confluence_get(client, f"pages/{id}")
    version = (current.get("version") or {}).get("number", 1)
    current_title = current.get("title", "")

    content = body
    if body_file:
        content = body_file.read_text()

    if format == "wiki":
        # v1 API properly converts wiki markup to storage format
        payload: dict = {
            "type": "page",
            "title": title or current_title,
            "version": {"number": version + 1},
        }
        if content is not None:
            payload["body"] = {
                "wiki": {
                    "value": content,
                    "representation": "wiki",
                },
            }
        confluence_v1_put(client, f"content/{id}", json=payload)
    else:
        payload = {
            "id": id,
            "status": "current",
            "version": {"number": version + 1},
            "title": title or current_title,
        }
        if content is not None:
            payload["body"] = {
                "representation": format,
                "value": content,
            }
        confluence_put(client, f"pages/{id}", json=payload)

    render_message(f"[green]Updated page {id}[/green]")


@app.command("search")
def search_pages(
    cql: str = typer.Option(..., "--cql", "-q", help="CQL query string"),
    limit: int = typer.Option(10, "--limit", "-l"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Search Confluence content with CQL."""
    client = get_client(profile)
    data = confluence_search(client, cql=cql, limit=limit)
    results = data.get("results", [])
    rows = []
    for r in results:
        content = r.get("content", {}) or r
        rows.append({
            "id": content.get("id", ""),
            "type": content.get("type", r.get("entityType", "")),
            "title": content.get("title", r.get("title", "")),
            "space": (content.get("space") or {}).get("key", ""),
            "url": r.get("url", ""),
        })
    render(rows, ["id", "type", "title", "space"], output=output, title="Search Results")

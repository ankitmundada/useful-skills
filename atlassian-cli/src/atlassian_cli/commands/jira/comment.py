"""Jira issue comment commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from atlassian_cli.client import get_client, jira_get, jira_post, jira_put, jira_delete
from atlassian_cli.output import render, render_message

app = typer.Typer(help="Issue comment commands.")


def _extract_comment_row(c: dict) -> dict:
    body = c.get("body", "")
    if isinstance(body, dict):
        body = _adf_to_text(body)
    return {
        "id": c.get("id", ""),
        "author": (c.get("author") or {}).get("displayName", ""),
        "created": c.get("created", "")[:16],
        "body": body[:100],
    }


def _adf_to_text(adf: dict) -> str:
    if adf.get("type") == "text":
        return adf.get("text", "")
    parts = []
    for child in adf.get("content", []):
        parts.append(_adf_to_text(child))
    return " ".join(filter(None, parts))


COMMENT_COLUMNS = ["id", "author", "created", "body"]


@app.command("add")
def add_comment(
    key: str = typer.Argument(help="Issue key"),
    body: Optional[str] = typer.Option(None, "--body", "-b", help="Comment text"),
    body_file: Optional[Path] = typer.Option(None, "--body-file", help="Read comment from file"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Add a comment to an issue."""
    client = get_client(profile)

    text = _resolve_body(body, body_file)

    # Try to parse as ADF JSON, otherwise wrap as ADF
    try:
        adf = json.loads(text)
        if adf.get("type") == "doc":
            payload = {"body": adf}
        else:
            payload = {"body": _text_to_adf(text)}
    except (json.JSONDecodeError, AttributeError):
        payload = {"body": _text_to_adf(text)}

    result = jira_post(client, f"issue/{key}/comment", json=payload)
    render_message(f"[green]Comment added to {key} (id: {result.get('id')})[/green]")


@app.command("list")
def list_comments(
    key: str = typer.Argument(help="Issue key"),
    limit: int = typer.Option(10, "--limit", "-l"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """List comments on an issue."""
    client = get_client(profile)
    data = jira_get(client, f"issue/{key}/comment", maxResults=limit, orderBy="-created")
    comments = data.get("comments", [])
    rows = [_extract_comment_row(c) for c in comments]
    render(rows, COMMENT_COLUMNS, output=output, title=f"Comments on {key}")


@app.command("edit")
def edit_comment(
    key: str = typer.Argument(help="Issue key"),
    id: str = typer.Option(..., "--id", help="Comment ID"),
    body: Optional[str] = typer.Option(None, "--body", "-b"),
    body_file: Optional[Path] = typer.Option(None, "--body-file"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Edit an existing comment."""
    client = get_client(profile)
    text = _resolve_body(body, body_file)
    jira_put(client, f"issue/{key}/comment/{id}", json={"body": _text_to_adf(text)})
    render_message(f"[green]Comment {id} updated on {key}[/green]")


@app.command("delete")
def delete_comment(
    key: str = typer.Argument(help="Issue key"),
    id: str = typer.Option(..., "--id", help="Comment ID"),
    yes: bool = typer.Option(False, "--yes", "-y"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Delete a comment."""
    if not yes:
        typer.confirm(f"Delete comment {id} on {key}?", abort=True)
    client = get_client(profile)
    jira_delete(client, f"issue/{key}/comment/{id}")
    render_message(f"[yellow]Deleted comment {id} on {key}[/yellow]")


# ── helpers ──────────────────────────────────────────────────────────────

import sys

def _resolve_body(body: str | None, body_file: Path | None) -> str:
    if body_file:
        return body_file.read_text()
    if body:
        return body
    print("Specify --body or --body-file.", file=sys.stderr)
    raise SystemExit(1)


def _text_to_adf(text: str) -> dict:
    paragraphs = []
    for line in text.split("\n"):
        paragraphs.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": line}] if line else [],
        })
    return {"version": 1, "type": "doc", "content": paragraphs}

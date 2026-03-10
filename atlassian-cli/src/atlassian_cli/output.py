"""Output formatting: table, JSON, CSV."""

from __future__ import annotations

import csv
import io
import json
import sys
from typing import Any, Sequence

from rich.console import Console
from rich.table import Table

console = Console()


def render(
    rows: Sequence[dict[str, Any]],
    columns: list[str],
    *,
    output: str = "table",
    title: str | None = None,
) -> None:
    """Render a list of row dicts in the chosen format.

    Args:
        rows: List of dicts, each representing a row.
        columns: Column keys to display, in order.
        output: "table" (Rich table), "json", or "csv".
        title: Optional table title (table format only).
    """
    if output == "json":
        _render_json(rows, columns)
    elif output == "csv":
        _render_csv(rows, columns)
    else:
        _render_table(rows, columns, title=title)


def render_single(data: dict[str, Any], *, output: str = "table") -> None:
    """Render a single item as key-value pairs."""
    if output == "json":
        print(json.dumps(data, indent=2))
        return

    if output == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=list(data.keys()))
        writer.writeheader()
        writer.writerow(data)
        return

    # Table: key-value layout
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")
    for key, value in data.items():
        table.add_row(key, _truncate(str(value), 120))
    console.print(table)


def render_message(msg: str) -> None:
    """Print a simple success/info message."""
    console.print(msg)


def _render_table(
    rows: Sequence[dict[str, Any]],
    columns: list[str],
    *,
    title: str | None = None,
) -> None:
    if not rows:
        console.print("[dim]No results.[/dim]")
        return

    table = Table(title=title, show_lines=False)
    for col in columns:
        table.add_column(col, overflow="fold")
    for row in rows:
        table.add_row(*(str(row.get(col, "")) for col in columns))
    console.print(table)


def _render_json(rows: Sequence[dict[str, Any]], columns: list[str]) -> None:
    # Only include requested columns
    filtered = [{col: row.get(col) for col in columns} for row in rows]
    print(json.dumps(filtered, indent=2))


def _render_csv(rows: Sequence[dict[str, Any]], columns: list[str]) -> None:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({col: row.get(col) for col in columns})
    print(buf.getvalue(), end="")


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"

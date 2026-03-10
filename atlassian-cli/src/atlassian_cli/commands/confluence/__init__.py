"""Confluence command group."""

import typer

from atlassian_cli.commands.confluence.page import app as page_app
from atlassian_cli.commands.confluence.space import app as space_app
from atlassian_cli.commands.confluence.blog import app as blog_app

app = typer.Typer(help="Confluence commands.")

app.add_typer(page_app, name="page")
app.add_typer(space_app, name="space")
app.add_typer(blog_app, name="blog")

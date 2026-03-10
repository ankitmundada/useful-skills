"""atlassian-cli — open-source CLI for Jira and Confluence."""

import typer

from atlassian_cli.commands.auth import app as auth_app
from atlassian_cli.commands.jira import app as jira_app
from atlassian_cli.commands.confluence import app as confluence_app

app = typer.Typer(
    name="atlassian-cli",
    help="Open-source CLI for Jira and Confluence.",
    no_args_is_help=True,
)

app.add_typer(auth_app, name="auth")
app.add_typer(jira_app, name="jira")
app.add_typer(confluence_app, name="confluence")


def main() -> None:
    app()

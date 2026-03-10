"""Jira command group."""

import typer

from atlassian_cli.commands.jira.issue import app as issue_app
from atlassian_cli.commands.jira.comment import app as comment_app
from atlassian_cli.commands.jira.link import app as link_app
from atlassian_cli.commands.jira.board import app as board_app
from atlassian_cli.commands.jira.sprint import app as sprint_app
from atlassian_cli.commands.jira.project import app as project_app

app = typer.Typer(help="Jira commands.")

# issue is the main group; comment and link are nested under it
issue_app.add_typer(comment_app, name="comment")
issue_app.add_typer(link_app, name="link")

app.add_typer(issue_app, name="issue")
app.add_typer(board_app, name="board")
app.add_typer(sprint_app, name="sprint")
app.add_typer(project_app, name="project")

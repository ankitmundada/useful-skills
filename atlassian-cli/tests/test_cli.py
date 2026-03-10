"""Tests for CLI command wiring and arg parsing (no API calls)."""

from __future__ import annotations

from typer.testing import CliRunner

from atlassian_cli.app import app

runner = CliRunner()


class TestTopLevel:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "auth" in result.output
        assert "jira" in result.output
        assert "confluence" in result.output

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage" in result.output


class TestJiraSubcommands:
    def test_jira_help(self):
        result = runner.invoke(app, ["jira", "--help"])
        assert result.exit_code == 0
        assert "issue" in result.output
        assert "board" in result.output
        assert "sprint" in result.output
        assert "project" in result.output

    def test_issue_help(self):
        result = runner.invoke(app, ["jira", "issue", "--help"])
        assert result.exit_code == 0
        assert "search" in result.output
        assert "view" in result.output
        assert "create" in result.output
        assert "edit" in result.output
        assert "delete" in result.output
        assert "transition" in result.output
        assert "assign" in result.output
        assert "comment" in result.output
        assert "link" in result.output

    def test_comment_help(self):
        result = runner.invoke(app, ["jira", "issue", "comment", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "list" in result.output
        assert "edit" in result.output
        assert "delete" in result.output

    def test_link_help(self):
        result = runner.invoke(app, ["jira", "issue", "link", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "list" in result.output
        assert "types" in result.output

    def test_board_help(self):
        result = runner.invoke(app, ["jira", "board", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "view" in result.output
        assert "sprints" in result.output

    def test_sprint_help(self):
        result = runner.invoke(app, ["jira", "sprint", "--help"])
        assert result.exit_code == 0
        assert "view" in result.output
        assert "issues" in result.output
        assert "create" in result.output
        assert "update" in result.output
        assert "delete" in result.output
        assert "move" in result.output

    def test_project_help(self):
        result = runner.invoke(app, ["jira", "project", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "view" in result.output


class TestConfluenceSubcommands:
    def test_confluence_help(self):
        result = runner.invoke(app, ["confluence", "--help"])
        assert result.exit_code == 0
        assert "page" in result.output
        assert "space" in result.output
        assert "blog" in result.output

    def test_page_help(self):
        result = runner.invoke(app, ["confluence", "page", "--help"])
        assert result.exit_code == 0
        assert "view" in result.output
        assert "create" in result.output
        assert "edit" in result.output
        assert "search" in result.output

    def test_space_help(self):
        result = runner.invoke(app, ["confluence", "space", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "view" in result.output
        assert "create" in result.output

    def test_blog_help(self):
        result = runner.invoke(app, ["confluence", "blog", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "view" in result.output
        assert "create" in result.output


class TestAuthCommands:
    def test_auth_help(self):
        result = runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output

    def test_auth_status_no_profiles(self):
        result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "No profiles" in result.output

    def test_auth_login_and_status(self):
        result = runner.invoke(app, [
            "auth", "login",
            "--profile", "test",
            "--site", "https://test.atlassian.net",
            "--email", "a@b.com",
            "--token", "tok123",
        ])
        assert result.exit_code == 0
        assert "Saved" in result.output

        result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "test" in result.output
        assert "test.atlassian.net" in result.output

    def test_auth_login_normalizes_url(self):
        result = runner.invoke(app, [
            "auth", "login",
            "--site", "team.atlassian.net/",
            "--email", "a@b.com",
            "--token", "t",
        ])
        assert result.exit_code == 0
        assert "https://team.atlassian.net" in result.output

    def test_auth_logout(self):
        # Login first
        runner.invoke(app, [
            "auth", "login",
            "--site", "https://x.net",
            "--email", "a@b.com",
            "--token", "t",
        ])
        result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_auth_logout_nonexistent(self):
        result = runner.invoke(app, ["auth", "logout", "--profile", "nope"])
        assert result.exit_code == 1

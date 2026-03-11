"""Tests for Confluence page/blog commands: wiki write, markdown read."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from atlassian_cli.app import app
from atlassian_cli.output import html_to_markdown

runner = CliRunner()


# ── html_to_markdown tests ─────────────────────────────────────────────


class TestHtmlToMarkdown:
    def test_headings(self):
        assert html_to_markdown("<h1>Title</h1>") == "# Title"

    def test_bold_italic(self):
        result = html_to_markdown("<p>This is <strong>bold</strong> and <em>italic</em>.</p>")
        assert "**bold**" in result
        assert "*italic*" in result

    def test_unordered_list(self):
        html = "<ul><li>One</li><li>Two</li></ul>"
        result = html_to_markdown(html)
        assert "* One" in result or "- One" in result
        assert "* Two" in result or "- Two" in result

    def test_ordered_list(self):
        html = "<ol><li>First</li><li>Second</li></ol>"
        result = html_to_markdown(html)
        assert "1." in result
        assert "First" in result

    def test_table(self):
        html = (
            "<table><tbody>"
            "<tr><th>A</th><th>B</th></tr>"
            "<tr><td>1</td><td>2</td></tr>"
            "</tbody></table>"
        )
        result = html_to_markdown(html)
        assert "A" in result
        assert "B" in result
        assert "1" in result
        assert "---" in result  # table separator

    def test_link(self):
        html = '<a href="https://example.com">Click</a>'
        result = html_to_markdown(html)
        assert "[Click]" in result
        assert "https://example.com" in result

    def test_empty_string(self):
        assert html_to_markdown("") == ""

    def test_plain_text(self):
        assert html_to_markdown("Just text") == "Just text"

    def test_strips_confluence_ids(self):
        html = '<h1 id="PageTitle-Heading">Heading</h1>'
        result = html_to_markdown(html)
        assert result == "# Heading"
        assert "PageTitle" not in result


# ── Page view (markdown default) ────────────────────────────────────────


MOCK_PAGE_RESPONSE = {
    "id": "12345",
    "title": "Test Page",
    "status": "current",
    "spaceId": "99",
    "version": {"number": 1},
    "body": {
        "view": {
            "value": "<h1>Hello</h1><p>This is <strong>bold</strong>.</p>",
        },
    },
}


class TestPageViewMarkdown:
    @patch("atlassian_cli.commands.confluence.page.get_client")
    @patch("atlassian_cli.commands.confluence.page.confluence_get")
    def test_default_format_is_markdown(self, mock_get, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_get.return_value = MOCK_PAGE_RESPONSE

        result = runner.invoke(app, ["confluence", "page", "view", "12345"])
        assert result.exit_code == 0

        # Should have fetched "view" format from API (not "storage")
        call_kwargs = mock_get.call_args
        assert call_kwargs[1].get("body-format") == "view"

        # Output should contain markdown, not HTML
        assert "# Hello" in result.output
        assert "**bold**" in result.output
        assert "<h1>" not in result.output

    @patch("atlassian_cli.commands.confluence.page.get_client")
    @patch("atlassian_cli.commands.confluence.page.confluence_get")
    def test_storage_format_passthrough(self, mock_get, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_get.return_value = {
            **MOCK_PAGE_RESPONSE,
            "body": {"storage": {"value": "<h1>Raw HTML</h1>"}},
        }

        result = runner.invoke(app, ["confluence", "page", "view", "12345", "--body-format", "storage"])
        assert result.exit_code == 0

        # Should pass "storage" directly to API
        call_kwargs = mock_get.call_args
        assert call_kwargs[1].get("body-format") == "storage"

        # Should NOT convert to markdown
        assert "<h1>" in result.output


# ── Page create (wiki via v1, others via v2) ────────────────────────────


class TestPageCreate:
    @patch("atlassian_cli.commands.confluence.page.get_client")
    @patch("atlassian_cli.commands.confluence.page.confluence_v1_post")
    def test_wiki_uses_v1_api(self, mock_v1_post, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_v1_post.return_value = {"id": "999"}

        result = runner.invoke(app, [
            "confluence", "page", "create",
            "--space", "100", "--title", "Wiki Page",
            "--body", "h1. Hello",
        ])
        assert result.exit_code == 0
        assert "999" in result.output

        # Verify v1 API was called with wiki body structure
        payload = mock_v1_post.call_args[1]["json"]
        assert payload["type"] == "page"
        assert payload["body"]["wiki"]["representation"] == "wiki"
        assert payload["body"]["wiki"]["value"] == "h1. Hello"

    @patch("atlassian_cli.commands.confluence.page.get_client")
    @patch("atlassian_cli.commands.confluence.page.confluence_post")
    def test_storage_uses_v2_api(self, mock_v2_post, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_v2_post.return_value = {"id": "888"}

        result = runner.invoke(app, [
            "confluence", "page", "create",
            "--space", "100", "--title", "HTML Page",
            "--body", "<h1>Hello</h1>",
            "--format", "storage",
        ])
        assert result.exit_code == 0

        # Verify v2 API was called
        payload = mock_v2_post.call_args[1]["json"]
        assert payload["body"]["representation"] == "storage"
        assert payload["body"]["value"] == "<h1>Hello</h1>"

    @patch("atlassian_cli.commands.confluence.page.get_client")
    @patch("atlassian_cli.commands.confluence.page.confluence_v1_post")
    def test_wiki_sets_parent_as_ancestor(self, mock_v1_post, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_v1_post.return_value = {"id": "999"}

        runner.invoke(app, [
            "confluence", "page", "create",
            "--space", "100", "--title", "Child",
            "--body", "text", "--parent", "50",
        ])

        payload = mock_v1_post.call_args[1]["json"]
        assert payload["ancestors"] == [{"id": "50"}]


# ── Page edit (wiki via v1, others via v2) ──────────────────────────────


class TestPageEdit:
    @patch("atlassian_cli.commands.confluence.page.get_client")
    @patch("atlassian_cli.commands.confluence.page.confluence_get")
    @patch("atlassian_cli.commands.confluence.page.confluence_v1_put")
    def test_wiki_edit_uses_v1_api(self, mock_v1_put, mock_get, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_get.return_value = {"title": "Old Title", "version": {"number": 3}}

        result = runner.invoke(app, [
            "confluence", "page", "edit", "12345",
            "--body", "h1. Updated",
        ])
        assert result.exit_code == 0

        payload = mock_v1_put.call_args[1]["json"]
        assert payload["body"]["wiki"]["representation"] == "wiki"
        assert payload["version"]["number"] == 4

    @patch("atlassian_cli.commands.confluence.page.get_client")
    @patch("atlassian_cli.commands.confluence.page.confluence_get")
    @patch("atlassian_cli.commands.confluence.page.confluence_put")
    def test_storage_edit_uses_v2_api(self, mock_v2_put, mock_get, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_get.return_value = {"title": "Old Title", "version": {"number": 1}}

        result = runner.invoke(app, [
            "confluence", "page", "edit", "12345",
            "--body", "<h1>Updated</h1>", "--format", "storage",
        ])
        assert result.exit_code == 0

        payload = mock_v2_put.call_args[1]["json"]
        assert payload["body"]["representation"] == "storage"


# ── Blog view (markdown default) ────────────────────────────────────────


MOCK_BLOG_RESPONSE = {
    "id": "54321",
    "title": "Test Blog",
    "status": "current",
    "spaceId": "99",
    "createdAt": "2026-03-11T00:00:00Z",
    "body": {
        "view": {
            "value": "<h2>Blog Post</h2><p>Content here.</p>",
        },
    },
}


class TestBlogViewMarkdown:
    @patch("atlassian_cli.commands.confluence.blog.get_client")
    @patch("atlassian_cli.commands.confluence.blog.confluence_get")
    def test_default_format_is_markdown(self, mock_get, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_get.return_value = MOCK_BLOG_RESPONSE

        result = runner.invoke(app, ["confluence", "blog", "view", "54321"])
        assert result.exit_code == 0

        call_kwargs = mock_get.call_args
        assert call_kwargs[1].get("body-format") == "view"

        assert "## Blog Post" in result.output
        assert "<h2>" not in result.output


# ── Blog create (wiki via v1) ───────────────────────────────────────────


class TestBlogCreate:
    @patch("atlassian_cli.commands.confluence.blog.get_client")
    @patch("atlassian_cli.commands.confluence.blog.confluence_v1_post")
    def test_wiki_uses_v1_api(self, mock_v1_post, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_v1_post.return_value = {"id": "777"}

        result = runner.invoke(app, [
            "confluence", "blog", "create",
            "--space", "100", "--title", "Wiki Blog",
            "--body", "h1. Blog Post",
        ])
        assert result.exit_code == 0
        assert "777" in result.output

        payload = mock_v1_post.call_args[1]["json"]
        assert payload["type"] == "blogpost"
        assert payload["body"]["wiki"]["representation"] == "wiki"

    @patch("atlassian_cli.commands.confluence.blog.get_client")
    @patch("atlassian_cli.commands.confluence.blog.confluence_post")
    def test_storage_uses_v2_api(self, mock_v2_post, mock_client, saved_config):
        mock_client.return_value = MagicMock()
        mock_v2_post.return_value = {"id": "666"}

        result = runner.invoke(app, [
            "confluence", "blog", "create",
            "--space", "100", "--title", "HTML Blog",
            "--body", "<p>Content</p>",
            "--format", "storage",
        ])
        assert result.exit_code == 0

        payload = mock_v2_post.call_args[1]["json"]
        assert payload["body"]["representation"] == "storage"

"""Tests for issue module helper functions (no API calls)."""

from __future__ import annotations

import pytest

from atlassian_cli.commands.jira.issue import (
    _extract_issue_row,
    _extract_issue_detail,
    _adf_to_text,
    _text_to_adf,
)
from conftest import SAMPLE_ISSUE


class TestExtractIssueRow:
    def test_full_issue(self):
        row = _extract_issue_row(SAMPLE_ISSUE)
        assert row["key"] == "PROJ-1"
        assert row["summary"] == "Fix login bug"
        assert row["status"] == "In Progress"
        assert row["assignee"] == "Alice"
        assert row["priority"] == "High"
        assert row["type"] == "Bug"

    def test_missing_fields(self):
        row = _extract_issue_row({"key": "X-1", "fields": {}})
        assert row["key"] == "X-1"
        assert row["summary"] == ""
        assert row["assignee"] == "Unassigned"

    def test_null_assignee(self):
        issue = {"key": "X-1", "fields": {"assignee": None}}
        row = _extract_issue_row(issue)
        assert row["assignee"] == "Unassigned"

    def test_empty_dict(self):
        row = _extract_issue_row({})
        assert row["key"] == ""


class TestExtractIssueDetail:
    def test_full_detail(self):
        detail = _extract_issue_detail(SAMPLE_ISSUE)
        assert detail["Key"] == "PROJ-1"
        assert detail["Labels"] == "bug, urgent"
        assert "Login returns 500" in detail["Description"]

    def test_null_fields(self):
        issue = {"key": "X-1", "fields": {"assignee": None, "reporter": None, "status": None, "priority": None, "issuetype": None}}
        detail = _extract_issue_detail(issue)
        assert detail["Assignee"] == "Unassigned"
        assert detail["Reporter"] == ""
        assert detail["Status"] == ""


class TestAdfToText:
    def test_simple_paragraph(self):
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }
        assert "Hello world" in _adf_to_text(adf)

    def test_multiple_paragraphs(self):
        adf = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Line 1"}]},
                {"type": "paragraph", "content": [{"type": "text", "text": "Line 2"}]},
            ],
        }
        text = _adf_to_text(adf)
        assert "Line 1" in text
        assert "Line 2" in text

    def test_nested_content(self):
        adf = {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": "item"}]}
                    ],
                }
            ],
        }
        assert "item" in _adf_to_text(adf)

    def test_empty_doc(self):
        assert _adf_to_text({"type": "doc", "content": []}) == ""

    def test_text_node(self):
        assert _adf_to_text({"type": "text", "text": "direct"}) == "direct"


class TestTextToAdf:
    def test_single_line(self):
        adf = _text_to_adf("Hello")
        assert adf["type"] == "doc"
        assert adf["version"] == 1
        assert len(adf["content"]) == 1
        assert adf["content"][0]["type"] == "paragraph"
        assert adf["content"][0]["content"][0]["text"] == "Hello"

    def test_multiline(self):
        adf = _text_to_adf("Line 1\nLine 2\nLine 3")
        assert len(adf["content"]) == 3

    def test_empty_line_produces_empty_paragraph(self):
        adf = _text_to_adf("Before\n\nAfter")
        assert len(adf["content"]) == 3
        # Middle paragraph should have empty content
        assert adf["content"][1]["content"] == []

    def test_empty_string(self):
        adf = _text_to_adf("")
        assert len(adf["content"]) == 1
        # Empty string produces a paragraph with empty content (same as blank line)
        assert adf["content"][0]["content"] == []

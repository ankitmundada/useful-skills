"""Tests for output module."""

from __future__ import annotations

import json

import pytest

from atlassian_cli.output import render, render_single, _truncate


ROWS = [
    {"key": "PROJ-1", "summary": "First issue", "status": "Open"},
    {"key": "PROJ-2", "summary": "Second issue", "status": "Done"},
]
COLUMNS = ["key", "summary", "status"]


class TestRenderJson:
    def test_json_output(self, capsys):
        render(ROWS, COLUMNS, output="json")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 2
        assert data[0]["key"] == "PROJ-1"
        assert data[1]["status"] == "Done"

    def test_json_filters_to_columns(self, capsys):
        rows = [{"key": "X-1", "summary": "Hi", "status": "Open", "extra": "ignored"}]
        render(rows, ["key", "summary"], output="json")
        data = json.loads(capsys.readouterr().out)
        assert "extra" not in data[0]
        assert set(data[0].keys()) == {"key", "summary"}

    def test_json_empty(self, capsys):
        render([], COLUMNS, output="json")
        data = json.loads(capsys.readouterr().out)
        assert data == []


class TestRenderCsv:
    def test_csv_output(self, capsys):
        render(ROWS, COLUMNS, output="csv")
        out = capsys.readouterr().out.replace("\r\n", "\n")
        lines = out.strip().split("\n")
        assert lines[0] == "key,summary,status"
        assert lines[1] == "PROJ-1,First issue,Open"
        assert lines[2] == "PROJ-2,Second issue,Done"

    def test_csv_empty(self, capsys):
        render([], COLUMNS, output="csv")
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        # Just the header
        assert lines[0] == "key,summary,status"


class TestRenderSingle:
    def test_json_single(self, capsys):
        data = {"Key": "PROJ-1", "Summary": "Test"}
        render_single(data, output="json")
        out = json.loads(capsys.readouterr().out)
        assert out["Key"] == "PROJ-1"

    def test_csv_single(self, capsys):
        data = {"Key": "PROJ-1", "Summary": "Test"}
        render_single(data, output="csv")
        out = capsys.readouterr().out.replace("\r\n", "\n")
        lines = out.strip().split("\n")
        assert lines[0] == "Key,Summary"
        assert lines[1] == "PROJ-1,Test"


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert _truncate("12345", 5) == "12345"

    def test_long_string_truncated(self):
        result = _truncate("hello world", 6)
        assert len(result) == 6
        assert result.endswith("…")
        assert result == "hello…"

    def test_empty_string(self):
        assert _truncate("", 5) == ""

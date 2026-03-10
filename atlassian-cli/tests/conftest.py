"""Shared fixtures for tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlassian_cli.config import Config, Profile, CONFIG_DIR, CONFIG_FILE


@pytest.fixture(autouse=True)
def isolate_config(tmp_path, monkeypatch):
    """Redirect config to a temp directory so tests never touch real config."""
    cfg_dir = tmp_path / ".config" / "atlassian-cli"
    cfg_file = cfg_dir / "config.json"
    monkeypatch.setattr("atlassian_cli.config.CONFIG_DIR", cfg_dir)
    monkeypatch.setattr("atlassian_cli.config.CONFIG_FILE", cfg_file)
    # Also clear the env var so it doesn't leak into tests
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    return cfg_dir, cfg_file


@pytest.fixture
def saved_config(isolate_config):
    """Create a saved config with a default profile."""
    cfg_dir, cfg_file = isolate_config
    cfg = Config(
        default_profile="default",
        profiles={
            "default": Profile(
                site="https://test.atlassian.net",
                email="user@test.com",
                token="test-token-123",
            ),
        },
    )
    cfg.save()
    return cfg


# ── Jira API response fixtures ──────────────────────────────────────────


SAMPLE_ISSUE = {
    "key": "PROJ-1",
    "fields": {
        "summary": "Fix login bug",
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Alice", "accountId": "abc123"},
        "priority": {"name": "High"},
        "issuetype": {"name": "Bug"},
        "reporter": {"displayName": "Bob"},
        "labels": ["bug", "urgent"],
        "created": "2026-01-15T10:00:00.000+0000",
        "updated": "2026-03-01T14:30:00.000+0000",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Login returns 500 error"}],
                }
            ],
        },
    },
}

SAMPLE_SEARCH_RESPONSE = {
    "issues": [SAMPLE_ISSUE],
    "total": 1,
}

SAMPLE_TRANSITIONS = {
    "transitions": [
        {"id": "31", "name": "Start Progress", "to": {"name": "In Progress"}},
        {"id": "51", "name": "Done", "to": {"name": "Done"}},
        {"id": "21", "name": "To Do", "to": {"name": "To Do"}},
    ],
}

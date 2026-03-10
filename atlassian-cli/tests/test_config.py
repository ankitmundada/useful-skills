"""Tests for config module."""

from __future__ import annotations

import json
import os

import pytest

from atlassian_cli.config import Config, Profile


class TestProfile:
    def test_get_token_from_field(self):
        p = Profile(site="https://x.atlassian.net", email="a@b.com", token="secret")
        assert p.get_token() == "secret"

    def test_get_token_from_env_overrides(self, monkeypatch):
        p = Profile(site="https://x.atlassian.net", email="a@b.com", token="stored")
        monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-token")
        assert p.get_token() == "env-token"

    def test_get_token_empty_string_without_env(self):
        p = Profile(site="https://x.atlassian.net", email="a@b.com", token="")
        assert p.get_token() == ""


class TestConfig:
    def test_load_empty_when_no_file(self, isolate_config):
        cfg = Config.load()
        assert cfg.profiles == {}
        assert cfg.default_profile == "default"

    def test_save_and_load_roundtrip(self, isolate_config):
        cfg_dir, cfg_file = isolate_config
        cfg = Config(
            default_profile="prod",
            profiles={
                "prod": Profile(site="https://prod.atlassian.net", email="a@b.com", token="tok"),
            },
        )
        cfg.save()

        assert cfg_file.exists()
        loaded = Config.load()
        assert loaded.default_profile == "prod"
        assert "prod" in loaded.profiles
        assert loaded.profiles["prod"].site == "https://prod.atlassian.net"
        assert loaded.profiles["prod"].token == "tok"

    def test_save_creates_directory(self, isolate_config):
        cfg_dir, _ = isolate_config
        assert not cfg_dir.exists()
        Config(profiles={"x": Profile(site="https://x.net", email="a@b.com")}).save()
        assert cfg_dir.exists()

    def test_multiple_profiles(self, isolate_config):
        cfg = Config(
            default_profile="dev",
            profiles={
                "dev": Profile(site="https://dev.atlassian.net", email="d@b.com", token="d"),
                "prod": Profile(site="https://prod.atlassian.net", email="p@b.com", token="p"),
            },
        )
        cfg.save()
        loaded = Config.load()
        assert len(loaded.profiles) == 2
        assert loaded.profiles["dev"].token == "d"
        assert loaded.profiles["prod"].token == "p"

    def test_get_profile_default(self, saved_config):
        cfg = Config.load()
        p = cfg.get_profile()
        assert p.site == "https://test.atlassian.net"

    def test_get_profile_by_name(self, saved_config):
        cfg = Config.load()
        p = cfg.get_profile("default")
        assert p.email == "user@test.com"

    def test_get_profile_missing_exits(self, saved_config):
        cfg = Config.load()
        with pytest.raises(SystemExit):
            cfg.get_profile("nonexistent")

    def test_get_profile_no_token_exits(self, isolate_config):
        cfg = Config(profiles={"empty": Profile(site="https://x.net", email="a@b.com", token="")})
        cfg.save()
        loaded = Config.load()
        with pytest.raises(SystemExit):
            loaded.get_profile("empty")

    def test_config_file_is_valid_json(self, isolate_config):
        cfg = Config(profiles={"x": Profile(site="https://x.net", email="a@b.com", token="t")})
        cfg.save()
        _, cfg_file = isolate_config
        data = json.loads(cfg_file.read_text())
        assert "profiles" in data
        assert "default_profile" in data

"""Configuration management for atlassian-cli.

Stores site URL and email in ~/.config/atlassian-cli/config.json.
API token comes from ATLASSIAN_API_TOKEN env var or the config file.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "atlassian-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Profile:
    site: str  # e.g. "https://yourteam.atlassian.net"
    email: str
    token: str = ""  # stored in config; env var ATLASSIAN_API_TOKEN overrides

    def get_token(self) -> str:
        return os.environ.get("ATLASSIAN_API_TOKEN", self.token)


@dataclass
class Config:
    default_profile: str = "default"
    profiles: dict[str, Profile] = field(default_factory=dict)

    # ---- persistence ----

    @classmethod
    def load(cls) -> Config:
        if not CONFIG_FILE.exists():
            return cls()
        raw = json.loads(CONFIG_FILE.read_text())
        profiles = {
            name: Profile(**data) for name, data in raw.get("profiles", {}).items()
        }
        return cls(
            default_profile=raw.get("default_profile", "default"),
            profiles=profiles,
        )

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        raw = {
            "default_profile": self.default_profile,
            "profiles": {name: asdict(p) for name, p in self.profiles.items()},
        }
        CONFIG_FILE.write_text(json.dumps(raw, indent=2) + "\n")

    # ---- helpers ----

    def get_profile(self, name: str | None = None) -> Profile:
        name = name or self.default_profile
        if name not in self.profiles:
            raise SystemExit(
                f"Profile '{name}' not found. Run: atlassian-cli auth login"
            )
        profile = self.profiles[name]
        if not profile.get_token():
            raise SystemExit(
                f"No API token for profile '{name}'. "
                "Set ATLASSIAN_API_TOKEN or re-run: atlassian-cli auth login"
            )
        return profile

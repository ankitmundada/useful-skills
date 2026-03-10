# atlassian-cli

Open-source Python CLI for Jira and Confluence Cloud. Built for humans and AI agents.

## Install

```bash
# Homebrew (macOS/Linux)
brew install ankitmundada/tap/atlassian-cli

# pip / pipx
pip install cli-atlassian
# or
pipx install cli-atlassian
```

## Setup

1. Create an API token at https://id.atlassian.com/manage/api-tokens
2. Run:

```bash
atlassian-cli auth login
```

You'll be prompted for your site URL, email, and token. Credentials are stored at `~/.config/atlassian-cli/config.json`.

Alternatively, set the `ATLASSIAN_API_TOKEN` environment variable.

## Quick start

```bash
# Search issues
atlassian-cli jira issue search --jql "assignee = currentUser() AND status != Done"

# View an issue
atlassian-cli jira issue view PROJ-123

# Create an issue
atlassian-cli jira issue create --project PROJ --type Task --summary "Fix login bug"

# Transition
atlassian-cli jira issue transition PROJ-123 --status "Done"

# Add a comment
atlassian-cli jira issue comment add PROJ-123 --body "Fixed in commit abc123"

# Sprint management
atlassian-cli jira board sprints 42 --state active
atlassian-cli jira sprint create --board 42 --name "Sprint 5" --goal "Ship auth"
atlassian-cli jira sprint update 100 --state active

# Confluence
atlassian-cli confluence space list
atlassian-cli confluence page search --cql "space = 'ENG' AND title ~ 'design'"
atlassian-cli confluence page create --space 12345 --title "Meeting Notes" --body "<p>Notes here</p>"
```

## Commands

```
atlassian-cli auth login|logout|status

atlassian-cli jira issue search|view|create|edit|delete|transition|assign
atlassian-cli jira issue comment add|list|edit|delete
atlassian-cli jira issue link add|list|types
atlassian-cli jira board list|view|sprints
atlassian-cli jira sprint view|issues|create|update|delete|move
atlassian-cli jira project list|view

atlassian-cli confluence page view|create|edit|search
atlassian-cli confluence space list|view|create
atlassian-cli confluence blog list|view|create
```

Every read command supports `--output table|json|csv` (default: `table`).

## Output formats

```bash
# Rich table (default, for humans)
atlassian-cli jira issue search --jql "project = PROJ" --limit 5

# JSON (for scripts and AI agents)
atlassian-cli jira issue search --jql "project = PROJ" --output json

# CSV (for spreadsheets)
atlassian-cli jira issue search --jql "project = PROJ" --output csv
```

## Multiple profiles

```bash
# Set up profiles for different instances
atlassian-cli auth login --profile work --site https://work.atlassian.net --email you@work.com --token xxx
atlassian-cli auth login --profile personal --site https://me.atlassian.net --email you@me.com --token yyy

# Use a specific profile
atlassian-cli jira issue search --jql "..." --profile work

# Check what's configured
atlassian-cli auth status
```

## Why not acli?

|                   | atlassian-cli                   | acli                         |
| ----------------- | ------------------------------- | ---------------------------- |
| Open source       | Yes (MIT)                       | No                           |
| Extensible        | Fork it, PR it                  | Can't                        |
| Install           | `brew install` / `pip install`  | Download binary              |
| Command names     | `issue`, `sprint`               | `workitem`, `list-workitems` |
| Bug fixes         | Community-driven                | Wait for vendor              |
| AI-agent friendly | Compact output, `--output json` | Same                         |

## Development

```bash
git clone https://github.com/ankitmundada/useful-skills.git
cd useful-skills/atlassian-cli
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE).

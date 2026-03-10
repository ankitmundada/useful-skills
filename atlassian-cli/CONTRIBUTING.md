# Contributing

Thanks for your interest in contributing to atlassian-cli.

## Setup

```bash
git clone https://github.com/ankitmundada/useful-skills.git
cd useful-skills/atlassian-cli
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -v
```

Tests use mocked HTTP — no Atlassian account needed.

## Adding a new command

1. Find the right module in `src/atlassian_cli/commands/` (e.g., `jira/issue.py` for issue commands).
2. Add your command function with `@app.command()`.
3. Use `get_client(profile)` for auth and the appropriate API helper (`jira_get`, `agile_post`, `confluence_get`, etc.).
4. Use `render()` or `render_single()` for output.
5. Add tests in `tests/`.

Example:

```python
@app.command()
def my_command(
    key: str = typer.Argument(help="Issue key"),
    output: str = typer.Option("table", "--output", "-o"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Short description."""
    client = get_client(profile)
    data = jira_get(client, f"issue/{key}")
    render_single(data, output=output)
```

## Adding a new command group

1. Create a new module in the appropriate directory.
2. Define `app = typer.Typer(help="...")`.
3. Wire it into the parent `__init__.py`.
4. Add help-output tests in `tests/test_cli.py`.

## Code style

- Keep it simple. Each command is a function — no complex abstractions.
- Use `from __future__ import annotations` in every file.
- Type hints on all function signatures.
- Run `ruff check src/` before submitting.

## Pull requests

- One feature or fix per PR.
- Include tests for new commands.
- Update the skill docs (`project-management-atlassian-cli/SKILL.md`) if command syntax changes.

## API reference

- Jira REST API v3: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- Jira Agile API: https://developer.atlassian.com/cloud/jira/software/rest/
- Confluence REST API v2: https://developer.atlassian.com/cloud/confluence/rest/v2/

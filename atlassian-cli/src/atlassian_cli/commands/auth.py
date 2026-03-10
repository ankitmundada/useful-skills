"""Auth commands: login, logout, status."""

from __future__ import annotations

import typer
from rich import print as rprint

from atlassian_cli.config import Config, Profile

app = typer.Typer(help="Manage authentication.")


@app.command()
def login(
    profile: str = typer.Option("default", help="Profile name"),
    site: str = typer.Option(..., prompt=True, help="Site URL (e.g. https://team.atlassian.net)"),
    email: str = typer.Option(..., prompt=True, help="Your Atlassian email"),
    token: str = typer.Option(..., prompt=True, hide_input=True, help="API token"),
) -> None:
    """Store credentials for an Atlassian Cloud site."""
    # Normalize site URL
    site = site.rstrip("/")
    if not site.startswith("https://"):
        site = f"https://{site}"

    cfg = Config.load()
    cfg.profiles[profile] = Profile(site=site, email=email, token=token)
    if len(cfg.profiles) == 1:
        cfg.default_profile = profile
    cfg.save()
    rprint(f"[green]Saved profile '{profile}' for {site}[/green]")


@app.command()
def logout(
    profile: str = typer.Option("default", help="Profile to remove"),
) -> None:
    """Remove stored credentials for a profile."""
    cfg = Config.load()
    if profile not in cfg.profiles:
        raise typer.Exit(code=1)
    del cfg.profiles[profile]
    cfg.save()
    rprint(f"[yellow]Removed profile '{profile}'[/yellow]")


@app.command()
def status() -> None:
    """Show configured profiles and their auth status."""
    cfg = Config.load()
    if not cfg.profiles:
        rprint("[yellow]No profiles configured. Run: atlassian-cli auth login[/yellow]")
        return
    for name, profile in cfg.profiles.items():
        default = " (default)" if name == cfg.default_profile else ""
        has_token = bool(profile.get_token())
        status_str = "[green]authenticated[/green]" if has_token else "[red]no token[/red]"
        rprint(f"  {name}{default}: {profile.site} ({profile.email}) — {status_str}")

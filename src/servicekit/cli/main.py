"""Main Typer CLI application for servicekit."""

import typer

app = typer.Typer(
    name="servicekit",
    help="ServiceKit CLI - Framework utilities for building data services",
    no_args_is_help=True,
)

# Register command groups
from . import migrations  # noqa: E402

app.add_typer(migrations.app, name="migrations", help="Database migration commands")

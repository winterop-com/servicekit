"""Migration management commands."""

from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(help="Database migration commands")


@app.command("init")
def init_migrations(
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory for migrations"),
    ] = Path("alembic"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing files"),
    ] = False,
) -> None:
    """Initialize Alembic migrations for your project.

    Creates an alembic directory with:
    - env.py configured for async SQLAlchemy
    - alembic.ini configuration file
    - versions/ directory for migration scripts
    - script.py.mako template

    After initialization, you can:
    1. Import your models in alembic/env.py
    2. Generate migrations: alembic revision --autogenerate -m "description"
    3. Apply migrations: alembic upgrade head
    """
    from servicekit.migrations.helpers import init_alembic_directory

    typer.echo(f"Initializing migrations in: {output_dir}")

    try:
        init_alembic_directory(
            output_dir=output_dir,
            force=force,
        )
        typer.secho("✓ Migration directory initialized successfully!", fg=typer.colors.GREEN)
        typer.echo("\nNext steps:")
        typer.echo(f"  1. Import your models in {output_dir}/env.py")
        typer.echo("  2. Generate migration: alembic revision --autogenerate -m 'initial'")
        typer.echo("  3. Apply migrations: alembic upgrade head")
        typer.echo("\nSee docs: https://winterop-com.github.io/servicekit/guides/database-migrations/")
    except FileExistsError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        typer.echo("Use --force to overwrite existing files")
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

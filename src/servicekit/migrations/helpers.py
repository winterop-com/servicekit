"""Migration helper utilities and template rendering."""

from pathlib import Path

from jinja2 import Environment, PackageLoader


def init_alembic_directory(
    output_dir: Path,
    force: bool = False,
    model_imports: list[str] | None = None,
) -> None:
    """Initialize Alembic directory structure with templates.

    Args:
        output_dir: Directory to create alembic structure in
        force: Overwrite existing files if True
        model_imports: Optional list of import statements to add to env.py
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if already exists
    if (output_dir / "env.py").exists() and not force:
        raise FileExistsError(f"Migration directory already exists: {output_dir}\nUse --force to overwrite")

    # Setup Jinja2 environment
    env = Environment(loader=PackageLoader("servicekit.migrations", "templates"))

    # Render env.py
    env_template = env.get_template("env.py.jinja")
    env_content = env_template.render(model_imports=model_imports or [])
    (output_dir / "env.py").write_text(env_content)

    # Render alembic.ini (in parent directory)
    ini_template = env.get_template("alembic.ini.jinja")
    ini_content = ini_template.render(script_location=str(output_dir))
    (output_dir.parent / "alembic.ini").write_text(ini_content)

    # Create versions/ directory
    (output_dir / "versions").mkdir(exist_ok=True)

    # Render script.py.mako
    mako_template = env.get_template("script.py.mako")
    (output_dir / "script.py.mako").write_text(mako_template.render())

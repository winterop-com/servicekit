"""Tests for servicekit CLI commands."""

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from servicekit.cli import app

runner = CliRunner()


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self) -> None:
        """Test CLI help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ServiceKit CLI" in result.stdout

    def test_migrations_help(self) -> None:
        """Test migrations help command."""
        result = runner.invoke(app, ["migrations", "--help"])
        assert result.exit_code == 0
        assert "Database migration commands" in result.stdout

    def test_migrations_init_help(self) -> None:
        """Test migrations init help command."""
        result = runner.invoke(app, ["migrations", "init", "--help"])
        assert result.exit_code == 0
        assert "Initialize Alembic migrations" in result.stdout

    def test_migrations_init_creates_structure(self) -> None:
        """Test that migrations init creates correct directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            result = runner.invoke(app, ["migrations", "init", "--output", str(output_dir)])

            assert result.exit_code == 0
            assert "Migration directory initialized successfully" in result.stdout

            # Check created files
            assert (output_dir / "env.py").exists()
            assert (output_dir / "versions").exists()
            assert (output_dir / "versions").is_dir()
            assert (output_dir / "script.py.mako").exists()
            assert (Path(tmpdir) / "alembic.ini").exists()

    def test_migrations_init_custom_output_dir(self) -> None:
        """Test migrations init with custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "custom_migrations"

            result = runner.invoke(app, ["migrations", "init", "--output", str(output_dir)])

            assert result.exit_code == 0
            assert (output_dir / "env.py").exists()

    def test_migrations_init_fails_if_exists(self) -> None:
        """Test that migrations init fails if directory already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            # First initialization
            result = runner.invoke(app, ["migrations", "init", "--output", str(output_dir)])
            assert result.exit_code == 0

            # Second initialization should fail
            result = runner.invoke(app, ["migrations", "init", "--output", str(output_dir)])
            assert result.exit_code == 1
            assert "--force" in result.stdout or "already exists" in result.stdout

    def test_migrations_init_force_overwrites(self) -> None:
        """Test that migrations init --force overwrites existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            # First initialization
            result = runner.invoke(app, ["migrations", "init", "--output", str(output_dir)])
            assert result.exit_code == 0

            # Modify a file
            env_file = output_dir / "env.py"
            env_file.write_text("# Modified")

            # Force overwrite
            result = runner.invoke(app, ["migrations", "init", "--output", str(output_dir), "--force"])
            assert result.exit_code == 0

            # Check file was overwritten
            new_content = env_file.read_text()
            assert new_content != "# Modified"
            assert "servicekit" in new_content.lower()

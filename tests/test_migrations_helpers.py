"""Tests for migration helper functions."""

import tempfile
from pathlib import Path

from servicekit.migrations.helpers import init_alembic_directory


class TestMigrationHelpers:
    """Test migration helper functions."""

    def test_init_alembic_directory_creates_structure(self) -> None:
        """Test that init_alembic_directory creates correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            init_alembic_directory(output_dir)

            # Check files created
            assert (output_dir / "env.py").exists()
            assert (output_dir / "versions").exists()
            assert (output_dir / "script.py.mako").exists()
            assert (Path(tmpdir) / "alembic.ini").exists()

    def test_init_alembic_directory_env_py_content(self) -> None:
        """Test that env.py has correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            init_alembic_directory(output_dir)

            env_content = (output_dir / "env.py").read_text()

            # Check key components
            assert "from servicekit import Base" in env_content
            assert "target_metadata = Base.metadata" in env_content
            assert "run_migrations_offline" in env_content
            assert "run_migrations_online" in env_content
            assert "run_async_migrations" in env_content

    def test_init_alembic_directory_with_custom_imports(self) -> None:
        """Test that custom model imports are included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            custom_imports = [
                "from myapp.models import User  # noqa: F401",
                "from myapp.models import Product  # noqa: F401",
            ]

            init_alembic_directory(output_dir, model_imports=custom_imports)

            env_content = (output_dir / "env.py").read_text()

            # Check custom imports present
            for import_line in custom_imports:
                assert import_line in env_content

    def test_init_alembic_directory_alembic_ini_content(self) -> None:
        """Test that alembic.ini has correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            init_alembic_directory(output_dir)

            ini_content = (Path(tmpdir) / "alembic.ini").read_text()

            # Check configuration
            assert "[alembic]" in ini_content
            assert "script_location" in ini_content
            assert "sqlalchemy.url" in ini_content

    def test_init_alembic_directory_raises_if_exists(self) -> None:
        """Test that init raises FileExistsError if directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            # First init
            init_alembic_directory(output_dir)

            # Second init should raise
            try:
                init_alembic_directory(output_dir)
                assert False, "Expected FileExistsError"
            except FileExistsError as e:
                assert "already exists" in str(e)

    def test_init_alembic_directory_force_overwrites(self) -> None:
        """Test that force=True overwrites existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            # First init
            init_alembic_directory(output_dir)

            # Modify file
            env_file = output_dir / "env.py"
            env_file.write_text("# Modified")

            # Force overwrite
            init_alembic_directory(output_dir, force=True)

            # Check overwritten
            env_content = env_file.read_text()
            assert env_content != "# Modified"
            assert "servicekit" in env_content.lower()

    def test_init_alembic_directory_versions_directory_empty(self) -> None:
        """Test that versions directory is created but empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "alembic"

            init_alembic_directory(output_dir)

            versions_dir = output_dir / "versions"
            assert versions_dir.exists()
            assert versions_dir.is_dir()
            assert not list(versions_dir.iterdir()), "versions/ should be empty"

"""Tests for DataFrame data interchange format."""

from pathlib import Path
from typing import Any

import pytest

from servicekit.data import DataFrame


class TestDataFrameFromDict:
    """Test DataFrame.from_dict() method."""

    def test_from_dict_basic(self) -> None:
        """Create DataFrame from dictionary."""
        data: dict[str, list[Any]] = {"name": ["Alice", "Bob"], "age": [25, 30]}
        df = DataFrame.from_dict(data)

        assert df.columns == ["name", "age"]
        assert df.data == [["Alice", 25], ["Bob", 30]]

    def test_from_dict_empty(self) -> None:
        """Create DataFrame from empty dictionary."""
        df = DataFrame.from_dict({})

        assert df.columns == []
        assert df.data == []

    def test_from_dict_mismatched_lengths(self) -> None:
        """from_dict raises ValueError for mismatched column lengths."""
        data: dict[str, list[Any]] = {"name": ["Alice", "Bob"], "age": [25]}

        with pytest.raises(ValueError, match="All columns must have the same length"):
            DataFrame.from_dict(data)


class TestDataFrameFromRecords:
    """Test DataFrame.from_records() method."""

    def test_from_records_basic(self) -> None:
        """Create DataFrame from list of records."""
        records = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
        df = DataFrame.from_records(records)

        assert df.columns == ["name", "age"]
        assert df.data == [["Alice", 25], ["Bob", 30]]

    def test_from_records_empty(self) -> None:
        """Create DataFrame from empty list."""
        df = DataFrame.from_records([])

        assert df.columns == []
        assert df.data == []


class TestDataFrameToDict:
    """Test DataFrame.to_dict() method."""

    def test_to_dict_orient_dict(self) -> None:
        """Convert DataFrame to dict orient."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        result = df.to_dict(orient="dict")

        assert result == {"name": {0: "Alice", 1: "Bob"}, "age": {0: 25, 1: 30}}

    def test_to_dict_orient_list(self) -> None:
        """Convert DataFrame to list orient."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        result = df.to_dict(orient="list")

        assert result == {"name": ["Alice", "Bob"], "age": [25, 30]}

    def test_to_dict_orient_records(self) -> None:
        """Convert DataFrame to records orient."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        result = df.to_dict(orient="records")

        assert result == [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]

    def test_to_dict_invalid_orient(self) -> None:
        """to_dict raises ValueError for invalid orient."""
        df = DataFrame(columns=["name"], data=[["Alice"]])

        with pytest.raises(ValueError, match="Invalid orient"):
            df.to_dict(orient="invalid")  # type: ignore[arg-type]


class TestDataFrameImportErrors:
    """Test ImportError handling for optional dependencies."""

    def test_from_pandas_no_pandas(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """from_pandas raises ImportError when pandas not installed."""

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            raise ImportError()

        monkeypatch.setattr("builtins.__import__", mock_import)

        with pytest.raises(ImportError, match="pandas is required"):
            DataFrame.from_pandas(None)

    def test_from_polars_no_polars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """from_polars raises ImportError when polars not installed."""

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            raise ImportError()

        monkeypatch.setattr("builtins.__import__", mock_import)

        with pytest.raises(ImportError, match="polars is required"):
            DataFrame.from_polars(None)

    def test_from_xarray_no_xarray(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """from_xarray raises ImportError when xarray not installed."""

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            raise ImportError()

        monkeypatch.setattr("builtins.__import__", mock_import)

        with pytest.raises(ImportError, match="xarray is required"):
            DataFrame.from_xarray(None)

    def test_to_pandas_no_pandas(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """to_pandas raises ImportError when pandas not installed."""

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            raise ImportError()

        monkeypatch.setattr("builtins.__import__", mock_import)

        df = DataFrame(columns=["x"], data=[[1]])
        with pytest.raises(ImportError, match="pandas is required"):
            df.to_pandas()

    def test_to_polars_no_polars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """to_polars raises ImportError when polars not installed."""

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            raise ImportError()

        monkeypatch.setattr("builtins.__import__", mock_import)

        df = DataFrame(columns=["x"], data=[[1]])
        with pytest.raises(ImportError, match="polars is required"):
            df.to_polars()


class TestDataFrameTypeErrors:
    """Test TypeError handling for wrong input types."""

    def test_from_pandas_wrong_type(self) -> None:
        """from_pandas raises TypeError for non-DataFrame input."""
        pytest.importorskip("pandas")

        with pytest.raises(TypeError, match="Expected pandas DataFrame"):
            DataFrame.from_pandas("not a dataframe")

    def test_from_polars_wrong_type(self) -> None:
        """from_polars raises TypeError for non-DataFrame input."""
        pytest.importorskip("polars")

        with pytest.raises(TypeError, match="Expected Polars DataFrame"):
            DataFrame.from_polars("not a dataframe")

    def test_from_xarray_wrong_type(self) -> None:
        """from_xarray raises TypeError for non-DataArray input."""
        pytest.importorskip("xarray")

        with pytest.raises(TypeError, match="Expected xarray DataArray"):
            DataFrame.from_xarray("not a dataarray")

    def test_from_xarray_wrong_dimensions(self) -> None:
        """from_xarray raises ValueError for non-2D DataArray."""
        xr = pytest.importorskip("xarray")
        import numpy as np

        # Create 1D DataArray
        da = xr.DataArray(np.array([1, 2, 3]))

        with pytest.raises(ValueError, match="Only 2D DataArrays supported"):
            DataFrame.from_xarray(da)


class TestDataFrameProperties:
    """Test DataFrame utility properties."""

    def test_shape_basic(self) -> None:
        """shape property returns correct dimensions."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2], [3, 4]])
        assert df.shape == (2, 2)

    def test_shape_empty(self) -> None:
        """shape property handles empty DataFrame."""
        df = DataFrame(columns=[], data=[])
        assert df.shape == (0, 0)

    def test_shape_no_rows(self) -> None:
        """shape property with columns but no rows."""
        df = DataFrame(columns=["a", "b"], data=[])
        assert df.shape == (0, 2)

    def test_shape_rectangular(self) -> None:
        """shape property with different row and column counts."""
        df = DataFrame(columns=["a", "b", "c"], data=[[1, 2, 3], [4, 5, 6]])
        assert df.shape == (2, 3)

    def test_empty_true_no_rows(self) -> None:
        """empty returns True when no rows."""
        df = DataFrame(columns=["a"], data=[])
        assert df.empty is True

    def test_empty_true_no_columns(self) -> None:
        """empty returns True when no columns."""
        df = DataFrame(columns=[], data=[])
        assert df.empty is True

    def test_empty_false_with_data(self) -> None:
        """empty returns False when DataFrame has data."""
        df = DataFrame(columns=["a"], data=[[1], [2]])
        assert df.empty is False

    def test_size_basic(self) -> None:
        """size property returns total element count."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2], [3, 4]])
        assert df.size == 4

    def test_size_empty(self) -> None:
        """size property returns 0 for empty DataFrame."""
        df = DataFrame(columns=[], data=[])
        assert df.size == 0

    def test_size_single_column(self) -> None:
        """size property with single column."""
        df = DataFrame(columns=["a"], data=[[1], [2], [3]])
        assert df.size == 3

    def test_size_rectangular(self) -> None:
        """size property with non-square DataFrame."""
        df = DataFrame(columns=["a", "b", "c"], data=[[1, 2, 3], [4, 5, 6]])
        assert df.size == 6

    def test_ndim(self) -> None:
        """ndim property always returns 2."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2]])
        assert df.ndim == 2

    def test_ndim_empty(self) -> None:
        """ndim returns 2 even for empty DataFrame."""
        df = DataFrame(columns=[], data=[])
        assert df.ndim == 2


class TestDataFrameCSV:
    """Test DataFrame CSV methods."""

    def test_from_csv_string_basic(self) -> None:
        """Create DataFrame from CSV string."""
        csv_string = "name,age\nAlice,25\nBob,30"
        df = DataFrame.from_csv(csv_string=csv_string)

        assert df.columns == ["name", "age"]
        assert df.data == [["Alice", "25"], ["Bob", "30"]]

    def test_from_csv_string_no_header(self) -> None:
        """Create DataFrame from CSV string without header."""
        csv_string = "Alice,25\nBob,30"
        df = DataFrame.from_csv(csv_string=csv_string, has_header=False)

        assert df.columns == ["col_0", "col_1"]
        assert df.data == [["Alice", "25"], ["Bob", "30"]]

    def test_from_csv_string_custom_delimiter(self) -> None:
        """Create DataFrame from CSV string with custom delimiter."""
        csv_string = "name;age\nAlice;25\nBob;30"
        df = DataFrame.from_csv(csv_string=csv_string, delimiter=";")

        assert df.columns == ["name", "age"]
        assert df.data == [["Alice", "25"], ["Bob", "30"]]

    def test_from_csv_string_empty(self) -> None:
        """Create DataFrame from empty CSV string."""
        df = DataFrame.from_csv(csv_string="")

        assert df.columns == []
        assert df.data == []

    def test_from_csv_file_basic(self, tmp_path: Path) -> None:
        """Create DataFrame from CSV file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,25\nBob,30")

        df = DataFrame.from_csv(path=csv_file)

        assert df.columns == ["name", "age"]
        assert df.data == [["Alice", "25"], ["Bob", "30"]]

    def test_from_csv_file_not_found(self) -> None:
        """from_csv raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            DataFrame.from_csv(path="nonexistent.csv")

    def test_from_csv_neither_path_nor_string(self) -> None:
        """from_csv raises ValueError when neither path nor csv_string provided."""
        with pytest.raises(ValueError, match="Either path or csv_string must be provided"):
            DataFrame.from_csv()

    def test_from_csv_both_path_and_string(self, tmp_path: Path) -> None:
        """from_csv raises ValueError when both path and csv_string provided."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,2")

        with pytest.raises(ValueError, match="mutually exclusive"):
            DataFrame.from_csv(path=csv_file, csv_string="a,b\n1,2")

    def test_from_csv_encoding(self, tmp_path: Path) -> None:
        """Create DataFrame from CSV file with specific encoding."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,city\nAlice,Zürich", encoding="utf-8")

        df = DataFrame.from_csv(path=csv_file, encoding="utf-8")

        assert df.columns == ["name", "city"]
        assert df.data == [["Alice", "Zürich"]]

    def test_to_csv_string_basic(self) -> None:
        """Export DataFrame to CSV string."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        csv_string = df.to_csv()

        assert csv_string is not None
        assert "name,age" in csv_string
        assert "Alice,25" in csv_string
        assert "Bob,30" in csv_string

    def test_to_csv_string_no_header(self) -> None:
        """Export DataFrame to CSV string without header."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        csv_string = df.to_csv(include_header=False)

        assert csv_string is not None
        assert "name,age" not in csv_string
        assert "Alice,25" in csv_string
        assert "Bob,30" in csv_string

    def test_to_csv_string_custom_delimiter(self) -> None:
        """Export DataFrame to CSV string with custom delimiter."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        csv_string = df.to_csv(delimiter=";")

        assert csv_string is not None
        assert "name;age" in csv_string
        assert "Alice;25" in csv_string

    def test_to_csv_string_empty(self) -> None:
        """Export empty DataFrame to CSV string."""
        df = DataFrame(columns=[], data=[])
        csv_string = df.to_csv()

        # Empty DataFrame produces only a newline character
        assert csv_string.strip() == ""

    def test_to_csv_file_basic(self, tmp_path: Path) -> None:
        """Export DataFrame to CSV file."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        csv_file = tmp_path / "output.csv"

        result = df.to_csv(path=csv_file)

        assert result is None
        assert csv_file.exists()

        content = csv_file.read_text()
        assert "name,age" in content
        assert "Alice,25" in content
        assert "Bob,30" in content

    def test_to_csv_file_encoding(self, tmp_path: Path) -> None:
        """Export DataFrame to CSV file with specific encoding."""
        df = DataFrame(columns=["name", "city"], data=[["Alice", "Zürich"]])
        csv_file = tmp_path / "output.csv"

        df.to_csv(path=csv_file, encoding="utf-8")

        content = csv_file.read_text(encoding="utf-8")
        assert "Zürich" in content

    def test_csv_roundtrip_string(self) -> None:
        """Round-trip DataFrame through CSV string."""
        original = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])

        csv_string = original.to_csv()
        restored = DataFrame.from_csv(csv_string=csv_string)

        # Note: CSV conversion makes all values strings
        assert restored.columns == original.columns
        assert restored.data == [["Alice", "25"], ["Bob", "30"]]

    def test_csv_roundtrip_file(self, tmp_path: Path) -> None:
        """Round-trip DataFrame through CSV file."""
        original = DataFrame(columns=["x", "y"], data=[[1, 2], [3, 4]])
        csv_file = tmp_path / "roundtrip.csv"

        original.to_csv(path=csv_file)
        restored = DataFrame.from_csv(path=csv_file)

        # CSV conversion makes all values strings
        assert restored.columns == original.columns
        assert restored.data == [["1", "2"], ["3", "4"]]

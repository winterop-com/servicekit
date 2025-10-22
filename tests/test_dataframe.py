"""Tests for DataFrame data interchange format."""

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

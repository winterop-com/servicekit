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
        assert csv_string is not None
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


class TestDataFrameInspection:
    """Test DataFrame data inspection methods."""

    def test_head_default(self) -> None:
        """head() returns first 5 rows by default."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(10)])
        result = df.head()

        assert result.columns == ["x"]
        assert result.data == [[0], [1], [2], [3], [4]]

    def test_head_custom_n(self) -> None:
        """head() returns first n rows."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(10)])
        result = df.head(3)

        assert result.data == [[0], [1], [2]]

    def test_head_negative(self) -> None:
        """head() with negative n returns all except last |n| rows."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(10)])
        result = df.head(-3)

        assert result.data == [[0], [1], [2], [3], [4], [5], [6]]

    def test_head_exceeds_length(self) -> None:
        """head() with n > row count returns all rows."""
        df = DataFrame(columns=["x"], data=[[1], [2]])
        result = df.head(100)

        assert result.data == [[1], [2]]

    def test_tail_default(self) -> None:
        """tail() returns last 5 rows by default."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(10)])
        result = df.tail()

        assert result.columns == ["x"]
        assert result.data == [[5], [6], [7], [8], [9]]

    def test_tail_custom_n(self) -> None:
        """tail() returns last n rows."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(10)])
        result = df.tail(3)

        assert result.data == [[7], [8], [9]]

    def test_tail_negative(self) -> None:
        """tail() with negative n returns all except first |n| rows."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(10)])
        result = df.tail(-3)

        assert result.data == [[3], [4], [5], [6], [7], [8], [9]]

    def test_tail_exceeds_length(self) -> None:
        """tail() with n > row count returns all rows."""
        df = DataFrame(columns=["x"], data=[[1], [2]])
        result = df.tail(100)

        assert result.data == [[1], [2]]

    def test_sample_n(self) -> None:
        """sample() with n returns specified number of rows."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(100)])
        result = df.sample(n=10, random_state=42)

        assert len(result.data) == 10
        assert result.columns == ["x"]

    def test_sample_frac(self) -> None:
        """sample() with frac returns fractional sample."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(100)])
        result = df.sample(frac=0.1, random_state=42)

        assert len(result.data) == 10

    def test_sample_random_state(self) -> None:
        """sample() with random_state gives reproducible results."""
        df = DataFrame(columns=["x"], data=[[i] for i in range(100)])

        result1 = df.sample(n=10, random_state=42)
        result2 = df.sample(n=10, random_state=42)

        assert result1.data == result2.data

    def test_sample_both_n_and_frac_error(self) -> None:
        """sample() raises ValueError when both n and frac provided."""
        df = DataFrame(columns=["x"], data=[[1], [2], [3]])

        with pytest.raises(ValueError, match="mutually exclusive"):
            df.sample(n=2, frac=0.5)

    def test_sample_neither_error(self) -> None:
        """sample() raises ValueError when neither n nor frac provided."""
        df = DataFrame(columns=["x"], data=[[1], [2], [3]])

        with pytest.raises(ValueError, match="Either n or frac must be provided"):
            df.sample()

    def test_sample_frac_too_large(self) -> None:
        """sample() raises ValueError when frac > 1.0."""
        df = DataFrame(columns=["x"], data=[[1], [2], [3]])

        with pytest.raises(ValueError, match="frac must be <= 1.0"):
            df.sample(frac=1.5)


class TestDataFrameColumnOps:
    """Test DataFrame column operation methods."""

    def test_select_basic(self) -> None:
        """select() returns DataFrame with only specified columns."""
        df = DataFrame(columns=["a", "b", "c"], data=[[1, 2, 3], [4, 5, 6]])
        result = df.select(["a", "c"])

        assert result.columns == ["a", "c"]
        assert result.data == [[1, 3], [4, 6]]

    def test_select_single_column(self) -> None:
        """select() works with single column."""
        df = DataFrame(columns=["a", "b", "c"], data=[[1, 2, 3]])
        result = df.select(["b"])

        assert result.columns == ["b"]
        assert result.data == [[2]]

    def test_select_column_not_found(self) -> None:
        """select() raises KeyError for non-existent column."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2]])

        with pytest.raises(KeyError, match="Column 'z' not found"):
            df.select(["a", "z"])

    def test_drop_basic(self) -> None:
        """drop() returns DataFrame without specified columns."""
        df = DataFrame(columns=["a", "b", "c"], data=[[1, 2, 3], [4, 5, 6]])
        result = df.drop(["b"])

        assert result.columns == ["a", "c"]
        assert result.data == [[1, 3], [4, 6]]

    def test_drop_multiple_columns(self) -> None:
        """drop() can remove multiple columns."""
        df = DataFrame(columns=["a", "b", "c", "d"], data=[[1, 2, 3, 4]])
        result = df.drop(["b", "d"])

        assert result.columns == ["a", "c"]
        assert result.data == [[1, 3]]

    def test_drop_column_not_found(self) -> None:
        """drop() raises KeyError for non-existent column."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2]])

        with pytest.raises(KeyError, match="Column 'z' not found"):
            df.drop(["z"])

    def test_rename_basic(self) -> None:
        """rename() returns DataFrame with renamed columns."""
        df = DataFrame(columns=["a", "b", "c"], data=[[1, 2, 3]])
        result = df.rename({"a": "x", "c": "z"})

        assert result.columns == ["x", "b", "z"]
        assert result.data == [[1, 2, 3]]

    def test_rename_partial(self) -> None:
        """rename() only renames specified columns."""
        df = DataFrame(columns=["a", "b", "c"], data=[[1, 2, 3]])
        result = df.rename({"a": "x"})

        assert result.columns == ["x", "b", "c"]

    def test_rename_column_not_found(self) -> None:
        """rename() raises KeyError for non-existent column."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2]])

        with pytest.raises(KeyError, match="Column 'z' not found"):
            df.rename({"z": "new_name"})

    def test_rename_duplicate_names(self) -> None:
        """rename() raises ValueError if renaming creates duplicates."""
        df = DataFrame(columns=["a", "b", "c"], data=[[1, 2, 3]])

        with pytest.raises(ValueError, match="duplicate column names"):
            df.rename({"a": "b"})


class TestDataFrameValidation:
    """Test DataFrame validation methods."""

    def test_validate_success(self) -> None:
        """validate_structure() succeeds for valid DataFrame."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2], [3, 4]])
        df.validate_structure()  # Should not raise

    def test_validate_unequal_row_lengths(self) -> None:
        """validate_structure() raises ValueError for rows with wrong length."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2], [3, 4, 5]])

        with pytest.raises(ValueError, match="Row 1 has 3 values, expected 2"):
            df.validate_structure()

    def test_validate_duplicate_columns(self) -> None:
        """validate_structure() raises ValueError for duplicate column names."""
        df = DataFrame(columns=["a", "a", "b"], data=[[1, 2, 3]])

        with pytest.raises(ValueError, match="Duplicate column names"):
            df.validate_structure()

    def test_validate_empty_column_name(self) -> None:
        """validate_structure() raises ValueError for empty column name."""
        df = DataFrame(columns=["a", "", "b"], data=[[1, 2, 3]])

        with pytest.raises(ValueError, match="Column at index 1 is empty"):
            df.validate_structure()

    def test_infer_types_basic(self) -> None:
        """infer_types() correctly identifies column types."""
        df = DataFrame(columns=["int_col", "float_col", "str_col", "bool_col"], data=[[1, 2.5, "hello", True]])

        result = df.infer_types()

        assert result["int_col"] == "int"
        assert result["float_col"] == "float"
        assert result["str_col"] == "str"
        assert result["bool_col"] == "bool"

    def test_infer_types_mixed(self) -> None:
        """infer_types() detects mixed types."""
        df = DataFrame(columns=["mixed_col"], data=[[1], ["hello"], [3]])

        result = df.infer_types()

        assert result["mixed_col"] == "mixed"

    def test_infer_types_int_and_float(self) -> None:
        """infer_types() treats int+float columns as float."""
        df = DataFrame(columns=["num_col"], data=[[1], [2.5], [3]])

        result = df.infer_types()

        assert result["num_col"] == "float"

    def test_infer_types_null(self) -> None:
        """infer_types() detects null columns."""
        df = DataFrame(columns=["null_col"], data=[[None], [None]])

        result = df.infer_types()

        assert result["null_col"] == "null"

    def test_has_nulls_true(self) -> None:
        """has_nulls() detects columns with None values."""
        df = DataFrame(columns=["a", "b"], data=[[1, None], [2, 3]])

        result = df.has_nulls()

        assert result["a"] is False
        assert result["b"] is True

    def test_has_nulls_false(self) -> None:
        """has_nulls() returns False for columns without None values."""
        df = DataFrame(columns=["a", "b"], data=[[1, 2], [3, 4]])

        result = df.has_nulls()

        assert result["a"] is False
        assert result["b"] is False


class TestDataFrameIteration:
    """Test DataFrame iteration and length."""

    def test_len(self) -> None:
        """len() returns number of rows."""
        df = DataFrame(columns=["a"], data=[[1], [2], [3]])
        assert len(df) == 3

    def test_len_empty(self) -> None:
        """len() returns 0 for empty DataFrame."""
        df = DataFrame(columns=["a"], data=[])
        assert len(df) == 0

    def test_iter(self) -> None:
        """Iterate over rows as dictionaries."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])

        rows = list(df)

        assert rows == [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]

    def test_iter_empty(self) -> None:
        """Iterate over empty DataFrame."""
        df = DataFrame(columns=["a"], data=[])
        assert list(df) == []


class TestDataFrameJSON:
    """Test DataFrame JSON support."""

    def test_from_json_records(self) -> None:
        """Create DataFrame from JSON array."""
        json_string = '[{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]'
        df = DataFrame.from_json(json_string)

        assert df.columns == ["name", "age"]
        assert df.data == [["Alice", 25], ["Bob", 30]]

    def test_from_json_empty(self) -> None:
        """Create DataFrame from empty JSON array."""
        df = DataFrame.from_json("[]")
        assert df.columns == []
        assert df.data == []

    def test_from_json_not_array(self) -> None:
        """from_json raises ValueError for non-array JSON."""
        with pytest.raises(ValueError, match="JSON must be an array of objects"):
            DataFrame.from_json('{"a": 1}')

    def test_to_json_records(self) -> None:
        """Export DataFrame as JSON records."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])

        result = df.to_json(orient="records")

        assert result == '[{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]'

    def test_to_json_columns(self) -> None:
        """Export DataFrame as JSON columns."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])

        result = df.to_json(orient="columns")

        assert result == '{"name": ["Alice", "Bob"], "age": [25, 30]}'

    def test_to_json_empty(self) -> None:
        """Export empty DataFrame as JSON."""
        df = DataFrame(columns=[], data=[])
        assert df.to_json() == "[]"

    def test_json_roundtrip(self) -> None:
        """Round-trip JSON conversion preserves data."""
        original = DataFrame(columns=["x", "y"], data=[[1, 2], [3, 4]])

        json_string = original.to_json()
        restored = DataFrame.from_json(json_string)

        assert restored.columns == original.columns
        assert restored.data == original.data


class TestDataFrameColumnAccess:
    """Test DataFrame column access methods."""

    def test_get_column(self) -> None:
        """get_column() returns column values."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])

        result = df.get_column("age")

        assert result == [25, 30]

    def test_get_column_not_found(self) -> None:
        """get_column() raises KeyError for missing column."""
        df = DataFrame(columns=["a"], data=[[1]])

        with pytest.raises(KeyError, match="Column 'b' not found"):
            df.get_column("b")

    def test_getitem_single_column(self) -> None:
        """df['col'] returns column values."""
        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])

        result = df["age"]

        assert result == [25, 30]

    def test_getitem_multiple_columns(self) -> None:
        """df[['col1', 'col2']] returns DataFrame."""
        df = DataFrame(columns=["name", "age", "city"], data=[["Alice", 25, "NYC"], ["Bob", 30, "LA"]])

        result = df[["name", "city"]]

        assert isinstance(result, DataFrame)
        assert result.columns == ["name", "city"]
        assert result.data == [["Alice", "NYC"], ["Bob", "LA"]]

    def test_getitem_not_found(self) -> None:
        """df['col'] raises KeyError for missing column."""
        df = DataFrame(columns=["a"], data=[[1]])

        with pytest.raises(KeyError, match="Column 'b' not found"):
            df["b"]


class TestDataFrameUnique:
    """Test DataFrame.unique() method."""

    def test_unique_basic(self) -> None:
        """unique() returns unique values."""
        df = DataFrame(columns=["category"], data=[["A"], ["B"], ["A"], ["C"], ["B"]])

        result = df.unique("category")

        assert result == ["A", "B", "C"]

    def test_unique_preserves_order(self) -> None:
        """unique() preserves order of first appearance."""
        df = DataFrame(columns=["x"], data=[[3], [1], [2], [1], [3]])

        result = df.unique("x")

        assert result == [3, 1, 2]

    def test_unique_with_none(self) -> None:
        """unique() includes None values."""
        df = DataFrame(columns=["x"], data=[[1], [None], [2], [None], [1]])

        result = df.unique("x")

        assert result == [1, None, 2]

    def test_unique_all_same(self) -> None:
        """unique() with all same values."""
        df = DataFrame(columns=["x"], data=[["A"], ["A"], ["A"]])
        assert df.unique("x") == ["A"]

    def test_unique_not_found(self) -> None:
        """unique() raises KeyError for missing column."""
        df = DataFrame(columns=["a"], data=[[1]])

        with pytest.raises(KeyError, match="Column 'b' not found"):
            df.unique("b")


class TestDataFrameValueCounts:
    """Test DataFrame.value_counts() method."""

    def test_value_counts_basic(self) -> None:
        """value_counts() returns counts."""
        df = DataFrame(columns=["category"], data=[["A"], ["B"], ["A"], ["C"], ["B"], ["A"]])

        result = df.value_counts("category")

        assert result == {"A": 3, "B": 2, "C": 1}

    def test_value_counts_with_none(self) -> None:
        """value_counts() counts None values."""
        df = DataFrame(columns=["x"], data=[[1], [None], [2], [None], [1]])

        result = df.value_counts("x")

        assert result == {1: 2, None: 2, 2: 1}

    def test_value_counts_single_value(self) -> None:
        """value_counts() with all same values."""
        df = DataFrame(columns=["x"], data=[["A"], ["A"], ["A"]])
        assert df.value_counts("x") == {"A": 3}

    def test_value_counts_empty(self) -> None:
        """value_counts() on empty DataFrame."""
        df = DataFrame(columns=["x"], data=[])
        assert df.value_counts("x") == {}

    def test_value_counts_not_found(self) -> None:
        """value_counts() raises KeyError for missing column."""
        df = DataFrame(columns=["a"], data=[[1]])

        with pytest.raises(KeyError, match="Column 'b' not found"):
            df.value_counts("b")


class TestDataFrameSort:
    """Test DataFrame.sort() method."""

    def test_sort_ascending(self) -> None:
        """sort() in ascending order."""
        df = DataFrame(columns=["name", "age"], data=[["Bob", 30], ["Alice", 25], ["Charlie", 35]])

        result = df.sort("age")

        assert result.data == [["Alice", 25], ["Bob", 30], ["Charlie", 35]]

    def test_sort_descending(self) -> None:
        """sort() in descending order."""
        df = DataFrame(columns=["name", "score"], data=[["Alice", 85], ["Bob", 95], ["Charlie", 90]])

        result = df.sort("score", ascending=False)

        assert result.data == [["Bob", 95], ["Charlie", 90], ["Alice", 85]]

    def test_sort_with_none_ascending(self) -> None:
        """sort() with None values (ascending)."""
        df = DataFrame(columns=["x"], data=[[3], [None], [1], [None], [2]])

        result = df.sort("x")

        # None values should be at the end
        assert result.data == [[1], [2], [3], [None], [None]]

    def test_sort_with_none_descending(self) -> None:
        """sort() with None values (descending)."""
        df = DataFrame(columns=["x"], data=[[3], [None], [1], [None], [2]])

        result = df.sort("x", ascending=False)

        # None values should still be at the end
        assert result.data == [[3], [2], [1], [None], [None]]

    def test_sort_strings(self) -> None:
        """sort() string values."""
        df = DataFrame(columns=["name"], data=[["Charlie"], ["Alice"], ["Bob"]])

        result = df.sort("name")

        assert result.data == [["Alice"], ["Bob"], ["Charlie"]]

    def test_sort_immutable(self) -> None:
        """sort() returns new DataFrame, doesn't modify original."""
        df = DataFrame(columns=["x"], data=[[3], [1], [2]])

        result = df.sort("x")

        assert df.data == [[3], [1], [2]]  # Original unchanged
        assert result.data == [[1], [2], [3]]

    def test_sort_not_found(self) -> None:
        """sort() raises KeyError for missing column."""
        df = DataFrame(columns=["a"], data=[[1]])

        with pytest.raises(KeyError, match="Column 'b' not found"):
            df.sort("b")


class TestDataFramePandasIntegration:
    """Test DataFrame integration with pandas."""

    def test_from_pandas_basic(self) -> None:
        """Convert pandas DataFrame to servicekit DataFrame."""
        pd = pytest.importorskip("pandas")

        pdf = pd.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})
        df = DataFrame.from_pandas(pdf)

        assert df.columns == ["name", "age"]
        assert df.data == [["Alice", 25], ["Bob", 30]]

    def test_to_pandas_basic(self) -> None:
        """Convert servicekit DataFrame to pandas DataFrame."""
        pytest.importorskip("pandas")

        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        pdf = df.to_pandas()

        assert list(pdf.columns) == ["name", "age"]
        assert pdf.values.tolist() == [["Alice", 25], ["Bob", 30]]

    def test_pandas_roundtrip(self) -> None:
        """Round-trip conversion with pandas preserves data."""
        pd = pytest.importorskip("pandas")

        original_pdf = pd.DataFrame({"x": [1, 2, 3], "y": [4.0, 5.0, 6.0], "z": ["a", "b", "c"]})

        df = DataFrame.from_pandas(original_pdf)
        restored_pdf = df.to_pandas()

        pd.testing.assert_frame_equal(original_pdf, restored_pdf)

    def test_pandas_with_none(self) -> None:
        """Pandas conversion handles None values."""
        pd = pytest.importorskip("pandas")
        import numpy as np

        pdf = pd.DataFrame({"a": [1, np.nan, 3], "b": ["x", None, "z"]})
        df = DataFrame.from_pandas(pdf)

        # np.nan stays as np.nan in the data (not automatically converted to None)
        assert isinstance(df.data[1][0], float) and np.isnan(df.data[1][0])
        assert df.data[1][1] is None  # None -> None


class TestDataFramePolarsIntegration:
    """Test DataFrame integration with Polars."""

    def test_from_polars_basic(self) -> None:
        """Convert Polars DataFrame to servicekit DataFrame."""
        pl = pytest.importorskip("polars")

        pldf = pl.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})
        df = DataFrame.from_polars(pldf)

        assert df.columns == ["name", "age"]
        assert df.data == [["Alice", 25], ["Bob", 30]]

    def test_to_polars_basic(self) -> None:
        """Convert servicekit DataFrame to Polars DataFrame."""
        pytest.importorskip("polars")

        df = DataFrame(columns=["name", "age"], data=[["Alice", 25], ["Bob", 30]])
        pldf = df.to_polars()

        assert pldf.columns == ["name", "age"]
        assert pldf.rows() == [("Alice", 25), ("Bob", 30)]

    def test_polars_roundtrip(self) -> None:
        """Round-trip conversion with Polars preserves data."""
        pl = pytest.importorskip("polars")

        original_pldf = pl.DataFrame({"x": [1, 2, 3], "y": [4.0, 5.0, 6.0], "z": ["a", "b", "c"]})

        df = DataFrame.from_polars(original_pldf)
        restored_pldf = df.to_polars()

        assert original_pldf.equals(restored_pldf)

    def test_polars_with_none(self) -> None:
        """Polars conversion handles None values."""
        pl = pytest.importorskip("polars")

        pldf = pl.DataFrame({"a": [1, None, 3], "b": ["x", None, "z"]})
        df = DataFrame.from_polars(pldf)

        assert df.data[1][0] is None
        assert df.data[1][1] is None


class TestDataFrameXarrayIntegration:
    """Test DataFrame integration with xarray."""

    def test_from_xarray_basic(self) -> None:
        """Convert xarray DataArray to servicekit DataFrame."""
        xr = pytest.importorskip("xarray")
        pytest.importorskip("pandas")
        import numpy as np

        # xarray with named coordinates produces string column names
        da = xr.DataArray(np.array([[1, 2], [3, 4], [5, 6]]), dims=["x", "y"], coords={"y": ["col1", "col2"]})
        df = DataFrame.from_xarray(da)

        assert df.shape == (3, 2)
        assert df.columns == ["col1", "col2"]
        assert len(df.data) == 3

    def test_xarray_via_pandas(self) -> None:
        """Xarray conversion goes through pandas."""
        xr = pytest.importorskip("xarray")
        pytest.importorskip("pandas")
        import numpy as np

        # Create 2D DataArray with named dimensions
        da = xr.DataArray(
            np.array([[1.0, 2.0], [3.0, 4.0]]), dims=["row", "col"], coords={"row": [0, 1], "col": ["a", "b"]}
        )

        df = DataFrame.from_xarray(da)

        # Should have 2 rows (from row dimension) and 2 columns (from col dimension)
        assert df.shape == (2, 2)
        assert df.data == [[1.0, 2.0], [3.0, 4.0]]

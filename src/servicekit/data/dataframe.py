"""Universal DataFrame schema for servicekit services."""

import csv
import io
import json
import random
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel


class DataFrame(BaseModel):
    """Universal interchange format for tabular data from pandas, polars, xarray, and other libraries."""

    columns: list[str]
    data: list[list[Any]]

    @classmethod
    def from_pandas(cls, df: Any) -> Self:
        """Create schema from pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for from_pandas(). Install with: uv add pandas") from None

        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df)}")

        return cls(
            columns=df.columns.tolist(),
            data=df.values.tolist(),
        )

    @classmethod
    def from_polars(cls, df: Any) -> Self:
        """Create schema from Polars DataFrame."""
        try:
            import polars as pl
        except ImportError:
            raise ImportError("polars is required for from_polars(). Install with: uv add polars") from None

        if not isinstance(df, pl.DataFrame):
            raise TypeError(f"Expected Polars DataFrame, got {type(df)}")

        return cls(
            columns=df.columns,
            data=[list(row) for row in df.rows()],
        )

    @classmethod
    def from_xarray(cls, da: Any) -> Self:
        """Create schema from xarray DataArray (2D only)."""
        try:
            import xarray as xr
        except ImportError:
            raise ImportError("xarray is required for from_xarray(). Install with: uv add xarray") from None

        if not isinstance(da, xr.DataArray):
            raise TypeError(f"Expected xarray DataArray, got {type(da)}")

        if len(da.dims) != 2:
            raise ValueError(f"Only 2D DataArrays supported, got {len(da.dims)} dimensions")

        # Convert to pandas then use from_pandas
        pdf = da.to_pandas()
        return cls.from_pandas(pdf)

    @classmethod
    def from_dict(cls, data: dict[str, list[Any]]) -> Self:
        """Create schema from dictionary of columns."""
        if not data:
            return cls(columns=[], data=[])

        columns = list(data.keys())
        num_rows = len(next(iter(data.values())))

        if not all(len(vals) == num_rows for vals in data.values()):
            raise ValueError("All columns must have the same length")

        rows = [[data[col][i] for col in columns] for i in range(num_rows)]

        return cls(columns=columns, data=rows)

    @classmethod
    def from_records(cls, records: list[dict[str, Any]]) -> Self:
        """Create schema from list of records (row-oriented)."""
        if not records:
            return cls(columns=[], data=[])

        columns = list(records[0].keys())
        data = [[record[col] for col in columns] for record in records]

        return cls(columns=columns, data=data)

    @classmethod
    def from_csv(
        cls,
        path: str | Path | None = None,
        *,
        csv_string: str | None = None,
        delimiter: str = ",",
        has_header: bool = True,
        encoding: str = "utf-8",
    ) -> Self:
        r"""Create DataFrame from CSV file or string.

        Args:
            path: Path to CSV file (mutually exclusive with csv_string)
            csv_string: CSV data as string (mutually exclusive with path)
            delimiter: Column delimiter (default: comma)
            has_header: First row contains column names
            encoding: File encoding

        Returns:
            DataFrame instance

        Raises:
            ValueError: If neither or both path and csv_string provided
            FileNotFoundError: If path does not exist

        Example:
            >>> df = DataFrame.from_csv("data.csv")
            >>> df = DataFrame.from_csv(csv_string="a,b\n1,2\n3,4")
        """
        # Validate mutually exclusive parameters
        if path is None and csv_string is None:
            raise ValueError("Either path or csv_string must be provided")
        if path is not None and csv_string is not None:
            raise ValueError("path and csv_string are mutually exclusive")

        # Read CSV data
        if path is not None:
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {path}")
            with path_obj.open("r", encoding=encoding, newline="") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
        else:
            # csv_string is not None
            string_io = io.StringIO(csv_string)
            reader = csv.reader(string_io, delimiter=delimiter)
            rows = list(reader)

        # Handle empty CSV
        if not rows:
            return cls(columns=[], data=[])

        # Extract columns and data
        if has_header:
            columns = rows[0]
            data = rows[1:]
        else:
            # Generate column names
            num_cols = len(rows[0]) if rows else 0
            columns = [f"col_{i}" for i in range(num_cols)]
            data = rows

        return cls(columns=columns, data=data)

    def to_pandas(self) -> Any:
        """Convert schema to pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas(). Install with: uv add pandas") from None

        return pd.DataFrame(self.data, columns=self.columns)

    def to_polars(self) -> Any:
        """Convert schema to Polars DataFrame."""
        try:
            import polars as pl
        except ImportError:
            raise ImportError("polars is required for to_polars(). Install with: uv add polars") from None

        return pl.DataFrame(self.data, schema=self.columns, orient="row")

    def to_dict(self, orient: Literal["dict", "list", "records"] = "dict") -> Any:
        """Convert schema to dictionary with specified orient (dict, list, or records)."""
        if orient == "dict":
            return {col: {i: self.data[i][j] for i in range(len(self.data))} for j, col in enumerate(self.columns)}
        elif orient == "list":
            return {col: [row[j] for row in self.data] for j, col in enumerate(self.columns)}
        elif orient == "records":
            return [{col: row[j] for j, col in enumerate(self.columns)} for row in self.data]
        else:
            raise ValueError(f"Invalid orient: {orient}")

    def to_csv(
        self,
        path: str | Path | None = None,
        *,
        delimiter: str = ",",
        include_header: bool = True,
        encoding: str = "utf-8",
    ) -> str | None:
        """Export DataFrame to CSV file or string.

        Args:
            path: Path to write CSV file (if None, returns string)
            delimiter: Column delimiter
            include_header: Include column names in first row
            encoding: File encoding

        Returns:
            CSV string if path is None, otherwise None

        Example:
            >>> df.to_csv("output.csv")
            >>> csv_str = df.to_csv()  # Returns string
        """
        # Write to string buffer or file
        if path is None:
            # Return as string
            output = io.StringIO()
            writer = csv.writer(output, delimiter=delimiter)

            if include_header:
                writer.writerow(self.columns)

            writer.writerows(self.data)

            return output.getvalue()
        else:
            # Write to file
            path_obj = Path(path)
            with path_obj.open("w", encoding=encoding, newline="") as f:
                writer = csv.writer(f, delimiter=delimiter)

                if include_header:
                    writer.writerow(self.columns)

                writer.writerows(self.data)

            return None

    # Convenience aliases
    from_dataframe = from_pandas
    to_dataframe = to_pandas

    @property
    def shape(self) -> tuple[int, int]:
        """Return tuple representing dimensionality of the DataFrame."""
        return (len(self.data), len(self.columns))

    @property
    def empty(self) -> bool:
        """Indicator whether DataFrame is empty."""
        return len(self.data) == 0 or len(self.columns) == 0

    @property
    def size(self) -> int:
        """Return int representing number of elements in this object."""
        return len(self.data) * len(self.columns)

    @property
    def ndim(self) -> int:
        """Return int representing number of axes/array dimensions."""
        return 2

    def head(self, n: int = 5) -> Self:
        """Return first n rows.

        Args:
            n: Number of rows to return (negative values return all except last |n| rows)

        Returns:
            New DataFrame with first n rows

        Example:
            >>> df.head(10)
            >>> df.head(-3)  # All except last 3 rows
        """
        if n >= 0:
            selected_data = self.data[:n]
        else:
            selected_data = self.data[:n] if n != 0 else self.data
        return self.__class__(columns=self.columns, data=selected_data)

    def tail(self, n: int = 5) -> Self:
        """Return last n rows.

        Args:
            n: Number of rows to return (negative values return all except first |n| rows)

        Returns:
            New DataFrame with last n rows

        Example:
            >>> df.tail(10)
            >>> df.tail(-3)  # All except first 3 rows
        """
        if n >= 0:
            selected_data = self.data[-n:] if n > 0 else []
        else:
            selected_data = self.data[abs(n) :]
        return self.__class__(columns=self.columns, data=selected_data)

    def sample(
        self,
        n: int | None = None,
        frac: float | None = None,
        *,
        random_state: int | None = None,
    ) -> Self:
        """Return random sample of rows.

        Args:
            n: Number of rows to sample (mutually exclusive with frac)
            frac: Fraction of rows to sample (mutually exclusive with n)
            random_state: Random seed for reproducibility

        Returns:
            New DataFrame with sampled rows

        Raises:
            ValueError: If neither or both n and frac provided, or if frac > 1.0

        Example:
            >>> df.sample(n=100)
            >>> df.sample(frac=0.1, random_state=42)
        """
        # Validate parameters
        if n is None and frac is None:
            raise ValueError("Either n or frac must be provided")
        if n is not None and frac is not None:
            raise ValueError("n and frac are mutually exclusive")

        # Set random seed if provided
        if random_state is not None:
            random.seed(random_state)

        # Calculate sample size
        total_rows = len(self.data)
        if frac is not None:
            if frac > 1.0:
                raise ValueError("frac must be <= 1.0")
            sample_size = int(total_rows * frac)
        else:
            sample_size = min(n, total_rows) if n is not None else 0

        # Sample indices
        if sample_size >= total_rows:
            sampled_indices = list(range(total_rows))
            random.shuffle(sampled_indices)
        else:
            sampled_indices = random.sample(range(total_rows), sample_size)

        # Extract sampled rows
        sampled_data = [self.data[i] for i in sampled_indices]

        return self.__class__(columns=self.columns, data=sampled_data)

    def select(self, columns: list[str]) -> Self:
        """Return DataFrame with only specified columns.

        Args:
            columns: List of column names to keep

        Returns:
            New DataFrame with selected columns

        Raises:
            KeyError: If any column does not exist

        Example:
            >>> df.select(["name", "age"])
        """
        # Validate all columns exist
        for col in columns:
            if col not in self.columns:
                raise KeyError(f"Column '{col}' not found in DataFrame")

        # Get column indices
        indices = [self.columns.index(col) for col in columns]

        # Extract data for selected columns
        new_data = [[row[i] for i in indices] for row in self.data]

        return self.__class__(columns=columns, data=new_data)

    def drop(self, columns: list[str]) -> Self:
        """Return DataFrame without specified columns.

        Args:
            columns: List of column names to drop

        Returns:
            New DataFrame without dropped columns

        Raises:
            KeyError: If any column does not exist

        Example:
            >>> df.drop(["temp_col"])
        """
        # Validate all columns exist
        for col in columns:
            if col not in self.columns:
                raise KeyError(f"Column '{col}' not found in DataFrame")

        # Get columns to keep
        keep_cols = [c for c in self.columns if c not in columns]

        # Get indices for columns to keep
        indices = [self.columns.index(col) for col in keep_cols]

        # Extract data for kept columns
        new_data = [[row[i] for i in indices] for row in self.data]

        return self.__class__(columns=keep_cols, data=new_data)

    def rename(self, mapper: dict[str, str]) -> Self:
        """Return DataFrame with renamed columns.

        Args:
            mapper: Dictionary mapping old names to new names

        Returns:
            New DataFrame with renamed columns

        Raises:
            KeyError: If any old column name does not exist
            ValueError: If new names create duplicates

        Example:
            >>> df.rename({"old_name": "new_name"})
        """
        # Validate all old column names exist
        for old_name in mapper:
            if old_name not in self.columns:
                raise KeyError(f"Column '{old_name}' not found in DataFrame")

        # Create new column list
        new_cols = [mapper.get(col, col) for col in self.columns]

        # Check for duplicates
        if len(new_cols) != len(set(new_cols)):
            raise ValueError("Renaming would create duplicate column names")

        return self.__class__(columns=new_cols, data=self.data)

    def validate_structure(self) -> None:
        """Validate DataFrame structure.

        Checks:
        - All rows have same length as columns
        - Column names are unique
        - No null/empty column names

        Raises:
            ValueError: If validation fails

        Example:
            >>> df.validate_structure()
        """
        # Check for empty column names
        for i, col in enumerate(self.columns):
            if col == "":
                raise ValueError(f"Column at index {i} is empty")

        # Check for duplicate column names
        if len(self.columns) != len(set(self.columns)):
            duplicates = [col for col in self.columns if self.columns.count(col) > 1]
            raise ValueError(f"Duplicate column names found: {set(duplicates)}")

        # Check all rows have same length as columns
        num_cols = len(self.columns)
        for i, row in enumerate(self.data):
            if len(row) != num_cols:
                raise ValueError(f"Row {i} has {len(row)} values, expected {num_cols}")

    def infer_types(self) -> dict[str, str]:
        """Infer column data types.

        Returns:
            Dictionary mapping column names to type strings
            Types: "int", "float", "str", "bool", "null", "mixed"

        Example:
            >>> df.infer_types()
            {"age": "int", "name": "str", "score": "float"}
        """
        result: dict[str, str] = {}

        for col_idx, col_name in enumerate(self.columns):
            # Extract all values for this column
            values = [row[col_idx] for row in self.data]

            # Filter out None values for type checking
            non_null_values = [v for v in values if v is not None]

            if not non_null_values:
                result[col_name] = "null"
                continue

            # Check types
            types_found = set()
            for val in non_null_values:
                if isinstance(val, bool):
                    types_found.add("bool")
                elif isinstance(val, int):
                    types_found.add("int")
                elif isinstance(val, float):
                    types_found.add("float")
                elif isinstance(val, str):
                    types_found.add("str")
                else:
                    types_found.add("other")

            # Determine final type
            if len(types_found) > 1:
                # Special case: int and float can be treated as float
                if types_found == {"int", "float"}:
                    result[col_name] = "float"
                else:
                    result[col_name] = "mixed"
            elif "bool" in types_found:
                result[col_name] = "bool"
            elif "int" in types_found:
                result[col_name] = "int"
            elif "float" in types_found:
                result[col_name] = "float"
            elif "str" in types_found:
                result[col_name] = "str"
            else:
                result[col_name] = "mixed"

        return result

    def has_nulls(self) -> dict[str, bool]:
        """Check for null values in each column.

        Returns:
            Dictionary mapping column names to boolean
            True if column contains None values

        Example:
            >>> df.has_nulls()
            {"age": False, "email": True}
        """
        result: dict[str, bool] = {}

        for col_idx, col_name in enumerate(self.columns):
            # Check if any value in this column is None
            has_null = any(row[col_idx] is None for row in self.data)
            result[col_name] = has_null

        return result

    # Iteration and length

    def __len__(self) -> int:
        """Return number of rows."""
        return len(self.data)

    def __iter__(self) -> Any:
        """Iterate over rows as dictionaries."""
        for row in self.data:
            yield dict(zip(self.columns, row))

    # JSON support

    @classmethod
    def from_json(cls, json_string: str) -> Self:
        """Create DataFrame from JSON string (array of objects).

        Args:
            json_string: JSON array of objects

        Returns:
            DataFrame instance

        Raises:
            ValueError: If JSON is not a list of objects

        Example:
            >>> df = DataFrame.from_json('[{"a": 1, "b": 2}, {"a": 3, "b": 4}]')
        """
        records = json.loads(json_string)
        if not isinstance(records, list):
            raise ValueError("JSON must be an array of objects")
        return cls.from_records(records)

    def to_json(self, orient: Literal["records", "columns"] = "records") -> str:
        """Export DataFrame as JSON string.

        Args:
            orient: "records" for list of objects, "columns" for dict of arrays

        Returns:
            JSON string

        Example:
            >>> df.to_json()
            '[{"a": 1}, {"a": 2}]'
            >>> df.to_json(orient="columns")
            '{"a": [1, 2]}'
        """
        # Map "columns" to "list" for to_dict()
        dict_orient: Literal["dict", "list", "records"] = "list" if orient == "columns" else orient
        return json.dumps(self.to_dict(orient=dict_orient))

    # Column access

    def get_column(self, column: str) -> list[Any]:
        """Get all values for a column.

        Args:
            column: Column name

        Returns:
            List of values

        Raises:
            KeyError: If column does not exist

        Example:
            >>> df.get_column("age")
            [25, 30, 35]
        """
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")
        idx = self.columns.index(column)
        return [row[idx] for row in self.data]

    def __getitem__(self, key: str | list[str]) -> list[Any] | Self:
        """Support df['col'] and df[['col1', 'col2']].

        Args:
            key: Column name or list of column names

        Returns:
            List of values for single column, or DataFrame for multiple columns

        Example:
            >>> df["age"]  # Returns list
            >>> df[["name", "age"]]  # Returns DataFrame
        """
        if isinstance(key, str):
            return self.get_column(key)
        return self.select(key)

    # Analytics methods

    def unique(self, column: str) -> list[Any]:
        """Get unique values from a column (preserves order).

        Args:
            column: Column name

        Returns:
            List of unique values in order of first appearance

        Raises:
            KeyError: If column does not exist

        Example:
            >>> df.unique("category")
            ['A', 'B', 'C']
        """
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")

        col_idx = self.columns.index(column)
        seen = set()
        result = []
        for row in self.data:
            val = row[col_idx]
            if val not in seen:
                seen.add(val)
                result.append(val)
        return result

    def value_counts(self, column: str) -> dict[Any, int]:
        """Count occurrences of each unique value in column.

        Args:
            column: Column name

        Returns:
            Dictionary mapping values to counts

        Raises:
            KeyError: If column does not exist

        Example:
            >>> df.value_counts("category")
            {'A': 3, 'B': 2, 'C': 1}
        """
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")

        col_idx = self.columns.index(column)
        counts: dict[Any, int] = {}
        for row in self.data:
            val = row[col_idx]
            counts[val] = counts.get(val, 0) + 1
        return counts

    def sort(self, by: str, ascending: bool = True) -> Self:
        """Sort DataFrame by column.

        Args:
            by: Column name to sort by
            ascending: Sort in ascending order (default True)

        Returns:
            New sorted DataFrame

        Raises:
            KeyError: If column does not exist

        Example:
            >>> df.sort("age")
            >>> df.sort("score", ascending=False)
        """
        if by not in self.columns:
            raise KeyError(f"Column '{by}' not found in DataFrame")

        col_idx = self.columns.index(by)

        # Sort with None values at the end
        def sort_key(row: list[Any]) -> tuple[int, Any]:
            val = row[col_idx]
            if val is None:
                # Use a tuple to ensure None sorts last
                return (1, None) if ascending else (0, None)
            return (0, val) if ascending else (1, val)

        sorted_data = sorted(self.data, key=sort_key, reverse=not ascending)
        return self.__class__(columns=self.columns, data=sorted_data)


__all__ = ["DataFrame"]

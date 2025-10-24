"""Universal DataFrame schema for servicekit services."""

import csv
import io
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


__all__ = ["DataFrame"]

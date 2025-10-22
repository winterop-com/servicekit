"""Universal DataFrame schema for servicekit services."""

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

    # Convenience aliases
    from_dataframe = from_pandas
    to_dataframe = to_pandas


__all__ = ["DataFrame"]

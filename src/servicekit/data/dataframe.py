"""Universal DataFrame schema for servicekit services."""

from typing import Any, Literal, Self, cast

import pandas as pd
import polars as pl
import xarray as xr
from pydantic import BaseModel


class DataFrame(BaseModel):
    """Universal Pydantic schema for tabular data from any library.

    This schema provides a simple columns + data representation that works
    with pandas, polars, xarray, and other data libraries. It acts as a
    universal interchange format for HTTP APIs.
    """

    columns: list[str]
    data: list[list[Any]]

    @classmethod
    def from_pandas(cls, df: pd.DataFrame) -> Self:
        """Create schema from pandas DataFrame."""
        if not isinstance(df, pd.DataFrame):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Expected pandas DataFrame, got {type(df)}")

        return cls(
            columns=df.columns.tolist(),
            data=df.values.tolist(),
        )

    @classmethod
    def from_polars(cls, df: pl.DataFrame) -> Self:
        """Create schema from Polars DataFrame."""
        if not isinstance(df, pl.DataFrame):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Expected Polars DataFrame, got {type(df)}")

        return cls(
            columns=df.columns,
            data=[list(row) for row in df.rows()],
        )

    @classmethod
    def from_xarray(cls, da: xr.DataArray) -> Self:
        """Create schema from xarray DataArray (2D only)."""
        if not isinstance(da, xr.DataArray):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Expected xarray DataArray, got {type(da)}")

        if len(da.dims) != 2:
            raise ValueError(f"Only 2D DataArrays supported, got {len(da.dims)} dimensions")

        # Convert to pandas then use from_pandas
        pdf = cast(pd.DataFrame, da.to_pandas())
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

    def to_pandas(self) -> pd.DataFrame:
        """Convert schema to pandas DataFrame."""
        return pd.DataFrame(self.data, columns=self.columns)

    def to_polars(self) -> pl.DataFrame:
        """Convert schema to Polars DataFrame."""
        return pl.DataFrame(self.data, schema=self.columns, orient="row")

    def to_dict(self, orient: Literal["dict", "list", "records"] = "dict") -> Any:
        """Convert schema to dictionary.

        Args:
            orient: Output format
                - 'dict': {column: {index: value}}
                - 'list': {column: [values]}
                - 'records': [{column: value}]
        """
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

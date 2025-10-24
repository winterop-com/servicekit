# servicekit.data

Universal data schemas for HTTP APIs.

## Overview

The `servicekit.data` module provides a single `DataFrame` schema that works with multiple data libraries (pandas, polars, xarray) while maintaining a simple, universal representation.

## Quick Start

```python
from servicekit.data import DataFrame

# From pandas
import pandas as pd
df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
schema = DataFrame.from_pandas(df)

# From polars (requires: uv add polars)
import polars as pl
df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
schema = DataFrame.from_polars(df)

# From dict
schema = DataFrame.from_dict({"a": [1, 2], "b": [3, 4]})

# From records
schema = DataFrame.from_records([{"a": 1, "b": 3}, {"a": 2, "b": 4}])

# Convert back
pandas_df = schema.to_pandas()
polars_df = schema.to_polars()
dict_data = schema.to_dict(orient="list")
records = schema.to_dict(orient="records")
```

## API Reference

### DataFrame

Universal schema for tabular data.

**Fields:**
- `columns: list[str]` - Column names
- `data: list[list[Any]]` - Row data

**Class Methods:**

| Method | Description | Requires |
|--------|-------------|----------|
| `from_pandas(df)` | Create from pandas DataFrame | `pandas` |
| `from_polars(df)` | Create from Polars DataFrame | `polars` |
| `from_xarray(da)` | Create from xarray DataArray (2D) | `xarray` |
| `from_dict(data)` | Create from dict of columns | - |
| `from_records(records)` | Create from list of dicts | - |
| `from_dataframe(df)` | Alias for `from_pandas()` | `pandas` |

**Instance Methods:**

*Conversion:*
| Method | Description | Requires |
|--------|-------------|----------|
| `to_pandas()` | Convert to pandas DataFrame | `pandas` |
| `to_polars()` | Convert to Polars DataFrame | `polars` |
| `to_dict(orient)` | Convert to dict (orient: dict/list/records) | - |
| `to_csv(path)` | Export to CSV file or string | - |
| `to_json(orient)` | Export as JSON string | - |
| `to_dataframe()` | Alias for `to_pandas()` | `pandas` |

*Data Manipulation:*
| Method | Description | Requires |
|--------|-------------|----------|
| `filter(predicate)` | Filter rows using predicate function | - |
| `apply(func, column)` | Apply function to column values | - |
| `add_column(name, values)` | Add new column to DataFrame | - |
| `drop_rows(indices)` | Drop rows by index | - |
| `drop_duplicates(subset)` | Remove duplicate rows | - |
| `fillna(value/dict)` | Replace None values | - |
| `concat(other)` | Concatenate DataFrames vertically | - |
| `melt(id_vars, value_vars, var_name, value_name)` | Unpivot DataFrame from wide to long format | - |
| `pivot(index, columns, values)` | Pivot DataFrame from long to wide format | - |
| `transpose()` | Swap rows and columns (matrix transpose) | - |
| `merge(other, on, how, left_on, right_on, suffixes)` | Merge DataFrames using database-style joins | - |

*Missing Data:*
| Method | Description | Requires |
|--------|-------------|----------|
| `isna()` | Return DataFrame of booleans showing None locations | - |
| `notna()` | Return DataFrame of booleans showing non-None locations | - |
| `dropna(axis, how)` | Remove rows or columns with None values | - |
| `has_nulls()` | Check for None values per column | - |

*Statistical Analysis:*
| Method | Description | Requires |
|--------|-------------|----------|
| `describe()` | Generate summary statistics | - |
| `groupby(column)` | Group by column values (returns GroupBy) | - |
| `unique(column)` | Get unique values from column | - |
| `value_counts(column)` | Count occurrences of each value | - |
| `nunique(column)` | Count unique values in column | - |

*Utilities:*
| Method | Description | Requires |
|--------|-------------|----------|
| `equals(other)` | Check if two DataFrames are identical | - |
| `deepcopy()` | Create independent copy of DataFrame | - |
| `head(n)` | Return first n rows | - |
| `tail(n)` | Return last n rows | - |
| `sample(n, frac)` | Return random sample of rows | - |
| `select(columns)` | Keep only specified columns | - |
| `drop(columns)` | Remove specified columns | - |
| `rename(mapper)` | Rename columns | - |
| `rename_columns(mapper)` | Rename columns (alias for rename) | - |
| `sort(by, ascending)` | Sort DataFrame by column | - |
| `validate_structure()` | Validate DataFrame integrity | - |
| `infer_types()` | Infer column data types | - |

## Installation

The `DataFrame` class is included in servicekit core. Install the data libraries you need separately:

```bash
# For pandas support
uv add pandas

# For Polars support
uv add polars

# For xarray support
uv add xarray

# Or install multiple libraries
uv add pandas polars xarray
```

Each method will provide a helpful error message if the required library is not installed.

## Examples

### REST API with Multiple Formats

```python
from servicekit.data import DataFrame
from pydantic import BaseModel

class DataRequest(BaseModel):
    data: DataFrame
    format: str = "pandas"

@app.post("/process")
async def process_data(request: DataRequest):
    # Client sends universal format
    if request.format == "pandas":
        df = request.data.to_pandas()
        # Process with pandas
    elif request.format == "polars":
        df = request.data.to_polars()
        # Process with polars

    # Return universal format
    result = DataFrame.from_pandas(processed_df)
    return {"result": result}
```

### Data Transformation Service

See `examples/vega_visualization/` for a complete example of using `DataFrame` to build a data transformation service (DataFrame → Vega-Lite specs).

### Simple Usage Examples

See `examples/dataframe_usage/` for simple standalone examples:
- `pandas_example.py` - pandas conversion
- `polars_example.py` - Polars conversion
- `xarray_example.py` - xarray conversion

## Design Philosophy

The `DataFrame` schema uses a simple `columns` + `data` representation that is:

1. **Library-agnostic**: No dependency on specific data libraries
2. **HTTP-friendly**: Easily serializable to JSON
3. **Universal**: Works with pandas, polars, xarray, and plain Python
4. **Lightweight**: Minimal dependencies in core servicekit

This allows services to accept and return data in a universal format while internally using any data processing library they prefer.

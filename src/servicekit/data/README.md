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

# From polars (requires: uv add 'servicekit[polars]')
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
| `from_pandas(df)` | Create from pandas DataFrame | `[data]` |
| `from_polars(df)` | Create from Polars DataFrame | `[polars]` |
| `from_xarray(da)` | Create from xarray DataArray (2D) | `[xarray]` |
| `from_dict(data)` | Create from dict of columns | - |
| `from_records(records)` | Create from list of dicts | - |
| `from_dataframe(df)` | Alias for `from_pandas()` | `[data]` |

**Instance Methods:**

| Method | Description | Requires |
|--------|-------------|----------|
| `to_pandas()` | Convert to pandas DataFrame | `[data]` |
| `to_polars()` | Convert to Polars DataFrame | `[polars]` |
| `to_dict(orient)` | Convert to dict (orient: dict/list/records) | - |
| `to_dataframe()` | Alias for `to_pandas()` | `[data]` |

## Installation

```bash
# Pandas support
uv add 'servicekit[data]'

# Polars support
uv add 'servicekit[polars]'

# Xarray support
uv add 'servicekit[xarray]'

# All formats
uv add 'servicekit[data,polars,xarray]'
```

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

## Backwards Compatibility

The old `PandasDataFrame` name is still available as an alias:

```python
from servicekit.data import PandasDataFrame  # Works
from servicekit.data import DataFrame        # Preferred
```

## Design Philosophy

The `DataFrame` schema uses a simple `columns` + `data` representation that is:

1. **Library-agnostic**: No dependency on specific data libraries
2. **HTTP-friendly**: Easily serializable to JSON
3. **Universal**: Works with pandas, polars, xarray, and plain Python
4. **Lightweight**: Minimal dependencies in core servicekit

This allows services to accept and return data in a universal format while internally using any data processing library they prefer.

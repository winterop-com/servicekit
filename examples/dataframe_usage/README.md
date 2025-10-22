# DataFrame Usage Examples

Simple standalone examples demonstrating how to use servicekit's `DataFrame` class with different data libraries.

## Prerequisites

Install servicekit:

```bash
uv add servicekit
```

Then install the data library you want to use:

```bash
# For pandas
uv add pandas

# For Polars
uv add polars

# For xarray
uv add xarray numpy
```

## Examples

### Pandas Example

```bash
python pandas_example.py
```

Shows how to:
- Convert pandas DataFrame to servicekit DataFrame
- Convert servicekit DataFrame back to pandas

### Polars Example

```bash
python polars_example.py
```

Shows how to:
- Convert Polars DataFrame to servicekit DataFrame
- Convert servicekit DataFrame back to Polars

### xarray Example

```bash
python xarray_example.py
```

Shows how to:
- Convert xarray DataArray (2D) to servicekit DataFrame
- Convert to pandas for further processing

## DataFrame Class

The `DataFrame` class provides a universal interchange format for tabular data. It stores data in a simple column-oriented structure:

```python
from servicekit.data import DataFrame

df = DataFrame(
    columns=["name", "age"],
    data=[["Alice", 25], ["Bob", 30]]
)
```

### Available Methods

**From other formats:**
- `DataFrame.from_pandas(df)` - requires `pandas`
- `DataFrame.from_polars(df)` - requires `polars`
- `DataFrame.from_xarray(da)` - requires `xarray` (2D DataArrays only)
- `DataFrame.from_dict(data)` - no extra dependencies
- `DataFrame.from_records(records)` - no extra dependencies

**To other formats:**
- `df.to_pandas()` - requires `pandas`
- `df.to_polars()` - requires `polars`
- `df.to_dict(orient="dict"|"list"|"records")` - no extra dependencies

Each method will provide a helpful error message if the required library is not installed.

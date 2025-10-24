# DataFrame Usage Examples

Comprehensive examples demonstrating how to use servicekit's `DataFrame` class for data interchange, transformation, and API integration.

## Prerequisites

Install servicekit:

```bash
uv add servicekit
```

For library-specific examples, install the required library:

```bash
# For pandas
uv add pandas

# For Polars
uv add polars

# For xarray
uv add xarray numpy

# For API integration
uv add fastapi uvicorn
```

## Examples

### Core Features (No Extra Dependencies)

#### CSV Example
```bash
python csv_example.py
```

Shows how to:
- Read and write CSV files
- Convert to/from CSV strings
- Use custom delimiters (TSV)
- Handle headers and no-header files
- Round-trip CSV data

#### Data Inspection Example
```bash
python inspection_example.py
```

Shows how to:
- Use DataFrame properties (shape, size, empty, etc.)
- View data with head() and tail()
- Use negative indexing (pandas-style)
- Random sampling with sample()
- Reproducible sampling with random_state

#### Column Operations Example
```bash
python column_operations_example.py
```

Shows how to:
- Select specific columns
- Drop unwanted columns
- Rename columns
- Chain operations together
- Handle errors gracefully

#### Validation Example
```bash
python validation_example.py
```

Shows how to:
- Validate DataFrame structure
- Infer column data types
- Detect null values
- Handle mixed type columns
- Generate data quality reports

#### API Integration Example
```bash
python api_integration_example.py
```

Shows how to:
- Upload CSV data via API
- Validate data quality
- Download data as CSV
- Transform data with operations
- Generate data statistics
- Sample random data

Then visit http://localhost:8000/docs for interactive API documentation.

### Library Integration Examples

#### Pandas Example
```bash
python pandas_example.py
```

Shows how to:
- Convert pandas DataFrame to servicekit DataFrame
- Convert servicekit DataFrame back to pandas

#### Polars Example
```bash
python polars_example.py
```

Shows how to:
- Convert Polars DataFrame to servicekit DataFrame
- Convert servicekit DataFrame back to Polars

#### xarray Example
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

### Feature Overview

#### Creating DataFrames
- `DataFrame.from_dict(data)` - From dictionary (no dependencies)
- `DataFrame.from_records(records)` - From list of dicts (no dependencies)
- `DataFrame.from_csv(path/csv_string)` - From CSV (no dependencies)
- `DataFrame.from_pandas(df)` - From pandas (requires pandas)
- `DataFrame.from_polars(df)` - From polars (requires polars)
- `DataFrame.from_xarray(da)` - From xarray (requires xarray)

#### Exporting DataFrames
- `df.to_dict(orient)` - To dictionary (no dependencies)
- `df.to_csv(path)` - To CSV file/string (no dependencies)
- `df.to_pandas()` - To pandas (requires pandas)
- `df.to_polars()` - To polars (requires polars)

#### Properties
- `df.shape` - (rows, columns) tuple
- `df.num_rows` - Number of rows
- `df.num_columns` - Number of columns
- `df.size` - Total elements (rows × columns)
- `df.empty` - True if no rows or columns
- `df.ndim` - Always 2 (2-dimensional)

#### Data Inspection
- `df.head(n)` - First n rows (default 5)
- `df.tail(n)` - Last n rows (default 5)
- `df.sample(n/frac, random_state)` - Random sample

#### Column Operations
- `df.select(columns)` - Keep only specified columns
- `df.drop(columns)` - Remove specified columns
- `df.rename(mapper)` - Rename columns

#### Validation
- `df.validate_structure()` - Validate DataFrame integrity
- `df.infer_types()` - Infer column data types
- `df.has_nulls()` - Check for None values per column

### Type Support

Inferred types from `infer_types()`:
- `"int"` - All integers
- `"float"` - All floats (or mix of int/float)
- `"str"` - All strings
- `"bool"` - All booleans
- `"null"` - All None values
- `"mixed"` - Multiple different types

Each method will provide a helpful error message if a required library is not installed.

## Additional Resources

- See [DataFrame Guide](../../docs/guides/dataframe.md) for comprehensive documentation
- Visit the [examples directory](../) for more servicekit examples

# DataFrame Data Interchange

Servicekit provides a universal DataFrame class for seamless data interchange between different data libraries (pandas, polars, xarray) and file formats (CSV, Parquet). It's designed to be lightweight, framework-agnostic, and easy to use in API services.

## Quick Start

### Basic Usage

```python
from servicekit.data import DataFrame

# Create from dictionary
df = DataFrame.from_dict({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [25, 30, 35],
    "city": ["NYC", "SF", "LA"]
})

# Inspect data
print(df.shape)  # (3, 3)
print(df.head(2))

# Convert to other libraries
pandas_df = df.to_pandas()
polars_df = df.to_polars()
```

### In FastAPI Services

```python
from fastapi import FastAPI, UploadFile
from fastapi.responses import Response
from servicekit.data import DataFrame

app = FastAPI()

@app.post("/data/$upload")
async def upload_csv(file: UploadFile):
    """Accept CSV upload and process."""
    content = await file.read()
    df = DataFrame.from_csv(csv_string=content.decode())

    # Process data
    df = df.select(["name", "age"]).head(100)

    return {"rows": df.shape[0], "columns": df.columns}

@app.get("/data/$download")
async def download_csv():
    """Export data as CSV."""
    df = get_data()  # Your data source
    csv_data = df.to_csv()
    return Response(content=csv_data, media_type="text/csv")
```

## Core Concepts

### Data Structure

DataFrame uses a simple columnar structure:

```python
df = DataFrame(
    columns=["name", "age"],
    data=[
        ["Alice", 25],
        ["Bob", 30]
    ]
)
```

- **columns**: List of column names (strings)
- **data**: List of rows, where each row is a list of values
- **Type-agnostic**: Values can be any Python type

### Design Principles

- **Lightweight**: No required dependencies beyond Pydantic
- **Framework-agnostic**: Works with any Python environment
- **Lazy imports**: Optional libraries loaded only when needed
- **Immutable**: Methods return new DataFrames (no in-place modification)
- **API consistency**: All methods follow `from_X()` / `to_X()` pattern

## Creating DataFrames

### From Dictionary

```python
# Column-oriented (dict of lists)
df = DataFrame.from_dict({
    "name": ["Alice", "Bob"],
    "age": [25, 30]
})
```

### From Records

```python
# Row-oriented (list of dicts)
df = DataFrame.from_records([
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30}
])
```

### From CSV

```python
# From file
df = DataFrame.from_csv("data.csv")

# From string
csv_string = "name,age\nAlice,25\nBob,30"
df = DataFrame.from_csv(csv_string=csv_string)

# Custom delimiter
df = DataFrame.from_csv("data.tsv", delimiter="\t")

# Without header
df = DataFrame.from_csv("data.csv", has_header=False)
# Generates columns: col_0, col_1, ...
```

### From Other Libraries

```python
# From pandas
import pandas as pd
pandas_df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
df = DataFrame.from_pandas(pandas_df)

# From polars
import polars as pl
polars_df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
df = DataFrame.from_polars(polars_df)

# From xarray (2D only)
import xarray as xr
data_array = xr.DataArray([[1, 2], [3, 4]])
df = DataFrame.from_xarray(data_array)
```

## Exporting DataFrames

### To CSV

```python
# To file
df.to_csv("output.csv")

# To string
csv_string = df.to_csv()

# Without header
df.to_csv("output.csv", include_header=False)

# Custom delimiter
df.to_csv("output.tsv", delimiter="\t")
```

### To Dictionary

```python
# As dict of lists (default)
data = df.to_dict(orient="list")
# {"name": ["Alice", "Bob"], "age": [25, 30]}

# As list of records
data = df.to_dict(orient="records")
# [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]

# As dict of dicts
data = df.to_dict(orient="dict")
# {"name": {0: "Alice", 1: "Bob"}, "age": {0: 25, 1: 30}}
```

### To Other Libraries

```python
# To pandas
pandas_df = df.to_pandas()

# To polars
polars_df = df.to_polars()
```

## Data Inspection

### Properties

```python
# Shape (rows, columns)
print(df.shape)  # (100, 5)

# Number of rows
print(df.shape[0])  # 100
print(len(df))  # 100 - can also use len()

# Number of columns
print(df.shape[1])  # 5

# Check if empty
print(df.empty)  # False

# Number of dimensions (always 2)
print(df.ndim)  # 2

# Total elements
print(df.size)  # 500 (100 * 5)
```

### Viewing Data

```python
# First 5 rows (default)
df.head()

# First n rows
df.head(10)

# Last 5 rows (default)
df.tail()

# Last n rows
df.tail(10)

# Negative indexing (pandas-style)
df.head(-3)  # All except last 3 rows
df.tail(-3)  # All except first 3 rows
```

### Random Sampling

```python
# Sample n rows
sample = df.sample(n=100)

# Sample fraction
sample = df.sample(frac=0.1)  # 10% of rows

# Reproducible sampling
sample = df.sample(n=50, random_state=42)
```

### Iteration

```python
# Iterate over rows as dictionaries
for row in df:
    print(row)  # {'name': 'Alice', 'age': 25}

# Get number of rows with len()
num_rows = len(df)

# Use in list comprehensions
names = [row['name'] for row in df]
```

## Column Operations

### Accessing Columns

```python
# Get column values as list
ages = df.get_column("age")  # [25, 30, 35]
ages = df["age"]  # Same using [] syntax

# Select multiple columns as DataFrame
df_subset = df[["name", "age"]]
df_subset = df.select(["name", "age"])  # Equivalent
```

### Selecting Columns

```python
# Select specific columns
df_subset = df.select(["name", "age"])

# Single column
df_single = df.select(["age"])
```

### Dropping Columns

```python
# Drop specific columns
df_clean = df.drop(["temp_column", "debug_field"])

# Drop multiple
df_clean = df.drop(["col1", "col2", "col3"])
```

### Renaming Columns

```python
# Rename specific columns
df_renamed = df.rename({
    "old_name": "new_name",
    "user_id": "id"
})

# Partial rename (other columns unchanged)
df_renamed = df.rename({"age": "years"})
```

## Validation and Type Inference

### Structure Validation

```python
# Validate DataFrame structure
try:
    df.validate_structure()
    print("DataFrame is valid")
except ValueError as e:
    print(f"Validation failed: {e}")

# Checks performed:
# - All rows have same length as columns
# - Column names are unique
# - No empty column names
```

### Type Inference

```python
# Infer column data types
types = df.infer_types()
print(types)
# {"age": "int", "name": "str", "score": "float"}

# Supported types:
# - "int": All integers
# - "float": All floats (or mix of int/float)
# - "str": All strings
# - "bool": All booleans
# - "null": All None values
# - "mixed": Multiple different types
```

### Null Detection

```python
# Check for None values per column
nulls = df.has_nulls()
print(nulls)
# {"age": False, "email": True, "phone": True}

# Use for data quality checks
if any(nulls.values()):
    print("Warning: DataFrame contains null values")
```

## Sorting and Analytics

### Sorting

```python
# Sort by column (ascending)
df_sorted = df.sort("age")

# Sort descending
df_sorted = df.sort("score", ascending=False)

# None values always sort to the end
df_sorted = df.sort("nullable_column")
```

### Unique Values

```python
# Get unique values from a column
categories = df.unique("category")
# ['A', 'B', 'C'] - preserves order of first appearance

# Count unique values
num_unique = len(df.unique("category"))
```

### Value Counts

```python
# Count occurrences of each value
counts = df.value_counts("category")
# {'A': 3, 'B': 2, 'C': 1}

# Find most common value
most_common = max(counts, key=counts.get)

# Get distribution
total = len(df)
distribution = {k: v/total for k, v in counts.items()}
```

## JSON Support

### Creating from JSON

```python
# From JSON array of objects
json_data = '[{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]'
df = DataFrame.from_json(json_data)

# From API response
import requests
response = requests.get("https://api.example.com/data")
df = DataFrame.from_json(response.text)
```

### Exporting to JSON

```python
# As array of objects (records format)
json_str = df.to_json(orient="records")
# '[{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]'

# As object with arrays (columns format)
json_str = df.to_json(orient="columns")
# '{"name": ["Alice", "Bob"], "age": [25, 30]}'

# For API responses
from fastapi import Response

@app.get("/data")
async def get_data():
    df = get_dataframe()
    return Response(content=df.to_json(), media_type="application/json")
```

## Common Patterns

### Data Pipeline

```python
# Read, process, write
df = (
    DataFrame.from_csv("input.csv")
    .select(["name", "age", "score"])
    .rename({"score": "grade"})
    .head(1000)
)
df.to_csv("output.csv")
```

### API Data Validation

```python
from fastapi import FastAPI, HTTPException
from servicekit.data import DataFrame

@app.post("/data/$validate")
async def validate_data(file: UploadFile):
    """Validate uploaded CSV data."""
    content = await file.read()
    df = DataFrame.from_csv(csv_string=content.decode())

    # Validate structure
    try:
        df.validate_structure()
    except ValueError as e:
        raise HTTPException(400, f"Invalid structure: {e}")

    # Check required columns
    required = ["user_id", "timestamp", "value"]
    missing = set(required) - set(df.columns)
    if missing:
        raise HTTPException(400, f"Missing columns: {missing}")

    # Check for nulls
    nulls = df.has_nulls()
    if any(nulls.get(col, False) for col in required):
        raise HTTPException(400, "Required columns contain null values")

    # Return metadata
    return {
        "rows": df.shape[0],
        "columns": df.columns,
        "types": df.infer_types(),
        "sample": df.head(5).to_dict(orient="records")
    }
```

### Data Transformation

```python
def clean_dataframe(df: DataFrame) -> DataFrame:
    """Clean and standardize DataFrame."""
    # Remove unnecessary columns
    df = df.drop(["temp", "debug"])

    # Rename for consistency
    df = df.rename({
        "user_name": "name",
        "user_age": "age"
    })

    # Validate
    df.validate_structure()

    return df
```

### Format Conversion

```python
# CSV to Pandas
df = DataFrame.from_csv("data.csv")
pandas_df = df.to_pandas()

# Pandas to CSV
df = DataFrame.from_pandas(pandas_df)
df.to_csv("output.csv")

# Cross-library conversion
polars_df = DataFrame.from_pandas(pandas_df).to_polars()
```

## API Response Formats

### JSON Response

```python
from fastapi import FastAPI
from servicekit.data import DataFrame

@app.get("/data")
async def get_data():
    """Return data as JSON."""
    df = get_dataframe()
    return df.to_dict(orient="records")
```

### CSV Download

```python
from fastapi.responses import Response

@app.get("/data/export.csv")
async def download_csv():
    """Download data as CSV."""
    df = get_dataframe()
    csv_data = df.to_csv()

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=data.csv"
        }
    )
```

### Paginated Response

```python
from pydantic import BaseModel

class PaginatedData(BaseModel):
    """Paginated DataFrame response."""
    total: int
    page: int
    page_size: int
    data: list[dict]

@app.get("/data", response_model=PaginatedData)
async def get_paginated_data(page: int = 1, page_size: int = 100):
    """Return paginated data."""
    df = get_dataframe()

    # Calculate pagination
    total = df.shape[0]
    start = (page - 1) * page_size

    # Get page using head/tail
    if start + page_size < total:
        page_df = df.tail(-start).head(page_size)
    else:
        page_df = df.tail(-start)

    return PaginatedData(
        total=total,
        page=page,
        page_size=page_size,
        data=page_df.to_dict(orient="records")
    )
```

## Error Handling

### Import Errors

DataFrames with optional dependencies raise clear errors:

```python
try:
    df.to_pandas()
except ImportError as e:
    print(e)
    # "pandas is required for to_pandas(). Install with: uv add pandas"
```

### Validation Errors

```python
# Column not found
try:
    df.select(["nonexistent"])
except KeyError as e:
    print(e)  # "Column 'nonexistent' not found in DataFrame"

# Invalid structure
try:
    df = DataFrame(columns=["a", "b"], data=[[1, 2, 3]])
    df.validate_structure()
except ValueError as e:
    print(e)  # "Row 0 has 3 values, expected 2"
```

### CSV Errors

```python
# File not found
try:
    df = DataFrame.from_csv("missing.csv")
except FileNotFoundError as e:
    print(e)  # "File not found: missing.csv"

# Invalid parameters
try:
    df = DataFrame.from_csv()  # Neither path nor csv_string
except ValueError as e:
    print(e)  # "Either path or csv_string must be provided"
```

## Performance Considerations

### When to Use DataFrame

**Good use cases:**
- API data interchange (JSON ↔ DataFrame ↔ CSV)
- Small to medium datasets (<100k rows)
- Format conversion between libraries
- Data validation and inspection
- Prototyping and development

**Not recommended for:**
- Large datasets (>1M rows) - use pandas/polars directly
- Heavy data transformations - use specialized libraries
- Production analytics - use pandas/polars/DuckDB
- High-performance computing - use NumPy/pandas

### Memory Efficiency

```python
# DataFrame stores data as list of lists (row-oriented)
# For large datasets, convert to columnar format:
pandas_df = df.to_pandas()  # More efficient for operations

# For very large files, consider streaming:
# - Read in chunks with pandas
# - Process incrementally
# - Use DataFrame for API boundaries only
```

## Testing with DataFrame

### Test Data Creation

```python
import pytest
from servicekit.data import DataFrame

@pytest.fixture
def sample_data():
    """Create sample DataFrame for testing."""
    return DataFrame.from_dict({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [95, 87, 92]
    })

def test_data_processing(sample_data):
    """Test data processing pipeline."""
    result = sample_data.select(["name", "score"])
    assert result.shape == (3, 2)
    assert "id" not in result.columns
```

### CSV Round-Trip Testing

```python
def test_csv_roundtrip(tmp_path):
    """Test CSV export and import."""
    # Create test data
    original = DataFrame.from_dict({
        "name": ["Alice", "Bob"],
        "age": [25, 30]
    })

    # Write to file
    csv_file = tmp_path / "test.csv"
    original.to_csv(csv_file)

    # Read back
    restored = DataFrame.from_csv(csv_file)

    # Verify (note: CSV makes all values strings)
    assert restored.columns == original.columns
    assert restored.shape == original.shape
```

## Best Practices

### Recommended Practices

- **Validate early**: Call `validate_structure()` after data ingestion
- **Check types**: Use `infer_types()` to understand your data
- **Handle nulls**: Use `has_nulls()` to detect data quality issues
- **Immutable pattern**: Chain operations without modifying originals
- **Small data**: Use DataFrame for API boundaries, not heavy processing
- **Clear errors**: Let ImportError guide users to install dependencies
- **CSV for interchange**: Use CSV for human-readable data exchange

### Avoid

- **Large datasets**: Don't use for >100k rows (use pandas/polars instead)
- **Heavy operations**: Don't use for joins, aggregations, complex queries
- **In-place modification**: Don't try to modify DataFrames (they're immutable)
- **Type assumptions**: CSV imports make all values strings
- **Missing validation**: Always validate data from external sources

## Dependencies

### Core (Required)
- **pydantic**: For data validation and serialization

### Optional (No Dependencies)
- **CSV support**: Uses Python stdlib `csv` module
- **Data inspection**: Uses Python stdlib `random` module
- **Column operations**: Pure Python (no dependencies)
- **Validation**: Pure Python (no dependencies)

### Optional (With Dependencies)
Install as needed:

```bash
# For pandas support
uv add pandas

# For polars support
uv add polars

# For xarray support
uv add xarray

# For PyArrow/Parquet support (future)
uv add 'servicekit[arrow]'
```

## Examples

### Example Files

See `examples/` directory:
- Basic DataFrame operations
- API integration patterns
- CSV upload/download
- Data validation workflows

### Interactive Session

```python
from servicekit.data import DataFrame

# Create sample data
df = DataFrame.from_dict({
    "product": ["Apple", "Banana", "Cherry", "Date"],
    "price": [1.2, 0.5, 3.0, 2.5],
    "stock": [100, 150, 80, 60]
})

# Explore
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns}")
print(df.head(2))

# Analyze
print(f"Types: {df.infer_types()}")
print(f"Has nulls: {df.has_nulls()}")

# Transform
expensive = df.select(["product", "price"])
print(expensive.to_dict(orient="records"))

# Export
expensive.to_csv("expensive_items.csv")
```

## Troubleshooting

### ImportError for Optional Libraries

**Problem**: Getting ImportError when using pandas/polars methods.

**Solution**:
```bash
# Install required library
uv add pandas  # or polars, xarray
```

### CSV Values All Strings

**Problem**: After `from_csv()`, all values are strings.

**Solution**: CSV format doesn't preserve types. Either:
1. Convert manually after import
2. Use `infer_types()` to detect types
3. Use Parquet for type preservation (future feature)

### Column Not Found Errors

**Problem**: `KeyError: Column 'x' not found`.

**Solution**:
```python
# Check available columns
print(df.columns)

# Case-sensitive matching
df.select(["Name"])  # Error if column is "name"
```

### Memory Issues with Large Data

**Problem**: Running out of memory with large DataFrames.

**Solution**: DataFrame is designed for small-medium data. For large datasets:
```python
# Use pandas directly for large data
import pandas as pd
pandas_df = pd.read_csv("large_file.csv", chunksize=10000)

# Or use polars for better performance
import polars as pl
polars_df = pl.read_csv("large_file.csv")
```

## Next Steps

- **Learn More**: See other guides for integrating DataFrame with APIs
- **Contribute**: Submit PRs for new format support (Parquet, Arrow, etc.)
- **Examples**: Check `examples/` directory for real-world usage

For related features, see:
- [API Development Guide](../README.md) - Building services with servicekit
- [Authentication Guide](authentication.md) - Securing data endpoints
- [Job Scheduler Guide](job-scheduler.md) - Processing DataFrame data in background

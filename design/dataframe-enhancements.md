# DataFrame Enhancement Design Document

**Version:** 1.0
**Status:** Proposal
**Created:** 2025-10-24
**Author:** Claude Code

## Table of Contents

- [Overview](#overview)
- [Motivation](#motivation)
- [Goals](#goals)
- [Non-Goals](#non-goals)
- [Technical Approach](#technical-approach)
- [Proposed API](#proposed-api)
- [Implementation Phases](#implementation-phases)
- [Backward Compatibility](#backward-compatibility)
- [Testing Strategy](#testing-strategy)
- [Dependencies](#dependencies)
- [Examples](#examples)
- [Open Questions](#open-questions)

## Overview

This document proposes enhancements to the `servicekit.data.DataFrame` class to transform it from a basic interchange format into a comprehensive data serialization and interchange library. The enhancements focus on adding I/O capabilities (CSV, Parquet, Arrow), utility methods for data manipulation, and support for additional data libraries while maintaining the lightweight, framework-agnostic design.

## Motivation

### Current State

The `DataFrame` class currently provides:
- Basic structure: `columns` (list) and `data` (list of lists)
- Conversions: pandas, polars, xarray
- Dictionary operations: from_dict, from_records, to_dict
- Lazy dependency loading (no required dependencies)

### Limitations

1. **No File I/O**: Cannot read/write CSV, Parquet, or other common formats
2. **Limited Introspection**: No way to query shape, check if empty, or inspect types
3. **No Data Operations**: Cannot head/tail, select columns, or perform basic transformations
4. **Missing Industry Standards**: No Arrow/Parquet support (de facto standard for data interchange)
5. **No Binary Formats**: Missing MessagePack, Parquet for efficient API responses

### Use Cases Driving These Changes

1. **API Data Exchange**
   - Services need to accept CSV uploads and convert to DataFrame
   - Services need to return data as CSV, Parquet, or JSON depending on client preference
   - Binary formats (Parquet, MessagePack) reduce bandwidth for large datasets

2. **Data Pipeline Integration**
   - ML services need to read training data from CSV files
   - Visualization services need to export chart data as CSV
   - Analytics services need Parquet for efficient columnar storage

3. **Developer Experience**
   - Debugging: Quick inspection with head(), tail(), shape
   - Testing: Easy sample data creation from CSV strings
   - Validation: Type checking and null detection

4. **Interoperability**
   - Arrow IPC format for zero-copy data sharing
   - NumPy for numerical computing integration
   - DuckDB for in-memory SQL queries on DataFrame data

## Goals

1. **Add Essential File I/O**: CSV, Parquet, Arrow formats
2. **Improve Developer Experience**: Utility methods for inspection and manipulation
3. **Support Industry Standards**: PyArrow/Arrow ecosystem integration
4. **Maintain Design Principles**:
   - Lightweight core (no required dependencies)
   - Lazy imports (import only when methods are called)
   - Simple API (consistent from_X / to_X pattern)
   - Framework-agnostic (works in any Python environment)
5. **Enable Performance**: Binary formats for efficient data transfer
6. **Preserve Backward Compatibility**: No breaking changes to existing API

## Non-Goals

1. **Not a DataFrame Library**: We're not replacing pandas/polars, just facilitating interchange
2. **Not a Query Engine**: Complex operations should be done in pandas/polars/DuckDB
3. **Not a Storage System**: This is for data in transit, not persistent storage
4. **No Distributed Computing**: No Dask/Ray integration (leave that to specialized libraries)
5. **No Complex Analytics**: No built-in aggregations, joins beyond basic operations

## Technical Approach

### Design Principles

1. **Lazy Imports**: All library imports happen inside methods
2. **Clear Error Messages**: ImportError messages include installation instructions
3. **Type Safety**: Full type hints, Pydantic validation where appropriate
4. **Consistency**: All methods follow from_X() / to_X() pattern
5. **Optional Dependencies**: Use extras in pyproject.toml for optional features

### Dependency Strategy

```toml
[project.optional-dependencies]
csv = []  # No extra dependencies (use stdlib csv module)
arrow = ["pyarrow>=14.0.0"]  # For Arrow, Parquet, Feather
parquet = ["pyarrow>=14.0.0"]  # Alias for arrow
numpy = ["numpy>=1.24.0"]
duckdb = ["duckdb>=0.9.0"]
msgpack = ["msgpack>=1.0.0"]
excel = ["openpyxl>=3.1.0"]
all = ["pyarrow>=14.0.0", "numpy>=1.24.0", "duckdb>=0.9.0", "msgpack>=1.0.0", "openpyxl>=3.1.0"]
```

### Error Handling Pattern

```python
def from_parquet(cls, path: str | Path) -> Self:
    """Create DataFrame from Parquet file."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError(
            "pyarrow is required for from_parquet(). "
            "Install with: uv add 'servicekit[arrow]'"
        ) from None

    # Implementation...
```

## Proposed API

### Phase 1: Essential I/O (Priority: High)

#### CSV Support

```python
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
    """Create DataFrame from CSV file or string.

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
        >>> df = DataFrame.from_csv(csv_string="a,b\\n1,2\\n3,4")
    """

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
```

#### PyArrow/Arrow Support

```python
@classmethod
def from_arrow(cls, table: Any) -> Self:
    """Create DataFrame from PyArrow Table.

    Args:
        table: PyArrow Table instance

    Returns:
        DataFrame instance

    Raises:
        ImportError: If pyarrow not installed
        TypeError: If input is not a PyArrow Table

    Example:
        >>> import pyarrow as pa
        >>> table = pa.table({"a": [1, 2], "b": [3, 4]})
        >>> df = DataFrame.from_arrow(table)
    """

def to_arrow(self) -> Any:
    """Convert DataFrame to PyArrow Table.

    Returns:
        PyArrow Table

    Raises:
        ImportError: If pyarrow not installed

    Example:
        >>> table = df.to_arrow()
        >>> print(table.schema)
    """
```

#### Parquet Support

```python
@classmethod
def from_parquet(
    cls,
    path: str | Path,
    *,
    columns: list[str] | None = None,
) -> Self:
    """Create DataFrame from Parquet file.

    Args:
        path: Path to Parquet file
        columns: Specific columns to read (None = all)

    Returns:
        DataFrame instance

    Raises:
        ImportError: If pyarrow not installed
        FileNotFoundError: If path does not exist

    Example:
        >>> df = DataFrame.from_parquet("data.parquet")
        >>> df = DataFrame.from_parquet("data.parquet", columns=["a", "b"])
    """

def to_parquet(
    self,
    path: str | Path | None = None,
    *,
    compression: str = "snappy",
) -> bytes | None:
    """Export DataFrame to Parquet file or bytes.

    Args:
        path: Path to write Parquet file (if None, returns bytes)
        compression: Compression codec (snappy, gzip, brotli, zstd, none)

    Returns:
        Parquet bytes if path is None, otherwise None

    Example:
        >>> df.to_parquet("output.parquet")
        >>> parquet_bytes = df.to_parquet()  # Returns bytes for API response
    """
```

#### Utility Properties

```python
@property
def shape(self) -> tuple[int, int]:
    """Return (num_rows, num_columns)."""
    return (len(self.data), len(self.columns))

@property
def num_rows(self) -> int:
    """Return number of rows."""
    return len(self.data)

@property
def num_columns(self) -> int:
    """Return number of columns."""
    return len(self.columns)

@property
def is_empty(self) -> bool:
    """Return True if DataFrame has no rows."""
    return len(self.data) == 0
```

### Phase 2: Developer Experience (Priority: Medium)

#### Data Inspection Methods

```python
def head(self, n: int = 5) -> Self:
    """Return first n rows.

    Args:
        n: Number of rows to return

    Returns:
        New DataFrame with first n rows

    Example:
        >>> df.head(10)
    """

def tail(self, n: int = 5) -> Self:
    """Return last n rows."""

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

    Example:
        >>> df.sample(n=100)
        >>> df.sample(frac=0.1)
    """
```

#### Column Operations

```python
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

def rename(self, mapper: dict[str, str]) -> Self:
    """Return DataFrame with renamed columns.

    Args:
        mapper: Dictionary mapping old names to new names

    Returns:
        New DataFrame with renamed columns

    Raises:
        KeyError: If any old column name does not exist

    Example:
        >>> df.rename({"old_name": "new_name"})
    """
```

#### Validation Methods

```python
def validate(self) -> None:
    """Validate DataFrame structure.

    Checks:
    - All rows have same length as columns
    - Column names are unique
    - No null/empty column names

    Raises:
        ValueError: If validation fails

    Example:
        >>> df.validate()
    """

def infer_types(self) -> dict[str, str]:
    """Infer column data types.

    Returns:
        Dictionary mapping column names to type strings
        Types: "int", "float", "str", "bool", "null", "mixed"

    Example:
        >>> df.infer_types()
        {"age": "int", "name": "str", "score": "float"}
    """

def has_nulls(self) -> dict[str, bool]:
    """Check for null values in each column.

    Returns:
        Dictionary mapping column names to boolean
        True if column contains None values

    Example:
        >>> df.has_nulls()
        {"age": False, "email": True}
    """
```

### Phase 3: Advanced Formats (Priority: Low)

#### JSON Lines (JSONL)

```python
@classmethod
def from_jsonl(
    cls,
    path: str | Path | None = None,
    *,
    jsonl_string: str | None = None,
) -> Self:
    """Create DataFrame from JSON Lines file or string.

    Each line is a JSON object representing one row.

    Example:
        >>> df = DataFrame.from_jsonl("data.jsonl")
        >>> df = DataFrame.from_jsonl(jsonl_string='{"a":1}\\n{"a":2}')
    """

def to_jsonl(
    self,
    path: str | Path | None = None,
) -> str | None:
    """Export DataFrame to JSON Lines format."""
```

#### NumPy Support

```python
@classmethod
def from_numpy(
    cls,
    array: Any,
    columns: list[str] | None = None,
) -> Self:
    """Create DataFrame from NumPy array.

    Args:
        array: 2D NumPy array
        columns: Column names (generated if None)

    Example:
        >>> import numpy as np
        >>> arr = np.array([[1, 2], [3, 4]])
        >>> df = DataFrame.from_numpy(arr, columns=["a", "b"])
    """

def to_numpy(self) -> Any:
    """Convert DataFrame to NumPy array.

    Returns:
        2D NumPy array (columns × rows)
    """
```

#### DuckDB Support

```python
def to_duckdb(self) -> Any:
    """Convert DataFrame to DuckDB relation.

    Returns:
        DuckDB relation (query-able object)

    Example:
        >>> rel = df.to_duckdb()
        >>> result = rel.filter("age > 18").df()
    """

@classmethod
def from_duckdb(cls, relation: Any) -> Self:
    """Create DataFrame from DuckDB relation.

    Args:
        relation: DuckDB relation object

    Example:
        >>> df = DataFrame.from_duckdb(rel)
    """

def query(self, sql: str) -> Self:
    """Run SQL query on DataFrame using DuckDB.

    Args:
        sql: SQL query (use 'df' as table name)

    Returns:
        New DataFrame with query results

    Raises:
        ImportError: If duckdb not installed

    Example:
        >>> result = df.query("SELECT * FROM df WHERE age > 18")
        >>> result = df.query("SELECT name, AVG(score) FROM df GROUP BY name")
    """
```

### Phase 4: Specialized Formats (Priority: Very Low)

#### MessagePack Support

```python
@classmethod
def from_msgpack(cls, data: bytes) -> Self:
    """Create DataFrame from MessagePack bytes."""

def to_msgpack(self) -> bytes:
    """Export DataFrame to MessagePack format.

    More efficient than JSON for binary APIs.
    """
```

#### Excel Support

```python
@classmethod
def from_excel(
    cls,
    path: str | Path,
    sheet_name: str | int = 0,
) -> Self:
    """Create DataFrame from Excel file."""

def to_excel(
    self,
    path: str | Path,
    sheet_name: str = "Sheet1",
) -> None:
    """Export DataFrame to Excel file."""
```

#### Arrow IPC/Feather

```python
@classmethod
def from_feather(cls, path: str | Path) -> Self:
    """Create DataFrame from Feather file.

    Fast binary format for local interchange.
    """

def to_feather(self, path: str | Path) -> None:
    """Export DataFrame to Feather format."""
```

## Implementation Phases

### Phase 1: Essential I/O (2-3 weeks)

**Deliverables:**
- CSV read/write methods
- PyArrow Table conversions
- Parquet read/write methods
- Utility properties (shape, is_empty, num_rows, num_columns)
- Comprehensive tests with mocked dependencies
- Documentation with examples

**Testing:**
- Unit tests for CSV parsing edge cases
- Integration tests with actual PyArrow (when installed)
- Mock tests for import errors
- Performance benchmarks for large datasets

**PR Strategy:**
- Single PR with all Phase 1 features
- Update servicekit[arrow] extras in pyproject.toml
- Add examples to examples/dataframe_usage/

### Phase 2: Developer Experience (1-2 weeks)

**Deliverables:**
- head/tail/sample methods
- select/drop/rename column operations
- validate/infer_types/has_nulls inspection
- Tests for all methods
- Documentation updates

**Testing:**
- Unit tests for all methods
- Edge cases (empty DataFrames, single column, etc.)
- Integration with Phase 1 features

**PR Strategy:**
- Single PR for all Phase 2 features
- Can be developed in parallel with Phase 1

### Phase 3: Advanced Formats (2 weeks)

**Deliverables:**
- JSON Lines support
- NumPy conversions
- DuckDB integration with SQL query support
- Tests and documentation

**Testing:**
- Integration tests with NumPy and DuckDB
- SQL query correctness tests
- Performance tests for DuckDB queries

**PR Strategy:**
- Separate PRs for each library integration
- NumPy (small, quick)
- DuckDB + SQL (larger, needs review)

### Phase 4: Specialized Formats (1 week, optional)

**Deliverables:**
- MessagePack support
- Excel support
- Feather/Arrow IPC

**Testing:**
- Format round-trip tests
- Binary correctness verification

**PR Strategy:**
- Low priority, implement if there's demand
- Separate PRs for each format

## Backward Compatibility

### Breaking Changes: None

All additions are new methods. Existing API remains unchanged:
- `columns` and `data` fields unchanged
- All existing methods work exactly as before
- No changes to serialization format

### Deprecated Features: None

No deprecations in this proposal.

### Migration Path: N/A

No migration needed. New features are purely additive.

## Testing Strategy

### Unit Tests

1. **CSV Module**
   - `test_from_csv_file()` - Read from file path
   - `test_from_csv_string()` - Read from string
   - `test_to_csv_file()` - Write to file
   - `test_to_csv_string()` - Return as string
   - `test_csv_custom_delimiter()` - Semicolon, tab, etc.
   - `test_csv_no_header()` - Generate column names
   - `test_csv_empty()` - Empty DataFrame

2. **Arrow/Parquet Module**
   - `test_from_arrow_table()` - Convert from PyArrow
   - `test_to_arrow_table()` - Convert to PyArrow
   - `test_from_parquet()` - Read Parquet file
   - `test_to_parquet_file()` - Write Parquet file
   - `test_to_parquet_bytes()` - Return bytes
   - `test_parquet_compression()` - Different codecs
   - `test_arrow_not_installed()` - ImportError handling

3. **Utility Methods**
   - `test_shape_property()` - Correct dimensions
   - `test_is_empty()` - Empty detection
   - `test_head()` - First n rows
   - `test_tail()` - Last n rows
   - `test_sample()` - Random sampling
   - `test_select_columns()` - Column selection
   - `test_drop_columns()` - Column dropping
   - `test_rename_columns()` - Column renaming

4. **Validation**
   - `test_validate_success()` - Valid DataFrame
   - `test_validate_unequal_rows()` - Catch errors
   - `test_infer_types()` - Type detection
   - `test_has_nulls()` - Null detection

### Integration Tests

1. **Round-trip Tests**
   - pandas → DataFrame → pandas
   - polars → DataFrame → polars
   - DataFrame → CSV → DataFrame
   - DataFrame → Parquet → DataFrame
   - DataFrame → Arrow → DataFrame

2. **Cross-library Tests**
   - pandas → DataFrame → polars
   - DataFrame → Arrow → DuckDB
   - NumPy → DataFrame → pandas

### Performance Tests

1. **Benchmarks**
   - Large CSV (10M rows) read/write
   - Parquet vs CSV performance
   - Arrow zero-copy performance
   - Memory usage for large DataFrames

2. **Profiling**
   - Identify bottlenecks in conversions
   - Optimize hot paths

### CI/CD Integration

```yaml
# .github/workflows/test.yml
test-dataframe:
  strategy:
    matrix:
      optional-deps:
        - "none"  # Test without optional dependencies
        - "arrow"  # Test with PyArrow
        - "all"  # Test with all dependencies
  steps:
    - name: Install dependencies
      run: |
        if [ "${{ matrix.optional-deps }}" = "none" ]; then
          uv sync
        else
          uv sync --extra ${{ matrix.optional-deps }}
        fi
    - name: Run tests
      run: make test
```

## Dependencies

### Required (No Changes)

- Python 3.13+
- pydantic

### Optional (New)

```toml
[project.optional-dependencies]
csv = []  # Uses stdlib csv module
arrow = ["pyarrow>=14.0.0"]
parquet = ["pyarrow>=14.0.0"]  # Alias for arrow
numpy = ["numpy>=1.24.0"]
duckdb = ["duckdb>=0.9.0"]
msgpack = ["msgpack>=1.0.0"]
excel = ["openpyxl>=3.1.0"]
all = [
    "pyarrow>=14.0.0",
    "numpy>=1.24.0",
    "duckdb>=0.9.0",
    "msgpack>=1.0.0",
    "openpyxl>=3.1.0",
]
```

### Why These Libraries?

- **PyArrow**: Industry standard for Arrow format, required for Parquet
- **NumPy**: Fundamental library for numerical computing
- **DuckDB**: Fast in-memory SQL engine, perfect for DataFrame queries
- **msgpack**: Efficient binary serialization
- **openpyxl**: Excel file support (business users)

## Examples

### Example 1: CSV I/O in API

```python
from fastapi import UploadFile
from servicekit.data import DataFrame

@app.post("/data/$upload")
async def upload_csv(file: UploadFile):
    """Accept CSV upload and store as DataFrame."""
    content = await file.read()
    df = DataFrame.from_csv(csv_string=content.decode())

    # Process data...
    df = df.select(["name", "age", "email"])
    df = df.head(1000)  # Limit to 1000 rows

    # Store or process...
    return {"rows": df.num_rows, "columns": df.columns}

@app.get("/data/$download")
async def download_csv(format: str = "csv"):
    """Export data as CSV or Parquet."""
    df = get_dataframe()  # Load from storage

    if format == "csv":
        csv_data = df.to_csv()
        return Response(content=csv_data, media_type="text/csv")
    elif format == "parquet":
        parquet_bytes = df.to_parquet()
        return Response(content=parquet_bytes, media_type="application/vnd.apache.parquet")
```

### Example 2: Data Validation Pipeline

```python
from servicekit.data import DataFrame

def validate_upload(df: DataFrame) -> dict:
    """Validate uploaded DataFrame."""
    # Check structure
    df.validate()

    # Inspect data
    info = {
        "shape": df.shape,
        "types": df.infer_types(),
        "nulls": df.has_nulls(),
        "sample": df.head(5).to_dict(orient="records"),
    }

    # Check for required columns
    required = ["user_id", "timestamp", "value"]
    if not all(col in df.columns for col in required):
        raise ValueError(f"Missing required columns: {required}")

    return info
```

### Example 3: SQL Queries on DataFrame

```python
from servicekit.data import DataFrame

# Load data
df = DataFrame.from_csv("sales.csv")

# Run SQL query
result = df.query("""
    SELECT
        product,
        SUM(quantity) as total_qty,
        AVG(price) as avg_price
    FROM df
    WHERE date >= '2025-01-01'
    GROUP BY product
    ORDER BY total_qty DESC
    LIMIT 10
""")

print(result.to_dict(orient="records"))
```

### Example 4: Parquet for Large Data Transfer

```python
from servicekit.data import DataFrame
import pandas as pd

# Create large dataset
large_df = pd.DataFrame({
    "id": range(1_000_000),
    "value": np.random.randn(1_000_000),
})

# Convert to DataFrame
df = DataFrame.from_pandas(large_df)

# Export as compressed Parquet (much smaller than CSV)
df.to_parquet("data.parquet", compression="zstd")

# Later, load efficiently
df2 = DataFrame.from_parquet("data.parquet")
assert df.shape == df2.shape
```

### Example 5: Data Pipeline with Multiple Formats

```python
from servicekit.data import DataFrame

# Read from various sources
df1 = DataFrame.from_csv("data1.csv")
df2 = DataFrame.from_parquet("data2.parquet")
df3 = DataFrame.from_pandas(get_pandas_data())

# Inspect and validate
print(f"df1: {df1.shape}, types: {df1.infer_types()}")
print(f"df2: {df2.shape}, types: {df2.infer_types()}")

# Transform
df1 = df1.select(["user_id", "score"]).rename({"user_id": "id"})
df2 = df2.drop(["temp_column"])

# Combine (manual for now, or use DuckDB)
# Export in different formats
df1.to_csv("output1.csv")
df2.to_parquet("output2.parquet", compression="snappy")
df3.to_msgpack()  # Binary format for API
```

## Open Questions

### 1. Concatenation and Merging

**Question**: Should we add `concat()` and `merge()` methods for combining DataFrames?

**Options**:
- **Option A**: Add methods - more convenient, but increases complexity
- **Option B**: Document DuckDB SQL approach - pushes complexity to DuckDB
- **Option C**: Defer to pandas/polars - keep DataFrame focused on interchange

**Recommendation**: Option B for now (use DuckDB SQL for joins), revisit based on user demand.

### 2. Type Metadata Storage

**Question**: Should we store and preserve type information in the DataFrame schema?

**Current**: `columns: list[str]`, `data: list[list[Any]]` (no type info)

**Options**:
- **Option A**: Add `dtypes: dict[str, str] | None` field to schema
- **Option B**: Infer types on-the-fly with `infer_types()` method
- **Option C**: Rely on Arrow schema for type preservation

**Trade-offs**:
- Option A: Breaks JSON schema, requires migration
- Option B: Current approach, works but no type preservation
- Option C: Only works with Arrow ecosystem

**Recommendation**: Option B for now (infer_types method), consider Option C (Arrow schema) in Phase 3.

### 3. Index Support

**Question**: Should DataFrame support an index (like pandas)?

**Current**: No index, just row number

**Options**:
- **Option A**: Add optional `index: list[Any] | None` field
- **Option B**: Keep it simple, no index
- **Option C**: Support index only in conversions (preserve pandas index)

**Recommendation**: Option B for now, revisit if users need it.

### 4. Streaming/Chunking

**Question**: Should we support streaming large files (read in chunks)?

**Use Case**: 10GB CSV file that doesn't fit in memory

**Options**:
- **Option A**: Add `from_csv_chunked(path, chunk_size=10000)` generator
- **Option B**: Document pandas/polars approach for large files
- **Option C**: Use Arrow Dataset API for large Parquet files

**Recommendation**: Option B (out of scope), suggest using pandas chunking or polars lazy API.

### 5. Compression Support

**Question**: Should CSV methods support automatic compression detection?

**Options**:
- **Option A**: Auto-detect .gz, .bz2 extensions and decompress
- **Option B**: Add explicit `compression` parameter
- **Option C**: No compression support (use external tools)

**Recommendation**: Option A for read (auto-detect), Option B for write (explicit parameter).

## Alternatives Considered

### Alternative 1: Use Apache Arrow as the Internal Format

**Approach**: Store data as Arrow Table internally instead of list of lists.

**Pros**:
- Zero-copy conversions to/from Arrow
- Type information preserved
- Columnar storage more efficient

**Cons**:
- Requires PyArrow as a dependency (breaks lightweight design)
- More complex implementation
- Harder to debug (binary format)
- Overkill for small DataFrames in APIs

**Decision**: Rejected. Keep simple list-of-lists format, use Arrow for I/O only.

### Alternative 2: Support Only Pandas/Polars (Remove from_dict, etc.)

**Approach**: Require pandas or polars, remove pure-Python methods.

**Pros**:
- Simpler implementation
- Leverage mature libraries

**Cons**:
- Requires dependency for basic operations
- Loses framework-agnostic design
- Higher barrier to entry

**Decision**: Rejected. Keep pure-Python core, optional integrations.

### Alternative 3: Build on Existing Library (pyarrow.Table, pandas.DataFrame)

**Approach**: Wrap existing library instead of custom class.

**Pros**:
- Less code to maintain
- Leverage existing ecosystem

**Cons**:
- Forces dependency
- Loses control over API
- Harder to keep lightweight

**Decision**: Rejected. Custom class gives us full control over API and dependencies.

## Success Metrics

### Adoption Metrics

- Number of projects using new I/O methods
- GitHub stars/downloads increase
- Issues/questions about DataFrame features

### Performance Metrics

- Parquet vs CSV transfer speed (target: 10x faster)
- Memory usage for large DataFrames
- Import time (should remain < 10ms)

### Quality Metrics

- Test coverage (target: > 95%)
- Zero production bugs in first 3 months
- Clear documentation for all features

## References

- [Apache Arrow Format](https://arrow.apache.org/)
- [Parquet File Format](https://parquet.apache.org/)
- [pandas DataFrame API](https://pandas.pydata.org/docs/reference/frame.html)
- [Polars DataFrame API](https://pola-rs.github.io/polars/py-polars/html/reference/dataframe/index.html)
- [DuckDB Python API](https://duckdb.org/docs/api/python/overview)

## Appendix A: API Quick Reference

### I/O Methods

| Method | Input | Output | Requires |
|--------|-------|--------|----------|
| `from_csv()` | File/string | DataFrame | stdlib |
| `to_csv()` | - | File/string | stdlib |
| `from_parquet()` | File | DataFrame | pyarrow |
| `to_parquet()` | - | File/bytes | pyarrow |
| `from_arrow()` | Table | DataFrame | pyarrow |
| `to_arrow()` | - | Table | pyarrow |
| `from_jsonl()` | File/string | DataFrame | stdlib |
| `to_jsonl()` | - | File/string | stdlib |
| `from_numpy()` | Array | DataFrame | numpy |
| `to_numpy()` | - | Array | numpy |
| `from_duckdb()` | Relation | DataFrame | duckdb |
| `to_duckdb()` | - | Relation | duckdb |
| `from_msgpack()` | Bytes | DataFrame | msgpack |
| `to_msgpack()` | - | Bytes | msgpack |
| `from_excel()` | File | DataFrame | openpyxl |
| `to_excel()` | - | File | openpyxl |

### Utility Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `shape` | tuple[int, int] | (rows, columns) |
| `num_rows` | int | Row count |
| `num_columns` | int | Column count |
| `is_empty` | bool | True if no rows |
| `head(n)` | DataFrame | First n rows |
| `tail(n)` | DataFrame | Last n rows |
| `sample(n)` | DataFrame | Random n rows |
| `select(cols)` | DataFrame | Keep columns |
| `drop(cols)` | DataFrame | Remove columns |
| `rename(mapper)` | DataFrame | Rename columns |
| `validate()` | None | Check integrity |
| `infer_types()` | dict | Column types |
| `has_nulls()` | dict | Null detection |
| `query(sql)` | DataFrame | SQL query |

## Appendix B: Migration from PandasDataFrame

**Note**: This proposal comes after the recent rename from `PandasDataFrame` to `DataFrame`. This is a reminder of that migration for context.

### Old Code (Pre-rename)

```python
from servicekit.data import PandasDataFrame

df = PandasDataFrame.from_pandas(pd_df)
```

### New Code (Post-rename)

```python
from servicekit.data import DataFrame

df = DataFrame.from_pandas(pd_df)
```

**Status**: Migration complete, `PandasDataFrame` alias removed in v0.3.3.

## Changelog

- **2025-10-24**: Initial proposal (v1.0)

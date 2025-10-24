# DataFrame Enhancement Design Document

**Version:** 2.0
**Status:** Phase 3 & 4 Proposed
**Created:** 2025-10-24
**Updated:** 2025-10-24

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

This document proposes advanced format support for the `servicekit.data.DataFrame` class to enable specialized data interchange scenarios beyond CSV.

## Motivation

### Current State

The `DataFrame` class provides:
- CSV I/O with stdlib (no dependencies)
- Library integrations: pandas, polars, xarray
- Data inspection: head, tail, sample
- Column operations: select, drop, rename
- Validation: structure checks, type inference, null detection
- Utility properties: shape, size, empty, ndim

### Proposed Enhancements

This document proposes adding advanced format support for specialized use cases:
- **Binary Formats**: Parquet, Arrow, MessagePack for efficient data transfer
- **Streaming Formats**: JSONL for large datasets
- **Interoperability**: NumPy for numerical computing, DuckDB for SQL queries
- **Business Formats**: Excel for enterprise users

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

1. **Add Advanced File I/O**: Parquet, Arrow, JSONL formats
2. **Support Industry Standards**: PyArrow/Arrow ecosystem integration
3. **Maintain Design Principles**:
   - Lightweight core (no required dependencies)
   - Lazy imports (import only when methods are called)
   - Simple API (consistent from_X / to_X pattern)
   - Framework-agnostic (works in any Python environment)
4. **Enable Performance**: Binary formats for efficient data transfer
5. **Preserve Backward Compatibility**: No breaking changes to existing API

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

### PyArrow/Arrow Support

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

### Advanced Formats

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

### Specialized Formats

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

### Phase 1: Arrow/Parquet Support (2 weeks)

**Deliverables:**
- PyArrow Table conversions
- Parquet read/write methods
- Comprehensive tests
- Documentation and examples

**Dependencies:**
- `pyarrow>=14.0.0` (optional)

**Priority:** Medium

### Phase 2: Advanced Formats (2 weeks)

**Deliverables:**
- JSON Lines support (uses stdlib json)
- NumPy conversions (requires numpy)
- DuckDB integration with SQL query support (requires duckdb)
- Tests and documentation

**Dependencies:**
- `numpy>=1.24.0` (optional)
- `duckdb>=0.9.0` (optional)

**Priority:** Low

### Phase 3: Specialized Formats (1 week)

**Deliverables:**
- MessagePack support (requires msgpack)
- Excel support (requires openpyxl)
- Feather/Arrow IPC (requires pyarrow)

**Dependencies:**
- `msgpack>=1.0.0` (optional)
- `openpyxl>=3.1.0` (optional)

**Priority:** Low

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

1. **Arrow/Parquet Module**
   - `test_from_arrow_table()` - Convert from PyArrow
   - `test_to_arrow_table()` - Convert to PyArrow
   - `test_from_parquet()` - Read Parquet file
   - `test_to_parquet_file()` - Write Parquet file
   - `test_to_parquet_bytes()` - Return bytes
   - `test_parquet_compression()` - Different codecs
   - `test_arrow_not_installed()` - ImportError handling

2. **JSONL Module**
   - `test_from_jsonl_file()` - Read JSONL file
   - `test_from_jsonl_string()` - Read JSONL string
   - `test_to_jsonl_file()` - Write JSONL file
   - `test_to_jsonl_string()` - Return as string

3. **NumPy Module**
   - `test_from_numpy_2d()` - Convert from NumPy array
   - `test_to_numpy()` - Convert to NumPy array
   - `test_numpy_with_columns()` - Custom column names

4. **DuckDB Module**
   - `test_to_duckdb()` - Convert to DuckDB relation
   - `test_from_duckdb()` - Convert from DuckDB relation
   - `test_query()` - SQL queries on DataFrame

### Integration Tests

1. **Round-trip Tests**
   - DataFrame → Parquet → DataFrame
   - DataFrame → Arrow → DataFrame
   - DataFrame → JSONL → DataFrame

2. **Cross-library Tests**
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

Test with and without optional dependencies to ensure lazy imports work correctly.

## Dependencies

### Required (No Changes)

- Python 3.13+
- pydantic

### Proposed Optional Dependencies

```toml
[project.optional-dependencies]
arrow = ["pyarrow>=14.0.0"]
parquet = ["pyarrow>=14.0.0"]  # Alias for arrow
numpy = ["numpy>=1.24.0"]
duckdb = ["duckdb>=0.9.0"]
msgpack = ["msgpack>=1.0.0"]
excel = ["openpyxl>=3.1.0"]
data-all = [
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


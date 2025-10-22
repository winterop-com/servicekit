"""Simple example showing DataFrame usage with polars."""

import polars as pl

from servicekit.data import DataFrame

# Create a Polars DataFrame
df = pl.DataFrame(
    {
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "city": ["New York", "London", "Paris"],
    }
)

print("Original Polars DataFrame:")
print(df)
print()

# Convert to servicekit DataFrame
sk_df = DataFrame.from_polars(df)

print("Servicekit DataFrame:")
print(f"Columns: {sk_df.columns}")
print(f"Data: {sk_df.data}")
print()

# Convert back to Polars
df_back = sk_df.to_polars()

print("Converted back to Polars:")
print(df_back)

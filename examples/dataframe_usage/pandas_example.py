"""Simple example showing DataFrame usage with pandas."""

import pandas as pd

from servicekit.data import DataFrame

# Create a pandas DataFrame
df = pd.DataFrame(
    {
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "city": ["New York", "London", "Paris"],
    }
)

print("Original pandas DataFrame:")
print(df)
print()

# Convert to servicekit DataFrame
sk_df = DataFrame.from_pandas(df)

print("Servicekit DataFrame:")
print(f"Columns: {sk_df.columns}")
print(f"Data: {sk_df.data}")
print()

# Convert back to pandas
df_back = sk_df.to_pandas()

print("Converted back to pandas:")
print(df_back)

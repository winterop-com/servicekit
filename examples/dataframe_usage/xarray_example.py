"""Simple example showing DataFrame usage with xarray."""

import numpy as np
import xarray as xr

from servicekit.data import DataFrame

# Create a 2D xarray DataArray
data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
da = xr.DataArray(
    data,
    dims=["row", "col"],
    coords={"row": ["A", "B", "C"], "col": ["x", "y", "z"]},
)

print("Original xarray DataArray:")
print(da)
print()

# Convert to servicekit DataFrame
sk_df = DataFrame.from_xarray(da)

print("Servicekit DataFrame:")
print(f"Columns: {sk_df.columns}")
print(f"Data: {sk_df.data}")
print()

# Convert to pandas (xarray conversion goes through pandas)
df = sk_df.to_pandas()

print("Converted to pandas:")
print(df)

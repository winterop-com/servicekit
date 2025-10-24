"""Example demonstrating advanced DataFrame features."""

from servicekit.data import DataFrame

print("=== Row Filtering ===")
# Create sample data with adults and minors
df_people = DataFrame.from_dict(
    {
        "name": ["Alice", "Bob", "Charlie", "Dave", "Eve"],
        "age": [25, 17, 30, 16, 35],
        "active": [True, True, False, True, True],
        "score": [95, 87, 92, 78, 88],
    }
)

# Filter for adults only
adults = df_people.filter(lambda row: row["age"] >= 18)
print(f"Adults only: {adults.shape[0]} rows")
for row in adults:
    print(f"  {row['name']}: age {row['age']}")
print()

# Filter with multiple conditions
active_adults = df_people.filter(lambda row: row["age"] >= 18 and row["active"])
print(f"Active adults: {active_adults.shape[0]} rows")
print()

print("=== Column Transformations ===")
# Apply transformations to columns
df_upper = df_people.apply(str.upper, "name")
print("Uppercase names:")
print(f"  {df_upper.get_column('name')}")
print()

# Apply calculations
df_doubled = df_people.apply(lambda x: x * 2, "score")
print("Doubled scores:")
print(f"  {df_doubled.get_column('score')}")
print()

print("=== Adding Columns ===")
# Calculate pass/fail and add as new column
pass_fail: list[str] = ["PASS" if row["score"] >= 80 else "FAIL" for row in df_people]
df_with_result = df_people.add_column("result", pass_fail)
print("With results:")
for row in df_with_result:
    print(f"  {row['name']}: {row['score']} -> {row['result']}")
print()

print("=== Drop Rows ===")
# Remove specific rows by index
df_no_first = df_people.drop_rows([0])
print(f"Dropped first row: {df_no_first.shape[0]} rows remaining")
print(f"  Names: {df_no_first.get_column('name')}")
print()

print("=== Remove Duplicates ===")
# Create data with duplicates
df_dup = DataFrame.from_dict(
    {
        "user_id": [1, 2, 1, 3, 2],
        "name": ["Alice", "Bob", "Alice", "Charlie", "Bob"],
        "timestamp": ["09:00", "09:05", "09:10", "09:15", "09:20"],
    }
)

print("Original data with duplicates:")
for row in df_dup:
    print(f"  {row}")

df_unique = df_dup.drop_duplicates(subset=["user_id"])
print(f"\nAfter removing duplicates: {df_unique.shape[0]} unique users")
for row in df_unique:
    print(f"  {row}")
print()

print("=== Fill Missing Values ===")
# Create data with None values
df_missing = DataFrame.from_dict(
    {
        "name": ["Alice", "Bob", None, "Dave"],
        "age": [25, None, 30, None],
        "city": ["NYC", "LA", "Chicago", None],
    }
)

print("Data with missing values:")
nulls = df_missing.has_nulls()
for col, has_null in nulls.items():
    print(f"  {col}: {'Has nulls' if has_null else 'Complete'}")

# Fill with defaults
df_filled = df_missing.fillna({"name": "Unknown", "age": 0, "city": "N/A"})
print("\nAfter filling:")
for row in df_filled:
    print(f"  {row}")
print()

print("=== Concatenate DataFrames ===")
# Combine multiple batches
batch1 = DataFrame.from_dict({"name": ["Alice", "Bob"], "score": [95, 87]})
batch2 = DataFrame.from_dict({"name": ["Charlie", "Dave"], "score": [92, 78]})

combined = batch1.concat(batch2)
print(f"Combined batches: {combined.shape[0]} total rows")
for row in combined:
    print(f"  {row}")
print()

print("=== Statistical Summary ===")
# Create numeric dataset
df_sales = DataFrame.from_dict(
    {
        "product": ["Widget", "Gadget", "Tool", "Device", "Widget"],
        "price": [10.50, 25.00, 15.75, 30.00, 10.50],
        "quantity": [100, 50, 75, 25, 120],
    }
)

stats = df_sales.describe()
print("Statistics for numeric columns:")
print(f"  Stat column: {stats.get_column('stat')}")
print(f"  Price stats: {stats.get_column('price')}")
print(f"  Quantity stats: {stats.get_column('quantity')}")
print()

print("=== Group By Operations ===")
# Count by category
counts = df_sales.groupby("product").count()
print("Product counts:")
for row in counts:
    print(f"  {row['product']}: {row['count']} times")
print()

# Sum quantities by product
totals = df_sales.groupby("product").sum("quantity")
print("Total quantity by product:")
for row in totals:
    print(f"  {row['product']}: {row['quantity_sum']} units")
print()

# Average price by product
avg_prices = df_sales.groupby("product").mean("price")
print("Average price by product:")
for row in avg_prices:
    print(f"  {row['product']}: ${row['price_mean']:.2f}")
print()

print("=== Complete Pipeline ===")
# Demonstrate chaining multiple operations
df_raw = DataFrame.from_dict(
    {
        "name": ["alice", "BOB", "alice", "CHARLIE", "dave", None],
        "age": [25, None, 25, 30, 16, 28],
        "score": [95, 87, 95, 92, 78, None],
        "active": [True, True, True, False, True, True],
    }
)

print("Processing pipeline:")
print(f"  Starting with: {df_raw.shape[0]} rows")

df_processed = (
    df_raw.fillna({"name": "Unknown", "age": 0, "score": 0})
    .apply(str.lower, "name")
    .apply(str.capitalize, "name")
    .drop_duplicates(subset=["name", "age"])
    .filter(lambda row: row["age"] >= 18)
    .filter(lambda row: row["score"] >= 80)
    .sort("score", ascending=False)
)

print(f"  After processing: {df_processed.shape[0]} rows")
print("\nFinal results:")
for row in df_processed:
    print(f"  {row['name']}: age {row['age']}, score {row['score']}")

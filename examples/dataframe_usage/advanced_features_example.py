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

print("\n=== Missing Data Detection ===")
# Create data with missing values
df_missing_data = DataFrame.from_dict(
    {
        "employee": ["Alice", "Bob", "Charlie", "Dave"],
        "department": ["Sales", None, "Engineering", "Sales"],
        "salary": [50000, 60000, None, 55000],
        "bonus": [None, 5000, None, 3000],
    }
)

print("Original data:")
for row in df_missing_data:
    print(f"  {row}")

# Detect missing values
print("\nMissing value detection (isna):")
is_null = df_missing_data.isna()
for i, row in enumerate(is_null):
    print(f"  Row {i}: {row}")

# Check which columns have nulls
print("\nColumns with missing values:")
nulls = df_missing_data.has_nulls()
for col, has_null in nulls.items():
    print(f"  {col}: {'Yes' if has_null else 'No'}")

print("\n=== Missing Data Cleaning ===")
# Drop rows with any None values
clean_data = df_missing_data.dropna(axis=0, how="any")
print(f"After dropna (rows with any None): {clean_data.shape[0]} rows")
for row in clean_data:
    print(f"  {row}")

# Drop columns with any None values
no_null_cols = df_missing_data.dropna(axis=1, how="any")
print(f"\nAfter dropna (columns with any None): {no_null_cols.columns}")

# Fill missing values
filled_data = df_missing_data.fillna({"department": "Unknown", "salary": 0, "bonus": 0})
print("\nAfter filling missing values:")
for row in filled_data:
    print(f"  {row}")

print("\n=== DataFrame Comparison ===")
# Compare DataFrames
df1 = DataFrame.from_dict({"name": ["Alice", "Bob"], "age": [25, 30]})
df2 = DataFrame.from_dict({"name": ["Alice", "Bob"], "age": [25, 30]})
df3 = DataFrame.from_dict({"name": ["Bob", "Alice"], "age": [30, 25]})

print("df1 equals df2:", df1.equals(df2))
print("df1 equals df3 (different order):", df1.equals(df3))

print("\n=== DataFrame Copying ===")
# Demonstrate copy independence
original = DataFrame.from_dict({"name": ["Alice"], "value": [100]})
copied = original.deepcopy()

print("Original before modification:")
print(f"  {original.data}")

# Modify copy
copied.data[0][1] = 999

print("Original after modifying copy:")
print(f"  {original.data}")
print("Copy after modification:")
print(f"  {copied.data}")

print("\n=== Unique Value Counting ===")
# Count unique values
df_categories = DataFrame.from_dict(
    {
        "product": ["Widget", "Gadget", "Widget", "Tool", "Widget", "Gadget"],
        "status": ["active", "active", "inactive", "active", "active", "inactive"],
    }
)

print("Data:")
for row in df_categories:
    print(f"  {row}")

print(f"\nUnique products: {df_categories.nunique('product')}")
print(f"Unique statuses: {df_categories.nunique('status')}")

print("\nActual unique values:")
print(f"  Products: {df_categories.unique('product')}")
print(f"  Statuses: {df_categories.unique('status')}")

print("\nValue counts:")
product_counts = df_categories.value_counts("product")
for product, count in product_counts.items():
    print(f"  {product}: {count}")

print("\n=== Data Reshaping with melt() ===")
# Create wide format data (student grades)
df_grades = DataFrame.from_dict(
    {
        "student": ["Alice", "Bob", "Charlie"],
        "math": [90, 78, 95],
        "science": [85, 92, 89],
        "history": [88, 81, 93],
    }
)

print("Wide format (grades across subjects):")
for row in df_grades:
    print(f"  {row['student']}: Math={row['math']}, Science={row['science']}, History={row['history']}")

# Melt to long format
melted = df_grades.melt(
    id_vars=["student"], value_vars=["math", "science", "history"], var_name="subject", value_name="score"
)

print("\nLong format (one row per subject):")
for row in melted:
    print(f"  {row['student']} - {row['subject']}: {row['score']}")

print("\n=== Survey Data Analysis ===")
# Survey responses in wide format
survey = DataFrame.from_dict(
    {
        "respondent_id": [1, 2, 3, 4],
        "age": [25, 30, 35, 28],
        "q1_rating": [5, 4, 5, 3],
        "q2_rating": [4, 4, 5, 4],
        "q3_rating": [5, 3, 5, 5],
    }
)

print("Survey responses (wide format):")
for row in survey:
    print(
        f"  Respondent {row['respondent_id']} (age {row['age']}): "
        f"Q1={row['q1_rating']}, Q2={row['q2_rating']}, Q3={row['q3_rating']}"
    )

# Melt for analysis
responses = survey.melt(
    id_vars=["respondent_id", "age"],
    value_vars=["q1_rating", "q2_rating", "q3_rating"],
    var_name="question",
    value_name="rating",
)

print("\nMelted survey data:")
print(f"  Total responses: {len(responses.data)}")

# Average rating per question using groupby
avg_by_question = responses.groupby("question").mean("rating")
print("\nAverage rating per question:")
for row in avg_by_question:
    print(f"  {row['question']}: {row['rating_mean']:.2f}")

print("\n=== Time Series Sales Data ===")
# Monthly sales in wide format
sales = DataFrame.from_dict(
    {
        "region": ["North", "South", "East"],
        "product": ["Widget", "Widget", "Widget"],
        "jan": [1000, 1200, 900],
        "feb": [1100, 1300, 950],
        "mar": [1200, 1400, 1000],
    }
)

print("Sales by region (wide format):")
for row in sales:
    print(f"  {row['region']} {row['product']}: Jan={row['jan']}, Feb={row['feb']}, Mar={row['mar']}")

# Melt to time series format
time_series = sales.melt(
    id_vars=["region", "product"], value_vars=["jan", "feb", "mar"], var_name="month", value_name="sales"
)

print("\nTime series format:")
print(f"  Total records: {len(time_series.data)}")

# Total sales by month
monthly_totals = time_series.groupby("month").sum("sales")
print("\nTotal sales by month:")
for row in monthly_totals:
    print(f"  {row['month']}: ${row['sales_sum']:,}")

# Sales by region
region_totals = time_series.groupby("region").sum("sales")
print("\nTotal sales by region:")
for row in region_totals:
    print(f"  {row['region']}: ${row['sales_sum']:,}")

print("\n=== Sensor Data Standardization ===")
# API response with different metrics as columns
sensor_data = DataFrame.from_dict(
    {
        "sensor_id": ["s1", "s2", "s3"],
        "location": ["room_a", "room_b", "room_c"],
        "temp_c": [22.5, 23.1, 21.8],
        "humidity_pct": [45, 48, 42],
        "pressure_kpa": [101.3, 101.2, 101.4],
    }
)

print("Sensor readings (wide format):")
for row in sensor_data:
    print(
        f"  {row['sensor_id']} ({row['location']}): {row['temp_c']}°C, {row['humidity_pct']}%, {row['pressure_kpa']}kPa"
    )

# Standardize to key-value format
metrics = sensor_data.melt(
    id_vars=["sensor_id", "location"],
    value_vars=["temp_c", "humidity_pct", "pressure_kpa"],
    var_name="metric_type",
    value_name="metric_value",
)

print("\nStandardized metrics format:")
for row in metrics:
    print(f"  {row['sensor_id']} - {row['metric_type']}: {row['metric_value']}")

print("\n=== Combined melt() + filter() + groupby() Pipeline ===")
# Start with quarterly sales data
quarterly_sales = DataFrame.from_dict(
    {
        "region": ["North", "North", "South", "South", "East", "East"],
        "product": ["Widget", "Gadget", "Widget", "Gadget", "Widget", "Gadget"],
        "q1": [1000, 800, 1200, 900, 950, 750],
        "q2": [1100, 850, 1300, 950, 1000, 800],
        "q3": [1200, 900, 1400, 1000, 1050, 850],
    }
)

print("Quarterly sales data:")
for row in quarterly_sales:
    print(f"  {row['region']} - {row['product']}: Q1={row['q1']}, Q2={row['q2']}, Q3={row['q3']}")

# Pipeline: melt -> filter -> groupby
melted_sales = quarterly_sales.melt(
    id_vars=["region", "product"], value_vars=["q1", "q2", "q3"], var_name="quarter", value_name="sales"
)

# Filter for high-performing quarters (sales > 1000)
high_sales = melted_sales.filter(lambda row: row["sales"] > 1000)

print(f"\nHigh-performing quarters (sales > 1000): {len(high_sales.data)} records")

# Count high-performing quarters by region
region_performance = high_sales.groupby("region").count()
print("\nHigh-performing quarters by region:")
for row in region_performance:
    print(f"  {row['region']}: {row['count']} quarters")

print("\n=== Pivoting Data (Long to Wide) ===")
# Inverse of melt() - transform long format to wide format
df_long_metrics = DataFrame.from_dict(
    {
        "date": ["2024-01", "2024-01", "2024-02", "2024-02", "2024-03", "2024-03"],
        "metric": ["sales", "profit", "sales", "profit", "sales", "profit"],
        "value": [1000, 200, 1100, 220, 1200, 240],
    }
)

print("Long format (metrics in rows):")
for row in df_long_metrics:
    print(f"  {row['date']} - {row['metric']}: {row['value']}")

# Pivot to wide format
df_wide_metrics = df_long_metrics.pivot(index="date", columns="metric", values="value")

print("\nWide format (metrics in columns):")
for row in df_wide_metrics:
    print(f"  {row['date']}: Sales={row['sales']}, Profit={row['profit']}")

print("\n=== Round-trip: Melt then Pivot ===")
# Start with wide format
original = DataFrame.from_dict({"id": [1, 2, 3], "metric_a": [100, 200, 300], "metric_b": [10, 20, 30]})

print("Original (wide):")
for row in original:
    print(f"  ID {row['id']}: A={row['metric_a']}, B={row['metric_b']}")

# Melt to long format
melted_temp = original.melt(id_vars=["id"], value_vars=["metric_a", "metric_b"])
print(f"\nAfter melt (long): {len(melted_temp.data)} rows")

# Pivot back to wide format
restored = melted_temp.pivot(index="id", columns="variable", values="value")
print("\nRestored (wide):")
for row in restored:
    print(f"  ID {row['id']}: metric_a={row['metric_a']}, metric_b={row['metric_b']}")

print("\n=== Merging DataFrames (Inner Join) ===")
# Users from one service
users = DataFrame.from_dict({"user_id": [1, 2, 3, 4], "name": ["Alice", "Bob", "Charlie", "Dave"]})

# Orders from another service
orders = DataFrame.from_dict({"order_id": [101, 102, 103], "user_id": [1, 2, 1], "amount": [50, 75, 100]})

print("Users:")
for row in users:
    print(f"  {row['user_id']}: {row['name']}")

print("\nOrders:")
for row in orders:
    print(f"  Order {row['order_id']}: user={row['user_id']}, amount=${row['amount']}")

# Inner join - only users with orders
joined = orders.merge(users, on="user_id", how="inner")

print("\nJoined (inner - users with orders):")
for row in joined:
    print(f"  Order {row['order_id']}: {row['name']} - ${row['amount']}")

print("\n=== Merging with Left Join ===")
# Left join - all orders, even if user not found
joined_left = orders.merge(users, on="user_id", how="left")

print("Joined (left - all orders):")
for row in joined_left:
    user_name = row["name"] if row["name"] is not None else "Unknown"
    print(f"  Order {row['order_id']}: {user_name} - ${row['amount']}")

print("\n=== Merging with Different Column Names ===")
products = DataFrame.from_dict(
    {
        "product_id": [1, 2, 3],
        "product_name": ["Widget", "Gadget", "Tool"],
        "price": [10.0, 15.0, 20.0],
    }
)

sales_data = DataFrame.from_dict({"sale_id": [1, 2, 3, 4], "item_id": [1, 2, 1, 3], "quantity": [5, 3, 2, 4]})

print("Products:")
for row in products:
    print(f"  {row['product_id']}: {row['product_name']} - ${row['price']}")

print("\nSales:")
for row in sales_data:
    print(f"  Sale {row['sale_id']}: item={row['item_id']}, qty={row['quantity']}")

# Merge on different column names
enriched_sales = sales_data.merge(products, left_on="item_id", right_on="product_id", how="left")

print("\nEnriched sales data:")
for row in enriched_sales:
    revenue = row["quantity"] * row["price"]
    print(f"  Sale {row['sale_id']}: {row['product_name']} x {row['quantity']} = ${revenue:.2f}")

print("\n=== Merging with Multiple Keys ===")
# Join on composite keys (region + product)
inventory = DataFrame.from_dict(
    {
        "region": ["North", "North", "South", "South"],
        "product": ["Widget", "Gadget", "Widget", "Gadget"],
        "stock": [100, 50, 150, 75],
    }
)

demand = DataFrame.from_dict(
    {
        "region": ["North", "North", "South"],
        "product": ["Widget", "Gadget", "Widget"],
        "demand": [80, 60, 120],
    }
)

print("Inventory:")
for row in inventory:
    print(f"  {row['region']} - {row['product']}: {row['stock']} units")

print("\nDemand:")
for row in demand:
    print(f"  {row['region']} - {row['product']}: {row['demand']} units")

# Merge on multiple columns
supply_status = inventory.merge(demand, on=["region", "product"], how="left")

print("\nSupply status:")
for row in supply_status:
    if row["demand"] is not None:
        surplus = row["stock"] - row["demand"]
        status = "OK" if surplus >= 0 else "SHORTAGE"
        print(
            f"  {row['region']} - {row['product']}: "
            f"stock={row['stock']}, demand={row['demand']}, surplus={surplus} ({status})"
        )
    else:
        print(f"  {row['region']} - {row['product']}: stock={row['stock']}, demand=N/A (no demand data)")

print("\n=== Complex Pipeline: Melt + Filter + Pivot ===")
# Start with quarterly performance
performance = DataFrame.from_dict(
    {
        "employee": ["Alice", "Alice", "Bob", "Bob", "Charlie", "Charlie"],
        "quarter": ["Q1", "Q2", "Q1", "Q2", "Q1", "Q2"],
        "score": [85, 92, 78, 82, 95, 98],
    }
)

print("Raw performance data:")
for row in performance:
    print(f"  {row['employee']} {row['quarter']}: {row['score']}")

# Filter for high performers (score >= 85)
high_performers = performance.filter(lambda row: row["score"] >= 85)

print(f"\nHigh performers (score >= 85): {len(high_performers.data)} records")

# Pivot for reporting
report = high_performers.pivot(index="employee", columns="quarter", values="score")

print("\nPerformance report (high performers only):")
for row in report:
    q1_score = f"{row['Q1']}" if row["Q1"] is not None else "N/A"
    q2_score = f"{row['Q2']}" if row["Q2"] is not None else "N/A"
    print(f"  {row['employee']}: Q1={q1_score}, Q2={q2_score}")

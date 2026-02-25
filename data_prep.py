"""
DATA PREP: Simple data check script

WHAT IT DOES:
  Loads the orders CSV and prints a few basic stats (row count, date range, order status counts).
  That way we can confirm the data is there and see the time range before using it in the dashboard.

WHY IT'S IN THIS PROJECT:
  - Validates the data the dashboard uses (same CSV, quick sanity check).
  - Gives you one small Python file you can run and explain line by line (merge, groupby, etc. live in SQL; this is simple pandas).
  - On GitHub it shows you can load data and inspect it with Python, not only SQL.

HOW TO RUN (from project root):
  python data_prep.py
"""

# --- IMPORTS ---
# pandas: library for tables (DataFrames). read_csv() loads a CSV; .shape, .min(), .max(), .value_counts() are methods we use below.
import pandas as pd
# pathlib.Path: builds file paths that work on Windows/Mac/Linux. We use it to point to the 'data' folder.
from pathlib import Path

# --- PATHS ---
# __file__ = this script's file path (e.g. C:\...\sql_portfolio\data_prep.py)
# .resolve() = turn it into an absolute path
# .parent = the folder that contains this file (sql_portfolio)
# / "data" = add the "data" subfolder. So DATA_DIR = sql_portfolio/data
DATA_DIR = Path(__file__).resolve().parent / "data"
# Full path to the orders CSV file
orders_path = DATA_DIR / "olist_orders_dataset.csv"

# --- LOAD DATA ---
# read_csv() reads the CSV from disk into a DataFrame (a table in memory). 'orders' is that table.
orders = pd.read_csv(orders_path)

# --- DATA CONVERSION ---
# Convert the timestamp column from 'object' (text) to datetime.
# This ensures .min() and .max() are accurate and any date-based analysis is correct.
orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])

# --- PRINT BASIC STATS ---
# .shape = (number of rows, number of columns). Quick way to see size of the table.
print("Orders shape:", orders.shape)
# Now that we've converted to datetime, .min() and .max() give the true earliest and latest date.
print("Date range:", orders["order_purchase_timestamp"].min(), "to", orders["order_purchase_timestamp"].max())
# value_counts() = how many rows have each value (e.g. delivered: 96478, shipped: 1107, ...). Shows distribution of order status.
print("\nOrder status counts:")
print(orders["order_status"].value_counts())

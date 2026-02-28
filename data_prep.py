"""
Load orders CSV and print basic stats (shape, date range, order status counts).
Validates the same data the dashboard uses. Run from project root:  python data_prep.py
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
orders_path = DATA_DIR / "olist_orders_dataset.csv"

orders = pd.read_csv(orders_path)
orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])

print("Orders shape:", orders.shape)
print("Date range:", orders["order_purchase_timestamp"].min(), "to", orders["order_purchase_timestamp"].max())
print("\nOrder status counts:")
print(orders["order_status"].value_counts())

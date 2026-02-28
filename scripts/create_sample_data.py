"""
Build data_sample/ from your full data/ for Streamlit Cloud deployment.
Run from project root:  python scripts/create_sample_data.py

Requires: Full Olist dataset in data/ (same CSVs you use when running the app locally).
Output: data_sample/ = a subset of your real data, referentially consistent, with
        Retention & Loyalty working. The deployed app will match your local report
        (same structure and logic, smaller subset).

After running: git add data_sample/ && git commit -m "Update data_sample for Cloud" && git push
Then reboot the app on Streamlit Cloud.
"""
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
OUT_DIR = BASE / "data_sample"
SQL_DIR = BASE / "sql"

# Sample size (subset of your real data)
TARGET_REPEAT = 1000   # customers with 2+ delivered orders (that have payments)
TARGET_SINGLE = 600   # customers with 1 delivered order (with payment)
MAX_GEO_ROWS = 3000
RANDOM_STATE = 42


def main():
    if not (DATA_DIR / "olist_orders_dataset.csv").exists():
        print("ERROR: data/olist_orders_dataset.csv not found.")
        print("Put the full Olist dataset in data/ (same as when you run the app locally), then run this script again.")
        sys.exit(1)
    if not (DATA_DIR / "olist_order_payments_dataset.csv").exists():
        print("ERROR: data/olist_order_payments_dataset.csv not found.")
        sys.exit(1)

    OUT_DIR.mkdir(exist_ok=True)

    # 1) Orders that have at least one payment (retention view JOINs orders with payments)
    orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
    payments = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")
    order_ids_with_payment = set(payments["order_id"].dropna().unique())

    # 2) Delivered orders that have a payment (only these count for retention)
    delivered = orders[
        (orders["order_status"] == "delivered") & (orders["order_id"].isin(order_ids_with_payment))
    ].copy()
    order_count = delivered.groupby("customer_id").size()
    repeat_cids = order_count[order_count >= 2].index.tolist()
    single_cids = order_count[order_count == 1].index.tolist()

    if len(repeat_cids) == 0:
        print("ERROR: In your data, no customer has 2+ delivered orders that have a payment.")
        print("Use the full Olist dataset (e.g. from Kaggle) in data/, then run this script again.")
        sys.exit(1)

    # 3) Sample customers (deterministic)
    n_repeat = min(TARGET_REPEAT, len(repeat_cids))
    n_single = min(TARGET_SINGLE, len(single_cids))
    rng = pd.Series(repeat_cids).sample(n=n_repeat, random_state=RANDOM_STATE).tolist()
    sng = pd.Series(single_cids).sample(n=n_single, random_state=RANDOM_STATE).tolist()
    selected_customer_ids = set(rng) | set(sng)

    # 4) All orders for these customers that have a payment (so retention view keeps them)
    candidate_orders = orders[orders["customer_id"].isin(selected_customer_ids)]
    selected_order_ids = set(
        candidate_orders[candidate_orders["order_id"].isin(order_ids_with_payment)]["order_id"]
    )

    # 5) Write CSVs (referentially consistent)
    customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")
    customers_out = customers[customers["customer_id"].isin(selected_customer_ids)]
    customers_out.to_csv(OUT_DIR / "olist_customers_dataset.csv", index=False)
    print(f"  olist_customers_dataset.csv: {len(customers_out)} rows")

    orders_out = orders[orders["order_id"].isin(selected_order_ids)]
    orders_out.to_csv(OUT_DIR / "olist_orders_dataset.csv", index=False)
    print(f"  olist_orders_dataset.csv: {len(orders_out)} rows")

    for name, key in [
        ("olist_order_payments_dataset.csv", "order_id"),
        ("olist_order_items_dataset.csv", "order_id"),
        ("olist_order_reviews_dataset.csv", "order_id"),
    ]:
        path = DATA_DIR / name
        if not path.exists():
            print(f"  Skip (not found): {name}")
            continue
        df = pd.read_csv(path)
        df = df[df[key].isin(selected_order_ids)]
        df.to_csv(OUT_DIR / name, index=False)
        print(f"  {name}: {len(df)} rows")

    # Products and sellers from order_items
    oi_path = DATA_DIR / "olist_order_items_dataset.csv"
    if oi_path.exists():
        oi = pd.read_csv(oi_path)
        oi = oi[oi["order_id"].isin(selected_order_ids)]
        pids = oi["product_id"].dropna().unique()
        sids = oi["seller_id"].dropna().unique()
        prod = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
        prod[prod["product_id"].isin(pids)].to_csv(OUT_DIR / "olist_products_dataset.csv", index=False)
        sell = pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")
        sell[sell["seller_id"].isin(sids)].to_csv(OUT_DIR / "olist_sellers_dataset.csv", index=False)
        print(f"  olist_products_dataset.csv, olist_sellers_dataset.csv: written")

    # Translation: full copy
    trans = DATA_DIR / "product_category_name_translation.csv"
    if trans.exists():
        pd.read_csv(trans).to_csv(OUT_DIR / "product_category_name_translation.csv", index=False)
        print(f"  product_category_name_translation.csv: written")

    # Geolocation: zips from sampled customers
    geo_path = DATA_DIR / "olist_geolocation_dataset.csv"
    if geo_path.exists():
        zips = set(customers_out["customer_zip_code_prefix"].dropna().astype(int).astype(str))
        geo = pd.read_csv(geo_path)
        geo["_zip"] = geo["geolocation_zip_code_prefix"].astype(str)
        geo = geo[geo["_zip"].isin(zips)].drop(columns=["_zip"])
        if len(geo) > MAX_GEO_ROWS:
            geo = geo.head(MAX_GEO_ROWS)
        geo.to_csv(OUT_DIR / "olist_geolocation_dataset.csv", index=False)
        print(f"  olist_geolocation_dataset.csv: {len(geo)} rows")

    # 6) Verify retention engine returns rows (same table names as app)
    try:
        import duckdb
        # Map CSV stem -> table name (must match app.py csv_to_table_name and SQL)
        def csv_to_table(stem):
            s = stem.lower()
            if s.startswith("olist_") and s.endswith("_dataset"):
                t = s[6:-8]
                return t.rstrip("_") if t.endswith("_") else t
            return s.replace("-", "_")
        con = duckdb.connect(":memory:")
        for f in sorted(OUT_DIR.glob("*.csv")):
            tbl = csv_to_table(f.stem)
            con.execute(f'CREATE TABLE "{tbl}" AS SELECT * FROM read_csv_auto(?)', [str(f.resolve())])
        retention_sql = (SQL_DIR / "retention_engine.sql").read_text(encoding="utf-8").strip().rstrip(";")
        retention_df = con.execute(retention_sql).fetchdf()
        n_ret = len(retention_df)
        con.close()
    except Exception as e:
        print(f"  Verification failed: {e}")
        print("  Fix the data or script and run again. Do not push data_sample until verification passes.")
        sys.exit(1)

    if n_ret == 0:
        print("  ERROR: Retention & Loyalty would have 0 rows with this sample.")
        print("  Do not push. Ensure data/ has the full Olist dataset and run again.")
        sys.exit(1)

    print(f"  Verified: Retention & Loyalty has {n_ret} rows.")
    print("")
    print("Next: git add data_sample/ && git commit -m 'Update data_sample for Cloud' && git push")
    print("Then: Streamlit Cloud → Manage app → Reboot app")


if __name__ == "__main__":
    main()

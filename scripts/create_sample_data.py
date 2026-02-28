"""
One-time script: build data_sample/ from your full data/ for deployment.
Run from project root:  python scripts/create_sample_data.py
Keeps referential integrity and ensures enough repeat customers so Retention & Loyalty has data.
Commit data_sample/ so Streamlit Cloud has data.
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "data_sample"

# Target sample sizes: enough for charts, small enough to commit
TARGET_REPEAT_CUSTOMERS = 1200   # customers with 2+ delivered orders (for retention engine)
TARGET_SINGLE_CUSTOMERS = 800    # customers with 1 delivered order
MAX_GEOLOCATION_ROWS = 3000      # cap geolocation size
MAX_PRODUCT_CATEGORY_ROWS = None # keep all (small file)


def main():
    OUT_DIR.mkdir(exist_ok=True)

    orders_path = DATA_DIR / "olist_orders_dataset.csv"
    customers_path = DATA_DIR / "olist_customers_dataset.csv"
    if not orders_path.exists() or not customers_path.exists():
        print("Need data/olist_orders_dataset.csv and data/olist_customers_dataset.csv. Exiting.")
        return

    # Load orders and customers
    orders = pd.read_csv(orders_path)
    customers = pd.read_csv(customers_path)

    # Delivered orders only (retention engine uses delivered)
    delivered = orders[orders["order_status"] == "delivered"].copy()
    order_count_per_customer = delivered.groupby("customer_id").size()

    repeat_customers = order_count_per_customer[order_count_per_customer >= 2].index.tolist()
    single_customers = order_count_per_customer[order_count_per_customer == 1].index.tolist()

    # Sample so we have plenty of repeat customers for Retention & Loyalty charts
    n_repeat = min(TARGET_REPEAT_CUSTOMERS, len(repeat_customers))
    n_single = min(TARGET_SINGLE_CUSTOMERS, len(single_customers))
    if n_repeat < len(repeat_customers):
        repeat_customers = pd.Series(repeat_customers).sample(n=n_repeat, random_state=42).tolist()
    if n_single < len(single_customers):
        single_customers = pd.Series(single_customers).sample(n=n_single, random_state=42).tolist()

    selected_customer_ids = set(repeat_customers) | set(single_customers)
    # All orders (any status) for these customers
    selected_order_ids = set(orders[orders["customer_id"].isin(selected_customer_ids)]["order_id"])

    # Filter orders
    orders_out = orders[orders["order_id"].isin(selected_order_ids)]
    orders_out.to_csv(OUT_DIR / "olist_orders_dataset.csv", index=False)
    print(f"Wrote {len(orders_out)} rows -> data_sample/olist_orders_dataset.csv")

    # Filter customers
    customers_out = customers[customers["customer_id"].isin(selected_customer_ids)]
    customers_out.to_csv(OUT_DIR / "olist_customers_dataset.csv", index=False)
    print(f"Wrote {len(customers_out)} rows -> data_sample/olist_customers_dataset.csv")

    # Child tables: filter by selected_order_ids
    for name, key in [
        ("olist_order_items_dataset.csv", "order_id"),
        ("olist_order_payments_dataset.csv", "order_id"),
        ("olist_order_reviews_dataset.csv", "order_id"),
    ]:
        src = DATA_DIR / name
        if not src.exists():
            print(f"Skip (not found): {name}")
            continue
        df = pd.read_csv(src)
        df = df[df[key].isin(selected_order_ids)]
        df.to_csv(OUT_DIR / name, index=False)
        print(f"Wrote {len(df)} rows -> data_sample/{name}")

    # Products and sellers from order_items
    order_items_path = DATA_DIR / "olist_order_items_dataset.csv"
    if order_items_path.exists():
        oi = pd.read_csv(order_items_path)
        oi = oi[oi["order_id"].isin(selected_order_ids)]
        product_ids = oi["product_id"].dropna().unique()
        seller_ids = oi["seller_id"].dropna().unique()

        products = pd.read_csv(DATA_DIR / "olist_products_dataset.csv")
        products_out = products[products["product_id"].isin(product_ids)]
        products_out.to_csv(OUT_DIR / "olist_products_dataset.csv", index=False)
        print(f"Wrote {len(products_out)} rows -> data_sample/olist_products_dataset.csv")

        sellers = pd.read_csv(DATA_DIR / "olist_sellers_dataset.csv")
        sellers_out = sellers[sellers["seller_id"].isin(seller_ids)]
        sellers_out.to_csv(OUT_DIR / "olist_sellers_dataset.csv", index=False)
        print(f"Wrote {len(sellers_out)} rows -> data_sample/olist_sellers_dataset.csv")

    # Product category translation: keep all
    trans_path = DATA_DIR / "product_category_name_translation.csv"
    if trans_path.exists():
        df = pd.read_csv(trans_path)
        df.to_csv(OUT_DIR / "product_category_name_translation.csv", index=False)
        print(f"Wrote {len(df)} rows -> data_sample/product_category_name_translation.csv")

    # Geolocation: only zip codes that appear in sampled customers
    geo_path = DATA_DIR / "olist_geolocation_dataset.csv"
    if geo_path.exists():
        zips = set(customers_out["customer_zip_code_prefix"].dropna().astype(int).astype(str))
        geo = pd.read_csv(geo_path)
        geo_zips = geo["geolocation_zip_code_prefix"].astype(str)
        geo = geo[geo_zips.isin(zips)]
        if MAX_GEOLOCATION_ROWS and len(geo) > MAX_GEOLOCATION_ROWS:
            geo = geo.head(MAX_GEOLOCATION_ROWS)
        geo.to_csv(OUT_DIR / "olist_geolocation_dataset.csv", index=False)
        print(f"Wrote {len(geo)} rows -> data_sample/olist_geolocation_dataset.csv")

    print("Done. Commit data_sample/ and push so Streamlit Cloud can use it (Retention & Loyalty will have data).")


if __name__ == "__main__":
    main()

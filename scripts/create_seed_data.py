"""
Generate a minimal referentially consistent data_sample so Retention & Loyalty has data
without needing the full Olist dataset. Run from project root:  python scripts/create_seed_data.py
Use this when you don't have full data/ or when create_sample_data.py yielded 0 repeat customers.
Output: data_sample/ with same CSV names and schema as the real dataset.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import uuid

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data_sample"
DATA_DIR = BASE / "data"

# Target: enough repeat customers for retention charts
N_REPEAT_CUSTOMERS = 80   # customers with 2+ delivered orders
N_SINGLE_CUSTOMERS = 120  # customers with 1 delivered order
ORDERS_PER_REPEAT = (2, 4)  # min, max delivered orders per repeat customer


def _id():
    return uuid.uuid4().hex[:32]


def main():
    OUT_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(42)

    customers = []
    orders = []
    order_payments = []
    order_items = []
    order_reviews = []
    product_ids = set()
    seller_ids = set()

    # Create customers
    all_customer_ids = [_id() for _ in range(N_REPEAT_CUSTOMERS + N_SINGLE_CUSTOMERS)]
    for i, cid in enumerate(all_customer_ids):
        customers.append({
            "customer_id": cid,
            "customer_unique_id": _id(),
            "customer_zip_code_prefix": 1000 + (i % 100),
            "customer_city": "São Paulo",
            "customer_state": "SP",
        })

    # Orders: repeat customers get 2–4 delivered orders each, single get 1
    t0 = datetime(2017, 10, 1)
    order_id_list = []
    for i, cid in enumerate(all_customer_ids):
        if i < N_REPEAT_CUSTOMERS:
            n_orders = rng.integers(ORDERS_PER_REPEAT[0], ORDERS_PER_REPEAT[1] + 1)
        else:
            n_orders = 1
        for k in range(n_orders):
            oid = _id()
            order_id_list.append(oid)
            dt = t0 + timedelta(days=i * 3 + k * 30)
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            delivered = dt + timedelta(days=5)
            estimated = dt + timedelta(days=10)
            orders.append({
                "order_id": oid,
                "customer_id": cid,
                "order_status": "delivered",
                "order_purchase_timestamp": dt_str,
                "order_approved_at": dt_str,
                "order_delivered_carrier_date": (dt + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "order_delivered_customer_date": delivered.strftime("%Y-%m-%d %H:%M:%S"),
                "order_estimated_delivery_date": estimated.strftime("%Y-%m-%d 00:00:00"),
            })
            order_payments.append({
                "order_id": oid,
                "payment_sequential": 1,
                "payment_type": "credit_card",
                "payment_installments": 1,
                "payment_value": round(50 + rng.random() * 200, 2),
            })
            # One item per order (sales_engine needs order_items)
            pid, sid = _id(), _id()
            product_ids.add(pid)
            seller_ids.add(sid)
            order_items.append({
                "order_id": oid,
                "order_item_id": 1,
                "product_id": pid,
                "seller_id": sid,
                "shipping_limit_date": dt_str,
                "price": round(30 + rng.random() * 150, 2),
                "freight_value": round(10 + rng.random() * 20, 2),
            })
            order_reviews.append({
                "review_id": _id(),
                "order_id": oid,
                "review_score": int(rng.integers(1, 6)),
                "review_comment_title": "",
                "review_comment_message": "",
                "review_creation_date": delivered.strftime("%Y-%m-%d %H:%M:%S"),
                "review_answer_timestamp": delivered.strftime("%Y-%m-%d %H:%M:%S"),
            })

    # Products (sales_engine needs product_category)
    cat = "cama_mesa_banho"
    products = [
        {
            "product_id": pid,
            "product_category_name": cat,
            "product_name_lenght": 50,
            "product_description_lenght": 200,
            "product_photos_qty": 1,
            "product_weight_g": 500,
            "product_length_cm": 20,
            "product_height_cm": 10,
            "product_width_cm": 15,
        }
        for pid in product_ids
    ]

    # Sellers
    sellers = [
        {"seller_id": sid, "seller_zip_code_prefix": 1301, "seller_city": "São Paulo", "seller_state": "SP"}
        for sid in seller_ids
    ]

    # Geolocation (zip codes we used)
    zips = sorted(set(c["customer_zip_code_prefix"] for c in customers))
    geolocation = [
        {
            "geolocation_zip_code_prefix": z,
            "geolocation_lat": -23.55,
            "geolocation_lng": -46.63,
            "geolocation_city": "São Paulo",
            "geolocation_state": "SP",
        }
        for z in zips
    ]

    # Product category translation: copy from data/ if present, else minimal
    trans_path = DATA_DIR / "product_category_name_translation.csv"
    if trans_path.exists():
        trans = pd.read_csv(trans_path)
    else:
        trans = pd.DataFrame([
            {"product_category_name": "cama_mesa_banho", "product_category_name_english": "bed_bath_table"},
            {"product_category_name": "beleza_saude", "product_category_name_english": "health_beauty"},
        ])

    # Write CSVs
    pd.DataFrame(customers).to_csv(OUT_DIR / "olist_customers_dataset.csv", index=False)
    pd.DataFrame(orders).to_csv(OUT_DIR / "olist_orders_dataset.csv", index=False)
    pd.DataFrame(order_payments).to_csv(OUT_DIR / "olist_order_payments_dataset.csv", index=False)
    pd.DataFrame(order_items).to_csv(OUT_DIR / "olist_order_items_dataset.csv", index=False)
    pd.DataFrame(order_reviews).to_csv(OUT_DIR / "olist_order_reviews_dataset.csv", index=False)
    pd.DataFrame(products).to_csv(OUT_DIR / "olist_products_dataset.csv", index=False)
    pd.DataFrame(sellers).to_csv(OUT_DIR / "olist_sellers_dataset.csv", index=False)
    pd.DataFrame(geolocation).to_csv(OUT_DIR / "olist_geolocation_dataset.csv", index=False)
    trans.to_csv(OUT_DIR / "product_category_name_translation.csv", index=False)

    repeat_count = N_REPEAT_CUSTOMERS
    print(f"Wrote data_sample/: {len(customers)} customers, {len(orders)} orders, {repeat_count} repeat customers (2+ delivered).")
    print("Retention & Loyalty will have data. Commit data_sample/ and push.")


if __name__ == "__main__":
    main()

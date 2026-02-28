# Olist E‑commerce Analytics Dashboard (SQL‑First)

**Live dashboard:** [Open the app](https://olist-sql-dashboard.streamlit.app)

## Overview

This project is a SQL‑first e‑commerce analytics dashboard built on the public [Olist Brazilian E‑commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). It is designed to showcase senior‑level SQL modeling, business analytics, and storytelling.

- **Analytics engine:** DuckDB (in‑memory, columnar database)
- **UI:** Streamlit + Plotly
- **Focus:** Three “engines” implemented as SQL views:
  - **Sales & Profit**
  - **Logistics & Sentiment**
  - **Retention & Loyalty**

The Python/Streamlit layer is intentionally thin: it applies filters and renders charts, while almost all business logic lives in SQL.

---

## Project Goals

I built this project to demonstrate that I can:

- Design **business‑relevant metrics and views**
- Write **advanced SQL** (CTEs, window functions, multi‑table joins, correct aggregation grain)
- Connect **business questions** (revenue, operations, retention) to clear, interactive visuals

---

## Dataset

- Source: Olist Brazilian E‑commerce Public Dataset
- Loaded from local `/data` CSV files into DuckDB tables on app startup:
  - `orders`, `order_items`, `order_payments`, `order_reviews`
  - `customers`, `products`, `product_category_name_translation`
  - `sellers`, `geolocation`

> To run locally: download the dataset from Kaggle and place the CSVs in the `data/` folder. To deploy so the live app matches local exactly, commit the `data/` folder to the repo (see **DEPLOY.md**).

---

## How to Run

**Option 1 — Live (no setup)**  
Open the dashboard in your browser: **[https://olist-sql-dashboard.streamlit.app](https://olist-sql-dashboard.streamlit.app)**

**Option 2 — Local**  
In the folder that contains `app.py`, run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

**Data check script:** From the same folder, run `python data_prep.py` to confirm the orders data is present and see its date range and row count. No dashboard required.

---

## Where to Find the SQL

The SQL for each analytics engine lives in the **`sql/`** folder so the logic is easy to find and reuse:

| Engine | File |
|--------|------|
| Sales & Profit | [sql/sales_engine.sql](sql/sales_engine.sql) |
| Logistics & Sentiment | [sql/logistics_engine.sql](sql/logistics_engine.sql) |
| Retention & Loyalty | [sql/retention_engine.sql](sql/retention_engine.sql) |

`app.py` loads these files at startup and registers them as DuckDB views. No SQL is hidden in the UI layer.

---

## Architecture

### Data loading

On startup, `app.py`:

1. Scans the `data/` folder for `.csv` files.
2. Loads each CSV into DuckDB using `read_csv_auto`.
3. Creates one DuckDB table per file (e.g. `olist_orders_dataset.csv` → `orders`).

### SQL views

Three main DuckDB views implement the analytics “engines”:

- `sales_engine` – revenue and product mix
- `logistics_engine` – delivery performance vs customer sentiment
- `retention_engine` – customer lifetime value and loyalty behavior

The Streamlit pages query these views with filters (dates, states) and render charts.

---

## Dashboard Pages

### 1. Executive Summary — Sales & Profit Engine

**Business question:**  
How is revenue trending, and what categories and regions drive it?

**SQL view:** `sales_engine`

- **Tables used:** `orders`, `order_items`, `products`, `product_category_name_translation`, `customers`
- **Key logic:**
  - Filters to **delivered** orders only.
  - Joins items to products and category translations (English names).
  - Joins customers to attach `customer_state`.
  - Standardizes timestamps with `DATE_TRUNC('day', order_purchase_timestamp)`.

**Filters:** Order date range, Customer state (multi-select)

**Visuals:**

1. **Monthly Revenue (line chart)** – `SUM(price)` grouped by month; shows revenue trends over time.
2. **Top 15 Categories by Revenue (bar chart)** – `SUM(price)` grouped by product category; highlights which categories drive the business.

---

### 2. Logistics & Sentiment — Logistics & Sentiment Engine

**Business question:**  
Do shipping delays lead to worse customer reviews?

**SQL view:** `logistics_engine`

- **Tables used:** `orders`, `order_reviews`
- **Key logic:**
  - Filters to **delivered** orders with valid actual and estimated dates.
  - Joins to reviews with non-null `review_score`.
  - Computes `days_late = delivered_date − estimated_date` (positive = late, 0 = on time, negative = early).
  - Buckets delivery performance in SQL: Early, On time, Late 1–2 days, Late 3–7 days, Late 8+ days.

**Filter:** Delivery date range

**Visual:** Average Review Score by Delivery Performance (bar chart) – groups by delivery bucket, `AVG(review_score)`, order counts in table.

**Interpretation:** Shows whether late deliveries correlate with lower review scores and connects operations to customer experience.

---

### 3. Retention & Loyalty — Retention & Loyalty Engine

**Business question:**  
Do we retain customers, and who are the most valuable loyalists?

**SQL view:** `retention_engine`

- **Tables used:** `customers`, `orders`, `order_payments`
- **Key logic:**
  - Filters to **delivered** orders.
  - Uses window functions (`LAG`) to build per-customer timelines and compute `days_between` consecutive orders.
  - Aggregates payments per order (`ORDER_PAYMENTS_AGG`) to avoid double-counting.
  - One row per **repeat customer** (`total_orders > 1`) with: `first_order_date`, `last_order_date`, `tenure_days`, `total_orders`, `total_spent`, `avg_days_between_orders`.

**Filter:** First order date range

**Metrics and visuals:**

- **Repeat Rate (%)** – % of delivered customers who become repeat buyers.
- **Avg days between 1st & 2nd purchase** – early repeat behavior.
- **Median days between orders** – typical reorder cadence.
- **Scatter: Customer Value vs Repeat Frequency** – X: `avg_days_between_orders`, Y: `total_spent`, size: `total_orders`.
- **Distribution of total orders per customer** – how deep loyalty goes (2, 3, 4+ orders).
- **Top Loyal Customers (table)** – top 20 by `total_spent` with `total_orders` and `avg_days_between_orders`.

---

### 4. Raw SQL Lab

A scratchpad to run your own SQL against the same DuckDB instance the dashboard uses.

**Tables** (from the CSVs): `orders`, `order_items`, `order_payments`, `order_reviews`, `customers`, `products`, `product_category_name_translation`, `sellers`, `geolocation`

**Views** (the three engines): `sales_engine`, `logistics_engine`, `retention_engine`

Example: `SELECT * FROM orders LIMIT 10` or `SELECT * FROM sales_engine WHERE customer_state = 'SP' LIMIT 5`

---

## SQL Techniques Demonstrated

- **CTEs** for step-by-step transformations
- **Window functions:** `LAG`, `ROW_NUMBER`
- **Date/time logic:** `DATE_TRUNC`, `date_diff`
- **Safe aggregation grain:** per-order payment aggregation before rolling up to customers
- **Bucketing:** `CASE WHEN` for delivery performance bands
- **Parameterised filtering:** date and state filters passed into SQL

---

## Assumptions & Design Choices

- Revenue and behavior are measured on **delivered orders** only.
- Customer value = **total payments per order** (no refunds/COGS in dataset).
- Delivery lateness: `days_late = delivered − estimated` (positive = late).
- Retention view focuses on **repeat customers** (`total_orders > 1`).

---

## Possible Next Steps

- **Retention over time:** Track how many customers who first bought in a given month came back in later months (e.g. “Jan 2018 cohort: 20% ordered again within 3 months”).
- **Profitability:** Use freight and product cost (if available) to show revenue minus costs, not just revenue.
- **Smarter delivery–review analysis:** Slice the “late delivery → worse reviews” result by state, category, or seller so we know where the problem is worst.

---

If you have any questions about the SQL logic or the trade-offs behind these metrics, feel free to reach out.
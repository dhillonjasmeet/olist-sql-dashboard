# Olist SQL Dashboard — Full Project Breakdown

A study guide for the entire project: what we built, what each file does, and how the SQL and Streamlit pieces fit together. Python is explained in simple language.

---

## Part 1: Project overview

**What this project is**
- A **SQL-first** analytics dashboard on the Olist Brazilian e-commerce dataset.
- **DuckDB** holds the data in memory and runs all the analytics via SQL.
- **Streamlit** is the UI: filters, charts, and tables. It stays thin; the real logic is in SQL.
- **Live app:** [https://olist-sql-dashboard.streamlit.app](https://olist-sql-dashboard.streamlit.app)

**Why “SQL-first”**
- The three main analyses (Sales, Logistics, Retention) are each defined as one **SQL view** in the `sql/` folder.
- The app loads those SQL files, creates views in DuckDB, then runs more SQL (with your filter choices) to get the numbers for the charts. So you can study and change the logic in one place: the `.sql` files.

**Main steps we did (high level)**
1. **Data:** Put Olist CSVs in `data/`; app loads them into DuckDB tables.
2. **SQL engines:** Wrote three views — Sales, Logistics, Retention — in `sql/*.sql`.
3. **Streamlit:** Built four pages (Executive Summary, Logistics & Sentiment, Retention & Loyalty, Raw SQL Lab) with filters and Plotly charts.
4. **Deployment:** Committed `data/` to the repo and deployed the app on Streamlit Community Cloud so the live URL uses the same data as local.

---

## Part 2: What’s in each file

### **`app.py`** (main application)

**Role:** Starts the app, loads data into DuckDB, creates the three SQL views, and runs the Streamlit UI (sidebar, pages, filters, charts).

**In simple terms:**
- **Top (imports and paths):** Imports Streamlit, DuckDB, pandas, Plotly; defines where the project folder, `data/`, and `sql/` are.
- **`_get_data_dir()`:** Decides which folder to read CSVs from: `data/` if it has CSVs, otherwise `data_sample/` (e.g. on Cloud). Returns that folder path.
- **`csv_to_table_name()`:** Converts a CSV filename to a DuckDB table name (e.g. `olist_orders_dataset.csv` → `orders`).
- **`load_data_into_duckdb()`:** Creates an in-memory DuckDB database, finds all CSVs in the chosen folder, and loads each CSV into a table with the name from `csv_to_table_name()`. Cached so we don’t reload on every click.
- **`_load_sql()`:** Reads a `.sql` file from `sql/` and returns its text (for creating views).
- **View setup:** Loads the three SQL files and runs `CREATE OR REPLACE VIEW ...` so DuckDB has `sales_engine`, `logistics_engine`, and `retention_engine`.
- **`main()`:**  
  - Sets page title and layout.  
  - Loads data and checks that at least the `orders` table exists; if not, shows an error and stops.  
  - Creates the three views; if that fails, shows an error and stops.  
  - Builds the sidebar (title + page selector: Executive Summary, Logistics & Sentiment, Retention & Loyalty, Raw SQL Lab).  
  - For each selected page: gets filter bounds from the right view, builds filter widgets (sliders, multiselect), runs SQL with those filter values, and displays metrics, Plotly charts, and/or dataframes.

So: **app.py** = “load data → create views → show the right page and run the SQL that page needs.”

---

### **`sql/sales_engine.sql`**

**Role:** Defines the **Sales & Profit** dataset: one row per order-item line, with purchase date, product category, price, and customer state. Only delivered orders.

**What it does (step by step):**
1. **`total_products`:** For each product, gets category name in English (from the translation table) or falls back to the raw category name.
2. **`total_orders`:** For each delivered order, gets order_id, purchase date (day), product_id, price, and customer state by joining orders → order_items and orders → customers. Only `order_status = 'delivered'`.
3. **Final SELECT:** Joins that order-level data to `total_products` to attach `product_category`, and outputs: `order_id`, `purchase_date`, `product_id`, `product_category`, `price`, `customer_state`.

**Grain:** One row per order item (an order can have multiple rows if it has multiple items).  
**Used by:** Executive Summary page (monthly revenue, top 15 categories), with date and state filters applied in the app.

---

### **`sql/logistics_engine.sql`**

**Role:** Connects **delivery performance** (on time vs late) to **review scores**. One row per delivered order that has a review.

**What it does:**
1. **`base`:** For delivered orders that have both delivery and estimated dates and a review score, gets order_id, delivered timestamp, estimated timestamp, and review_score.
2. **`metrics`:** Computes `days_late = delivered_ts - estimated_ts` (in days). Positive = late, 0 = on time, negative = early.
3. **Final SELECT:** Adds a **delivery bucket** with `CASE`:
   - `days_late <= -1` → `'Early'`
   - `days_late = 0` → `'On time'`
   - `1–2` → `'Late 1-2 days'`
   - `3–7` → `'Late 3-7 days'`
   - else → `'Late 8+ days'`  
   Outputs: `delivery_date`, `days_late`, `delivery_time`, `review_score`.

**Used by:** Logistics & Sentiment page: average review score by delivery bucket (and order counts in a table), with a delivery-date filter.

---

### **`sql/retention_engine.sql`**

**Role:** Describes **repeat customers** (2+ delivered orders): when they first/last ordered, how much they spent, how many orders, and average days between orders.

**What it does:**
1. **`ORDER_INTERVALS`:** For each delivered order, per customer, uses **LAG** to get the previous order date. So we have current and previous order dates per row.
2. **`TIME_DIFFS`:** For rows that have a previous order, computes `days_between` = current order date − previous order date (per customer).
3. **`ORDER_PAYMENTS_AGG`:** Sums `payment_value` per order so we don’t double-count when an order has multiple payment rows.
4. **Final SELECT:** Joins customers → orders → `ORDER_PAYMENTS_AGG`, and left-joins `TIME_DIFFS` to get average days between orders. Filters to delivered only. Groups by customer. Uses **HAVING COUNT(DISTINCT o.order_id) > 1** so we only keep repeat customers. Outputs: `customer_unique_id`, `first_order_date`, `last_order_date`, `tenure_days`, `total_orders`, `total_spent`, `avg_days_between_orders`.

**Grain:** One row per repeat customer.  
**Used by:** Retention & Loyalty page: metrics (repeat rate, medians, avg days 1st→2nd purchase), scatter (value vs repeat frequency), distribution of order count, and top 20 by total spent. Filter: first order date range.

---

### **`data_prep.py`**

**Role:** Quick data check. Loads the orders CSV, converts the purchase timestamp to datetime, and prints: number of rows/columns, date range, and counts per order status.

**In simple terms:** It uses the same `data/` folder as the app. You run `python data_prep.py` to confirm the orders file is there and see its shape and date range without opening the dashboard.

---

### **`requirements.txt`**

Lists the Python packages the app needs: `streamlit`, `duckdb`, `plotly`, `pandas`. You run `pip install -r requirements.txt` to install them.

---

### **`.gitignore`**

Tells Git which files/folders not to track: e.g. `__pycache__/`, `.venv/`, `data_sample/`, and personal notes like `PROJECT_WALKTHROUGH.md`, `HOW_TO_TALK_ABOUT_THIS.md`, `data_prep_NOTES.py`. Your `data/` CSVs are committed so the live app can use them.

---

### **`README.md`**

Project title, live dashboard link, short overview, how to run (live link first, then local), where the SQL lives, and documentation of the three engines and the Raw SQL Lab. Aimed at recruiters and readers of the repo.

---

### **`data/`** (folder)

Contains the Olist CSV files (e.g. `olist_orders_dataset.csv`, `olist_customers_dataset.csv`, `olist_order_payments_dataset.csv`, etc.). The app loads all `.csv` files from here (or from `data_sample/` if `data/` has no CSVs). Same data is used locally and on Streamlit Cloud because `data/` is committed.

---

## Part 3: SQL techniques you used

| Technique | Where it’s used | What it does |
|-----------|-----------------|--------------|
| **CTEs (WITH … AS)** | All three engines | Break the logic into steps (e.g. base → metrics → final SELECT). Easier to read and debug. |
| **LAG()** | retention_engine | For each customer’s orders in date order, gets the previous order’s date so we can compute days between orders. |
| **PARTITION BY / ORDER BY** | retention_engine (LAG) | LAG is computed per customer (PARTITION BY customer_unique_id) in date order. |
| **ROW_NUMBER()** | app.py (Retention page) | Used in an inline query to get “first” and “second” order per customer to compute avg days between 1st and 2nd purchase. |
| **DATE_TRUNC / date_diff** | All three + app | Standardize to day/month and compute differences in days. |
| **CASE WHEN** | logistics_engine | Bucket numeric `days_late` into labels: Early, On time, Late 1–2 days, etc. |
| **COALESCE** | sales_engine | Use English category name when available, otherwise raw category. |
| **JOINs** | All | Link orders to items, customers, payments, reviews, products, translation table. |
| **LEFT JOIN** | sales_engine, retention_engine | Keep orders/items even when category or time-diff is missing. |
| **HAVING** | retention_engine | Keep only customers with more than one delivered order. |
| **Aggregation (SUM, AVG, COUNT, MIN, MAX)** | All three | Revenue, counts, averages, first/last dates. |

---

## Part 4: Streamlit pages and visualizations

**How it works in general**
- The sidebar has a radio button to pick the page.
- Each page (except Raw SQL Lab) gets min/max dates (and sometimes state list) from the right view, then builds sliders/multiselect from that.
- The app builds a SQL string with `WHERE` (and maybe `IN`) using the selected filter values and runs it with `con.execute(..., params).fetchdf()`.
- Results are shown as **metrics** (`st.metric`), **Plotly charts** (`px.line`, `px.bar`, `px.scatter` + `st.plotly_chart`), or **tables** (`st.dataframe`).

---

### **Page 1: Executive Summary (Sales & Profit)**

- **Data source:** `sales_engine` view.
- **Filters (sidebar):**  
  - Order date range (slider from min/max `purchase_date`).  
  - Customer state (multiselect; options from distinct `customer_state` in `sales_engine`).
- **SQL in the app:**  
  - Monthly revenue: `date_trunc('month', purchase_date)`, `SUM(price)`, grouped by month, with your date and state filter.  
  - Top 15 categories: `product_category`, `SUM(price)`, grouped by category, ordered by revenue DESC, LIMIT 15, same filters.
- **Visualizations:**  
  1. **Line chart:** Monthly revenue (month on x-axis, revenue on y-axis).  
  2. **Bar chart:** Top 15 categories by revenue (category on x-axis, revenue on y-axis).

---

### **Page 2: Logistics & Sentiment**

- **Data source:** `logistics_engine` view.
- **Filter:** Delivery date range (slider from min/max `delivery_date`).
- **SQL in the app:**  
  For the selected delivery date range: group by `delivery_time`, count orders, average `review_score`. Order by a CASE so buckets appear: Early → On time → Late 1–2 → Late 3–7 → Late 8+.
- **Visualizations:**  
  1. **Bar chart:** Delivery bucket (x) vs average review score (y), with color scale (e.g. red–yellow–green).  
  2. **Table:** Same grouping: delivery_time, order count, avg review score.

---

### **Page 3: Retention & Loyalty**

- **Data source:** `retention_engine` view (and a couple of inline SQL queries for repeat rate and avg days 1st→2nd purchase).
- **Filter:** First order date range (slider from min/max `first_order_date`).
- **SQL in the app:**  
  - Main dataset: `customer_unique_id`, `total_spent`, `total_orders`, `avg_days_between_orders` from `retention_engine` with the date filter.  
  - Repeat rate: CTEs counting “all customers with at least one delivered order” and “customers in retention_engine” (repeat); rate = repeat / all.  
  - Avg days 1st→2nd: CTEs with ROW_NUMBER to get 1st and 2nd order per customer, then average of days between those two.  
  - Distribution: `total_orders`, COUNT of customers, from `retention_engine` with date filter, grouped by `total_orders`.
- **Visualizations:**  
  1. **Metrics (two columns):** Repeat rate %, customers in range, median total spent; avg days 1st→2nd purchase, median total orders, median days between orders.  
  2. **Scatter:** X = avg days between orders, Y = total spent, point size = total orders (customer value vs repeat frequency).  
  3. **Bar chart:** Total orders per customer (x) vs number of customers (y).  
  4. **Table:** Top 20 customers by total spent (columns: customer_unique_id, total_spent, total_orders, avg_days_between_orders).

---

### **Page 4: Raw SQL Lab**

- **No filters.** A text area for free-form SQL and a “Run” button.
- **Behavior:** When you click Run, the app runs your SQL against the same DuckDB connection (so all tables and the three views are available) and shows the result as a dataframe. Errors are shown in red.

---

## Part 5: Python in simple language

- **`Path(__file__).resolve().parent`** — “The folder where this script (app.py) lives.” We use it to build paths to `data/` and `sql/` so the app works from the project root.
- **`@st.cache_resource`** — “Run this function once and reuse the result.” Used for `load_data_into_duckdb()` so we don’t reload all CSVs on every interaction.
- **`con.execute(sql).fetchdf()`** — “Run this SQL in DuckDB and give me the result as a pandas DataFrame.” Used everywhere we need to build a chart or table.
- **`con.execute(sql, params)`** — Same, but the query can have `?` placeholders; `params` is a list of values (e.g. start date, end date, list of states) so we avoid SQL injection and keep the query clean.
- **`st.sidebar.slider(...)`** — Puts a date or number range slider in the sidebar; returns the selected range (e.g. (start_d, end_d)).
- **`st.sidebar.multiselect(...)`** — List of options; user can pick several. We use it for states (default: all).
- **`px.line(df, x=..., y=...)`** — Builds a Plotly line chart from a DataFrame; we then pass it to `st.plotly_chart(fig)` to show it.
- **`px.bar(...)` / `px.scatter(...)`** — Same idea for bar and scatter plots.
- **`st.metric(label, value)`** — One big number with a label (e.g. “Repeat rate”, “45.2%”).
- **`st.dataframe(df)`** — Shows a DataFrame as an interactive table.
- **`st.columns(2)`** — Splits the next block into two columns (e.g. for two groups of metrics).
- **`try: ... except: st.error(...); st.stop()`** — If something fails (no data, view creation error), show a message and stop so the user doesn’t see a crash.

---

## Part 6: Data flow (end to end)

1. You run `streamlit run app.py` (or open the live link).
2. **Startup:** App finds `data/` (or `data_sample/`), loads every CSV into DuckDB tables (`orders`, `customers`, `order_items`, etc.).
3. App reads `sql/sales_engine.sql`, `sql/logistics_engine.sql`, `sql/retention_engine.sql` and runs `CREATE OR REPLACE VIEW` for each. Now DuckDB has three views on top of the base tables.
4. You pick a page. The app runs SQL to get min/max dates (and options like states) from the right view, then builds the filters.
5. You change a filter (or use defaults). The app builds a new SQL string with your choices (e.g. date range, states), runs it, gets a DataFrame, and draws the chart or table.
6. Raw SQL Lab: you type SQL and click Run; the same DuckDB connection runs it and shows the result.

So: **CSVs → DuckDB tables → three SQL views → Streamlit filters + SQL per page → Plotly + tables.**

---

## Part 7: Deployment (what we did)

- **Goal:** Live app at a URL that uses the **same** data as on your machine.
- **Approach:** Allow committing the `data/` folder (removed `data/*.csv` from `.gitignore`). Repo has the same CSVs you use locally.
- **Steps:** Put Olist CSVs in `data/` → `git add data/` → commit → push. On Streamlit Community Cloud, point the app to this repo and main file `app.py`. Cloud runs the app and reads `data/` from the repo, so the report matches local.

---

You can use this document to review the project, explain it in interviews, or change the SQL/Streamlit logic and know exactly where to look.

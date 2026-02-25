# How to Explain This Project (Without Reading Every Line)

Use this as a cheat sheet to understand the app and talk about it confidently in interviews.

---

## Step 1: Know the Big Picture (30 seconds)

- **What it is:** A dashboard that answers three business questions using SQL and a thin Python/Streamlit UI.
- **Data:** Olist e-commerce CSVs (orders, items, customers, products, reviews, payments, etc.).
- **Flow:** CSVs → DuckDB tables → SQL views (the “engines”) → Streamlit runs queries with filters → Plotly draws charts.

You don’t need to memorize the code. You need to say: “Data loads into DuckDB, my SQL views do the logic, and Python just runs those queries and passes the results to the charts.”

---

## Step 2: Map the App in Four Chunks

Open `app.py` and think of it as four parts. You only need to know what each part *does*, not every line.

| Part | Rough line range | What it does in one sentence |
|------|------------------|------------------------------|
| **Setup** | Top (~lines 1–50) | Imports, paths, `load_data_into_duckdb()` loads all CSVs into DuckDB tables; `_load_sql()` reads the `.sql` files; the three `*_ENGINE_SQL` variables hold the view definitions. |
| **Views** | Middle (before `main`) | `get_sales_data(conn)` runs the Sales Engine query and returns a DataFrame. The Logistics and Retention views are created inside `main()` from the SQL files. |
| **main()** | Rest of file | Creates the DuckDB connection and the three views; builds the sidebar (page choice + filters); for each page, runs the right SQL with the chosen filters and passes the result to Plotly. |
| **Page blocks** | Inside `main()` | Each `if page == "..."` block: (1) gets filter values from the sidebar, (2) runs one or more SQL queries with those values, (3) calls `px.line`, `px.bar`, `px.scatter`, or `st.dataframe` with the query result. |

When someone says “walk me through the code,” you can say: “The top loads data and SQL; `main()` wires the sidebar and pages; each page block runs SQL with the user’s filters and sends the result to a chart.”

---

## Step 3: Trace One Flow End-to-End (Executive Summary)

Follow one path so you can explain it in 30 seconds. Pick **Executive Summary**:

1. **User:** Opens the app, picks “Executive Summary,” selects a date range and some states in the sidebar.
2. **Code:** Reads `date_range` and `selected_states` from the sidebar.
3. **Code:** Builds a `WHERE` clause: `purchase_date BETWEEN ? AND ?` and `customer_state IN (...)`.
4. **Code:** Runs two queries against the `sales_engine` view with that `WHERE` clause:
   - One groups by month and sums `price` → monthly revenue.
   - One groups by category, sums `price`, takes top 15 → category revenue.
5. **Code:** Passes each result DataFrame to `px.line()` and `px.bar()`.
6. **User:** Sees the charts update.

**Script to say:** “On Executive Summary, the user picks a date range and states. We pass those into the SQL so the `sales_engine` view is filtered. We run two queries: one for monthly revenue, one for top categories. We pass the results to Plotly and it draws the line chart and bar chart. So the logic is in SQL; Python just runs the queries and visualizes.”

---

## Step 4: Vocabulary to Use When Explaining

- **DuckDB:** In-memory database we load the CSVs into; we run SQL against it.
- **View:** A saved query (e.g. `sales_engine`). We don’t copy-paste the big query every time; we `SELECT * FROM sales_engine WHERE ...`.
- **CTE:** “Common Table Expression”—the `WITH x AS (SELECT ...)` blocks in the SQL files. They break the query into steps.
- **Parameterized query:** We put `?` in the SQL and pass the filter values (dates, states) separately so it’s safe and clear.
- **DataFrame:** What DuckDB returns (table-like). Plotly and Streamlit take DataFrames as input.
- **Streamlit:** Renders the sidebar and the page; when the user changes a filter, the script re-runs and we run the SQL again with the new values.

You don’t need to define these in an interview; use the words naturally when you say “we pass the filters into the parameterized query” or “the view is built from CTEs.”

---

## Step 5: “How I Built This” Script (Practice Out Loud)

- “I started with the business questions: revenue and mix, delivery vs reviews, and retention. I modeled each as a SQL view so the logic lives in the database.”
- “The SQL is in the `sql/` folder—one file per engine. The app loads those files and registers them as DuckDB views. So anyone can read the transformation logic without digging through Python.”
- “The UI is Streamlit. Each page has filters in the sidebar. When the user changes a filter, we rebuild the WHERE clause, run the query against the right view, and pass the result to Plotly. So Python is mostly orchestration: run this query, pass that result to this chart.”
- “I focused on getting the SQL and the metrics right; the dashboard is there so you can slice by date and geography and see the same logic.”

---

## Step 6: “How I’d Change or Extend It” (Shows You Understand the Data)

- “I’d add a simple data check script: load the CSVs, print row counts and date ranges, maybe a few value counts. That would make it obvious we’re not dropping rows or mixing up dates.”
- “For retention, we could add a cohort view: customers who first ordered in month X, and what share ordered again in the next 1–3 months. That’s the same tables and LAG logic, just aggregated by cohort month.”
- “For logistics, we could slice the delivery–review relationship by state or seller so we know where the problem is worst. Same view, add a dimension to the GROUP BY.”

These show you understand the *data* and the *questions*, not just the code.

---

## Step 7: One Thing You Can Say You Wrote (Optional but Strong)

Add a tiny script that does **one** clear thing with the data, and do it yourself (or with minimal help). Then you can say: “I wrote a short script that loads the orders CSV and prints summary stats so we can confirm the date range and volume.”

Example idea: a file `data_prep.py` or `scripts/check_data.py` that (1) loads `data/olist_orders_dataset.csv` with pandas, (2) prints `df.shape`, (3) prints `order_purchase_timestamp` min/max, (4) prints `order_status` value counts. About 10 lines. You can point to it and say “I wrote this to validate the data before building the dashboard.”

---

## Summary

1. **Big picture:** Data → DuckDB → SQL views → Streamlit runs filtered queries → Plotly charts.
2. **Map:** Setup (load data + SQL), views, `main()` (sidebar + pages), page blocks (query + chart).
3. **One flow:** Executive Summary: filters → WHERE clause → two queries on `sales_engine` → two charts.
4. **Vocabulary:** DuckDB, view, CTE, parameterized query, DataFrame, Streamlit—use these when explaining.
5. **Script:** Practice the “how I built this” and “how I’d extend it” bullets above.
6. **Optional:** One small data-check script you write so you have something to point to as “I wrote this.”

You don’t need to be a senior Python developer. You need to show you understand the data, the business questions, and how the pieces fit together. This walkthrough gives you the map and the words to do that.

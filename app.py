"""
Olist data explorer: DuckDB + Streamlit.
Loads all CSVs from /data into DuckDB tables and provides navigation views.
"""
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_SAMPLE_DIR = BASE_DIR / "data_sample"
SQL_DIR = BASE_DIR / "sql"


def _get_data_dir() -> Path:
    """Use data/ if it has CSVs (local full data); else data_sample/ (for deployed demo)."""
    if DATA_DIR.exists() and list(DATA_DIR.glob("*.csv")):
        return DATA_DIR
    if DATA_SAMPLE_DIR.exists() and list(DATA_SAMPLE_DIR.glob("*.csv")):
        return DATA_SAMPLE_DIR
    return DATA_DIR  # will be empty on first deploy until sample is committed


def csv_to_table_name(csv_path: Path) -> str:
    """Map CSV filename to DuckDB table name (e.g. olist_orders_dataset.csv -> orders)."""
    name = csv_path.stem.lower()
    if name.startswith("olist_") and name.endswith("_dataset"):
        t = name[6:-8]  # strip 'olist_' and '_dataset'
        return t.rstrip("_") if t.endswith("_") else t  # "orders_" -> "orders"
    return name.replace("-", "_")


@st.cache_resource
def load_data_into_duckdb():
    """Load every CSV from data/ or data_sample/ into DuckDB with matching table names."""
    con = duckdb.connect(":memory:")
    data_dir = _get_data_dir()
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        return con  # no tables; caller will show friendly message
    for csv_path in csv_files:
        table_name = csv_to_table_name(csv_path)
        # Use read_csv_auto and register as table
        con.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto(?)",
            [str(csv_path.resolve())],
        )
    return con


def _load_sql(name: str) -> str:
    """Load SQL from sql/<name>.sql for clarity and reuse."""
    path = SQL_DIR / f"{name}.sql"
    return path.read_text(encoding="utf-8").strip().rstrip(";")


SALES_ENGINE_SQL = _load_sql("sales_engine")


def get_sales_data(conn):
    """Return Sales & Profit Engine result: order-level lines with category, price, state."""
    return conn.execute(SALES_ENGINE_SQL).fetchdf()


LOGISTICS_ENGINE_SQL = _load_sql("logistics_engine")


RETENTION_ENGINE_SQL = _load_sql("retention_engine")


def main():
    st.set_page_config(page_title="Olist Data Explorer", layout="wide")
    con = load_data_into_duckdb()

    # Fail fast if no data was loaded.
    try:
        con.execute("SELECT 1 FROM orders LIMIT 1")
    except Exception:
        data_dir = _get_data_dir()
        csv_count = len(list(data_dir.glob("*.csv"))) if data_dir.exists() else 0
        st.error(
            "**No data loaded.** The app needs CSV files in the **data/** folder. "
            f"Checked: `data/` exists={data_dir.exists()}, CSV count={csv_count}. "
            "**Local:** Put your Olist CSVs in **data/** and run the app again. "
            "**Streamlit Cloud:** Commit your **data/** folder to the repo (`git add data/`, commit, push), then reboot the app."
        )
        st.stop()

    try:
        con.execute(f"CREATE OR REPLACE VIEW sales_engine AS {SALES_ENGINE_SQL}")
        con.execute(f"CREATE OR REPLACE VIEW logistics_engine AS {LOGISTICS_ENGINE_SQL}")
        con.execute(f"CREATE OR REPLACE VIEW retention_engine AS {RETENTION_ENGINE_SQL}")
    except Exception:
        st.error("Data loaded but view creation failed. Check app logs.")
        st.stop()

    st.sidebar.title("Olist Explorer")
    page = st.sidebar.radio(
        "Navigation",
        [
            "Executive Summary",
            "Logistics & Sentiment",
            "Retention & Loyalty",
            "Raw SQL Lab",
        ],
        label_visibility="collapsed",
    )

    if page == "Executive Summary":
        st.header("Executive Summary")
        # Build filters from the full sales_engine view (stable options, SQL-driven)
        date_bounds = con.execute(
            """
            SELECT
                MIN(purchase_date)::DATE AS min_date,
                MAX(purchase_date)::DATE AS max_date
            FROM sales_engine
            """
        ).fetchone()

        if date_bounds is None or date_bounds[0] is None:
            st.warning("No sales data available.")
        else:
            min_date, max_date = date_bounds

            st.sidebar.subheader("Filters")
            date_range = st.sidebar.slider(
                "Order date range",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="YYYY-MM-DD",
            )

            state_options = [
                r[0]
                for r in con.execute(
                    """
                    SELECT DISTINCT customer_state
                    FROM sales_engine
                    WHERE customer_state IS NOT NULL
                    ORDER BY customer_state
                    """
                ).fetchall()
            ]

            selected_states = st.sidebar.multiselect(
                "Customer state",
                options=state_options,
                default=state_options,
            )

            start_d, end_d = date_range

            # Build SQL WHERE clause with parameters for filters
            where_clause = "WHERE purchase_date BETWEEN ? AND ?"
            params = [start_d, end_d]

            if selected_states:
                placeholders = ",".join(["?"] * len(selected_states))
                where_clause += f" AND customer_state IN ({placeholders})"
                params.extend(selected_states)

            # Monthly revenue (pure SQL over the sales_engine view)
            monthly_sql = f"""
                SELECT
                    date_trunc('month', purchase_date) AS month,
                    SUM(price) AS revenue
                FROM sales_engine
                {where_clause}
                GROUP BY 1
                ORDER BY 1
            """
            rev_by_month = con.execute(monthly_sql, params).fetchdf()

            if rev_by_month.empty:
                st.warning("No data for the selected filters.")
            else:
                fig = px.line(
                    rev_by_month,
                    x="month",
                    y="revenue",
                    title="Monthly Revenue",
                    labels={"month": "Month", "revenue": "Revenue (BRL)"},
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

                # Top 15 categories by revenue (pure SQL, filtered)
                cat_sql = f"""
                    SELECT
                        COALESCE(product_category, 'Uncategorized') AS product_category,
                        SUM(price) AS revenue
                    FROM sales_engine
                    {where_clause}
                    GROUP BY 1
                    ORDER BY revenue DESC
                    LIMIT 15
                """
                top15 = con.execute(cat_sql, params).fetchdf()

                if not top15.empty:
                    fig_cat = px.bar(
                        top15,
                        x="product_category",
                        y="revenue",
                        title="Total Revenue by Category (Top 15)",
                        labels={"product_category": "Category", "revenue": "Revenue (BRL)"},
                    )
                    fig_cat.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_cat, use_container_width=True)

    elif page == "Logistics & Sentiment":
        st.header("Logistics & Sentiment")
        st.caption("Does delivering late lead to worse reviews?")
        # Date filter for logistics, driven by delivered date from the view
        date_bounds_log = con.execute(
            """
            SELECT
                MIN(delivery_date)::DATE AS min_date,
                MAX(delivery_date)::DATE AS max_date
            FROM logistics_engine
            """
        ).fetchone()

        if date_bounds_log is None or date_bounds_log[0] is None:
            st.warning("No logistics data available.")
            sentiment_df = None
        else:
            min_d_log, max_d_log = date_bounds_log

            st.sidebar.subheader("Logistics Filters")
            delivery_range = st.sidebar.slider(
                "Delivery date range",
                min_value=min_d_log,
                max_value=max_d_log,
                value=(min_d_log, max_d_log),
                format="YYYY-MM-DD",
            )

            start_deliv, end_deliv = delivery_range

            sentiment_sql = """
            SELECT
                delivery_time,
                COUNT(*) AS orders,
                ROUND(AVG(review_score), 2) AS avg_review_score
            FROM logistics_engine
            WHERE delivery_date BETWEEN ? AND ?
            GROUP BY delivery_time
            ORDER BY
                CASE delivery_time
                    WHEN 'Early' THEN 1
                    WHEN 'On time' THEN 2
                    WHEN 'Late 1-2 days' THEN 3
                    WHEN 'Late 3-7 days' THEN 4
                    ELSE 5
                END
            """
            sentiment_df = con.execute(sentiment_sql, [start_deliv, end_deliv]).fetchdf()

        if sentiment_df.empty:
            st.warning("No review data available.")
        else:
            fig = px.bar(
                sentiment_df,
                x="delivery_time",
                y="avg_review_score",
                title="Average Review Score by Delivery Performance",
                labels={"delivery_time": "Delivery", "avg_review_score": "Avg Review Score"},
                color="avg_review_score",
                color_continuous_scale="RdYlGn",
            )
            fig.update_layout(showlegend=False, xaxis_tickangle=-20)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(sentiment_df, use_container_width=True, hide_index=True)

    elif page == "Retention & Loyalty":
        st.header("Retention & Loyalty")
        st.caption("Which customers are most valuable, and how often do they come back?")

        # Date filter based on first_order_date from retention view
        clv_bounds = con.execute(
            """
            SELECT
                MIN(first_order_date)::DATE AS min_date,
                MAX(first_order_date)::DATE AS max_date
            FROM retention_engine
            """
        ).fetchone()

        if clv_bounds is None or clv_bounds[0] is None:
            st.warning("No retention data available.")
        else:
            min_clv, max_clv = clv_bounds

            st.sidebar.subheader("Retention Filters")
            clv_range = st.sidebar.slider(
                "First order date range",
                min_value=min_clv,
                max_value=max_clv,
                value=(min_clv, max_clv),
                format="YYYY-MM-DD",
            )
            start_clv, end_clv = clv_range

            # Base WHERE clause for retention charts
            clv_where = "WHERE first_order_date BETWEEN ? AND ?"
            clv_params = [start_clv, end_clv]

            # Chart 1: Total spent vs average days between orders (CLV vs repeat cadence)
            clv_sql = f"""
                SELECT
                    customer_unique_id,
                    total_spent,
                    total_orders,
                    avg_days_between_orders
                FROM retention_engine
                {clv_where}
            """
            clv_df = con.execute(clv_sql, clv_params).fetchdf()

            if clv_df.empty:
                st.warning("No customers match the selected retention filters.")
            else:
                # Global repeat rate (across all delivered customers)
                repeat_row = con.execute(
                    """
                    WITH first_orders AS (
                        SELECT
                            c.customer_unique_id,
                            MIN(DATE_TRUNC('DAY', o.order_purchase_timestamp)) AS first_order_date
                        FROM customers c
                        JOIN orders o
                            ON c.customer_id = o.customer_id
                        WHERE o.order_status = 'delivered'
                        GROUP BY c.customer_unique_id
                    ),
                    all_customers AS (
                        SELECT COUNT(*) AS cnt FROM first_orders
                    ),
                    repeat_customers AS (
                        SELECT COUNT(*) AS cnt FROM retention_engine
                    )
                    SELECT repeat_customers.cnt, all_customers.cnt
                    FROM repeat_customers, all_customers
                    """
                ).fetchone()

                repeat_customers_cnt, total_customers_cnt = repeat_row if repeat_row else (0, 0)
                repeat_rate_pct = (
                    repeat_customers_cnt * 100.0 / total_customers_cnt if total_customers_cnt else 0.0
                )

                # Average days between first and second purchase (global)
                first_second_row = con.execute(
                    """
                    WITH customer_orders AS (
                        SELECT
                            c.customer_unique_id,
                            DATE_TRUNC('DAY', o.order_purchase_timestamp) AS order_date
                        FROM customers c
                        JOIN orders o
                            ON c.customer_id = o.customer_id
                        WHERE o.order_status = 'delivered'
                    ),
                    first_two AS (
                        SELECT
                            customer_unique_id,
                            order_date,
                            ROW_NUMBER() OVER (
                                PARTITION BY customer_unique_id
                                ORDER BY order_date
                            ) AS rn
                        FROM customer_orders
                    ),
                    pairs AS (
                        SELECT
                            f1.customer_unique_id,
                            date_diff('DAY', f1.order_date, f2.order_date) AS days_between
                        FROM first_two f1
                        JOIN first_two f2
                            ON f1.customer_unique_id = f2.customer_unique_id
                           AND f1.rn = 1
                           AND f2.rn = 2
                    )
                    SELECT ROUND(AVG(days_between), 1) AS avg_days
                    FROM pairs
                    """
                ).fetchone()
                avg_first_second = first_second_row[0] if first_second_row and first_second_row[0] is not None else None

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Repeat rate", f"{repeat_rate_pct:.1f}%")
                    st.metric("Customers (repeat buyers in range)", len(clv_df))
                    st.metric("Median total spent", f"{clv_df['total_spent'].median():.2f}")

                with col2:
                    st.metric(
                        "Avg days between 1st & 2nd purchase",
                        f"{avg_first_second:.1f}" if avg_first_second is not None else "N/A",
                    )
                    st.metric("Median total orders", int(clv_df['total_orders'].median()))
                    st.metric("Median days between orders", f"{clv_df['avg_days_between_orders'].median():.1f}")

                scatter_fig = px.scatter(
                    clv_df,
                    x="avg_days_between_orders",
                    y="total_spent",
                    size="total_orders",
                    title="Customer Value vs Repeat Frequency",
                    labels={
                        "avg_days_between_orders": "Avg days between orders",
                        "total_spent": "Total spent (BRL)",
                        "total_orders": "Total orders",
                    },
                )
                scatter_fig.update_layout(xaxis_title="Avg days between orders", yaxis_title="Total spent (BRL)")
                st.plotly_chart(scatter_fig, use_container_width=True)

                # Chart 2: Distribution of total orders per repeat customer
                dist_sql = f"""
                    SELECT
                        total_orders,
                        COUNT(*) AS customers
                    FROM retention_engine
                    {clv_where}
                    GROUP BY total_orders
                    ORDER BY total_orders
                """
                dist_df = con.execute(dist_sql, clv_params).fetchdf()

                if not dist_df.empty:
                    dist_fig = px.bar(
                        dist_df,
                        x="total_orders",
                        y="customers",
                        title="Distribution of Total Orders per Customer",
                        labels={"total_orders": "Total orders", "customers": "Number of customers"},
                    )
                    st.plotly_chart(dist_fig, use_container_width=True)

                # Top Loyalists table
                top_loyal = clv_df.sort_values("total_spent", ascending=False).head(20)
                st.subheader("Top Loyal Customers (by Total Spent)")
                st.dataframe(
                    top_loyal[
                        ["customer_unique_id", "total_spent", "total_orders", "avg_days_between_orders"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

    else:  # Raw SQL Lab
        st.header("Raw SQL Lab")
        sql = st.text_area("SQL", height=120, placeholder="SELECT * FROM orders LIMIT 10")
        if st.button("Run"):
            if sql.strip():
                try:
                    result = con.execute(sql).fetchdf()
                    st.dataframe(result, use_container_width=True)
                except Exception as e:
                    st.error(str(e))
            else:
                st.warning("Enter a SQL query.")


if __name__ == "__main__":
    main()

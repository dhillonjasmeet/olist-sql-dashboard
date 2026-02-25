# Olist E‑commerce Analytics Dashboard (SQL‑First)

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

> Note: The CSVs themselves are not committed to this repository due to size. You can download them from Kaggle and place them in the `data/` folder.

---

## How to Run

```bash
# from the project root
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL that Streamlit prints (usually `http://localhost:8501`).
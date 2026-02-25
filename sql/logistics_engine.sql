-- View 2: Logistics & Sentiment Engine
-- Grain: one row per reviewed delivered order
-- days_late = delivered - estimated (positive = late). Buckets in SQL for clarity.

WITH base AS (
  SELECT
    o.order_id,
    CAST(o.order_delivered_customer_date AS TIMESTAMP)  AS delivered_ts,
    CAST(o.order_estimated_delivery_date AS TIMESTAMP)  AS estimated_ts,
    o_r.review_score
  FROM orders o
  JOIN order_reviews o_r
    ON o.order_id = o_r.order_id
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_estimated_delivery_date IS NOT NULL
    AND o_r.review_score IS NOT NULL
),
metrics AS (
  SELECT
    order_id,
    delivered_ts,
    estimated_ts,
    date_diff('day', estimated_ts, delivered_ts) AS days_late,
    review_score
  FROM base
)
SELECT
  CAST(delivered_ts AS DATE) AS delivery_date,
  days_late,
  CASE
    WHEN days_late <= -1 THEN 'Early'
    WHEN days_late = 0 THEN 'On time'
    WHEN days_late BETWEEN 1 AND 2 THEN 'Late 1-2 days'
    WHEN days_late BETWEEN 3 AND 7 THEN 'Late 3-7 days'
    ELSE 'Late 8+ days'
  END AS delivery_time,
  review_score
FROM metrics;

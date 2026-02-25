-- View 3: Retention & Loyalty Engine
-- Grain: one row per repeat customer (total_orders > 1)
-- Uses LAG for days_between orders; ORDER_PAYMENTS_AGG to avoid double-counting payments.

WITH ORDER_INTERVALS AS (
    SELECT 
        c.customer_unique_id,
        o.order_id,
        DATE_TRUNC('DAY', o.order_purchase_timestamp) AS order_purchase_date,
        o.order_status,
        LAG(DATE_TRUNC('DAY', o.order_purchase_timestamp)) OVER (
            PARTITION BY c.customer_unique_id
            ORDER BY DATE_TRUNC('DAY', o.order_purchase_timestamp)
        ) AS previous_order_date
    FROM customers AS c
    JOIN orders AS o
        ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
),

TIME_DIFFS AS (
    SELECT 
        customer_unique_id,
        date_diff('DAY', previous_order_date, order_purchase_date) AS days_between
    FROM ORDER_INTERVALS
    WHERE previous_order_date IS NOT NULL  
),

ORDER_PAYMENTS_AGG AS (
    SELECT
        op.order_id,
        SUM(op.payment_value) AS order_revenue
    FROM order_payments AS op
    GROUP BY op.order_id
)

SELECT 
    c.customer_unique_id, 
    MIN(DATE_TRUNC('DAY', o.order_purchase_timestamp)) AS first_order_date,
    MAX(DATE_TRUNC('DAY', o.order_purchase_timestamp)) AS last_order_date,
    date_diff(
        'DAY', 
        MIN(DATE_TRUNC('DAY', o.order_purchase_timestamp)),
        MAX(DATE_TRUNC('DAY', o.order_purchase_timestamp))
    ) AS tenure_days,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(opa.order_revenue) AS total_spent,
    ROUND(AVG(td.days_between), 1) AS avg_days_between_orders
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
JOIN ORDER_PAYMENTS_AGG AS opa
    ON o.order_id = opa.order_id
LEFT JOIN TIME_DIFFS AS td 
    ON c.customer_unique_id = td.customer_unique_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id
HAVING COUNT(DISTINCT o.order_id) > 1
ORDER BY total_spent DESC;

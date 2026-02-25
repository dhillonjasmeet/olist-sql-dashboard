-- View 1: Sales & Profit Engine
-- Grain: one row per order item line (order_id, product_id, price, category, state)
-- Used by: Executive Summary (monthly revenue, top categories by state/date filter)

WITH total_products AS (
    SELECT
        p.product_id,
        COALESCE(pc.product_category_name_english, p.product_category_name) AS product_category
    FROM products AS p
    LEFT JOIN product_category_name_translation AS pc
        ON p.product_category_name = pc.product_category_name
),

total_orders AS (
    SELECT
        o.order_id,
        date_trunc('day', CAST(o.order_purchase_timestamp AS TIMESTAMP)) AS purchase_date,
        oi.product_id,
        oi.price,
        c.customer_state
    FROM orders AS o
    LEFT JOIN order_items AS oi
        ON o.order_id = oi.order_id
    LEFT JOIN customers AS c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
)

SELECT
    t_o.order_id,
    t_o.purchase_date,
    t_o.product_id,
    t_p.product_category,
    t_o.price,
    t_o.customer_state
FROM total_orders AS t_o
LEFT JOIN total_products AS t_p
    ON t_o.product_id = t_p.product_id;

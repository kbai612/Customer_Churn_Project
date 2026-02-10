WITH transactions AS (
    SELECT * FROM {{ ref('stg_transactions') }}
)

SELECT
    transaction_id,
    customer_id,
    transaction_date,
    DAYOFWEEK(transaction_date) AS day_of_week,
    DAYNAME(transaction_date) AS day_name,
    MONTH(transaction_date) AS transaction_month,
    YEAR(transaction_date) AS transaction_year,
    DATE_TRUNC('month', transaction_date) AS transaction_month_date,
    product_category,
    quantity,
    unit_price,
    total_amount,
    payment_method
FROM transactions

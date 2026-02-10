WITH source AS (
    SELECT
        transaction_id,
        customer_id,
        transaction_date,
        product_category,
        quantity,
        unit_price,
        total_amount,
        payment_method
    FROM {{ source('churn_raw', 'transactions') }}
)

SELECT
    TRIM(transaction_id) AS transaction_id,
    TRIM(customer_id) AS customer_id,
    transaction_date::DATE AS transaction_date,
    TRIM(product_category) AS product_category,
    quantity,
    unit_price,
    total_amount,
    TRIM(payment_method) AS payment_method
FROM source
WHERE transaction_id IS NOT NULL
  AND customer_id IS NOT NULL
  AND transaction_date IS NOT NULL
  AND total_amount >= 0

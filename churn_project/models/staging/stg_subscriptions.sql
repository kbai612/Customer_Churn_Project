WITH source AS (
    SELECT
        customer_id,
        plan_type,
        monthly_charges,
        contract_type,
        last_payment_date,
        is_active
    FROM {{ source('churn_raw', 'subscriptions') }}
)

SELECT
    TRIM(customer_id) AS customer_id,
    TRIM(plan_type) AS plan_type,
    monthly_charges,
    TRIM(contract_type) AS contract_type,
    last_payment_date::DATE AS last_payment_date,
    is_active
FROM source
WHERE customer_id IS NOT NULL
  AND last_payment_date IS NOT NULL

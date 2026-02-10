-- Test to ensure churn_flag is only 0 or 1 across all churn-related models

SELECT
    customer_id,
    churn_flag
FROM {{ ref('fact_churn') }}
WHERE churn_flag NOT IN (0, 1)

UNION ALL

SELECT
    customer_id,
    churn_flag
FROM {{ ref('churn_features') }}
WHERE churn_flag NOT IN (0, 1)

{{ config(materialized='table') }}

WITH customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
),

transactions AS (
    SELECT * FROM {{ ref('fact_transactions') }}
),

customer_first_purchase AS (
    SELECT
        customer_id,
        MIN(transaction_date) AS first_purchase_date,
        DATE_TRUNC('month', MIN(transaction_date)) AS first_purchase_month
    FROM transactions
    GROUP BY customer_id
),

monthly_activity AS (
    SELECT DISTINCT
        t.customer_id,
        DATE_TRUNC('month', t.transaction_date) AS activity_month,
        cfp.first_purchase_month,
        DATEDIFF('month', cfp.first_purchase_month, DATE_TRUNC('month', t.transaction_date)) AS months_since_first_purchase
    FROM transactions t
    JOIN customer_first_purchase cfp ON t.customer_id = cfp.customer_id
),

cohort_size AS (
    SELECT
        first_purchase_month AS cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size
    FROM customer_first_purchase
    GROUP BY first_purchase_month
),

cohort_retention AS (
    SELECT
        ma.first_purchase_month AS cohort_month,
        ma.months_since_first_purchase AS month_number,
        COUNT(DISTINCT ma.customer_id) AS retained_customers
    FROM monthly_activity ma
    GROUP BY ma.first_purchase_month, ma.months_since_first_purchase
),

retention_rates AS (
    SELECT
        cr.cohort_month,
        cr.month_number,
        cr.retained_customers,
        cs.cohort_size,
        ROUND((cr.retained_customers::FLOAT / cs.cohort_size::FLOAT) * 100, 2) AS retention_rate_pct,
        CASE 
            WHEN cr.month_number > 0 
            THEN LAG(cr.retained_customers) OVER (
                PARTITION BY cr.cohort_month 
                ORDER BY cr.month_number
            )
            ELSE NULL
        END AS previous_month_retained,
        CASE 
            WHEN cr.month_number > 0 AND LAG(cr.retained_customers) OVER (
                PARTITION BY cr.cohort_month 
                ORDER BY cr.month_number
            ) > 0
            THEN ROUND(
                ((cr.retained_customers::FLOAT - LAG(cr.retained_customers) OVER (
                    PARTITION BY cr.cohort_month 
                    ORDER BY cr.month_number
                ))::FLOAT / LAG(cr.retained_customers) OVER (
                    PARTITION BY cr.cohort_month 
                    ORDER BY cr.month_number
                )::FLOAT) * 100, 
                2
            )
            ELSE NULL
        END AS churn_rate_mom_pct
    FROM cohort_retention cr
    JOIN cohort_size cs ON cr.cohort_month = cs.cohort_month
),

cohort_revenue AS (
    SELECT
        cfp.first_purchase_month AS cohort_month,
        SUM(t.total_amount) AS total_cohort_revenue,
        AVG(t.total_amount) AS avg_transaction_value,
        COUNT(DISTINCT t.transaction_id) AS total_transactions
    FROM transactions t
    JOIN customer_first_purchase cfp ON t.customer_id = cfp.customer_id
    GROUP BY cfp.first_purchase_month
),

final AS (
    SELECT
        rr.cohort_month,
        rr.month_number,
        rr.cohort_size,
        rr.retained_customers,
        rr.retention_rate_pct,
        rr.previous_month_retained,
        rr.churn_rate_mom_pct,
        cr.total_cohort_revenue,
        cr.avg_transaction_value,
        cr.total_transactions,
        ROUND(cr.total_cohort_revenue / rr.cohort_size, 2) AS revenue_per_customer,
        
        CASE
            WHEN rr.retention_rate_pct >= 80 THEN 'Excellent'
            WHEN rr.retention_rate_pct >= 60 THEN 'Good'
            WHEN rr.retention_rate_pct >= 40 THEN 'Fair'
            ELSE 'Poor'
        END AS retention_health,
        
        CASE
            WHEN rr.month_number = 0 THEN 'Month 0 (Acquisition)'
            WHEN rr.month_number <= 3 THEN 'Early Stage (1-3 months)'
            WHEN rr.month_number <= 6 THEN 'Growth Stage (4-6 months)'
            WHEN rr.month_number <= 12 THEN 'Maturity Stage (7-12 months)'
            ELSE 'Loyalty Stage (12+ months)'
        END AS lifecycle_stage
        
    FROM retention_rates rr
    LEFT JOIN cohort_revenue cr ON rr.cohort_month = cr.cohort_month
)

SELECT * FROM final
ORDER BY cohort_month DESC, month_number ASC

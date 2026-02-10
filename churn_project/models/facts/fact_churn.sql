WITH customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
),

transactions AS (
    SELECT * FROM {{ ref('fact_transactions') }}
),

customer_transactions AS (
    SELECT
        customer_id,
        COUNT(DISTINCT transaction_id) AS total_transactions,
        MAX(transaction_date) AS last_transaction_date,
        MIN(transaction_date) AS first_transaction_date,
        SUM(total_amount) AS total_spent,
        AVG(total_amount) AS avg_transaction_value
    FROM transactions
    GROUP BY customer_id
),

final AS (
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.age,
        c.age_group,
        c.gender,
        c.signup_date,
        c.cohort_month,
        c.tenure_months,
        c.tenure_days,
        c.city,
        c.state,
        c.segment,
        c.plan_type,
        c.monthly_charges,
        c.contract_type,
        c.last_payment_date,
        c.is_active,
        
        CASE 
            WHEN c.last_payment_date < DATEADD('day', -{{ var('churn_threshold_days') }}, CURRENT_DATE()) 
            THEN 1 
            ELSE 0 
        END AS churn_flag,
        
        COALESCE(ct.total_transactions, 0) AS total_transactions,
        ct.last_transaction_date,
        ct.first_transaction_date,
        COALESCE(ct.total_spent, 0) AS monetary,
        COALESCE(ct.avg_transaction_value, 0) AS avg_transaction_value,
        
        DATEDIFF('day', ct.last_transaction_date, CURRENT_DATE()) AS recency_days,
        COALESCE(ct.total_transactions, 0) AS frequency,
        
        DATEDIFF('day', ct.last_transaction_date, CURRENT_DATE()) AS days_since_last_transaction
        
    FROM customers c
    LEFT JOIN customer_transactions ct ON c.customer_id = ct.customer_id
)

SELECT * FROM final

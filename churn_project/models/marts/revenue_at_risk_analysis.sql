{{ config(materialized='table') }}

WITH churn_features AS (
    SELECT * FROM {{ ref('churn_features') }}
),

transactions AS (
    SELECT * FROM {{ ref('fact_transactions') }}
),

customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS total_historical_revenue,
        AVG(total_amount) AS avg_transaction_value,
        COUNT(DISTINCT transaction_id) AS total_transactions,
        MAX(transaction_date) AS last_transaction_date,
        MIN(transaction_date) AS first_transaction_date,
        DATEDIFF('month', MIN(transaction_date), MAX(transaction_date)) + 1 AS revenue_generating_months,
        
        SUM(CASE WHEN transaction_date >= DATEADD('month', -3, CURRENT_DATE()) THEN total_amount ELSE 0 END) AS revenue_last_3_months,
        SUM(CASE WHEN transaction_date >= DATEADD('month', -6, CURRENT_DATE()) THEN total_amount ELSE 0 END) AS revenue_last_6_months,
        SUM(CASE WHEN transaction_date >= DATEADD('year', -1, CURRENT_DATE()) THEN total_amount ELSE 0 END) AS revenue_last_12_months
    FROM transactions
    GROUP BY customer_id
),

final AS (
    SELECT
        cf.customer_id,
        cf.first_name,
        cf.last_name,
        cf.email,
        cf.segment,
        cf.contract_type,
        cf.plan_type,
        cf.monthly_charges,
        cf.tenure_months,
        cf.churn_flag,
        cf.churn_risk_score,
        cf.risk_category,
        cf.rfm_segment,
        cf.engagement_segment,
        cf.estimated_lifetime_value,
        cf.revenue_at_risk,
        cf.annualized_subscription_value,
        cf.retention_probability,
        cf.cohort_month,
        cf.acquisition_channel,
        
        cr.total_historical_revenue,
        cr.avg_transaction_value,
        cr.total_transactions,
        cr.revenue_generating_months,
        cr.revenue_last_3_months,
        cr.revenue_last_6_months,
        cr.revenue_last_12_months,
        
        CASE 
            WHEN cr.revenue_generating_months > 0 
            THEN ROUND(cr.total_historical_revenue / cr.revenue_generating_months, 2)
            ELSE 0
        END AS avg_monthly_revenue,
        
        ROUND(cf.annualized_subscription_value + COALESCE(cr.revenue_last_12_months, 0), 2) AS total_annual_value,
        
        CASE
            WHEN cf.churn_flag = 1 THEN cr.total_historical_revenue
            ELSE 0
        END AS realized_churn_loss,
        
        CASE
            WHEN cf.churn_flag = 0 AND cf.churn_risk_score >= 70 
            THEN cf.annualized_subscription_value + COALESCE(cr.revenue_last_12_months, 0)
            WHEN cf.churn_flag = 0 AND cf.churn_risk_score >= 50 
            THEN (cf.annualized_subscription_value + COALESCE(cr.revenue_last_12_months, 0)) * 0.6
            WHEN cf.churn_flag = 0 AND cf.churn_risk_score >= 30 
            THEN (cf.annualized_subscription_value + COALESCE(cr.revenue_last_12_months, 0)) * 0.3
            ELSE 0
        END AS potential_revenue_loss,
        
        CASE
            WHEN cf.estimated_lifetime_value > 1000 THEN 'High Value'
            WHEN cf.estimated_lifetime_value > 500 THEN 'Medium Value'
            WHEN cf.estimated_lifetime_value > 100 THEN 'Low Value'
            ELSE 'Minimal Value'
        END AS customer_value_tier,
        
        CASE
            WHEN cf.churn_risk_score >= 70 AND cf.estimated_lifetime_value > 500 THEN 1
            ELSE 0
        END AS priority_retention_flag,
        
        CASE
            WHEN cf.churn_flag = 0 AND cf.churn_risk_score < 50 AND cr.revenue_last_3_months > cr.revenue_last_6_months 
            THEN 'Growing'
            WHEN cf.churn_flag = 0 AND cf.churn_risk_score < 50 
            THEN 'Stable'
            WHEN cf.churn_flag = 0 AND cf.churn_risk_score >= 50 
            THEN 'Declining'
            ELSE 'Churned'
        END AS revenue_trend,
        
        ROUND(
            CASE
                WHEN cf.churn_risk_score >= 80 THEN 250
                WHEN cf.churn_risk_score >= 70 THEN 150
                WHEN cf.churn_risk_score >= 60 THEN 100
                WHEN cf.churn_risk_score >= 50 THEN 50
                ELSE 25
            END, 
            2
        ) AS estimated_retention_cost,
        
        ROUND(
            (cf.revenue_at_risk - 
            CASE
                WHEN cf.churn_risk_score >= 80 THEN 250
                WHEN cf.churn_risk_score >= 70 THEN 150
                WHEN cf.churn_risk_score >= 60 THEN 100
                WHEN cf.churn_risk_score >= 50 THEN 50
                ELSE 25
            END) * cf.retention_probability,
            2
        ) AS expected_retention_roi
        
    FROM churn_features cf
    LEFT JOIN customer_revenue cr ON cf.customer_id = cr.customer_id
)

SELECT * FROM final
ORDER BY potential_revenue_loss DESC, churn_risk_score DESC

WITH churn_data AS (
    SELECT * FROM {{ ref('fact_churn') }}
),

rfm_scores AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        age,
        age_group,
        gender,
        signup_date,
        cohort_month,
        tenure_months,
        tenure_days,
        city,
        state,
        segment,
        plan_type,
        monthly_charges,
        contract_type,
        last_payment_date,
        is_active,
        churn_flag,
        recency_days,
        frequency,
        monetary,
        total_transactions,
        last_transaction_date,
        avg_transaction_value,
        days_since_last_transaction,
        
        NTILE(5) OVER (ORDER BY recency_days DESC) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS monetary_score
        
    FROM churn_data
),

segmented AS (
    SELECT
        *,
        {{ rfm_segment('recency_score', 'frequency_score', 'monetary_score') }} AS rfm_segment,
        
        (recency_score * 0.4) + (frequency_score * 0.3) + (monetary_score * 0.3) AS rfm_composite_score,
        
        CASE
            WHEN churn_flag = 1 THEN 100
            WHEN recency_days > 60 AND frequency < 3 THEN 85
            WHEN recency_days > 45 AND contract_type = 'Month-to-month' THEN 75
            WHEN recency_days > 30 AND monetary < 100 THEN 65
            WHEN contract_type = 'Month-to-month' AND tenure_months < 6 THEN 60
            WHEN recency_days > 20 THEN 50
            WHEN frequency < 2 AND tenure_months < 3 THEN 45
            ELSE 30
        END AS churn_risk_score
        
    FROM rfm_scores
),

final AS (
    SELECT
        *,
        CASE
            WHEN churn_flag = 1 THEN 'Already Churned - Win-back Campaign'
            WHEN churn_risk_score >= 85 THEN 'Urgent: Personalized Retention Call + 30% Discount'
            WHEN churn_risk_score >= 75 THEN 'High Priority: Loyalty Reward + Upgrade Offer'
            WHEN churn_risk_score >= 65 THEN 'Send Re-engagement Email + Special Promotion'
            WHEN churn_risk_score >= 50 THEN 'Monitor Closely + Survey for Feedback'
            WHEN rfm_segment = 'Champions' THEN 'VIP Treatment + Exclusive Benefits'
            WHEN rfm_segment = 'Loyal Customers' THEN 'Thank You Message + Referral Bonus'
            WHEN rfm_segment IN ('New Customers', 'Promising') THEN 'Onboarding Support + Product Education'
            ELSE 'Standard Communication'
        END AS recommended_action,
        
        CASE
            WHEN monetary > 1000 AND frequency > 10 THEN monetary * 0.15
            WHEN monetary > 500 AND frequency > 5 THEN monetary * 0.10
            WHEN monetary > 100 THEN monetary * 0.05
            ELSE 50
        END AS estimated_lifetime_value
        
    FROM segmented
)

SELECT * FROM final

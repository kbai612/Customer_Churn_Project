WITH churn_data AS (
    SELECT * FROM {{ ref('fact_churn') }}
),

behavioral_metrics AS (
    SELECT * FROM {{ ref('fact_behavioral_metrics') }}
),

customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
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

enriched_data AS (
    SELECT
        r.*,
        b.total_events,
        b.active_days,
        b.login_count,
        b.feature_usage_count,
        b.support_ticket_count,
        b.app_crash_count,
        b.last_event_date,
        b.engagement_rate,
        b.avg_events_per_active_day,
        b.avg_session_duration_minutes,
        b.days_since_last_event,
        b.events_last_7_days,
        b.events_last_30_days,
        b.logins_last_30_days,
        b.feature_usage_last_30_days,
        b.days_since_last_login,
        b.features_per_login,
        b.problem_event_rate_pct,
        c.acquisition_channel,
        c.device_type,
        c.initial_referral_credits
    FROM rfm_scores r
    LEFT JOIN behavioral_metrics b ON r.customer_id = b.customer_id
    LEFT JOIN customers c ON r.customer_id = c.customer_id
),

engagement_scores AS (
    SELECT
        *,
        
        CASE
            WHEN days_since_last_event IS NULL THEN 0
            WHEN days_since_last_event <= 3 THEN 5
            WHEN days_since_last_event <= 7 THEN 4
            WHEN days_since_last_event <= 14 THEN 3
            WHEN days_since_last_event <= 30 THEN 2
            ELSE 1
        END AS engagement_recency_score,
        
        CASE
            WHEN logins_last_30_days IS NULL THEN 0
            WHEN logins_last_30_days >= 15 THEN 5
            WHEN logins_last_30_days >= 10 THEN 4
            WHEN logins_last_30_days >= 5 THEN 3
            WHEN logins_last_30_days >= 2 THEN 2
            ELSE 1
        END AS engagement_frequency_score,
        
        CASE
            WHEN feature_usage_last_30_days IS NULL THEN 0
            WHEN feature_usage_last_30_days >= 20 THEN 5
            WHEN feature_usage_last_30_days >= 10 THEN 4
            WHEN feature_usage_last_30_days >= 5 THEN 3
            WHEN feature_usage_last_30_days >= 2 THEN 2
            ELSE 1
        END AS feature_adoption_score
        
    FROM enriched_data
),

segmented AS (
    SELECT
        *,
        {{ rfm_segment('recency_score', 'frequency_score', 'monetary_score') }} AS rfm_segment,
        
        (recency_score * 0.4) + (frequency_score * 0.3) + (monetary_score * 0.3) AS rfm_composite_score,
        
        (engagement_recency_score + engagement_frequency_score + feature_adoption_score) / 3.0 AS engagement_composite_score,
        
        CASE
            WHEN churn_flag = 1 THEN 100
            WHEN days_since_last_event > 60 AND engagement_recency_score <= 2 THEN 95
            WHEN recency_days > 60 AND frequency < 3 AND logins_last_30_days < 2 THEN 90
            WHEN support_ticket_count > 3 AND problem_event_rate_pct > 5 THEN 85
            WHEN recency_days > 45 AND contract_type = 'Month-to-month' AND engagement_frequency_score <= 2 THEN 80
            WHEN days_since_last_login > 30 AND feature_adoption_score <= 2 THEN 75
            WHEN recency_days > 30 AND monetary < 100 AND engagement_composite_score < 2.5 THEN 70
            WHEN contract_type = 'Month-to-month' AND tenure_months < 6 AND logins_last_30_days < 5 THEN 65
            WHEN feature_usage_count < 3 AND tenure_months >= 3 THEN 60
            WHEN recency_days > 20 AND engagement_recency_score <= 3 THEN 55
            WHEN frequency < 2 AND tenure_months < 3 THEN 50
            WHEN engagement_composite_score < 2 THEN 45
            ELSE 30
        END AS churn_risk_score,
        
        CASE
            WHEN engagement_composite_score >= 4 THEN 'Highly Engaged'
            WHEN engagement_composite_score >= 3 THEN 'Moderately Engaged'
            WHEN engagement_composite_score >= 2 THEN 'Lightly Engaged'
            WHEN engagement_composite_score > 0 THEN 'Barely Engaged'
            ELSE 'No Engagement Data'
        END AS engagement_segment
        
    FROM engagement_scores
),

with_ltv AS (
    SELECT
        *,
        
        CASE
            WHEN churn_flag = 1 THEN 'Already Churned - Win-back Campaign'
            WHEN churn_risk_score >= 90 THEN 'Critical: Executive Outreach + Custom Retention Package'
            WHEN churn_risk_score >= 80 THEN 'Urgent: Personalized Retention Call + 30% Discount'
            WHEN churn_risk_score >= 70 THEN 'High Priority: Loyalty Reward + Upgrade Offer'
            WHEN churn_risk_score >= 60 THEN 'Send Re-engagement Email + Special Promotion'
            WHEN churn_risk_score >= 50 THEN 'Monitor Closely + Survey for Feedback'
            WHEN engagement_segment = 'Barely Engaged' OR engagement_segment = 'No Engagement Data' 
                THEN 'Product Education + Feature Training'
            WHEN rfm_segment = 'Champions' THEN 'VIP Treatment + Exclusive Benefits'
            WHEN rfm_segment = 'Loyal Customers' THEN 'Thank You Message + Referral Bonus'
            WHEN rfm_segment IN ('New Customers', 'Promising') THEN 'Onboarding Support + Product Education'
            ELSE 'Standard Communication'
        END AS recommended_action,
        
        CASE
            WHEN monetary > 1000 AND frequency > 10 AND engagement_composite_score >= 3 THEN monetary * 0.20
            WHEN monetary > 1000 AND frequency > 10 THEN monetary * 0.15
            WHEN monetary > 500 AND frequency > 5 AND engagement_composite_score >= 3 THEN monetary * 0.12
            WHEN monetary > 500 AND frequency > 5 THEN monetary * 0.10
            WHEN monetary > 200 AND engagement_composite_score >= 3 THEN monetary * 0.08
            WHEN monetary > 100 THEN monetary * 0.05
            WHEN engagement_composite_score >= 3 THEN 75
            ELSE 50
        END AS estimated_lifetime_value,
        
        monthly_charges * 12 AS annualized_subscription_value,
        
        CASE
            WHEN contract_type = 'Two year' THEN 0.85
            WHEN contract_type = 'One year' THEN 0.70
            ELSE 0.50
        END AS retention_probability
        
    FROM segmented
),

final AS (
    SELECT
        *,
        
        CASE
            WHEN churn_risk_score >= 80 THEN estimated_lifetime_value * 0.90
            WHEN churn_risk_score >= 70 THEN estimated_lifetime_value * 0.75
            WHEN churn_risk_score >= 60 THEN estimated_lifetime_value * 0.60
            WHEN churn_risk_score >= 50 THEN estimated_lifetime_value * 0.40
            ELSE estimated_lifetime_value * 0.20
        END AS revenue_at_risk,
        
        CASE
            WHEN churn_flag = 1 THEN 'Churned'
            WHEN churn_risk_score >= 70 THEN 'High Risk'
            WHEN churn_risk_score >= 50 THEN 'Medium Risk'
            ELSE 'Low Risk'
        END AS risk_category
        
    FROM with_ltv
)

SELECT * FROM final

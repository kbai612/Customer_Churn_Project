WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

subscriptions AS (
    SELECT * FROM {{ ref('stg_subscriptions') }}
),

joined AS (
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.age,
        c.gender,
        c.signup_date,
        c.city,
        c.state,
        c.segment,
        c.acquisition_channel,
        c.device_type,
        c.timezone,
        c.preferred_language,
        c.customer_lifetime_days,
        c.initial_referral_credits,
        s.plan_type,
        s.monthly_charges,
        s.contract_type,
        s.last_payment_date,
        s.is_active
    FROM customers c
    LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
)

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    age,
    CASE
        WHEN age BETWEEN 18 AND 25 THEN '18-25'
        WHEN age BETWEEN 26 AND 35 THEN '26-35'
        WHEN age BETWEEN 36 AND 45 THEN '36-45'
        WHEN age BETWEEN 46 AND 55 THEN '46-55'
        ELSE '56+'
    END AS age_group,
    gender,
    signup_date,
    DATE_TRUNC('month', signup_date) AS cohort_month,
    DATEDIFF('month', signup_date, CURRENT_DATE()) AS tenure_months,
    DATEDIFF('day', signup_date, CURRENT_DATE()) AS tenure_days,
    city,
    state,
    segment,
    acquisition_channel,
    device_type,
    timezone,
    preferred_language,
    customer_lifetime_days,
    initial_referral_credits,
    plan_type,
    monthly_charges,
    contract_type,
    last_payment_date,
    is_active
FROM joined

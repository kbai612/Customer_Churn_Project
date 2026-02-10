{{ config(materialized='table') }}

WITH behavioral_events AS (
    SELECT * FROM {{ ref('stg_behavioral_events') }}
),

customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
),

customer_funnel_events AS (
    SELECT
        be.customer_id,
        MIN(CASE WHEN be.event_type = 'login' THEN be.event_date END) AS first_login_date,
        MIN(CASE WHEN be.event_type = 'feature_browse' THEN be.event_date END) AS first_browse_date,
        MIN(CASE WHEN be.event_type = 'feature_search' THEN be.event_date END) AS first_search_date,
        MIN(CASE WHEN be.event_type = 'feature_wishlist' THEN be.event_date END) AS first_wishlist_date,
        MIN(CASE WHEN be.event_type = 'feature_checkout' THEN be.event_date END) AS first_checkout_date,
        
        COUNT(DISTINCT CASE WHEN be.event_type = 'login' THEN be.event_id END) AS total_logins,
        COUNT(DISTINCT CASE WHEN be.event_type = 'feature_browse' THEN be.event_id END) AS total_browse,
        COUNT(DISTINCT CASE WHEN be.event_type = 'feature_search' THEN be.event_id END) AS total_search,
        COUNT(DISTINCT CASE WHEN be.event_type = 'feature_wishlist' THEN be.event_id END) AS total_wishlist,
        COUNT(DISTINCT CASE WHEN be.event_type = 'feature_checkout' THEN be.event_id END) AS total_checkout
    FROM behavioral_events be
    GROUP BY be.customer_id
),

funnel_progression AS (
    SELECT
        c.customer_id,
        c.signup_date,
        c.cohort_month,
        c.segment,
        c.acquisition_channel,
        c.device_type,
        c.churn_flag,
        
        cfe.first_login_date,
        cfe.first_browse_date,
        cfe.first_search_date,
        cfe.first_wishlist_date,
        cfe.first_checkout_date,
        
        CASE WHEN cfe.first_login_date IS NOT NULL THEN 1 ELSE 0 END AS reached_login,
        CASE WHEN cfe.first_browse_date IS NOT NULL THEN 1 ELSE 0 END AS reached_browse,
        CASE WHEN cfe.first_search_date IS NOT NULL THEN 1 ELSE 0 END AS reached_search,
        CASE WHEN cfe.first_wishlist_date IS NOT NULL THEN 1 ELSE 0 END AS reached_wishlist,
        CASE WHEN cfe.first_checkout_date IS NOT NULL THEN 1 ELSE 0 END AS reached_checkout,
        
        DATEDIFF('day', c.signup_date, cfe.first_login_date) AS days_to_first_login,
        DATEDIFF('day', c.signup_date, cfe.first_browse_date) AS days_to_first_browse,
        DATEDIFF('day', c.signup_date, cfe.first_search_date) AS days_to_first_search,
        DATEDIFF('day', c.signup_date, cfe.first_checkout_date) AS days_to_first_checkout,
        
        cfe.total_logins,
        cfe.total_browse,
        cfe.total_search,
        cfe.total_wishlist,
        cfe.total_checkout,
        
        CASE
            WHEN cfe.first_checkout_date IS NOT NULL THEN 'Checkout'
            WHEN cfe.first_wishlist_date IS NOT NULL THEN 'Wishlist'
            WHEN cfe.first_search_date IS NOT NULL THEN 'Search'
            WHEN cfe.first_browse_date IS NOT NULL THEN 'Browse'
            WHEN cfe.first_login_date IS NOT NULL THEN 'Login'
            ELSE 'No Activity'
        END AS funnel_stage_reached,
        
        CASE
            WHEN cfe.first_login_date IS NULL THEN 'Signup_Abandonment'
            WHEN cfe.first_browse_date IS NULL THEN 'Login_Abandonment'
            WHEN cfe.first_search_date IS NULL THEN 'Browse_Abandonment'
            WHEN cfe.first_checkout_date IS NULL THEN 'Search_Abandonment'
            ELSE 'Completed_Funnel'
        END AS abandonment_stage
        
    FROM customers c
    LEFT JOIN customer_funnel_events cfe ON c.customer_id = cfe.customer_id
),

feature_adoption AS (
    SELECT
        customer_id,
        COUNT(DISTINCT event_type) AS unique_features_used,
        
        CASE
            WHEN COUNT(DISTINCT CASE WHEN event_type LIKE 'feature_%' THEN event_type END) >= 5 THEN 'Power User'
            WHEN COUNT(DISTINCT CASE WHEN event_type LIKE 'feature_%' THEN event_type END) >= 3 THEN 'Active User'
            WHEN COUNT(DISTINCT CASE WHEN event_type LIKE 'feature_%' THEN event_type END) >= 1 THEN 'Casual User'
            ELSE 'Non-Feature User'
        END AS feature_adoption_segment
        
    FROM behavioral_events
    GROUP BY customer_id
),

final AS (
    SELECT
        fp.*,
        fa.unique_features_used,
        fa.feature_adoption_segment,
        
        CASE
            WHEN fp.reached_checkout = 1 AND fp.days_to_first_checkout <= 7 THEN 'Fast Converter'
            WHEN fp.reached_checkout = 1 AND fp.days_to_first_checkout <= 30 THEN 'Standard Converter'
            WHEN fp.reached_checkout = 1 THEN 'Slow Converter'
            ELSE 'Non-Converter'
        END AS conversion_velocity,
        
        CASE
            WHEN fp.total_logins >= 20 AND fp.total_checkout >= 5 THEN 'Highly Active'
            WHEN fp.total_logins >= 10 AND fp.total_checkout >= 2 THEN 'Moderately Active'
            WHEN fp.total_logins >= 3 THEN 'Lightly Active'
            ELSE 'Inactive'
        END AS activity_level
        
    FROM funnel_progression fp
    LEFT JOIN feature_adoption fa ON fp.customer_id = fa.customer_id
)

SELECT * FROM final

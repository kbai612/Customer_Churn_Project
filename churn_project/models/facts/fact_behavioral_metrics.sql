{{ config(materialized='table') }}

WITH behavioral_events AS (
    SELECT * FROM {{ ref('stg_behavioral_events') }}
),

customer_engagement AS (
    SELECT
        customer_id,
        COUNT(DISTINCT event_id) AS total_events,
        COUNT(DISTINCT event_date) AS active_days,
        COUNT(DISTINCT CASE WHEN event_type = 'login' THEN event_id END) AS login_count,
        COUNT(DISTINCT CASE WHEN event_type LIKE 'feature_%' THEN event_id END) AS feature_usage_count,
        COUNT(DISTINCT CASE WHEN event_type = 'support_ticket' THEN event_id END) AS support_ticket_count,
        COUNT(DISTINCT CASE WHEN event_type = 'app_crash' THEN event_id END) AS app_crash_count,
        
        MAX(event_date) AS last_event_date,
        MIN(event_date) AS first_event_date,
        DATEDIFF('day', MIN(event_date), MAX(event_date)) + 1 AS engagement_span_days,
        
        AVG(CASE WHEN session_duration_minutes IS NOT NULL THEN session_duration_minutes END) AS avg_session_duration_minutes,
        SUM(CASE WHEN session_duration_minutes IS NOT NULL THEN session_duration_minutes END) AS total_session_duration_minutes,
        AVG(CASE WHEN pages_viewed IS NOT NULL THEN pages_viewed END) AS avg_pages_per_session,
        SUM(CASE WHEN pages_viewed IS NOT NULL THEN pages_viewed END) AS total_pages_viewed
    FROM behavioral_events
    GROUP BY customer_id
),

time_based_metrics AS (
    SELECT
        customer_id,
        
        COUNT(DISTINCT CASE 
            WHEN event_date >= DATEADD('day', -7, CURRENT_DATE()) THEN event_id 
        END) AS events_last_7_days,
        
        COUNT(DISTINCT CASE 
            WHEN event_date >= DATEADD('day', -30, CURRENT_DATE()) THEN event_id 
        END) AS events_last_30_days,
        
        COUNT(DISTINCT CASE 
            WHEN event_date >= DATEADD('day', -90, CURRENT_DATE()) THEN event_id 
        END) AS events_last_90_days,
        
        COUNT(DISTINCT CASE 
            WHEN event_type = 'login' AND event_date >= DATEADD('day', -30, CURRENT_DATE()) THEN event_id 
        END) AS logins_last_30_days,
        
        COUNT(DISTINCT CASE 
            WHEN event_type LIKE 'feature_%' AND event_date >= DATEADD('day', -30, CURRENT_DATE()) THEN event_id 
        END) AS feature_usage_last_30_days,
        
        MAX(CASE WHEN event_type = 'login' THEN event_date END) AS last_login_date,
        MAX(CASE WHEN event_type LIKE 'feature_%' THEN event_date END) AS last_feature_usage_date
        
    FROM behavioral_events
    GROUP BY customer_id
),

final AS (
    SELECT
        ce.customer_id,
        ce.total_events,
        ce.active_days,
        ce.login_count,
        ce.feature_usage_count,
        ce.support_ticket_count,
        ce.app_crash_count,
        ce.last_event_date,
        ce.first_event_date,
        ce.engagement_span_days,
        
        CASE 
            WHEN ce.engagement_span_days > 0 
            THEN ROUND(ce.active_days::FLOAT / ce.engagement_span_days::FLOAT, 4)
            ELSE 0
        END AS engagement_rate,
        
        CASE 
            WHEN ce.active_days > 0 
            THEN ROUND(ce.total_events::FLOAT / ce.active_days::FLOAT, 2)
            ELSE 0
        END AS avg_events_per_active_day,
        
        ce.avg_session_duration_minutes,
        ce.total_session_duration_minutes,
        ce.avg_pages_per_session,
        ce.total_pages_viewed,
        
        DATEDIFF('day', ce.last_event_date, CURRENT_DATE()) AS days_since_last_event,
        
        tm.events_last_7_days,
        tm.events_last_30_days,
        tm.events_last_90_days,
        tm.logins_last_30_days,
        tm.feature_usage_last_30_days,
        tm.last_login_date,
        tm.last_feature_usage_date,
        
        DATEDIFF('day', tm.last_login_date, CURRENT_DATE()) AS days_since_last_login,
        
        CASE
            WHEN ce.login_count > 0 
            THEN ROUND(ce.feature_usage_count::FLOAT / ce.login_count::FLOAT, 2)
            ELSE 0
        END AS features_per_login,
        
        CASE
            WHEN ce.total_events > 0 
            THEN ROUND((ce.support_ticket_count + ce.app_crash_count)::FLOAT / ce.total_events::FLOAT * 100, 2)
            ELSE 0
        END AS problem_event_rate_pct
        
    FROM customer_engagement ce
    LEFT JOIN time_based_metrics tm ON ce.customer_id = tm.customer_id
)

SELECT * FROM final

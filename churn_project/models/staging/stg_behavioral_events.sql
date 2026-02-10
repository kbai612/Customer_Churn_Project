WITH source AS (
    SELECT
        event_id,
        customer_id,
        event_date,
        event_type,
        device_type,
        session_duration_minutes,
        pages_viewed
    FROM {{ source('churn_raw', 'behavioral_events') }}
)

SELECT
    TRIM(event_id) AS event_id,
    TRIM(customer_id) AS customer_id,
    event_date::DATE AS event_date,
    TRIM(event_type) AS event_type,
    TRIM(device_type) AS device_type,
    session_duration_minutes,
    pages_viewed
FROM source
WHERE event_id IS NOT NULL
    AND customer_id IS NOT NULL

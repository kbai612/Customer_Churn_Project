WITH source AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        age,
        gender,
        signup_date,
        city,
        state,
        segment
    FROM {{ source('churn_raw', 'customers') }}
)

SELECT
    TRIM(customer_id) AS customer_id,
    TRIM(first_name) AS first_name,
    TRIM(last_name) AS last_name,
    LOWER(TRIM(email)) AS email,
    age,
    TRIM(gender) AS gender,
    signup_date::DATE AS signup_date,
    TRIM(city) AS city,
    TRIM(state) AS state,
    TRIM(segment) AS segment
FROM source
WHERE customer_id IS NOT NULL

{% macro rfm_segment(recency_score, frequency_score, monetary_score) %}
    CASE
        WHEN {{ recency_score }} >= 4 AND {{ frequency_score }} >= 4 AND {{ monetary_score }} >= 4 THEN 'Champions'
        WHEN {{ recency_score }} >= 3 AND {{ frequency_score }} >= 4 AND {{ monetary_score }} >= 4 THEN 'Loyal Customers'
        WHEN {{ recency_score }} >= 4 AND {{ frequency_score }} <= 2 AND {{ monetary_score }} <= 2 THEN 'New Customers'
        WHEN {{ recency_score }} >= 3 AND {{ frequency_score }} >= 3 AND {{ monetary_score }} >= 3 THEN 'Potential Loyalists'
        WHEN {{ recency_score }} >= 3 AND {{ frequency_score }} <= 3 AND {{ monetary_score }} <= 3 THEN 'Promising'
        WHEN {{ recency_score }} <= 2 AND {{ frequency_score }} >= 3 AND {{ monetary_score }} >= 3 THEN 'At Risk'
        WHEN {{ recency_score }} <= 2 AND {{ frequency_score }} >= 4 AND {{ monetary_score }} >= 4 THEN 'Cant Lose Them'
        WHEN {{ recency_score }} <= 1 AND {{ frequency_score }} >= 4 AND {{ monetary_score }} >= 4 THEN 'Lost High Value'
        WHEN {{ recency_score }} >= 3 AND {{ frequency_score }} <= 2 AND {{ monetary_score }} <= 2 THEN 'Need Attention'
        WHEN {{ recency_score }} <= 2 AND {{ frequency_score }} <= 2 AND {{ monetary_score }} <= 2 THEN 'Hibernating'
        WHEN {{ recency_score }} <= 1 AND {{ frequency_score }} <= 2 AND {{ monetary_score }} <= 2 THEN 'Lost'
        ELSE 'Other'
    END
{% endmacro %}

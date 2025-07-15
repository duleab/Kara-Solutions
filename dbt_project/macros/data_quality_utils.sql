-- Basic utility macro for data quality flags
{% macro add_data_quality_flags() %}
    CASE 
        WHEN message_text IS NULL OR LENGTH(TRIM(message_text)) = 0 THEN true
        ELSE false
    END as has_empty_content,
    
    CASE 
        WHEN created_at > CURRENT_TIMESTAMP THEN true
        WHEN created_at < '2020-01-01' THEN true
        ELSE false
    END as has_invalid_date
{% endmacro %}

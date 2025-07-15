-- Incremental model template
-- Copy this template to create incremental versions of your large tables

{{
    config(
        materialized='incremental',
        unique_key='id',
        on_schema_change='fail'
    )
}}

SELECT 
    id,
    -- Add your columns here
    created_at,
    updated_at
FROM {{ source('your_source', 'your_table') }}

{% if is_incremental() %}
    -- Only process new or updated records
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
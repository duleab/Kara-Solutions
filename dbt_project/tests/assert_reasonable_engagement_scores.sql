-- Custom test: Check for reasonable engagement scores
SELECT *
FROM {{ ref('fact_message_analytics') }}
WHERE engagement_score < 0 
   OR engagement_score > 100

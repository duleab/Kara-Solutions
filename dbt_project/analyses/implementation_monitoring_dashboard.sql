-- Implementation Monitoring Dashboard
-- This analysis provides real-time monitoring of system health and implementation progress
-- Run this regularly to track the success of your advanced enhancements

-- =============================================================================
-- SECTION 1: DATA QUALITY MONITORING
-- =============================================================================

WITH data_quality_metrics AS (
    SELECT 
        'telegram_messages' as table_name,
        COUNT(*) as total_records,
        COUNT(CASE WHEN text IS NOT NULL THEN 1 END) as non_null_messages,
        COUNT(CASE WHEN LENGTH(text) > 0 THEN 1 END) as non_empty_messages,
        COUNT(CASE WHEN date > {{ dbt.dateadd('day', -7, dbt.current_timestamp()) }} THEN 1 END) as recent_records,
         MAX(date) as latest_record_date,
         MIN(date) as earliest_record_date
     FROM {{ source('telegram_data', 'telegram_messages') }}
    
    UNION ALL
    
    SELECT 
        'telegram_channels' as table_name,
        COUNT(*) as total_records,
        COUNT(CASE WHEN title IS NOT NULL THEN 1 END) as non_null_messages,
        COUNT(CASE WHEN LENGTH(title) > 0 THEN 1 END) as non_empty_messages,
        COUNT(CASE WHEN scraped_at > {{ dbt.dateadd('day', -7, dbt.current_timestamp()) }} THEN 1 END) as recent_records,
        MAX(scraped_at) as latest_record_date,
        MIN(scraped_at) as earliest_record_date
    FROM {{ source('telegram_data', 'telegram_channels') }}
    
    UNION ALL
    
    SELECT 
        'business_info' as table_name,
        COUNT(*) as total_records,
        COUNT(CASE WHEN business_name IS NOT NULL THEN 1 END) as non_null_messages,
        COUNT(CASE WHEN LENGTH(business_name) > 0 THEN 1 END) as non_empty_messages,
        COUNT(CASE WHEN extracted_at > {{ dbt.dateadd('day', -7, dbt.current_timestamp()) }} THEN 1 END) as recent_records,
         MAX(extracted_at) as latest_record_date,
         MIN(extracted_at) as earliest_record_date
     FROM {{ source('telegram_data', 'business_info') }}
),

-- =============================================================================
-- SECTION 2: MODEL PERFORMANCE MONITORING
-- =============================================================================

model_performance AS (
    SELECT 
        'fact_message_analytics' as model_name,
        COUNT(*) as record_count,
        COUNT(CASE WHEN engagement_score > 0 THEN 1 END) as records_with_engagement,
        COUNT(CASE WHEN business_category IS NOT NULL THEN 1 END) as records_with_business_info,
        AVG(engagement_score) as avg_engagement_score,
        COUNT(CASE WHEN has_quality_issues = true THEN 1 END) as quality_issues_count,
        MAX(message_date) as latest_message_date
    FROM {{ ref('fact_message_analytics') }}
),

-- =============================================================================
-- SECTION 3: BUSINESS METRICS MONITORING
-- =============================================================================

business_metrics AS (
    SELECT 
        COUNT(DISTINCT channel_id) as active_channels,
        COUNT(DISTINCT CASE WHEN business_category IS NOT NULL THEN channel_id END) as channels_with_business_info,
        COUNT(DISTINCT business_category) as unique_business_categories,
        AVG(engagement_score) as overall_avg_engagement,
        COUNT(CASE WHEN message_date >= {{ dbt.dateadd('hour', -24, dbt.current_timestamp()) }} THEN 1 END) as messages_last_24h,
        COUNT(CASE WHEN message_date >= {{ dbt.dateadd('day', -7, dbt.current_timestamp()) }} THEN 1 END) as messages_last_7d,
        COUNT(CASE WHEN message_date >= {{ dbt.dateadd('day', -30, dbt.current_timestamp()) }} THEN 1 END) as messages_last_30d
    FROM {{ ref('fact_message_analytics') }}
),

-- =============================================================================
-- SECTION 4: ANOMALY DETECTION
-- =============================================================================

anomalies AS (
    SELECT 
        'engagement_anomalies' as anomaly_type,
        COUNT(*) as anomaly_count,
        MAX(engagement_score) as max_engagement,
        MIN(engagement_score) as min_engagement
    FROM {{ ref('fact_message_analytics') }}
    WHERE engagement_score > (
        SELECT AVG(engagement_score) + 3 * STDDEV(engagement_score)
        FROM {{ ref('fact_message_analytics') }}
    )
    OR engagement_score < 0
    
    UNION ALL
    
    SELECT 
        'message_volume_anomalies' as anomaly_type,
        COUNT(*) as anomaly_count,
        MAX(daily_message_count) as max_daily_messages,
        MIN(daily_message_count) as min_daily_messages
    FROM (
        SELECT 
            DATE(message_date) as message_day,
            COUNT(*) as daily_message_count
        FROM {{ ref('fact_message_analytics') }}
        WHERE message_date >= {{ dbt.dateadd('day', -30, dbt.current_timestamp()) }}
        GROUP BY DATE(message_date)
    ) daily_counts
    WHERE daily_message_count > (
        SELECT AVG(daily_message_count) + 2 * STDDEV(daily_message_count)
        FROM (
            SELECT 
                DATE(message_date) as message_day,
                COUNT(*) as daily_message_count
            FROM {{ ref('fact_message_analytics') }}
            WHERE message_date >= {{ dbt.dateadd('day', -30, dbt.current_timestamp()) }}
            GROUP BY DATE(message_date)
        ) sub_daily_counts
    )
),

-- =============================================================================
-- SECTION 5: IMPLEMENTATION PROGRESS TRACKING
-- =============================================================================

implementation_status AS (
    SELECT 
        'Data Quality Tests' as feature_category,
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name LIKE '%test%' 
                AND table_schema = 'analytics'
            ) THEN 'Implemented'
            ELSE 'Pending'
        END as status,
        'Custom tests for data validation' as description
    
    UNION ALL
    
    SELECT 
        'Business Intelligence',
        CASE 
            WHEN COUNT(*) > 0 THEN 'Implemented'
            ELSE 'Pending'
        END,
        'Advanced analytics models'
    FROM {{ ref('fact_message_analytics') }}
    WHERE business_category IS NOT NULL
    
    UNION ALL
    
    SELECT 
        'Performance Optimization',
        CASE 
            WHEN COUNT(*) > 10000 THEN 'Needed'
            ELSE 'Adequate'
        END,
        'Query performance optimization'
    FROM {{ ref('fact_message_analytics') }}
),

-- =============================================================================
-- SECTION 6: SYSTEM HEALTH INDICATORS
-- =============================================================================

system_health AS (
    SELECT 
        'Data Freshness' as health_metric,
        CASE 
            WHEN MAX(latest_record_date) >= {{ dbt.dateadd('hour', -2, dbt.current_timestamp()) }} THEN 'Healthy'
            WHEN MAX(latest_record_date) >= {{ dbt.dateadd('hour', -24, dbt.current_timestamp()) }} THEN 'Warning'
            ELSE 'Critical'
        END as status,
        MAX(latest_record_date) as last_update,
        'Data pipeline freshness' as description
    FROM data_quality_metrics
    
    UNION ALL
    
    SELECT 
        'Data Completeness',
        CASE 
            WHEN AVG({{ dbt.safe_cast('non_null_messages', dbt.type_float()) }} / NULLIF(total_records, 0)) >= 0.95 THEN 'Healthy'
            WHEN AVG({{ dbt.safe_cast('non_null_messages', dbt.type_float()) }} / NULLIF(total_records, 0)) >= 0.90 THEN 'Warning'
            ELSE 'Critical'
        END,
        NULL,
        CONCAT('Avg completeness: ', 
               ROUND(AVG({{ dbt.safe_cast('non_null_messages', dbt.type_float()) }} / NULLIF(total_records, 0)) * 100, 2), '%')
    FROM data_quality_metrics
    
    UNION ALL
    
    SELECT 
        'Business Coverage',
        CASE 
            WHEN {{ dbt.safe_cast('channels_with_business_info', dbt.type_float()) }} / NULLIF(active_channels, 0) >= 0.80 THEN 'Healthy'
            WHEN {{ dbt.safe_cast('channels_with_business_info', dbt.type_float()) }} / NULLIF(active_channels, 0) >= 0.60 THEN 'Warning'
            ELSE 'Critical'
        END,
        NULL,
        CONCAT('Business info coverage: ', 
               ROUND({{ dbt.safe_cast('channels_with_business_info', dbt.type_float()) }} / NULLIF(active_channels, 0) * 100, 2), '%')
    FROM business_metrics
)

-- =============================================================================
-- FINAL DASHBOARD OUTPUT
-- =============================================================================

SELECT 
    '=== IMPLEMENTATION MONITORING DASHBOARD ===' as section,
    CURRENT_TIMESTAMP as report_generated_at,
    NULL as metric_name,
    NULL as value,
    NULL as status,
    NULL as description

UNION ALL

SELECT 
    '1. DATA QUALITY METRICS',
    NULL,
    table_name,
    CONCAT(total_records, ' records'),
    CASE 
        WHEN {{ dbt.safe_cast('non_null_messages', dbt.type_float()) }} / NULLIF(total_records, 0) >= 0.95 THEN '✅ Excellent'
        WHEN {{ dbt.safe_cast('non_null_messages', dbt.type_float()) }} / NULLIF(total_records, 0) >= 0.90 THEN '⚠️ Good'
        ELSE '❌ Needs Attention'
    END,
    CONCAT('Completeness: ', ROUND({{ dbt.safe_cast('non_null_messages', dbt.type_float()) }} / NULLIF(total_records, 0) * 100, 2), '%')
FROM data_quality_metrics

UNION ALL

SELECT 
    '2. MODEL PERFORMANCE',
    NULL,
    model_name,
    CONCAT(record_count, ' records'),
    CASE 
        WHEN {{ dbt.safe_cast('quality_issues_count', dbt.type_float()) }} / NULLIF(record_count, 0) <= 0.05 THEN '✅ Excellent'
        WHEN {{ dbt.safe_cast('quality_issues_count', dbt.type_float()) }} / NULLIF(record_count, 0) <= 0.10 THEN '⚠️ Good'
        ELSE '❌ Needs Attention'
    END,
    CONCAT('Quality issues: ', ROUND({{ dbt.safe_cast('quality_issues_count', dbt.type_float()) }} / NULLIF(record_count, 0) * 100, 2), '%')
FROM model_performance

UNION ALL

SELECT 
    '3. BUSINESS METRICS',
    NULL,
    'Channel Activity',
    CONCAT(active_channels, ' channels'),
    CASE 
        WHEN messages_last_24h > 100 THEN '✅ High Activity'
        WHEN messages_last_24h > 10 THEN '⚠️ Moderate Activity'
        ELSE '❌ Low Activity'
    END,
    CONCAT(messages_last_24h, ' messages in last 24h')
FROM business_metrics

UNION ALL

SELECT 
    '4. ANOMALY DETECTION',
    NULL,
    anomaly_type,
    CONCAT(anomaly_count, ' anomalies'),
    CASE 
        WHEN anomaly_count = 0 THEN '✅ No Anomalies'
        WHEN anomaly_count <= 5 THEN '⚠️ Few Anomalies'
        ELSE '❌ Many Anomalies'
    END,
    'Review and investigate if needed'
FROM anomalies

UNION ALL

SELECT 
    '5. IMPLEMENTATION STATUS',
    NULL,
    feature_category,
    status,
    CASE 
        WHEN status = 'Implemented' THEN '✅ Complete'
        WHEN status = 'Needed' THEN '⚠️ Action Required'
        ELSE '📋 Pending'
    END,
    description
FROM implementation_status

UNION ALL

SELECT 
    '6. SYSTEM HEALTH',
    NULL,
    health_metric,
    COALESCE(last_update::TEXT, 'N/A'),
    CASE 
        WHEN status = 'Healthy' THEN '✅ Healthy'
        WHEN status = 'Warning' THEN '⚠️ Warning'
        ELSE '❌ Critical'
    END,
    description
FROM system_health

ORDER BY section, metric_name;

-- =============================================================================
-- ADDITIONAL QUERIES FOR DETAILED ANALYSIS
-- =============================================================================

-- Uncomment and run these queries for more detailed analysis:

/*
-- Top performing channels by engagement
SELECT 
    c.channel_name,
    COUNT(*) as message_count,
    AVG(f.engagement_score) as avg_engagement,
    MAX(f.message_date) as latest_message
FROM {{ ref('fact_message_analytics') }} f
JOIN {{ ref('stg_telegram_channels') }} c ON f.channel_id = c.id
GROUP BY c.channel_name
ORDER BY avg_engagement DESC
LIMIT 10;
*/

/*
-- Business category performance
SELECT 
    business_category,
    COUNT(*) as message_count,
    AVG(engagement_score) as avg_engagement,
    COUNT(DISTINCT channel_id) as channel_count
FROM {{ ref('fact_message_analytics') }}
WHERE business_category IS NOT NULL
GROUP BY business_category
ORDER BY avg_engagement DESC;
*/

/*
-- Daily message volume trend (last 30 days)
SELECT 
    DATE(message_date) as message_day,
    COUNT(*) as daily_message_count,
    AVG(engagement_score) as daily_avg_engagement
FROM {{ ref('fact_message_analytics') }}
WHERE message_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(message_date)
ORDER BY message_day DESC;
*/
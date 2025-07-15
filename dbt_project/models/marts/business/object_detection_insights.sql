{{ config(
    materialized='table'
) }}

with detection_analytics as (
    select * from {{ ref('object_detection_analytics') }}
),

-- Daily detection summary
daily_detection_summary as (
    select
        date(detection_created_at) as detection_date,
        channel_name,
        object_category,
        count(*) as total_detections,
        count(distinct media_file_id) as unique_images_processed,
        avg(confidence) as avg_confidence,
        count(case when confidence_level = 'high' then 1 end) as high_confidence_detections,
        count(case when detection_quality = 'excellent' then 1 end) as excellent_quality_detections
    from detection_analytics
    group by 1, 2, 3
),

-- Object class popularity
object_popularity as (
    select
        object_class,
        object_category,
        count(*) as detection_count,
        avg(confidence) as avg_confidence,
        count(distinct channel_name) as channels_detected_in,
        rank() over (order by count(*) desc) as popularity_rank
    from detection_analytics
    group by 1, 2
),

-- Channel detection patterns
channel_patterns as (
    select
        channel_name,
        channel_type,
        count(*) as total_detections,
        count(distinct object_class) as unique_objects_detected,
        count(distinct date(detection_created_at)) as active_detection_days,
        avg(confidence) as avg_detection_confidence,
        
        -- Most common object in this channel
        mode() within group (order by object_class) as most_common_object,
        
        -- Detection quality distribution
        round(100.0 * count(case when confidence_level = 'high' then 1 end) / count(*), 2) as high_confidence_percentage
    from detection_analytics
    group by 1, 2
),

-- Medical relevance scoring
medical_relevance as (
    select
        detection_pk,
        message_id,
        channel_name,
        object_class,
        confidence,
        
        -- Medical relevance score based on object type and context
        case 
            when object_category = 'medical_tools' then confidence * 1.0
            when object_category = 'containers' and channel_type = 'medical' then confidence * 0.8
            when object_category = 'people' and channel_type = 'medical' then confidence * 0.6
            when object_category = 'documents_devices' and channel_type = 'medical' then confidence * 0.4
            else confidence * 0.2
        end as medical_relevance_score,
        
        detection_created_at
    from detection_analytics
)

-- Final insights model
select
    'daily_summary' as insight_type,
    detection_date::text as dimension_1,
    channel_name as dimension_2,
    object_category as dimension_3,
    total_detections as metric_1,
    avg_confidence as metric_2,
    high_confidence_detections as metric_3,
    null as metric_4,
    current_timestamp as created_at
from daily_detection_summary

union all

select
    'object_popularity' as insight_type,
    object_class as dimension_1,
    object_category as dimension_2,
    popularity_rank::text as dimension_3,
    detection_count as metric_1,
    avg_confidence as metric_2,
    channels_detected_in as metric_3,
    null as metric_4,
    current_timestamp as created_at
from object_popularity

union all

select
    'channel_patterns' as insight_type,
    channel_name as dimension_1,
    channel_type as dimension_2,
    most_common_object as dimension_3,
    total_detections as metric_1,
    avg_detection_confidence as metric_2,
    unique_objects_detected as metric_3,
    high_confidence_percentage as metric_4,
    current_timestamp as created_at
from channel_patterns
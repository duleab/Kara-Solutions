{{ config(
    materialized='table'
) }}

with detected_objects as (
    select * from {{ ref('stg_detected_objects') }}
),

media_files as (
    select * from {{ ref('stg_media_files') }}
),

messages as (
    select * from {{ ref('stg_messages') }}
),

channels as (
    select * from {{ ref('stg_channels') }}
),

-- Join all relevant data
detection_enriched as (
    select
        d.detection_pk,
        d.message_id,
        d.media_file_id,
        d.object_class,
        d.confidence,
        d.confidence_level,
        d.object_category,
        d.bbox_area,
        d.detection_created_at,
        
        -- Media file information
        m.file_type,
        m.file_size,
        m.file_size_category,
        m.file_name,
        
        -- Message information
        msg.channel_id,
        msg.message_text,
        msg.message_date,
        
        -- Channel information
        c.channel_name,
        c.channel_type,
        
        -- Add detection quality metrics
        case 
            when d.confidence >= 0.9 then 'excellent'
            when d.confidence >= 0.8 then 'good'
            when d.confidence >= 0.6 then 'fair'
            else 'poor'
        end as detection_quality
        
    from detected_objects d
    left join media_files m on d.media_file_id = m.media_file_pk
    left join messages msg on d.message_id = msg.message_pk
    left join channels c on msg.channel_id = c.channel_pk
)

select * from detection_enriched
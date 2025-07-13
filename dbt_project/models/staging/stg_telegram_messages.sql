{{ config(materialized='view') }}

with source_data as (
    select
        id as message_pk,
        message_id,
        channel_id,
        sender_id,
        message_text,
        date as message_date,
        views,
        forwards,
        replies,
        is_reply,
        reply_to_msg_id,
        has_media,
        media_type,
        created_at
    from {{ source('raw', 'telegram_messages') }}
),

cleaned_data as (
    select
        message_pk,
        message_id,
        channel_id,
        sender_id,
        
        -- Clean message text
        case
            when message_text is null or trim(message_text) = '' then null
            else trim(message_text)
        end as message_text,
        
        -- Clean and validate message date
        message_date,
        
        -- Ensure non-negative metrics
        greatest(coalesce(views, 0), 0) as views,
        greatest(coalesce(forwards, 0), 0) as forwards,
        greatest(coalesce(replies, 0), 0) as replies,
        
        coalesce(is_reply, false) as is_reply,
        reply_to_msg_id,
        coalesce(has_media, false) as has_media,
        
        case
            when media_type is null then 'none'
            when lower(media_type) like '%photo%' then 'photo'
            when lower(media_type) like '%video%' then 'video'
            when lower(media_type) like '%document%' then 'document'
            else 'other'
        end as media_type_clean,
        
        created_at,
        
        -- Extract time components
        extract(hour from message_date) as message_hour,
        extract(dow from message_date) as day_of_week,
        date_trunc('day', message_date) as message_date_only,
        date_trunc('week', message_date) as message_week,
        date_trunc('month', message_date) as message_month,
        
        -- Calculate message length
        case
            when message_text is not null then length(message_text)
            else 0
        end as message_length,
        
        -- Engagement score (simple calculation)
        (coalesce(views, 0) * 0.1 + coalesce(forwards, 0) * 2 + coalesce(replies, 0) * 3) as engagement_score,
        
        -- Message type classification
        case
            when message_text is null or trim(message_text) = '' then 'media_only'
            when has_media then 'text_with_media'
            else 'text_only'
        end as message_type
        
    from source_data
    where message_date is not null
      and message_date >= '2020-01-01'  -- Filter out obviously invalid dates
      and message_date <= current_timestamp
)

select * from cleaned_data
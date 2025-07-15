{{ config(
    materialized='table',
    indexes=[
      {'columns': ['channel_id', 'date_id'], 'type': 'btree'},
      {'columns': ['date_id'], 'type': 'btree'},
      {'columns': ['business_category'], 'type': 'btree'}
    ]
) }}

with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

business_info as (
    select * from {{ ref('stg_business_info') }}
),

channels as (
    select * from {{ ref('dim_channels') }}
),

dates as (
    select * from {{ ref('dim_dates') }}
),

final as (
    select
        -- Message identifiers
        m.message_pk,
        m.channel_id,
        c.title as channel_name,
        c.channel_category,
        
        -- Date dimension foreign key
        d.date_id,
        
        -- Message content
        m.message_text,
        m.message_date,
        m.message_date_only,
        m.message_hour,
        m.day_of_week,
        m.message_week,
        m.message_month,
        
        -- Engagement metrics
        m.views,
        m.forwards,
        m.replies,
        {{ calculate_engagement_score('m.views', 'm.forwards', 'm.replies') }} as engagement_score,
        
        -- Message characteristics
        m.message_length,
        m.message_type,
        m.has_media,
        m.media_type_clean as media_type,
        m.is_reply,
        m.reply_to_msg_id,
        
        -- Sender information
        m.sender_id,
        m.sender_username,
        m.sender_first_name,
        m.sender_last_name,
        
        -- Business information
        b.business_name,
        b.phone_number,
        b.service_type,
        b.location,
        {{ get_business_category('b.business_name', 'b.service_type') }} as business_category,
        b.business_completeness_score,
        b.has_complete_info,
        
        -- Data quality flags
        case when b.business_info_pk is not null then true else false end as has_business_info,
        case when m.views > 0 or m.forwards > 0 or m.replies > 0 then true else false end as has_engagement,
        case when length(trim(m.message_text)) > 10 then true else false end as has_substantial_content
        
    from messages m
    left join business_info b on m.message_pk = b.message_id
    left join channels c on m.channel_id = c.channel_id
    left join dates d on m.message_date_only = d.date_actual
)

select * from final
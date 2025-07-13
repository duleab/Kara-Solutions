{{ config(materialized='table') }}

with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

channels as (
    select * from {{ ref('stg_telegram_channels') }}
),

business_info as (
    select * from {{ ref('stg_business_info') }}
),

message_analytics as (
    select
        m.message_pk,
        m.message_id,
        m.channel_id,
        c.channel_name,
        c.channel_category,
        c.title as channel_title,
        
        -- Message details
        m.message_text,
        m.message_date,
        m.message_date_only,
        m.message_week,
        m.message_month,
        m.message_hour,
        m.day_of_week,
        
        -- Engagement metrics
        m.views,
        m.forwards,
        m.replies,
        m.engagement_score,
        
        -- Message characteristics
        m.message_length,
        m.message_type,
        m.has_media,
        m.media_type_clean as media_type,
        m.is_reply,
        
        -- Business information
        b.business_name_clean as business_name,
        b.product_name_clean as product_name,
        b.price_numeric as price,
        b.contact_info_clean as contact_info,
        b.phone_number,
        b.address_clean as address,
        b.city,
        b.business_category,
        b.has_delivery,
        b.has_business_info,
        b.has_price_info,
        b.has_contact_info,
        
        -- Time-based features
        case
            when m.message_hour between 6 and 11 then 'Morning'
            when m.message_hour between 12 and 17 then 'Afternoon'
            when m.message_hour between 18 and 21 then 'Evening'
            else 'Night'
        end as time_of_day,
        
        case
            when m.day_of_week in (0, 6) then 'Weekend'
            else 'Weekday'
        end as day_type,
        
        -- Engagement categories
        case
            when m.views >= 1000 then 'High'
            when m.views >= 100 then 'Medium'
            when m.views > 0 then 'Low'
            else 'No Views'
        end as view_category,
        
        case
            when m.engagement_score >= 100 then 'High Engagement'
            when m.engagement_score >= 10 then 'Medium Engagement'
            when m.engagement_score > 0 then 'Low Engagement'
            else 'No Engagement'
        end as engagement_category,
        
        -- Content quality indicators
        case
            when m.message_length >= 500 then 'Long'
            when m.message_length >= 100 then 'Medium'
            when m.message_length > 0 then 'Short'
            else 'No Text'
        end as content_length_category,
        
        -- Business completeness score
        (
            case when b.has_business_info then 1 else 0 end +
            case when b.has_price_info then 1 else 0 end +
            case when b.has_contact_info then 1 else 0 end +
            case when b.address_clean is not null then 1 else 0 end +
            case when b.has_delivery then 1 else 0 end
        ) as business_completeness_score,
        
        m.created_at
        
    from messages m
    left join channels c on m.channel_id = c.channel_id
    left join business_info b on m.message_pk = b.message_id
)

select * from message_analytics
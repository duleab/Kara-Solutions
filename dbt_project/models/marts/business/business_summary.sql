{{ config(materialized='table') }}

with fact_messages as (
    select * from {{ ref('fact_message_analytics') }}
),

business_metrics as (
    select
        channel_name,
        channel_category,
        business_category,
        city,
        
        -- Message counts
        count(*) as total_messages,
        count(case when has_business_info then 1 end) as messages_with_business_info,
        count(case when has_price_info then 1 end) as messages_with_price,
        count(case when has_contact_info then 1 end) as messages_with_contact,
        count(case when has_media then 1 end) as messages_with_media,
        
        -- Engagement metrics
        sum(views) as total_views,
        sum(forwards) as total_forwards,
        sum(replies) as total_replies,
        avg(views) as avg_views_per_message,
        avg(engagement_score) as avg_engagement_score,
        
        -- Business metrics
        count(distinct business_name) as unique_businesses,
        count(distinct product_name) as unique_products,
        avg(price) as avg_price,
        min(price) as min_price,
        max(price) as max_price,
        
        -- Contact and delivery
        count(distinct phone_number) as unique_phone_numbers,
        count(case when has_delivery then 1 end) as businesses_with_delivery,
        
        -- Time metrics
        min(message_date) as first_message_date,
        max(message_date) as last_message_date,
        
        -- Quality metrics
        avg(business_completeness_score) as avg_business_completeness,
        avg(message_length) as avg_message_length,
        
        -- Activity patterns
        count(case when time_of_day = 'Morning' then 1 end) as morning_messages,
        count(case when time_of_day = 'Afternoon' then 1 end) as afternoon_messages,
        count(case when time_of_day = 'Evening' then 1 end) as evening_messages,
        count(case when time_of_day = 'Night' then 1 end) as night_messages,
        
        count(case when day_type = 'Weekend' then 1 end) as weekend_messages,
        count(case when day_type = 'Weekday' then 1 end) as weekday_messages
        
    from fact_messages
    group by 
        channel_name,
        channel_category,
        business_category,
        city
),

final as (
    select
        *,
        
        -- Calculate percentages
        round(
            (messages_with_business_info::float / total_messages) * 100, 2
        ) as pct_messages_with_business_info,
        
        round(
            (messages_with_price::float / total_messages) * 100, 2
        ) as pct_messages_with_price,
        
        round(
            (messages_with_contact::float / total_messages) * 100, 2
        ) as pct_messages_with_contact,
        
        round(
            (messages_with_media::float / total_messages) * 100, 2
        ) as pct_messages_with_media,
        
        round(
            (businesses_with_delivery::float / nullif(messages_with_business_info, 0)) * 100, 2
        ) as pct_businesses_with_delivery,
        
        -- Activity ratios
        round(
            (weekend_messages::float / total_messages) * 100, 2
        ) as pct_weekend_activity,
        
        -- Engagement per view ratio
        case
            when total_views > 0 then round((total_forwards + total_replies)::float / total_views * 100, 4)
            else 0
        end as engagement_rate_pct,
        
        -- Days active
        extract(days from (last_message_date - first_message_date)) + 1 as days_active,
        
        -- Messages per day
        case
            when extract(days from (last_message_date - first_message_date)) + 1 > 0
            then round(total_messages::float / (extract(days from (last_message_date - first_message_date)) + 1), 2)
            else 0
        end as messages_per_day
        
    from business_metrics
)

select * from final
order by total_messages desc, avg_engagement_score desc
{{ config(materialized='table') }}

with fact_messages as (
    select * from {{ ref('fact_message_analytics') }}
),

business_metrics as (
    select
        channel_id,
        
        -- Message counts
        count(*) as total_messages,
        count(case when has_media then 1 end) as messages_with_media,
        
        -- Engagement metrics
        sum(views) as total_views,
        sum(forwards) as total_forwards,
        sum(replies) as total_replies,
        avg(views) as avg_views_per_message,
        avg(engagement_score) as avg_engagement_score,
        
        -- Time metrics
        min(message_date) as first_message_date,
        max(message_date) as last_message_date,
        
        -- Quality metrics
        avg(message_length) as avg_message_length,
        
        -- Activity patterns
        count(case when message_hour between 6 and 11 then 1 end) as morning_messages,
        count(case when message_hour between 12 and 17 then 1 end) as afternoon_messages,
        count(case when message_hour between 18 and 22 then 1 end) as evening_messages,
        count(case when message_hour between 23 and 5 then 1 end) as night_messages,
        
        count(case when day_of_week in (0, 6) then 1 end) as weekend_messages,
        count(case when day_of_week between 1 and 5 then 1 end) as weekday_messages
        
    from fact_messages
    group by channel_id
),

final as (
    select
        *,
        
        -- Calculate percentages
        round(
            (messages_with_media::float / total_messages) * 100, 2
        ) as pct_messages_with_media,
        
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
order by total_views desc, avg_engagement_score desc
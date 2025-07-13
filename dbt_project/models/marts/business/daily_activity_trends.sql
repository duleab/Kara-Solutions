{{ config(materialized='table') }}

with fact_messages as (
    select * from {{ ref('fact_message_analytics') }}
),

daily_metrics as (
    select
        message_date_only as activity_date,
        channel_name,
        channel_category,
        business_category,
        
        -- Daily counts
        count(*) as daily_messages,
        count(case when has_business_info then 1 end) as daily_business_messages,
        count(case when has_media then 1 end) as daily_media_messages,
        count(distinct business_name) as daily_unique_businesses,
        
        -- Daily engagement
        sum(views) as daily_views,
        sum(forwards) as daily_forwards,
        sum(replies) as daily_replies,
        sum(engagement_score) as daily_engagement_score,
        
        -- Daily averages
        avg(views) as avg_daily_views_per_message,
        avg(message_length) as avg_daily_message_length,
        avg(price) as avg_daily_price,
        
        -- Content distribution
        count(case when message_type = 'text_only' then 1 end) as text_only_messages,
        count(case when message_type = 'text_with_media' then 1 end) as text_with_media_messages,
        count(case when message_type = 'media_only' then 1 end) as media_only_messages,
        
        -- Time patterns
        count(case when time_of_day = 'Morning' then 1 end) as morning_messages,
        count(case when time_of_day = 'Afternoon' then 1 end) as afternoon_messages,
        count(case when time_of_day = 'Evening' then 1 end) as evening_messages,
        count(case when time_of_day = 'Night' then 1 end) as night_messages
        
    from fact_messages
    group by 
        message_date_only,
        channel_name,
        channel_category,
        business_category
),

with_trends as (
    select
        *,
        
        -- Calculate 7-day moving averages
        avg(daily_messages) over (
            partition by channel_name, business_category
            order by activity_date
            rows between 6 preceding and current row
        ) as messages_7day_avg,
        
        avg(daily_engagement_score) over (
            partition by channel_name, business_category
            order by activity_date
            rows between 6 preceding and current row
        ) as engagement_7day_avg,
        
        avg(daily_views) over (
            partition by channel_name, business_category
            order by activity_date
            rows between 6 preceding and current row
        ) as views_7day_avg,
        
        -- Calculate day-over-day changes
        daily_messages - lag(daily_messages, 1) over (
            partition by channel_name, business_category
            order by activity_date
        ) as messages_day_change,
        
        daily_engagement_score - lag(daily_engagement_score, 1) over (
            partition by channel_name, business_category
            order by activity_date
        ) as engagement_day_change,
        
        -- Calculate week-over-week changes
        daily_messages - lag(daily_messages, 7) over (
            partition by channel_name, business_category
            order by activity_date
        ) as messages_week_change,
        
        -- Day of week
        extract(dow from activity_date) as day_of_week,
        to_char(activity_date, 'Day') as day_name,
        
        -- Week and month identifiers
        date_trunc('week', activity_date) as week_start,
        date_trunc('month', activity_date) as month_start
        
    from daily_metrics
),

final as (
    select
        *,
        
        -- Calculate percentage changes
        case
            when lag(daily_messages, 1) over (
                partition by channel_name, business_category
                order by activity_date
            ) > 0
            then round(
                (messages_day_change::float / lag(daily_messages, 1) over (
                    partition by channel_name, business_category
                    order by activity_date
                )) * 100, 2
            )
            else null
        end as messages_day_change_pct,
        
        case
            when lag(daily_messages, 7) over (
                partition by channel_name, business_category
                order by activity_date
            ) > 0
            then round(
                (messages_week_change::float / lag(daily_messages, 7) over (
                    partition by channel_name, business_category
                    order by activity_date
                )) * 100, 2
            )
            else null
        end as messages_week_change_pct,
        
        -- Activity level classification
        case
            when daily_messages >= messages_7day_avg * 1.5 then 'High Activity'
            when daily_messages >= messages_7day_avg * 0.5 then 'Normal Activity'
            when daily_messages > 0 then 'Low Activity'
            else 'No Activity'
        end as activity_level,
        
        -- Weekend indicator
        case
            when day_of_week in (0, 6) then true
            else false
        end as is_weekend
        
    from with_trends
)

select * from final
order by activity_date desc, channel_name, business_category
-- Channel Performance Analysis
-- This analysis helps identify top-performing channels and engagement patterns
-- Run with: dbt compile --select analyses/channel_performance_analysis

with channel_metrics as (
  select
    channel_id,
    count(*) as total_messages,
    avg(engagement_score) as avg_engagement,
    sum(views) as total_views,
    sum(case when has_media then 1 else 0 end) as media_messages,
    min(message_date) as first_message,
    max(message_date) as last_message,
    extract(days from (max(message_date) - min(message_date))) + 1 as days_active
  from {{ ref('stg_telegram_messages') }}
  group by channel_id
),

performance_ranking as (
  select
    *,
    total_messages::float / nullif(days_active, 0) as messages_per_day,
    media_messages::float / total_messages * 100 as media_percentage,
    row_number() over (order by avg_engagement desc) as engagement_rank,
    row_number() over (order by total_views desc) as views_rank,
    row_number() over (order by total_messages desc) as volume_rank
  from channel_metrics
  where days_active > 0
)

select
  channel_id,
  total_messages,
  round(avg_engagement, 2) as avg_engagement,
  total_views,
  round(messages_per_day, 2) as messages_per_day,
  round(media_percentage, 1) as media_percentage,
  engagement_rank,
  views_rank,
  volume_rank,
  case
    when engagement_rank <= 5 and views_rank <= 5 then 'Top Performer'
    when engagement_rank <= 10 and views_rank <= 10 then 'Good Performer'
    when messages_per_day >= 1 then 'High Volume'
    else 'Standard'
  end as performance_category,
  first_message,
  last_message,
  days_active
from performance_ranking
order by avg_engagement desc
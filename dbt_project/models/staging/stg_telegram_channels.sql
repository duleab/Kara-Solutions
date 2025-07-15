{{ config(materialized='view') }}

with source_data as (
    select
        id as channel_id,
        username as channel_name,
        username as channel_url,
        id as telegram_channel_id,
        title,
        about as description,
        participants_count,
        created_date as created_at,
        scraped_at as updated_at
    from {{ source('telegram_data', 'telegram_channels') }}
),

cleaned_data as (
    select
        channel_id,
        lower(trim(channel_name)) as channel_name,
        channel_url,
        telegram_channel_id,
        coalesce(nullif(trim(title), ''), 'Unknown') as title,
        coalesce(nullif(trim(description), ''), 'No description') as description,
        coalesce(participants_count, 0) as participants_count,
        created_at,
        updated_at,
        
        -- Add channel category based on name
        case
            when lower(channel_name) like '%med%' or lower(channel_name) like '%pharm%' then 'Medical/Pharmacy'
            when lower(channel_name) like '%cosmetic%' or lower(channel_name) like '%beauty%' then 'Cosmetics/Beauty'
            else 'Other'
        end as channel_category,
        
        -- Calculate days since creation
        extract(days from (now() - created_at)) as days_since_creation
        
    from source_data
)

select * from cleaned_data
{{ config(
    materialized='table',
    indexes=[
      {'columns': ['channel_id'], 'type': 'btree'},
      {'columns': ['channel_name'], 'type': 'btree'}
    ]
) }}

with channels as (
    select * from {{ ref('stg_telegram_channels') }}
),

final as (
    select
        channel_id,
        channel_name,
        channel_url,
        telegram_channel_id,
        title,
        description,
        participants_count,
        created_at,
        updated_at,
        
        -- Derived attributes
        case 
            when lower(channel_name) like '%medical%' or lower(title) like '%medical%' then 'Medical'
            when lower(channel_name) like '%pharmacy%' or lower(title) like '%pharmacy%' then 'Pharmacy'
            when lower(channel_name) like '%hospital%' or lower(title) like '%hospital%' then 'Hospital'
            when lower(channel_name) like '%clinic%' or lower(title) like '%clinic%' then 'Clinic'
            else 'General Health'
        end as channel_category,
        
        case 
            when participants_count >= 10000 then 'Large'
            when participants_count >= 1000 then 'Medium'
            when participants_count >= 100 then 'Small'
            else 'Micro'
        end as channel_size,
        
        current_timestamp as dim_created_at
        
    from channels
)

select * from final
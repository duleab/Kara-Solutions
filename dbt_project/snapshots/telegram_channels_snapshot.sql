{% snapshot telegram_channels_snapshot %}

{{
  config(
    target_schema='snapshots',
    unique_key='id',
    strategy='timestamp',
    updated_at='scraped_at'
  )
}}

select
  id,
  username,
  title,
  about,
  participants_count,
  is_broadcast,
  is_megagroup,
  created_date,
  scraped_at
from {{ source('telegram_data', 'telegram_channels') }}

{% endsnapshot %}
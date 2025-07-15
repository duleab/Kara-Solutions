{{ config(materialized='table') }}

select
    message_pk,
    channel_id,
    message_text
from {{ ref('stg_telegram_messages') }}
limit 5
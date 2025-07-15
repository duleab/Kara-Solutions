{{ config(materialized='table') }}

select *
from telegram_messages
limit 1
{{ config(
    materialized='table',
    indexes=[
      {'columns': ['date_id'], 'type': 'btree'},
      {'columns': ['date_actual'], 'type': 'btree'},
      {'columns': ['year', 'month'], 'type': 'btree'}
    ]
) }}

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2022-01-01' as date)",
        end_date="cast('2025-12-31' as date)"
    ) }}
),

date_dimension as (
    select
        -- Primary key
        to_char(date_day, 'YYYYMMDD')::integer as date_id,
        
        -- Date attributes
        date_day as date_actual,
        extract(year from date_day) as year,
        extract(month from date_day) as month,
        extract(day from date_day) as day,
        extract(quarter from date_day) as quarter,
        extract(week from date_day) as week_of_year,
        extract(dow from date_day) as day_of_week,
        extract(doy from date_day) as day_of_year,
        
        -- Formatted dates
        to_char(date_day, 'YYYY-MM-DD') as date_string,
        to_char(date_day, 'Month') as month_name,
        to_char(date_day, 'Day') as day_name,
        to_char(date_day, 'YYYY-MM') as year_month,
        to_char(date_day, 'YYYY-Q') as year_quarter,
        
        -- Business logic
        case 
            when extract(dow from date_day) in (0, 6) then true
            else false
        end as is_weekend,
        
        case 
            when extract(dow from date_day) between 1 and 5 then true
            else false
        end as is_weekday,
        
        -- Ethiopian calendar considerations
        case 
            when extract(month from date_day) = 9 and extract(day from date_day) = 11 then 'Ethiopian New Year'
            when extract(month from date_day) = 1 and extract(day from date_day) = 7 then 'Ethiopian Christmas'
            when extract(month from date_day) = 1 and extract(day from date_day) = 19 then 'Timkat'
            when extract(month from date_day) = 5 and extract(day from date_day) = 1 then 'Labor Day'
            else null
        end as ethiopian_holiday,
        
        current_timestamp as dim_created_at
        
    from date_spine
)

select * from date_dimension
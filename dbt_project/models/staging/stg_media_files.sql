{{ config(
    materialized='view'
) }}

with source as (
    select * from {{ source('telegram_data', 'media_files') }}
),

renamed as (
    select
        id as media_file_pk,
        message_id,
        file_type,
        file_path,
        file_size,
        file_name,
        created_at as media_created_at,
        
        -- Add derived fields
        case 
            when file_type = 'image' then true
            else false
        end as is_image,
        
        -- Extract file extension
        lower(right(file_name, 4)) as file_extension,
        
        -- Calculate file size categories
        case 
            when file_size < 100000 then 'small'  -- < 100KB
            when file_size < 1000000 then 'medium' -- < 1MB
            else 'large'  -- >= 1MB
        end as file_size_category,
        
        -- Check if file path exists (basic validation)
        case 
            when file_path is not null and length(file_path) > 0 then true
            else false
        end as has_valid_path
        
    from source
)

select * from renamed
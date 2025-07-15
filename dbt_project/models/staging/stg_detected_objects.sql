{{ config(
    materialized='view'
) }}

with source as (
    select * from {{ source('telegram_data', 'detected_objects') }}
),

renamed as (
    select
        id as detection_pk,
        message_id,
        media_file_id,
        object_class,
        confidence,
        bbox_x,
        bbox_y,
        bbox_width,
        bbox_height,
        created_at as detection_created_at,
        
        -- Add derived fields
        case 
            when confidence >= 0.8 then 'high'
            when confidence >= 0.5 then 'medium'
            else 'low'
        end as confidence_level,
        
        -- Calculate bounding box area
        bbox_width * bbox_height as bbox_area,
        
        -- Categorize objects for medical context
        case 
            when object_class in ('bottle', 'cup') then 'containers'
            when object_class in ('person') then 'people'
            when object_class in ('book', 'cell phone') then 'documents_devices'
            when object_class in ('scissors') then 'medical_tools'
            else 'other'
        end as object_category
        
    from source
)

select * from renamed
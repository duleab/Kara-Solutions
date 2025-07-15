{{ config(materialized='view') }}

with source_data as (
    select
        id as business_info_pk,
        message_id,
        channel_username,
        business_name,
        phone_number,
        service_type,
        location,
        extracted_at
    from {{ source('telegram_data', 'business_info') }}
),

cleaned_data as (
    select
        business_info_pk,
        message_id,
        channel_username,
        
        -- Clean business name
        case
            when business_name is null or trim(business_name) = '' then null
            else trim(business_name)
        end as business_name_clean,
        
        -- Clean phone number
        case
            when phone_number is null or trim(phone_number) = '' then null
            else trim(phone_number)
        end as phone_number_clean,
        
        -- Extract phone number type
        case
            when phone_number like '%+251%' then 'International'
            when phone_number like '%09%' then 'Local'
            else 'Unknown'
        end as phone_number_type,
        
        -- Clean service type
        case
            when service_type is null or trim(service_type) = '' then 'Unknown'
            else trim(service_type)
        end as service_type_clean,
        
        -- Clean location
        case
            when location is null or trim(location) = '' then null
            else trim(location)
        end as location_clean,
        
        extracted_at,
        
        -- Business category based on service type
        case
            when lower(coalesce(service_type, '')) like '%pharmacy%' 
                 or lower(coalesce(service_type, '')) like '%medical%' then 'Medical/Pharmacy'
            when lower(coalesce(service_type, '')) like '%emergency%' then 'Emergency'
            when lower(coalesce(service_type, '')) like '%vaccination%' then 'Vaccination'
            when lower(coalesce(service_type, '')) like '%checkup%' then 'Checkup'
            else 'General Medical'
        end as business_category,
        
        -- Data quality flags
        case
            when business_name is not null and trim(business_name) != '' then true
            else false
        end as has_business_info,
        
        case
            when phone_number is not null and trim(phone_number) != '' then true
            else false
        end as has_contact_info
        
    from source_data
)

select * from cleaned_data
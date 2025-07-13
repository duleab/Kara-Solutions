{{ config(materialized='view') }}

with source_data as (
    select
        id as business_info_pk,
        message_id,
        business_name,
        product_name,
        price,
        contact_info,
        address,
        opening_hours,
        delivery_info,
        extracted_at
    from {{ source('raw', 'business_info') }}
),

cleaned_data as (
    select
        business_info_pk,
        message_id,
        
        -- Clean business name
        case
            when business_name is null or trim(business_name) = '' then null
            else trim(regexp_replace(business_name, '[^a-zA-Z0-9\s]', '', 'g'))
        end as business_name_clean,
        
        -- Clean product name
        case
            when product_name is null or trim(product_name) = '' then null
            else trim(product_name)
        end as product_name_clean,
        
        -- Clean and standardize price
        case
            when price is null or trim(price) = '' then null
            else trim(regexp_replace(price, '[^0-9.,]', '', 'g'))
        end as price_clean,
        
        -- Extract numeric price value
        case
            when price is null or trim(price) = '' then null
            else cast(
                regexp_replace(
                    regexp_replace(trim(price), '[^0-9.,]', '', 'g'),
                    ',', '', 'g'
                ) as decimal(10,2)
            )
        end as price_numeric,
        
        -- Clean contact info
        case
            when contact_info is null or trim(contact_info) = '' then null
            else trim(contact_info)
        end as contact_info_clean,
        
        -- Extract phone numbers from contact info
        case
            when contact_info ~ '\+251[0-9]{9}' then 
                regexp_extract(contact_info, '\+251[0-9]{9}', 1)
            when contact_info ~ '09[0-9]{8}' then 
                regexp_extract(contact_info, '09[0-9]{8}', 1)
            else null
        end as phone_number,
        
        -- Clean address
        case
            when address is null or trim(address) = '' then null
            else trim(address)
        end as address_clean,
        
        -- Extract city from address (simple pattern matching)
        case
            when lower(address) like '%addis ababa%' or lower(address) like '%addis%' then 'Addis Ababa'
            when lower(address) like '%dire dawa%' then 'Dire Dawa'
            when lower(address) like '%mekelle%' then 'Mekelle'
            when lower(address) like '%gondar%' then 'Gondar'
            when lower(address) like '%hawassa%' then 'Hawassa'
            when lower(address) like '%bahir dar%' then 'Bahir Dar'
            when lower(address) like '%jimma%' then 'Jimma'
            when lower(address) like '%dessie%' then 'Dessie'
            when lower(address) like '%adama%' or lower(address) like '%nazret%' then 'Adama'
            else 'Other'
        end as city,
        
        -- Clean opening hours
        case
            when opening_hours is null or trim(opening_hours) = '' then null
            else trim(opening_hours)
        end as opening_hours_clean,
        
        -- Clean delivery info
        case
            when delivery_info is null or trim(delivery_info) = '' then null
            else trim(delivery_info)
        end as delivery_info_clean,
        
        -- Check if delivery is available
        case
            when delivery_info is not null and trim(delivery_info) != '' then true
            when lower(coalesce(delivery_info, '')) like '%delivery%' then true
            when lower(coalesce(delivery_info, '')) like '%transport%' then true
            else false
        end as has_delivery,
        
        extracted_at,
        
        -- Business category based on product/business name
        case
            when lower(coalesce(business_name, product_name, '')) like '%pharmacy%' 
                 or lower(coalesce(business_name, product_name, '')) like '%drug%'
                 or lower(coalesce(business_name, product_name, '')) like '%medicine%'
                 or lower(coalesce(business_name, product_name, '')) like '%medical%' then 'Pharmacy'
            when lower(coalesce(business_name, product_name, '')) like '%cosmetic%'
                 or lower(coalesce(business_name, product_name, '')) like '%beauty%'
                 or lower(coalesce(business_name, product_name, '')) like '%skin%' then 'Cosmetics'
            when lower(coalesce(business_name, product_name, '')) like '%supplement%'
                 or lower(coalesce(business_name, product_name, '')) like '%vitamin%' then 'Supplements'
            else 'Other'
        end as business_category,
        
        -- Data quality flags
        case
            when business_name is not null or product_name is not null then true
            else false
        end as has_business_info,
        
        case
            when price is not null and price != '' then true
            else false
        end as has_price_info,
        
        case
            when contact_info is not null and contact_info != '' then true
            else false
        end as has_contact_info
        
    from source_data
)

select * from cleaned_data
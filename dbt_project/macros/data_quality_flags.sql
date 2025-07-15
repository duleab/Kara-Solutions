{% macro generate_data_quality_flags(table_alias='') %}
  {%- set prefix = table_alias + '.' if table_alias else '' -%}
  
  -- Data completeness flags
  case when {{ prefix }}message_text is not null and length(trim({{ prefix }}message_text)) > 0 then 1 else 0 end as has_content,
  case when {{ prefix }}views > 0 then 1 else 0 end as has_engagement,
  case when {{ prefix }}sender_id is not null then 1 else 0 end as has_sender_info,
  case when {{ prefix }}date is not null then 1 else 0 end as has_valid_date,
  
  -- Business information completeness
  case when {{ prefix }}business_name is not null and length(trim({{ prefix }}business_name)) > 0 then 1 else 0 end as has_business_name,
  case when {{ prefix }}phone_number is not null and length(trim({{ prefix }}phone_number)) > 0 then 1 else 0 end as has_phone,
  case when {{ prefix }}service_type is not null and length(trim({{ prefix }}service_type)) > 0 then 1 else 0 end as has_service_type,
  case when {{ prefix }}location is not null and length(trim({{ prefix }}location)) > 0 then 1 else 0 end as has_location
{% endmacro %}
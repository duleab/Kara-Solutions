{% macro get_business_category(business_name, service_type) %}
  case
    when lower({{ business_name }}) like '%pharmacy%' or lower({{ service_type }}) like '%pharmacy%' then 'Pharmacy'
    when lower({{ business_name }}) like '%clinic%' or lower({{ service_type }}) like '%clinic%' then 'Clinic'
    when lower({{ business_name }}) like '%hospital%' or lower({{ service_type }}) like '%hospital%' then 'Hospital'
    when lower({{ business_name }}) like '%dental%' or lower({{ service_type }}) like '%dental%' then 'Dental'
    when lower({{ business_name }}) like '%lab%' or lower({{ service_type }}) like '%lab%' then 'Laboratory'
    when lower({{ business_name }}) like '%medical%' or lower({{ service_type }}) like '%medical%' then 'Medical Services'
    when lower({{ business_name }}) like '%equipment%' or lower({{ service_type }}) like '%equipment%' then 'Medical Equipment'
    when lower({{ business_name }}) like '%insurance%' or lower({{ service_type }}) like '%insurance%' then 'Insurance'
    when lower({{ business_name }}) like '%ambulance%' or lower({{ service_type }}) like '%ambulance%' then 'Emergency Services'
    when lower({{ business_name }}) like '%therapy%' or lower({{ service_type }}) like '%therapy%' then 'Therapy'
    else 'Other'
  end
{% endmacro %}
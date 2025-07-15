{% test data_freshness(model, column_name, max_age_hours=24) %}

  select count(*)
  from {{ model }}
  where {{ column_name }} < (current_timestamp - interval '{{ max_age_hours }} hours')
    or {{ column_name }} is null

{% endtest %}
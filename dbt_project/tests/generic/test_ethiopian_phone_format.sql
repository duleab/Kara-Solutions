{% test ethiopian_phone_format(model, column_name) %}

  select count(*)
  from {{ model }}
  where {{ column_name }} is not null
    and not (
      -- Ethiopian phone number patterns
      {{ column_name }} ~ '^\+251[0-9]{9}$'  -- International format
      or {{ column_name }} ~ '^251[0-9]{9}$'   -- Without plus
      or {{ column_name }} ~ '^0[0-9]{9}$'     -- Local format
      or {{ column_name }} ~ '^[0-9]{9}$'      -- 9 digits
    )

{% endtest %}
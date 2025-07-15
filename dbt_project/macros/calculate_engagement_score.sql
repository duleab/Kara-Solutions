{% macro calculate_engagement_score(views, forwards, replies, weights=none) %}
  {%- set default_weights = {'views': 1, 'forwards': 3, 'replies': 5} -%}
  {%- set final_weights = weights or default_weights -%}
  
  (
    coalesce({{ views }}, 0) * {{ final_weights.views }} +
    coalesce({{ forwards }}, 0) * {{ final_weights.forwards }} +
    coalesce({{ replies }}, 0) * {{ final_weights.replies }}
  )
{% endmacro %}
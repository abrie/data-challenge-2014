SELECT
  type,
  MIN(created_at) as first_time,
  MAX(created_at) as last_time,
FROM
  $dataset
WHERE 
  type IS NOT NULL
GROUP EACH BY
  type

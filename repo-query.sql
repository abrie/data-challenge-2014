SELECT
  previous_state, present_state,
  COUNT(*) hits
FROM(
  SELECT
    state as present_state,
    LAG(present_state, 1, '~') OVER (PARTITION BY repository_url ORDER BY time) as previous_state
  FROM(
    SELECT
    repository_url,
    PARSE_UTC_USEC(created_at) as time,
    CASE
      WHEN type = "CreateEvent" THEN CONCAT("CreateEvent:",
        IF(payload_ref_type is null, "repository", payload_ref_type))
      WHEN type = "DeleteEvent" THEN CONCAT("DeleteEvent:", payload_ref_type)
      WHEN type = "PullRequestEvent" THEN CONCAT("PullRequestEvent:", payload_action)
      WHEN type = "IssuesEvent" THEN CONCAT("IssuesEvent:", payload_action)
      ELSE type
    END as state,
    FROM
        $dataset 
    WHERE
      repository_url IS NOT NULL
    GROUP EACH BY repository_url, time, state
  ) GROUP EACH BY repository_url, time, present_state
) GROUP EACH BY previous_state, present_state
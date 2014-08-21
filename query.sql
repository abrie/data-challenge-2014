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
WHEN type = "CreateEvent" THEN CONCAT("CreateEvent:", payload_ref_type)
WHEN type = "DeleteEvent" THEN CONCAT("DeleteEvent:", payload_ref_type)
WHEN type = "PullRequestEvent" THEN CONCAT("PullRequestEvent:", payload_action)
WHEN type = "IssuesEvent" THEN CONCAT("IssuesEvent:", payload_action)
ELSE type
END as state,
FROM
$dataset
WHERE
repository_url IS NOT NULL
AND QUARTER(TIMESTAMP(created_at)) = $quarter 
ORDER BY repository_url, time ASC
)) GROUP BY present_state, previous_state

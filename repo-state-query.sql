SELECT
  keys.concated_type as event,
  COUNT(keys.concated_type) as population,
FROM(
  SELECT
    keys.concated_type
  FROM 
    $dataset AS t 
  JOIN EACH
    (SELECT repository_url, 
      MAX(created_at) AS max_created_at,
      CASE
        WHEN type = "CreateEvent" THEN CONCAT("CreateEvent:",
          IF(payload_ref_type is null, "repository", payload_ref_type))
        WHEN type = "DeleteEvent" THEN CONCAT("DeleteEvent:", payload_ref_type)
        WHEN type = "PullRequestEvent" THEN CONCAT("PullRequestEvent:",
          CASE
            WHEN payload_action = "closed" THEN
              IF(payload_pull_request_merged == "false", "closed-not-merged","closed-merged")
            ELSE payload_action
          END)
        WHEN type = "IssuesEvent" THEN CONCAT("IssuesEvent:", payload_action)
        WHEN type = "GistEvent" THEN CONCAT("GistEvent:", payload_action)
        WHEN type = "IssueCommentEvent" THEN CONCAT("IssueCommentEvent:",
          IF(payload_action is null, "created", payload_action))
        WHEN type = "ReleaseEvent" THEN CONCAT("ReleaseEvent:", payload_action)
        WHEN type = "WatchEvent" THEN CONCAT("WatchEvent:", payload_action)
        WHEN type = "MemberEvent" THEN CONCAT("MemberEvent:", payload_action)
        WHEN type = "GollumEvent" Then CONCAT("GollumEvent:", payload_page_action)
        ELSE type
      END as concated_type,
      FROM
        $dataset 
      WHERE
        type IS NOT NULL
        AND repository_url IS NOT NULL
        AND NOT (type = "PullRequestEvent" AND payload_action = "merged")
        AND created_at >= "2011-2-12" // the offical start date of the archive.
      GROUP EACH BY
        repository_url,
        concated_type
    ) AS keys
  ON
    keys.repository_url = t.repository_url
    AND keys.max_created_at = t.created_at)
GROUP EACH BY
  event

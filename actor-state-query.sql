SELECT
  concated_type,
  COUNT(concated_type) as population,
  RATIO_TO_REPORT(population) OVER() as ratio
FROM(
  SELECT
    subselect_A.actor,
    subselect_A.created_at,
    CASE
      WHEN subselect_A.type = "CreateEvent" THEN CONCAT("CreateEvent:", subselect_A.payload_ref_type)
      WHEN subselect_A.type = "DeleteEvent" THEN CONCAT("DeleteEvent:", subselect_A.payload_ref_type)
      WHEN subselect_A.type = "PullRequestEvent" THEN CONCAT("PullRequestEvent:", subselect_A.payload_action)
      WHEN subselect_A.type = "IssuesEvent" THEN CONCAT("IssuesEvent:", subselect_A.payload_action)
      WHEN subselect_A.type = "GistEvent" THEN CONCAT("GistEvent:", subselect_A.payload_action)
      WHEN subselect_A.type = "IssueCommentEvent" THEN CONCAT("IssueCommentEvent:", subselect_A.payload_action)
      ELSE subselect_A.type
    END as concated_type,
    // the following subselect is because of a bigquery limitation with joins and table unions
    FROM(
        SELECT 
          created_at,
          actor,
          type,
          payload_ref_type,
          payload_action
        FROM
          $dataset
    ) subselect_A
    JOIN EACH(
      SELECT
        MAX(created_at) as max_created,
        actor,
        CASE
          WHEN type = "CreateEvent" THEN CONCAT("CreateEvent:", payload_ref_type)
          WHEN type = "DeleteEvent" THEN CONCAT("DeleteEvent:", payload_ref_type)
          WHEN type = "PullRequestEvent" THEN CONCAT("PullRequestEvent:", payload_action)
          WHEN type = "IssuesEvent" THEN CONCAT("IssuesEvent:", payload_action)
          WHEN type = "GistEvent" THEN CONCAT("GistEvent:", payload_action)
          WHEN type = "IssueCommentEvent" THEN CONCAT("IssueCommentEvent:", payload_action)
          ELSE type
        END as concated_type,
        FROM
          $dataset 
        GROUP EACH BY
          actor,
          concated_type
      ) subselect_B
    ON
      subselect_B.max_created = subselect_A.created_at
      AND
      subselect_B.actor = subselect_A.actor
)
GROUP BY
  concated_type

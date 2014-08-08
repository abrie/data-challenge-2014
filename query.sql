SELECT
  previous, present,
  COUNT(*) occurances,
  RATIO_TO_REPORT( occurances ) OVER( PARTITION BY previous ),
FROM(
  SELECT
    HASH(repository_url) as url_hash,
    CASE
      WHEN type = "CreateEvent" THEN payload_ref_type
      ELSE type
    END as present,
  PARSE_UTC_USEC(created_at) as time,
  LAG(
    CASE
      WHEN type = "CreateEvent" THEN payload_ref_type
      ELSE type
    END,1,'~'
  ) OVER (PARTITION BY url_hash ORDER BY time ASC) previous,
  FROM
    [publicdata:samples.github_timeline]
    //[githubarchive:github.timeline],
    //[githubarchive:github.2011]
  WHERE
    repository_url IS NOT NULL
    //AND
    //ABS( HASH(repository_url) % 6 ) = 0
)
GROUP EACH BY
  present, previous

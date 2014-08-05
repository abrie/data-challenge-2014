SELECT
preceeding_type, type,
COUNT(*) as total,
RATIO_TO_REPORT(total) OVER() as ratio,
FROM(
SELECT
repository_url,
CASE
WHEN type = "CreateEvent" THEN payload_ref_type
ELSE type
END as type,
LAG(type, 1, '~') OVER (PARTITION BY repository_url ORDER BY time ASC) as preceeding_type,
PARSE_UTC_USEC(created_at) as time,
FROM
//[githubarchive:github.timeline] as t1
[publicdata:samples.github_timeline] as t1
INNER JOIN(
SELECT
r_url,
FROM(
SELECT
repository_url as r_url,
COUNT(repository_url) as r_count,
FROM
//[githubarchive:github.timeline]
[publicdata:samples.github_timeline]
WHERE
repository_url IS NOT NULL
GROUP EACH BY
r_url
)
WHERE
r_count > 1000 AND
r_count < 2000
) as t2
ON
t1.repository_url = t2.r_url
ORDER BY
repository_url, time
)
GROUP EACH BY
type, preceeding_type
ORDER BY
ratio DESC

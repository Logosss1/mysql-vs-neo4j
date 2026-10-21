"""Examples of the same searches in MySQL and Neo4j."""
MYSQL_EXAMPLES = """-- Example 1: find suggested phishing videos for older adults (2 records).
SELECT r.id, r.title
FROM resource r
JOIN resource_topic rt ON rt.resource_id = r.id
JOIN resource_format rf ON rf.resource_id = r.id
JOIN resource_audience ra ON ra.resource_id = r.id
WHERE rt.topic_id = 'phishing' AND rf.format_id = 'video'
  AND ra.audience_id = 'older_adults'
  AND rt.review_status <> 'rejected' AND ra.review_status <> 'rejected'
ORDER BY r.id;

-- Example 2: find resources that share suggested topics with r034.
SELECT candidate.id, candidate.title, COUNT(*) AS shared_topics
FROM resource_topic seed
JOIN resource_topic other ON other.topic_id = seed.topic_id
JOIN resource candidate ON candidate.id = other.resource_id
WHERE seed.resource_id = 'r034' AND other.resource_id <> seed.resource_id
  AND seed.review_status <> 'rejected' AND other.review_status <> 'rejected'
GROUP BY candidate.id, candidate.title ORDER BY shared_topics DESC, candidate.id;

-- Example 3: count resources for each topic, including topics with none.
SELECT t.id, t.name, COUNT(rt.resource_id) AS resource_count
FROM topic t LEFT JOIN resource_topic rt
  ON rt.topic_id = t.id AND rt.review_status <> 'rejected'
GROUP BY t.id, t.name ORDER BY resource_count, t.id;

-- Example 4: show both citations and their access dates.
SELECT id, source_category, page_start, page_end, retrieved_on, citation_raw
FROM source_mention WHERE resource_id = 'r022' ORDER BY id;

-- Example 5: list source problems that need review.
SELECT m.resource_id, q.issue_code, m.page_start, q.detail
FROM quality_issue q JOIN source_mention m ON m.id = q.mention_id
WHERE q.review_status = 'open' ORDER BY m.resource_id, q.issue_code;

-- Example 6: search by word. Each database ranks results differently.
SELECT id, title, MATCH(title, citation_text) AGAINST ('phishing') AS score
FROM resource WHERE MATCH(title, citation_text) AGAINST ('phishing')
ORDER BY score DESC, id;

-- Example 7: list possible duplicates for review before merging.
SELECT from_resource_id, to_resource_id, evidence, review_status
FROM resource_relation WHERE relation_kind = 'possible_same_work';
"""

NEO4J_EXAMPLES = """// Example 1: find suggested phishing videos for older adults (2 records).
MATCH (r:Resource)-[rt:ABOUT]->(:Topic {id: 'phishing'}),
      (r)-[:HAS_FORMAT]->(:Format {id: 'video'}),
      (r)-[ra:FOR_AUDIENCE]->(:Audience {id: 'older_adults'})
WHERE rt.review_status <> 'rejected' AND ra.review_status <> 'rejected'
RETURN r.id AS id, r.title AS title ORDER BY id;

// Example 2: find resources that share suggested topics with r034.
MATCH (:Resource {id: 'r034'})-[seed:ABOUT]->(t:Topic)<-[other:ABOUT]-(candidate:Resource)
WHERE candidate.id <> 'r034' AND seed.review_status <> 'rejected' AND other.review_status <> 'rejected'
RETURN candidate.id AS id, candidate.title AS title, count(t) AS shared_topics
ORDER BY shared_topics DESC, id;

// Example 3: count resources for each topic, including topics with none.
MATCH (t:Topic)
OPTIONAL MATCH (r:Resource)-[rt:ABOUT]->(t) WHERE rt.review_status <> 'rejected'
RETURN t.id AS id, t.name AS name, count(r) AS resource_count ORDER BY resource_count, id;

// Example 4: show both citations and their access dates.
MATCH (s:SourceDocument)-[:HAS_MENTION]->(m:Mention)-[:REFERS_TO]->(:Resource {id: 'r022'})
RETURN m.id, m.source_category, m.page_start, m.page_end, m.retrieved_on, m.citation_raw
ORDER BY m.id;

// Example 5: list source problems that need review.
MATCH (m:Mention)-[:REFERS_TO]->(r:Resource), (m)-[:HAS_ISSUE]->(q:QualityIssue)
WHERE q.review_status = 'open'
RETURN r.id, q.issue_code, m.page_start, q.detail ORDER BY r.id, q.issue_code;

// Example 6: search by word. Each database ranks results differently.
CALL db.index.fulltext.queryNodes('resource_search', 'phishing') YIELD node, score
RETURN node.id AS id, node.title AS title, score ORDER BY score DESC, id;

// Example 7: list possible duplicates for review before merging.
MATCH (a:Resource)-[r:POSSIBLE_SAME_WORK]->(b:Resource)
RETURN a.id, b.id, r.evidence, r.review_status;

// Find topics, contributors, and resources connected to r034 within two steps.
MATCH path = (:Resource {id: 'r034'})-[:ABOUT|CREDITED_TO*1..2]-(neighbor)
RETURN path LIMIT 50;
"""

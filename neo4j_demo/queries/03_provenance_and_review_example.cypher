MATCH p = (b:ImportBatch)-[:IMPORTS_SOURCE]->(s:SourceDocument)
  -[:HAS_MENTION]->(m:Mention {id: 'bib-08'})-[:REFERS_TO]->(r:Resource)
OPTIONAL MATCH i = (m)-[:HAS_ISSUE]->(:QualityIssue)
OPTIONAL MATCH n = (s)-[:STATES]->(:PlanningStatement {id: 'plan-audiences'})
RETURN p, i, n;

MATCH p = (r1:Resource)-[:HAS_RESOURCE_LINK]->
  (link:ResourceLink {id: 'rel001'})-[:TARGETS_RESOURCE]->(r2:Resource)
MATCH e1 = (link)-[:FROM_EVIDENCE]->(m1:Mention)
MATCH e2 = (link)-[:TO_EVIDENCE]->(m2:Mention)
MATCH c1 = (m1)-[:REFERS_TO]->(r1)
MATCH c2 = (m2)-[:REFERS_TO]->(r2)
RETURN p, e1, e2, c1, c2;

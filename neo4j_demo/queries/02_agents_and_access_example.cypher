MATCH p = (r:Resource {id: 'r010'})
  -[:HAS_CONTRIBUTION]->(c:Contribution)-[:CREDITS_AGENT]->(a:Agent)
MATCH e = (c)-[:EVIDENCED_BY]->(m:Mention)
MATCH i = (r)-[:HAS_IDENTIFIER]->(identifier:Identifier)
MATCH f = (identifier)-[:EVIDENCED_BY]->(m)
RETURN p, e, i, f;

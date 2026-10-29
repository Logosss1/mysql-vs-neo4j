MATCH p = (s:SourceDocument)-[:STATES]->(d:AgeDefinition)
  -[:DEFINES_AUDIENCE]->(a:Audience {id: 'older_adults'})
MATCH v = (s)-[:STATES]->(:Topic {id: 'phishing'})
MATCH u = (s)-[:STATES]->(a)
RETURN p, v, u;

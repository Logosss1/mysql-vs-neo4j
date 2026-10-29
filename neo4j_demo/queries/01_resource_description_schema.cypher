CALL db.schema.visualization()
YIELD nodes, relationships
WITH [n IN nodes WHERE labels(n)[0] IN [
    'Resource',
    'TopicAssignment',
    'Topic',
    'AudienceAssignment',
    'Audience',
    'FormatAssignment',
    'Format',
    'Mention'
]] AS nodes, relationships
RETURN nodes,
  [r IN relationships
   WHERE startNode(r) IN nodes AND endNode(r) IN nodes
  ] AS relationships;

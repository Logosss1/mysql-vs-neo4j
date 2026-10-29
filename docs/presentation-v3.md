# V3 English presentation walkthrough

Follow the homepage from the overview through all five parts, then close with the database choice. The catalog examples run in the existing database. The content diagram describes the proposed extension.

For each example, paste the query into Neo4j Browser, click Run, select Graph, and use Zoom to fit. Click a node or arrow to inspect its properties.

## Opening and overview

**Point and operate:** Point to the 49 resources and 50 citation occurrences, then trace SourceDocument, Mention, and Resource in the reading map.

**Say:**

> Building on Zong-Hua's MySQL demo, I'll show how Neo4j organizes the same catalog. We have 49 resource records and 50 citation occurrences from the original resource list. One resource appears twice, so both citations are preserved. The source document identifies the original list. Each mention keeps a citation and its page location, and points to the corresponding resource. The V3 design connects these catalog records with their evidence and a proposed content layer.

## 1 Resource descriptions and classification

**Point and operate:** Point to r034, then its topic, audience, and format branches. Run the example and select TopicAssignment to show basis, review_status, and source_mention_id.

**Say:**

> A resource can have several descriptions: its topic, intended audience, and format. Each assignment records a specific classification and the evidence used for it. Here, r034 is tagged as a phishing video for older adults. The topic assignment is based on citation video-02 and has proposed status. A catalog maintainer can return to that citation and review the classification. Keeping the assignment as a record lets us inspect the reason for the label.

[Query file](../neo4j_demo/queries/01_resource_description_example.cypher)

```cypher
MATCH p = (r:Resource {id: 'r034'})
  -[:HAS_TOPIC_ASSIGNMENT|HAS_AUDIENCE_ASSIGNMENT|HAS_FORMAT_ASSIGNMENT]->(a)
  -[:ASSIGNS_TOPIC|ASSIGNS_AUDIENCE|ASSIGNS_FORMAT]->(term)
MATCH e = (a)-[:EVIDENCED_BY]->(m:Mention)
RETURN p, e;
```

## 2 People organizations and access

**Point and operate:** Run the r010 example. Follow Resource through Contribution to the FBI, then select Contribution and Identifier.

**Say:**

> An agent can be a person or an organization. The contribution record tells us their role for a particular resource, such as creator or publisher. In r010, the FBI is recorded as the creator, supported by citation bib-10. The identifier stores the resource address. This separates who contributed to the resource from how we access it, while keeping the citation evidence for both.

[Query file](../neo4j_demo/queries/02_agents_and_access_example.cypher)

```cypher
MATCH p = (r:Resource {id: 'r010'})
  -[:HAS_CONTRIBUTION]->(c:Contribution)-[:CREDITS_AGENT]->(a:Agent)
MATCH e = (c)-[:EVIDENCED_BY]->(m:Mention)
MATCH i = (r)-[:HAS_IDENTIFIER]->(identifier:Identifier)
MATCH f = (identifier)-[:EVIDENCED_BY]->(m)
RETURN p, e, i, f;
```

## 3 Sources imports and review

**Point and operate:** Trace ImportBatch to SourceDocument to bib-08 and r008. Select the two QualityIssue nodes and the source planning statement.

**Say:**

> This path traces a record back to its source. The import batch identifies the data snapshot, the source document identifies the file, and the mention preserves the citation and page. For bib-08, the catalog records issues involving missing access information and format details that need checking. Maintainers can inspect the source and update those issues. Planning statements preserve the collection goals and audience notes. Classification review, resource verification, and suitability for older adults are separate decisions.

[Query file](../neo4j_demo/queries/03_provenance_and_review_example.cypher)

```cypher
MATCH p = (b:ImportBatch)-[:IMPORTS_SOURCE]->(s:SourceDocument)
  -[:HAS_MENTION]->(m:Mention {id: 'bib-08'})-[:REFERS_TO]->(r:Resource)
OPTIONAL MATCH i = (m)-[:HAS_ISSUE]->(:QualityIssue)
OPTIONAL MATCH n = (s)-[:STATES]->(:PlanningStatement {id: 'plan-audiences'})
RETURN p, i, n;
```

## 4 Vocabulary and age definitions

**Point and operate:** Run the age example. Point to the source, Phishing, Older adults, and the four AgeDefinition nodes. Inspect minimum_age, comparison_operator, evidence, and review_status.

**Say:**

> Topics and audiences use shared vocabulary, so resources can be grouped consistently. The terms come from the source planning text and additions made during catalog curation. Age definitions retain the original wording. Here, four conditions point to older adults: 55 and above, 60 and above, 65 and above, and over 65. They remain unresolved for team review. Storing the operator separately preserves the distinction between 65 and above and over 65.

[Query file](../neo4j_demo/queries/04_vocabulary_and_age_example.cypher)

```cypher
MATCH p = (s:SourceDocument)-[:STATES]->(d:AgeDefinition)
  -[:DEFINES_AUDIENCE]->(a:Audience {id: 'older_adults'})
MATCH v = (s)-[:STATES]->(:Topic {id: 'phishing'})
MATCH u = (s)-[:STATES]->(a)
RETURN p, v, u;
```

## 5 Resource connections and content knowledge

**Point and operate:** Run rel001. Point to r031, ResourceLink, r043, bib-31, and video-11. Then return to the content-connections diagram in the same section.

**Say:**

> A resource link records an association and its reason. Here, r031 and r043 may describe the same talk because the title and speaker match, while the dates and platforms differ. Both citation records remain available for review. This proposed association already exists in the JSON, and the importer connects its IDs.

> The next part of V3 extends these connections into the resource content. EvidenceSpan would preserve an exact passage and its location. KnowledgeAssertion would record a statement drawn from that passage. Shared concepts would connect related statements across sources. This would let us ask which sources describe a scam tactic, what actions they recommend, and where the evidence appears. Our next discussion is to select one question and a small set of source materials.

[Query file](../neo4j_demo/queries/05_resource_links_example.cypher)

```cypher
MATCH p = (r1:Resource)-[:HAS_RESOURCE_LINK]->
  (link:ResourceLink {id: 'rel001'})-[:TARGETS_RESOURCE]->(r2:Resource)
MATCH e1 = (link)-[:FROM_EVIDENCE]->(m1:Mention)
MATCH e2 = (link)-[:TO_EVIDENCE]->(m2:Mention)
MATCH c1 = (m1)-[:REFERS_TO]->(r1)
MATCH c2 = (m2)-[:REFERS_TO]->(r2)
RETURN p, e1, e2, c1, c2;
```

## Closing and database choice

**Point and operate:** Return to Database choice for this catalog.

**Say:**

> MySQL remains our preferred starting point for catalog entry, filtering, counts, and review, and we already have Zong-Hua's prototype to build on. Neo4j makes the relationships and supporting paths easier to inspect. The content example will help us decide whether we have useful graph queries that justify maintaining a graph database. For now, the catalog is running, and the content layer is the design work to discuss next.


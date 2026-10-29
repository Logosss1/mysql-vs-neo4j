# V3 English presentation walkthrough

Use the opening schema slide, then follow the GitHub homepage from the overview and reading map through all five parts, Content connections, and the database choice. Each **Say** paragraph corresponds to the area named immediately above it.

The overview and Parts 1–4 show node types. Part 5 shows the individual records for `rel001`. Read the type views to explain the structure, and open a linked real-record example to inspect properties. For a short live demo, run the Part 5 query after explaining its figure.

In Neo4j Browser, paste one query, click **Run**, select **Graph**, and use **Zoom to fit**. Drag nodes to separate branches. Click real nodes or arrows to inspect their properties.

## Before opening GitHub: the V3 schema slide

**Point:** Trace the top path, SourceDocument → Mention → Resource.

**Say:**

> Across the top, each Mention preserves a citation and its page location in the original SourceDocument. The catalog has 50 citation occurrences linked to 49 resources.

**Point:** Move across the four middle groups.

**Say:**

> These groups organize resource descriptions, contributors and access information, source review, and connections between resources. I’ll explain these paths through the five sections in the GitHub README.

**Point:** Move to the dashed area containing EvidenceSpan, KnowledgeAssertion, and Concept.

**Say:**

> The dashed area outlines a proposed content layer connecting exact passages, statements drawn from them, and shared concepts. First, I’ll show how the current catalog stores resource descriptions and their evidence.

## GitHub overview and Simplified reading map

**Point:** Open [Overall graph](../README.md#overall-graph-what-is-stored). Identify the green SourceDocument circle, orange Mention circle, and lime Resource circle. Trace HAS_MENTION and REFERS_TO.

**Say:**

> The source document is the original resource list. Each mention preserves a citation and its page location, then points to the catalog record for that resource.

**Point:** Expand **Simplified reading map**. Start at Resource, then follow its classification, contributor, identifier, and resource-link branches.

**Say:**

> From Resource, the branches lead to classifications, contributors, identifiers, and related resources. These paths organize what the resource is about, who contributed to it, how to access it, and how it connects to other records.

**Point:** Follow Mention → HAS_ISSUE → QualityIssue, then scroll to Part 1.

**Say:**

> Quality issues stay attached to the citation that needs checking. The following sections show these paths in more detail, starting with resource classification.

The “via” arrows in the reading map summarize multi-step paths. The full assignment and evidence paths appear in the section figures. [Overview query](../neo4j_demo/queries/00_overview.cypher).

## 1. How resources are described and classified

**Point:** In the type figure, start at the central lime Resource circle and follow the three assignment branches to Topic, Audience, and Format.

**Say:**

> A resource connects to its topic, intended audience, and format through separate assignment records. Each assignment records how that particular resource was classified.

**Point:** Trace EVIDENCED_BY from the assignments to the orange Mention circle.

**Say:**

> These assignments link back to the citation used as evidence. Topic and audience assignments also keep a review status, so a catalog maintainer can check the classification.

**Transition:**

> The same approach also keeps track of who contributed to a resource and where it can be accessed.

[Query for the displayed type view](../neo4j_demo/queries/01_resource_description_schema.cypher).

<details>
<summary>Optional real-record demo: r034</summary>

Run the [r034 example](../neo4j_demo/queries/01_resource_description_example.cypher). Follow its branches to Phishing, Older adults, and Video. Click TopicAssignment to inspect `basis`, `review_status`, and `source_mention_id`.

> In this example, r034 has a proposed phishing assignment based on citation video-02. A catalog maintainer can return to that citation to review the classification.

```cypher
MATCH p = (r:Resource {id: 'r034'})
  -[:HAS_TOPIC_ASSIGNMENT|HAS_AUDIENCE_ASSIGNMENT|HAS_FORMAT_ASSIGNMENT]->(a)
  -[:ASSIGNS_TOPIC|ASSIGNS_AUDIENCE|ASSIGNS_FORMAT]->(term)
MATCH e = (a)-[:EVIDENCED_BY]->(m:Mention)
RETURN p, e;
```

</details>

## 2. People, organizations, and access

**Point:** From the top Resource circle, follow HAS_CONTRIBUTION to Contribution, then CREDITS_AGENT to Agent.

**Say:**

> Contribution records who is credited and their role, such as creator or publisher. Agent stores the person or organization involved.

**Point:** Follow Resource → HAS_IDENTIFIER → Identifier. Then trace the EVIDENCED_BY arrows from Contribution and Identifier to Mention.

**Say:**

> The other branch stores a URL, DOI, or resource contact number. Both branches retain the citation evidence for those details.

**Transition:**

> Following those citations back brings us to the source, import history, and review issues.

[Query for the displayed type view](../neo4j_demo/queries/02_agents_and_access_schema.cypher).

<details>
<summary>Optional real-record demo: r010 and the FBI</summary>

Run the [r010 example](../neo4j_demo/queries/02_agents_and_access_example.cypher). Follow Resource → Contribution → FBI. Click Contribution to inspect its role, then Identifier for access information.

> For r010, the FBI is recorded as the creator, supported by citation bib-10. The identifier keeps the resource’s access information with its citation evidence.

```cypher
MATCH p = (r:Resource {id: 'r010'})
  -[:HAS_CONTRIBUTION]->(c:Contribution)-[:CREDITS_AGENT]->(a:Agent)
MATCH e = (c)-[:EVIDENCED_BY]->(m:Mention)
MATCH i = (r)-[:HAS_IDENTIFIER]->(identifier:Identifier)
MATCH f = (identifier)-[:EVIDENCED_BY]->(m)
RETURN p, e, i, f;
```

</details>

## 3. Sources, imports, and review issues

**Point:** Trace the type figure from ImportBatch at the top through SourceDocument and Mention to Resource.

**Say:**

> The import batch identifies the imported data snapshot, and SourceDocument identifies the original file. Each Mention preserves a citation occurrence in that file and points to its resource record.

**Point:** Follow Mention → HAS_ISSUE → QualityIssue.

**Say:**

> QualityIssue lets catalog maintainers track problems such as missing access information. They can check the source and update the issue as the record is corrected.

**Point:** Follow SourceDocument → STATES → PlanningStatement.

**Say:**

> PlanningStatement preserves collection goals or audience notes from the source. The source also tells us where some of our vocabulary and age definitions came from.

[Query for the displayed type view](../neo4j_demo/queries/03_provenance_and_review_schema.cypher).

<details>
<summary>Optional real-record demo: bib-08 and its issues</summary>

Run the [bib-08 example](../neo4j_demo/queries/03_provenance_and_review_example.cypher). Trace the source to bib-08 and r008. Click the two QualityIssue records and the source planning statement.

> Citation bib-08 identifies r008 and has two quality issues involving missing access information and format information inferred from the citation. Maintainers can check those details against the source.

```cypher
MATCH p = (b:ImportBatch)-[:IMPORTS_SOURCE]->(s:SourceDocument)
  -[:HAS_MENTION]->(m:Mention {id: 'bib-08'})-[:REFERS_TO]->(r:Resource)
OPTIONAL MATCH i = (m)-[:HAS_ISSUE]->(:QualityIssue)
OPTIONAL MATCH n = (s)-[:STATES]->(:PlanningStatement {id: 'plan-audiences'})
RETURN p, i, n;
```

</details>

## 4. Where terms and age definitions come from

**Point:** From SourceDocument at the top, trace the STATES arrows to Topic and Audience.

**Say:**

> Topic and Audience provide shared terms for describing resources consistently. These arrows preserve the source of those terms.

**Point:** Follow SourceDocument → STATES → AgeDefinition, then DEFINES_AUDIENCE to Audience.

**Say:**

> AgeDefinition links an age condition to the audience it defines. Our catalog keeps four source definitions for older adults separately so the team can review them.

**Transition:**

> So far, we have described individual resources and their sources. The next section connects one resource to another.

[Query for the displayed type view](../neo4j_demo/queries/04_vocabulary_and_age_schema.cypher). The single AgeDefinition circle represents a type; the real-record query below displays four separate records.

<details>
<summary>Optional real-record demo: four age definitions</summary>

Run the [age-definition example](../neo4j_demo/queries/04_vocabulary_and_age_example.cypher). Inspect `minimum_age`, `comparison_operator`, `evidence`, and `review_status` on the four records.

> The source retains four conditions: 55 and above, 60 and above, 65 and above, and over 65. They remain unresolved for team review, with the original wording preserved.

```cypher
MATCH p = (s:SourceDocument)-[:STATES]->(d:AgeDefinition)
  -[:DEFINES_AUDIENCE]->(a:Audience {id: 'older_adults'})
MATCH v = (s)-[:STATES]->(:Topic {id: 'phishing'})
MATCH u = (s)-[:STATES]->(a)
RETURN p, v, u;
```

</details>

## 5. Resource connections

**Point:** In this real-record figure, start at r031 at the top, follow HAS_RESOURCE_LINK to ResourceLink, then TARGETS_RESOURCE to r043 at the bottom.

**Say:**

> This example connects r031 and r043 through a ResourceLink record. It records a proposed same-work association because the title and speaker match, while the dates and platforms differ.

**Point:** Follow FROM_EVIDENCE to bib-31 and TO_EVIDENCE to video-11. Trace each REFERS_TO arrow back to its resource.

**Say:**

> These citation records support the two ends of the association and point back to their respective resources. The association already exists in the JSON; the importer creates these arrows by matching its IDs.

**Run:** Paste the query below into Neo4j Browser, click **Run**, select **Graph**, and use **Zoom to fit**. Click ResourceLink to show `relation_type`, `evidence`, and `review_status`. [Query file](../neo4j_demo/queries/05_resource_links_example.cypher).

```cypher
MATCH p = (r1:Resource)-[:HAS_RESOURCE_LINK]->
  (link:ResourceLink {id: 'rel001'})-[:TARGETS_RESOURCE]->(r2:Resource)
MATCH e1 = (link)-[:FROM_EVIDENCE]->(m1:Mention)
MATCH e2 = (link)-[:TO_EVIDENCE]->(m2:Mention)
MATCH c1 = (m1)-[:REFERS_TO]->(r1)
MATCH c2 = (m2)-[:REFERS_TO]->(r2)
RETURN p, e1, e2, c1, c2;
```

## Content connections

**Point:** Return to [Content connections](../README.md#content-connections). Follow Resource → HAS_EVIDENCE_SPAN → EvidenceSpan in the proposed diagram.

**Say:**

> The proposed content layer moves from catalog descriptions into the resources themselves. EvidenceSpan would preserve an exact passage together with its source version and location.

**Point:** Follow KnowledgeAssertion → SUPPORTED_BY → EvidenceSpan.

**Say:**

> KnowledgeAssertion would record a statement drawn from that passage, together with its context and review status. The supporting passage would remain available for checking.

**Point:** Follow KnowledgeAssertion → USES_CONCEPT → Concept.

**Say:**

> Shared concepts would connect statements about the same scam tactic, communication channel, or response action across resources. This would help us find relevant statements and return the passages supporting them.

## Closing: database choice

**Point:** Scroll to [Database choice for this catalog](../README.md#database-choice-for-this-catalog).

**Say:**

> We currently favor MySQL because catalog entry, filtering, counts, and review fit the existing prototype. Neo4j makes the relationships easier to explore, and a small content example will help us decide whether we need that additional capability.

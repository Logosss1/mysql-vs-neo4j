# Content-layer schema outline

Discussion draft for Yuhao and Zong-Hua, 29 October 2026.

The proposed extension connects resources to exact source passages and reviewable statements. It supports discussion of what the library should answer and which information the catalog needs to retain.

## Relationship to the existing demo

| Version | Purpose | Status |
| --- | --- | --- |
| v1 | Source-preserving catalog graph with assignment nodes | Implemented in the current demo |
| v2 | Compact catalog diagram using relationship properties | Design reference |
| v3 | Content passages, statements, and domain concepts | Preliminary design proposal |

The catalog contains 49 resources and 50 citation occurrences. `SourceDocument` identifies the original resource list. `Mention` in v1, called `Citation` in v2, identifies a citation in that list. `EvidenceSpan` has a separate meaning: a passage inside the resource itself. The content proposal has not been applied to the database.

## Questions guiding the design

1. Which resources describe a particular scam tactic, and where is the supporting passage?
2. Which verification or support actions do those sources recommend, and in what context?
3. Where do resources discuss the same concept, and how do their populations or settings differ?

## Proposed content records

![Proposed content layer](schema/content-layer-outline.svg)

The diagram extends the v2 catalog view. Its arrows are proposed design relationships. It shows how a resource connects to an exact passage, how a statement retains that evidence, and how statements share concepts.

| Record | Purpose | Initial information |
| --- | --- | --- |
| Resource | Existing catalog item | Keep its ID and existing metadata. |
| EvidenceSpan | Exact source text | id, resource_id, source_version, verbatim_text, locator_kind, locator, alignment_status |
| KnowledgeAssertion | A statement drawn from a source | id, statement_type, statement_text, context, origin_method, review_status |
| Concept | A shared domain term | id, kind, label, definition; reuse a Topic ID when the meanings match. |

| Proposed relationship | Meaning |
| --- | --- |
| `Resource → HAS_EVIDENCE_SPAN → EvidenceSpan` | The passage comes from this resource. |
| `KnowledgeAssertion → SUPPORTED_BY → EvidenceSpan` | The statement points to the exact passage used as support. |
| `KnowledgeAssertion → USES_CONCEPT → Concept` | The statement concerns a shared term. A `role` property can distinguish a tactic from a recommended action. |

Candidate concept kinds are scam type, contact channel, manipulation, requested action, and response action. Reuse existing `Topic` IDs when definitions match. The team still needs to agree on vocabulary scope and whether additional kinds belong in the first version.

Preserve the source version on each span. A PDF locator should identify physical page(s) and text position, a webpage locator should identify a paragraph or anchor in a retained version, and a transcript locator should identify its time range. Keep source alignment separate from semantic review. A statement also needs its population, setting, attribution, and qualifications. Statements from different sources can share a concept while retaining separate evidence and context.

## Preparation flow

1. Obtain source content with clear access and retention conditions.
2. Preserve a source version and locate its passages.
3. Enter statements and their concept links.
4. Check the exact passage and the meaning of the statement.
5. Use the reviewed records in search and source-linked answers.

Manual entry can establish the first example. Dedicated `ContentVersion`, `ReviewEvent`, and `ExtractionRun` records belong to the next design pass as version retention, review workflow, and automation become concrete. Review history requirements include reviewer, time, decision, reason, and reversal. Existing catalog classifications, verification states, and review responsibilities keep their current meaning.

## JCDL methods informing this proposal

The methods below inform the outline. The proposed field names are project design choices.

- **P1: [Structured Knowledge Graph for Scholarly Exploration: IR and QA System for ETDs and their Elements](https://doi.org/10.1145/3805696.3846035)**, Chekuri and Fox (2026). Sections 3–4, pp. 3–6; proceedings PDF pp. 109–112. Represent internal document elements and retrieve their context.
- **P2: [From Media Records to Knowledge Graph: Interoperable Ontology Modeling for a Multimodal Martial Arts Archive](https://doi.org/10.1145/3805696.3846056)**, Chen, Hou, and Zhang (2026). Section 3.1, p. 2; proceedings PDF p. 143. Use competency questions to define concepts and relationships.
- **P3: [A Provenance-First Discovery Layer for Research Gaps, Limitations, and Future Directions in ETDs](https://doi.org/10.1145/3805696.3846045)**, Aboelnaga et al. (2026). Sections 3.2–4, pp. 3–4; proceedings PDF pp. 350–351. Keep exact source passages and locations separate from proposed interpretations.
- **P4: [HEXER: An Online Tool for Building, Validating and Exploring Knowledge Graphs from Historical Documents](https://doi.org/10.1145/3805696.3846516)**, Gordea and Cotea (2026). Sections 2.1–2.4, pp. 2–4; proceedings PDF pp. 795–797. Make review decisions inspectable and reversible. Section 2.4 stores the graph in PostgreSQL.

Article-local page numbers and file-order pages refer to the full proceedings supplied by Yuhao. The first paper evaluates a combined QA pipeline. HEXER demonstrates graph curation over PostgreSQL. Database selection remains a workload decision for this project.

## Discussion and files

- [Questions for Zong-Hua](schema-discussion.md)
- [Editable two-slide design](schema/Neo4j_Schema_Outline_v3_Editable.pptx)
- [Two-page English outline and discussion list](schema/Schema_Outline_and_Discussion_EN.docx)
- [Preserved original v2 diagram](schema/Neo4j_Schema_v2_Original.pptx)

This update changes design files only. Runtime schema code, importers, queries, configuration, and catalog data are unchanged. The content diagram has no corresponding database records yet.

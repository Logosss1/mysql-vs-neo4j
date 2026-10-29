# Earlier schema design references

V3 uses the names shown in the current screenshots and working queries. This page preserves earlier compact notation and design files for reference.

| Catalog record or path | Earlier compact notation |
| --- | --- |
| TopicAssignment, AudienceAssignment, FormatAssignment | ABOUT, FOR_AUDIENCE, HAS_FORMAT with basis and citation properties |
| Mention | Citation |
| Resource through Contribution to Agent | Agent CREATED or PUBLISHED Resource |
| Identifier | Locator with Url, Doi, or Phone subtype |
| QualityIssue, PlanningStatement | Issue, Note |
| SourceDocument HAS_MENTION Mention REFERS_TO Resource | SourceDocument HAS_CITATION Citation CITES Resource |
| AgeDefinition DEFINES_AUDIENCE Audience | Audience DEFINED_BY AgeRule |
| ResourceLink | POSSIBLY_SAME_AS or DESCRIBES_SERVICE with evidence properties |

These are alternative representations. Current queries use the catalog labels in the first column. Topic, audience, format, and contribution records retain their own evidence and roles in the unified V3 design.

## Preserved files

- [Original compact catalog diagram](schema/Neo4j_Schema_v2_Original.pptx)
- [Earlier two-slide outline](schema/Neo4j_Schema_Outline_v3_Editable.pptx)
- [Earlier Word outline and discussion list](schema/Schema_Outline_and_Discussion_EN.docx)

The two-slide outline and Word notes predate the unified terminology. Use the [V3 design](schema-design.md) and [English walkthrough](presentation-v3.md) for the current presentation.

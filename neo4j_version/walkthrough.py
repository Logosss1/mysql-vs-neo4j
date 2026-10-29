"""Focused graph views and checks used by the English group-meeting walkthrough."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUERY_DIR = ROOT / "neo4j_demo" / "queries"
PARTS = {
    1: ("Resource descriptions and classification", ["Resource", "TopicAssignment", "Topic", "AudienceAssignment", "Audience", "FormatAssignment", "Format", "Mention"]),
    2: ("People, organizations, and access", ["Resource", "Contribution", "Agent", "Identifier", "Mention"]),
    3: ("Provenance, import, and review issues", ["ImportBatch", "SourceDocument", "Mention", "Resource", "QualityIssue", "PlanningStatement"]),
    4: ("Vocabulary origins and age definitions", ["SourceDocument", "Topic", "Audience", "AgeDefinition"]),
    5: ("Resource-to-resource assertions", ["Resource", "ResourceLink", "Mention"]),
}
STEMS = {
    1: "01_resource_description", 2: "02_agents_and_access",
    3: "03_provenance_and_review", 4: "04_vocabulary_and_age",
    5: "05_resource_links",
}
EXPECTED_SCHEMA_COUNTS = {1: (8, 10), 2: (5, 6), 3: (6, 5), 4: (4, 4), 5: (3, 5)}
EXPECTED_EXAMPLE_IDS = {
    1: {"r034", "phishing", "older_adults", "video", "video-02"},
    2: {"r010", "a017", "bib-10"},
    3: {"vpl1", "bib-08", "r008", "plan-audiences"},
    4: {"vpl1", "older_adults", "phishing", "age1", "age2", "age3", "age4"},
    5: {"r031", "r043", "rel001", "bib-31", "video-11"},
}


def query_file(part: int, view: str = "schema") -> Path:
    return QUERY_DIR / f"{STEMS[part]}_{view}.cypher"


def graph_summary(rows):
    """Count unique graph objects returned as nodes, relationships, lists, or paths."""
    from neo4j.graph import Node, Relationship, Path as GraphPath
    nodes, relationships = {}, {}

    def add(value):
        if isinstance(value, Node):
            nodes[value.element_id] = value
        elif isinstance(value, Relationship):
            relationships[value.element_id] = value
            add(value.start_node)
            add(value.end_node)
        elif isinstance(value, GraphPath):
            for item in value.nodes:
                add(item)
            for item in value.relationships:
                add(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                add(item)
        elif isinstance(value, dict):
            for item in value.values():
                add(item)

    for row in rows:
        add(row)
    return {
        "nodes": len(nodes), "relationships": len(relationships),
        "labels": sorted({label for node in nodes.values() for label in node.labels}),
        "ids": sorted({node["id"] for node in nodes.values() if node.get("id")}),
        "relationship_types": sorted({r.type for r in relationships.values()}),
    }


def verify_views(driver):
    from .database import query
    results = []
    for part, (_, labels) in PARTS.items():
        for view in ("schema", "example"):
            path = query_file(part, view)
            result = graph_summary(query(driver, path.read_text(encoding="utf-8")))
            if view == "schema":
                ok = (result["nodes"], result["relationships"]) == EXPECTED_SCHEMA_COUNTS[part] and set(result["labels"]) == set(labels)
            else:
                ok = EXPECTED_EXAMPLE_IDS[part] <= set(result["ids"])
                if part == 5:
                    ok = ok and (result["nodes"], result["relationships"]) == (5, 6)
            if not ok:
                raise ValueError(f"Unexpected walkthrough result in {path.name}: {result}")
            results.append({"file": path.name, "status": "PASS", **result})
    overview = graph_summary(query(driver, (QUERY_DIR / "00_overview.cypher").read_text(encoding="utf-8")))
    if "CatalogRecord" in overview["labels"] or set(overview["labels"]) != set().union(*(set(p[1]) for p in PARTS.values())):
        raise ValueError("Overview does not match the five-part node inventory.")
    results.insert(0, {"file": "00_overview.cypher", "status": "PASS", **overview})
    return results

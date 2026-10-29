"""Validate the frozen catalog and map every input row into an auditable graph.

No functions from the baseline implementation are used in this module.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path

SOURCE_COMMIT = "37ebfdd0748cb0230459722430c970e1caa5a50e"
CATALOG_SHA256 = "32d4cb61c14e276e508bf805fd1c63ac33bd8cce6397863c8410baba608c957b"

FIELDS = {
    "source_document": "id filename sha256 text_sha256 page_count ingested_on",
    "resource": "id title publication_value publication_precision container_title publisher_statement citation_text verification_status",
    "source_mention": "id resource_id source_id source_category source_position page_start page_end citation_raw retrieved_on",
    "agent": "id name agent_kind identity_status",
    "resource_agent": "resource_id agent_id contribution_role credit_order source_mention_id",
    "format": "id name",
    "resource_format": "resource_id format_id source_mention_id basis",
    "topic": "id name source_id source_page basis",
    "audience": "id name source_id source_page",
    "resource_topic": "resource_id topic_id source_mention_id basis review_status",
    "resource_audience": "resource_id audience_id source_mention_id basis review_status",
    "identifier": "id resource_id identifier_kind identifier_value source_mention_id",
    "quality_issue": "id mention_id issue_code detail review_status",
    "resource_relation": "id from_resource_id to_resource_id relation_kind evidence review_status from_mention_id to_mention_id",
    "planning_statement": "id source_id statement_kind page_start page_end statement_text",
    "age_definition": "id audience_id source_id source_page minimum_age comparison_operator evidence review_status",
}
FIELDS = {name: value.split() for name, value in FIELDS.items()}
LABELS = dict(zip(FIELDS, [
    "SourceDocument", "Resource", "Mention", "Agent", "Contribution", "Format",
    "FormatAssignment", "Topic", "Audience", "TopicAssignment", "AudienceAssignment",
    "Identifier", "QualityIssue", "ResourceLink", "PlanningStatement", "AgeDefinition",
]))
KEYS = {name: ["id"] for name in FIELDS}
KEYS.update({
    "resource_agent": ["resource_id", "contribution_role", "credit_order"],
    "resource_format": ["resource_id", "format_id"],
    "resource_topic": ["resource_id", "topic_id"],
    "resource_audience": ["resource_id", "audience_id"],
})
NULLABLE = {("resource", field) for field in ["publication_value", "container_title", "publisher_statement"]}
NULLABLE.add(("source_mention", "retrieved_on"))
INTEGER_FIELDS = {"page_count", "source_position", "page_start", "page_end", "source_page", "credit_order", "minimum_age"}
ENUMS = {
    ("resource", "verification_status"): {"unverified", "verified", "rejected"},
    ("resource", "publication_precision"): {"unknown", "year", "month", "day"},
    ("agent", "agent_kind"): {"person", "organization"},
    ("resource_agent", "contribution_role"): {"creator", "publisher"},
    ("identifier", "identifier_kind"): {"url", "doi", "phone"},
    ("quality_issue", "review_status"): {"open", "resolved", "dismissed"},
    ("resource_relation", "relation_kind"): {"possible_same_work", "describes_service"},
    ("age_definition", "review_status"): {"unresolved", "approved", "rejected"},
    ("age_definition", "comparison_operator"): {">", ">="},
}
for _name in ["resource_topic", "resource_audience", "resource_relation"]:
    ENUMS[(_name, "review_status")] = {"proposed", "approved", "rejected"}
REFERENCES = {
    "source_mention": {"resource_id": "resource", "source_id": "source_document"},
    "resource_agent": {"resource_id": "resource", "agent_id": "agent", "source_mention_id": "source_mention"},
    "resource_format": {"resource_id": "resource", "format_id": "format", "source_mention_id": "source_mention"},
    "topic": {"source_id": "source_document"},
    "audience": {"source_id": "source_document"},
    "resource_topic": {"resource_id": "resource", "topic_id": "topic", "source_mention_id": "source_mention"},
    "resource_audience": {"resource_id": "resource", "audience_id": "audience", "source_mention_id": "source_mention"},
    "identifier": {"resource_id": "resource", "source_mention_id": "source_mention"},
    "quality_issue": {"mention_id": "source_mention"},
    "resource_relation": {"from_resource_id": "resource", "to_resource_id": "resource", "from_mention_id": "source_mention", "to_mention_id": "source_mention"},
    "planning_statement": {"source_id": "source_document"},
    "age_definition": {"audience_id": "audience", "source_id": "source_document"},
}


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def row_key(table: str, row: dict) -> str:
    return table + ":" + canonical([row[column] for column in KEYS[table]])


def sorted_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=canonical)


def load_snapshot(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CATALOG_SHA256:
        raise ValueError("Snapshot hash differs from the approved baseline. Register a new comparison version first.")
    data = json.loads(raw)
    validate(data)
    return data, digest


def _unique(rows, columns, context):
    values = [tuple(row[column] for column in columns) for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {context}: {columns}")


def validate(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != set(FIELDS):
        raise ValueError("Unexpected or missing catalog tables")
    for table, fields in FIELDS.items():
        if not isinstance(data[table], list):
            raise ValueError(f"Expected row array: {table}")
        for row in data[table]:
            if not isinstance(row, dict) or set(row) != set(fields):
                raise ValueError(f"Unexpected or missing fields: {table}")
            for field in fields:
                value = row[field]
                if value is None and (table, field) in NULLABLE:
                    continue
                if field in INTEGER_FIELDS:
                    if type(value) is not int or value < (0 if field == "minimum_age" else 1):
                        raise ValueError(f"Invalid integer: {table}.{field}")
                elif not isinstance(value, str) or not value.strip():
                    raise ValueError(f"Required text: {table}.{field}")
                allowed = ENUMS.get((table, field))
                if allowed and value not in allowed:
                    raise ValueError(f"Invalid enumeration: {table}.{field}")
        _unique(data[table], KEYS[table], table)
    for table, columns in [
        ("source_document", ["sha256"]), ("source_mention", ["source_id", "source_category", "source_position"]),
        ("format", ["name"]), ("topic", ["name"]), ("audience", ["name"]),
        ("identifier", ["identifier_kind", "identifier_value"]),
        ("resource_agent", ["resource_id", "agent_id", "contribution_role"]),
        ("resource_relation", ["from_resource_id", "to_resource_id", "relation_kind"]),
    ]:
        _unique(data[table], columns, table)
    lookup = {table: {row["id"]: row for row in rows} for table, rows in data.items() if "id" in FIELDS[table]}
    for table, references in REFERENCES.items():
        for row in data[table]:
            for column, target in references.items():
                if row[column] not in lookup[target]:
                    raise ValueError(f"Missing reference: {table}.{column}")
    for table in ["source_mention", "planning_statement", "topic", "audience", "age_definition"]:
        for row in data[table]:
            first = row.get("page_start", row.get("source_page"))
            last = row.get("page_end", first)
            if not 1 <= first <= last <= lookup["source_document"][row["source_id"]]["page_count"]:
                raise ValueError(f"Page outside source document: {table}")
    for table in ["resource_agent", "resource_format", "resource_topic", "resource_audience", "identifier"]:
        for row in data[table]:
            if lookup["source_mention"][row["source_mention_id"]]["resource_id"] != row["resource_id"]:
                raise ValueError(f"Evidence belongs to another resource: {table}")
    for row in data["resource_relation"]:
        if row["from_resource_id"] == row["to_resource_id"]:
            raise ValueError("Self resource link")
        for side in ["from", "to"]:
            if lookup["source_mention"][row[f"{side}_mention_id"]]["resource_id"] != row[f"{side}_resource_id"]:
                raise ValueError("Resource-link evidence mismatch")
    for row in data["resource"]:
        value, precision = row["publication_value"], row["publication_precision"]
        if precision == "unknown":
            if value is not None:
                raise ValueError("Unknown publication date must be null")
        else:
            expected_length = {"year": 4, "month": 7, "day": 10}[precision]
            if value is None or len(value) != expected_length:
                raise ValueError("Invalid publication precision")
            suffix = {"year": "-01-01", "month": "-01", "day": ""}[precision]
            parsed = date.fromisoformat(value + suffix)
            if parsed.isoformat() != value + suffix:
                raise ValueError("Noncanonical publication date")
    for row in data["age_definition"]:
        if row["minimum_age"] > 120:
            raise ValueError("Invalid age bound")
    for table, column in [("source_document", "ingested_on"), ("source_mention", "retrieved_on")]:
        for row in data[table]:
            if row[column] is not None:
                if date.fromisoformat(row[column]).isoformat() != row[column]:
                    raise ValueError("Invalid full date")


def graph_plan(data: dict, digest: str) -> dict:
    validate(data)
    grouped_nodes = {}
    for table, rows in data.items():
        grouped_nodes[LABELS[table]] = [
            {**row, "_key": row_key(table, row), "_table": table, "_snapshot": digest}
            for row in rows
        ]
    by_id = {table: {row["id"]: row for row in rows} for table, rows in data.items() if "id" in FIELDS[table]}
    edges = defaultdict(list)

    def link(source_table, source_row, kind, target_table, target_row):
        edges[kind].append({"a": row_key(source_table, source_row), "b": row_key(target_table, target_row)})

    for row in data["source_mention"]:
        link("source_document", by_id["source_document"][row["source_id"]], "HAS_MENTION", "source_mention", row)
        link("source_mention", row, "REFERS_TO", "resource", by_id["resource"][row["resource_id"]])
    for table, from_type, to_type, target_table, target_field in [
        ("resource_agent", "HAS_CONTRIBUTION", "CREDITS_AGENT", "agent", "agent_id"),
        ("resource_format", "HAS_FORMAT_ASSIGNMENT", "ASSIGNS_FORMAT", "format", "format_id"),
        ("resource_topic", "HAS_TOPIC_ASSIGNMENT", "ASSIGNS_TOPIC", "topic", "topic_id"),
        ("resource_audience", "HAS_AUDIENCE_ASSIGNMENT", "ASSIGNS_AUDIENCE", "audience", "audience_id"),
    ]:
        for row in data[table]:
            link("resource", by_id["resource"][row["resource_id"]], from_type, table, row)
            link(table, row, to_type, target_table, by_id[target_table][row[target_field]])
            link(table, row, "EVIDENCED_BY", "source_mention", by_id["source_mention"][row["source_mention_id"]])
    for row in data["identifier"]:
        link("resource", by_id["resource"][row["resource_id"]], "HAS_IDENTIFIER", "identifier", row)
        link("identifier", row, "EVIDENCED_BY", "source_mention", by_id["source_mention"][row["source_mention_id"]])
    for row in data["quality_issue"]:
        link("source_mention", by_id["source_mention"][row["mention_id"]], "HAS_ISSUE", "quality_issue", row)
    for row in data["resource_relation"]:
        link("resource", by_id["resource"][row["from_resource_id"]], "HAS_RESOURCE_LINK", "resource_relation", row)
        link("resource_relation", row, "TARGETS_RESOURCE", "resource", by_id["resource"][row["to_resource_id"]])
        link("resource_relation", row, "FROM_EVIDENCE", "source_mention", by_id["source_mention"][row["from_mention_id"]])
        link("resource_relation", row, "TO_EVIDENCE", "source_mention", by_id["source_mention"][row["to_mention_id"]])
    for table in ["topic", "audience", "planning_statement", "age_definition"]:
        for row in data[table]:
            link("source_document", by_id["source_document"][row["source_id"]], "STATES", table, row)
            if table == "age_definition":
                link(table, row, "DEFINES_AUDIENCE", "audience", by_id["audience"][row["audience_id"]])
    all_keys = {n["_key"] for rows in grouped_nodes.values() for n in rows}
    for kind, rows in edges.items():
        assert len(rows) == len({(r["a"], r["b"]) for r in rows}), kind
        assert all(r["a"] in all_keys and r["b"] in all_keys for r in rows), kind
    return {"nodes": grouped_nodes, "relationships": dict(edges), "snapshot_sha256": digest,
            "catalog_node_count": len(all_keys), "catalog_relationship_count": sum(map(len, edges.values()))}

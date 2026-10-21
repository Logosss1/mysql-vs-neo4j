"""Build the SQLite demo and MySQL/Neo4j files. Load databases through Docker."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile

from .dataset import ROOT, build_dataset, profile, write_json
from .queries import MYSQL_EXAMPLES, NEO4J_EXAMPLES
from .schema import TABLES, relational_schema


def open_sqlite(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def import_sqlite(connection: sqlite3.Connection, tables: dict) -> None:
    connection.executescript(relational_schema("sqlite"))
    with connection:
        for table in TABLES:
            rows = tables[table.name]
            if not rows:
                continue
            columns = list(rows[0])
            updates = ", ".join(f"{c}=excluded.{c}" for c in columns if c not in table.primary_key)
            sql = (f"INSERT INTO {table.name} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)}) "
                   f"ON CONFLICT ({', '.join(table.primary_key)}) DO UPDATE SET {updates}")
            connection.executemany(sql, [[row[c] for c in columns] for row in rows])
        connection.execute("DELETE FROM resource_fts")
        connection.execute("INSERT INTO resource_fts SELECT id, title, citation_text FROM resource")


def mysql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    # Encode text as UTF-8 hex so quotes and line breaks load safely in MySQL.
    return f"CONVERT(X'{str(value).encode('utf-8').hex()}' USING utf8mb4)"


def mysql_seed(tables: dict) -> str:
    statements = ["SET NAMES utf8mb4;", "START TRANSACTION;"]
    for table in TABLES:
        for row in tables[table.name]:
            columns = list(row)
            values = ", ".join(mysql_literal(row[c]) for c in columns)
            updates = ", ".join(f"{c}=incoming.{c}" for c in columns if c not in table.primary_key)
            statements.append(f"INSERT INTO {table.name} ({', '.join(columns)}) VALUES ({values}) AS incoming "
                              f"ON DUPLICATE KEY UPDATE {updates};")
    statements.append("COMMIT;")
    return "\n".join(statements) + "\n"


NODE_TABLES = {
    "source_document": "SourceDocument", "resource": "Resource", "source_mention": "Mention",
    "agent": "Agent", "format": "Format", "topic": "Topic", "audience": "Audience",
    "identifier": "Identifier", "quality_issue": "QualityIssue", "planning_statement": "PlanningStatement",
    "age_definition": "AgeDefinition",
}


def graph_rows(tables: dict) -> tuple[list, list]:
    """Build graph data for the Neo4j import and tests."""
    nodes, edges = [], []
    for table, label in NODE_TABLES.items():
        nodes.extend({"label": label, "properties": row} for row in tables[table])

    def edge(left_label, left, kind, right_label, right, props=None):
        edges.append({"from_label": left_label, "from_id": left, "type": kind,
                      "to_label": right_label, "to_id": right, "properties": props or {}})

    for m in tables["source_mention"]:
        edge("SourceDocument", m["source_id"], "HAS_MENTION", "Mention", m["id"])
        edge("Mention", m["id"], "REFERS_TO", "Resource", m["resource_id"])
    for row in tables["resource_agent"]:
        edge("Resource", row["resource_id"], "CREDITED_TO", "Agent", row["agent_id"], row)
    for table, relationship, label, key in [
        ("resource_format", "HAS_FORMAT", "Format", "format_id"),
        ("resource_topic", "ABOUT", "Topic", "topic_id"),
        ("resource_audience", "FOR_AUDIENCE", "Audience", "audience_id"),
    ]:
        for row in tables[table]:
            edge("Resource", row["resource_id"], relationship, label, row[key], row)
    for row in tables["identifier"]:
        edge("Resource", row["resource_id"], "HAS_IDENTIFIER", "Identifier", row["id"])
    for row in tables["quality_issue"]:
        edge("Mention", row["mention_id"], "HAS_ISSUE", "QualityIssue", row["id"])
    for row in tables["resource_relation"]:
        edge("Resource", row["from_resource_id"], row["relation_kind"].upper(),
             "Resource", row["to_resource_id"], row)
    for table, label in [("planning_statement", "PlanningStatement"), ("age_definition", "AgeDefinition"),
                         ("topic", "Topic"), ("audience", "Audience")]:
        for row in tables[table]:
            edge("SourceDocument", row["source_id"], "ASSERTS", label, row["id"])
            if table == "age_definition":
                edge(label, row["id"], "DEFINES", "Audience", row["audience_id"])
    return nodes, edges


def cypher_literal(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def cypher_properties(properties: dict) -> str:
    return "{" + ", ".join(f"{key}: {cypher_literal(value)}" for key, value in properties.items()) + "}"


def neo4j_schema() -> str:
    statements = [f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE;"
                  for label in NODE_TABLES.values()]
    statements += [
        "CREATE CONSTRAINT identifier_value IF NOT EXISTS FOR (n:Identifier) REQUIRE (n.identifier_kind, n.identifier_value) IS UNIQUE;",
        "CREATE CONSTRAINT mention_position IF NOT EXISTS FOR (n:Mention) REQUIRE (n.source_id, n.source_category, n.source_position) IS UNIQUE;",
        "CREATE INDEX resource_publication IF NOT EXISTS FOR (r:Resource) ON (r.publication_value);",
        "CREATE INDEX quality_queue IF NOT EXISTS FOR (q:QualityIssue) ON (q.review_status, q.issue_code);",
        "CREATE FULLTEXT INDEX resource_search IF NOT EXISTS FOR (r:Resource) ON EACH [r.title, r.citation_text];",
    ]
    return "\n".join(statements) + "\n"


def neo4j_seed(tables: dict) -> str:
    nodes, edges = graph_rows(tables)
    statements = ["// Load sample data with standard Cypher 5. No plugins needed.", ":begin"]
    for node in nodes:
        props = node["properties"]
        statements.append(f"MERGE (n:{node['label']} {{id: {cypher_literal(props['id'])}}}) "
                          f"SET n = {cypher_properties(props)};")
    for edge in edges:
        props = edge["properties"]
        # Include the role so one contributor can be both creator and publisher.
        identity = {"contribution_role": props["contribution_role"]} if edge["type"] == "CREDITED_TO" else {}
        statements.append(
            f"MATCH (a:{edge['from_label']} {{id: {cypher_literal(edge['from_id'])}}}), "
            f"(b:{edge['to_label']} {{id: {cypher_literal(edge['to_id'])}}}) "
            f"MERGE (a)-[r:{edge['type']} {cypher_properties(identity)}]->(b) "
            f"SET r = {cypher_properties(props)};")
    statements.append(":commit")
    return "\n".join(statements) + "\n"


def export(root: Path = ROOT) -> dict:
    tables = build_dataset(root)
    output = root / "build"
    output.mkdir(exist_ok=True)
    write_json(root / "data/catalog.json", tables)
    report = profile(tables)
    nodes, edges = graph_rows(tables)
    report.update(graph_nodes=len(nodes), graph_relationships=len(edges))
    write_json(root / "data/profile.json", report)
    write_json(output / "graph.json", {"nodes": nodes, "relationships": edges})
    (output / "mysql_schema.sql").write_text(relational_schema("mysql"), encoding="utf-8")
    (output / "mysql_seed.sql").write_text(mysql_seed(tables), encoding="utf-8")
    (output / "neo4j_schema.cypher").write_text(neo4j_schema(), encoding="utf-8")
    (output / "neo4j_seed.cypher").write_text(neo4j_seed(tables), encoding="utf-8")
    (output / "mysql_queries.sql").write_text(MYSQL_EXAMPLES, encoding="utf-8")
    (output / "neo4j_queries.cypher").write_text(NEO4J_EXAMPLES, encoding="utf-8")
    # Build a new demo file first. Replace the old file only after success.
    with tempfile.TemporaryDirectory(dir=output) as staging:
        staged_db = Path(staging) / "catalog.sqlite3"
        connection = open_sqlite(staged_db)
        try:
            import_sqlite(connection, tables)
        finally:
            connection.close()
        staged_db.replace(output / "catalog.sqlite3")
    return report


def docker_command(backend: str) -> list[str]:
    if backend == "mysql":
        shell = ('MYSQL_PWD="$MYSQL_PASSWORD" exec mysql --default-character-set=utf8mb4 '
                 '--user="$MYSQL_USER" "$MYSQL_DATABASE"')
    elif backend == "neo4j":
        shell = 'exec cypher-shell -u neo4j -p "${NEO4J_AUTH#*/}" -d neo4j --format plain'
    else:
        raise ValueError(backend)
    return ["docker", "compose", "exec", "-T", backend, "sh", "-c", shell]


def run_native(backend: str, query: str) -> str:
    result = subprocess.run(docker_command(backend), input=query.encode("utf-8"),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or "Database command failed")
    return result.stdout.decode("utf-8", errors="replace")


def load_native(backend: str) -> str:
    export()
    suffix = "sql" if backend == "mysql" else "cypher"
    output = ROOT / "build"
    # Create tables or graph rules first, then load the data.
    result = run_native(backend, (output / f"{backend}_schema.{suffix}").read_text(encoding="utf-8"))
    result += run_native(backend, (output / f"{backend}_seed.{suffix}").read_text(encoding="utf-8"))
    return result

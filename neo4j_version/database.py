"""Driver access and an explicit, source-preserving import into an empty database."""
from __future__ import annotations

from datetime import datetime, timezone
import os

from neo4j import GraphDatabase, READ_ACCESS, WRITE_ACCESS

from .model import FIELDS, LABELS, SOURCE_COMMIT, graph_plan, sorted_rows


def connect(password: str | None = None):
    password = password or os.getenv("NEO4J_PASSWORD")
    if not password:
        raise ValueError("Set NEO4J_PASSWORD or enter it at the CLI password prompt.")
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://127.0.0.1:17687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), password),
        connection_timeout=15,
        max_transaction_retry_time=15,
    )


def query(driver, cypher, parameters=None, *, write=False):
    with driver.session(
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
        default_access_mode=WRITE_ACCESS if write else READ_ACCESS,
    ) as session:
        return [dict(record) for record in session.run(cypher, parameters or {})]


def schema_statements():
    statements = [
        "CREATE CONSTRAINT yuhao_record_key IF NOT EXISTS FOR (n:CatalogRecord) REQUIRE n._key IS UNIQUE",
        "CREATE CONSTRAINT yuhao_import_hash IF NOT EXISTS FOR (n:ImportBatch) REQUIRE n.id IS UNIQUE",
    ]
    for table, fields in FIELDS.items():
        if "id" in fields:
            statements.append(
                f"CREATE CONSTRAINT yuhao_{table}_id IF NOT EXISTS "
                f"FOR (n:{LABELS[table]}) REQUIRE n.id IS UNIQUE"
            )
    for label, field in [("SourceDocument", "sha256"), ("Topic", "name"), ("Audience", "name"), ("Format", "name")]:
        statements.append(
            f"CREATE CONSTRAINT yuhao_{label.lower()}_{field} IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.{field} IS UNIQUE"
        )
    return statements + [
        "CREATE CONSTRAINT yuhao_identifier_value IF NOT EXISTS FOR (n:Identifier) REQUIRE (n.identifier_kind,n.identifier_value) IS UNIQUE",
        "CREATE INDEX yuhao_resource_date IF NOT EXISTS FOR (n:Resource) ON (n.publication_value)",
        "CREATE INDEX yuhao_issue_state IF NOT EXISTS FOR (n:QualityIssue) ON (n.review_status)",
        "CREATE FULLTEXT INDEX yuhao_resource_text IF NOT EXISTS FOR (n:Resource) ON EACH [n.title,n.citation_text]",
    ]


def verify_snapshot(driver, data, plan):
    rows = query(driver, "MATCH (n:CatalogRecord) RETURN properties(n) AS props")
    actual = {name: [] for name in FIELDS}
    for item in rows:
        props = item["props"]
        table = props.get("_table")
        if table not in FIELDS or props.get("_snapshot") != plan["snapshot_sha256"]:
            raise ValueError("Graph contains a different schema or data snapshot.")
        actual[table].append({field: props.get(field) for field in FIELDS[table]})
    for table in FIELDS:
        if sorted_rows(actual[table]) != sorted_rows(data[table]):
            raise ValueError(f"Stored records differ from the source snapshot: {table}")
    actual_edges = query(
        driver,
        "MATCH (a:CatalogRecord)-[r]->(b:CatalogRecord) "
        "RETURN a._key AS a,type(r) AS kind,b._key AS b",
    )
    expected = [(row["a"], kind, row["b"]) for kind, rows in plan["relationships"].items() for row in rows]
    if sorted((r["a"], r["kind"], r["b"]) for r in actual_edges) != sorted(expected):
        raise ValueError("Stored relationships differ from the source snapshot.")
    batches = query(driver, "MATCH (b:ImportBatch) RETURN b.id AS id")
    if batches != [{"id": plan["snapshot_sha256"]}]:
        raise ValueError("Expected one matching import batch.")
    totals = query(driver, "MATCH (n) RETURN count(n) AS nodes")[0]
    edge_total = query(driver, "MATCH ()-[r]->() RETURN count(r) AS relationships")[0]
    imports = query(driver, "MATCH (b:ImportBatch)-[:IMPORTS_SOURCE]->(s:SourceDocument) RETURN b.id AS batch,s.id AS source")
    expected_imports = sorted((plan["snapshot_sha256"], row["id"]) for row in data["source_document"])
    if sorted((r["batch"], r["source"]) for r in imports) != expected_imports:
        raise ValueError("Import provenance differs from the source snapshot.")
    if totals["nodes"] != plan["catalog_node_count"] + 1 or edge_total["relationships"] != plan["catalog_relationship_count"] + len(expected_imports):
        raise ValueError("Database contains additional nodes or relationships.")
    return {
        "source_arrays_verified": len(data),
        "catalog_records_verified": len(rows),
        "catalog_relationships_verified": len(actual_edges),
        **totals, **edge_total,
    }


def load(driver, data, digest):
    """Load an empty isolated database, or verify an already matching snapshot."""
    plan = graph_plan(data, digest)
    batches = query(driver, "MATCH (b:ImportBatch) RETURN b.id AS id")
    if batches:
        if batches != [{"id": digest}]:
            raise ValueError("Another snapshot is present; use a separate empty database.")
        return {"action": "verified_no_op", **verify_snapshot(driver, data, plan)}
    if query(driver, "MATCH (n) RETURN count(n) AS count")[0]["count"]:
        raise ValueError("Database is not empty; no import or schema change was made.")
    # Check the target before creating constraints or writing any records.
    for statement in schema_statements():
        query(driver, statement, write=True)
    with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j"), default_access_mode=WRITE_ACCESS) as session:
        with session.begin_transaction() as tx:
            if tx.run("MATCH (n) RETURN count(n) AS n").single()["n"]:
                raise ValueError("Target changed during preparation; import cancelled.")
            for label, rows in plan["nodes"].items():
                tx.run(f"UNWIND $rows AS row CREATE (n:CatalogRecord:{label}) SET n = row", rows=rows).consume()
            for kind, rows in plan["relationships"].items():
                created = tx.run(
                    f"UNWIND $rows AS row MATCH (a:CatalogRecord {{_key:row.a}}),(b:CatalogRecord {{_key:row.b}}) "
                    f"CREATE (a)-[:{kind}]->(b) RETURN count(*) AS n", rows=rows,
                ).single()["n"]
                if created != len(rows):
                    raise ValueError(f"Missing relationship endpoint: {kind}")
            tx.run(
                "CREATE (:ImportBatch {id:$digest, source_commit:$commit, imported_at:$time, catalog_rows:$rows})",
                digest=digest, commit=SOURCE_COMMIT, time=datetime.now(timezone.utc).isoformat(), rows=plan["catalog_node_count"],
            ).consume()
            tx.run(
                "MATCH (b:ImportBatch {id:$digest}),(s:SourceDocument) CREATE (b)-[:IMPORTS_SOURCE]->(s)",
                digest=digest,
            ).consume()
            tx.commit()
    query(driver, "CALL db.awaitIndexes(60)")
    return {"action": "imported", **verify_snapshot(driver, data, plan)}

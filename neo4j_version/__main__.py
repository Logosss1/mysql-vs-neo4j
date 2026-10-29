"""CLI for the independent v1 graph. Run from the repository root."""
from __future__ import annotations

import argparse
import getpass
import importlib.metadata
import json
import os
from pathlib import Path
import sys

from .model import SOURCE_COMMIT, graph_plan, load_snapshot, sorted_rows
from .queries import QUERIES, oracle
from .walkthrough import ROOT, PARTS, query_file, verify_views


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate the checked-in catalog without a database")
    sub.add_parser("load", help="Explicitly import into an empty isolated database, or verify a matching import")
    verify = sub.add_parser("verify", help="Read-only snapshot, catalog-question, and walkthrough checks")
    verify.add_argument("--output", type=Path, help="Optional JSON report path")
    show = sub.add_parser("show", help="Print a part's Cypher for pasting into Neo4j Browser")
    show.add_argument("part", type=int, choices=PARTS)
    show.add_argument("--view", choices=("schema", "example"), default="schema")
    question = sub.add_parser("query", help="Run an existing catalog question; IDs are lookup keys")
    question.add_argument("id", choices=[q["id"] for q in QUERIES])
    args = parser.parse_args(argv)
    if args.command == "show":
        print(query_file(args.part, args.view).read_text(encoding="utf-8"))
        return 0
    data, digest = load_snapshot(ROOT / "data" / "catalog.json")
    plan = graph_plan(data, digest)
    if args.command == "validate":
        print(json.dumps({"status": "PASS", "snapshot_sha256": digest, "source_commit": SOURCE_COMMIT,
                          "source_arrays": len(data), "resources": len(data["resource"]),
                          "mentions": len(data["source_mention"]), "catalog_nodes": plan["catalog_node_count"],
                          "catalog_relationships": plan["catalog_relationship_count"]}, indent=2))
        return 0
    from .database import connect, load, query, verify_snapshot
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        if not sys.stdin.isatty():
            parser.error("Set NEO4J_PASSWORD for a non-interactive run.")
        password = getpass.getpass("Neo4j password: ")
    with connect(password) as driver:
        driver.verify_connectivity()
        if args.command == "load":
            print(json.dumps(load(driver, data, digest), indent=2))
            return 0
        if args.command == "query":
            item = next(q for q in QUERIES if q["id"] == args.id)
            print(item["question"])
            print(json.dumps(sorted_rows(query(driver, item["neo4j"], item["parameters"])), ensure_ascii=False, indent=2))
            return 0
        snapshot = verify_snapshot(driver, data, plan)
        expected = oracle(data)
        checks = []
        for item in QUERIES:
            rows = sorted_rows(query(driver, item["neo4j"], item["parameters"]))
            if rows != sorted_rows(expected[item["id"]]):
                raise ValueError(f"Catalog question differs from JSON oracle: {item['id']}")
            checks.append({"id": item["id"], "question": item["question"], "rows": len(rows), "status": "PASS"})
        views = verify_views(driver)
        components = query(driver, "CALL dbms.components() YIELD name,versions,edition RETURN name,versions,edition")
        report = {"status": "PASS", "model": "v1_explicit_assignment_nodes", "source_commit": SOURCE_COMMIT,
                  "snapshot_sha256": digest, "driver_version": importlib.metadata.version("neo4j"),
                  "server": components, "snapshot": snapshot, "catalog_questions": checks, "walkthrough_queries": views}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)

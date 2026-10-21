"""Run with python -m elder_catalog. No extra Python packages needed."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys

from .dataset import ROOT, build_dataset, profile
from .storage import export, load_native, open_sqlite


def print_json(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def search(connection, text=None, topic=None, format_id=None, audience=None, limit=50):
    clauses, params = [], []
    for value, table, key in [(topic, "resource_topic", "topic_id"),
                              (format_id, "resource_format", "format_id"),
                              (audience, "resource_audience", "audience_id")]:
        if value:
            reviewed = " AND tag.review_status <> 'rejected'" if table != "resource_format" else ""
            clauses.append(f"EXISTS (SELECT 1 FROM {table} tag WHERE tag.resource_id=r.id AND tag.{key}=?{reviewed})")
            params.append(value)
    if text:
        # Search the user's words as plain text.
        words = re.findall(r"\w+", text, flags=re.UNICODE)
        if not words:
            return []
        clauses.append("r.id IN (SELECT resource_id FROM resource_fts WHERE resource_fts MATCH ?)")
        params.append(" AND ".join('"' + w + '"' for w in words))
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    sql = ("SELECT r.id, r.title, r.publication_value, r.verification_status FROM resource r" + where
           + " ORDER BY r.id LIMIT ?")
    return [dict(row) for row in connection.execute(sql, params)]


def related(connection, resource_id):
    sql = """SELECT r.id, r.title, COUNT(*) AS shared_topics
             FROM resource_topic seed JOIN resource_topic other ON other.topic_id=seed.topic_id
             JOIN resource r ON r.id=other.resource_id
             WHERE seed.resource_id=? AND other.resource_id<>?
               AND seed.review_status<>'rejected' AND other.review_status<>'rejected'
             GROUP BY r.id, r.title ORDER BY shared_topics DESC, r.id"""
    return [dict(row) for row in connection.execute(sql, (resource_id, resource_id))]


def coverage(connection):
    return [dict(row) for row in connection.execute("""
        SELECT t.id, t.name, COUNT(rt.resource_id) AS resource_count
        FROM topic t LEFT JOIN resource_topic rt ON rt.topic_id=t.id AND rt.review_status<>'rejected'
        GROUP BY t.id, t.name ORDER BY resource_count, t.id""")]


def show(connection, resource_id):
    record = connection.execute("SELECT * FROM resource WHERE id=?", (resource_id,)).fetchone()
    if record is None:
        raise ValueError(f"Unknown resource: {resource_id}")
    result = dict(record)
    for key, sql in {
        "mentions": "SELECT * FROM source_mention WHERE resource_id=? ORDER BY id",
        "identifiers": "SELECT * FROM identifier WHERE resource_id=? ORDER BY id",
        "credits": "SELECT a.name, a.agent_kind, ra.contribution_role, ra.credit_order FROM resource_agent ra JOIN agent a ON a.id=ra.agent_id WHERE ra.resource_id=? ORDER BY contribution_role, credit_order",
        "issues": "SELECT q.* FROM quality_issue q JOIN source_mention m ON m.id=q.mention_id WHERE m.resource_id=? ORDER BY q.id",
        "topics": "SELECT t.name, rt.basis, rt.review_status FROM resource_topic rt JOIN topic t ON t.id=rt.topic_id WHERE rt.resource_id=? ORDER BY t.id",
    }.items():
        result[key] = [dict(row) for row in connection.execute(sql, (resource_id,))]
    return result


def demo(connection):
    return {
        "profile": profile(build_dataset()),
        "proposed_phishing_videos": search(connection, topic="phishing", format_id="video", audience="older_adults"),
        "shared_topics_with_r034": related(connection, "r034"),
        "duplicate_url_provenance": [dict(r) for r in connection.execute(
            "SELECT id, source_category, page_start, retrieved_on FROM source_mention WHERE resource_id='r022' ORDER BY id")],
        "coverage_gaps": [row for row in coverage(connection) if row["resource_count"] == 0],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ROOT / "build/catalog.sqlite3", help="SQLite demo path")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="Extract curated data and build SQLite, MySQL and Neo4j artifacts")
    sub.add_parser("demo", help="Build and run matched catalog examples locally")
    query = sub.add_parser("search")
    query.add_argument("text", nargs="?")
    query.add_argument("--topic")
    query.add_argument("--format", dest="format_id")
    query.add_argument("--audience")
    query.add_argument("--limit", type=int, default=50)
    for cmd in ["show", "related"]:
        sub.add_parser(cmd).add_argument("resource_id")
    sub.add_parser("coverage")
    load = sub.add_parser("load", help="Load one running Compose database (schema then seed)")
    load.add_argument("backend", choices=["mysql", "neo4j"])
    args = parser.parse_args(argv)
    try:
        if args.command == "load":
            load_native(args.backend)
            print(f"Loaded {args.backend}: 49 records and 50 source mentions.")
            return 0
        if args.command in ("build", "demo"):
            report = export()
            if args.command == "build":
                print_json(report)
                return 0
        if not args.db.exists():
            raise ValueError("Demo database missing. Run: python -m elder_catalog build")
        with open_sqlite(args.db) as connection:
            if args.command == "demo":
                output = demo(connection)
            elif args.command == "search":
                if not 1 <= args.limit <= 1000:
                    raise ValueError("Limit must be between 1 and 1000")
                output = search(connection, args.text, args.topic, args.format_id, args.audience, args.limit)
            elif args.command == "show":
                output = show(connection, args.resource_id)
            elif args.command == "related":
                output = related(connection, args.resource_id)
            else:
                output = coverage(connection)
            print_json(output)
        return 0
    except (ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())

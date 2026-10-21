"""Tests for MySQL and Neo4j running in Docker.

PowerShell: $env:ELDER_NATIVE_TESTS='1'; python -m unittest discover -s tests -v
Use databases that contain only prototype data. Imports update existing records.
"""
import os
import unittest

from elder_catalog.dataset import build_dataset
from elder_catalog.queries import MYSQL_EXAMPLES, NEO4J_EXAMPLES
from elder_catalog.storage import NODE_TABLES, graph_rows, load_native, run_native


@unittest.skipUnless(os.environ.get("ELDER_NATIVE_TESTS") == "1", "Set ELDER_NATIVE_TESTS=1 with Compose services running")
class NativeMySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_native("mysql")
        load_native("mysql")
        cls.data = build_dataset()

    def test_repeat_import_counts(self):
        for table, rows in self.data.items():
            output = run_native("mysql", f"SELECT CONCAT('count=',COUNT(*)) FROM {table};")
            self.assertIn(f"count={len(rows)}\n", output)

    def test_matched_queries_execute_and_return_phishing_videos(self):
        output = run_native("mysql", MYSQL_EXAMPLES)
        self.assertIn("r034", output)
        self.assertIn("r041", output)
        query = """SELECT CONCAT('phishing=',COUNT(*)) FROM resource_topic rt
                   JOIN resource_format rf ON rf.resource_id=rt.resource_id
                   WHERE rt.topic_id='phishing' AND rf.format_id='video';"""
        self.assertIn("phishing=2\n", run_native("mysql", query))

    def test_native_constraints_reject_invalid_data(self):
        for query in [
            "INSERT INTO resource_format VALUES ('missing','book','bib-01','test');",
            "INSERT INTO resource_format VALUES ('r001','book','bib-02','test');",
            "UPDATE resource SET publication_precision='month' WHERE id='r001';",
        ]:
            with self.assertRaises(RuntimeError):
                run_native("mysql", query)


@unittest.skipUnless(os.environ.get("ELDER_NATIVE_TESTS") == "1", "Set ELDER_NATIVE_TESTS=1 with Compose services running")
class NativeNeo4jTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_native("neo4j")
        load_native("neo4j")
        cls.data = build_dataset()

    def test_repeat_import_counts_and_projection_size(self):
        for table, label in NODE_TABLES.items():
            output = run_native("neo4j", f"MATCH (n:{label}) RETURN 'count=' + toString(count(n));")
            self.assertIn(f'"count={len(self.data[table])}"', output)
        nodes, edges = graph_rows(self.data)
        self.assertIn(f'"count={len(nodes)}"', run_native("neo4j", "MATCH (n) RETURN 'count=' + toString(count(n));"))
        self.assertIn(f'"count={len(edges)}"', run_native("neo4j", "MATCH ()-[r]->() RETURN 'count=' + toString(count(r));"))

    def test_matched_queries_execute_and_return_phishing_videos(self):
        run_native("neo4j", "CALL db.awaitIndexes(60);")
        output = run_native("neo4j", NEO4J_EXAMPLES)
        self.assertIn("r034", output)
        self.assertIn("r041", output)
        query = """MATCH (r:Resource)-[:ABOUT]->(:Topic {id:'phishing'}),
                   (r)-[:HAS_FORMAT]->(:Format {id:'video'})
                   RETURN 'phishing=' + toString(count(r));"""
        self.assertIn('"phishing=2"', run_native("neo4j", query))

    def test_native_uniqueness_constraint_rejects_duplicate(self):
        with self.assertRaises(RuntimeError):
            run_native("neo4j", "CREATE (:Resource {id:'r001'});")

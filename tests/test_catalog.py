from collections import Counter
from copy import deepcopy
import hashlib
import sqlite3
import unittest

from elder_catalog.__main__ import coverage, related, search, show
from elder_catalog.dataset import ROOT, build_dataset, validate
from elder_catalog.storage import graph_rows, import_sqlite, mysql_literal, neo4j_seed


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_dataset()

    def test_all_source_mentions_accounted_for(self):
        self.assertEqual(49, len(self.data["resource"]))
        self.assertEqual(Counter({"bibliography": 32, "Videos": 13, "Podcasts": 1,
                                  "Websites": 1, "Hotlines": 1, "Fliers & Written Resources": 2}),
                         Counter(m["source_category"] for m in self.data["source_mention"]))

    def test_mentions_after_page_breaks_not_lost(self):
        mentions = {m["id"]: m for m in self.data["source_mention"]}
        for key, page in [("bib-10", 2), ("bib-11", 3), ("bib-30", 3), ("bib-31", 4), ("flyer-02", 5)]:
            self.assertEqual((page, page), (mentions[key]["page_start"], mentions[key]["page_end"]))

    def test_duplicate_url_retains_different_retrieval_dates(self):
        mentions = [m for m in self.data["source_mention"] if m["resource_id"] == "r022"]
        self.assertEqual({"2026-09-23", "2026-09-19"}, {m["retrieved_on"] for m in mentions})
        self.assertEqual(2, len(mentions))

    def test_partial_dates_are_not_fabricated(self):
        resources = {r["id"]: r for r in self.data["resource"]}
        for key, value, precision in [("r031", "2021-06", "month"), ("r002", "2020", "year"),
                                      ("r022", None, "unknown")]:
            self.assertEqual((value, precision), (resources[key]["publication_value"], resources[key]["publication_precision"]))

    def test_original_problematic_urls_preserved(self):
        mention = next(m for m in self.data["source_mention"] if m["id"] == "video-04")
        self.assertIn("S106474812030035X\\", mention["citation_raw"])
        identifier = next(i for i in self.data["identifier"] if i["resource_id"] == "r036")
        self.assertTrue(identifier["identifier_value"].endswith("S106474812030035X"))
        self.assertIn("proxy2.library.illinois.edu", identifier["identifier_value"])

    def test_unknown_formats_not_assumed_to_be_videos(self):
        formats = {f["resource_id"]: f["format_id"] for f in self.data["resource_format"]}
        self.assertEqual("unknown", formats["r035"])
        self.assertEqual("unknown", formats["r036"])

    def test_all_annotations_are_provisional(self):
        self.assertTrue(all(r["verification_status"] == "unverified" for r in self.data["resource"]))
        self.assertTrue(all(r["review_status"] == "proposed" for r in self.data["resource_topic"]))
        self.assertTrue(all(r["review_status"] == "proposed" for r in self.data["resource_audience"]))

    def test_ambiguous_age_cutoffs_preserved(self):
        self.assertEqual({(55, ">="), (60, ">="), (65, ">="), (65, ">")},
                         {(r["minimum_age"], r["comparison_operator"]) for r in self.data["age_definition"]})

    def test_planning_prose_and_orphan_fragment_retained(self):
        statements = {s["statement_kind"]: s for s in self.data["planning_statement"]}
        self.assertIn("AARP Tax Help", statements["goals"]["statement_text"])
        self.assertIn("Dow Jones", statements["unassigned_fragment"]["statement_text"])

    def test_source_hash_matches_pdf(self):
        digest = hashlib.sha256((ROOT / "VPL-1_resources.pdf").read_bytes()).hexdigest()
        self.assertEqual(digest, self.data["source_document"][0]["sha256"])

    def test_invalid_date_and_mismatched_evidence_rejected(self):
        data = deepcopy(self.data)
        data["resource"][0]["publication_value"] = "2026-02-30"
        with self.assertRaises(ValueError):
            validate(data)
        data = deepcopy(self.data)
        data["resource_topic"][0]["source_mention_id"] = "bib-02"
        with self.assertRaises(ValueError):
            validate(data)


class RelationalTests(unittest.TestCase):
    def setUp(self):
        self.data = build_dataset()
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        import_sqlite(self.db, self.data)

    def tearDown(self):
        self.db.close()

    def test_repeat_import_does_not_duplicate_data(self):
        import_sqlite(self.db, self.data)
        for table, rows in self.data.items():
            self.assertEqual(len(rows), self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], table)
        self.assertEqual(49, self.db.execute("SELECT COUNT(*) FROM resource_fts").fetchone()[0])
        self.assertEqual([], self.db.execute("PRAGMA foreign_key_check").fetchall())

    def test_filter_phishing_videos(self):
        self.assertEqual(["r034", "r041"], [r["id"] for r in search(self.db, topic="phishing", format_id="video", audience="older_adults")])

    def test_full_text_search_and_untrusted_input(self):
        self.assertEqual({"r013", "r034", "r041"}, {r["id"] for r in search(self.db, text="phishing")})
        self.assertEqual([], search(self.db, text="'; DROP TABLE resource; --"))
        self.assertEqual(49, self.db.execute("SELECT COUNT(*) FROM resource").fetchone()[0])

    def test_shared_topics_and_zero_coverage(self):
        self.assertEqual(["r013", "r041"], [r["id"] for r in related(self.db, "r034")])
        self.assertEqual({"grandchild_scams", "tech_support_scams", "government_impersonation", "credit_card_fraud", "mail_fraud", "tax_assistance"},
                         {r["id"] for r in coverage(self.db) if r["resource_count"] == 0})

    def test_author_order_and_publisher_statement(self):
        creators = [r["name"] for r in show(self.db, "r003")["credits"] if r["contribution_role"] == "creator"]
        self.assertEqual(["Chen, H.", "He, M.", "Xu, X.", "Atkin, D."], creators)
        self.assertEqual(0, self.db.execute("SELECT COUNT(*) FROM agent WHERE name='Independently published'").fetchone()[0])
        self.assertEqual("Independently published", show(self.db, "r008")["publisher_statement"])

    def test_constraints_reject_orphans_and_mismatched_provenance(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO resource_format VALUES ('missing', 'book', 'bib-01', 'test')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO resource_format VALUES ('r001', 'book', 'bib-02', 'test')")

    def test_unique_identifiers_and_invalid_precision_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO identifier SELECT 'duplicate',resource_id,identifier_kind,identifier_value,source_mention_id FROM identifier LIMIT 1")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE resource SET publication_precision='month' WHERE id='r001'")

    def test_rejected_annotation_is_excluded(self):
        self.db.execute("UPDATE resource_topic SET review_status='rejected' WHERE resource_id='r034'")
        self.assertEqual(["r041"], [r["id"] for r in search(self.db, topic="phishing", format_id="video")])


class GraphProjectionTests(unittest.TestCase):
    def test_graph_projection_preserves_relational_answers_and_endpoints(self):
        data = build_dataset()
        nodes, edges = graph_rows(data)
        keys = {(n["label"], n["properties"]["id"]) for n in nodes}
        self.assertEqual(len(nodes), len(keys))
        for edge in edges:
            self.assertIn((edge["from_label"], edge["from_id"]), keys)
            self.assertIn((edge["to_label"], edge["to_id"]), keys)
        phishing = {e["from_id"] for e in edges if e["type"] == "ABOUT" and e["to_id"] == "phishing"}
        videos = {e["from_id"] for e in edges if e["type"] == "HAS_FORMAT" and e["to_id"] == "video"}
        self.assertEqual({"r034", "r041"}, phishing & videos)
        self.assertEqual(50, sum(e["type"] == "REFERS_TO" for e in edges))
        self.assertEqual(3, sum(e["type"] == "POSSIBLE_SAME_WORK" for e in edges))

    def test_export_handles_untrusted_citation_characters(self):
        value = "'); DROP TABLE resource; -- \\ \n café"
        literal = mysql_literal(value)
        self.assertNotIn("DROP", literal)
        data = build_dataset()
        data["resource"][0]["title"] = 'x\"}) DELETE n; //\n'
        cypher = neo4j_seed(data)
        self.assertIn('title: "x\\\"}) DELETE n; //\\n"', cypher)
        self.assertTrue(cypher.endswith(":commit\n"))


if __name__ == "__main__":
    unittest.main()

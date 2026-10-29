"""Checks for source evidence and guarded imports in the independent walkthrough."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from neo4j_version.model import graph_plan, load_snapshot, validate


class WalkthroughTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.digest = load_snapshot(Path(__file__).resolve().parents[1] / "data/catalog.json")

    def test_assignment_evidence_must_belong_to_its_resource(self):
        changed = deepcopy(self.data)
        row = changed["resource_topic"][0]
        row["source_mention_id"] = next(
            m["id"] for m in changed["source_mention"] if m["resource_id"] != row["resource_id"]
        )
        with self.assertRaisesRegex(ValueError, "Evidence belongs to another resource"):
            validate(changed)

    def test_resource_assertion_rejects_self_link(self):
        changed = deepcopy(self.data)
        row = changed["resource_relation"][0]
        row["to_resource_id"] = row["from_resource_id"]
        with self.assertRaisesRegex(ValueError, "Self resource link"):
            validate(changed)

    @unittest.skipUnless(importlib.util.find_spec("neo4j"), "Install neo4j_demo/requirements.txt for driver tests")
    def test_populated_unrelated_database_is_refused_before_ddl(self):
        from neo4j_version.database import load
        with patch("neo4j_version.database.query", side_effect=[[], [{"count": 1}]]) as run:
            with self.assertRaisesRegex(ValueError, "not empty"):
                load(object(), self.data, self.digest)
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(not call.kwargs.get("write", False) for call in run.call_args_list))

    @unittest.skipUnless(importlib.util.find_spec("neo4j"), "Install neo4j_demo/requirements.txt for driver tests")
    def test_matching_snapshot_is_verified_without_writes(self):
        from neo4j_version.database import load
        with patch("neo4j_version.database.query", return_value=[{"id": self.digest}]) as run:
            with patch("neo4j_version.database.verify_snapshot", return_value={"checked": True}) as check:
                result = load(object(), self.data, self.digest)
        self.assertEqual(result["action"], "verified_no_op")
        self.assertEqual(run.call_count, 1)
        check.assert_called_once()


if __name__ == "__main__":
    unittest.main()

"""Offline provenance checks. Fixtures stay in TemporaryDirectory, never real KB."""

from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from scripts.kb_store import KnowledgeBaseError, LocalKnowledgeBase, public_url


class KnowledgeBaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.kb = LocalKnowledgeBase(self.temp.name)

    def source(self, status="retrieved"):
        return self.kb.add_source({
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/FIXTURE/",
            "title": "OFFLINE TEST FIXTURE, not research evidence", "source_kind": "paper",
            "retrieval_status": status, "dataset_version": "FIXTURE", "limitations": ["Test fixture."]},
            content="Offline test fixture content." if status == "retrieved" else None)

    def claim(self, source_id):
        return {"text": "FIXTURE CLAIM, not a biological finding", "claim_kind": "extraction",
                "evidence_type": "offline fixture", "source_location": "fixture line 1",
                "conditions": "offline test", "dataset_version": "FIXTURE", "review_status": "unreviewed",
                "created_by": "unittest", "source_ids": [source_id], "limitations": ["Synthetic fixture"],
                "neuron_ids": ["720575940600000001"], "cell_types": []}

    def test_snapshot_hash_and_exact_id_survive_restart(self):
        source = self.source()
        claim = self.kb.add_claim(self.claim(source["source_id"]))
        self.assertTrue((Path(self.temp.name) / source["snapshot_path"]).is_file())
        reopened = LocalKnowledgeBase(self.temp.name)
        found = reopened.query("720575940600000001")
        self.assertEqual(found[0]["claim_id"], claim["claim_id"])
        self.assertEqual(found[0]["neuron_ids"], ["720575940600000001"])

    def test_findings_cannot_use_search_metadata_as_evidence(self):
        source = self.source("candidate")
        with self.assertRaises(KnowledgeBaseError):
            self.kb.add_claim(self.claim(source["source_id"]))
        self.assertEqual(self.kb.summary()["counts"]["claims"], 0)

    def test_rejects_missing_sources_and_numeric_neuron_ids(self):
        with self.assertRaises(KnowledgeBaseError):
            self.kb.add_claim(self.claim("src_missing"))
        source = self.source()
        claim = self.claim(source["source_id"])
        claim["neuron_ids"] = [720575940600000001]
        with self.assertRaises(KnowledgeBaseError):
            self.kb.add_claim(claim)

    def test_search_candidate_does_not_downgrade_retrieved_source(self):
        source = self.source()
        candidate = self.source("candidate")
        self.assertEqual(candidate["retrieval_status"], "retrieved")
        self.assertEqual(candidate["content_sha256"], source["content_sha256"])
        self.assertEqual(self.kb.summary()["counts"]["sources"], 1)

    def test_run_requires_existing_provenance_and_fixture_label(self):
        row = {"run_kind": "fixture", "status": "completed", "agent": "unittest",
               "model_version": "fixture", "dataset_version": "fixture", "source_ids": [],
               "claim_ids": [], "parameters": {}, "result": {}}
        with self.assertRaises(KnowledgeBaseError):
            self.kb.add_run(row)
        row["status"] = "fixture"
        run = self.kb.add_run(row)
        self.assertEqual(self.kb.query(run["run_id"], "runs")[0]["status"], "fixture")

    def test_corrupt_records_preserved_and_fail_closed(self):
        path = Path(self.temp.name) / "claims.jsonl"
        path.write_text("not-json\n", encoding="utf-8")
        with self.assertRaises(KnowledgeBaseError):
            self.kb.query()
        self.assertEqual(path.read_text(), "not-json\n")

    def test_credentials_and_private_source_urls_rejected(self):
        for url in ("http://example.com", "https://localhost/a", "https://127.0.0.1/a",
                    "https://user:password@example.com/a", "https://example.com/a?token=secret"):
            with self.subTest(url=url), self.assertRaises(KnowledgeBaseError):
                public_url(url)

    def test_retrieved_metadata_without_content_rejected(self):
        with self.assertRaises(KnowledgeBaseError):
            self.kb.add_source({"url": "https://example.com/a", "title": "fixture",
                                "source_kind": "paper", "retrieval_status": "retrieved"})

    def test_claim_pins_snapshot_hash_after_later_refresh(self):
        first = self.source()
        claim = self.kb.add_claim(self.claim(first["source_id"]))
        refreshed = self.kb.add_source({
            "url": first["url"], "title": first["title"], "source_kind": "paper",
            "retrieval_status": "retrieved", "dataset_version": "FIXTURE", "limitations": ["Fixture"]},
            content="Updated offline fixture.")
        self.assertNotEqual(first["content_sha256"], refreshed["content_sha256"])
        self.assertEqual(claim["source_snapshot_sha256"][first["source_id"]], first["content_sha256"])
        self.assertEqual(len(refreshed["snapshots"]), 2)

    def test_concurrent_writers_preserve_all_claims(self):
        source = self.source()
        def save(index):
            kb = LocalKnowledgeBase(self.temp.name)
            row = self.claim(source["source_id"])
            row["text"] = f"OFFLINE FIXTURE {index}"
            return kb.add_claim(row)["claim_id"]
        with ThreadPoolExecutor(max_workers=4) as executor:
            ids = list(executor.map(save, range(20)))
        self.assertEqual(len(set(ids)), 20)
        self.assertEqual(self.kb.summary()["counts"]["claims"], 20)


if __name__ == "__main__":
    unittest.main()

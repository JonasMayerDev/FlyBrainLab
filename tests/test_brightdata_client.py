"""Provider fixtures test the adapter; they are not live research or billing proof."""

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from scripts.brightdata_client import BrightDataClient, BrightDataConfig, BrightDataError
from scripts.kb_store import KnowledgeBaseError, LocalKnowledgeBase


class BrightDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = BrightDataConfig(api_key="UNIT_TEST_SECRET_NEVER_REAL", serp_zone="fixture_serp",
                                       unlocker_zone="fixture_unlocker", max_requests=2,
                                       max_cost_usd=Decimal("0.02"), estimated_request_cost_usd=Decimal("0.01"),
                                       kb_directory=Path(self.temp.name), allowed_domains=("example.org",))
        self.calls = []

    def transport(self, payload, api_key, timeout):
        self.calls.append(payload)
        if payload["zone"] == "fixture_serp":
            return json.dumps({"organic": [
                {"link": "https://example.org/fixture", "title": "Offline fixture", "description": "Not research."},
                {"link": "https://disallowed.org/a", "title": "Excluded"}]}).encode()
        return b"# Offline fixture content. Not a real research source."

    def test_missing_credentials_prevent_network_and_persistence(self):
        config = replace(self.config, api_key="")
        client = BrightDataClient(config, self.transport)
        with self.assertRaises(BrightDataError):
            client.search("fixture query")
        self.assertEqual(self.calls, [])
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_product_zones_and_account_informed_budget_required(self):
        for change in ({"serp_zone": ""}, {"max_cost_usd": None}, {"estimated_request_cost_usd": None}):
            with self.subTest(change=change):
                with self.assertRaises(BrightDataError):
                    BrightDataClient(replace(self.config, **change), self.transport).search("fixture query")
        self.assertEqual(self.calls, [])

    def test_search_candidates_allowlist_and_cache(self):
        client = BrightDataClient(self.config, self.transport)
        result = client.search("fixture query")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["evidence_status"], "candidate")
        self.assertEqual(client.search("fixture query")["results"], result["results"])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0]["format"], "json")
        self.assertEqual(LocalKnowledgeBase(self.temp.name).summary()["counts"]["claims"], 0)

    def test_fetch_persists_real_response_fixture_as_retrieved_not_finding(self):
        result = BrightDataClient(self.config, self.transport).fetch("https://example.org/fixture", max_characters=10)
        self.assertEqual(result["source"]["retrieval_status"], "retrieved")
        self.assertTrue(result["content_truncated"])
        self.assertEqual(self.calls[0]["data_format"], "markdown")
        self.assertEqual(LocalKnowledgeBase(self.temp.name).summary()["counts"]["claims"], 0)

    def test_request_budget_is_persistent_across_clients(self):
        client = BrightDataClient(self.config, self.transport)
        client.search("fixture one")
        client.search("fixture two")
        with self.assertRaises(BrightDataError):
            BrightDataClient(self.config, self.transport).search("fixture three")
        self.assertEqual(len(self.calls), 2)

    def test_usd_estimate_cap_prevents_next_request(self):
        config = replace(self.config, max_cost_usd=Decimal("0.005"))
        with self.assertRaises(BrightDataError):
            BrightDataClient(config, self.transport).search("fixture query")
        self.assertEqual(self.calls, [])

    def test_failure_remains_counted_and_is_not_retried(self):
        def fail(*args):
            self.calls.append("attempt")
            raise BrightDataError("Offline transport fixture failure.")
        config = replace(self.config, max_requests=1)
        with self.assertRaises(BrightDataError):
            BrightDataClient(config, fail).search("fixture query")
        with self.assertRaises(BrightDataError):
            BrightDataClient(config, self.transport).search("fixture next")
        self.assertEqual(self.calls, ["attempt"])
        ledger = json.loads((Path(self.temp.name) / "brightdata_usage.json").read_text())
        self.assertEqual(ledger["requests"][0]["status"], "failed")

    def test_source_allowlist_credentials_and_port(self):
        client = BrightDataClient(self.config, self.transport)
        for url in ("https://disallowed.org/a", "https://example.org:444/a", "https://example.org/a?api_key=x"):
            with self.subTest(url=url), self.assertRaises((BrightDataError, KnowledgeBaseError)):
                client.fetch(url)
        self.assertEqual(self.calls, [])

    def test_invalid_serp_response_records_no_candidate_or_claim(self):
        with self.assertRaises(BrightDataError):
            BrightDataClient(self.config, lambda *args: b"not json").search("fixture query")
        self.assertEqual(LocalKnowledgeBase(self.temp.name).summary()["counts"]["sources"], 0)

    def test_secret_not_stored_or_returned_even_if_response_echoes_it(self):
        result = BrightDataClient(self.config, lambda *args: self.config.api_key.encode()).fetch("https://example.org/a")
        self.assertEqual(result["content"], "[REDACTED]")
        for path in Path(self.temp.name).rglob("*"):
            if path.is_file():
                self.assertNotIn(self.config.api_key, path.read_text())

    def test_status_is_readonly_and_redacts_key(self):
        result = self.config.readiness()
        self.assertNotIn(self.config.api_key, repr(result))
        self.assertNotIn(self.config.api_key, repr(self.config))
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_concurrent_requests_cannot_overrun_shared_limit(self):
        def request(index):
            try:
                BrightDataClient(self.config, self.transport).search(f"fixture query {index}")
                return True
            except BrightDataError:
                return False
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(request, range(6)))
        self.assertEqual(results.count(True), 2)
        self.assertEqual(len(self.calls), 2)


if __name__ == "__main__":
    unittest.main()

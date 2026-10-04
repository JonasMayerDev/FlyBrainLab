"""Tests for the independent session audit (flylab/audit.py). Replication tests need the project venv."""
import importlib.util
import unittest

from flylab import audit, board

HAS_SIM = importlib.util.find_spec("numpy") is not None and importlib.util.find_spec("pandas") is not None


def _session(prefix: str):
    rid, events = next((r, e) for r, e in board.real_sessions() if r.startswith(prefix))
    results = [(e, audit._artifact_path(rid, (e.get("data") or {}).get("artifact")))
               for e in events if e.get("type") == "experiment_result" and isinstance(e.get("data"), dict)]
    return rid, events, results


class AuditCheckTests(unittest.TestCase):
    def test_recorded_sessions_pass_the_static_checks(self):
        for prefix in ("20261004-010600", "20261004-093251", "20261004-120628"):
            rid, events, results = _session(prefix)
            for check in (audit.check_real_data(rid, events, results), audit.check_record(rid, events),
                          audit.check_sources(events, []), audit.check_approvals(events)):
                self.assertEqual(check["status"], "pass", (prefix, check))

    def test_unpaired_seeds_are_flagged(self):
        _, _, results = _session("20261004-120628")
        check = audit.check_paired_controls(results)
        self.assertEqual(check["status"], "warn")
        self.assertTrue(any(not p["same_seed"] for p in check["evidence"]))

    def test_uncertain_movement_is_not_counted_as_confirmed(self):
        _, events, _ = _session("20261004-093251")
        self.assertEqual(audit.check_movement(events)["status"], "warn")

    def test_invented_doi_is_caught(self):
        fake = [{"seq": 0, "type": "board_statement", "agent": "analysis", "content": "see doi 10.9999/not.a.paper"}]
        self.assertEqual(audit.check_sources(fake, [])["status"], "fail")

    @unittest.skipUnless(HAS_SIM, "needs the simulation venv (.venv)")
    def test_brain_run_replicates_exactly(self):
        rid, events, results = _session("20261004-093251")
        brain_only = [(e, p) for e, p in results if p and p.stem == "brain_01"]
        check = audit.check_replication(rid, brain_only, events)
        self.assertEqual(check["status"], "pass", check)


if __name__ == "__main__":
    unittest.main()

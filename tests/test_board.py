"""Contract tests for the expert-board export (flylab/board.py) and its agent tools."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from flylab import board, record, tools


class BoardExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = board.build_board()

    def test_mock_runs_are_excluded(self):
        ids = {s["run_id"] for s in self.b["sessions"]}
        self.assertNotIn("demo_mock_backward_walking", ids)
        self.assertTrue(all(not x["mock"] for x in self.b["experiments"]))

    def test_every_reference_resolves_to_a_recorded_experiment(self):
        known = {x["id"] for x in self.b["experiments"]}
        for s in self.b["sessions"]:
            for r in s["rounds"]:
                self.assertTrue(set(r["carried_forward"]) <= known)
                for p in r["posts"]:
                    self.assertTrue(set(p.get("refs", [])) <= known, p["seq"])

    def test_carried_forward_never_points_into_the_same_round(self):
        for s in self.b["sessions"]:
            for r in s["rounds"]:
                self.assertFalse(set(r["carried_forward"]) & set(r["experiments"]))

    def test_second_round_builds_on_first_round_results(self):
        # Recorded escape session: the cycle-2 decision named flight_01 / flight_02.
        s2 = next(s for s in self.b["sessions"] if "escape" in s["question"])
        self.assertIn("S2/flight_01", s2["rounds"][1]["carried_forward"])

    def test_sessions_without_prior_review_are_not_claimed_to_read_earlier_sessions(self):
        for s in self.b["sessions"]:
            if not s["read_prior_sessions"]:
                self.assertEqual(s["earlier_results_cited"], [])

    def test_coverage_statuses_are_valid(self):
        allowed = {"reproduced_body", "reproduced_brain", "conflict", "untested"}
        for b in self.b["coverage"]["behaviors"]:
            self.assertIn(b["status"], allowed)
            self.assertLessEqual(b["n_tested"], b["n_impulses"])
            for i in b["impulses"]:
                self.assertTrue(i["citation"]["doi"])


class BoardToolTests(unittest.TestCase):
    def test_prior_review_and_statement_are_recorded(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(record, "RUNS_DIR", Path(tmp)), \
                mock.patch.object(record, "CURRENT_FILE", Path(tmp) / "CURRENT"):
            rid = record.new_run("board tool test", set_current=False)
            res = tools.get_prior_results(agent="supervisor", run_id=rid)
            self.assertTrue(res["ok"])
            out = tools.log_board_statement("next: feeding", stance="nonsense", refs=["S1/brain_01"],
                                            agent="planner", run_id=rid)
            self.assertEqual(out["stance"], "propose")
            events = record.load(rid)
            self.assertEqual([e["type"] for e in events], ["question", "prior_review", "board_statement"])
            self.assertTrue(all("nonstandard_type" not in e for e in events))


if __name__ == "__main__":
    unittest.main()

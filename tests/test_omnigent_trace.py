"""Synthetic fixtures test provenance rejection; they are not scientific runs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from scripts import export_omnigent_trace as trace
from simulation.experiment import summarize


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def make_assay(tmp_path):
    target = write(tmp_path / "research/evidence/targets.json", {"fixture": True})
    design = {"dataset_version": "FAFB FlyWire v783", "model_commit": "fixture-commit",
              "duration_ms": 200, "timestep_ms": 0.1, "stimulus_rate_hz": 150,
              "seeds": [42, 43, 44], "stimulus_ids": ["10"], "readout_ids": ["20", "21"],
              "target_file": str(target.relative_to(tmp_path)),
              "target_file_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    design_path = write(tmp_path / "research/designs/fixture.json", design)
    design_hash = hashlib.sha256(design_path.read_bytes()).hexdigest()
    design_path.with_suffix(".sha256").write_text(design_hash)
    runs = []
    for seed in design["seeds"]:
        for condition in ("sham", "upstream_drive"):
            run_id = f"fixture-{seed}-{condition}"
            events = [] if condition == "sham" else [{"t_seconds": 0.01, "flywire_id": "20"}]
            counts = {"20": len(events), "21": 0}
            metrics = {"population_mean_rate_hz": len(events) / 0.4, "per_neuron_spike_counts": counts}
            run = {"run_id": run_id, "status": "completed", "condition": condition, "seed": seed,
                   "result_path": "data/runs/" + run_id, "wall_seconds": 1., "readout_metrics": metrics,
                   "design_sha256": design_hash, "dataset_version": design["dataset_version"],
                   "model_commit": design["model_commit"], "duration_ms": 200, "timestep_ms": 0.1,
                   "readout_neuron_ids": design["readout_ids"], "stimulated_neuron_ids": design["stimulus_ids"],
                   "stimulus_rate_hz": 0 if condition == "sham" else 150,
                   "full_network_included": True, "execution_context": "Omnigent native tool",
                   "spike_events": len(events), "spikes_file": "spikes.parquet"}
            folder = tmp_path / run["result_path"]
            write(folder / "run.json", run)
            write(folder / "readout.json", metrics)
            write(folder / "readout_spikes.json", {"duration_ms": 200, "events_are_complete": True,
                  "readout_neuron_ids": design["readout_ids"], "events": events})
            table = pa.table({"t_seconds": pa.array([e["t_seconds"] for e in events], type=pa.float64()),
                              "flywire_id": pa.array([e["flywire_id"] for e in events], type=pa.string())})
            pq.write_table(table, folder / "spikes.parquet")
            runs.append(run)
    result = {"status": "completed", "test": "A", "design_sha256": design_hash,
              "run_ids": [r["run_id"] for r in runs], "summary": summarize(runs, "A", design),
              "runs": [{k: r[k] for k in ("run_id", "condition", "seed", "result_path", "wall_seconds", "readout_metrics")} for r in runs],
              "comparison_path": "data/experiments/fixture.json"}
    write(tmp_path / result["comparison_path"], result)
    receipt_id = "tool_" + "a" * 32
    receipt = {"receipt_id": receipt_id, "test": "A", "design_path": "research/designs/fixture.json",
               "design_sha256": design_hash, "result": result}
    path = "data/discovery/tool-receipts/" + receipt_id + ".json"
    write(tmp_path / path, receipt)
    return {"output": {**receipt, "receipt_path": path}, "design_hash": design_hash, "receipt_id": receipt_id,
            "first_run": tmp_path / runs[0]["result_path"]}


def item(kind, data, position, created_at, status=1):
    return {"type": kind, "status": status, "position": position, "created_at": created_at,
            "data": data, "local_item_sha256": hashlib.sha256(json.dumps(data).encode()).hexdigest()}


def add_tool(session, name, arguments, output, timestamp):
    pos = len(session["items"])
    call_id = session["conversation_id"] + "-" + str(pos)
    session["items"].append(item(2, {"name": name, "arguments": json.dumps(arguments), "call_id": call_id}, pos, timestamp))
    session["items"].append(item(3, {"call_id": call_id, "output": json.dumps(output) if not isinstance(output, str) else output}, pos + 1, timestamp + 1))


def complete_tree(tmp_path, assay):
    root = {"conversation_id": "0" * 32, "parent_conversation_id": None, "role": "fly_discovery", "items": []}
    sessions = [root]
    for stage, role in enumerate(("researcher", "evidence_reviewer", "hypothesis_planner", "experimenter", "analyst"), 1):
        child_id = f"{stage:032x}"
        child = {"conversation_id": child_id, "parent_conversation_id": root["conversation_id"],
                 "role": role, "live_status": 4, "items": []}  # Closed children are valid.
        timestamp = stage * 20
        add_tool(root, "sys_session_send", {"agent": role}, {"conversation_id": child_id, "agent": role, "status": "launching"}, timestamp)
        prompt = "Evidence handoff" if role != "analyst" else "Analyze actual receipt " + assay["receipt_id"]
        child["items"].append(item(1, {"role": "user", "content": [{"type": "input_text", "text": prompt}]}, 0, timestamp + 1))
        final_text = role + " completed with checked evidence"
        if role == "researcher":
            add_tool(child, "read_source_snapshot", {"source_id": "src_fixture"},
                     {"status": "retrieved", "source_id": "src_fixture", "content_sha256": "b" * 64}, timestamp + 2)
        if role == "evidence_reviewer":
            add_tool(child, "search_knowledge", {"collection": "claims"}, [{"claim_id": "clm_fixture"}], timestamp + 2)
        if role == "hypothesis_planner":
            final_text = "Candidate tests A and B; select A; sealed design " + assay["design_hash"]
        if role == "experimenter":
            add_tool(child, "run_frozen_experiment", {"test": "A"}, assay["output"], timestamp + 2)
            final_text = "Actual experiment receipt " + assay["receipt_id"]
        if role == "analyst":
            submitted = {"question": "Fixture question", "hypothesis": "Fixture hypothesis", "selected_test": "A",
                         "actual_result": "Fixture rates", "updated_decision": "Run B", "decision_reason": "Positive response",
                         "candidate_tests": ["A", "B"], "source_ids": ["src_fixture"], "claim_ids": ["clm_fixture"],
                         "tool_receipt_ids": [assay["receipt_id"]], "limitations": ["Synthetic test fixture"], "next_test": "B"}
            record_id = "discovery_" + "c" * 32
            path = "data/discovery/" + record_id + ".json"
            write(tmp_path / path, {**submitted, "record_id": record_id})
            add_tool(child, "save_discovery_record", {"record_json": json.dumps(submitted)},
                     {"record_id": record_id, "path": path}, timestamp + 2)
            final_text = "Stored actual discovery record " + record_id
        child["items"].append(item(1, {"role": "assistant", "content": [{"type": "output_text", "text": final_text}]},
                                    len(child["items"]), timestamp + 5))
        add_tool(root, "sys_read_inbox", {}, f"[System: sub-agent task {child_id} completed — {role}:fixture returned: {final_text}]", timestamp + 7)
        sessions.append(child)
    return sessions


def append_followup_b(tmp_path, sessions, assay):
    """Create real tiny B artifacts and two additional native handoffs."""
    design = json.loads((tmp_path / "research/designs/fixture.json").read_text())
    records = []
    for seed in design["seeds"]:
        source = json.loads((tmp_path / f"data/runs/fixture-{seed}-upstream_drive/run.json").read_text())
        for condition in ("upstream_drive", "outgoing_disconnected"):
            run_id = f"fixture-B-{seed}-{condition}"
            events = [{"t_seconds": 0.01, "flywire_id": "20"}] if condition == "upstream_drive" else []
            metrics = {"population_mean_rate_hz": len(events) / 0.4,
                       "per_neuron_spike_counts": {"20": len(events), "21": 0}}
            record = {**source, "run_id": run_id, "condition": condition, "result_path": "data/runs/" + run_id,
                      "readout_metrics": metrics, "spike_events": len(events)}
            folder = tmp_path / record["result_path"]
            write(folder / "run.json", record)
            write(folder / "readout.json", metrics)
            write(folder / "readout_spikes.json", {"duration_ms": 200, "events_are_complete": True,
                  "readout_neuron_ids": design["readout_ids"], "events": events})
            pq.write_table(pa.table({"t_seconds": pa.array([e["t_seconds"] for e in events], type=pa.float64()),
                                    "flywire_id": pa.array([e["flywire_id"] for e in events], type=pa.string())}), folder / "spikes.parquet")
            records.append(record)
    result = {"status": "completed", "test": "B", "design_sha256": assay["design_hash"],
              "run_ids": [r["run_id"] for r in records], "summary": summarize(records, "B", design),
              "runs": [{k: r[k] for k in ("run_id", "condition", "seed", "result_path", "wall_seconds", "readout_metrics")} for r in records],
              "comparison_path": "data/experiments/fixture-B.json"}
    write(tmp_path / result["comparison_path"], result)
    receipt_id = "tool_" + "d" * 32
    receipt = {"receipt_id": receipt_id, "test": "B", "design_path": "research/designs/fixture.json",
               "design_sha256": assay["design_hash"], "result": result}
    receipt_path = "data/discovery/tool-receipts/" + receipt_id + ".json"
    write(tmp_path / receipt_path, receipt)
    root = sessions[0]
    for stage, role in ((6, "experimenter"), (7, "analyst")):
        child_id = f"{stage:032x}"
        timestamp = stage * 20
        child = {"conversation_id": child_id, "parent_conversation_id": root["conversation_id"],
                 "role": role, "live_status": 4, "items": []}
        add_tool(root, "sys_session_send", {"agent": role}, {"conversation_id": child_id, "agent": role, "status": "launching"}, timestamp)
        child["items"].append(item(1, {"role": "user", "content": [{"type": "input_text", "text": "Actual A/B receipts " + assay["receipt_id"] + " " + receipt_id}]}, 0, timestamp + 1))
        if role == "experimenter":
            add_tool(child, "run_frozen_experiment", {"test": "B"}, {**receipt, "receipt_path": receipt_path}, timestamp + 2)
            final_text = "Actual B receipt " + receipt_id
        else:
            record_id = "discovery_" + "e" * 32
            submitted = {"selected_test": "B", "next_test": "matched_input_and_sensory_validation",
                         "candidate_tests": ["A", "B"], "source_ids": ["src_fixture"], "claim_ids": ["clm_fixture"],
                         "tool_receipt_ids": [assay["receipt_id"], receipt_id]}
            path = "data/discovery/" + record_id + ".json"
            write(tmp_path / path, {**submitted, "record_id": record_id})
            add_tool(child, "save_discovery_record", {"record_json": json.dumps(submitted)}, {"record_id": record_id, "path": path}, timestamp + 2)
            final_text = "Stored B discovery record " + record_id
        child["items"].append(item(1, {"role": "assistant", "content": [{"type": "output_text", "text": final_text}]}, len(child["items"]), timestamp + 5))
        add_tool(root, "sys_read_inbox", {}, f"[System: sub-agent task {child_id} completed — {role}:fixture returned: {final_text}]", timestamp + 7)
        sessions.append(child)


def separate_followup_b(tmp_path, assay):
    prior_sessions = complete_tree(tmp_path, assay)
    prior = {"schema_version": 3, "root_conversation_id": prior_sessions[0]["conversation_id"],
             "native_discovery_loop_verified": True, "sessions": prior_sessions,
             "verification": trace.verify_tree(prior_sessions)}
    prior_path = "data/discovery/fixture-prior-trace.json"
    write(tmp_path / prior_path, prior)
    combined = complete_tree(tmp_path, assay)
    append_followup_b(tmp_path, combined, assay)
    original_root = combined[0]
    # Keep new evidence/plan/B stages. A remains only in the separate prior tree.
    retained_children = combined[1:4] + combined[-2:]
    root = {"conversation_id": "f" * 32, "parent_conversation_id": None, "role": "fly_discovery", "items": []}
    decision_path = "data/discovery/discovery_" + "c" * 32 + ".json"
    add_tool(root, "read_local_artifact", {"relative_path": decision_path},
             {"status": "ok", "path": decision_path, "truncated": False,
              "content": (tmp_path / decision_path).read_text()}, 210)
    for old_item in original_root["items"][:12] + original_root["items"][20:]:
        copied = json.loads(json.dumps(old_item))
        copied["position"] = len(root["items"])
        copied["created_at"] += 220
        root["items"].append(copied)
    sessions = [root]
    for index, child in enumerate(retained_children, 1):
        child = json.loads(json.dumps(child))
        old_id = child["conversation_id"]
        new_id = "f" * 24 + f"{index:08x}"
        root["items"] = json.loads(json.dumps(root["items"]).replace(old_id, new_id))
        child = json.loads(json.dumps(child).replace(old_id, new_id))
        child["parent_conversation_id"] = root["conversation_id"]
        for i in child["items"]:
            i["created_at"] += 220
        sessions.append(child)
    analyst = sessions[-1]
    save = next(i for i in analyst["items"] if i["type"] == 2)
    submitted = json.loads(json.loads(save["data"]["arguments"])["record_json"])
    submitted["tool_receipt_ids"] = ["tool_" + "d" * 32]
    save["data"]["arguments"] = json.dumps({"record_json": json.dumps(submitted)})
    record_id = "discovery_" + "e" * 32
    write(tmp_path / ("data/discovery/" + record_id + ".json"), {**submitted, "record_id": record_id})
    return sessions, {"path": prior_path}


class TraceVerificationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name).resolve()
        previous_root = trace.ROOT
        self.addCleanup(setattr, trace, "ROOT", previous_root)
        trace.ROOT = self.root
        self.assay = make_assay(self.root)

    def tree(self):
        return complete_tree(self.root, self.assay)

    def test_complete_closed_children_and_actual_artifacts_pass(self):
        result = trace.verify_tree(self.tree())
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(len(result["completed_handoffs"]), 5)
        self.assertEqual(result["verified_discovery_records"][0]["next_test"], "B")

    def test_session_presence_without_collected_handoff_fails(self):
        sessions = self.tree()
        root = sessions[0]
        root["items"] = [i for i in root["items"] if not (i["type"] == 3 and "researcher:fixture" in str(i["data"]))]
        result = trace.verify_tree(sessions)
        self.assertFalse(result["passed"])
        self.assertTrue(any("researcher" in error for error in result["failures"]))

    def test_completed_budget_failure_is_not_a_successful_handoff(self):
        sessions = self.tree()
        sessions[1]["items"][-1]["data"]["content"][0]["text"] = "You've hit the $0.30 cost budget."
        self.assertFalse(trace.verify_tree(sessions)["passed"])

    def test_ancillary_denial_after_valid_evidence_does_not_erase_recovery(self):
        sessions = self.tree()
        add_tool(sessions[1], "search_knowledge", {}, {"error": "Denied by policy: Exceeded10 calls"}, 24)
        result = trace.verify_tree(sessions)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(result["unsuccessful_tool_outputs"][0]["name"], "search_knowledge")

    def test_sequential_a_decision_then_b_and_second_analyst_record(self):
        sessions = self.tree()
        append_followup_b(self.root, sessions, self.assay)
        result = trace.verify_tree(sessions)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(len(result["completed_handoffs"]), 7)
        self.assertEqual(len(result["verified_numeric_receipts"]), 2)
        self.assertEqual(len(result["verified_discovery_records"]), 2)
        self.assertEqual(result["verified_discovery_records"][-1]["next_test"], "matched_input_and_sensory_validation")

    def test_denied_optional_followup_keeps_completed_a_loop_proof(self):
        sessions = self.tree()
        root = sessions[0]
        child_id = "9" * 32
        add_tool(root, "sys_session_send", {"agent": "experimenter"},
                 {"conversation_id": child_id, "agent": "experimenter", "status": "launching"}, 120)
        text = "[Denied by policy: Blocked by the session cost-budget policy: spend $2.12 reached $2.00]"
        sessions.append({"conversation_id": child_id, "parent_conversation_id": root["conversation_id"],
            "role": "experimenter", "live_status": 4, "items": [item(1, {"role": "assistant", "content": [{"type": "output_text", "text": text}]}, 0, 125)]})
        add_tool(root, "sys_read_inbox", {}, f"[System: sub-agent task {child_id} completed — experimenter:B returned: {text}]", 127)
        result = trace.verify_tree(sessions)
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(result["sessions_without_successful_collected_handoff"][0]["conversation_id"], child_id)

    def test_separate_b_root_reverifies_prior_a_once_and_keeps_distinct_roots(self):
        sessions, reference = separate_followup_b(self.root, self.assay)
        original_verify = trace.verify_tree
        visits = []
        def counted(tree, *args, **kwargs):
            visits.append(tree[0]["conversation_id"])
            return original_verify(tree, *args, **kwargs)
        with patch.object(trace, "verify_tree", side_effect=counted):
            result = trace.verify_tree(sessions, [reference, reference])
        self.assertTrue(result["passed"], result["failures"])
        self.assertEqual(visits.count("0" * 32), 1)
        proof = result["cross_session_followup_proofs"][0]
        self.assertEqual(proof["prior_root_conversation_id"], "0" * 32)
        self.assertEqual(proof["current_root_conversation_id"], "f" * 32)
        self.assertLess(proof["current_record_read"]["result_position"], proof["current_planner_launch_position"])

    def test_prior_true_boolean_cannot_replace_a_native_tree(self):
        sessions, reference = separate_followup_b(self.root, self.assay)
        path = self.root / reference["path"]
        prior = json.loads(path.read_text())
        prior["sessions"] = []
        write(path, prior)
        self.assertFalse(trace.verify_tree(sessions, [reference])["passed"])

    def test_prior_raw_hash_change_rejects_even_unchanged_spike_values(self):
        sessions, reference = separate_followup_b(self.root, self.assay)
        path = self.assay["first_run"] / "spikes.parquet"
        table = pq.read_table(path)
        pq.write_table(table, path, compression=None)
        result = trace.verify_tree(sessions, [reference])
        self.assertFalse(result["passed"])
        self.assertTrue(any("changed after recorded trace hashes" in error for error in result["failures"]))

    def test_prior_decision_read_after_current_plan_is_rejected(self):
        sessions, reference = separate_followup_b(self.root, self.assay)
        sessions[0]["items"][1]["position"] = 999
        self.assertFalse(trace.verify_tree(sessions, [reference])["passed"])

    def test_prior_trace_cycle_is_rejected(self):
        sessions, reference = separate_followup_b(self.root, self.assay)
        path = self.root / reference["path"]
        prior = json.loads(path.read_text())
        prior["prior_traces"] = [reference]
        write(path, prior)
        result = trace.verify_tree(sessions, [reference])
        self.assertFalse(result["passed"])
        self.assertTrue(any("Cycle" in error for error in result["failures"]))

    def test_planner_cannot_be_started_before_evidence_handoff(self):
        sessions = self.tree()
        reviewer_inbox = next(i for i in sessions[0]["items"] if i["type"] == 3 and "evidence_reviewer:fixture" in str(i["data"]))
        reviewer_inbox["position"] = 999
        result = trace.verify_tree(sessions)
        self.assertFalse(result["passed"])
        self.assertTrue(any("before preceding handoff" in e for e in result["failures"]))

    def test_raw_spike_mutation_rejects_numeric_receipt(self):
        event = {"output": self.assay["output"]}
        self.assertEqual(trace.numeric_integrity(event)["next_test"], "B")
        pq.write_table(pa.table({"t_seconds": [0.01], "flywire_id": ["20"]}), self.assay["first_run"] / "spikes.parquet")
        with self.assertRaisesRegex(ValueError, "spike count"):
            trace.numeric_integrity(event)

    def test_decision_cannot_contradict_frozen_result(self):
        sessions = self.tree()
        analyst = sessions[-1]
        event = next(e for e in trace.tool_events(analyst) if e["name"] == "save_discovery_record")
        record_path = self.root / event["output"]["path"]
        record = json.loads(record_path.read_text())
        record["next_test"] = "calibration"
        write(record_path, record)
        call = next(i for i in analyst["items"] if i["type"] == 2)
        submitted = json.loads(json.loads(call["data"]["arguments"])["record_json"])
        submitted["next_test"] = "calibration"
        call["data"]["arguments"] = json.dumps({"record_json": json.dumps(submitted)})
        result = trace.verify_tree(sessions)
        self.assertFalse(result["passed"])
        self.assertTrue(any("next_test" in error for error in result["failures"]))

    def test_uncompleted_native_tool_call_and_actual_metadata(self):
        sessions = self.tree()
        sessions[0]["items"].append(item(2, {"name": "apply_patch", "call_id": "unreturned"}, 100, 150, status=0))
        result = trace.verify_tree(sessions)
        self.assertFalse(result["no_arbitrary_shell_or_apply_patch_observed"])
        self.assertEqual(trace.runtime_labels([], sessions), {"harness": "unknown", "model": "unknown"})
        self.assertEqual(trace.runtime_labels([json.dumps({"executor": {"model": "actual-model", "config": {"harness": "codex"}}})], sessions),
                         {"harness": "codex", "model": "actual-model"})


if __name__ == "__main__":
    unittest.main()

"""Measure repeated local DNg02 identity lookup; no end-to-end discovery claim."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import statistics
import time

from scripts.kb_store import LocalKnowledgeBase

ROOT = Path(__file__).resolve().parents[1]


def benchmark(annotation_tsv: Path, repeats: int = 5) -> dict:
    if not 3 <= repeats <= 10:
        raise ValueError("Use3..10 repeats for this bounded benchmark")
    target = json.loads((ROOT / "research/evidence/dng02_targets.json").read_text())
    if hashlib.sha256(annotation_tsv.read_bytes()).hexdigest() != target["annotation_sha256"]:
        raise ValueError("The original annotation snapshot does not match")
    completeness = ROOT / "data/brain/flywire783/Completeness_783.csv"
    if hashlib.sha256(completeness.read_bytes()).hexdigest() != target["completeness_sha256"]:
        raise ValueError("The installed v783 completeness table does not match")
    expected = sorted(target["readout_ids"])
    kb = LocalKnowledgeBase()
    def full_scan():
        with completeness.open() as stream:
            installed_ids = {row[0] for row in list(csv.reader(stream))[1:]}
        with annotation_tsv.open() as stream:
            ids = sorted(row["root_id"] for row in csv.DictReader(stream, delimiter="\t")
                         if row["cell_type"].startswith("DNg02"))
        if not set(ids) <= installed_ids:
            raise ValueError("An annotated DNg02 identity is missing from the installed graph")
        return ids
    def reviewed_kb_lookup():
        rows = kb.query("pinned official v783 annotation", "claims", 100)
        candidates = [row for row in rows if row["claim_kind"] == "extraction" and
                      row["review_status"] == "checked" and "DNg02" in row["cell_types"]]
        if len(candidates) != 1:
            raise ValueError("Need exactly one reviewed identity-extraction claim")
        return sorted(candidates[0]["neuron_ids"])
    # Both sources have already been read; this measures repeat local retrieval.
    assert full_scan() == reviewed_kb_lookup() == expected
    raw = []
    for repetition in range(repeats):
        order = ["full_annotation_scan", "reviewed_kb_lookup"] if repetition % 2 == 0 else ["reviewed_kb_lookup", "full_annotation_scan"]
        for method in order:
            began = time.perf_counter_ns()
            ids = full_scan() if method == "full_annotation_scan" else reviewed_kb_lookup()
            elapsed_ms = (time.perf_counter_ns() - began) / 1_000_000
            if ids != expected:
                raise ValueError("Compared methods did not return the same identities")
            raw.append({"repeat": repetition + 1, "method": method, "wall_ms": elapsed_ms,
                        "returned_neuron_ids": ids, "identical_result": True})
    medians = {method: statistics.median(row["wall_ms"] for row in raw if row["method"] == method)
               for method in ["full_annotation_scan", "reviewed_kb_lookup"]}
    result = {"schema_version": 1, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "Retrieve the same25 reviewed DNg02 v783 IDs with their previously validated graph membership",
        "actual_bottleneck": "Repeatedly decoding a31MB annotation TSV and3.3MB completeness CSV for an unchanged identity question",
        "environment": {"python": platform.python_version(), "system": platform.system(), "machine": platform.machine()},
        "methodology": "One untimed warmup per method; five alternating-order repetitions; same process; warm local filesystem; no network; imports and one-time evidence review excluded",
        "repeats_per_method": repeats, "annotation_file_bytes": annotation_tsv.stat().st_size,
        "completeness_file_bytes": completeness.stat().st_size, "raw_measurements": raw,
        "median_wall_ms": medians,
        "observed_repeated_lookup_ratio": medians["full_annotation_scan"] / medians["reviewed_kb_lookup"],
        "absolute_median_ms_saved": medians["full_annotation_scan"] - medians["reviewed_kb_lookup"],
        "identity_validation": "Every timed lookup returned exactly the same25 sorted IDs",
        "annotation_source_sha256": target["annotation_sha256"], "limitations": [
            "This measures reuse of a small reviewed extraction after paying the initial evidence review cost.",
            "It is not total research/discovery acceleration, neural simulation acceleration, or an accuracy improvement.",
            "The cached claim is valid for the pinned snapshot; changed data require renewed identity validation.",
            "Both methods benefit from warm OS filesystem caching; cold starts and network costs were not measured.",
            "A repeated direct JSON-file lookup may be similarly fast; the benefit comes from retaining a checked extraction, not from a novel database algorithm."]}
    output = ROOT / "data/experiments/evidence_lookup_benchmark.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations-tsv", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(benchmark(args.annotations_tsv, args.repeats), indent=2))

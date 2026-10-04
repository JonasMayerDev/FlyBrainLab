"""Import actual public snapshots and reviewed DNg02 claims into the local KB.

The HTML/TSV arguments must be actual retrieved files. This writes KB records
outside iCloud by default and emits a small, portable receipt inside the project.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.kb_store import LocalKnowledgeBase

ROOT = Path(__file__).resolve().parents[1]


def import_evidence(annotation_tsv: Path, namiki_html: Path, shiu_html: Path,
                    directory: str | Path | None = None) -> dict:
    import pandas as pd
    targets = json.loads((ROOT / "research/evidence/dng02_targets.json").read_text())
    if hashlib.sha256(annotation_tsv.read_bytes()).hexdigest() != targets["annotation_sha256"]:
        raise ValueError("Annotation file does not match the pinned official release")
    namiki_text, shiu_text = namiki_html.read_text(), shiu_html.read_text()
    if "A population of descending neurons" not in namiki_text or "wingbeat amplitude" not in namiki_text:
        raise ValueError("The Namiki source file is not the actual expected article")
    if "A Drosophila computational brain model" not in shiu_text or "feeding" not in shiu_text:
        raise ValueError("The Shiu source file is not the actual expected article")
    annotations = pd.read_csv(annotation_tsv, sep="\t", dtype=str)
    selected_ids = targets["readout_ids"] + targets["upstream_stimulus_ids"]
    actual_rows = annotations[annotations.root_id.isin(selected_ids)].to_csv(sep="\t", index=False)
    kb = LocalKnowledgeBase(directory)
    sources = {}
    specs = [
        ("namiki", {"url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9206711/",
            "title": "Namiki et al. 2022 — A population of descending neurons that regulate the flight motor of Drosophila",
            "publication_date": "2022-01-31", "source_kind": "paper", "retrieval_status": "retrieved",
            "dataset_version": "live adult female Drosophila experimental preparations", "license": "CC-BY-4.0",
            "limitations": ["Experimental cell populations and GAL4 lines are not exact one-to-one FlyWire root mappings."]}, namiki_text),
        ("annotations", {"url": targets["annotation_url"],
            "title": "Schlegel et al. official FlyWire v783 annotation table, pinned v2.1.0",
            "publication_date": "2024", "source_kind": "dataset", "retrieval_status": "retrieved",
            "dataset_version": "FAFB FlyWire v783 / annotations v2.1.0", "license": "Source attribution retained; no separate repository license detected",
            "source_file_sha256": targets["annotation_sha256"], "snapshot_scope": "Actual TSV rows for25 DNg02 and8 selected upstream cells; complete original table hash recorded",
            "limitations": ["The local snapshot is an explicit selected-row excerpt, not the full annotation table."]}, actual_rows),
        ("shiu", {"url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/",
            "title": "Shiu et al. 2024 — A Drosophila computational brain model reveals sensorimotor processing",
            "publication_date": "2024-10-02", "source_kind": "paper", "retrieval_status": "retrieved",
            "dataset_version": "Published v630 model with authors' v783 data option", "license": "CC-BY-4.0",
            "limitations": ["Published biological validation focuses on feeding and grooming, not a connected flight body."]}, shiu_text),
        ("code", {"url": "https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/model.py",
            "title": "Shiu author LIF model.py at pinned commit91bdd1e7",
            "publication_date": None, "source_kind": "code", "retrieval_status": "retrieved",
            "dataset_version": "FAFB FlyWire v783 configured locally", "license": "MIT",
            "limitations": ["Undeclared reset assignment w=0 is removed locally; author source unchanged."]}, (ROOT / "simulation/vendor/shiu/model.py").read_text()),
    ]
    for name, metadata, actual_content in specs:
        sources[name] = kb.add_source(metadata, actual_content)
    common = {"dataset_version": "FAFB FlyWire v783", "review_status": "checked",
        "created_by": "Codex source review and exact local graph-ID check", "neuron_ids": targets["readout_ids"],
        "cell_types": ["DNg02"]}
    claim_specs = [
        {**common, "text": "In already-flying, tethered adult Drosophila, DNg02 population activation changed wingbeat amplitude. The paper relates response magnitude to the number of cells activated, and imaging supports different left/right activity under visual motion. It does not establish this project's upstream inputs, motor gain, or autonomous flight.",
            "claim_kind": "reported_finding", "evidence_type": "optogenetic perturbation and two-photon functional imaging",
            "source_ids": [sources["namiki"]["source_id"]], "source_location": "Summary; Results, Figures3A-B and4; paragraphs P8/P9/P15/P16 in saved HTML",
            "conditions": "Genetically modified female flies; tethered flight;100ms optogenetic pulses; closed-loop visual conditions",
            "limitations": ["Experiments presuppose a flying preparation.", "No validated mapping from spike rate to our virtual body's actuator gain."]},
        {**common, "text": "The pinned official v783 annotation release contains25 DNg02_a..g cells (13 left,12 right). Every selected root ID matches the installed author's138639-row completeness table. These25 identities form the frozen DNg02 readout.",
            "claim_kind": "extraction", "evidence_type": "official cell-type annotations plus exact local index membership validation",
            "source_ids": [sources["annotations"]["source_id"]], "source_location": "TSV cell_type prefix DNg02; research/evidence/dng02_targets.json neurons/readout_groups; full source hash30be6c73...",
            "conditions": "Same v783 materialization; annotation releasev2.1.0; no v630 or BANC ID substitution",
            "limitations": ["Subtype pooling does not identify every experimental split-GAL4 target.", "Some predicted neurotransmitters differ; numerical signs come from the installed connectivity weights."]},
        {**common, "text": "The published whole-brain LIF model was validated with feeding and antennal-grooming circuits. It uses initially silent neurons and simplified signed synaptic weights. The brain volume omits the complete descending-neuron motor circuit, so a DNg02 firing prediction does not validate flight.",
            "claim_kind": "reported_finding", "evidence_type": "primary model description and reported validation scope",
            "source_ids": [sources["shiu"]["source_id"]], "source_location": "Main: baseline firing0Hz; feeding/grooming validation; Methods; paragraph explaining incomplete descending-neuron circuits",
            "conditions": "Author's simplified LIF circuit-model validation; our local configuration uses public v783 data",
            "limitations": ["No new biological validation of the DNg02 assay.", "Absolute model firing rates should not be interpreted as calibrated biological rates."]},
        {**common, "text": "Eight right-side upstream neurons chosen before simulation by descending positive connectivity weight onto the DNg02 population are predicted to increase DNg02 mean firing; cutting their outgoing weights is predicted to reduce it by at least80%. This is the preregistered agent-generated model hypothesis.",
            "claim_kind": "hypothesis", "evidence_type": "graph-informed in-silico hypothesis",
            "neuron_ids": selected_ids, "source_ids": [sources["annotations"]["source_id"], sources["code"]["source_id"]],
            "source_location": "research/designs/dng02-input-v1.json and research/evidence/dng02_targets.json upstream_ranking",
            "conditions": "200ms;150Hz independent Poisson drive; seeds42,43,44; all installed cells and edges retained",
            "limitations": ["Most selected inputs lack a named cell type.", "Input selection by graph weight is not proof of a natural sensory pathway.", "Support would be a model prediction, not discovered biological flight function."]},
    ]
    existing_claims = kb.query("", "claims", 100)
    claims = []
    for record in claim_specs:
        existing = next((item for item in existing_claims
                         if item["text"] == record["text"] and
                         item["source_ids"] == record["source_ids"]), None)
        claims.append(existing or kb.add_claim(record))
    receipt = {"schema_version": 1, "sources": {name: {key: source[key] for key in
        ["source_id", "url", "retrieval_status", "content_sha256", "snapshot_path"]} for name, source in sources.items()},
        "claim_ids": [claim["claim_id"] for claim in claims], "knowledgebase": kb.summary(),
        "source_snapshot_note": "Actual retrieved contents; no search-snippet evidence is promoted to a finding."}
    (ROOT / "research/evidence/kb_import_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations-tsv", type=Path, required=True)
    parser.add_argument("--namiki-html", type=Path, required=True)
    parser.add_argument("--shiu-html", type=Path, required=True)
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(import_evidence(args.annotations_tsv, args.namiki_html, args.shiu_html, args.directory), indent=2))

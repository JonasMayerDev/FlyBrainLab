"""Expert board of the Embodied Fly Lab.

Lab hypothesis: a simulated whole-brain fly model, driven with the *real* stimuli
reported in published experiments (activation / silencing of identified neurons),
reproduces the fly's real behaviour repertoire - checked in simulation, one
behaviour at a time.

The specialist agents of agents/fly_lab.yaml form an expert board. Each round the
board reviews earlier results, discusses, picks the next stimulus (an impulse from
the literature catalogue data/ground_truth.json), runs it and decides what follows.
This module provides

  * EXPERTS            - who sits on the board and which decision each one owns,
  * behavior_coverage  - which behaviours of the repertoire the lab has reproduced,
                         contradicted or never tested (from benchmarks + live runs),
  * prior_results      - a compact digest of earlier research sessions, so the next
                         discussion starts from what the lab already learned,
  * export_board       - web/data/board.json for the discussion page (web/board.html).

Everything is read from committed files (runs/*/record.jsonl, data/benchmarks,
data/ground_truth.json). Nothing is invented: a session that did not read earlier
sessions is exported as such.

CLI:
    python3 -m flylab.board export            # writes web/data/board.json
    python3 -m flylab.board watch             # re-exports on every record change (live sessions)
    python3 -m flylab.board coverage          # prints the repertoire table
    python3 -m flylab.board prior             # prints the digest agents receive
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flylab import record

ROOT = record.ROOT
GROUND_TRUTH = ROOT / "data" / "ground_truth.json"
BENCH = ROOT / "data" / "benchmarks"
WEB_DATA = ROOT / "web" / "data"
BOARD_JSON = WEB_DATA / "board.json"

HYPOTHESIS = {
    "en": ("Does the wiring diagram alone predict how a fly's brain responds? If we give the copied fly brain the same "
           "nudges as published experiments on real flies, do the same command neurons switch on (and the others stay "
           "off) as in the real fly?"),
    "de": ("Reicht der Schaltplan allein, um die Reaktion des Fliegengehirns vorherzusagen? Wenn wir dem kopierten Gehirn "
           "dieselben Reize geben wie in veröffentlichten Experimenten, schalten sich dieselben Kommandoneuronen ein "
           "wie bei der echten Fliege?"),
    "vision": ("Long-term goal (unchanged): a virtual fly that behaves like a real one, up to flight. Body movements "
               "need a simulated nerve cord first; today the body only illustrates the brain's decision."),
}

# Board members = the Omnigent specialists (agents/fly_lab.yaml). "speaks_for" is the discipline the
# role represents on the board; "decides" is the decision the agent owns (same wording as the agent cards).
EXPERTS = [
    {"id": "human", "name": "Human PI", "speaks_for": "Scientist", "color": "#6b665d",
     "decides": "sets the research question and approves consequential actions"},
    {"id": "supervisor", "name": "Chair", "speaks_for": "Principal investigator", "color": "#b0722f",
     "decides": "agenda, hand-offs, whether a result reopens an assumption, when to stop"},
    {"id": "literature", "name": "Literature expert", "speaks_for": "Behavioural neuroscience", "color": "#2f6fb0",
     "decides": "which published findings count as evidence and where the gaps are"},
    {"id": "hypothesis", "name": "Connectome expert", "speaks_for": "Connectomics", "color": "#7a4fb3",
     "decides": "which candidate neurons to stimulate and what each hypothesis predicts"},
    {"id": "planner", "name": "Experiment designer", "speaks_for": "Experimental design", "color": "#1f7a72",
     "decides": "which of at least two competing tests to run (information gain vs. cost, budget)"},
    {"id": "safety", "name": "Safety officer", "speaks_for": "Safety and approval", "color": "#b3261e",
     "decides": "whether a plan is within budget and caps and must go to the human"},
    {"id": "runner", "name": "Simulation engineer", "speaks_for": "Simulation", "color": "#5a6b2f",
     "decides": "nothing scientific: runs exactly the approved stimuli"},
    {"id": "movement_verifier", "name": "Biomechanics expert", "speaks_for": "Movement verification",
     "color": "#c2410c", "decides": "did the body really perform the expected movement?"},
    {"id": "analysis", "name": "Data analyst", "speaks_for": "Analysis vs. literature", "color": "#0e7490",
     "decides": "verdict of each result against the published experiment and which results are surprises"},
    {"id": "record_keeper", "name": "Record keeper", "speaks_for": "Scientific record", "color": "#57534e",
     "decides": "whether the record supports each claim of the final report"},
]
_EXPERT_IDS = {e["id"] for e in EXPERTS}

# The behaviour repertoire the lab can address, in display order. "body" says where the simulated
# behaviour becomes visible: walking body, flight body, or only as a brain read-out (no body for it).
REPERTOIRE = [
    {"id": "forward", "label": "Forward walking", "body": "walking body", "plain": "Walking ahead"},
    {"id": "backward", "label": "Backward walking (retreat)", "body": "walking body", "plain": "Backing away from danger"},
    {"id": "turn_left", "label": "Turning left", "body": "walking body", "plain": "Steering to the left"},
    {"id": "turn_right", "label": "Turning right", "body": "walking body", "plain": "Steering to the right"},
    {"id": "escape", "label": "Escape takeoff", "body": "flight body", "plain": "Jumping into the air when something comes at it"},
    {"id": "flight_power", "label": "Flight power (wingbeat amplitude)", "body": "flight body", "plain": "Flapping harder to fly up"},
    {"id": "feed", "label": "Feeding", "body": "brain read-out only", "plain": "Starting to eat when it tastes sugar"},
    {"id": "groom", "label": "Grooming", "body": "brain read-out only", "plain": "Cleaning its antennae"},
]
# Plain names for the neuron groups the lab stimulates or reads out (simple view of web/board.html).
GLOSSARY = {
    "GF": "escape neuron (giant fiber)", "MDN": "moonwalker neurons (backward walking)",
    "P9": "forward-walking neurons", "DNa01": "steering neurons", "DNa02": "steering neurons",
    "DNg02": "wing-power neurons", "MN9": "swallowing neuron", "LPLC2": "eye neurons that see something approaching",
    "LC4": "eye neurons that see something approaching", "LC6": "eye neurons (type LC6)", "LC15": "eye neurons (type LC15)",
    "LC16": "eye neurons (type LC16)", "LC17": "eye neurons (type LC17)", "LC": "eye neurons",
    "sugar_GRN_shiu2024": "sugar-taste neurons", "JO_CE_shiu2024": "antenna touch neurons",
    "bitter_GRN_shiu2024": "bitter-taste neurons", "water_GRN_shiu2024": "water-taste neurons",
    "P9_L": "forward-walking neurons on the left side", "DNa02_L": "steering neurons on the left side",
    "DNa02_R": "steering neurons on the right side", "aBN1": "grooming command neurons (aBN1)",
    "DNg07": "grooming neurons (DNg07)", "aDN1_shiu2024": "grooming command neurons (aDN1)",
}
PLAIN_FILE = ROOT / "data" / "plain_summaries.json"

# Body videos for the simple view. They ILLUSTRATE a brain result: the brain decides how strongly the command
# neuron fires (number taken from the benchmark row / run artifact); the movement follows from the bridge rule.
MEDIA = [
    {"id": "lplc2_strong", "src": "assets/flight/LPLC2_bilateral.mp4", "bench": ("flight_validation", "LPLC2_bilateral"),
     "group": "GF", "nudge": "LPLC2 eye neurons (see something approaching), strong nudge: 150 pulses/s",
     "kind": "brain decides"},
    {"id": "lplc2_30", "src": "assets/flight/LPLC2_30Hz.mp4", "bench": ("flight_validation", "LPLC2_30Hz"),
     "group": "GF", "nudge": "LPLC2 eye neurons, gentle nudge: 30 pulses/s", "kind": "brain decides"},
    {"id": "lplc2_10", "src": "assets/flight/LPLC2_10Hz.mp4", "bench": ("flight_validation", "LPLC2_10Hz"),
     "group": "GF", "nudge": "LPLC2 eye neurons, very gentle nudge: 10 pulses/s", "kind": "brain decides"},
    {"id": "lc17_s3", "src": "runs/20261004-120628-at-lower-realistic-drive-rates-1-064e/artifacts/flight_01.mp4",
     "artifact": "runs/20261004-120628-at-lower-realistic-drive-rates-1-064e/artifacts/flight_01.json",
     "group": "GF", "nudge": "LC17 eye neurons (the surprise of experiment 3), gentle nudge: 14 pulses/s", "kind": "brain decides"},
    {"id": "lplc2_walk", "src": "assets/embodied/LPLC2_bilateral.mp4", "bench": ("embodied_validation", "LPLC2_bilateral"),
     "group": "MDN", "nudge": "LPLC2 eye neurons on the walking fly (real flies may back away)", "kind": "brain decides"},
    {"id": "mdn_direct", "src": "assets/embodied/MDN_bilateral.mp4", "bench": ("embodied_validation", "MDN_bilateral"),
     "group": "MDN", "nudge": "the moonwalker neurons themselves, switched on directly", "kind": "built in"},
]
TAKEOFF_HZ = 0.5 * 148.3  # flylab.bridge: take-off when the mean escape-neuron rate reaches half the reference rate


def _media() -> list[dict]:
    """Copy the selected videos into web/media/ and attach the brain number each one illustrates."""
    import shutil

    out_dir = WEB_DATA.parent / "media"
    out_dir.mkdir(parents=True, exist_ok=True)
    benches = {n: {r["condition"]: r for r in (_load_json(BENCH / f"{n}.json") or {}).get("rows", [])}
               for n in ("flight_validation", "embodied_validation")}
    items = []
    for m in MEDIA:
        src = ROOT / m["src"]
        if not src.exists():
            continue
        g = m["group"]
        if "bench" in m:
            row = benches[m["bench"][0]].get(m["bench"][1]) or {}
            k = row.get("key_group_rates_hz") or {}
            rate = (float(k.get(f"{g}_L", 0)) + float(k.get(f"{g}_R", 0))) / 2
            body = row.get("behavior")
            source = f"data/benchmarks/{m['bench'][0]}.json ({m['bench'][1]})"
        else:
            a = _load_json(ROOT / m["artifact"]) or {}
            rate = float((a.get("descending_group_rates_hz") or {}).get(g, 0.0))
            body = (a.get("flight") or {}).get("behavior")
            source = m["artifact"]
        dest = out_dir / f"{m['id']}.mp4"
        if not dest.exists() or dest.stat().st_size != src.stat().st_size:
            shutil.copyfile(src, dest)
        items.append({"id": m["id"], "video": f"media/{m['id']}.mp4", "nudge": m["nudge"], "group": g,
                      "group_plain": GLOSSARY.get(g, g), "rate_hz": round(rate, 1), "body": body, "kind": m["kind"],
                      "threshold_hz": round(TAKEOFF_HZ, 1) if g == "GF" else None, "source": source})
    return items
# Real behaviours for which the lab has NO catalogued published stimulus yet (gaps, not claims).
NOT_CATALOGUED = ["courtship song", "aggression", "egg laying", "landing", "flight saccades / steering in flight",
                  "phototaxis", "sleep"]

# Groups the frozen bridge / flight adapter reads directly: stimulating them tests the adapter, not the brain.
_ADAPTER_INPUTS = {"MDN", "P9", "P9_L", "P9_R", "DNa01", "DNa01_L", "DNa01_R", "DNa02", "DNa02_L", "DNa02_R",
                   "GF", "GF_L", "GF_R", "DNg02", "DNg02_L", "DNg02_R", "MN9"}
LIVE_WINDOW_S = 900  # a session without final report whose last event is younger than this counts as running
_ARTIFACT_RE = re.compile(r"\b((?:embodied|brain|screen|flightbody|flight|body)_\d+)\b", re.IGNORECASE)
_GT_RE = re.compile(r"\b(gt\d{2}_[a-z0-9_]+)\b", re.IGNORECASE)
_SESSION_REF_RE = re.compile(r"\b(S\d+)[/:·]((?:embodied|brain|screen|flightbody|flight|body)_\d+)\b")


# =========================================================================== helpers


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _ground_truth() -> dict[str, dict]:
    d = _load_json(GROUND_TRUTH) or {}
    return {e["id"]: e for e in d.get("entries", [])}


def _is_mock_run(run_id: str, events: list[dict]) -> str | None:
    """Reason why a run is not a real session (mock data or no experiment), else None."""
    if "mock" in run_id.lower():
        return "mock pipeline test (folder name)"
    for e in events:
        d = e.get("data")
        if isinstance(d, dict) and d.get("mock") is True:
            return "contains MOCK tool results"
    if not any(e.get("type") == "experiment_result" for e in events):
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(events[-1]["ts"])).total_seconds()
        except (IndexError, KeyError, ValueError, TypeError):
            age = None
        if age is None or age > LIVE_WINDOW_S or "selftest" in run_id:
            return "no experiment result recorded"
    return None


def real_sessions() -> list[tuple[str, list[dict]]]:
    """Real research sessions (oldest first) with their events; mock / empty runs are skipped."""
    out = []
    for rid in sorted(record.list_runs()):
        events = record.load(rid)
        if _is_mock_run(rid, events) is None:
            out.append((rid, events))
    return out


def _exp_name(artifact: Any) -> str | None:
    if not artifact:
        return None
    m = _ARTIFACT_RE.search(Path(str(artifact)).name)
    return m.group(1).lower() if m else None


def _top_rates(rates: dict | None, n: int = 4, min_hz: float = 0.5) -> dict[str, float]:
    """Highest bilateral group rates (skip _L/_R duplicates when the bilateral group is present)."""
    rates = rates or {}
    keys = [k for k in rates if not (k.endswith(("_L", "_R")) and k[:-2] in rates)]
    top = sorted(((k, float(rates[k])) for k in keys if float(rates[k] or 0) >= min_hz), key=lambda kv: -kv[1])
    return {k: round(v, 1) for k, v in top[:n]}


def _short(text: str, n: int) -> str:
    text = str(text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _experiment(sid: str, e: dict) -> dict | None:
    d = e.get("data") or {}
    name = _exp_name(d.get("artifact"))
    if not name:
        return None
    kind = d.get("kind", "?")
    ex = {"id": f"{sid}/{name}", "session": sid, "name": name, "seq": e.get("seq"), "ts": e.get("ts"),
          "kind": kind, "excite": d.get("excite") or [], "silence": d.get("silence") or [],
          "seed": d.get("seed"), "rate_hz": d.get("rate_hz"), "runtime_s": d.get("runtime_s"),
          "summary": e.get("content", ""), "mock": bool(d.get("mock"))}
    if kind == "screen":
        rows = d.get("rows") or []
        ex["excite"] = d.get("candidates") or [r.get("cell_type") for r in rows]
        ex["targets"] = d.get("target_groups") or []
        ex["screen"] = [{"cell_type": r.get("cell_type"), "rates": r.get("target_rates"), "hits": r.get("hit_targets")}
                        for r in rows]
        ex["hits_by_target"] = d.get("hits_by_target")
        ex["runtime_s"] = d.get("runtime_s")
    else:
        ex["readout_hz"] = _top_rates(d.get("descending_group_rates_hz"))
        ex["n_active"] = d.get("n_active")
    if kind == "embodied":
        ex["body"] = {"behavior": d.get("behavior"), "forward_disp_mm": d.get("forward_disp_mm"),
                      "heading_change_deg": d.get("heading_change_deg"), "drive": d.get("drive"),
                      "label_warning": d.get("label_warning")}
    if kind == "embodied_flight":
        ex["body"] = {"behavior": d.get("behavior"), "airborne": d.get("airborne"),
                      "max_height_mm": d.get("max_height_mm"), "command": d.get("command")}
    return ex


def _refs(text: str, sid: str, known: set[str]) -> list[str]:
    """Experiment ids mentioned in a text: 'flight_01' (same session) or 'S1/brain_02' (other session)."""
    out: list[str] = []
    for m in _SESSION_REF_RE.finditer(text):
        ref = f"{m.group(1)}/{m.group(2).lower()}"
        if ref in known and ref not in out:
            out.append(ref)
    for m in _ARTIFACT_RE.finditer(text):
        ref = f"{sid}/{m.group(1).lower()}"
        if ref in known and ref not in out:
            out.append(ref)
    return out


# =========================================================================== behaviour coverage


def _test(source: str, verdict: str, label_source: str, circular: bool, verifier: str | None = None,
          ref: str | None = None, note: str = "") -> dict:
    return {"source": source, "verdict": verdict, "label_source": label_source, "circular": circular,
            "verifier": verifier, "ref": ref, "note": note}


def behavior_coverage(sessions: list[tuple[str, list[dict]]] | None = None) -> dict:
    """Which behaviours of the repertoire the lab has reproduced, contradicted or not tested yet.

    A literature impulse (ground-truth entry) counts as tested when a committed benchmark row or a
    live analysis event compared a simulated result with it. Status per behaviour:
      reproduced_body   - consistent with a body run (walking / flight), not only by adapter design
      reproduced_brain  - consistent only as a brain read-out (no body movement, or adapter-circular)
      conflict          - at least one inconsistent comparison
      untested          - no comparison yet
    """
    gt = _ground_truth()
    tests: dict[str, list[dict]] = {k: [] for k in gt}

    emb = _load_json(BENCH / "embodied_validation.json") or {}
    for r in emb.get("rows", []):
        gid = r.get("gt_id")
        if gid in tests:
            beh = gt[gid]["expected_behavior"]
            body = beh in ("forward", "backward", "turn_left", "turn_right")
            circ = all(g in _ADAPTER_INPUTS for g in r.get("stimulus_groups") or []) and bool(r.get("stimulus_groups"))
            tests[gid].append(_test("benchmark: embodied_validation", r.get("verdict", "?"),
                                    "walking body" if body else "brain read-out", circ, None,
                                    f"replay:{r.get('condition')}", r.get("note") or ""))
    fl = _load_json(BENCH / "flight_validation.json") or {}
    rows = {r.get("condition"): r for r in fl.get("rows", [])}
    for key, verdict in ((fl.get("summary") or {}).get("verdicts") or {}).items():
        cond, _, gid = key.partition(":")
        if gid in tests:
            r = rows.get(cond, {})
            ver = (r.get("verification") or {}).get("final_verdict") if isinstance(r.get("verification"), dict) else None
            circ = "circular" in str(r.get("result_type", "")) or all(
                g in _ADAPTER_INPUTS for g in r.get("stimulus_groups") or [])
            tests[gid].append(_test("benchmark: flight_validation", verdict, "flight body", circ, ver, f"replay:{cond}"))

    for sid, rid, events in _numbered(sessions):
        for e in events:
            d = e.get("data") or {}
            if e.get("type") != "analysis" or not isinstance(d, dict) or d.get("ground_truth_id") not in tests:
                continue
            ls = str(d.get("label_source") or "")
            body = ls.startswith("body")
            mv = d.get("movement_verified")
            tests[d["ground_truth_id"]].append(_test(
                f"live session {sid}", d.get("verdict", "?"),
                ("flight body" if "flight" in str(d.get("experiment_ref", "")) else "walking body") if body else "brain read-out",
                bool(d.get("by_construction")), None if mv is None else ("correct" if mv else "not confirmed"),
                f"{sid}/{_exp_name(d.get('experiment_ref')) or '?'}", d.get("note") or ""))

    behaviors = []
    for b in REPERTOIRE:
        impulses = []
        for gid, entry in gt.items():
            if entry.get("expected_behavior") != b["id"]:
                continue
            c = entry.get("citation") or {}
            impulses.append({"gt_id": gid, "manipulation": entry.get("manipulation"), "target": entry.get("target_group"),
                             "effect": entry.get("effect"), "evidence": entry.get("evidence"),
                             "confidence": entry.get("confidence"),
                             "citation": {"doi": c.get("doi"), "title": c.get("title"), "year": c.get("year"),
                                          "first_author": str(c.get("authors", "")).split(",")[0].strip()},
                             "tests": tests.get(gid, [])})
        all_t = [t for i in impulses for t in i["tests"] if t["verdict"] in ("consistent", "inconsistent", "partially_consistent")]
        if any(t["verdict"] == "inconsistent" for t in all_t):
            status = "conflict"
        elif any(t["verdict"] == "consistent" and t["label_source"] != "brain read-out" and not t["circular"]
                 and t["verifier"] not in ("uncertain", "incorrect", "not confirmed") for t in all_t):
            status = "reproduced_body"
        elif any(t["verdict"] == "consistent" for t in all_t):
            status = "reproduced_brain"
        else:
            status = "untested"
        n_tested = sum(1 for i in impulses if i["tests"])
        behaviors.append({**b, "status": status, "n_impulses": len(impulses), "n_tested": n_tested, "impulses": impulses})

    counts: dict[str, int] = {}
    for b in behaviors:
        counts[b["status"]] = counts.get(b["status"], 0) + 1
    return {"behaviors": behaviors, "counts": counts, "not_catalogued": NOT_CATALOGUED,
            "n_impulses": len(gt), "n_impulses_tested": sum(1 for v in tests.values() if v)}


# =========================================================================== brain-level score (lab hypothesis)


def brain_score(cov: dict | None = None) -> dict:
    """Score of the lab hypothesis at brain level: for every published experiment that nudges SENSORY / UPSTREAM
    neurons (not a group the bridge reads, not the read-out itself), did the copied brain's command neurons respond
    as in the real fly? Brain read-out comparisons count first; a body run of such a stimulus counts through its
    brain part. Experiments that nudge bridge inputs are listed as pipeline checks (true by construction)."""
    cov = cov or behavior_coverage()
    gt = _ground_truth()
    items, checks = [], []
    for b in cov["behaviors"]:
        for i in b["impulses"]:
            entry = gt.get(i["gt_id"], {})
            row = {**{k: i[k] for k in ("gt_id", "manipulation", "target", "effect", "citation")}, "behavior": b["id"],
                   "behavior_plain": b.get("plain") or b["label"], "readout": entry.get("readout_group"),
                   "readout_plain": GLOSSARY.get(entry.get("readout_group") or "", entry.get("readout_group")),
                   "target_plain": GLOSSARY.get(i["target"], i["target"])}
            if i["target"] in _ADAPTER_INPUTS:
                checks.append({**row, "n_tests": len(i["tests"])})
                continue
            brain = [t for t in i["tests"] if t["label_source"] == "brain read-out"] or \
                    [t for t in i["tests"] if not t["circular"]]
            vs = {t["verdict"] for t in brain}
            verdict = ("untested" if not brain else "depends" if {"consistent", "inconsistent"} <= vs
                       else "disagrees" if "inconsistent" in vs else "agrees" if "consistent" in vs else "unclear")
            items.append({**row, "verdict": verdict, "n_tests": len(brain),
                          "sources": sorted({t["source"] for t in brain})})
    n = {v: sum(1 for x in items if x["verdict"] == v) for v in ("agrees", "depends", "disagrees", "unclear", "untested")}
    return {"items": items, "pipeline_checks": checks, "counts": n, "n_total": len(items),
            "n_conclusive": n["agrees"] + n["depends"] + n["disagrees"],
            "rule": "counted: published experiments that nudge sensory/upstream neurons; excluded: nudging the "
                    "neurons the brain-to-body link reads (true by construction)"}


# =========================================================================== prior results (input to the next round)


def _numbered(sessions: list[tuple[str, list[dict]]] | None = None):
    sessions = real_sessions() if sessions is None else sessions
    for i, (rid, events) in enumerate(sessions, start=1):
        yield f"S{i}", rid, events


def prior_results(exclude_run_id: str = "", max_sessions: int = 5) -> dict:
    """Compact digest of earlier sessions: experiments with key numbers, verdicts, surprises, reopened
    assumptions and the proposed next step. This is what the board reads before it discusses a new round."""
    out = []
    for sid, rid, events in _numbered():
        if rid == exclude_run_id:
            continue
        exps = [x for x in (_experiment(sid, e) for e in events if e.get("type") == "experiment_result") if x]
        verdicts = [{"gt_id": (e.get("data") or {}).get("ground_truth_id"), "verdict": (e.get("data") or {}).get("verdict"),
                     "on": f"{sid}/{_exp_name((e.get('data') or {}).get('experiment_ref')) or '?'}",
                     "surprise": bool((e.get("data") or {}).get("surprise"))}
                    for e in events if e.get("type") == "analysis" and isinstance(e.get("data"), dict)
                    and (e.get("data") or {}).get("ground_truth_id")]
        checks = [{"on": f"{sid}/{_exp_name((e.get('data') or {}).get('artifact'))}",
                   "expected": (e.get("data") or {}).get("expected_behavior"),
                   "final_verdict": (e.get("data") or {}).get("final_verdict")}
                  for e in events if e.get("type") == "movement_verification"]
        decisions = [{"decision": _short(e.get("content"), 240),
                      "reopens_assumption": (e.get("data") or {}).get("reopens_assumption"),
                      "next_step": (e.get("data") or {}).get("next_step")}
                     for e in events if e.get("type") == "decision" and e.get("agent") == "supervisor"]
        out.append({"session": sid, "run_id": rid, "question": events[0].get("content") if events else "",
                    "experiments": [{"id": x["id"], "kind": x["kind"], "excite": x["excite"][:12], "silence": x["silence"],
                                     "readout_hz": x.get("readout_hz"), "body": x.get("body"),
                                     "hits_by_target": x.get("hits_by_target")} for x in exps],
                    "literature_verdicts": verdicts, "movement_checks": checks, "decisions": decisions})
    out = out[-max_sessions:]
    cov = behavior_coverage()
    return {"hypothesis": HYPOTHESIS["en"], "sessions": out,
            "repertoire": [{"behavior": b["id"], "status": b["status"], "impulses_tested": f"{b['n_tested']}/{b['n_impulses']}"}
                           for b in cov["behaviors"]],
            "untested_or_conflicting": [b["id"] for b in cov["behaviors"] if b["status"] in ("untested", "conflict")],
            "how_to_cite": "Refer to an earlier experiment as <session>/<artifact>, e.g. S1/brain_02."}


# =========================================================================== web export


def _replay_index() -> list[dict]:
    idx = _load_json(WEB_DATA / "runs" / "index.json") or {}
    out = []
    for r in idx.get("runs", []):
        run = _load_json(WEB_DATA.parent / r["file"]) or {}
        s = run.get("stimulus") or {}
        out.append({"id": r["id"], "title": r["title"], "mode": r["mode"], "kind": r.get("kind"),
                    "excite": sorted(s.get("excite") or []), "silence": sorted(s.get("silence") or []),
                    "rate": s.get("excite_rate_hz")})
    return out


def _match_replay(ex: dict, replays: list[dict]) -> dict | None:
    """3D replay with the same stimulus (recomputed by flylab.export3d; not the identical run)."""
    if ex["kind"] == "screen":
        return None
    mode = "flight" if ex["kind"] in ("embodied_flight", "flight") or "GF" in ex["silence"] else "walk"
    cands = [r for r in replays if r["excite"] == sorted(ex["excite"]) and r["silence"] == sorted(ex["silence"])
             and r["kind"] != "negative_control" and (ex.get("rate_hz") in (None, r["rate"]))]
    cands.sort(key=lambda r: r["mode"] != mode)
    return {"id": cands[0]["id"], "title": cands[0]["title"]} if cands else None


def _post(sid: str, e: dict, known: set[str]) -> dict:
    d = e.get("data") if isinstance(e.get("data"), dict) else {}
    t = e.get("type")
    p: dict[str, Any] = {"seq": e.get("seq"), "ts": e.get("ts"), "agent": e.get("agent"), "type": t,
                         "text": _short(e.get("content"), 2400), "citations": e.get("citations") or []}
    blob = e.get("content", "") + " " + json.dumps(d, ensure_ascii=False) if d else e.get("content", "")
    if t == "experiment_result":
        name = _exp_name(d.get("artifact"))
        p["result"] = f"{sid}/{name}" if name else None
        p["refs"] = []
    else:
        p["refs"] = _refs(blob, sid, known)
    if t == "evidence" and d.get("hits"):
        p["hits"] = [{"title": h.get("title"), "year": h.get("year"), "doi": h.get("doi")} for h in d["hits"][:8]]
    if t == "evidence" and d.get("top"):
        p["ranking"] = [{"rank": r.get("rank"), "cell_type": r.get("cell_type"), "score": round(float(r.get("score", 0)), 1),
                         "note": r.get("sign_note")} for r in d["top"][:10]]
    if t == "hypothesis":
        p["hypothesis"] = {"id": d.get("hypothesis_id"), "predicted": d.get("predicted_behavior"),
                           "targets": d.get("target_groups"), "confidence": d.get("confidence")}
    if t == "experiment_options":
        p["options"] = [{"id": o.get("id"), "kind": o.get("kind"), "cost": o.get("est_cost_units"),
                         "gain": o.get("expected_information_gain"), "tests": o.get("tests_hypothesis"),
                         "why": _short(o.get("why") or o.get("description"), 400)}
                        for o in d.get("options", []) if isinstance(o, dict)]
        p["budget"] = d.get("budget_units")
    if t == "experiment_choice":
        p["choice"] = {"id": d.get("chosen_id"), "rationale": _short(d.get("rationale"), 900)}
    if t == "approval":
        p["approval"] = {"status": d.get("status"), "cost": d.get("est_cost_units"), "gate": d.get("gate")}
    if t == "movement_verification":
        p["verification"] = {"on": f"{sid}/{_exp_name(d.get('artifact'))}", "expected": d.get("expected_behavior"),
                             "source": d.get("expected_source"), "final": d.get("final_verdict"),
                             "kinematic": (d.get("kinematic") or {}).get("verdict"),
                             "vision": (d.get("vision") or {}).get("verdict"),
                             "vision_saw": (d.get("vision") or {}).get("observed_behavior"),
                             "vision_conf": (d.get("vision") or {}).get("confidence")}
    if t == "analysis" and d.get("ground_truth_id"):
        p["comparison"] = {"gt_id": d.get("ground_truth_id"), "expected": d.get("expected"), "observed": d.get("observed"),
                           "verdict": d.get("verdict"), "surprise": bool(d.get("surprise")),
                           "label_source": d.get("label_source"), "by_construction": bool(d.get("by_construction")),
                           "movement_verified": d.get("movement_verified"), "on": _exp_name(d.get("experiment_ref"))}
    if t == "decision":
        p["decision"] = {"reason": d.get("reason"), "next_step": d.get("next_step"),
                         "reopens_assumption": d.get("reopens_assumption")}
    if t == "board_statement":
        p["stance"] = d.get("stance")
        p["refs"] = list(dict.fromkeys([*(r for r in (d.get("refs") or []) if r in known), *p["refs"]]))
    if t == "prior_review":
        p["reviewed"] = [r for r in (d.get("experiments") or []) if r in known]
        p["refs"] = list(dict.fromkeys([*p["reviewed"], *p["refs"]]))
    if t == "note" and d.get("parallel_batch"):
        p["parallel"] = {"n": len(d.get("artifacts") or []), "wall_s": d.get("wall_s"),
                         "sum_s": d.get("sum_runtime_s"), "speedup": d.get("speedup")}
    return p


def _audit_summary(rid: str, n_events: int) -> dict | None:
    """runs/<rid>/audit.json (flylab.audit), slimmed for the page; flagged stale if the record grew since."""
    a = _load_json(record.RUNS_DIR / rid / "audit.json")
    if not a:
        return None
    return {"summary": a["summary"], "audited_at": a["audited_at"], "replicated": a["replicated"],
            "stale": a.get("n_events_audited") != n_events, "proves": a.get("proves"),
            "does_not_prove": a.get("does_not_prove"), "reproduce": a.get("reproduce"),
            "checks": [{k: c[k] for k in ("id", "title", "status", "detail")} for c in a["checks"]]}


def _git_rev() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def build_board() -> dict:
    sessions = real_sessions()
    replays = _replay_index()
    skipped = []
    for rid in sorted(record.list_runs()):
        why = _is_mock_run(rid, record.load(rid))
        if why:
            skipped.append({"run_id": rid, "reason": why})

    experiments: dict[str, dict] = {}
    for sid, rid, events in _numbered(sessions):
        for e in events:
            if e.get("type") == "experiment_result":
                ex = _experiment(sid, e)
                if ex:
                    ex["run_id"] = rid
                    ex["replay"] = _match_replay(ex, replays)
                    ex["verifications"], ex["comparisons"], ex["used_by"] = [], [], []
                    experiments[ex["id"]] = ex
    known = set(experiments)

    plain = (_load_json(PLAIN_FILE) or {}).get("sessions", {})
    out_sessions = []
    for sid, rid, events in _numbered(sessions):
        rounds: list[dict] = [{"n": 1, "posts": []}]
        for e in events:
            rounds[-1]["posts"].append(_post(sid, e, known))
            if e.get("type") == "decision" and e.get("agent") == "supervisor":
                rounds.append({"n": len(rounds) + 1, "posts": []})
        rounds = [r for r in rounds if r["posts"]]
        for i, r in enumerate(rounds):
            only_report = all(p["agent"] == "record_keeper" for p in r["posts"])
            r["title"] = "Final report" if only_report else f"Round {r['n']}"
            r["experiments"] = [p["result"] for p in r["posts"] if p.get("result")]
            for x in r["experiments"]:
                experiments[x]["round"] = r["n"]
            opened = rounds[i - 1]["posts"][-1] if i > 0 else None
            r["opened_by"] = opened["seq"] if opened and opened["type"] == "decision" else None
            own = set(r["experiments"])
            carried = []
            for p in ([opened] if opened else []) + r["posts"]:
                if p["type"] == "prior_review":  # a full review lists everything; only explicit citations count
                    continue
                for ref in p.get("refs", []):
                    if ref not in own and ref not in carried:
                        carried.append(ref)
            r["carried_forward"] = carried
            r["reviewed_earlier"] = sorted({x for p in r["posts"] if p["type"] == "prior_review" for x in p.get("reviewed", [])})
            decision = next((p for p in reversed(r["posts"]) if p["type"] == "decision" and p["agent"] == "supervisor"), None)
            r["decision_seq"] = decision["seq"] if decision else None
        for r in rounds:
            for p in r["posts"]:
                for ref in p.get("refs", []):
                    tag = {"session": sid, "round": r["n"], "seq": p["seq"], "agent": p["agent"], "type": p["type"]}
                    if tag not in experiments[ref]["used_by"]:
                        experiments[ref]["used_by"].append(tag)
                if p.get("verification") and p["verification"]["on"] in experiments:
                    experiments[p["verification"]["on"]]["verifications"].append(p["verification"])
                c = p.get("comparison")
                if c and c.get("on") and f"{sid}/{c['on']}" in experiments:
                    experiments[f"{sid}/{c['on']}"]["comparisons"].append(c)
        reviewed = sorted({ref for r in rounds for p in r["posts"] if p["type"] != "prior_review"
                           for ref in p.get("refs", []) if not ref.startswith(sid + "/")})
        cost = next((float(m.group(1)) for e in events for m in [re.search(r"\$(\d+\.\d+)", e.get("content", ""))] if m), None)
        finished = any(e.get("agent") == "record_keeper" and e.get("type") == "decision" for e in events)
        try:
            age_s = (datetime.now(timezone.utc) - datetime.fromisoformat(events[-1]["ts"])).total_seconds()
        except (KeyError, ValueError, TypeError):
            age_s = None
        status = "finished" if finished else ("running" if age_s is not None and age_s < LIVE_WINDOW_S else "stopped")
        out_sessions.append({"id": sid, "run_id": rid, "question": events[0].get("content", ""), "status": status,
                             "last_event_age_s": None if age_s is None else round(age_s),
                             "started": events[0].get("ts"), "ended": events[-1].get("ts"),
                             "n_events": len(events), "rounds": rounds, "earlier_results_cited": reviewed,
                             "read_prior_sessions": any(p["type"] == "prior_review" for r in rounds for p in r["posts"]),
                             "llm_cost_usd_mentioned": cost,
                             "plain": plain.get(rid), "audit": _audit_summary(rid, len(events)),
                             "record": f"runs/{rid}/record.jsonl"})

    counts: dict[str, int] = {e["id"]: 0 for e in EXPERTS}
    for s in out_sessions:
        for r in s["rounds"]:
            for p in r["posts"]:
                counts[p["agent"]] = counts.get(p["agent"], 0) + 1

    return {"format": "flylab-board-v1", "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "git_rev": _git_rev(), "hypothesis": HYPOTHESIS,
            "experts": [{**e, "n_posts": counts.get(e["id"], 0)} for e in EXPERTS],
            "coverage": behavior_coverage(sessions), "sessions": out_sessions,
            "experiments": list(experiments.values()), "skipped_runs": skipped, "glossary": GLOSSARY,
            "media": _media(), "brain_score": brain_score(),
            "reproduce": "python3 -m flylab.board export"}


def watch(path: Path = BOARD_JSON, interval_s: float = 3.0) -> None:
    """Re-export whenever a research record changes, so web/board.html can follow a live session."""
    import time

    last: tuple = ()
    while True:
        stamp = tuple(sorted((str(p), p.stat().st_mtime_ns) for p in record.RUNS_DIR.glob("*/record.jsonl")))
        if stamp != last:
            export_board(path)
            b = json.loads(path.read_text(encoding="utf-8"))
            live = [s["id"] for s in b["sessions"] if s["status"] == "running"]
            print(f"[board] {datetime.now().strftime('%H:%M:%S')} exported: {len(b['sessions'])} sessions, "
                  f"{len(b['experiments'])} experiments, running: {', '.join(live) or 'none'}", flush=True)
            last = stamp
        time.sleep(interval_s)


def export_board(path: Path = BOARD_JSON) -> Path:
    board = build_board()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(board, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Embodied Fly Lab expert board")
    ap.add_argument("cmd", choices=["export", "watch", "coverage", "prior"])
    ap.add_argument("--out", default=str(BOARD_JSON))
    a = ap.parse_args()
    if a.cmd == "export":
        p = export_board(Path(a.out))
        b = json.loads(p.read_text(encoding="utf-8"))
        print(f"wrote {p.relative_to(ROOT)}: {len(b['sessions'])} sessions, {len(b['experiments'])} experiments, "
              f"{sum(len(s['rounds']) for s in b['sessions'])} rounds; skipped {len(b['skipped_runs'])}")
    elif a.cmd == "watch":
        watch(Path(a.out))
    elif a.cmd == "coverage":
        cov = behavior_coverage()
        for b in cov["behaviors"]:
            print(f"{b['label']:<36} {b['status']:<17} impulses tested {b['n_tested']}/{b['n_impulses']}")
        print(f"not catalogued yet: {', '.join(cov['not_catalogued'])}")
    else:
        print(json.dumps(prior_results(), indent=1, ensure_ascii=False))

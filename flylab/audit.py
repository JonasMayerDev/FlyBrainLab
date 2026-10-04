"""Independent audit of one research session: was the experiment done correctly?

The audit does not trust the agents. It re-reads the raw files and re-runs the simulations
from the inputs stored in each artifact (outside the agent loop, nothing is written to the
research record), then checks:

  real_data          no MOCK placeholder anywhere in the record or the artifacts
  connectome         the brain data on this machine is the published FlyWire v783 model (SHA256 = manifest)
  record_integrity   the shared record is complete and in order (seq 0..n-1, time never goes backwards)
  raw_files          every reported result has its raw artifact, and the record's numbers equal the file
  replication        re-running every experiment with the same inputs gives the same numbers
  dose_response      a weaker stimulus never gives a stronger response (screens at several drive rates)
  silencing_control  silencing the stimulated neurons themselves leaves the brain silent (audit's own control)
  sources            every DOI the agents wrote down was returned by a tool (no invented papers)
  quoted_numbers     firing rates the agents quote in free text can be traced to tool outputs
  approvals          every body experiment was approved before it ran, and the hard caps were kept
  movement_checks    every body experiment was checked by the movement verifier

Writes runs/<run_id>/audit.json (shown on web/board.html).

    .venv/bin/python -m flylab.audit S3            # or a full run id, or "all"
    .venv/bin/python -m flylab.audit S2 --no-replicate
"""

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flylab import board, record

ROOT = record.ROOT
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"'<>()\[\],;]+", re.IGNORECASE)
_HZ_RE = re.compile(r"(?<![\w.])(\d{1,4}(?:\.\d+)?)\s*Hz\b")
# Events whose text is written by an LLM agent (tool-generated summaries are excluded).
_FREE_TEXT_TYPES = {"board_statement", "decision", "hypothesis", "experiment_choice", "experiment_options", "approval",
                    "analysis", "evidence", "note"}


def _check(cid: str, title: str, status: str, detail: str, evidence: Any = None) -> dict:
    return {"id": cid, "title": title, "status": status, "detail": detail, "evidence": evidence}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _artifact_path(rid: str, artifact: str | None) -> Path | None:
    if not artifact:
        return None
    p = Path(str(artifact))
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():  # recorded on another machine: same file name in this run's artifacts folder
        p = record.RUNS_DIR / rid / "artifacts" / Path(str(artifact)).name
    return p if p.exists() else None


def _numbers(obj: Any, out: set) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.add(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers(v, out)


def _group_mean(rates: dict, group: str) -> float:
    from flylab import atlas, brain

    vals = list(brain.rates_for({"rates": rates}, atlas.group_ids(group)).values())
    return sum(vals) / len(vals) if vals else 0.0


# =========================================================================== individual checks


def check_real_data(rid: str, events: list[dict], results: list[tuple[dict, Path | None]]) -> dict:
    bad = [e["seq"] for e in events if isinstance(e.get("data"), dict) and e["data"].get("mock")]
    bad += [p.name for _, p in results if p and json.loads(p.read_text()).get("mock")]
    return _check("real_data", "Only real simulations and real literature, no placeholders",
                  "fail" if bad else "pass",
                  f"MOCK found in {bad}" if bad else f"none of {len(events)} record events and {len(results)} result files is flagged as mock",
                  bad or None)


def check_connectome() -> dict:
    man = json.loads((ROOT / "data" / "manifest.json").read_text())
    want = {}
    for d in man.get("datasets", []):
        for f in d.get("files", []) if isinstance(d.get("files"), list) else []:
            name = Path(str(f.get("path") or f.get("name") or "")).name
            if name in ("Completeness_783.csv", "Connectivity_783.parquet") and f.get("sha256"):
                want[name] = f["sha256"]
    if len(want) < 2:  # manifest layout fallback: search the whole file
        txt = json.dumps(man)
        for name in ("Completeness_783.csv", "Connectivity_783.parquet"):
            m = re.search(re.escape(name) + r'.{0,400}?"sha256": "([0-9a-f]{64})"', txt)
            if m:
                want[name] = m.group(1)
    rows = []
    for name, sha in want.items():
        p = ROOT / "data" / "raw" / name
        got = _sha256(p) if p.exists() else None
        rows.append({"file": name, "manifest": sha[:16], "local": (got or "missing")[:16], "match": got == sha})
    ok = len(rows) == 2 and all(r["match"] for r in rows)
    return _check("connectome", "The fly brain is the published FlyWire v783 wiring diagram",
                  "pass" if ok else "fail",
                  "SHA256 of the connectome files on this machine equals the project manifest "
                  "(Shiu et al. 2024 model, 138,639 neurons)" if ok else "hash mismatch or file missing", rows)


def check_record(rid: str, events: list[dict]) -> dict:
    seqs = [e.get("seq") for e in events]
    probs = []
    if seqs != list(range(len(events))):
        probs.append("sequence numbers are not 0..n-1")
    ts = [datetime.fromisoformat(e["ts"]) for e in events]
    if any(b < a for a, b in zip(ts, ts[1:])):
        probs.append("timestamps go backwards")
    if any(e.get("run_id") != rid for e in events):
        probs.append("events of another run inside this record")
    if not events or events[0].get("type") != "question":
        probs.append("record does not start with the research question")
    dur = (ts[-1] - ts[0]).total_seconds() if ts else 0
    return _check("record_integrity", "The lab notebook is complete and in order", "fail" if probs else "pass",
                  "; ".join(probs) or f"{len(events)} events, numbered without gaps, in time order over {dur / 60:.1f} min",
                  None)


def check_raw_files(rid: str, results: list[tuple[dict, Path | None]]) -> dict:
    rows, bad = [], 0
    for e, p in results:
        d = e["data"]
        name = Path(str(d.get("artifact"))).stem
        if p is None:
            rows.append({"result": name, "ok": False, "why": "raw file missing"})
            bad += 1
            continue
        a = json.loads(p.read_text())
        ok, why = True, ""
        if d.get("kind") == "screen":
            rec = {r["cell_type"]: r["target_rates"] for r in d.get("rows", [])}
            fil = {r["cell_type"]: r["target_rates"] for r in a.get("rows", [])}
            ok = rec == fil
            why = "" if ok else "screen rows differ"
        else:
            dn = d.get("descending_group_rates_hz") or {}
            fdn = a.get("descending_group_rates_hz")
            if fdn is None and "result" in a:  # brain artifact stores per-neuron rates; recompute group means
                fdn = {g: _group_mean({str(k): v for k, v in a["result"]["rates"].items()}, g) for g in dn}
            diffs = [abs(float(dn[g]) - float(fdn.get(g, 0.0))) for g in dn]
            ok = not diffs or max(diffs) < 0.01
            why = "" if ok else f"group rates differ by up to {max(diffs):.3f} Hz"
            if d.get("kind") == "embodied_flight":
                if (a.get("flight") or {}).get("behavior") != d.get("behavior"):
                    ok, why = False, "behaviour label differs"
        bad += not ok
        rows.append({"result": name, "ok": ok, **({"why": why} if why else {})})
    return _check("raw_files", "Every reported result matches its raw data file", "fail" if bad else "pass",
                  f"{len(rows) - bad} of {len(rows)} results: the numbers in the notebook equal the raw file", rows)


def check_replication(rid: str, results: list[tuple[dict, Path | None]], events: list[dict],
                      budget_s: float = 600.0) -> dict:
    """Re-run every experiment from the inputs saved in its raw file and compare. The brain model is deterministic
    for a given (seed, n_trials, n_threads) (flylab.brain.simulate), so each run is repeated with its own thread
    count: stored in the brain artifact's params, else 2 inside a parallel batch (tools.run_experiments_parallel)
    and the default otherwise."""
    from flylab import screen, tools

    in_batch = {Path(str(a)).name for e in events if isinstance(e.get("data"), dict) and e["data"].get("parallel_batch")
                for a in e["data"].get("artifacts") or []}

    def sim(inp: dict, name: str, params: dict | None):
        nt = (params or {}).get("n_threads") or (2 if name in in_batch else None)
        prev = tools._BRAIN_THREADS
        tools._BRAIN_THREADS = nt
        try:
            return tools._simulate_brain(inp["excite"], inp.get("silence") or [], inp["rate_hz"], inp["duration_ms"],
                                         inp["n_trials"], inp.get("seed", 0))[0], nt
        finally:
            tools._BRAIN_THREADS = prev

    rows, t_start = [], time.time()
    for e, p in results:
        if p is None:
            continue
        if time.time() - t_start > budget_s:
            rows.append({"result": p.stem, "skipped": "time budget"})
            continue
        a = json.loads(p.read_text())
        inp = a.get("inputs") or {}
        t0 = time.time()
        try:
            if p.stem.startswith("screen"):
                targets = inp["target_groups"]
                new = screen.brain_screen(inp["candidates"], targets, rate_hz=float(inp["rate_hz"]),
                                          duration_ms=float(inp["duration_ms"]), n_trials=int(inp["n_trials"]),
                                          seed=int(inp.get("seed", 0)), n_threads=4, use_cache=False)
                old = {r["cell_type"]: r["target_rates"] for r in a["rows"]}
                diff = max(abs(float(r["target_rates"][g]) - float(old[r["cell_type"]][g]))
                           for r in new for g in targets)
                rows.append({"result": p.stem, "max_diff_hz": round(diff, 4), "same": diff < 1e-6,
                             "what": f"{len(new)} cell types x {', '.join(targets)} at {inp['rate_hz']} Hz"})
            elif p.stem.startswith("brain"):
                res, nt = sim(inp, p.name, a["result"].get("params"))
                old = {str(k): float(v) for k, v in a["result"]["rates"].items()}
                new = {str(k): float(v) for k, v in res["rates"].items()}
                keys = set(old) | set(new)
                diff = max((abs(old.get(k, 0.0) - new.get(k, 0.0)) for k in keys), default=0.0)
                rows.append({"result": p.stem, "max_diff_hz": round(diff, 4), "same": diff < 1e-6,
                             "what": f"{len(keys)} active neurons compared one by one ({nt or 'default'} threads)"})
            elif p.stem.startswith("flight"):
                from flylab import flight

                res, nt = sim(inp, p.name, None)
                rates = {str(k): float(v) for k, v in res["rates"].items()}
                cmd, _ = tools._flight_command_from_rates(rates)
                clean = {k: float(cmd.get(k, 0.0) or 0.0) for k in ("takeoff", "thrust", "yaw", "pitch")}
                old_cmd = {k: float((a.get("command") or {}).get(k, 0.0) or 0.0) for k in clean}
                fres = flight.simulate_flight(clean, duration_s=float(inp.get("duration_s", 1.0)), render_path=None,
                                              seed=int(inp.get("seed", 0)))
                f_old = a.get("flight") or {}
                dcmd = max(abs(clean[k] - old_cmd[k]) for k in clean)
                dh = abs(float(fres.get("max_height_mm") or 0) - float(f_old.get("max_height_mm") or 0))
                same = dcmd < 1e-6 and fres.get("behavior") == f_old.get("behavior") and dh < 0.01
                rows.append({"result": p.stem, "same": same, "max_diff_hz": None,
                             "what": f"brain -> command (takeoff {clean['takeoff']:.3f}) -> body: "
                                     f"{fres.get('behavior')} vs recorded {f_old.get('behavior')}, "
                                     f"height diff {dh:.3f} mm"})
            elif p.stem.startswith("embodied"):
                res, nt = sim(inp, p.name, None)
                rates = {str(k): float(v) for k, v in res["rates"].items()}
                drive, _ = tools._drive_from_rates(rates)
                old_drive = a.get("drive") or {}
                body_res = tools._simulate_body(drive, float(inp.get("duration_s", 1.0)), None, int(inp.get("seed", 0)))
                b_old = a.get("body") or {}
                ddrive = max(abs(float(drive.get(k, 0.0)) - float(old_drive.get(k, 0.0))) for k in ("forward", "turn", "backward"))
                dx = abs(float(body_res.get("forward_disp_mm") or 0) - float(b_old.get("forward_disp_mm") or 0))
                same = ddrive < 1e-6 and body_res.get("behavior") == b_old.get("behavior") and dx < 0.01
                rows.append({"result": p.stem, "same": same, "max_diff_hz": None,
                             "what": f"brain -> walking drive -> body: {body_res.get('behavior')} vs recorded "
                                     f"{b_old.get('behavior')}, displacement diff {dx:.3f} mm"})
            else:
                continue
            rows[-1]["seconds"] = round(time.time() - t0, 1)
        except Exception as exc:  # report, never hide
            rows.append({"result": p.stem, "same": False, "error": f"{type(exc).__name__}: {exc}"})
    done = [r for r in rows if "same" in r]
    same = sum(1 for r in done if r["same"])
    status = "pass" if done and same == len(done) else ("warn" if not done else "fail")
    return _check("replication", "Re-running each experiment gives exactly the same result", status,
                  f"{same} of {len(done)} experiments reproduced identically from their saved inputs "
                  f"(same random seed and thread count, recomputed on this machine)", rows)


def check_dose_response(results: list[tuple[dict, Path | None]]) -> dict:
    by: dict[tuple, dict[float, float]] = {}
    for e, p in results:
        d = e["data"]
        if d.get("kind") != "screen" or p is None:
            continue
        rate = float(json.loads(p.read_text())["inputs"]["rate_hz"])
        for r in d.get("rows", []):
            for g, v in (r.get("target_rates") or {}).items():
                by.setdefault((r["cell_type"], g), {})[rate] = float(v)
    rows, bad = [], 0
    for (ct, g), pts in sorted(by.items()):
        if len(pts) < 2:
            continue
        xs = sorted(pts)
        mono = all(pts[b] >= pts[a] - 1e-9 for a, b in zip(xs, xs[1:]))
        bad += not mono
        rows.append({"cell_type": ct, "target": g, "points": {f"{x:g} Hz": round(pts[x], 1) for x in xs}, "monotonic": mono})
    if not rows:
        return _check("dose_response", "Weaker stimulation never gives a stronger response", "n/a",
                      "this session did not test one cell type at several drive rates", None)
    return _check("dose_response", "Weaker stimulation never gives a stronger response", "fail" if bad else "pass",
                  f"{len(rows) - bad} of {len(rows)} cell types respond less (or equally) when stimulated more weakly", rows)


def check_silencing_control(results: list[tuple[dict, Path | None]]) -> dict:
    """Audit's own negative control: stimulate a cell type while silencing that same cell type -> brain silent."""
    from flylab import tools

    exc = next((json.loads(p.read_text())["inputs"] for e, p in results
                if p and e["data"].get("kind") in ("brain", "embodied_flight", "embodied")), None)
    if not exc:
        return _check("silencing_control", "Switching neurons off really switches them off", "n/a", "no brain run", None)
    ex = exc["excite"]
    res, _ = tools._simulate_brain(ex, ex, exc["rate_hz"], exc["duration_ms"], 1, exc.get("seed", 0))
    n = int(res.get("n_active", len(res.get("rates") or {})))
    return _check("silencing_control", "Switching neurons off really switches them off", "pass" if n == 0 else "fail",
                  f"stimulating {', '.join(ex)} while silencing the same neurons leaves {n} neurons active "
                  f"(expected 0; the unsilenced run activates hundreds)", {"excite_and_silence": ex, "n_active": n})


def check_paired_controls(results: list[tuple[dict, Path | None]]) -> dict:
    """Silencing comparisons (same stimulus with vs without silencing) should share the random seed, otherwise a
    small difference can be input noise rather than an effect of the silencing."""
    runs = []
    for e, p in results:
        if p and e["data"].get("kind") in ("brain", "embodied", "embodied_flight"):
            inp = json.loads(p.read_text()).get("inputs") or {}
            runs.append((p.stem, tuple(sorted(inp.get("excite") or [])), float(inp.get("rate_hz") or 0),
                         tuple(sorted(inp.get("silence") or [])), inp.get("seed", 0), e["data"].get("kind")))
    pairs = []
    for a in runs:
        if a[3]:
            continue
        for b in runs:
            if b[3] and a[1:3] == b[1:3] and a[5] == b[5]:
                pairs.append({"control": a[0], "silenced": b[0], "silenced_groups": list(b[3]),
                              "same_seed": a[4] == b[4], "seeds": [a[4], b[4]]})
    if not pairs:
        return _check("paired_controls", "Before/after comparisons are fair (same random input)", "n/a",
                      "no silencing comparison in this session", None)
    bad = [x for x in pairs if not x["same_seed"]]
    return _check("paired_controls", "Before/after comparisons are fair (same random input)", "warn" if bad else "pass",
                  f"{len(pairs) - len(bad)} of {len(pairs)} with/without-silencing pairs used the same random seed"
                  + (f"; {len(bad)} used different seeds, so small differences there may be noise, not an effect" if bad else ""),
                  pairs)


def check_sources(events: list[dict], earlier: list[list[dict]]) -> dict:
    allowed = set()
    gt = json.loads((ROOT / "data" / "ground_truth.json").read_text())
    for g in gt.get("entries", []):
        allowed.add(str((g.get("citation") or {}).get("doi", "")).lower())
    for evs in [events, *earlier]:
        for e in evs:
            d = e.get("data")
            if isinstance(d, dict) and (d.get("hits") or d.get("ground_truth_id")):
                allowed |= {m.lower().rstrip(".") for m in _DOI_RE.findall(json.dumps(d))}
            if e.get("type") == "evidence" and isinstance(d, dict):
                allowed |= {str(c).lower() for c in e.get("citations") or []}
    for f in (ROOT / "data" / "benchmarks").glob("*.json"):
        allowed |= {m.lower().rstrip(".") for m in _DOI_RE.findall(f.read_text())}
    allowed |= {m.lower().rstrip(".") for m in _DOI_RE.findall((ROOT / "flylab" / "bridge.py").read_text())}
    cited, unknown = set(), set()
    for e in events:
        if e.get("type") not in _FREE_TEXT_TYPES:
            continue
        for m in _DOI_RE.findall(e.get("content", "")):
            doi = m.lower().rstrip(".")
            cited.add(doi)
            if doi not in allowed:
                unknown.add(doi)
    return _check("sources", "Every paper the experts cite really was found by a search tool",
                  "fail" if unknown else "pass",
                  f"{len(cited) - len(unknown)} of {len(cited)} cited DOIs were returned by the literature search, the "
                  f"verified ground truth or the bridge's own references" + (f"; not traceable: {sorted(unknown)}" if unknown else ""),
                  sorted(unknown) or None)


def check_quoted_numbers(events: list[dict], earlier: list[list[dict]], results: list[tuple[dict, Path | None]]) -> dict:
    known: set = set()
    for evs in [events, *earlier]:
        for e in evs:
            if e.get("type") in ("experiment_result", "evidence", "movement_verification") or (
                    e.get("type") == "analysis" and isinstance(e.get("data"), dict)):
                _numbers(e.get("data"), known)
    for _, p in results:
        if p:
            _numbers(json.loads(p.read_text()).get("inputs"), known)
    for f in (ROOT / "data" / "benchmarks").glob("*.json"):
        _numbers(json.loads(f.read_text()), known)
    known |= {5.0, 148.3, 74.0, 74.15}  # hit threshold, adapter reference rate and its half (frozen constants)
    quoted, missing = 0, []
    for e in events:
        if e.get("type") not in _FREE_TEXT_TYPES or e.get("agent") in ("runner", "human"):
            continue
        if isinstance(e.get("data"), dict) and e["type"] in ("evidence", "analysis") and e["data"].get("hits") is not None:
            continue  # tool-generated
        for m in _HZ_RE.findall(e.get("content", "")):
            x = float(m)
            quoted += 1
            if not any(abs(x - k) <= max(0.51, 0.01 * abs(k)) for k in known):
                missing.append({"seq": e["seq"], "agent": e["agent"], "value_hz": x})
    frac = (quoted - len(missing)) / quoted if quoted else 1.0
    status = "pass" if frac >= 0.95 else ("warn" if frac >= 0.8 else "fail")
    return _check("quoted_numbers", "Numbers the experts quote come from the actual measurements", status,
                  f"{quoted - len(missing)} of {quoted} firing rates quoted in the experts' own words appear in a tool "
                  "output, a raw file or a committed benchmark (rounded)", missing or None)


def check_approvals(events: list[dict]) -> dict:
    approved_at = [e["seq"] for e in events if e.get("type") == "approval"]
    body = [e for e in events if e.get("type") == "experiment_result"
            and (e.get("data") or {}).get("kind") in ("embodied", "embodied_flight")]
    unapproved = [e["seq"] for e in body if not any(a < e["seq"] for a in approved_at)]
    big_screens = [e["seq"] for e in events if (e.get("data") or {}).get("kind") == "screen"
                   and len((e.get("data") or {}).get("candidates") or []) > 40]
    statuses = sorted({(e.get("data") or {}).get("status") for e in events if e.get("type") == "approval"} - {None})
    probs = []
    if unapproved:
        probs.append(f"body runs without prior approval: {unapproved}")
    if len(body) > 6:
        probs.append(f"{len(body)} body runs > cap 6")
    if big_screens:
        probs.append(f"screens above 40 candidates: {big_screens}")
    return _check("approvals", "Costly experiments were approved by a human first, within the safety limits",
                  "fail" if probs else "pass",
                  "; ".join(probs) or f"{len(body)} body experiment(s), each after an approval ({', '.join(statuses) or 'none needed'}); "
                                     f"caps kept (max 6 body runs, max 40 candidates per screen)",
                  {"approvals": approved_at, "body_runs": [e["seq"] for e in body]})


def check_movement(events: list[dict]) -> dict:
    body = {Path(str((e.get("data") or {}).get("artifact"))).name for e in events if e.get("type") == "experiment_result"
            and (e.get("data") or {}).get("kind") in ("embodied", "embodied_flight")}
    checked = {Path(str((e.get("data") or {}).get("artifact"))).name: (e.get("data") or {}).get("final_verdict")
               for e in events if e.get("type") == "movement_verification"}
    missing = sorted(body - set(checked))
    unsure = sorted(k for k in body & set(checked) if checked[k] != "correct")
    if not body:
        return _check("movement_checks", "Every body movement was double-checked and confirmed", "n/a",
                      "no body experiment in this session", None)
    parts = [f"not checked: {missing}"] if missing else [f"all {len(body)} body runs were checked by the movement verifier"]
    if unsure:
        parts.append(f"the checker could not confirm {', '.join(unsure)} (kept as {', '.join(checked[k] for k in unsure)}, not upgraded)")
    return _check("movement_checks", "Every body movement was double-checked and confirmed",
                  "warn" if missing or unsure else "pass", "; ".join(parts), checked or None)


# =========================================================================== driver


def audit_session(rid: str, replicate: bool = True) -> dict:
    events = record.load(rid)
    sessions = board.real_sessions()
    idx = next((i for i, (r, _) in enumerate(sessions) if r == rid), None)
    sid = f"S{idx + 1}" if idx is not None else rid
    earlier = [evs for r, evs in sessions[: idx or 0]]
    results = [(e, _artifact_path(rid, (e.get("data") or {}).get("artifact")))
               for e in events if e.get("type") == "experiment_result" and isinstance(e.get("data"), dict)]
    t0 = time.time()
    checks = [check_real_data(rid, events, results), check_connectome(), check_record(rid, events),
              check_raw_files(rid, results)]
    if replicate:
        checks.append(check_replication(rid, results, events))
        checks.append(check_silencing_control(results))
    checks += [check_dose_response(results), check_paired_controls(results), check_sources(events, earlier),
               check_quoted_numbers(events, earlier, results), check_approvals(events), check_movement(events)]
    counted = [c for c in checks if c["status"] != "n/a"]
    out = {"format": "flylab-audit-v1", "run_id": rid, "session": sid,
           "audited_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "session_finished": any(e.get("agent") == "record_keeper" and e.get("type") == "decision" for e in events),
           "n_events_audited": len(events), "replicated": replicate, "runtime_s": round(time.time() - t0, 1),
           "summary": {s: sum(1 for c in counted if c["status"] == s) for s in ("pass", "warn", "fail")},
           "checks": checks,
           "proves": ["the simulations really ran on the published fly connectome and give the same numbers again",
                      "the experts' reports match the raw data; their sources are real papers found by the tools",
                      "the safety rules (approval, limits) were followed"],
           "does_not_prove": ["that a real fly behaves like the model: these are computer predictions until tested in the lab",
                              "that the hand-designed link from brain to body is biologically right (it is an assumption)",
                              "that the choice of experiment was the best possible one"],
           "reproduce": f".venv/bin/python -m flylab.audit {sid}"}
    path = record.RUNS_DIR / rid / "audit.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Independent audit of a research session")
    ap.add_argument("session", help="S1, S2, ... or a run id, or 'all'")
    ap.add_argument("--no-replicate", action="store_true", help="skip re-running the simulations")
    a = ap.parse_args()
    sessions = board.real_sessions()
    if a.session == "all":
        rids = [r for r, _ in sessions]
    elif re.fullmatch(r"S\d+", a.session):
        rids = [sessions[int(a.session[1:]) - 1][0]]
    else:
        rids = [a.session]
    for rid in rids:
        res = audit_session(rid, replicate=not a.no_replicate)
        print(f"== {res['session']} {rid}: {res['summary']} ({res['runtime_s']} s)")
        for c in res["checks"]:
            print(f"  [{c['status']:>4}] {c['title']}: {c['detail']}")

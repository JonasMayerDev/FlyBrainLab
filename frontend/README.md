# FlyBrainLab replay viewer

Public demo: https://valleebo.github.io/FlyBrainLab/

The canonical team repository remains `JonasMayerDev/FlyBrainLab`. Pages runs
on the explicitly configured hosting mirror `valleebo/FlyBrainLab`; the
workflow builds both repositories and deploys only the mirror.

## Run locally

```bash
# From the repository root, regenerate the recorded public data:
.venv/bin/python scripts/export_replays.py
cd frontend
npm ci
npm run dev
```

Production verification: `npm run build`; then `npm run preview`.
Node 24 or newer is used by CI. Dependency versions and the npm lockfile are
committed. No API credentials or server are needed by the static viewer.

## What the viewer displays

- Original completed Brian2 runs with exact FlyWire IDs stored as strings.
- Play/pause, keyboard-accessible millisecond timeline and adjustable replay
  length; playback stretches simulation time and does not run new experiments.
- An explicitly abstract neuron layout: targets, readouts, most active cells
  and sampled actual model IDs. It contains no anatomical coordinates or
  invented connectivity edges. Simulation scope and displayed sample are
  separate labels.
- Histograms computed from the complete recorded spike file. Individual
  event rendering is capped at 30,000 with the sampling method disclosed.
- Matched control runs, fixed-seed pooled summaries and recorded next
  decisions; independent feasibility is labeled separately by execution context.
- Dataset/model versions, parameters, source links and SHA-256 fingerprints.
- Verified Omnigent handoffs with actual session IDs, final-output and parent
  inbox hashes, observed tool names, fresh numerical receipts and the saved
  result-dependent analyst decision. Only independently verified raw run IDs
  are marked as native; a pending continuation is not presented as executed.
- Where an exact neural provenance link exists, the real Flybody root
  trajectory and six wing angles drive the original author Flybody meshes.
  The complete measured path stays at its actual scale: centimeters, z-up.
  Head, abdomen, legs and other unexported joints use the fixed compiled
  model reference pose. Playback stops at the recorded final state. An
  authors' published-policy replay takes priority over the earlier approximate
  wing controller for the same exact neural source; earlier diagnostics stay
  linked separately.
- Graceful WebGL fallback: the recorded data, controls, parameters and
  time histogram remain accessible when 3D is unavailable.

These model results do not validate biological flight. The default native-A
body replay uses the authors' independently trained flight policy and its
body feedback for the recorded 200 ms horizon. Neural input remains open loop,
and the fixed rate-to-wing adapter is biologically uncalibrated. Earlier
approximate-controller runs terminate early and remain separate diagnostics.
The body pose is a separate measured physics record, not a movement inferred
solely from stimulating a named neuron.

## Body geometry and framing

Open `?view=body` for the body view. Its camera follows the recorded fly at
the actual centimeter scale; turn off **Follow fly** to frame the whole path.
This changes the camera only. There is no procedural flapping, gait or
extrapolation: root position/orientation and six wing angles come from the replay.
Other joints stay at the author flight-task reference pose, including retracted legs.

`public/models/flybody/` contains 85 original meshes (272,550 triangles) from
the Apache-2.0 [Flybody author commit](https://github.com/TuragaLab/flybody/tree/d015e9bfe441bd90ae431bac24c55cb74bdbce26).
Source hashes, buffer descriptors and the independent four-pose MuJoCo
kinematics check are recorded in `manifest.json`; LICENSE and NOTICE accompany
the assets. The binary uses float32 positions and uint16 indices (3.14 MiB).
With the existing pinned `requirements.body.lock` runtime, reproduce only
the geometry export from the repository root:

```bash
.runtime/body-venv/bin/python scripts/export_flybody_geometry.py
```

That helper compiles the installed model and checks existing recorded poses;
it does not step the simulator, run a controller or regenerate scientific runs.

## Export contract

`scripts/export_replays.py` reads completed `data/runs/*/run.json` and the
referenced `spikes.parquet`; a preview is used only when the full spike file
is unavailable and is labeled incomplete when appropriate. The exporter
checks count consistency, exact IDs, finite duration and event time bounds.
It reads frozen scientific comparison records under `data/experiments/`
and links completed body records under `data/body/` only by exact source
neural run ID.

The native proof index is reduced from `data/discovery/native-trace.json` and,
when its separate strict audit passes, `data/discovery/native-trace-b.json`.
The exporter checks the trace's strict verification result, rechecks every
verified receipt artifact hash and the analyst-record hash, and publishes only
small proof metadata and specialist-output excerpts. It does not put the whole
session tree, source snapshots, authentication or hidden runtime state in the
browser. Each selected native test displays its own five handoffs and root
session; the other verified session is linked separately. Library cards identify
test A or B to distinguish repeated conditions. Native-A drive seed 42 is the
default when that verified record exists.
For a cross-session follow-up, the exporter also rechecks the preceding trace,
decision and receipt hashes and the native read-before-planning order. The pane
shows this proof separately without merging the two native root sessions.

Generated public files live in `data/replay/` and are committed. The build
copies these JSON exports into ignored `frontend/public/replays/` and
publishes them with relative asset paths, supporting a repository Pages
URL and a custom domain without a routing server. Raw source records stay
linked to the canonical team repository.

Browser QA artifacts are local in `frontend/output/playwright/`; they do
not feed the scientific data or the displayed dynamics.

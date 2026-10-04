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
- Where an exact neural provenance link exists, the real Flybody root
  trajectory is replayed as a schematic marker and its complete measured
  path. Coordinates are centimeters, z-up; no anatomy is inferred. The
  marker stops at the recorded early termination and is never extrapolated.
- Graceful WebGL fallback: the recorded data, controls, parameters and
  time histogram remain accessible when 3D is unavailable.

These model results do not validate biological flight. The current body
controller is an author-provided approximate wing pattern, open loop, and
terminates early. The body pose is a separate measured physics record, not
a movement inferred solely from stimulating a named neuron.

## Export contract

`scripts/export_replays.py` reads completed `data/runs/*/run.json` and the
referenced `spikes.parquet`; a preview is used only when the full spike file
is unavailable and is labeled incomplete when appropriate. The exporter
checks count consistency, exact IDs, finite duration and event time bounds.
It reads frozen scientific comparison records under `data/experiments/`
and links completed body records under `data/body/` only by exact source
neural run ID.

Generated public files live in `data/replay/` and are committed. The build
copies these JSON exports into ignored `frontend/public/replays/` and
publishes them with relative asset paths, supporting a repository Pages
URL and a custom domain without a routing server. Raw source records stay
linked to the canonical team repository.

Browser QA artifacts are local in `frontend/output/playwright/`; they do
not feed the scientific data or the displayed dynamics.

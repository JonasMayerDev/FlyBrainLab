# Texte für HackOS und das separate Google Form

**Vor Versand:** finale öffentliche URL prüfen, Namen/Rollen ergänzen und mögliche weitere neue Runs mit `README.md`/Trace abgleichen. Die nativen A- und B-Durchläufe sind streng verifiziert; B wurde nach A in einer zweiten, nachweislich verbundenen Omnigent-Sitzung ausgeführt. Die zusätzliche C3-Demo braucht ihren eigenen akzeptierten Einreichungsweg. Die v2-Kopplung mit veröffentlichter Autorenpolicy ist inzwischen über sechs tatsächlich gemessene 200-ms-Läufe belegt; die frühere v1-Diagnose bleibt separat erhalten.

Öffentliches Medienpaket: [Videoentwürfe und zusätzliche C3-Demo](https://github.com/JonasMayerDev/FlyBrainLab/releases/tag/demo-2026-10-04). Ein öffentlicher Downloadlink bestätigt noch keinen akzeptierten Einreichungsweg.

## Pflichtfelder

| Feld | Eintrag / Status |
|---|---|
| Project name | **FlyBrainLab** — Arbeitsname aus dem Repository; im Team bestätigen |
| Challenge | **Challenge 03 — Databricks: Agentic Scientific Discovery**; offizielle passende Auswahl wählen |
| GitHub repository | `https://github.com/JonasMayerDev/FlyBrainLab` |
| Live project URL | `https://valleebo.github.io/FlyBrainLab/` — öffentlicher Pages-Mirror, anonym im echten Browser geprüft; kanonischer Code bleibt im oben genannten Repository |
| Team | Vier tatsächliche Namen und Beiträge; außer Valentin noch nicht bestätigt |
| Team photo | Echtes Teamfoto, JPG/PNG/WebP, ≤10 MB |
| Team introduction | `team_intro.mp4`, 46-s-Textentwurf ohne Personen/Ton; bestätigte Teamgröße, Hub, Projektzweck und Arbeitsbereiche, menschliche Prüfung/Namen/Beiträge offen |
| Product demo | `product_demo.mp4`/`.mov`, ≤60 s/1 GB |
| Technical walkthrough | `technical_walkthrough.mp4`/`.mov`, ≤60 s/1 GB |
| Additional two-minute C3 demo | `c3_demo.mp4`; Upload-/Linkfeld im Google Form bzw. akzeptierten Weg klären |

## Kurzbeschreibung — Deutsch

FlyBrainLab verbindet wissenschaftliche Evidenz, kontrollierte Fliegengehirn-Simulationen und einen öffentlichen Replay-Viewer. Omnigent führt nachgewiesene, miteinander verbundene Forschungsloops aus. Acht vorab graphgewählte Inputs erhöhen den gemessenen Populationsoutput von 25 flugbezogenen DNg02-Zellen im vollständigen installierten FlyWire-v783-LIF-Modell. Der ergebnisabhängig gewählte zweite Test entfernt die Antwort durch Trennung der Ausgangsgewichte. Ein eingefrorener Adapter koppelt neue native Spike-Daten an Flybody/MuJoCo mit veröffentlichter Flugpolicy. Sechs Körperläufe erreichen 200 ms ohne vorzeitigen Abbruch; echte Gelenk- und Positionsunterschiede werden gemessen. Die bestehende Policy liefert die Stabilisierung, das Gehirn bleibt ohne sensorischen Rückkanal. Biologische Kalibrierung und längerfristig stabiler Flug bleiben offen. Quellen, Kontrollen, Run Records und die nächste Entscheidung sind überprüfbar.

## Short description — English

FlyBrainLab connects scientific evidence, controlled fly-brain simulations, and a public replay viewer. Omnigent executes verified, linked research loops. Eight graph-selected inputs raise the measured population output of 25 flight-related DNg02 cells in the complete installed FlyWire v783 LIF model. The result-dependent second test removes this response by disconnecting outgoing weights. A frozen adapter couples new native spike data to Flybody/MuJoCo with a published flight policy. Six body runs reach 200 ms without early termination and show measured joint and position differences. Stabilization comes from the existing policy; the brain has no sensory feedback. Biological calibration and longer-horizon flight remain open. Sources, controls, run records, and the next decision are inspectable.

## Problem and scientific question — English

Connectomes describe connections but do not automatically explain behavior. FlyBrainLab makes one constrained hypothesis test reproducible: can eight connectivity-selected upstream inputs evoke population activity across twenty-five flight-related DNg02 readouts, and does that response depend on the inputs’ outgoing connections? The question concerns a frozen numerical model. It does not assign an established biological function to unnamed input neurons or claim autonomous fly-brain emulation.

## What we built — English

The project uses pinned FlyWire v783 data, a published whole-network LIF model in Brian2, a provenance-aware local knowledgebase, frozen controlled experiment designs, and a Flybody/MuJoCo motor adapter. A static Vite/TypeScript/Three.js viewer replays actual exported runs with units, parameters, sources, and limitations. Omnigent uses specialist research, evidence-review, hypothesis-planning, experiment, and analysis roles.

## Agent workflow — English

Omnigent orchestrated two actual, linked native discovery sessions. Each persisted trace passes a strict audit of all five successful specialist handoffs, numerical-tool receipts, raw-spike integrity, and the analyst record. The workflow moves from question and evidence to the frozen hypothesis, executes Test A, and uses its positive result to select Test B. The follow-up session re-reads A's saved decision before planning and executes B with six new neural runs. The B audit independently revalidates the preceding A trace, record, receipts, and raw hashes. Both candidate tests were designed before execution. Independent preflight runs retain their separate provenance.

Local supporting artifacts: `data/discovery/native-trace.json`, `data/discovery/native-trace-b.json`, A analyst record `data/discovery/discovery_b166bf63865447098bd121ee6cbea21c.json`, and B analyst record `data/discovery/discovery_0c3c59b3fbb044c78c9c7c7189676c68.json`.

## Results and limitations — English

The fresh native Omnigent Test A reproduced DNg02 readout rates of 17.2, 18.8, and 18.4 Hz across three fixed seeds, averaging 18.13 ± 0.83 Hz over all twenty-five cells, including silent cells, and the full 200-ms horizon. Thirteen or fourteen readout cells were active per driven seed; the mean does not imply all twenty-five fired. Sham yielded zero. Numerical execution took approximately 20.91 seconds. The new native comparison is `data/experiments/comparison-dng02-20261004T005438Z-0aa143.json`.

The fresh native follow-up Test B disconnected 2,202 outgoing rows while preserving direct input activation. It removed the DNg02 population response in all three seeds: 18.13 ± 0.83 Hz in the unchanged graph versus 0 Hz with disconnection, a 100% reduction per seed. Its numerical execution took approximately 19.88 seconds. The new comparison is `data/experiments/comparison-dng02-20261004T011205Z-88d84a.json`; its native receipt is `data/discovery/tool-receipts/tool_dec9321a154f4053b3d99f56f0b1376b.json`. This supports outgoing-connection dependency in the frozen model. These are descriptive model results, not biological replicates or a statistical population claim.

In the v2 body experiment, complete fresh native A spike events drive a frozen adapter into the authors’ published pretrained RL flight policy. All six paired body runs reach the full 200-ms horizon with 1,001 measured states each, no early termination, and no disabled failure checks. The minimum thorax height is approximately 1.012 cm. Across three seeds, driven/sham differences are 0.02875–0.03102 rad in wing-angle RMS and 0.001641–0.002797 cm in root position at the shared endpoint. This is a technical neural-to-controller-to-physics effect under fixed motor assumptions. Stabilization is supplied by the pre-existing trained policy, not discovered by the connectome. The body policy reads physical feedback; the brain remains open-loop. Body replay was executed separately downstream of native A. Biological motor calibration, a complete flight VNC, and longer-horizon stability remain open. Supporting artifact: `data/coupling/native_policy_comparison.json`.

The earlier v1 test-pattern run is retained as a failed controller route: its default stop at 38.8 ms is reference end, not instability. Extending the reference shows a fall below the height threshold at 53.6 ms. Bypassing termination produces finite states below the floor and is explicitly invalid flight; those diagnostic states are not substituted for the successful v2 runs.

## Measured improvement — English

We timed one repeated local evidence task: reparsing the original annotation/completeness files versus reading the previously verified identity claim from the local knowledgebase. Five alternating repetitions on the same process with a warm filesystem cache returned exactly the same twenty-five IDs. Medians were 427.73 ms and 0.282 ms, saving about 0.427 seconds per repeated lookup. The one-time evidence collection and review occurred beforehand in both paths. This measures reuse of a checked extraction, not end-to-end discovery speed, scientific accuracy, or simulation acceleration.

## AI contribution and responsibility — English

Omnigent manages research decisions and tool use; numerical solvers compute neural and body dynamics. Sources, extracted claims, model hypotheses, and adapter assumptions are explicitly distinguished. IDs and data releases are pinned. Credentials remain outside public code and browser bundles. BrightData tools are implemented, but the currently used primary evidence was retrieved directly rather than through a verified BrightData live call. The public viewer clearly labels recorded simulations. A native trace is required before claiming an executed agent workflow.

## Next experiment — English

After native B confirmed outgoing-connection dependency, compare matched non-target inputs to assess specificity and characterize the selected inputs biologically. Extend the independently supplied flight policy’s stability assessment beyond the 200-ms pilot; preserve the fixed coupling, and pursue independent muscle/VNC calibration and sensory feedback. Retain the unsuccessful v1 test-pattern route rather than presenting its below-floor diagnostic continuation as flight.

## Primary evidence links

- [DNg02 study, Namiki et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9206711/) — flight-related population readout in tethered already-flying flies.
- [Whole-brain model, Shiu et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/) — published simplified neural model and its validation scope.
- [Pinned FlyWire annotations v2.1.0](https://github.com/flyconnectome/flywire_annotations/tree/v2.1.0) — v783 identity mapping.
- [Flybody author code](https://github.com/TuragaLab/flybody) — body model and existing controller interfaces.

## Nach dem Absenden

Beide Bestätigungen speichern, beispielsweise `exports/hackos_confirmation.png` und `exports/google_form_confirmation.png`, mit Uhrzeit und tatsächlichem Projektlink in einer lokalen Notiz. Erst danach Issue #10 als abgeschlossen behandeln. Ein ausgefüllter Entwurf, lokale MP4-Dateien oder ein Repo-Link allein sind keine Einreichung.

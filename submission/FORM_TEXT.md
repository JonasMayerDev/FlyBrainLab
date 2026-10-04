# Texte für HackOS und das separate Google Form

**Vor Versand:** finale öffentliche URL prüfen, Namen/Rollen ergänzen und den nativen Omnigent-Status in `README.md`/Trace abgleichen. Die Texte beschreiben tatsächliche numerische Ergebnisse; sie behaupten keinen stabilen Flug. Die zusätzliche C3-Demo braucht ihren eigenen akzeptierten Einreichungsweg.

## Pflichtfelder

| Feld | Eintrag / Status |
|---|---|
| Project name | **FlyBrainLab** — Arbeitsname aus dem Repository; im Team bestätigen |
| Challenge | **Challenge 03 — Databricks: Agentic Scientific Discovery**; offizielle passende Auswahl wählen |
| GitHub repository | `https://github.com/JonasMayerDev/FlyBrainLab` |
| Live project URL | `https://valleebo.github.io/FlyBrainLab/` — öffentlicher Pages-Mirror, anonym im echten Browser geprüft; kanonischer Code bleibt im oben genannten Repository |
| Team | Vier tatsächliche Namen und Beiträge; außer Valentin noch nicht bestätigt |
| Team photo | Echtes Teamfoto, JPG/PNG/WebP, ≤10 MB |
| Team introduction | `team_intro.mp4`/`.mov`, ≤60 s/1 GB; echte Menschen/Rollen |
| Product demo | `product_demo.mp4`/`.mov`, ≤60 s/1 GB |
| Technical walkthrough | `technical_walkthrough.mp4`/`.mov`, ≤60 s/1 GB |
| Additional two-minute C3 demo | `c3_demo.mp4`; Upload-/Linkfeld im Google Form bzw. akzeptierten Weg klären |

## Kurzbeschreibung — Deutsch

FlyBrainLab verbindet nachvollziehbare wissenschaftliche Evidenz mit kontrollierten Fliegengehirn-Simulationen und einem öffentlichen Replay-Viewer. Acht vorab graphgewählte Inputs aktivieren flugbezogene DNg02-Neuronen im vollständigen installierten FlyWire-v783-LIF-Modell. Sham und getrennte Ausgangsgewichte kontrollieren diesen Befund. Ein eingefrorener Adapter übergibt gespeicherte Spikes an Flybody/MuJoCo; echte Körperzustände sind sichtbar, stabiler oder biologisch validierter Flug ist noch nicht erreicht. Quellen, Parameter, Kontrollen, Run Records und die nächste Forschungsentscheidung bleiben überprüfbar.

## Short description — English

FlyBrainLab connects traceable scientific evidence with controlled fly-brain simulations and a public replay viewer. Eight inputs selected from the graph before execution activate flight-related DNg02 neurons in the complete installed FlyWire v783 LIF model. Sham stimulation and disconnected outgoing weights control the result. A frozen adapter passes saved spikes to Flybody/MuJoCo. The viewer displays actual body states; stable or biologically validated flight has not been achieved. Sources, parameters, controls, run records, and the next research decision remain inspectable.

## Problem and scientific question — English

Connectomes describe connections but do not automatically explain behavior. FlyBrainLab makes one constrained hypothesis test reproducible: can eight connectivity-selected upstream inputs evoke activity in twenty-five flight-related DNg02 neurons, and does that response depend on the inputs’ outgoing connections? The question concerns a frozen numerical model. It does not assign an established biological function to unnamed input neurons or claim autonomous fly-brain emulation.

## What we built — English

The project uses pinned FlyWire v783 data, a published whole-network LIF model in Brian2, a provenance-aware local knowledgebase, frozen controlled experiment designs, and a Flybody/MuJoCo motor adapter. A static Vite/TypeScript/Three.js viewer replays actual exported runs with units, parameters, sources, and limitations. Omnigent is configured with specialist research, evidence-review, hypothesis-planning, experiment, and analysis roles. Include the following verified-workflow paragraph only after checking the native trace and linked numerical receipts.

**Verified-workflow paragraph — include only if native trace has passed:**

Omnigent orchestrated the actual recorded discovery loop. Its persisted native trace shows specialist roles, structured handoffs, and experiment-tool receipts linked to new numerical runs. The workflow moves from question and evidence to the frozen hypothesis, executes the selected test, uses the result to trigger the second test, and records an updated next decision. Independent preflight runs retain their separate provenance.

**Fallback paragraph if that verification is still missing:**

Omnigent specialist roles and experiment tools are implemented, but the full native discovery loop is not yet evidenced. The available numerical preflight runs were executed independently. This is an outstanding Challenge 03 requirement rather than a completed orchestration claim.

## Results and limitations — English

In the initial independently executed controlled runs, DNg02 readout rates were 17.2, 18.8, and 18.4 Hz across three fixed seeds, averaging 18.13 ± 0.83 Hz over all twenty-five cells and the full 200-ms horizon. Sham and disconnected-output conditions yielded zero. Disconnecting 2,202 outgoing rows preserved direct input activation while removing the DNg02 response. These are descriptive model results, not biological replicates or a statistical population claim. Native Omnigent results must be reported from their own linked run records.

The fixed motor adapter changes a pre-existing wingbeat test pattern and leads to small measured differences in MuJoCo wing angles and body positions. All initial body runs terminate at the reference-trajectory end at 38.8 ms; that default stop is not an instability finding. In a separately documented diagnostic with extended reference, the same controller falls below the 0.2-cm thorax-height threshold at 53.6 ms. Bypassing termination reaches 200 ms with finite states below the floor, which is explicitly invalid flight. Coupling is open-loop, with chosen normalization and gain; the model lacks a complete flight-controlling ventral nerve cord. No stable flight or biological motor calibration is demonstrated.

## Measured improvement — English

We timed one repeated local evidence task: reparsing the original annotation/completeness files versus reading the previously verified identity claim from the local knowledgebase. Five alternating repetitions on the same process with a warm filesystem cache returned exactly the same twenty-five IDs. Medians were 427.73 ms and 0.282 ms, saving about 0.427 seconds per repeated lookup. The one-time evidence collection and review occurred beforehand in both paths. This measures reuse of a checked extraction, not end-to-end discovery speed, scientific accuracy, or simulation acceleration.

## AI contribution and responsibility — English

Omnigent manages research decisions and tool use; numerical solvers compute neural and body dynamics. Sources, extracted claims, model hypotheses, and adapter assumptions are explicitly distinguished. IDs and data releases are pinned. Credentials remain outside public code and browser bundles. BrightData tools are implemented, but the currently used primary evidence was retrieved directly rather than through a verified BrightData live call. The public viewer clearly labels recorded simulations. A native trace is required before claiming an executed agent workflow.

## Next experiment — English

Compare a matched set of non-target inputs to assess specificity, characterize the selected inputs biologically, and independently stabilize a compatible existing flight controller. Then repeat the frozen neural-to-body coupling and pursue independent muscle/VNC calibration and sensory feedback. Longer neural runs alone will not resolve the observed descent under the test wingbeat pattern.

## Primary evidence links

- [DNg02 study, Namiki et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9206711/) — flight-related population readout in tethered already-flying flies.
- [Whole-brain model, Shiu et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/) — published simplified neural model and its validation scope.
- [Pinned FlyWire annotations v2.1.0](https://github.com/flyconnectome/flywire_annotations/tree/v2.1.0) — v783 identity mapping.
- [Flybody author code](https://github.com/TuragaLab/flybody) — body model and existing controller interfaces.

## Nach dem Absenden

Beide Bestätigungen speichern, beispielsweise `exports/hackos_confirmation.png` und `exports/google_form_confirmation.png`, mit Uhrzeit und tatsächlichem Projektlink in einer lokalen Notiz. Erst danach Issue #10 als abgeschlossen behandeln. Ein ausgefüllter Entwurf, lokale MP4-Dateien oder ein Repo-Link allein sind keine Einreichung.

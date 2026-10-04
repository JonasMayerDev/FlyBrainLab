# Flybody/MuJoCo und neuronaler Motoradapter

Stand: 4. Oktober 2026, echte lokale Läufe. Die Körperintegration ist umgesetzt: vollständige gespeicherte DNg02-Spikes treiben über einen eingefrorenen Adapter einen vorhandenen Wingbeat-Controller, dessen Kräfte in MuJoCo die Körperzustände verändern. Eine **vorhandene trainierte Autorenpolicy hält den Körper in einem getrennten 200-ms-Lauf in der Luft**. Die Stabilisierung stammt von dieser RL-Policy; biologische Flugsteuerung durch das Connectome ist nicht validiert. Die erste einfache Wingbeat-Baseline endet nach 38,8 ms an ihrer kurzen synthetischen Referenz. Bei verlängerter Referenz zeigt sie einen Höhenabbruch bei 53,6 ms.

## Tatsächliche Laufumgebung

| Komponente | Geprüfter Stand |
|---|---|
| Körper | Flybody 0.1.0, Drosophila melanogaster |
| Autorencode | `d015e9bfe441bd90ae431bac24c55cb74bdbce26` |
| Numerische Physik | MuJoCo 3.14.0 |
| Umgebung | dm_control 1.0.47 |
| Python / NumPy | 3.12.14 / 1.26.4 |
| Physik / Controller | 0,05 ms / 0,2 ms |
| Installation | isoliert in `.runtime/body-venv/`; gepinnt in `requirements.body.lock` |

Der Core-Body-Runtime verändert die neuronale `.venv` nicht. Flybody-Autorencode und Modellassets werden durch die gepinnte Installation geladen; SHA-256 jedes installierten Python-, XML- und OBJ-Files steht in `data/body/runtime_manifest.json`. Apache-2.0-Lizenz: `data/body/LICENSE.flybody`. Die erste einfache Baseline verwendet keine TensorFlow-/Acme-/Ray-Extensions. Für die getrennte Autorenpolicy-Inferenz besteht eine eigene Umgebung; neues RL-Training wird in keiner Variante eingesetzt.

Neu aufsetzen und baseline ausführen:

```sh
.venv/bin/python -m venv .runtime/body-venv
.runtime/body-venv/bin/python -m pip install -r requirements.body.lock
.runtime/body-venv/bin/python -m simulation.body --duration-ms 200 --seed 42
```

Der Runner setzt Grafik auf `MUJOCO_GL=disable` und speichert lokale Font-/Matplotlib-Caches unter `.runtime/`. Ein Fenster/GPU-Rendering ist für numerische Zustände nicht erforderlich.

## Körper und Controller

`simulation.body` startet die originale `flight_imitation()`-Umgebung im Inference-Modus. Der Autorencontroller `WingBeatPatternGenerator` erzeugt bei 218 Hz ein **approximiertes Testmuster**. Die Umgebung übersetzt Soll-Flügelwinkel proportional in Kräfte; sie enthält hier keine gelernte Flugpolicy. Das ist eine konkrete vorhandene Controllerannahme, keine durch das Connectome entdeckte Muskelsteuerung.

Die Autorenumgebung initialisiert die Fliege anhand ihrer Inference-Referenz etwa 1 cm über dem Boden mit 20 cm/s Vorwärtsgeschwindigkeit. Der Export enthält ausschließlich die gemessene `walker`-Physik, nie die Referenz-/Ghost-Trajektorie. Ausgangsgeschwindigkeit, Gravitation, Gelenkreihenfolge und Controllerparameter stehen im Run Record. Boden-Kollisionen sind in dieser Flugumgebung standardmäßig ausgeschaltet. Die Abbruchbedingungen werden respektiert; nach einem Abbruch werden keine Zustände fortgeschrieben.

## Eingefrorener Adapter

Spezifikation: `data/coupling/adapter_v1.json`, erstellt vor den gekoppelten Körpervergleichen. Hash: `76b7dcdc5f529f4b1ba9dfee6791eca8150f12cfb54fe4a99f57e89bc2ee162e`.

1. Alle 25 v783-DNg02-Einträge aus `research/evidence/dng02_targets.json` bilden den Readout. Links/rechts wird gemeinsam ausgewertet; eine seitenspezifische Muskelzuordnung ist nicht kalibriert.
2. Für jeden Controllerschritt wird die mittlere Spike-Rate aller 25 Zellen im **kausalen** Fenster `[t−10 ms, t)` berechnet. Zukünftige oder genau bei `t` auftretende Spikes gehen erst im nächsten Schritt ein.
3. `u = clip(rate / 100 Hz, 0, 1)`.
4. Beide Wing-Yaw-Sollwinkel erhalten um das unveränderte Zentrum 0,3 rad die Auslenkung `(1 + 0,1 × u)`. Der maximale Anstieg ist 10 %. Roll/Pitch und 218-Hz-Grundfrequenz bleiben im Autorenmuster.
5. Die originale Umgebung übersetzt das modifizierte Muster in Kräfte; MuJoCo berechnet die resultierende Bewegung.

Die publizierte DNg02-Amplitudenbeziehung motiviert die Richtung des Experiments. Das 10-ms-Fenster, 100-Hz-Normalisierung, positive 10-%-Verstärkung, Pooling und Yaw-Zuordnung sind **gewählte technische Modellannahmen**. Diese Zahlen sind nicht aus einer biologischen Muskelkalibrierung abgeleitet. Die Wiederverwendung gespeicherter Spikes ist Open-loop: kein sensorischer Rückkanal, kein VNC-Modell, keine gemeinsame neuronale/physikalische Integration in Echtzeit.

Der Runner verlangt vollständige `readout_spikes.json`-Events und passende IDs/Dauer. Gekappte Spike-Previews werden zurückgewiesen. Die neuronale Uhr wird weder gedehnt noch wiederholt. Ein Körperlauf kann wegen der physikalischen Abbruchbedingung kürzer als der 200-ms-neuronale Lauf sein.

```sh
# Die Spezifikation existiert bereits; freeze überschreibt sie nicht.
.venv/bin/python -m simulation.coupling freeze
.runtime/body-venv/bin/python -m simulation.coupling run data/runs/NEURAL_RUN_ID
.runtime/body-venv/bin/python -m simulation.coupling compare data/body/SHAM_RUN_ID data/body/DRIVE_RUN_ID
.venv/bin/python -m unittest discover -s tests -p 'test_body*.py' -v
```

## Echte Ergebnisse des ersten technischen Vergleichs

Baseline: `data/body/body-baseline-20261004T002023Z-1147b1/run.json`, 3,53 Sekunden Wall Time, 195 Zustände, 38,8 ms tatsächliche Physik. Die requested Dauer von 200 ms wird ausdrücklich als angeforderter Horizont gespeichert, nicht als erreichte Laufzeit ausgegeben.

Die erste Kopplung verwendet die drei echten A-Test-Paare aus `data/experiments/comparison-dng02-20261004T001804Z-8345bd.json`. Diese neuronalen Vorläufe wurden manuell ausgeführt; damit ist diese Körperkopplung allein noch keine Omnigent-Discovery-Schleife. `data/coupling/preflight_comparison.json` erhält diese ersten Run-IDs und den Hash des identischen Adapters. `data/coupling/comparison.json` ist die zuletzt ausgeführte Vergleichsauswertung.

| Seed | Max. Amplitudenfaktor Drive / Sham | RMS-Unterschied gemessener Flügelwinkel | Abstand der Körperpositionen bei 38,8 ms |
|---|---|---|---|
| 42 | 1,036 / 1,000 | 0,007015 rad | 0,004621 cm |
| 43 | 1,028 / 1,000 | 0,007456 rad | 0,005519 cm |
| 44 | 1,020 / 1,000 | 0,005322 rad | 0,002311 cm |

Alle Paare starten mit identischem physikalischem Zustand innerhalb desselben Seeds. Die Vergleiche verwenden ausschließlich den gemeinsamen tatsächlich gemessenen Horizont. Sham liegt mit Null-Readout beim unveränderten Controller; die Drive-Bedingung verändert reale Gelenkwinkel und Körperpositionen. Das ist ein **technischer Readout→Adapter→Physik-Nachweis unter gewählten Annahmen**. Ein geringer Positionsunterschied belegt keine korrekte biologische Vorhersage. Alle sechs Körperläufe enden bei 38,8 ms an der kurzen Referenztrajektorie. Dieser erste Abbruch allein belegt keine Controllerinstabilität; die folgende Diagnose untersucht sie separat.

### Korrektur der Abbruchursache und getrennte Diagnosen

`data/body/termination_diagnostics.json` enthält drei unabhängige echte Läufe mit Seed 42. Die vorherige Vermutung, der 38,8-ms-Abbruch sei ein Stabilitätsfehler, ist durch Prüfung der konkreten Abbruchbedingungen korrigiert. Die ursprünglichen Laufdateien bleiben erhalten.

| Variante | Tatsächliche Dauer | Beobachtung |
|---|---|---|
| Originalreferenz | 38,8 ms | Referenzende bei Schritt 194; Thorax 0,5975 cm, oberhalb 0,2-cm-Grenze; kein Beschleunigungsabbruch |
| Nur Referenz verlängert | 53,6 ms | Gleicher Anfangszustand/Controller; Thorax fällt auf 0,1934 cm, unter Höhenmarke |
| Referenz verlängert, Task-Abbruch explizit deaktiviert | 200 ms | 1.001 endliche Physikzustände; niedrigste Höhe −7,1447 cm; Fliege fällt durch die standardmäßig kontaktlose Bodenebene |

Die Referenzverlängerung setzt keine gemessene Körperposition nach dem Reset und liefert keine Kontrollaktion. Der dritte Lauf ist ausschließlich eine numerische Diagnose; die ausgeschaltete Abbruchprüfung steht in Run Record und Trajektorie. Er darf keine 200-ms-Flugvalidierung oder erfolgreich stabilisierten Flug suggerieren.

```sh
.runtime/body-venv/bin/python -m simulation.body --extend-reference
.runtime/body-venv/bin/python -m simulation.body --extend-reference --disable-task-termination
```

### Vorhandene trainierte Flugpolicy: gemessener 200-ms-Controllerlauf

Die offiziellen Ergänzungsdaten enthalten eine kleine bestehende Flight-SavedModel-Policy (Policyarchiv 6,5 MB) und ein veröffentlichtes `wing_pattern_fmech.npy` (Flugdatensatzarchiv 12,9 MB). Quellen, Artikelversion 4, Dateinummern, Anbieter-MD5 und extrahierte SHA-256 stehen in `data/body/published_assets_manifest.json`. Die Datenlizenz ist GPL-3.0+; Originalarchive und Modellgewichte bleiben unter der ausgeschlossenen `.runtime/body-published-data/`. Es werden ausschließlich eigene Run Records und numerische Zustände veröffentlicht.

Das veröffentlichte Flügelmuster allein erreicht mit eingeschalteten Abbruchprüfungen 60,6 ms; dann unterschreitet der Thorax 0,2 cm (`data/body/body-diagnostic-20261004T004906Z-66edbb/`). Mit der **vorhandenen trainierten Flight-Policy** erreicht der Körper dagegen volle 200 ms, 1.001 Zustände, minimale Thoraxhöhe 1,01176 cm und 3,98632 cm Verschiebung (`data/body/body-diagnostic-20261004T005630Z-eaf2a2/`). Die Task-Abbruchprüfungen bleiben eingeschaltet. Das ist ein kurzer nachgewiesener Controllerflug unter Modellannahmen, kein Nachweis allgemeinen oder biologisch korrekten Flugverhaltens.

Die separate `.runtime/flight-policy-venv/` ist in `requirements.body.policy.lock` gepinnt: TensorFlow 2.18.0, TensorFlow Probability 0.25.0, tf-keras 2.18.0. Die Autorenpolicy stammt aus einer älteren TensorFlow-Umgebung. `simulation.body_policy` registriert deshalb genau einen alten Independent-TypeSpec-Namen als Alias des aktuellen identischen Distributionstyps. Diese Kompatibilitätsanpassung ist protokolliert. Gespeicherte Gewichte und Graphen bleiben unverändert. Beobachtungen werden wie im Autorenbeispiel in float32 mit Batchdimension umgewandelt; die deterministische Distributionserwartung wird mit der Autorenfunktion `canonical2real` auf physikalische Aktuatorgrenzen abgebildet.

```sh
.venv/bin/python -m simulation.body_download
.venv/bin/python -m venv .runtime/flight-policy-venv
.runtime/flight-policy-venv/bin/python -m pip install -r requirements.body.policy.lock
.runtime/flight-policy-venv/bin/python -m simulation.body --extend-reference --published-wing-pattern --published-flight-policy
```

Der Body-Controller nutzt tatsächliche Körperbeobachtungen und seine vorgegebene Referenz. Die neuronale Simulation erhält weiterhin keinen sensorischen Rückkanal. Diese beiden Rückkopplungen werden getrennt ausgewiesen.

### Zweite eingefrorene Kopplungsvariante

`data/coupling/adapter_v2_policy.json` ist am 4.10., 00:59:36 UTC, **vor** seinen gekoppelten 200-ms-Vergleichen eingefroren. Hash: `bde975de924f55e9793c395196674933fbc659093535cb6ed48e9d11e906bc03`. Er erhält unverändert die v1-Readout-IDs, das 10-ms-Fenster, die 100-Hz-Skala, das 0,3-rad-Zentrum und die maximale 10-%-Verstärkung. Neu sind ausschließlich der explizit dokumentierte vorhandene Policy-/Muster-Controller und die ausreichend lange Task-Referenz. v1-Spezifikation und alle bisherigen Ergebnisse bleiben erhalten.

```sh
.venv/bin/python -m simulation.coupling freeze-policy
.runtime/flight-policy-venv/bin/python -m simulation.coupling run data/runs/NEURAL_RUN_ID --published-policy
.runtime/flight-policy-venv/bin/python -m simulation.coupling compare data/body/SHAM_POLICY_RUN data/body/DRIVE_POLICY_RUN --published-policy
```

Der v2-Export enthält zusätzlich unmodifizierte/modifizierte Wingbeat-Sollwinkel, deren Differenz, Policyaktion vor dem Wingbeat-Anteil und tatsächlich angewendete Aktuatorkontrolle. Damit kann die Kette Spike→Rate→Sollwinkeldifferenz→Physik direkt überprüft werden. Die RL-Policy kompensiert Körperabweichungen selbstständig; kleine Positionsänderungen sind deshalb kein Maß für biologisch korrekte neuronale Flugsteuerung.

### Frische native Omnigent-Run-Provenienz

`data/coupling/native_comparison.json` verwendet die sechs frischen A-Neuronenläufe aus `data/experiments/comparison-dng02-20261004T005438Z-0aa143.json`. Der tatsächliche Omnigent-Tool-Receipt `tool_f45963ca9f204a4ca9b3f02fd266fcbf` und Datei-Hashes sind verlinkt. v1 liefert identische Messwerte zum ersten technischen Test. Die neuronalen Läufe sind unter Omnigent ausgeführt; der anschließende Körperlauf ist ausdrücklich eine manuell gestartete Wiederverwendung dieser echten neuronalen Ergebnisse.

`data/coupling/native_policy_comparison.json` enthält die getrennte v2-Auswertung derselben sechs echten Omnigent-A-Neuronenläufe. **Alle sechs Körperläufe erreichen volle 200 ms mit 1.001 tatsächlichen Zuständen und eingeschalteten Task-Abbruchprüfungen.** Die minimale Thoraxhöhe liegt bei 1,0118–1,0146 cm. Anfangszustand, Controller/Policy, Adapter und Seed sind pro Drive/Sham-Paar identisch; ausschließlich die tatsächlichen neuronalen Events unterscheiden sich.

| Seed | Max. Drive-Faktor / Sham | Max. neuronale Sollwinkeldifferenz | RMS-Unterschied gemessener Flügelwinkel | Positionsunterschied nach 200 ms |
|---|---|---|---|---|
| 42 | 1,052 / 1,000 | 0,05390 rad | 0,03102 rad | 0,001641 cm |
| 43 | 1,040 / 1,000 | 0,04435 rad | 0,02875 rad | 0,002797 cm |
| 44 | 1,040 / 1,000 | 0,04066 rad | 0,03102 rad | 0,001732 cm |

Sham hat null Readout-Spikes und keine relevante Adapter-Sollwinkeldifferenz (maximal 1,1×10⁻¹⁶ rad Rundung). Die Körperfeedback-Policyaktionen unterscheiden sich danach mit RMS 0,0111–0,0114. Damit sind sowohl der direkte Eingriff in den Wingbeat-Sollwinkel als auch die anschließende reale Physikantwort dokumentiert. Die Stabilisierung durch eine unabhängig trainierte Autorenpolicy bleibt eine Modellkomponente; der Vergleich validiert weder VNC-/Muskelzuordnung noch biologisches Flugverhalten.

Für die aktuelle öffentliche Demo hat **v2 Vorrang bei exakt gleicher ursprünglicher neuronaler Run-ID**; ältere v1-Ausgaben bleiben separat nachvollziehbar. Beispiel Seed 42: `data/body/body-coupled-policy-20261004T010033Z-7a8980/` (Sham), `data/body/body-coupled-policy-20261004T010044Z-de8a13/` (Drive).

## Export für den öffentlichen Replay-Viewer

Pro Lauf liegen `run.json`, `trajectory.json` und `model_manifest.json` vor. `trajectory.json` enthält alle Controllerschritte, keine erfundene Animation:

```json
{
  "units": {"position": "cm", "time": "ms", "angles": "rad"},
  "axis_convention": "right-handed MuJoCo world; z-up; quaternion xyzw",
  "states": [{
    "time_ms": 0.2,
    "position": [0.0, 0.0, 1.0],
    "quaternion": [0.0, 0.0, 0.0, 1.0],
    "wing_angles_rad": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  }]
}
```

Diese Zahlen sind ein **Schema-Beispiel**, kein zusätzlicher gemessener Zustand. Echte Dateien enthalten außerdem qpos/qvel, Geschwindigkeiten, Adapterrate und Amplitudenfaktor. MuJoCos Quaternion `wxyz` wird im Export ausdrücklich in Three.js-Format `xyzw` umgeordnet. Weltachse bleibt z-up; Viewer müssen diese Konvention beachten. Für die Wiedergabe kann das Tempo verlangsamt werden, die experimentelle Zeitachse bleibt in Millisekunden erhalten. Eine vereinfachte Viewer-Fliege ist eine Darstellung der Zustände, kein neues Körpermodell.

## Prüfungen, Grenzen und nächster Schritt

Fünf Vertragsprüfungen bestehen: kausale Fenstergrenzen, Nullsignal/Sättigung, Ablehnung gekappter oder fremder Events, Ablehnung von Zeiten außerhalb des neuronalen Horizonts und Ablehnung einer geänderten Evidenzdatei selbst bei unveränderten IDs. Beim Laden muss der aktuelle Evidenz-SHA-256 mit der eingefrorenen Adapterquelle übereinstimmen. Tatsächliche Baseline sowie drei gekoppelte Drive/Sham-Paare sind zusätzlich ausgeführt und auf endliche physikalische Zustände geprüft. Laufrecords erhalten Provenienz zu ursprünglicher neuronaler Bedingung, Seed und Eingabedatei-Hashes.

Nächstes Experiment: die vorhandene Flugpolicy über längere Horizonte separat prüfen und die Rate→Muskel-/Flügelzuordnung anhand unabhängiger biologischer Messdaten kalibrieren. Der Schritt „bestehende Policy einbinden, 200-ms-Baseline zeigen und eingefrorene neuronale Kopplung wiederholen“ ist mit v2 tatsächlich ausgeführt. Muskel-/VNC-Kalibrierung, allgemeiner Flugnachweis und sensorischer Rückkanal zum Connectome bleiben offen.

Primärquellen: [Flybody-Autorenrepository](https://github.com/TuragaLab/flybody), [gepinntes Fluginterface](https://github.com/TuragaLab/flybody/blob/d015e9bfe441bd90ae431bac24c55cb74bdbce26/flybody/fly_envs.py), [Wingbeat-Testmuster](https://github.com/TuragaLab/flybody/blob/d015e9bfe441bd90ae431bac24c55cb74bdbce26/flybody/tasks/pattern_generators.py), [Flybody-Publikation](https://doi.org/10.1038/s41586-025-09029-4), [DNg02-Amplitudenstudie](https://doi.org/10.1016/j.cub.2022.01.008).

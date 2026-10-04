# Tatsächliche neuronale Ergebnisse

**Eine kontrollierte Modellantwort liegt vor:** Acht vorab graphgewählte Inputs
aktivieren nicht direkt stimulierte, flugbezogene DNg02-Zellen im gesamten
installierten v783-LIF-Graph. Werden die Ausgangsgewichte dieser Inputs auf null
gesetzt, verschwindet die DNg02-Antwort in allen drei vorab fixierten Seeds.

Diese Aussage betrifft das eingefrorene numerische Modell. Eine biologische
Funktion der graphgewählten Inputs, Flugbeginn oder autonomer Flug des
gekoppelten Körpers ist damit nicht nachgewiesen.

## Unabhängige Machbarkeitsläufe vor Omnigent

Die folgenden Läufe wurden tatsächlich ausgeführt und tragen die Herkunft
`independent-feasibility-before-Omnigent`. Sie bestätigen den ausführbaren
Experimentcode. Der C3-Nachweis der Orchestrierung benötigt zusätzlich den
separaten echten Omnigent-Aufruf mit Rollen, Handoffs und ergebnisabhängiger
nächster Entscheidung. Ein Herkunftstext im Run Record allein beweist das nicht.

| Bedingung | Seed 42 | Seed 43 | Seed 44 | Mittel ± Stichproben-SD |
|---|---:|---:|---:|---:|
| 0-Hz-Sham | 0 Hz | 0 Hz | 0 Hz | 0 ± 0 Hz |
| 150-Hz-Input, unveränderter Graph | 17,2 Hz | 18,8 Hz | 18,4 Hz | 18,13 ± 0,83 Hz |
| 150-Hz-Input, Ausgangsgewichte getrennt | 0 Hz | 0 Hz | 0 Hz | 0 ± 0 Hz |

Die Rate mittelt über alle **25 DNg02-Zellen**, einschließlich stiller Zellen,
und über den vollständigen **200-ms-Zeitraum**. Pro Seed gibt es einen numerischen
Lauf je Bedingung, keine biologischen Replikate und keinen p-Wert.

Test A ergibt positive gepaarte Ratendifferenzen in jedem Seed. Die versiegelte
Entscheidungsregel führt deshalb zu Test B. Test B erreicht **100 % Rückgang**
je Seed und überschreitet die vorab verlangte 80-%-Schwelle.
Es wurden **2.202 ausgehende Verbindungszeilen** der acht Inputs auf null gesetzt.
Die unveränderte Inputstimulation erzeugt weiterhin Aktivität in den acht
Inputzellen; die DNg02-Antwort wird also nicht durch Abschalten der externen
Stimulation entfernt.

Die unveränderten Inputläufe sind in A und B bei identischen Seeds
Spike-für-Spike gleich: 1.129 / 994 / 1.090 Spikeevents, verteilt auf
243 / 201 / 236 aktive Zellen. Die getrennten Bedingungen enthalten
222 / 223 / 222 Inputspikes und jeweils genau acht aktive Zellen.
Die Dateien enthalten den vollständigen Spikeausgang, nicht nur eine Animation.

## Rechenaufwand und Reproduzierbarkeit

- Test A: **19,607 s** Gesamtzeit für sechs Läufe.
- Test B: **18,465 s** Gesamtzeit für sechs Läufe.
- Neuronale Integration: vollständiger Graph mit **138.639 Neuronen** und
  **15.091.983 autorenseitig verarbeiteten Verbindungszeilen**; keine Teilnetz-
  Abkürzung. Ein Prozess, Brian2-NumPy-Runtime.
- Beobachteter maximaler Prozessspeicher: etwa **1,24 GiB** für A und
  **1,60 GiB** für B. Das sind Prozess-Peaks der jeweiligen seriellen Läufe.

Vergleichsartefakte:

- [Test A](../../data/experiments/comparison-dng02-20261004T001804Z-8345bd.json)
- [Test B](../../data/experiments/comparison-dng02-20261004T001927Z-32a28b.json)
- [Versiegeltes Design](../designs/dng02-input-v1.json)
- [Neuronenidentitäten und Auswahlregel](dng02_targets.json)

Jeder Vergleich listet die vollständigen Run-Pfade. In jedem Lauf liegen
`run.json`, `spikes.parquet`, `readout.json`, vollständige `readout_spikes.json`
und eine ausdrücklich begrenzte allgemeine Spike-Vorschau.

## Gemessener Engpass der Evidenzsuche

Bei derselben wiederholten Identitätsfrage wurden zwei tatsächliche lokale
Wege verglichen: die vollständige 31-MB-Annotation und 3,3-MB-Completeness-Datei
erneut parsen, oder den zuvor geprüften ID-Claim aus der Knowledgebase lesen.
Fünf Wiederholungen pro Weg, wechselnde Reihenfolge, warmer Dateisystemcache,
derselbe Pythonprozess. Alle Messungen lieferten exakt dieselben 25 IDs.

Der Median betrug **427,73 ms** für erneutes Parsen und **0,282 ms** für den
geprüften KB-Claim. Das spart in diesem kleinen wiederholten Schritt etwa
**0,427 s pro Abfrage**. Ein direkter bereits gespeicherter JSON-Ausschnitt
kann ähnlich schnell sein; der Nutzen liegt im Wiederverwenden einer geprüften
Extraktion. Die einmalige Recherche und Prüfung wurde in beiden Wegen
vorher erledigt und ist ausdrücklich nicht Teil dieses Benchmarks.

[Rohmessungen und Grenzen](../../data/experiments/evidence_lookup_benchmark.json)
und [ausführbarer Benchmark](../benchmark_evidence_lookup.py) erhalten den
Versuchsaufbau. Diese Zeiten belegen **keine gesamte Discovery-Beschleunigung,
keinen Genauigkeitsgewinn und keine Beschleunigung der Gehirnsimulation**.

## Nächste wissenschaftliche Entscheidung

Die nächste Prüfung soll die Identitäten der vorgeschalteten Inputs biologisch
einordnen und einen gleich großen, hinsichtlich Transmitter und ausgehender
Konnektivität passenden Nichtziel-Input vergleichen. Erst danach sind
natürliche sensorische Eingänge und unabhängige Körper-/Biologiekalibrierung
sinnvoll. Ein positiver Brain-to-Body-Vergleich mit festem Motoradapter bleibt
bis dahin eine technische Modellkopplung mit expliziten Annahmen.

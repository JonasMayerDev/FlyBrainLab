# FlyBrainLab – Messwerte und wissenschaftliche Grenzen

Stand: 4. Oktober 2026. Öffentliches Replay: [valleebo.github.io/FlyBrainLab](https://valleebo.github.io/FlyBrainLab/). [Team-Repository](https://github.com/JonasMayerDev/FlyBrainLab).

## Wissenschaftliche Frage

Erhöht die Stimulation von acht anhand ihrer positiven Konnektivität gewählten Eingangsneuronen die Aktivität in 25 annotierten DNg02-Neuronen im eingefrorenen vollständigen v783-LIF-Modell? Benötigt diese Reaktion die ausgehenden Verbindungen der stimulierten Eingänge?

[Namiki et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9206711/) verbinden DNg02-Populationsaktivität mit Flügelamplitude während bereits etablierter, angebundener Flugbedingungen. Die Studie belegt hier keine autonome Fluginitiierung. Die offizielle, gepinnte FlyWire-Annotation ordnet 25 konkrete DNg02-IDs zu; alle sind im installierten v783-Graph vorhanden. Die Auswahl der acht vorgeschalteten Eingänge ist eine graphgestützte Modellhypothese. Eine visuelle oder sensorische Eingangsfunktion wird ihnen nicht zugeschrieben.

Quellen, genaue Bedingungen, Snapshot-Hashes und Claims: [DNG02_EVIDENCE.md](../research/evidence/DNG02_EVIDENCE.md). Vorab versiegeltes Design und Auswahl zwischen zwei Tests: [EXPERIMENT_DESIGN.md](../research/designs/EXPERIMENT_DESIGN.md).

## Vergleich im neuronalen Modell

Der vollständige installierte Graph umfasst 138.639 Neuronen und 15.091.983 autorenseitig verarbeitete Verbindungszeilen. Diese sind keine einzelnen rohen Synapsenpunkte. Je Bedingung wurden 200 ms mit 0,1-ms-Schritt, 150-Hz-Stimulation und den vorab gewählten Seeds 42/43/44 gerechnet. Kein DNg02-Readout gehört zu den stimulierten Eingängen. Die Raten berücksichtigen alle 25 Ausleseneuronen einschließlich stummer Zellen.

| Bedingung | Seed 42 | Seed 43 | Seed 44 |
|---|---:|---:|---:|
| Sham | 0 Hz | 0 Hz | 0 Hz |
| Eingangsneuronen stimuliert | 17,2 Hz | 18,8 Hz | 18,4 Hz |
| Gleicher Reiz, ausgehende Verbindungen der Eingänge getrennt | 0 Hz | 0 Hz | 0 Hz |

Gepoolte Aktivierungsrate: **18,13 ± 0,83 Hz**, Mittelwert ± Stichprobenstandardabweichung über drei Simulations-Seeds. Bei der zweiten Kontrolle wurden ausschließlich die 2.202 ausgehenden Verbindungszeilen der acht stimulierten Eingänge auf Gewicht null gesetzt. Der externe Reiz bleibt identisch. Das liefert einen kausalen Kontrollbefund innerhalb dieses Modells. Es ist keine neue unabhängige biologische Validierung.

Die zunächst separat ausgeführten Machbarkeitsläufe und ihre vollständigen Rohdaten sind in [NEURAL_RESULTS.md](../research/evidence/NEURAL_RESULTS.md) dokumentiert. Sie liefen außerhalb Omnigent. Ein tatsächlicher Omnigent-Nachweis erfordert zusätzlich den nativen Session-Trace und neue numerische Tool-Receipts; ein frei gesetztes `execution_context` allein genügt nicht.

Die vorab gespeicherte Entscheidungsregel wählt nach einer positiven Antwort in allen drei Seeds den Test mit getrennten Ausgangsverbindungen. Bei Nullantwort wäre die getrennt registrierte direkte DNg02-Kalibrierung der nächste Test; Targets oder Gewinne werden nicht nachträglich passend eingestellt.

## Körperkopplung

Gepinntes Flybody/MuJoCo berechnet tatsächliche physikalische Zustände. Ein vor den Vergleichen eingefrorener Adapter nutzt das vergangene 10-ms-Fenster des DNg02-Readouts für ein begrenztes Flügelamplitudenkommando. Der vorhandene Autorencontroller ist ein approximierter WingBeatPatternGenerator, kein vom Team trainierter oder biologisch kalibrierter Connectome-Controller. Die Kopplung ist **Open-loop**.

Die gekoppelten Drive-/Sham-Vergleiche zeigen unterschiedliche Flügelwinkel und Körperpositionen. Die ursprünglichen Körperläufe terminieren nach **38,8 ms**, weil die Standardreferenz endet. Ein separater Diagnoselauf mit längerer Referenz fällt bei53,6ms unter die Thorax-Höhengrenze. Ein ausdrücklich deaktivierter Terminierungscheck erzeugt200ms Zustände, aber der Körper fällt unter die kontaktlose Bodenebene; das ist kein gültiger Flugnachweis. [Diagnosebeleg](../data/body/termination_diagnostics.json). Keine Zustände nach dem tatsächlichen Ende werden extrapoliert. Anfangsimpuls, Controller und Adapter sind Modellannahmen. Die beobachtete Bewegung ist **kein stabiler autonomer Flug**. Nächster Embodiment-Schritt ist eine unabhängige Stabilisierung/Kalibrierung der Körperbaseline, bevor weitere Brain-to-Motor-Hypothesen getestet werden.

Versionen, tatsächliche Zustände, Vergleichswerte und Reproduktion: [BODY_INTEGRATION.md](BODY_INTEGRATION.md).

## Gemessener Engpass

Eine wiederholte DNg02-Identitätssuche wurde über fünf alternierende lokale Wiederholungen gemessen. Beide Wege liefern exakt dieselben 25 IDs:

| Weg | Median |
|---|---:|
| Offizielle Annotation erneut parsen und v783-Mitgliedschaft prüfen | 427,73 ms |
| Bereits geprüften, quellengestützten Claim aus lokaler KB lesen | 0,282 ms |

Die Einsparung beträgt rund **0,427 Sekunden pro wiederholtem Identitätsabruf** auf diesem Rechner. Das ist ein enger Nachweis für Wiederverwendung geprüfter Evidenz. Die Messung verwendet warme lokale Dateien; initiale Recherche, Quellenprüfung, Netzabruf und Modellrechnung sind nicht eingeschlossen. Sie belegt weder eine Gesamtbeschleunigung der Forschung noch höhere biologische Genauigkeit. Rohzeiten und Gleichheitsprüfung: [evidence_lookup_benchmark.json](../data/experiments/evidence_lookup_benchmark.json).

## Darstellung und Verantwortlichkeit

Der Browser spielt aufgezeichnete numerische Ergebnisse ab. Die Neuronenansicht ist ein abstrahiertes Layout, keine rekonstruierten anatomischen Koordinaten. Browser-Rendering berechnet keine Gehirn- oder Körperdynamik. IDs sind Strings. Eine neuronale Vollgraphrechnung und die Auswahl sichtbarer aktiver Neuronen sind unterschiedliche Nachweise.

Anthropic-/BrightData-Credentials und Salden bleiben unbestätigt. Der vorhandene Codex-CLI-Zugang kann unter Omnigent eingesetzt werden; unabhängig heruntergeladene echte Primärquellen sind ausdrücklich von BrightData-Abrufen getrennt. API-Schlüssel und veränderlicher Dienst-/KB-Zustand bleiben lokal außerhalb des iCloud-Projekts.

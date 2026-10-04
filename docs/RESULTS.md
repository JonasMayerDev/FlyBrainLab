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

Die gekoppelten Drive-/Sham-Vergleiche zeigen unterschiedliche Flügelwinkel und Körperpositionen. Die ursprünglichen Körperläufe terminieren nach **38,8 ms**, weil die Standardreferenz endet. Ein separater Diagnoselauf mit längerer Referenz fällt bei 53,6 ms unter die Thorax-Höhengrenze. Ein ausdrücklich deaktivierter Terminierungscheck erzeugt 200 ms Zustände, aber der Körper fällt unter die kontaktlose Bodenebene; das ist kein gültiger Flugnachweis. [Diagnosebeleg](../data/body/termination_diagnostics.json). Keine Zustände nach dem tatsächlichen Ende werden extrapoliert. Anfangsimpuls, Controller und Adapter sind Modellannahmen. Diese frühen v1-Daten sind **kein stabiler autonomer Flug**. Die separat unten berichtete v2 verbessert das technische Zeitfenster mit einer vorhandenen Autorenpolicy; biologische Kalibrierung bleibt erforderlich.

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

## Verifizierte native Tests A und B

Der tatsächliche Omnigent-Baum `2e99e639e48743ee874f0ecfefc8a08d` enthält fünf abgeschlossene Spezialisten-Handoffs, sechs neue numerische A-Bedingungen, Kontrollanalyse und gespeicherte Folgeentscheidung. Die strenge [Traceprüfung A](../data/discovery/native-trace.json) bindet native Toolausgaben an Designseal, Rohspikes, Vergleich und Analyst-Record. Die numerische Toolausführung benötigte 20,9062 s und wählte aufgrund der positiven Antwort Test B.

Der erste optionale B-Start und seine Wiederaufnahme im A-Baum scheiterten an der dort gespeicherten Startup-Verbrauchsgrenze. Die Fehler bleiben sichtbar. Anschließend wurde B in einer **neuen nativen Session** `944082e71d344da6a3b44e5b7abdd723` mit korrigierten Grenzen ausgeführt. Sie enthält erneut fünf abgeschlossene Spezialisten-Handoffs, sechs neue numerische B-Bedingungen und einen neuen Analyst-Record. Die numerische Toolausführung benötigte 19,8832 s. Nach Trennung der Ausgangsverbindungen beträgt die DNg02-Rate in allen drei Seeds 0 Hz, während die Eingangsreize identisch bleiben.

Die [Traceprüfung B](../data/discovery/native-trace-b.json) validiert die A-Artefakte unabhängig erneut und belegt, dass die neue Session den tatsächlichen A-Entscheidungsrecord **vor** Planung und Experimentausführung gelesen hat. Es handelt sich um zwei verbundene Sessions, nicht um einen einzelnen durchgehenden Baum. Der B-Analyst wählt als nächsten Schritt eine Prüfung mit passenden Kontrollinputs und biologisch belegten sensorischen Eingängen (`matched_input_and_sensory_validation`); dieser weitere Test ist geplant, noch nicht ausgeführt.

Die native Orchestrierung spart hier keine numerische Rechenzeit: die manuellen Machbarkeitsläufe benötigten 19,607 s für A bzw. 18,465 s für B. Ihr belegter Beitrag ist die strukturierte, überprüfbare Weitergabe von Evidenz, Experiment und Entscheidung. Eine gemessene gesamte Forschungsbeschleunigung wird daraus nicht abgeleitet.

## Verbesserte Körperkopplung mit Autoren-Policy

Die anschließend vor Körpervergleich eingefrorene v2 koppelt dieselben neuen nativen A-Spikes an die unveränderte, bereits trainierte Flybody-Autoren-Policy. Alle sechs Drive-/Sham-Körperruns rechnen 200 ms mit 1.001 gemessenen Zuständen, ohne deaktivierten Terminierungscheck oder vorzeitiges Ende. Die minimale Thoraxhöhe bleibt bei ungefähr 1,012–1,015 cm. Stabilisierende Rückkopplung stammt aus der vorhandenen RL-Körperpolicy; das Gehirn erhält weiterhin keinen sensorischen Rückkanal.

Die neuronale Aktivität moduliert einen festen Motoradapter. Gemessene Drive-/Sham-Unterschiede: Flügelwinkel-RMS 0,02875–0,03102 rad und Körperposition am gemeinsamen Ende 0,001641–0,002797 cm. Diese kleinen Effekte belegen eine technische physikalische Kopplung; sie kalibrieren keine biologische Muskelsteuerung. [Vergleich und Provenienz](../data/coupling/native_policy_comparison.json), [v2-Adapter](../data/coupling/adapter_v2_policy.json). Kein neues RL-Training und keine aus dem Connectome entdeckte Stabilisierung behaupten. Längere Horizonte, biologisch belegte Eingänge und unabhängige Kalibrierung bleiben nächste Schritte.

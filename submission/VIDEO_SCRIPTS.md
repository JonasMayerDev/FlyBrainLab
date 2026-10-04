# Vier Videos: Sprechertexte und echte Bildquellen

Stand: 4. Oktober 2026. Ziel für die drei HackOS-Felder: **50–55 Sekunden**, harte Grenze je 60 Sekunden/1 GB. Zusätzliche C3-Demo: **115–120 Sekunden** über den noch zu klärenden eigenen Einreichungsweg.

Die Texte sind Aufnahmeskripte. **Ein Skript ist noch kein fertiges Video.** Mit einer Stoppuhr laut lesen; bei Bedarf Pausen oder optional markierte Sätze kürzen. Text und Messwerte müssen zum tatsächlich gezeigten Run passen. Vorab unabhängige Läufe dürfen nicht als nachträglich von Omnigent ausgeführt beschrieben werden. Die Projektbezeichnung „FlyBrainLab“ stammt vom Repository und bleibt bis zur Bestätigung der Arbeitsname.

Bildquellen: echte Viewer-Aufnahmen; eingefrorenes Design `research/designs/dng02-input-v1.json`; `research/evidence/DNG02_EVIDENCE.md`; tatsächliche Run-/Vergleichsdateien unter `data/experiments/` und `data/coupling/`; der von Omnigent selbst gespeicherte und geprüfte native Trace. Ein Diagramm erklärt die Architektur, beweist aber keine ausgeführte Orchestrierung. Keine Schlüssel, private Anbieterprofile oder Fremdtexte im Vollbild aufnehmen.

## 1. Team introduction — Ziel 50 Sekunden

**Menschliche Aufnahme erforderlich.** Vier echte Personen im Bild; keine erfundenen Namen/Rollen. Die folgende Verteilung ist ein Vorschlag und muss mit den tatsächlich ausgeführten Aufgaben übereinstimmen.

| Zeit | Bild | Gesprochener Inhalt |
|---|---|---|
| 0–5 s | Vier Personen, Projektname als Einblendung | Arbeitsname und Frage |
| 5–30 s | Jede Person kurz sprechen lassen | Name und tatsächlicher Beitrag |
| 30–43 s | Team, kurzer echter Viewer-Ausschnitt | Motivation und Nutzen |
| 43–50 s | Teamabschluss | C3, wissenschaftliche Grenze |

**Deutsch:**

> Wir sind das vierköpfige Team hinter FlyBrainLab. Unsere Frage: Wie kommen wir von den Verbindungen eines Fliegengehirns zu einer überprüfbaren Vorhersage? Ich bin Valentin und habe [tatsächliche Aufgabe] übernommen. Ich bin [Name 2], zuständig für [Aufgabe]. Ich bin [Name 3], zuständig für [Aufgabe]. Und ich bin [Name 4], zuständig für [Aufgabe]. Gemeinsam verbinden wir wissenschaftliche Quellen, einen kontrollierten neuronalen Test und echte Körperphysik. Unsere Demo macht Ergebnisse, Kontrollen und Grenzen sichtbar. Omnigent soll dabei jeden Forschungsschritt nachvollziehbar organisieren. Wir treten in Challenge drei an. Unsere Vision ist ein körpergebundenes Fliegenmodell; biologisch validierten oder stabilen Flug behaupten wir heute nicht.

**English:**

> We are the four-person team behind FlyBrainLab. Our question is: how can a fly connectome lead to a testable prediction? I’m Valentin, and I worked on [actual contribution]. I’m [name two], responsible for [contribution]. I’m [name three], responsible for [contribution]. And I’m [name four], responsible for [contribution]. Together, we connect scientific evidence, controlled neural experiments, and real body physics. Our demo makes results, controls, and limitations visible. Omnigent is designed to coordinate each research step with a trace we can inspect. We are entering Challenge Three. Our vision is an embodied fly model; we do not claim biologically validated or stable flight today.

Wenn der native Omnigent-Lauf bereits verifiziert ist, „soll … organisieren“ durch „organisiert den dokumentierten Forschungsablauf“ und „is designed to coordinate“ durch „coordinates the recorded research workflow“ ersetzen. Sonst die vorbereitete Fassung beibehalten.

## 2. Product demo — Ziel 54 Sekunden

| Zeit | Echter Nutzerablauf/Bild | Pflichtlabel |
|---|---|---|
| 0–6 s | Öffentliche Startseite öffnen | Recorded simulation / Aufgezeichneter Lauf |
| 6–17 s | Frage und kontrollierten 150-Hz-Input auswählen | Graphgewählte Inputs; keine direkt stimulierten DNg02-Zellen |
| 17–28 s | DNg02-Raten; Sham und getrennte Ausgangsgewichte vergleichen | 200 ms, drei Seeds, alle 25 Readoutzellen |
| 28–41 s | Körpertrajektorie abspielen/pausieren | Open-loop, echte Physik; Ende 38,8 ms |
| 41–54 s | Quelle/Run Record und nächste Entscheidung öffnen | Technische Annahmen und biologische Grenzen |

**Deutsch:**

> FlyBrainLab macht eine wissenschaftliche Modellfrage überprüfbar. Wir öffnen einen aufgezeichneten Simulationslauf. Acht vorab graphgewählte Inputs werden stimuliert; wir lesen fünfundzwanzig flugbezogene DNg02-Zellen aus. In den kontrollierten neuronalen Läufen reagieren diese Zellen. Sham und getrennte Ausgangsverbindungen ergeben keine Antwort. Alle Parameter und Quellen sind verlinkt. Die gespeicherten Spikes steuern anschließend über einen festen Adapter einen vorhandenen Flügelcontroller. Die Ansicht spielt tatsächlich berechnete Körperzustände ab und lässt sich pausieren. Der Körperlauf endet am Referenzende nach achtunddreißig Komma acht Millisekunden; stabiler Flug ist nicht nachgewiesen. So sehen Forschende das Ergebnis, seine Herkunft und die nächste Prüfung: passende Nichtziel-Inputs vergleichen und den Körpercontroller separat stabilisieren.

**English:**

> FlyBrainLab makes a scientific model question inspectable. We open a recorded simulation. Eight inputs, selected from the graph before the experiment, are stimulated; twenty-five flight-related DNg02 neurons are the readout. In the controlled neural runs, these cells respond. Sham stimulation and disconnected input outputs produce no response. Parameters and sources are linked. Saved spikes then drive an existing wingbeat controller through a fixed adapter. This view replays actual body states with playback and pause controls. The body run reaches the reference end after thirty-eight point eight milliseconds; stable flight is not demonstrated. Researchers can inspect the result, its provenance, and the next test: matched non-target inputs and separate controller stabilization.

## 3. Technical walkthrough — Ziel 55 Sekunden

| Zeit | Bild | Kernbeleg |
|---|---|---|
| 0–10 s | Architektur, danach native Trace-Seite | Omnigent und tatsächliche Rollen/Tools |
| 10–21 s | Gepinnte Evidenz/ID-Datei und Design | Versionen, Quelle, zwei Tests vor dem Lauf |
| 21–34 s | Run Record, Messwerte, B-Entscheidung | Numerische Ausführung und veränderte Entscheidung |
| 34–45 s | Adapter/Body-Provenienz, Viewer | Getrennte Ebenen und Open-loop |
| 45–55 s | Grenzen, nächstes Experiment | Kein biologischer Flugnachweis; BrightData-Status ehrlich |

**Deutsch, nur mit geprüftem nativem Trace:**

> Unsere Architektur trennt Forschung, Simulation und Darstellung. Omnigent koordiniert Recherche, Evidenzprüfung, Testplanung, Experiment und Analyse. Die native Rollen- und Toolspur dokumentiert den tatsächlichen Ablauf. Quellen und Neuronenidentitäten sind versioniert; das Design mit zwei Tests war vor dem Lauf fixiert. Python und Brian2 berechnen das vollständige installierte FlyWire-Netz. Die positive DNg02-Antwort führt zum zweiten Test: Ausgangsgewichte der Inputs auf null setzen. Die Antwort verschwindet in allen drei Seeds. Ein eingefrorener Adapter übergibt gespeicherte Spikes an Flybody und MuJoCo. GitHub Pages zeigt diese Daten als Replay. Das ist Open-loop, mit gewählten Motorannahmen. Das Referenzende bei 38,8 Millisekunden ist kein Instabilitätsnachweis; ein separater verlängerter Test fällt. BrightData ist vorbereitet, aber nicht für diese Evidenz verwendet. Biologische Validierung bleibt offen.

**English, only with the verified native trace:**

> Our architecture separates research, simulation, and visualization. Omnigent coordinates research, evidence review, test planning, experiment execution, and analysis. Its native role and tool trace records the actual workflow. Sources and neuron identities are versioned; the two-test design was frozen before execution. Python and Brian2 simulate the complete installed FlyWire network. A positive DNg02 response leads to the second test: setting the inputs’ outgoing weights to zero. The response disappears in all three seeds. A frozen adapter passes saved spikes to Flybody and MuJoCo. GitHub Pages displays these data as a replay. This is open-loop, with chosen motor assumptions. The reference end at 38.8 milliseconds is not instability; a separate extended probe falls. BrightData is prepared but was not used for this evidence. Biological validation remains open.

**Wenn kein verifizierter nativer Trace vorliegt:** Den Anfang ersetzen durch: „Omnigent mit fünf Spezialrollen ist eingerichtet. Die hier gezeigten numerischen Vorläufe wurden unabhängig ausgeführt; die vorgeschriebene native Discovery-Schleife ist noch nicht nachgewiesen.“ / “Omnigent is configured with five specialist roles. The numerical preflight runs shown here were executed independently; the required native discovery loop has not yet been demonstrated.” Das Video darf dann keinen vollständig erfüllten C3-Nachweis behaupten.

## 4. Zusätzliche C3-Demo — Ziel 118 Sekunden

Diese Aufnahme gehört **nicht** in eines der drei 60-Sekunden-HackOS-Felder. Vor dem Upload den akzeptierten Einreichungsweg bestätigen.

| Zeit | Schritt | Tatsächlich zeigen |
|---|---|---|
| 0–12 s | Question | Frage, Readout und Versionslabel |
| 12–30 s | Evidence | Namiki-Quelle mit Fundstelle; geprüfte 25 v783-IDs |
| 30–44 s | Hypothesis / Two tests | versiegeltes Design A/B und Auswahlregel |
| 44–65 s | Experiment | echte native Omnigent-Rollen/Toolreceipts und neue numerische Run-IDs |
| 65–84 s | Result / Updated decision | positive A-Differenz → tatsächlich ausgeführter B-Test → nächster Kontrolltest |
| 84–99 s | Embodiment | echte gekoppelte Trajektorie, 38,8-ms-Referenzende; separater Fall bei 53,6 ms; Adapterlabel |
| 99–110 s | Measured improvement | 427,73 ms vs. 0,282 ms; enger wiederholter ID-Lookup |
| 110–118 s | Grenzen / Next experiment | passende Nichtziel-Inputs, biologische Prüfung, Controllerstabilität |

**Deutsch, nur mit geprüftem nativem Trace:**

> FlyBrainLab untersucht eine konkrete Modellfrage: Können acht graphgewählte Inputs flugbezogene DNg02-Zellen aktivieren, und hängt die Antwort von ihren Ausgangsverbindungen ab?
>
> Die Evidenz kommt aus einer DNg02-Studie an bereits fliegenden, fixierten Fruchtfliegen. Sie motiviert unseren Ausgang, beweist aber keinen autonomen Flug. Offizielle Annotationen liefern fünfundzwanzig passende Identitäten im verwendeten FlyWire-v783-Datensatz. Quellen, Versionen und Fundstellen bleiben erhalten.
>
> Vor dem Lauf haben wir zwei Tests und drei Seeds fixiert. Test A vergleicht hundertfünfzig Hertz Input mit Sham. Bei einer positiven Differenz in jedem Seed folgt Test B: dieselbe Stimulation mit getrennten Ausgangsgewichten. Das ist eine Modellintervention, keine biologische Hemmmethode.
>
> Hier zeigt der native Omnigent-Trace die Spezialrollen, strukturierten Übergaben und tatsächlichen Experimenttools. Brian2 simuliert das vollständige installierte Netz. Der positive A-Befund führt zum B-Test. Im unveränderten Modell antworten die DNg02-Zellen; nach der Ausgangstrennung verschwindet die Antwort. Wir erhalten vollständige Spike-Daten und neue Run Records.
>
> Ein vorab eingefrorener Adapter koppelt die gespeicherten Spikes an echte MuJoCo-Körperphysik. Die Referenz endet nach achtunddreißig Komma acht Millisekunden. Mit verlängerter Referenz fällt das unveränderte Testmuster nach dreiundfünfzig Komma sechs Millisekunden unter die Höhen-Schwelle. Diese technische Kopplung ist Open-loop und biologisch nicht kalibriert.
>
> Ein enger Engpass ist messbar: Wiederholtes Neuparsen der Identitäten braucht im Median rund vierhundertachtundzwanzig Millisekunden, der geprüfte KB-Claim unter eine Millisekunde. Das ist kein Nachweis einer schnelleren gesamten Forschung.
>
> Das nächste Experiment vergleicht passende Nichtziel-Inputs. Für Flug benötigen wir zusätzlich einen stabilen Controller, unabhängige Kalibrierung und sensorische Rückkopplung.

**English, only with the verified native trace:**

> FlyBrainLab asks a concrete model question: can eight graph-selected inputs activate flight-related DNg02 neurons, and does that response depend on their outgoing connections?
>
> Our evidence comes from a DNg02 study in already flying, tethered fruit flies. It motivates the readout but does not establish autonomous flight. Official annotations identify twenty-five matching neurons in our FlyWire v783 dataset. Sources, versions, and locations are retained.
>
> Before execution, we froze two tests and three seeds. Test A compares one hundred fifty hertz input stimulation with sham. A positive difference in every seed triggers Test B: the same stimulus with disconnected outgoing weights. This is a model intervention, not a biological silencing method.
>
> The native Omnigent trace shows specialist roles, structured handoffs, and actual experiment tools. Brian2 simulates the complete installed network. The positive A result leads to Test B. DNg02 cells respond in the unchanged model; disconnecting the outputs removes the response. Complete spike data and new run records are preserved.
>
> A previously frozen adapter couples saved spikes to real MuJoCo body physics. The reference ends after thirty-eight point eight milliseconds. With an extended reference, the unchanged test pattern falls below its height threshold at fifty-three point six milliseconds. This technical coupling is open-loop and not biologically calibrated.
>
> We measured one narrow bottleneck: repeatedly parsing neuron identities takes a median of about four hundred twenty-eight milliseconds; reading the verified knowledgebase claim takes less than one millisecond. This does not establish faster discovery overall.
>
> The next experiment compares matched non-target inputs. Flight also requires a stable controller, independent calibration, and sensory feedback.

## Vor Freigabe einmal gegenprüfen

- Neue native Run-IDs/Resultate gegen den Text prüfen; bei abweichenden Werten Text und Einblendungen gemeinsam ändern.
- Die Zahlen 18,13 ± 0,83 Hz und 100 % Rückgang stammen zunächst aus den unabhängigen Vorläufen. Nur mit passendem Trace und neuen Vergleichsartefakten eine Omnigent-Provenienz nennen.
- Körperzeit der ursprünglichen Kopplung ist **38,8 ms gemessen**, am Referenzende, nicht die angeforderten 200 ms. Separater verlängert-referenter Test: Höhen-Schwelle bei 53,6 ms unterschritten. Die diagnostische Fortsetzung bis 200 ms unter dem Boden ist ausdrücklich kein gültiger Flug. Keine Frames nach dem Abbruch erfinden. Wiedergabe darf verlangsamt werden, mit originaler Millisekundenachse.
- Der ID-Lookup-Benchmark misst warmen lokalen Cache und geprüfte Extraktion. Keine „10× wissenschaftlicher Durchbruch“-Behauptung.
- Keine synthetischen Stimmen/Persönlichkeiten als Team ausgeben. Synthetische Narration, falls verwendet, kennzeichnen. Aktuelle vorbereitete Sprechertexte allein nutzen keine Sprachgenerierung.

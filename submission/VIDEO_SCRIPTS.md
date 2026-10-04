# Vier Videos: Sprechertexte und echte Bildquellen

Stand: 4. Oktober 2026. Ziel für die drei HackOS-Felder: **50–55 Sekunden**, harte Grenze je 60 Sekunden/1 GB. Zusätzliche C3-Demo: **115–120 Sekunden** über den noch zu klärenden eigenen Einreichungsweg.

Die Texte sind Aufnahmeskripte. Vier captionierte MP4-Entwürfe sind vorbereitet. Die Teamvorstellung zeigt bestätigte Teamgröße, Hub, Projektzweck und Arbeitsbereiche; persönliche Namen, Beiträge und Motive bleiben zur Bestätigung offen. Mit einer Stoppuhr laut lesen; bei Bedarf Pausen oder optional markierte Sätze kürzen. Diese Texte beschreiben die streng verifizierten nativen **A- und B-Loops in zwei verbundenen Omnigent-Sitzungen** und die neue **v2-Kopplung über 200 ms**. Die zweite Sitzung liest die vorherige A-Entscheidung vor der B-Planung; beide erhalten eigene Receipts. Vorab unabhängige Läufe dürfen nicht als nachträglich von Omnigent ausgeführt beschrieben werden. Die Projektbezeichnung „FlyBrainLab“ stammt vom Repository und bleibt bis zur Bestätigung der Arbeitsname.

Bildquellen: echte Viewer-Aufnahmen; eingefrorenes Design `research/designs/dng02-input-v1.json`; `research/evidence/DNG02_EVIDENCE.md`; tatsächliche Run-/Vergleichsdateien unter `data/experiments/` und `data/coupling/`; der von Omnigent selbst gespeicherte und geprüfte native Trace. Ein Diagramm erklärt die Architektur, beweist aber keine ausgeführte Orchestrierung. Keine Schlüssel, private Anbieterprofile oder Fremdtexte im Vollbild aufnehmen.

## 1. Team introduction — Ziel 50 Sekunden

**Captionierter Team-Entwurf vorhanden:** `exports/team_intro.mp4`, 46 Sekunden, ohne Tonspur oder Personenbilder. Die Karten nennen ausschließlich bestätigte Fakten und Projektarbeitsbereiche; sie weisen keine persönlichen Rollen zu und erfinden keine Motivation. Die folgende menschliche Aufnahme kann den Entwurf nach Teamprüfung ergänzen oder ersetzen. Ihre Namen, Beiträge und Motive müssen von den tatsächlichen Personen bestätigt sein.

| Zeit | Bild | Gesprochener Inhalt |
|---|---|---|
| 0–5 s | Vier Personen, Projektname als Einblendung | Arbeitsname und Frage |
| 5–30 s | Jede Person kurz sprechen lassen | Name und tatsächlicher Beitrag |
| 30–43 s | Team, kurzer echter Viewer-Ausschnitt | Motivation und Nutzen |
| 43–50 s | Teamabschluss | C3, wissenschaftliche Grenze |

**Deutsch:**

> Wir sind das vierköpfige Team hinter FlyBrainLab. Unsere Frage: Wie kommen wir von den Verbindungen eines Fliegengehirns zu einer überprüfbaren Vorhersage? Ich bin Valentin und habe [tatsächliche Aufgabe] übernommen. Ich bin [Name 2], zuständig für [Aufgabe]. Ich bin [Name 3], zuständig für [Aufgabe]. Und ich bin [Name 4], zuständig für [Aufgabe]. Gemeinsam verbinden wir wissenschaftliche Quellen, einen kontrollierten neuronalen Test und echte Körperphysik. Unsere Demo macht Ergebnisse, Kontrollen und Grenzen sichtbar. Omnigent organisiert den dokumentierten Forschungsablauf. Wir treten in Challenge drei an. Unsere Vision ist ein körpergebundenes Fliegenmodell; biologisch validierten Flug oder autonome Connectome-Steuerung behaupten wir heute nicht.

**English:**

> We are the four-person team behind FlyBrainLab. Our question is: how can a fly connectome lead to a testable prediction? I’m Valentin, and I worked on [actual contribution]. I’m [name two], responsible for [contribution]. I’m [name three], responsible for [contribution]. And I’m [name four], responsible for [contribution]. Together, we connect scientific evidence, controlled neural experiments, and real body physics. Our demo makes results, controls, and limitations visible. Omnigent coordinates the recorded research workflow with an inspectable trace. We are entering Challenge Three. Our vision is an embodied fly model; we do not claim biologically validated flight or autonomous connectome control today.

Die nativen A- und B-Loops sind verifiziert; Rollen-/Teambeiträge bleiben von den tatsächlichen Menschen zu ergänzen.

## 2. Product demo — 55-s-Export / Sprecherziel höchstens 55 Sekunden

| Zeit | Echter Nutzerablauf/Bild | Pflichtlabel |
|---|---|---|
| 0–4 s | Öffentliche Übersicht | Recorded simulation / Aufgezeichneter Lauf |
| 4–10 s | native A42-Stimulation | Graphgewählte Inputs; Population von 25 Readoutzellen, inklusive stiller Zellen |
| 10–15 s | native A42-Sham | gleicher Seed, keine Stimulation, null DNg02-Output |
| 15–21 s | native B42-Ausgangstrennung | null DNg02-Output; 222 andere Spike-Ereignisse bleiben |
| 21–29 s | neue v2-Körpertrajektorie abspielen | vortrainierte Policy stabilisiert; Gehirn ohne Feedback |
| 29–34 s | Body-Vergleich | sechs echte 200-ms-Läufe und gemessene Unterschiede |
| 34–44 s | A-Trace und A→B-Nachweis | zwei verbundene native Sitzungen; A-Entscheidung vor B gelesen |
| 44–48 s | Quellen | Originalquellen und Run Records |
| 48–55 s | Grenzen/Übersicht | passende Nichtziel-Inputs, biologische Kalibrierung und längere Tests |

**Deutsch:**

> FlyBrainLab macht eine wissenschaftliche Modellfrage überprüfbar. Wir öffnen einen aufgezeichneten Lauf. Acht graphgewählte Inputs werden stimuliert; wir messen die Population von fünfundzwanzig flugbezogenen DNg02-Zellen, einschließlich stiller Zellen. Ihr mittlerer Output steigt; Sham und getrennte Ausgangsgewichte liefern keine DNg02-Antwort. Die Eingänge feuern im B-Test weiter. Alle Parameter und Quellen sind verlinkt. Neue Spike-Daten aus dem Omnigent-Test steuern über einen festen Adapter eine veröffentlichte, vortrainierte Flugpolicy. Die Ansicht spielt echte Körperzustände ab und lässt sich pausieren. Sechs Körperläufe erreichen zweihundert Millisekunden ohne vorzeitigen Abbruch. Die bestehende Policy stabilisiert; das Gehirn empfängt keine Körpersensoren. Gelenk- und Positionsunterschiede sind gemessen. Biologische Kalibrierung und längere Flugtests bleiben offen.

**English:**

> FlyBrainLab makes a scientific model question inspectable. We open a recorded run. Eight graph-selected inputs are stimulated; we measure a population of twenty-five flight-related DNg02 cells, including silent cells. Their mean output rises; sham and disconnected outgoing weights give zero DNg02 response. Inputs still spike in B. Parameters and sources are linked. New spikes from the Omnigent test drive a published pretrained flight policy through a fixed adapter. The viewer replays actual body states with playback and pause controls. Six body runs reach two hundred milliseconds without early termination. The existing policy supplies stabilization; the brain receives no body sensors. Joint and position differences are measured. Biological calibration and longer flight tests remain open.

## 3. Technical walkthrough — Ziel 55 Sekunden

| Zeit | Bild | Kernbeleg |
|---|---|---|
| 0–10 s | Architektur, danach native Trace-Seite | Omnigent und tatsächliche Rollen/Tools |
| 10–21 s | Gepinnte Evidenz/ID-Datei und Design | Versionen, Quelle, zwei Tests vor dem Lauf |
| 21–34 s | Run Record, Messwerte, B-Entscheidung | Numerische Ausführung und veränderte Entscheidung |
| 34–45 s | Adapter/Body-Provenienz, Viewer | Getrennte Ebenen und Open-loop |
| 45–55 s | Grenzen, nächstes Experiment | Kein biologischer Flugnachweis; BrightData-Status ehrlich |

**Deutsch, verifizierte A/B-Loops und v2-Kopplung:**

> Unsere Architektur trennt Forschung, Simulation und Darstellung. Omnigent koordiniert fünf Spezialrollen; die nativen Toolspuren belegen A und den verbundenen B-Forschungsloop. Quellen und Neuronenidentitäten sind versioniert, zwei Testdesigns vorab fixiert. Brian2 berechnet das vollständige installierte FlyWire-Netz. Die positive DNg02-Antwort gegen Sham wählt den zweiten Test: Ausgangsgewichte auf null setzen. B entfernt die Antwort in allen drei Seeds; passende Nichtziel-Inputs folgen. Ein eingefrorener Adapter koppelt neue Spikes an Flybody und MuJoCo mit veröffentlichter Flugpolicy. Sechs Läufe erreichen zweihundert Millisekunden ohne vorzeitigen Abbruch; physikalische Unterschiede sind gemessen. Die vortrainierte Policy stabilisiert den Körper; das Gehirn bleibt ohne Rückkanal. GitHub Pages zeigt Replay-Daten. Motorannahmen und biologische Validierung bleiben offen. BrightData wurde für diese Evidenz nicht verwendet.

**English, verified A/B loops and v2 coupling:**

> Our architecture separates research, simulation, and visualization. Omnigent coordinates five specialists; the native traces prove A and its linked B follow-up. Sources and neuron identities are versioned, with two frozen test designs. Brian2 simulates the complete installed FlyWire network. A positive DNg02 response against sham selects the second test: disconnecting outgoing weights. B removes the response in all three seeds; matched non-target inputs follow. A frozen adapter couples new spikes to Flybody and MuJoCo with a published flight policy. Six runs reach two hundred milliseconds without early termination; physical differences are measured. The pretrained policy stabilizes the body; the brain has no feedback. GitHub Pages shows recorded data. Motor assumptions and biological validation remain open. BrightData was not used for this evidence.

A und B besitzen eigene streng geprüfte native Receipts. Die unabhängigen Vorläufe bleiben davon getrennt; eine zweite native Sitzung ist ausdrücklich als verbundener Follow-up ausgewiesen.

## 4. Zusätzliche C3-Demo — Ziel 118 Sekunden

Diese Aufnahme gehört **nicht** in eines der drei 60-Sekunden-HackOS-Felder. Vor dem Upload den akzeptierten Einreichungsweg bestätigen.

| Zeit | Schritt | Tatsächlich zeigen |
|---|---|---|
| 0–12 s | Question | Frage, Readout und Versionslabel |
| 12–30 s | Evidence | Namiki-Quelle mit Fundstelle; geprüfte 25 v783-IDs |
| 30–44 s | Hypothesis / Two tests | versiegeltes Design A/B und Auswahlregel |
| 44–65 s | Experiment | echte native Omnigent-Rollen/Toolreceipts und neue numerische Run-IDs |
| 65–84 s | Result / Updated decision | positive A-Differenz → native B-Ausführung → Antwort entfernt → passende Kontroll-Inputs |
| 84–99 s | Embodiment | v2-Kopplung: 200 ms, Policy stabilisiert, neuronaler Rückkanal fehlt |
| 99–110 s | Measured improvement | 427,73 ms vs. 0,282 ms; enger wiederholter ID-Lookup |
| 110–118 s | Grenzen / Next experiment | passende Nichtziel-Inputs, biologische Prüfung, Controllerstabilität |

**Deutsch, verifizierte A/B-Loops und v2-Kopplung:**

> FlyBrainLab untersucht eine konkrete Modellfrage: Können acht graphgewählte Inputs flugbezogene DNg02-Zellen aktivieren, und hängt die Antwort von ihren Ausgangsverbindungen ab?
>
> Die Evidenz kommt aus einer DNg02-Studie an bereits fliegenden, fixierten Fruchtfliegen. Sie motiviert unseren Ausgang, beweist aber keinen autonomen Flug. Offizielle Annotationen liefern fünfundzwanzig passende Identitäten im verwendeten FlyWire-v783-Datensatz. Quellen, Versionen und Fundstellen bleiben erhalten.
>
> Vor dem Lauf haben wir zwei Tests und drei Seeds fixiert. Test A vergleicht hundertfünfzig Hertz Input mit Sham. Bei einer positiven Differenz in jedem Seed folgt Test B: dieselbe Stimulation mit getrennten Ausgangsgewichten. Das ist eine Modellintervention, keine biologische Hemmmethode.
>
> Hier zeigt der native Omnigent-Trace fünf Spezialrollen, strukturierte Übergaben und tatsächliche Experimenttools. Brian2 simuliert das vollständige installierte Netz. A liefert im Mittel rund achtzehn Hertz über alle fünfundzwanzig Zellen, einschließlich stiller Zellen. Der positive Befund gegen Sham führt zu B. Eine verbundene native Folgesitzung liest diese Entscheidung und führt B aus: null Hertz nach Ausgangstrennung in allen drei Seeds. Vollständige Spike-Daten und neue Run Records bleiben erhalten.
>
> In separaten Körperläufen koppelt ein vorab eingefrorener Adapter die neuen Spikes an eine veröffentlichte, vortrainierte Flugpolicy. Alle sechs gepaarten Läufe erreichen zweihundert Millisekunden ohne vorzeitigen Abbruch. Gelenk- und Positionsunterschiede sind gemessen. Die bestehende Policy stabilisiert; das Gehirn erhält keine Körpersensoren. Diese technische Zuordnung ist biologisch nicht kalibriert.
>
> Ein enger Engpass ist messbar: Wiederholtes Neuparsen der Identitäten braucht im Median rund vierhundertachtundzwanzig Millisekunden, der geprüfte KB-Claim unter eine Millisekunde. Das ist kein Nachweis einer schnelleren gesamten Forschung.
>
> Nach dem bestätigten B-Befund folgen passende Nichtziel-Inputs. Längere Flugtests, unabhängige Kalibrierung und sensorische Rückkopplung bleiben nötig.

**English, verified A/B loops and v2 coupling:**

> FlyBrainLab asks a concrete model question: can eight graph-selected inputs activate flight-related DNg02 neurons, and does that response depend on their outgoing connections?
>
> Our evidence comes from a DNg02 study in already flying, tethered fruit flies. It motivates the readout but does not establish autonomous flight. Official annotations identify twenty-five matching neurons in our FlyWire v783 dataset. Sources, versions, and locations are retained.
>
> Before execution, we froze two tests and three seeds. Test A compares one hundred fifty hertz input stimulation with sham. A positive difference in every seed triggers Test B: the same stimulus with disconnected outgoing weights. This is a model intervention, not a biological silencing method.
>
> The native Omnigent trace shows five specialists, structured handoffs, and actual experiment tools. Brian2 simulates the complete installed network. A produces about eighteen hertz averaged over all twenty-five cells, including silent cells. Its positive result against sham selects B. A linked native follow-up session reads that decision and executes B: zero hertz after disconnection in all three seeds. Complete spike data and new run records are preserved.
>
> In separate body replays, a previously frozen adapter couples new spikes to a published pretrained flight policy. All six paired runs reach two hundred milliseconds without early termination. Joint and position differences are measured. The existing policy supplies stabilization; the brain receives no body sensors. This technical mapping is not biologically calibrated.
>
> We measured one narrow bottleneck: repeatedly parsing neuron identities takes a median of about four hundred twenty-eight milliseconds; reading the verified knowledgebase claim takes less than one millisecond. This does not establish faster discovery overall.
>
> After B confirms model dependency, compare matched non-target inputs. Longer flight trials, independent calibration, and sensory feedback remain necessary.

## Vor Freigabe einmal gegenprüfen

- Neue native Run-IDs/Resultate gegen den Text prüfen; bei abweichenden Werten Text und Einblendungen gemeinsam ändern.
- Die Zahlen 18,13 ± 0,83 Hz und 100 % Rückgang sind durch neue native A/B-Vergleichsartefakte und streng geprüfte Receipts belegt. Bei der Populationsrate zählen alle 25 Zellen; nur 13–14 feuern pro angetriebenem Seed. Die früheren unabhängigen Vorläufe besitzen eigene Provenienz.
- Körperzeit der ursprünglichen Kopplung ist **38,8 ms gemessen**, am Referenzende, nicht die angeforderten 200 ms. Separater verlängert-referenter Test: Höhen-Schwelle bei 53,6 ms unterschritten. Die diagnostische Fortsetzung bis 200 ms unter dem Boden ist ausdrücklich kein gültiger Flug. Keine Frames nach dem Abbruch erfinden. Wiedergabe darf verlangsamt werden, mit originaler Millisekundenachse.
- Die neue **v2** verwendet eine veröffentlichte Autorenpolicy und erreicht in sechs echten gepaarten Läufen 200 ms ohne vorzeitigen Abbruch und mit aktivierten physikalischen Abbruchprüfungen. Dieses separate positive Resultat ersetzt die v1-Diagnose nicht rückwirkend. Körperpolicy-Feedback ist kein Feedback in das Gehirn.
- Der ID-Lookup-Benchmark misst warmen lokalen Cache und geprüfte Extraktion. Keine „10× wissenschaftlicher Durchbruch“-Behauptung.
- Keine synthetischen Stimmen/Persönlichkeiten als Team ausgeben. Synthetische Narration, falls verwendet, kennzeichnen. Aktuelle vorbereitete Sprechertexte allein nutzen keine Sprachgenerierung.

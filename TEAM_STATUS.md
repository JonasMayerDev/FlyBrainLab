# FlyBrainLab – Stand für 09:00

Stand: **4. Oktober 2026, Nachtarbeit**. Challenge 03 Databricks „Agentic Scientific Discovery“. Deadline heute 15:00; internes Ziel 14:30, Feature-Freeze 11:30.

**[Öffentliche Demo](https://valleebo.github.io/FlyBrainLab/)**. Kanonischer Code und Team-Issues bleiben [JonasMayerDev/FlyBrainLab](https://github.com/JonasMayerDev/FlyBrainLab). Die Demo spielt echte aufgezeichnete Ergebnisse ab; der Hosting-Mirror veröffentlicht denselben Viewer.

**Acht von zehn Issues sind belegt abgeschlossen.** #2 und #10 bleiben offen.

## Nachgewiesener Stand

| Teil | Ergebnis | Beleg |
|---|---|---|
| Vollgraph | 138.639 Neuronen, 15.091.983 verarbeitete Verbindungszeilen, Shiu/Brian2 v783 | `data/brain/`, `simulation/` |
| Literatur und Identität | DNg02-Flügelamplitude im bereits bestehenden Flug; 25 v783-Readouts, acht graphgewählte Inputs; vier geprüfte KB-Claims | `research/evidence/` |
| Versiegelter Test | A: Sham gegen Inputstimulation; B: identische Stimulation mit getrennten Ausgangsverbindungen; Seeds 42/43/44 | `research/designs/` |
| Neuronale Resultate | Sham 0 Hz; Drive 17,2/18,8/18,4 Hz; Disconnection 0 Hz in allen Seeds | `data/experiments/`, `data/runs/` |
| Omnigent | Zwei native Sessions mit zehn abgeschlossenen Handoffs und zwölf neuen A/B-Bedingungen; B liest die tatsächliche A-Entscheidung vor Planung und Ausführung | `data/discovery/native-trace*.json` |
| Körper und Adapter | Flybody/MuJoCo mit vorhandener Autorenpolicy: sechs 200-ms-Läufe mit je 1.001 Zuständen und gemessenen Kontrollunterschieden | `data/coupling/native_policy_comparison.json` |
| Viewer | 26 echte neuronale Runs; zwölf nativ verifiziert; sechs passende Körperreplays, Quellen und A→B-Nachweis. öffentlich anonym auf Desktop und in mobiler Emulation geprüft | `frontend/`, `data/replay/` |
| Engpassmessung | Identischer 25-ID-Abruf: 427,73 ms erneutes Parsing gegenüber 0,282 ms KB-Claim; nur warmer lokaler Wiederholungsabruf | `data/experiments/evidence_lookup_benchmark.json` |
| Abgabevorbereitung | Texte DE/EN und vier captionierte MP4-Entwürfe innerhalb der Zeit-/Dateigrenzen, ohne erfundene Personen oder Stimmen | `submission/` |

Die 25 Readouts umfassen auch stumme Neuronen; unter Stimulation reagieren 13–14 davon. Die ursprüngliche Körperreferenz endet bei 38,8 ms. V2 mit vorhandener Autorenpolicy liefert 200 ms echte Zustände ohne vorzeitiges Ende. Stabilisierung stammt aus dieser Policy. Der neuronale Adapter bleibt Open-loop: kein sensorischer Rückkanal zum Gehirn, keine biologische Muskelkalibrierung und kein Nachweis autonomer Fluginitiation.

## Offen und menschlich erforderlich

1. **#2 Zugänge:** Anthropic-/BrightData-Aktivierung, Guthaben, Zonen und Tarif sind unbestätigt. Vorhandener Codex-Zugang hat die native Omnigent-Route ermöglicht. Keine Schlüssel in Chat, Git oder iCloud ablegen.
2. **#10 Abgabe:** echtes Teamfoto aufnehmen; vier Videoentwürfe gemeinsam prüfen und besonders die Teamvorstellung personalisieren. Namen und tatsächliche Beiträge bestätigen. HackOS und danach Google Form ausfüllen, Uploads abspielen und beide Bestätigungen sichern.
3. **Nächstes wissenschaftliches Experiment:** passende Kontrollinputs und belegte sensorische Eingänge prüfen. Dies ist die dokumentierte B-Folgeentscheidung, noch kein ausgeführter Test. Längere Flugstabilität und biologische Kalibrierung bleiben offen; kein Walking-Scopewechsel.

## 09:00–14:30

- **09:00:** Demo gemeinsam öffnen; eine Person für die endgültige Abgabe und eine zweite für den Gegencheck benennen. [Morgencheckliste](submission/MORNING_CHECKLIST.md) abarbeiten.
- **09:30:** belegte Aussagen für Pitch und Videos bestätigen; persönliche Teamvorstellung und Foto aufnehmen.
- **11:30:** Feature-Freeze. Nur Fehler beheben und Abgabe fertigstellen.
- **12:15:** vier Videos kontrolliert; Teamfoto vorhanden; Texte und Links fertig.
- **13:30:** Uploads spätestens beginnen; Verarbeitung und Wiedergabe prüfen.
- **14:30:** HackOS und danach Google Form tatsächlich eingereicht; beide Bestätigungen gesichert.

Startbefehle: [README](README.md). Wissenschaftlicher Nachweis: [Resultate](docs/RESULTS.md). Persönliche Medien und bestätigte Einreichungen dürfen nicht durch synthetische Platzhalter ersetzt werden.

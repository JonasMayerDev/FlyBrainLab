# FlyBrainLab – Stand für09:00

Stand: **4. Oktober2026, Nachtarbeit**. Challenge03 Databricks „Agentic Scientific Discovery“. Deadline heute15:00; internes Ziel14:30, Feature-Freeze11:30.

**Öffentliche Demo: https://valleebo.github.io/FlyBrainLab/**. Anonym auf Desktop und Mobilgerät geprüft. Kanonischer Code und Team-Issues bleiben [JonasMayerDev/FlyBrainLab](https://github.com/JonasMayerDev/FlyBrainLab). Die Demo spielt echte aufgezeichnete Ergebnisse ab.

## Nachgewiesener Stand

| Teil | Ergebnis | Beleg |
|---|---|---|
| Vollgraph |138.639Neuronen,15.091.983Verbindungszeilen, Shiu/Brian2 v783 |`data/brain/`, `simulation/` |
| Literatur/Identität | Namiki DNg02-Flügelamplitude im bereits bestehenden Flug;25v783Readouts,8graphgewählte Inputs; vier echte KB-Claims |`research/evidence/` |
| Versiegelter Test | A:Sham vsInputstimulation; B:identische Stimulation mit getrennten Ausgangsverbindungen; Seeds42/43/44 |`research/designs/` |
| Manuelle Machbarkeit | Sham0Hz; Drive17,2/18,8/18,4Hz; Disconnection0Hz.12echte wissenschaftliche Runs |`data/experiments/`, `data/runs/` |
| Omnigent | Native Codex-Route mit bestehender Anmeldung; reale Spezialisten-Handoffs laufen. Vollständigen Loop erst nach Traceprüfung als fertig markieren |`agents/`, `scripts/export_omnigent_trace.py` |
| Körper/Adapter | Flybody/MuJoCo, echte Zustände; eingefrorener kausaler10msOpen-loop-Adapter, gemessene Körperunterschiede |`data/body/`, `data/coupling/`, `docs/BODY_INTEGRATION.md` |
| Viewer |14echte Neuronenruns und6passende Körpertrajektorien; Controls, Messwerte, Hashes, Quellen. Desktop/Mobilekonsole fehlerfrei |`frontend/`, `data/replay/` |
| Engpassmessung | Wiederholter identischer25-ID-Abruf:427,73ms erneutesParsing vs0,282ms KB-Claim. Warmcachevergleich, keine gesamte Forschungsbeschleunigung |`data/experiments/evidence_lookup_benchmark.json` |
| Abgabevorbereitung | Texte DE/EN, Storyboards, Assetvalidator, reale Produktaufnahme; persönliche Inhalte fehlen |`submission/` |

DNg02-Stimulation im Modell ist kein Beweis für Fluginitiation, natürlichen Sinnespfad oder biologisch kalibrierte Motorsteuerung. Die Körperdaten reichen zunächst38,8ms; die Ursache und längere diagnostische Runs werden getrennt geprüft. Ein neuronaler Run, Adapterausgang, physischer Körperzustand und Rendering bleiben getrennte Belege.

## Offen und menschlich erforderlich

1. **#2 Zugänge:** Anthropic-/BrightData-Aktivierung, Guthaben, Zonen und Tarif sind unbestätigt. Schlüssel nie in Chat/Git/iCloud ablegen. Vorhandener Codex-Zugang ermöglicht die native Omnigent-Route unabhängig davon.
2. **#10 Abgabe:** echtes Vierer-Teamfoto, Namen/Rollen, persönliche Teamvorstellung; vorbereitete Videos anschauen, Uploads und beide Formulare abschließen. Kein Ersatzfoto und keine erfundenen Teammitglieder.
3. **Flugziel:** Längere/stabile und biologisch validierte Flugsteuerung bleibt offen. Kein Walking-Scopewechsel wurde beschlossen. Die derzeitige Demo zeigt eine flugbezogene neuronale Vorhersage mit expliziter Motorannahme.

##09:00–14:30

-09:00: Demo gemeinsam öffnen; eine Person für die endgültige Abgabe und eine zweite für Gegencheck benennen. [Morgencheckliste](submission/MORNING_CHECKLIST.md) abarbeiten.
-09:30: wissenschaftlichen und Körperstand prüfen, reale Grenzen bestätigen; gezielt entscheiden, welche belegten Ergebnisse gepitcht werden.
-11:30: Feature-Freeze. Nur belegte Runs und korrigierte Aussagen verwenden.
-12:15: Teamfoto/Teamintro aufgenommen, Produkt-/Technik-/C3-Videos kontrolliert.
-13:30: Uploads spätestens beginnen; Verarbeitung/Wiedergabe prüfen.
-14:30: HackOS und danach das dort verlinkte Google Form tatsächlich eingereicht; beide Bestätigungen gesichert.

Startbefehle: [README](README.md). Wissenschaftlicher Nachweis: [Resultate](docs/RESULTS.md). Issues nur bei belegter Abnahme schließen; Blocker im jeweiligen Issue konkret benennen.

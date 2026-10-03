# FlyBrainLab – Teamstart und Fortschritt

Stand: **4. Oktober 2026, ca. 01:35 Uhr Europe/Berlin**. Dieser Stand ist ein überprüfter Snapshot; spätere Runs und Entscheidungen hier und im jeweiligen Issue ergänzen.

**Abgabe heute 15:00 Uhr, internes Ziel 14:30, Feature-Freeze 11:30.** Vier Menschen, Challenge 03: Databricks „Agentic Scientific Discovery“.

## Was wir bauen

Wir verbinden ein öffentliches Drosophila-Connectome mit einem neuronalen Modell, einer quellenbasierten Knowledgebase und einem virtuellen Fliegenkörper. Omnigent organisiert die Forschung: Frage → Evidenz → Hypothese → Experiment → Ergebnis → geänderte nächste Entscheidung. Wir wollen ausgewählte Neuronen stimulieren und neuronale Aktivität sowie Körperbewegung messen. Flug bleibt das gewünschte Verhalten; ein engerer erster Demo-Scope ist eine ausdrückliche Teamentscheidung.

Die Jury sieht **echte vorberechnete Experimente in einem öffentlichen Replay-Viewer**. Stack: Vite + TypeScript + Three.js, GitHub Pages über Actions. Die numerische Simulation läuft lokal in Python; die Website spielt exportierte Daten ab.

## Was tatsächlich fertig und geprüft ist

| Baustein | Nachgewiesener Stand | Nachweis im Repository |
|---|---|---|
| Gehirndaten | FAFB FlyWire v783: 138.639 Neuronen, 15.091.983 autorenseitig verarbeitete Neuronpaar-Verbindungszeilen; Hashes/Schema/Indices geprüft | [Manifest](data/brain/manifest.json), [Validierung](data/brain/validation.json) |
| Neuronales Modell | Gepinnter Shiu-Autorencode, Brian2 2.9.0; vollständiger heruntergeladener Graph numerisch gestartet | [Simulation](simulation/README.md), [Autorencode/Lizenz](simulation/vendor/shiu/) |
| Echte Starttests | 20 ms, Seed 42, generisches Target: 150 Hz → 2 Spikes in einem aktiven Neuron; Sham 0 Hz → 0 Spikes. Laufzeit ca. 2,5 bzw. 2,2 s | [Vergleich](data/runs/technical_setup_check.json), [Run Records und Rohdaten](data/runs/) |
| Omnigent | 0.16.0, Supervisor + fünf Spezialagenten; echte Tools/Policies und native Tool-Subprozesse offline geprüft | [Bundle](agents/fly-discovery/), [Prüfbericht](agents/setup-validation.json) |
| Lokaler Dienst | Auf dem eingerichteten Mac gestartet, Healthcheck erfolgreich; Dienst startet nicht automatisch auf einem Teamrechner | [Startanleitung](agents/README.md) |
| Knowledgebase | Lokal: vier Quellen, ein echter Autor-README-Snapshot, zwei Setup-Run-Records, bisher null Funktionsclaims | [Schema und Einrichtung](research/README.md), [Quellenmetadaten](research/seed_sources.json) |
| BrightData-Anbindung | SERP-/Web-Unlocker-Tools implementiert; zusammen mit KB 22 Offline-Tests bestanden | [Adapter](scripts/brightdata_client.py), [Tests](tests/) |
| Teamaufgaben | Zehn Issues mit Priorität, Aufgaben und Abnahmekriterien angelegt | [Issue-Übersicht](GITHUB_ISSUES.md) |

**Die Starttests liefen außerhalb Omnigent und wurden retrospektiv verglichen.** Sie prüfen die numerische Umgebung. Noch kein funktionell validiertes Target, kein Körperadapter, kein Flugnachweis und keine abgeschlossene C3-Forschungsschleife. FlyWire-v783 ist ein Gehirn-Connectome, kein automatisch anschließbarer vollständiger Körpercontroller.

## Was uns gerade blockiert bzw. noch fehlt

- Gültiger Claude-API-Zugang und tatsächlicher Saldo; Schlüsselpräsenz ist noch kein erfolgreicher Aufruf.
- BrightData-API-Key, SERP-/Web-Unlocker-Zonen und bestätigter Requesttarif; Angebote/Saldo noch unbestätigt.
- Quellenbelegte Funktion sowie kompatible v783-Stimulations- und Ausleseneuronen.
- Vorab eingefrorenes wissenschaftliches Testdesign und tatsächlich ausgeführter Omnigent-Experimentloop.
- Flybody/MuJoCo-Baseline, Motoradapter/Körperkopplung und gegebenenfalls sensorischer Rückkanal.
- Öffentlicher Viewer und Pages-Deployment. Das GitHub-Repository ist noch keine öffentliche Simulationsdemo.
- Abgabeort der zusätzlichen zweiminütigen Track-Demo.

## Vier parallele Arbeitsbereiche

Rollen sind ein Vorschlag; Namen/Handles im Team festlegen und die passenden Issues übernehmen.

| Person/Rolle | Erste konkrete Aktion | Danach | Issues |
|---|---|---|---|
| A: Recherche/KB | Eine Funktion anhand von Primärliteratur belegen; passende v783-IDs und Fundstellen prüfen | Zwei Tests und begründete Auswahl mit B einfrieren; Claims/Unsicherheiten dokumentieren | [#3](https://github.com/JonasMayerDev/FlyBrainLab/issues/3), [#4](https://github.com/JonasMayerDev/FlyBrainLab/issues/4) |
| B: Omnigent/Gehirn | Anbieterzugänge sicher einrichten, ein Modell-/Such-/Abruf-Handoff tatsächlich testen | Ausgewählten Versuch unter Omnigent ausführen, Ergebnisse und veränderte nächste Entscheidung sichern | [#2](https://github.com/JonasMayerDev/FlyBrainLab/issues/2), [#5](https://github.com/JonasMayerDev/FlyBrainLab/issues/5) |
| C: Körper/Integration | Ein vorhandenes Flybody/MuJoCo-Beispiel starten und echte Körperzustände exportieren | Mit B dokumentierten Motoradapter einfrieren und Kontrollvergleich versuchen | [#6](https://github.com/JonasMayerDev/FlyBrainLab/issues/6), [#7](https://github.com/JonasMayerDev/FlyBrainLab/issues/7) |
| D: Frontend/Abgabe | Öffentliches Vite/Three.js-Gerüst veröffentlichen; vorhandene technische Run-Daten als solche anzeigen | Echte Forschungsruns einbinden; Foto/Videos und doppelte Abgabe koordinieren. Valentin kann Darstellung/Video übernehmen | [#1](https://github.com/JonasMayerDev/FlyBrainLab/issues/1), [#8](https://github.com/JonasMayerDev/FlyBrainLab/issues/8), [#10](https://github.com/JonasMayerDev/FlyBrainLab/issues/10) |

[Resultate/Engpassmessung #9](https://github.com/JonasMayerDev/FlyBrainLab/issues/9) gemeinsam durch A/B/D bearbeiten. Jede Abgabe bekommt eine verantwortliche Person und einen Gegencheck.

## Start auf einem weiteren Rechner

Die geprüfte Laufumgebung ist macOS/arm64 mit Python 3.12.14 und 8 GiB RAM. Die KB nutzt Unix-Dateisperren; Windows ist hier nicht geprüft. Python 3.12 und `uv` bereitstellen, dann auf Mac/Linux:

```sh
git clone https://github.com/JonasMayerDev/FlyBrainLab.git
cd FlyBrainLab
UV_CACHE_DIR="$PWD/.cache/uv" uv venv --python 3.12 .venv
UV_CACHE_DIR="$PWD/.cache/uv" uv pip install --python .venv/bin/python -r requirements.lock
.venv/bin/python scripts/omnigent_run.py --check
```

Nur für die neuronalen Runs sind zusätzlich die ca. 104 MB Originaldaten nötig:

```sh
.venv/bin/python -m simulation.download_brain
.venv/bin/python -m simulation.brain validate
```

KB lokal anlegen und nur mit Quellenmetadaten starten:

```sh
.venv/bin/python scripts/kb_store.py init
.venv/bin/python scripts/kb_store.py seed
```

Der lokale KB-Inhalt des zuerst eingerichteten Rechners wird **nicht** durch Git übertragen. Kleine tatsächliche Setup-Ergebnisse liegen bereits unter `data/runs/`; neue Quellen/Claims/Ergebnisse nur über bewusst geprüfte Exporte austauschen. Eigene Arbeit in getrennten Branches führen und Changes über kleine PRs zusammenführen.

### Claude und BrightData

Die konkreten BrightData-Kontoschritte stehen in [Issue #2](https://github.com/JonasMayerDev/FlyBrainLab/issues/2). Die vorhandene direkte API-Anbindung braucht SERP- und Web-Unlocker-Zonen; kein zusätzlicher MCP-Umbau erforderlich.

Im interaktiven Projektterminal:

```sh
.venv/bin/python scripts/with_credentials.py --anthropic --brightdata --unlocker -- .venv/bin/python scripts/omnigent_run.py
```

Schlüssel werden verdeckt abgefragt und nur an den Kindprozess weitergegeben. Keine Keys/Codes in GitHub, Chats, Videos oder eine `.env` im iCloud-Projekt schreiben. Zonennamen und konservativen Requestpreis aus dem aktivierten Konto eingeben. Kostenlimits sind begrenzte Requests/Schätzungen, keine garantierte Providerrechnung.

Der erste Launcher-Prompt recherchiert und interpretiert vorhandene Setup-Daten. Anschließend den ausgewählten **neuen** wissenschaftlichen Test wirklich unter Omnigent ausführen; bloßes Einlesen alter Runs schließt #5 nicht.

## Kontrollpunkte bis zur Abgabe

Das ursprüngliche Ziel „Pages bis 01:30“ wurde nicht erreicht; Web/Pages ist der nächste parallele Meilenstein. Den Abendstand sichern, bevor ihr pausiert; ungeprüfte Nachtjobs nicht als fertige Arbeit einplanen.

| Zeitpunkt Europe/Berlin | Prüfpunkte |
|---|---|
| Jetzt | A/B: Zugänge, belegte Targets/Testplanung; C: Körperbaseline; D: öffentliches Viewer-Gerüst |
| 09:30 | Kopplungs-/Flugmachbarkeit ausdrücklich im Team entscheiden. Bei Blockern genaue Ursache/Stand sichern, Scope gemeinsam wählen |
| 11:30 | Feature-Freeze; tatsächlicher Omnigent-Test, Auswertung und nächste Entscheidung gesichert |
| 12:15 | Öffentliche URL und Repo/Assets auf fremdem Gerät geprüft; danach Aufnahme |
| 13:30 | Spätestens Uploads starten und Verarbeitung/Wiedergabe prüfen |
| 14:30 | HackOS und Google Form eingereicht, beide Bestätigungen gesichert |
| 15:00 | Offizielle Deadline; Nachfrist nicht als Arbeitsbudget nutzen |

Abgabe: Teamfoto; drei Plattformvideos jeweils ≤60 s/1 GB; zusätzliche zweiminütige C3-Demo; Repository/Policies/Evidenz/Experimente/Resultate/gemessene Verbesserung/nächstes Experiment. Vollständige Details: [Hackathon-Plan](HACKATHON_PLAN.md), [C3-Brief](Challenges/c3.pdf).

## Fortschritt aktualisieren

Nach jedem Meilenstein im passenden Issue kurz notieren: getesteter Befehl, Datum/Run-ID, tatsächliches Ergebnis, Artefakt-/Commit-Link, Blocker und nächste Entscheidung. Status nur auf „erledigt“ setzen, wenn die Abnahmekriterien belegt sind. #1 bleibt nach dem ersten Code-Push offen, bis Pages öffentlich funktioniert.

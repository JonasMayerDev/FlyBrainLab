# Fly Discovery – lokales Hackathon-Setup

Challenge 03: Databricks „Agentic Scientific Discovery“. Deadline: 4. Oktober 2026, 15:00 Europe/Berlin.

**Teammitglieder: zuerst [TEAM_STATUS.md](TEAM_STATUS.md) lesen.** Dort stehen geprüfter Fortschritt, aktuelle Blocker, vier parallele Arbeitsbereiche und konkrete Startschritte. Aufgaben: [GitHub-Issues](https://github.com/JonasMayerDev/FlyBrainLab/issues).

Das Setup verbindet ein vorhandenes Drosophila-Gehirnmodell mit einer lokalen Evidenzablage und einer nativen Omnigent-Agentenarchitektur. Die spätere öffentliche Demo spielt echte Ergebnisse ab. Körperkopplung, Flug und veröffentlichter Viewer sind noch nicht umgesetzt.

## Was bereits funktioniert

| Baustein | Geprüfter Stand |
|---|---|
| Python | Isolierte `.venv`, CPython 3.12.14; direkte und vollständige Dependency-Pins |
| Gehirndaten | FAFB FlyWire v783: 138.639 Neuronen und 15.091.983 autorenseitig verarbeitete Verbindungszeilen |
| Modell | Gepinnter Shiu-Autorencode, Brian2 2.9.0; Lizenz und Datei-Prüfsummen erhalten |
| Numerischer Starttest | Vollständiger heruntergeladener Graph, 20 ms simulierte Zeit: 150-Hz-Pilot erzeugt 2 Spikes, 0-Hz-Sham 0 Spikes |
| Omnigent | 0.16.0 installiert; Supervisor plus fünf Spezialagenten, konkrete Tools und Policies mit dem installierten Parser geprüft |
| Lokaler Omnigent-Dienst | Gestartet; `/health` an `http://127.0.0.1:6767` antwortet erfolgreich. Live-Modellzugang noch nicht geprüft |
| Native Toolausführung | Echte Omnigent-Tool-Subprozesse lesen Setupstatus und Ergebnisdateien; keine Modellaufrufe dafür nötig |
| Lokale Knowledgebase | Vier Quellen, ein heruntergeladener Autor-README-Snapshot und zwei tatsächliche neuronale Setup-Run-Records |
| BrightData | SERP-/Web-Unlocker-Adapter verdrahtet; 22 Offline-Tests für Adapter und Speicherung bestanden |
| Git | Dieses Repository enthält den lokalen Code-/Dokumentationsstand und kleine echte Ergebnisse; öffentlicher Viewer/Pages noch offen |

GitHub-Repository: [JonasMayerDev/FlyBrainLab](https://github.com/JonasMayerDev/FlyBrainLab). Schreibzugriff geprüft, zehn Teamaufgaben erstellt; Übersicht in [GITHUB_ISSUES.md](GITHUB_ISSUES.md). Große Originaldaten, Secrets und lokale Dienste/KB sind ausgeschlossen; die kleinen Spike-Parquet-Dateien der tatsächlichen Setup-Runs sind enthalten.

Die kurzen neuronalen Läufe sind technische Setupchecks, keine biologische Funktionsvalidierung. Sie liefen vor der Omnigent-Einrichtung und werden auch so gespeichert. Der Vergleich wurde retrospektiv dokumentiert. Kein Körperadapter, kein sensorischer Rückkanal und kein Flugnachweis.

## Dateien und lokale Ablage

```text
agents/fly-discovery/       native Omnigent-Konfiguration, Spezialagenten, Tools und Policies
simulation/                Download, Validierung und begrenzter neuronaler Pilot
simulation/vendor/shiu/    unveränderter Autorencode, MIT-Lizenz
data/brain/                Datensatzmanifest, Validierung, große lokale Datendateien
data/runs/                 echte technische Run Records und Spike-Dateien
scripts/                   BrightData, lokale KB, Start- und Statuswerkzeuge
research/                  Quellenmetadaten und Dokumentation
tests/                     Offline-Verifikation ohne bezahlte Aufrufe
```

**Die Knowledgebase bleibt außerhalb von iCloud Drive:**

```text
~/Library/Application Support/FlyDiscovery/knowledgebase/
  sources.jsonl
  claims.jsonl
  runs.jsonl
  snapshots/
```

Omnigent speichert seinen veränderlichen Dienstzustand unter `~/Library/Application Support/FlyDiscovery/omnigent/`. Das Projekt selbst liegt in iCloud Drive; deshalb keine echte `.env` mit Schlüsseln dort anlegen. `RESEARCH_KB_DIR` kann den KB-Pfad explizit ändern. Öffentliche Exporte aus der lokalen KB sind ein separater späterer Schritt.

## Jetzt prüfen

Im Terminal dieses Projektordners:

```sh
.venv/bin/python scripts/check_setup.py
.venv/bin/python scripts/omnigent_run.py --check
.venv/bin/python scripts/brightdata_client.py status
```

Diese Befehle benötigen keine Schlüssel und lösen keine Modell-/BrightData-Aufrufe aus. Der native Configcheck prüft auch die tatsächlich geladenen Tools je Rolle; syntaktisch akzeptiertes YAML allein genügt nicht.

## Fehlende Zugänge einrichten und den echten Agentenlauf starten

1. Anthropic-Angebot einlösen und den tatsächlichen Console-Saldo prüfen. Dort einen API-Key für das Teamprojekt erstellen.
2. BrightData-Angebot aktivieren. API-Key und Namen einer **SERP-API-Zone** sowie einer **Web-Unlocker-Zone** bereithalten; der Angebotscode ist kein API-Key.
3. Den konservativen Preis pro Request aus den aktiven Produkttarifen prüfen; für den gemeinsamen Zähler den höheren zutreffenden Wert verwenden. Das Schätzbudget ersetzt keine anbieterseitige Kostengrenze.
4. Den folgenden Befehl lokal starten. Schlüssel werden verdeckt abgefragt und nur über die Prozessumgebung an den frisch gestarteten CLI-Runner weitergegeben; weder in den Projektdateien noch als Kommandozeilenargument gespeichert.

```sh
.venv/bin/python scripts/with_credentials.py --anthropic --brightdata --unlocker -- .venv/bin/python scripts/omnigent_run.py
```

Die Eingabe wird bei Schlüsseln nicht angezeigt. Zonennamen und Requestpreis sind normale Eingaben. Im Startwrapper gelten maximal zehn BrightData-Anfragen und 1 USD geschätztes Budget; die Omnigent-Konfiguration enthält weitere Session-/Agentenbaum-Limits. Bereits reservierte Requests bleiben nach Fehlern mitgezählt, weil ein Timeout eine berechnete Anfrage sein kann.

Der erste Prompt liest vorhandene echte Setup-Ergebnisse, delegiert Recherche/Evidenzprüfung, plant zwei künftige Tests und leitet eine nächste Entscheidung ab. **Eine abgeschlossene wissenschaftliche C3-Schleife ist damit noch nicht nachgewiesen.** Der ausgesuchte wissenschaftliche Versuch muss anschließend tatsächlich unter Omnigent ausgeführt und interpretiert werden.

API-Zugriff und Live-Handoffs sind mangels Zugangsdaten noch nicht getestet. Eine grüne Offline-Prüfung oder bloße Schlüsselpräsenz bestätigt keinen gültigen Anbieterzugang.

## Gehirndaten und Modell reproduzieren

```sh
.venv/bin/python -m simulation.download_brain --verify-only
.venv/bin/python -m simulation.brain validate
.venv/bin/python -m simulation.brain pilot --duration-ms 20 --rate-hz 150 --seed 42
```

Neu herunterladen: `.venv/bin/python -m simulation.download_brain`. Große Originaldateien werden nicht in normales Git aufgenommen; Quellen, Version, Lizenz, Größe und SHA256 stehen in `data/brain/manifest.json`.

Das neuronale Modell nutzt alle heruntergeladenen v783-Verbindungszeilen. Laufzeitanpassungen sind in jedem Run Record dokumentiert: nur benötigte Connectivity-Spalten laden und eine ungültige `w=0`-Resetzuweisung aus den Laufzeitparametern entfernen. Die Vendorquelle bleibt unverändert. FlyWire-IDs in JSON/JavaScript als Strings erhalten.

## Installation auf einem weiteren Rechner

Python 3.12 und `uv` bereitstellen, dann:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv venv --python 3.12 .venv
UV_CACHE_DIR="$PWD/.cache/uv" uv pip install --python .venv/bin/python -r requirements.lock
.venv/bin/python -m simulation.download_brain
.venv/bin/python scripts/kb_store.py init
.venv/bin/python scripts/kb_store.py seed
.venv/bin/python scripts/omnigent_run.py --check
```

Die neue lokale KB startet mit Metadaten; vorhandene Wissens- und Run-Daten werden nicht automatisch über Git übertragen.

## Verifikation und nächste Arbeit

```sh
.venv/bin/python -m unittest discover -s tests -v
UV_CACHE_DIR="$PWD/.cache/uv" uv pip check --python .venv/bin/python
```

Geprüft sind unter anderem konkurrierende Schreibzugriffe, gemeinsame Requestlimits, Provenienz, gepinnte Quellenfassungen, String-IDs und Secret-Redaktion. Keine echten API-Ergebnisse werden durch Testfixtures ersetzt.

Als Nächstes: Anbieterzugänge tatsächlich testen, eine funktionell belegte v783-Neuronengruppe recherchieren, die wissenschaftliche Testwahl einfrieren und ausführen. Körper-/Motoranbindung und öffentlicher Three.js-Replay folgen darauf. Abgabecheckliste und Zeitplan: `HACKATHON_PLAN.md`; Stack und Credits: `STACK.md`; technische Details: `agents/README.md`, `simulation/README.md`, `research/README.md`.

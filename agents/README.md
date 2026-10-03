# Lokale Omnigent-Orchestrierung

Installierte und geprüfte Version: **Omnigent 0.16.0**, Python 3.12. Die native Agenten-Bundle liegt unter `agents/fly-discovery/`. Sie ersetzt keinen wissenschaftlichen Versuch durch LLM-Antworten: Omnigent delegiert Aufgaben und ruft echte Recherche-, Knowledgebase- und numerische Tools auf.

| Agent | Aufgabe | Tatsächliche Toolrechte |
|---|---|---|
| `fly_discovery` | Aufgaben delegieren, Handoffs prüfen, Ergebnis und nächsten Schritt verbinden | Fünf native Spezialagenten, definierte lokale Tools |
| `researcher` | Primärquellen finden und lesen | BrightData SERP/Unlocker, Quellenmetadaten, KB-Suche |
| `evidence_reviewer` | Fundstelle, Version und Aussage prüfen | KB-Suche, begrenzter Quellenabruf, Claims speichern |
| `hypothesis_planner` | Zwei mögliche Tests entwerfen, einen begründet auswählen | KB-Suche, Setupstatus, gekennzeichnete Hypothesen speichern |
| `experimenter` | Vorhandene echte Setup-Runs prüfen; gegebenenfalls einen kleinen Pilot ausführen | Setupstatus, Artefakte, KB-Runs, 1–20-ms-Pilot |
| `analyst` | Messwerte interpretieren und nächste Entscheidung formulieren | Lokale Artefakte und KB-Runs |

Native Unteragenten sind im `config.yaml` über `tools.agents` eingetragen. Jeder besitzt eigene `instructions.md`, konkrete `@tool`-Wrapper und `guardrails`. Es gibt keine selbstgeschriebene Ersatz-Orchestrierung und keine allgemeinen Shell-, Dateiänderungs-, Veröffentlichungs- oder Sharing-Tools.

## Stand und erste Befehle

Ohne Schlüssel lässt sich die gesamte Konfiguration offline prüfen:

```sh
.venv/bin/python scripts/omnigent_run.py --check
```

Dieser Check lädt den echten Omnigent-Parser, alle sechs Agenten, die Tool-Schemas und die Policies. Er führt keine Modellaufrufe, BrightData-Aufrufe oder neue Simulation aus. Die vorhandenen numerischen Setup-Runs entstanden vor der Omnigent-Session und werden entsprechend zugeschrieben.

Für den ersten echten Agentenlauf werden ein aktivierter Anthropic-API-Zugang sowie BrightData-API-Key, SERP-Zone, Web-Unlocker-Zone und ein zum aktiven Produktplan passender Preis pro Request benötigt. Die eigentlichen Modell-/Webzugänge sind bisher **nicht live getestet**. Im interaktiven Terminal:

```sh
.venv/bin/python scripts/with_credentials.py --anthropic --brightdata --unlocker -- .venv/bin/python scripts/omnigent_run.py
```

Die Schlüssel werden verdeckt eingegeben und nur dem Kindprozess übergeben. Es wird keine Schlüsseldatei angelegt. Keine Schlüssel in Chat, GitHub, Videos oder Beispielkonfigurationen einfügen. Der Launcher prüft alle erforderlichen BrightData-Einstellungen vor dem Modellstart. Ein gültiger Schlüssel allein beweist noch keinen aktivierten Guthabensaldo.

Ein konkretes für den aktiven Zugang zugelassenes Claude-Modell kann optional über `scripts/omnigent_run.py --model <Modell-ID>` gewählt werden. Ohne diese Option verwendet die native Claude-SDK-Harness ihren verfügbaren Providerdefault. Open Source benötigt für diese Route keinen Databricks-Workspace; Modell- und Webaufrufe bleiben vom jeweiligen Zugang/Budget abhängig.

Der erste Prompt veranlasst echte Recherche und native Handoffs. Er prüft/importiert bestehende numerische Runs, entwirft zwei weitere Tests und lässt den Analyseagenten eine nächste Entscheidung ableiten. Ein vorhandener technischer Pilot wird nicht unnötig wiederholt. Die heute eingerichtete Verbindung zum Modell kann bei einer späteren kleinen Probe explizite **v783-Neuronen-IDs als Strings** übernehmen.

## Lokaler Zustand und Grenzen

- Knowledgebase: standardmäßig `~/Library/Application Support/FlyDiscovery/knowledgebase`, überschreibbar mit `RESEARCH_KB_DIR`.
- Omnigent: standardmäßig `~/Library/Application Support/FlyDiscovery/omnigent/data` und `/config`, überschreibbar mit `OMNIGENT_DATA_DIR` und `OMNIGENT_CONFIG_HOME`. `HOME` wird nicht geändert. Diese Zustände liegen außerhalb des iCloud-Projektordners und des Git-Repositories.
- Die lokale Omnigent-Weboberfläche ist die Arbeitsoberfläche für das Team. Die öffentliche GitHub-Pages-Replay-Demo wird separat gebaut.
- Pro Spezialagent sind zehn Toolcalls und eine gemessene Claude-Kostenschwelle von 0,30 USD konfiguriert; beim Supervisor 40 Calls/1 USD, für seinen Agentenbaum zusätzlich 2 USD. Omnigent prüft gemessene Kosten vor weiteren Aktionen. Das ist keine Vorabgarantie für die Rechnung einer bereits begonnenen Modellantwort; Produktkontolimits bleiben relevant. Die Policies sperren hier alle benannten Claude-Modellfamilien nach Erreichen der Schwelle.
- BrightData hat einen getrennten, prozessübergreifenden Requestzähler mit Cache und Schätzbudget. Der eingegebene Requestpreis muss aus eurem aktiven Plan kommen. Die Omnigent-Modellkostenpolicy deckt Webzugriffskosten nicht ab.
- Der kleine Gehirnpilot prüft die numerische Laufumgebung. Er ist keine biologische Validierung, kein Körper-/Flugnachweis und kein Ersatz für das geforderte C3-Experiment. Körperkopplung und sensorischer Rückkanal sind weiterhin offen.
- Ohne echte Modell-/BrightData-Aufrufe ist die Discovery-Schleife nicht verifiziert. Offline-Parser- und Toolchecks werden in `setup-validation.json` getrennt dokumentiert.

## Dokumentation und versionsbezogene Entscheidung

Die mit 0.16.0 getestete native Directory-Bundle verwendet konkrete Toolwrapper pro Agent. Die Kompatibilitätsroute für einzelne YAML-Dateien ließ bei unserem Parsercheck Inline-Unteragenten-Instructions, `inherit`-Tools und Unteragenten-Policies weg. Deshalb wird diese Route nicht als Projekteinstieg verwendet.

Primärquellen: [Omnigent Repository/Installation](https://github.com/omnigent-ai/omnigent), [native AgentSpec](https://github.com/omnigent-ai/omnigent/blob/main/omnigent/spec/AGENTSPEC.md), [Policies](https://github.com/omnigent-ai/omnigent/blob/main/docs/POLICIES.md), [lokale Zustandsverzeichnisse](https://github.com/omnigent-ai/omnigent/blob/main/docs/DATA_DIR_LAYOUT.md). Die konkrete installierte Version und deren Parser wurden lokal geprüft; bewegliche `main`-Dokumentation allein ist kein Laufnachweis.

# Native Omnigent-Forschung

Omnigent 0.16.0 orchestriert Supervisor und fünf echte Spezialisten. Der native Directory-Bundle ist `agents/fly-discovery/`; `scripts/omnigent_run.py` erzeugt pro Start eine isolierte Kopie. Kein selbst geschriebenes Agentenframework ersetzt Omnigent.

| Rolle | Aufgabe |
|---|---|
| `fly_discovery` | Reale Handoffs und ergebnisabhängige nächste Aufgaben |
| `researcher` | Tatsächliche gehashte Primärquellen lesen |
| `evidence_reviewer` | Literaturbedingungen und v783-Identitäten prüfen |
| `hypothesis_planner` | Versiegelte A/B-Tests vergleichen und wählen |
| `experimenter` | Neues eingefrorenes numerisches Experiment ausführen |
| `analyst` | Kontrollen interpretieren und nächste Entscheidung speichern |

## Start

Mit angemeldeter Codex-CLI, kontoabhängig unterstütztem Modell und importierter Evidenz:

```sh
.venv/bin/python scripts/omnigent_run.py --check --harness codex --evidence-mode existing --model gpt-5.5
.venv/bin/python scripts/omnigent_run.py --harness codex --evidence-mode existing --model gpt-5.5 --discovery
```

`existing` entfernt BrightData-Suche/Abruf tatsächlich aus dem Bundle. Die Primärquellen wurden unabhängig direkt bezogen. Dies ist kein bestätigter BrightData-Zugang. Die optionale Claude-/BrightData-Route benutzt den bestehenden verdeckten Credentials-Helfer; Konten/Tarife müssen vorher bestätigt sein.

Die Codex-Route nutzt bestehende CLI-Anmeldung, schreibt keine Benutzerkonfiguration um und exportiert keine Anmeldung. Native CLI-MCP-Server werden pro Prozess unterdrückt; Shell/UnifiedExec/Websearch sind abgeschaltet. Die Omnigent-Policy erlaubt deklarierte Recherche-/KB-/Simulationswerkzeuge und notwendige Agenten-Lifecycle-Ereignisse. `sys_agent_start` ist ein interner Startcheck: dessen Blockierung verhindert Inbox/Handoffs. Die Codex-Route begrenzt den Supervisor auf 40 und Spezialisten auf 20 Toolaufrufe. API-äquivalente Verbrauchsschätzungen im vorhandenen Abonnement bleiben auf6 USD für den Supervisor,6 USD pro Spezialist und16 USD im Baum begrenzt. Das ist keine neue API-Anmeldung oder bestätigte Rechnung; die Claude-Route behält ihre kleineren ursprünglichen Kostenlimits. Die Trace dokumentiert beobachtete Werkzeuge; die Policy allein beweist keine umfassende Betriebssystem-Sandbox für sämtliche nativen Dateioperationen.

## Async-Handoffs

`sys_session_send` liefert sofort einen Handle. Der Supervisor delegiert genau einmal und beendet/yieldet seinen aktuellen Turn. Omnigent wartet im Runner-Kontext und weckt den Parent nach Fertigstellung; dann wird die Inbox einmal gelesen. Wiederholtes Polling kann40 Toolaufrufe verbrauchen und die eigentliche Kette blockieren. Der Headless-CLI-Lauf folgt den nativen Wakeups; keine externe Nachbildung von Agentenantworten.

## Belege

`run_frozen_experiment` führt ausschließlich A/B/calibration aus dem versiegelten Design aus und schreibt einen echten Tool-Receipt. `save_discovery_record` hält Question, Quellen/Claims, Testkandidaten, Ergebnis und nächste Entscheidung fest; es behauptet selbst keinen verifizierten Gesamtloop. Der separate Export prüft native Session-/Inbox-/Toolbelege und verknüpfte Dateien. Manuelle Machbarkeitsruns bleiben als solche gekennzeichnet.

```sh
.venv/bin/python -m scripts.export_omnigent_trace --help
```

Mutable Omnigent-Daten bleiben unter `~/Library/Application Support/FlyDiscovery/`, außerhalb iCloud. Nur gezielt bereinigte Ergebnis-Traces gehören ins Repository; keine Auth-/State-Tabellen oder vollständigen fremden Artikeltexte.

Bei einem behebbaren Fehler kann derselbe native Conversation-Baum mit `--resume <actual32hexID>` fortgeführt werden. Reale frühere Handoffs/Receipts bleiben erhalten; die Conversation behält ihre ursprüngliche Agentenversion. Änderungen an deren Policy-Bundle erfordern eine frische native Session; ein neu registrierter Bundle ersetzt das bestehende Spec nicht rückwirkend. Startup-Gates können Parent-Verbrauch in den Child-Kontext übernehmen; deshalb liegen die Codex-Rollenlimits nicht unter dem Supervisorlimit.

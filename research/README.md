# Lokale Knowledgebase und Bright Data

Die Knowledgebase speichert Quellen, Claims und Run Records als JSONL. Sie ist
kein Connectome-Speicher: die Millionen Verbindungen des Gehirnmodells gehören
in dessen eigene Datendateien.

Standardpfad auf diesem Mac:
`~/Library/Application Support/FlyDiscovery/knowledgebase`.
Dieser Pfad liegt außerhalb des iCloud-Projektordners. `RESEARCH_KB_DIR` kann ihn
ändern; ein Pfad im aktuellen Projektordner könnte durch iCloud synchronisiert
werden. Die Software selbst verwendet keinen Cloud-Datenbankdienst.

## Start und Status

Vom Projektordner aus:

```sh
.venv/bin/python scripts/kb_store.py init
.venv/bin/python scripts/kb_store.py seed
.venv/bin/python scripts/kb_store.py status
.venv/bin/python scripts/brightdata_client.py status
```

Der erste Aufruf legt den lokalen Ordner an. Die Seed-Datei enthält ausschließlich
vier Quellenmetadaten mit `retrieval_status: metadata_only`. Es werden keine
biologischen Findings, Experimente oder vermeintlichen Flugresultate erfunden.
`brightdata_client.py status` liest nur Konfiguration; keine Netzwerkverbindung,
keine Schlüsselwerte und keine neuen Dateien.

## Bright Data anschließen

Root verwaltet die sichere Eingabe/Umgebung. Die Module benötigen:

| Variable | Bedeutung |
|---|---|
| `BRIGHTDATA_API_KEY` | API-Schlüssel, ausschließlich im Prozess-Environment |
| `BRIGHTDATA_SERP_ZONE` | Aktive Zone für das SERP-Produkt |
| `BRIGHTDATA_UNLOCKER_ZONE` | Aktive Zone für Web Unlocker |
| `BRIGHTDATA_MAX_REQUESTS` | Gemeinsame persistente Höchstzahl; Default 10 |
| `BRIGHTDATA_MAX_COST_USD` | Grenze für geschätzte Kosten; muss gesetzt sein |
| `BRIGHTDATA_ESTIMATED_REQUEST_COST_USD` | Konservativer Wert aus dem tatsächlichen Accounttarif; muss gesetzt sein |
| `BRIGHTDATA_ALLOWED_DOMAINS` | Optional: durch Kommas getrennte erlaubte Quellendomains |
| `RESEARCH_KB_DIR` | Optional: anderer lokaler Speicherpfad |

Es gibt keinen angenommenen Standardpreis. Die USD-Grenze ist nur eine Schätzung
anhand der konfigurierten Stückkosten; sie erzwingt nicht die Abrechnung beim
Anbieter. Tarif und Accountausgabenlimit zusätzlich im Bright-Data-Account prüfen.
Die Request-Anzahl wird tatsächlich im lokalen Ledger durchgesetzt. Ein
fehlgeschlagener oder abgebrochener Versuch bleibt gezählt, weil er bereits
Kosten verursacht haben kann. Es gibt keine automatischen Wiederholungen.

Suche und Abruf verwenden den offiziellen `POST https://api.brightdata.com/request`
mit Bearer-Authentifizierung und einer passenden Produktzone. Suche verlangt
strukturiertes JSON; Abruf verlangt Markdown-Text. Der aktuelle Account muss für
beide Produkte freigeschaltet sein; ein eingelöster Promo-Code beweist das nicht.
[SERP-Referenz](https://docs.brightdata.com/api-reference/rest-api/serp/serp-api),
[Web-Unlocker-Referenz](https://docs.brightdata.com/api-reference/rest-api/unlocker/unlock-website)

Nach Einrichtung der Umgebung:

```sh
.venv/bin/python scripts/brightdata_client.py search 'Drosophila descending neurons flight initiation primary paper'
.venv/bin/python scripts/brightdata_client.py fetch 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/' --title 'Shiu et al. 2024' --dataset-version 'FAFB paper release; verify IDs'
```

Die erste erfolgreiche Suche speichert **Kandidaten**, keine Findings. Der Abruf
speichert einen SHA256-geprüften Textsnapshot und liefert dessen `source_id`.
Agenten müssen Text und Fundstelle prüfen, bevor sie daraus einen Claim erzeugen.
Quellentext wird als externe Daten gekennzeichnet und darf keine Agentenanweisungen
ersetzen. Nur rechtmäßig zugängliche Inhalte abrufen und speichern.

Die Standard-Quellendomains umfassen PMC/PubMed, Nature, GitHub, NeuroMechFly,
FlyWire/Codex, Zenodo, Eon, bioRxiv, eLife und Janelia. Kandidaten anderer Domains
werden nicht gespeichert. Zusätzliche Primärquellendomains können über die
Konfiguration ergänzt werden. Abruf akzeptiert HTTPS ohne Zugangsdaten und nur
den Standardport. Maximal 2 MiB pro Providerantwort; große Connectome-Dateien
werden direkt über das Brain-Downloadskript geladen.

## Omnigent-Funktionstools

Diese importierbaren Python-Funktionen sind die echten Tooladapter:

```text
scripts.brightdata_client.search_literature(query: str, max_results: int = 5) -> dict
scripts.brightdata_client.fetch_source(url: str, title: str = "", dataset_version: str = "unknown", max_characters: int = 20000) -> dict
scripts.kb_store.store_source(source_json: str) -> dict
scripts.kb_store.store_claim(claim_json: str) -> dict
scripts.kb_store.search_knowledge(query: str, collection: str = "claims", limit: int = 20) -> list[dict]
scripts.kb_store.record_experiment(run_json: str) -> dict
```

`store_source` akzeptiert Quellenmetadaten, keine erfundenen Abrufzustände.
`fetch_source` nimmt tatsächlichen Abruf und Snapshot-Speicherung vor. Claim-/Run-
Argumente sind JSON-Strings, damit Omnigent ein kleines stabiles Toolschema erhält.
Die native Registrierung/Policies stehen unter `agents/`.

## Claim-Schema

Beispielschema, **keine tatsächliche wissenschaftliche Aussage**:

```json
{
  "text": "Hier die eng gefasste, tatsächlich belegte Aussage eintragen.",
  "claim_kind": "extraction",
  "source_ids": ["src_ID_AUS_FETCH_SOURCE"],
  "source_location": "Results, Unterabschnitt, Absatz oder Figure-ID",
  "dataset_version": "Die tatsächlich untersuchte Version",
  "neuron_ids": ["IDs ALS STRINGS"],
  "cell_types": [],
  "evidence_type": "optogenetic intervention / model prediction / anatomy",
  "conditions": "Spezies, Entwicklungsstadium, Stimulus und Versuchsbedingungen",
  "limitations": ["Belegte Unsicherheit oder noch unbekannte Validierung"],
  "review_status": "unreviewed",
  "created_by": "evidence_agent"
}
```

Alle gezeigten Felder sind erforderlich. `claim_kind` ist `reported_finding`,
`extraction`, `hypothesis` oder `model_assumption`. `review_status` ist
`unreviewed`, `checked` oder `rejected`. Mindestens eine Neuronen-ID oder ein
Zelltyp wird benötigt. Große FlyWire-IDs bleiben Strings, damit keine numerische
Rundung auftritt. Unbekannte Source-IDs werden abgelehnt. Findings/Extraktionen
benötigen abgerufene Quellen; Metadaten allein reichen nicht. Eine Quelle oder
ein Claim-Eintrag bestätigt die biologische Richtigkeit noch nicht automatisch.
Jeder Claim pinnt den SHA256-Hash der beim Speichern vorliegenden Quellenfassung;
spätere Abrufe erhalten die vorherigen Snapshots in der Quellenhistorie.

## Run-Schema

```json
{
  "run_kind": "neural_simulation",
  "status": "planned",
  "agent": "experiment_agent",
  "model_version": "Commit und Konfiguration",
  "dataset_version": "FAFB v783",
  "source_ids": [],
  "claim_ids": [],
  "parameters": {"stimulus": {}, "seed": null, "time_step_ms": null},
  "result": {}
}
```

Zulässige Arten: `research`, `neural_simulation`, `body_simulation`,
`coupled_simulation`, `fixture`. Status: `planned`, `completed`, `failed`,
`fixture`. Fixtures müssen mit Status `fixture` gekennzeichnet werden. Referenzen
auf Quellen/Claims müssen existieren. Für wissenschaftliche Runs echte Parameter,
Seeds, Adapter-/Controllerversion, Kontrolle und Resultat ergänzen. Ein Record
allein ist kein unabhängiger Nachweis, dass ein Experiment ausgeführt wurde.

## Lokale Speicherung und Grenzen

```text
knowledgebase/
  manifest.json          Speicherformat und Schema-Version
  sources.jsonl          Quellenmanifest einschließlich Abrufstatus/Hash
  claims.jsonl           Aussagen, Hypothesen und Modellannahmen mit Provenienz
  runs.jsonl             deklarierte Run Records mit Parametern/Resultaten
  snapshots/<sha>.txt    tatsächlich abgerufener Quellentext
  cache/<sha>.json       wiederverwendbare erfolgreiche Providerantworten
  brightdata_usage.json  reservierte Versuche, Status, geschätzte Kosten
  .write.lock            Prozessübergreifende Schreibsperre
```

`flock` serialisiert die Schreiber; JSON/JSONL-Dateien werden nach Flush und fsync
atomar ersetzt. Mehrere Agenten können dieselbe kleine KB benutzen. Keine
Semantik-/Vektordatenbank und kein Modelltraining erforderlich. Queries verwenden
eine einfache Suche über die angegebenen Begriffe. Der Store ist für eine kleine
Hackathon-Literaturmenge gedacht. Ein defekter Datensatz/Usage-Ledger wird nicht
still repariert oder gelöscht, sondern muss geprüft werden.

Identische erfolgreich gecachte Bright-Data-Anfragen brauchen keinen weiteren
Provideraufruf. Neue gleichzeitige identische Anfragen können vor der ersten
Antwort mehrfach reserviert werden; jede zählt gegen die gemeinsame Grenze.
Die lokale Cachewiederverwendung wird anhand von Zone, URL und Ausgabeformat
ermittelt. API-Schlüssel werden nicht protokolliert oder gespeichert; bekannte
Schlüsselwerte in Providerantworten werden vor der Speicherung redigiert.

## Offline-Validierung

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_brightdata_client.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_kb_store.py' -v
```

Tests verwenden ausschließlich markierte Provider-/Claim-Fixtures in temporären
Ordnern. Sie prüfen Persistenz, Provenienz, ID-Präzision, unzulässige Quellen,
fehlende Konfiguration, Caching, persistente Request-/Kostengrenzen und
Secret-Redaktion. Das sind keine Live-Verbindungs- oder Forschungsnachweise.

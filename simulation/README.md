# Lokales Fliegengehirn

Das heruntergeladene Modell ist das veröffentlichte **Whole-brain-LIF-Modell von Shiu et al.** mit den im Autorenrepository bereitgestellten **FlyWire FAFB v783**-Tabellen. Es ist ein neuronales Modell; ein virtueller Körper und Flug sind noch nicht angeschlossen.

## Quellen und Dateien

- Autorencode: https://github.com/philshiu/Drosophila_brain_model
- Eingefrorener Commit: `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`.
- Publikation: https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/
- Ursprüngliche Connectome-Daten und Attribution: FlyWire Consortium, *FlyWire Whole-brain Connectome Connectivity Data* (2024), Version 783.0, https://zenodo.org/records/10676866 (CC-BY-4.0).
- Die model-ready Dateien sind die verarbeiteten Tabellen aus dem Shiu-Autorenrepository, keine unveränderte Kopie des gesamten Rohsynapsenarchivs.
- Unveränderter Autorencode und MIT-Lizenz: `simulation/vendor/shiu/`.
- Daten, Downloadquellen, Dateigrößen und SHA-256-Prüfsummen: `data/brain/manifest.json`.

Die Originalkonfiguration des Autorenmodells verwendet v630. Unsere Pfade verwenden ausdrücklich v783; Versionswechsel werden nicht stillschweigend durchgeführt.

## Ausführen

Aus dem Projektordner mit der von der Haupteinrichtung verwalteten Python-Umgebung:

```sh
.venv/bin/python -m simulation.download_brain --verify-only
.venv/bin/python -m simulation.brain validate
.venv/bin/python -m simulation.brain pilot --duration-ms 20 --rate-hz 150 --seed 42
```

Fehlende Dateien lassen sich über `.venv/bin/python -m simulation.download_brain` nachladen. Unerwartete vorhandene Dateien werden nicht überschrieben. Benötigte Pakete: Brian2, NumPy, Pandas, PyArrow und Joblib; zentrale Installation erfolgt im gemeinsamen Projekt-Setup.

Der Pilot verwendet **das vollständige heruntergeladene Netzwerk**, einen Prozess, einen Durchlauf, 0,1 ms Zeitschritt und einen technischen Probe-Stimulus. Dauer ist auf höchstens 200 ms und 32 Targets begrenzt. Standardmäßig wird die erste vorhandene v783-Neuronen-ID stimuliert; das ist keine biologisch ausgewählte Flug- oder Bewegungsfunktion. Eigene IDs über `--neuron-id` müssen in genau dieser v783-Tabelle vorhanden sein.

Der Runner bewahrt den Autorencode unverändert. Falls dessen Reset-Zeile `w=0` auf eine im Neuronenmodell nicht deklarierte Variable verweist, wird diese Zuweisung im Runtime-Parameter entfernt und in `compatibility_adjustments` protokolliert. Das ist eine technische Anpassung für unsere Laufumgebung.

## Ergebnisse

Jeder Aufruf schreibt in einen neuen Ordner unter `data/runs/brain-pilot-.../`:

- `run.json`: Versionen, Stimulus, Seed, Dauer, vollständige Netzwerkgröße, Laufzeit, Erfolg/Fehler und Grenzen.
- `spikes.parquet`: tatsächliche Spike-Zeitpunkte und Neuronen-IDs.
- `spikes_preview.json`: höchstens die ersten 1.000 Events für einen kleinen Viewer; ausdrücklich als begrenzte Vorschau gekennzeichnet.

FlyWire IDs in browserfähigen Exporten sind **Strings**, weil diese 64-Bit-Werte außerhalb des sicheren JavaScript-Ganzzahlbereichs liegen.

Ein erfolgreicher kurzer Pilot belegt, dass das neuronale Netzwerk berechenbar ist. Er belegt weder Flug noch Körperbewegung oder eine neu entdeckte biologische Funktion. Ein späteres Experiment muss ein begründetes Target, Kontrollbedingungen, ausreichende Dauer/Wiederholungen und getrennte neuronale sowie Körpermessgrößen festlegen.

## Tatsächlich geprüft am 4. Oktober 2026

- Alle neun heruntergeladenen Dateien stimmen mit den gespeicherten SHA-256-Prüfsummen überein.
- Schema, eindeutige IDs, Indexgrenzen und endliche Gewichte validiert: **138.639 Neuronen, 15.091.983 neuron-pair-Zeilen**.
- Echter Whole-network-Pilot: 20 ms, 150 Hz, Seed 42, ein technisches Target; zwei Spike-Events in einem Neuron. Laufzeit der Modellkonstruktion und Berechnung: **2,494 Sekunden**.
- Ergebnis: `data/runs/brain-pilot-20261003T230750Z-1204ca/run.json`.
- Technischer Stimulus-Aus-Test mit identischem Seed, Target und Dauer: 0 Hz erzeugte null Spike-Events, Laufzeit 2,246 Sekunden, maximaler Prozessspeicher ca. 1,014 GiB. Ergebnis: `data/runs/brain-pilot-20261003T230843Z-6f1ee2/run.json`.
- Der Vergleich steht in `data/runs/technical_setup_check.json` und ist ausdrücklich eine nachträgliche Dokumentation von Setupchecks, kein vorregistriertes biologisches Experiment und kein Ersatz für den wissenschaftlichen C3-Discovery-Test.
- Laufumgebung: CPython 3.12.14, Brian2 2.9.0, NumPy 1.26.4, Pandas 2.2.3, PyArrow 25.0.1. Das ist ein geprüfter kurzer Lauf mit neueren Paketversionen, keine vollständige Reproduktion aller publizierten Experimente.
- Zur Speicherreduktion liest der Wrapper nur die drei vom Modell verwendeten Connectivity-Spalten; alle Netzwerkzeilen bleiben enthalten. Auch diese Anpassung wird protokolliert.

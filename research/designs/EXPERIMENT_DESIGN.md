# Fixierter DNg02-Inputtest

Die Frage lautet: **Können acht vorab anhand der Konnektivität ausgewählte rechte
Inputs im vollständigen v783-LIF-Modell Aktivität in den flugbezogenen DNg02-
Zellen erzeugen, und hängt die Antwort von den Ausgangsverbindungen der Inputs ab?**

Die Hypothese ist eine Vorhersage des Modells. Sie behauptet keine bereits
entdeckte biologische Funktion dieser vorgeschalteten Zellen.

`dng02-input-v1.json` wurde am **4. Oktober 2026, 00:17:05 UTC / 02:17:05 Europe/Berlin**
gespeichert und gehasht, vor dem ersten neuronalen Lauf dieses Designs.
Die danebenliegende `.sha256`-Datei versiegelt das Design. Der Runner prüft
zusätzlich Targetdatei und Datensatz-Hashes. Veränderungen führen zum Fehler
und dürfen nicht stillschweigend als ursprünglicher Test weiterlaufen.

## Zwei Tests und eine ergebnisabhängige Entscheidung

| Test | Bedingungen | Warum dieser Test? |
|---|---|---|
| A: Antwortnachweis | 150-Hz-Input gegen 0-Hz-Sham | Zuerst prüfen, ob nicht direkt stimulierte DNg02-Zellen überhaupt reagieren. |
| B: Ausgangsverbindungen | derselbe 150-Hz-Input mit unverändertem Graph gegen auf null gesetzte Ausgangsgewichte der acht Inputs | Danach prüfen, ob die Antwort durch den modellierten Graph vermittelt wird. |

Vorab gewählt ist **A**. Sind die gepaarten DNg02-Ratendifferenzen in allen drei
Seeds größer als null, empfiehlt die festgelegte Regel **B**. Andernfalls folgt
eine separat vorab registrierte direkte DNg02-Kalibrierung. Ein Nullresultat
wird erhalten; Inputs und Parameter werden nicht nach dem Ergebnis umgebaut.

Test B verlangt eine Senkung um mindestens **80 % in jedem Seed** mit einer
nichtnull Antwort in der unveränderten Bedingung. Die Ausgangstrennung setzt
ausschließlich ausgehende Gewichte der acht Inputzellen auf null. Eingänge und
alle übrigen Verbindungen bleiben numerisch erhalten. Sie entspricht einer
**modellierten Ausgangstrennung**, nicht der Behauptung einer realistischen
biologischen Hemmung mit einer bestimmten experimentellen Methode.

## Fixierte Größen

- Voller installierter Graph: 138.639 Neuronen und 15.091.983 Verbindungszeilen.
- Zeitraum: **200 ms**; Zeitschritt **0,1 ms**; **ein Prozess**.
- Hauptstimulus: acht feste vorgeschaltete IDs, **150 Hz unabhängiger Poissoninput**.
- Seeds: **42, 43, 44**, in identischer Reihenfolge pro Bedingung.
- Readout: alle **25** fixierten DNg02-IDs, einschließlich stiller Zellen im Nenner.
- Primärgröße: mittlere Spikes pro Zelle pro Sekunde über das gesamte 200-ms-Fenster.
- Ergänzend: Raten links/rechts, aktive Readoutzellen, Einzelzellcounts,
  aktive nicht direkt stimulierte Neuronen und tatsächliche Rechenzeit.

Die Sham-Bedingung erzeugt dieselben Inputobjekte mit Rate null. Dadurch bleiben
insbesondere die vom Autorcode angepassten Refraktärzeiten der Inputzellen
vergleichbar. Modellkonstanten sind vollständig in der JSON-Datei dokumentiert.
Der Autorcode bleibt unverändert; im Wrapper wird die ungültige Resetzuweisung
`w=0` entfernt, da `w` in dessen Neurongleichungen nicht deklariert ist.

Es gibt beschreibende Werte über drei simulierte Seeds, keine p-Werte und keine
Übertragung auf eine Population realer Tiere. Die 0-Hz-Shamantwort ist im Modell
mit anfänglich stillen Zellen erwartbar. Ein positiver Ausgangstest weist damit
eine gezielte Modellantwort nach, keine generell realistische Gehirnaktivität.

## Ausführung und Herkunft

```bash
.venv/bin/python -m simulation.experiment --test A --execution-context manual
.venv/bin/python -m simulation.experiment --test B --execution-context manual
```

Das gleiche Interface wird vom echten Omnigent-Experimenttool aufgerufen:
`simulation.experiment.run_experiment(test="A", execution_context="...")`.
Ein Textfeld `execution_context` beweist allein keine Orchestrierung. Dafür
müssen tatsächliche Omnigent-Sessiondaten und Toolaufrufe vorliegen. Die ersten
Machbarkeitsläufe sind ausdrücklich als unabhängig vor Omnigent markiert.

Jeder Lauf erhält `run.json`, vollständige Spike-Parquetdaten, eine begrenzte
Spike-Vorschau, `readout.json` und **vollständige DNg02-Events** in
`readout_spikes.json`. Letztere erlauben dem Körpermodul eine Datenübergabe
ohne zusätzliche pandas-/Arrow-Abhängigkeiten. Gepaarte Vergleiche und die
nächste Entscheidung werden in `data/experiments/comparison-dng02-*.json`
gespeichert.

Neuronale Aktivität, ein separat versiegelter Motoradapter, die echte
Körperphysik und die Darstellung behalten eigene Messgrößen und Grenzen.
Der neuronale Test verfügt über keinen sensorischen Rückkanal.

# DNg02: belegte Flugrelevanz und überprüfte v783-Identitäten

Stand: 4. Oktober 2026. Die Auswahl bleibt im Flugkontext. Das Experiment
untersucht zunächst eine neuronale Vorhersage; die langfristige Flugvision
ist damit noch nicht erreicht.

**Belegter Einstieg:** Namiki et al. zeigen bei bereits fliegenden, fixierten
Fruchtfliegen einen Zusammenhang zwischen DNg02-Populationsaktivierung und
Flügelschlagamplitude. Die Bildgebung untersucht auch unterschiedliche Aktivität
auf beiden Seiten bei visuellen Reizen. Das ist eine passende Funktionsquelle
für einen flugbezogenen neuronalen Ausgang.

Quelle: [Namiki et al. 2022, Current Biology](https://pmc.ncbi.nlm.nih.gov/articles/PMC9206711/),
DOI [10.1016/j.cub.2022.01.008](https://doi.org/10.1016/j.cub.2022.01.008),
Summary sowie Ergebnisse/Figuren 3 und 4. Die Versuche begründen keine Aussage,
dass unsere Stimulation einen ruhenden virtuellen Körper autonom abheben lässt.

## Identitäten statt Versionsmischung

Die [offiziellen FlyWire-Annotationen](https://github.com/flyconnectome/flywire_annotations/tree/v2.1.0)
von Schlegel et al. werden auf Release **v2.1.0** und Commit
`ebd66db2596fcc39c6950fb54ea3efa00f7fe8a0` fixiert. Die vollständige heruntergeladene
TSV-Datei hat SHA-256
`30be6c73975a70c56d930e27911f36455d3886e15abf383b78edd2a5d679e0b6`.

Die Auswahl `cell_type` beginnt mit `DNg02` ergibt **25 Zellen**, davon
**13 links und 12 rechts**. Alle 25 Root-IDs sind in der tatsächlich installierten
`Completeness_783.csv` mit 138.639 Neuronen vorhanden. `dng02_targets.json` enthält
jede ID als String, die Annotation, die Seite und den zugehörigen Brian2-Index.
Es werden weder v630-IDs übernommen noch BANC-/VNC-IDs in den Graph eingesetzt.

Die Untertypen `DNg02_a` bis `DNg02_g` werden für diesen begrenzten Test gemeinsam
ausgelesen. Diese Auswahl wird nicht mit der gesamten Population eines
bestimmten genetischen Treibers aus dem biologischen Experiment gleichgesetzt.
Einzelne Transmittervorhersagen in der Annotation unterscheiden sich; die
numerischen Vorzeichen stammen weiterhin aus der fixierten, autorenseitig
verarbeiteten Konnektivität.

## Was stimuliert wird

DNg02 wird in den Haupttests **nicht direkt stimuliert**. Stattdessen werden
acht rechte vorgeschaltete Zellen ausgewählt, ausschließlich anhand der
Konnektivität vor dem neuronalen Lauf:

1. Positive `Excitatory x Connectivity`-Gewichte auf die 25 DNg02-Zellen addieren.
2. Auf offiziell rechts annotierte Zellen außerhalb des Readouts beschränken.
3. Absteigend nach dieser Summe sortieren, bei Gleichstand aufsteigend nach ID.
4. Die ersten acht IDs fixieren.

Diese Zellen heißen bewusst **graphgewählte vorgeschaltete Inputs**. Sie werden
nicht als bereits bestätigte visuelle Sinnesneuronen ausgegeben. Sieben haben
in dieser Annotation keinen spezifischen Zelltypnamen; eine heißt `CB0630`.
Die genaue Rangfolge und Gewichte stehen in `dng02_targets.json`.

## Modellgrenzen

[Shiu et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/)
beschreiben und prüfen ein vereinfachtes LIF-Modell insbesondere für Feeding
und antennales Grooming. Der veröffentlichte Brain-Graph enthält keinen
vollständigen flugsteuernden ventralen Nervenstrang. Unsere DNg02-Vorhersage
benötigt deshalb eigene biologische Validierung und einen offen dokumentierten
Motoradapter. Absolute Modellraten sind keine kalibrierten biologischen Raten.

## Lokale Knowledgebase

`import_dng02_evidence.py` speichert tatsächlich heruntergeladene Namiki-/Shiu-
HTML-Fassungen, 33 tatsächliche Zeilen der fixierten Annotation und den gepinnten
Autorcode in der Knowledgebase außerhalb von iCloud. Bei der Annotation ist
der Ausschnitt ausdrücklich als solcher gekennzeichnet; der Hash der
vollständigen Originaldatei bleibt erhalten. Die öffentlichen Projektdateien
enthalten nur kleine abgeleitete Identitätsdaten, Quellenverweise und den
Importbeleg `kb_import_receipt.json`.

Vier Claims unterscheiden biologische Literaturbefunde, geprüfte Identitäten,
Modellgrenzen und die agentengenerierte Hypothese. Suchtreffer und Metadaten
allein werden nicht als abgerufene Evidenz ausgegeben. Die Quellen wurden direkt
von Primärquellen abgerufen; **BrightData war an diesem Abruf nicht beteiligt**.

Reproduzierbarer Import nach dem Download der drei öffentlichen Quelldateien:

```bash
.venv/bin/python -m research.import_dng02_evidence \
  --annotations-tsv /tmp/flywire-neuron-annotations-v2.1.0.tsv \
  --namiki-html /tmp/namiki-dng02-paper.html \
  --shiu-html /tmp/shiu-brain-model-paper.html
```

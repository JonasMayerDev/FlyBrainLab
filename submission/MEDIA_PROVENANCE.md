# Medienherkunft und Aufnahmequalität

Die vorbereiteten Demo-Videos bestehen aus **echten öffentlichen Browseraufnahmen und tatsächlichen Projektartefakten mit englischen Texteinblendungen**. Sie haben derzeit keine Tonspur. Eine menschliche Stimme kann mit den deutschen oder englischen Skripten aus `VIDEO_SCRIPTS.md` ergänzt werden; zuvor die tatsächliche Laufzeit laut messen. Es wurde keine synthetische Stimme erzeugt.

## Produktvideo

- Quelle: `frontend/output/playwright/public-product-clean.webm`, im echten Browser auf [der öffentlichen Pages-Seite](https://valleebo.github.io/FlyBrainLab/) aufgenommen.
- Ablauf: neuronaler Drive-Replay, Sham, Ausgangstrennung, Body-Replay, kontrollierter Vergleich, Quellen und wissenschaftliche Grenzen.
- Der ursprüngliche Screenrecord ist etwa 45 Sekunden lang. Das letzte tatsächlich aufgenommene Bild wird für die abschließende Texteinblendung gehalten; das fertige Produktvideo dauert 50 Sekunden. Es werden keine zusätzlichen Klicks oder Körperzustände erfunden.
- Die neuronalen und gekoppelten Runs im ursprünglichen öffentlichen Screenrecord sind ausdrücklich die **unabhängigen Machbarkeitsläufe vor Omnigent**. Der native Omnigent-Nachweis ist ein eigenes Artefakt und wird in den Technik-/C3-Videos gezeigt.

## Technik- und C3-Video

`render_demo_videos.py` liest den geprüften nativen Omnigent-Trace und die verknüpften neuen Vergleichsdateien. Ohne verifiziertes Rollen-/Toolprotokoll und Test-A-Receipt verweigert es eine Behauptung des vollständigen nativen Workflows. Test B kann nur als ausgeführt gezeigt werden, wenn auch dessen native Receipt und neue Vergleichsdatei vorliegen. Andernfalls wird B klar als entworfener nächster Test angezeigt.

Die Videos sind ein **Artefakt-Walkthrough mit Karten und realen Viewer-Screenshots**, kein vorgetäuschter Live-LLM-Aufruf. Die native Rollenaktivität ist in den verlinkten Run Records/Trace prüfbar. Die technische Body-Vorprüfung behält ihre eigenständige Herkunft. Der Renderer erstellt keine neue Simulation.

## Reproduzierbar bauen

Pillow ist im gebündelten primären Python verfügbar. Den konkreten Runtime-Pfad bei Bedarf mit `load_workspace_dependencies` ermitteln; kein neues Mediaframework installieren. FFmpeg ist bereits isoliert in `.runtime/media-venv` vorhanden. Beispiel mit tatsächlich vorhandenen Trace-/Vergleichspfaden:

```sh
/Users/valentin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  submission/render_demo_videos.py \
  --recording frontend/output/playwright/public-product-clean.webm \
  --trace PATH_TO_VERIFIED_NATIVE_TRACE.json \
  --test-a PATH_TO_NEW_NATIVE_TEST_A_COMPARISON.json \
  --test-b PATH_TO_NEW_NATIVE_TEST_B_COMPARISON.json
```

`--test-b` weglassen, wenn B im nativen Loop erst die nächste Entscheidung ist. Die Platzhalter sind Pfade, keine behaupteten bereits vorhandenen Dateien. Das Ergebnis erhält `exports/video_source_manifest.json` mit SHA-256 der Quellen und Medien. Anschließend:

```sh
.venv/bin/python scripts/validate_submission_assets.py --output submission/exports/asset_validation.json
```

Vor der Einreichung müssen Menschen alle Videos vollständig ansehen. Der Validator kann Aussagequalität, Lesbarkeit, Identität des Teams, Uploadverarbeitung und echte Abgabebestätigungen nicht nachweisen. Ein echtes Teamfoto und eine echte Teamvorstellung werden bewusst nicht automatisiert erfunden.

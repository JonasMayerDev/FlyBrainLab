# Medienherkunft und Aufnahmequalität

Die vorbereiteten Demo-Videos bestehen aus **echten öffentlichen Browseraufnahmen und tatsächlichen Projektartefakten mit englischen Texteinblendungen**. Sie haben derzeit keine Tonspur. Eine menschliche Stimme kann mit den deutschen oder englischen Skripten aus `VIDEO_SCRIPTS.md` ergänzt werden; zuvor die tatsächliche Laufzeit laut messen. Es wurde keine synthetische Stimme erzeugt.

## Produktvideo

- Quelle: `frontend/output/playwright/public-product-final.webm`, anonym im echten Browser auf [der öffentlichen Pages-Seite](https://valleebo.github.io/FlyBrainLab/) aufgenommen; Quellcommit `e7ae4a4f3e80bfbd8f739957dcb08880e3d91545`.
- Ablauf: exakt neue native A42-Stimulation und Sham, native B42-Ausgangstrennung, neue v2-Körperzustände, 200-ms-Vergleich, A-Trace, A→B-Verknüpfung, Quellen und Grenzen.
- Die vollständige Aufnahmedatei enthält 99,20 Sekunden mit Vor-/Nachlauf. Nach visueller Prüfung und Gegencheck des Viewer-Agenten verwendet der Export den tatsächlichen Ausschnitt **6–61 Sekunden**, ohne erfundene Klicks oder Simulationszustände. Der 55-s-Export entfernt nur den leeren Aufnahmerand unter der oberen 812-Pixel-Inhaltsfläche. Die abschließende Übersicht stammt aus der realen Aufnahme.
- Der mittlere DNg02-Output enthält alle 25 Readoutzellen einschließlich stiller Zellen. B liefert null DNg02-Output, aber im gezeigten Seed bleiben 222 echte Spike-Ereignisse erhalten; null Whole-network-Aktivität wird nicht behauptet.
- Die zuvor aufgenommene `public-product-clean.webm` zeigte unabhängige Vorläufe/v1. Sie wird nicht nachträglich als native A/B/v2-Aufnahme umetikettiert.

## Teamvorstellung als prüfbarer Entwurf

`team_intro.mp4` ist ein 46-sekündiger Textentwurf ohne Personenbilder oder Tonspur. Er nennt vier Menschen im Team, den Munich Hub, den bestätigten Track, Projektzweck und Arbeitsbereiche. Die Bereiche sind keine individuellen Rollenzuweisungen. Namen, tatsächliche persönliche Beiträge und persönliche Motivation bleiben offen und werden nicht erfunden. Die Teamprüfung kann diese Inhalte ergänzen; das echte Pflicht-Teamfoto bleibt ein separates fehlendes Medium. Der Medienvalidator prüft Format und Laufzeit, bestätigt aber keinen vollständigen persönlichen Teaminhalt.

## Technik- und C3-Video

`render_demo_videos.py` liest den geprüften nativen Omnigent-Trace und die verknüpften neuen Vergleichsdateien. Ohne verifiziertes Rollen-/Toolprotokoll und Test-A-Receipt verweigert es eine Behauptung des vollständigen nativen Workflows. Die finale A/B-Fassung verwendet beide streng verifizierten nativen Traces, die jeweiligen neuen Receipts und Vergleichsdateien. B wurde in einer zweiten nativen Sitzung ausgeführt. Deren Audit belegt das Lesen der gespeicherten A-Entscheidung vor B-Planung und revalidiert As archivierte Artefakte und Rohdaten unabhängig. Ohne gültigen B-Trace wird eine B-Ausführungsbehauptung verweigert.

Die Videos sind ein **Artefakt-Walkthrough mit Karten und realen Viewer-Screenshots**, kein vorgetäuschter Live-LLM-Aufruf. Die native Rollenaktivität ist in den verlinkten Run Records/Trace prüfbar. Die v2-Körperkopplung liest sechs gemessene 200-ms-Läufe mit der veröffentlichten, vortrainierten Autorenpolicy. Sie verwendet neue native A-Spikes, wurde numerisch aber separat nach dem Omnigent-Gehirnexperiment ausgeführt. Stabilisierung stammt von der bestehenden Policy; deren Körperfeedback ist kein sensorischer Rückkanal in das Connectome. Der Renderer erstellt keine neue Simulation. Die exakten Trace-Fassungen am Renderzeitpunkt werden in `exports/native_trace_A_at_render.json` und `exports/native_trace_B_at_render.json` erhalten, falls eine spätere Fortsetzung die aktuellen Traces erweitert. Beide nativen Sitzungen bleiben getrennt erhalten und sind durch die geprüfte A→B-Referenz verbunden.

## Reproduzierbar bauen

Pillow ist im gebündelten primären Python verfügbar. Den konkreten Runtime-Pfad bei Bedarf mit `load_workspace_dependencies` ermitteln; kein neues Mediaframework installieren. FFmpeg ist bereits isoliert in `.runtime/media-venv` vorhanden. Beispiel mit tatsächlich vorhandenen Trace-/Vergleichspfaden:

```sh
/Users/valentin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  submission/render_demo_videos.py \
  --recording frontend/output/playwright/public-product-final.webm \
  --recording-start 6 --recording-crop-height 812 --product-v2 \
  --public-commit e7ae4a4f3e80bfbd8f739957dcb08880e3d91545 \
  --trace data/discovery/native-trace.json \
  --trace-b data/discovery/native-trace-b.json \
  --test-a data/experiments/comparison-dng02-20261004T005438Z-0aa143.json \
  --test-b data/experiments/comparison-dng02-20261004T011205Z-88d84a.json
```

Für eine A-only-Fassung `--test-b` und `--trace-b` weglassen. `--product-v2` nur verwenden, wenn der tatsächliche Screenrecord die neue native A-Auswahl mit v2-200-ms-Körperzuständen zeigt; eine alte v1-Aufnahme wird durch neue Einblendungen nicht zu v2. Das Ergebnis erhält `exports/video_source_manifest.json` mit SHA-256 der Quellen und Medien. Anschließend:

```sh
.venv/bin/python scripts/validate_submission_assets.py \
  --output submission/exports/asset_validation.json \
  --public-output submission/exports/asset_validation_public.json
```

Vor der Einreichung müssen Menschen alle Videos vollständig ansehen. Der Validator kann Aussagequalität, Lesbarkeit, Identität des Teams, Uploadverarbeitung und echte Abgabebestätigungen nicht nachweisen. Ein echtes Teamfoto und eine echte Teamvorstellung werden bewusst nicht automatisiert erfunden.

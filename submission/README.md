# Abgabe am 4. Oktober 2026

Diese Mappe bereitet Issue [#10](https://github.com/JonasMayerDev/FlyBrainLab/issues/10) vor. Sie ist **kein Beleg für eine abgeschlossene Einreichung**. HackOS und das anschließend verlinkte Google Form müssen beide abgeschickt werden; die beiden Bestätigungen gehören in `exports/`.

**Tatsächlich vorbereitet:** Teamvorstellungsentwurf (46 s), Produktvideo (55 s), Technikvideo (55 s) und C3-Demo (118 s), jeweils MP4/H.264/1080p mit englischen Texteinblendungen, ohne Tonspur. Alle vier wurden vollständig decodiert, auf Grenzen geprüft und visuell kontrolliert. Die Teamvorstellung ist ausdrücklich ein Textentwurf aus bestätigten Projektfakten und Arbeitsbereichen; persönliche Namen, Beiträge und Motive bleiben offen. Technik-/C3-Video zeigen die streng geprüften nativen Omnigent-A- und B-Durchläufe in zwei nachweislich verbundenen Sitzungen; A wählt ergebnisabhängig B, dessen Ausgangstrennung die DNg02-Modellantwort in allen drei Seeds entfernt. Die neuen Technik-/C3-Karten zeigen die v2-Kopplung: sechs echte 200-ms-Körperläufe mit vortrainierter Autorenpolicy, gemessenen physikalischen Unterschieden und offen benannten Motorannahmen. Das finale Produktvideo verwendet die echte öffentliche Aufnahme des Commits e7ae4a4 mit den neuen nativen A/B-Runs und der v2-Kopplung; die früheren v1-Dateien werden nicht durch neue Einblendungen umgedeutet. Finale menschliche Sichtung bleibt erforderlich.

| Datei in `exports/` | Länge | Größe | Status |
|---|---:|---:|---|
| `product_demo.mp4` | 55,000 s | ca. 2,15 MB | echter finaler öffentlicher A/B/v2-Screenrecord mit erklärenden Einblendungen |
| `technical_walkthrough.mp4` | 55,000 s | ca. 0,92 MB | geprüfte native A/B-Traces, v2-Kopplung und technische Grenzen |
| `c3_demo.mp4` | 118,000 s | ca. 1,63 MB | vollständige verbundene A/B-Schleifen, zwei Testdesigns, v2-Körperdaten, nächste Entscheidung |
| `team_photo.jpg` / anderes erlaubtes Bildformat | — | — | tatsächliches Teamfoto fehlt |
| `team_intro.mp4` | 46,000 s | ca. 0,51 MB | Textentwurf mit bestätigter Teamgröße, Hub, Zweck und Arbeitsbereichen; persönliche Inhalte zur Prüfung offen |

Exakte Hashes und Quellpfade stehen in `exports/video_source_manifest.json`; `exports/asset_validation.json` meldet das fehlende Teamfoto bewusst als Fehler. Der Teamvorstellungsentwurf braucht menschliche Inhaltsprüfung; bestandene Mediengrenzen ersetzen diese nicht. A und B besitzen eigene neue numerische Receipts und geprüfte Run Records. Der B-Trace belegt das erneute Lesen von As ergebnisabhängiger Entscheidung vor der B-Planung und validiert As archivierte Quellen und Rohdaten unabhängig. Die vorherigen unabhängigen Vorläufe behalten ihre eigene Provenienz.

**Öffentlich verfügbar:** [GitHub-Release mit vier Videos, SRTs, Prüfbericht und ZIP-Paket](https://github.com/JonasMayerDev/FlyBrainLab/releases/tag/demo-2026-10-04). Der Release ist keine HackOS-/Google-Form-Einreichung. Die lokale Version liegt in `exports/`; Code und öffentliche Medienprüfberichte sind ebenfalls versioniert.

## Dateien und Reihenfolge

1. [Sprechertexte und Storyboards](VIDEO_SCRIPTS.md): Deutsch und Englisch; drei Plattformvideos mit Ziel 50–55 Sekunden und eine zusätzliche C3-Demo mit Ziel 115–120 Sekunden. Namen sind bei der Teamvorstellung ausdrücklich offen.
2. [Einreichungstexte](FORM_TEXT.md): wissenschaftlich begrenzte Beschreibung zum Einfügen; aktuelle Provenienz vor Versand kontrollieren.
3. [Checkliste für 09:00](MORNING_CHECKLIST.md): die wenigen menschlichen Aufgaben und Abnahmechecks.
4. [Asset-Vertrag](asset_manifest.json): Dateinamen und die aus dem bereitgestellten Screenshot übernommenen Grenzen.
5. `exports/`: lokale Bilder, Videos und Prüfberichte; große Medien werden nicht in Git übernommen.

Öffentlicher Viewer: [valleebo.github.io/FlyBrainLab](https://valleebo.github.io/FlyBrainLab/). Dieser Mirror wurde anonym im echten Browser mit Desktop- und mobiler Ansichtsbreite geprüft; das kanonische Code-Repository bleibt `JonasMayerDev/FlyBrainLab`. Der Gegencheck auf einem tatsächlichen zweiten Gerät bleibt in der Morgencheckliste. Die Oberfläche spielt aufgezeichnete Runs ab.

## Medien prüfen

Der Validator braucht einen lokalen FFmpeg-Binary. Er findet zuerst `FFMPEG_BINARY`, dann `ffmpeg` im PATH und danach das installierte `imageio_ffmpeg` in `.runtime/media-venv`. Es wird nichts heruntergeladen. `--public-output` erstellt zusätzlich eine teilbare Berichtsfassung ohne lokale absolute Pfade; der vollständige lokale Bericht bleibt separat. Python kann die Standardbibliothek verwenden; zusätzliche Python-Pakete sind für die Prüfung nicht erforderlich.

```sh
.venv/bin/python scripts/validate_submission_assets.py \
  --output submission/exports/asset_validation.json \
  --public-output submission/exports/asset_validation_public.json
```

Abweichende Dateinamen sind möglich:

```sh
.venv/bin/python scripts/validate_submission_assets.py \
  --team-photo /absolute/path/team.webp \
  --team-intro /absolute/path/team-intro.mov \
  --product-demo /absolute/path/product-demo.mp4 \
  --technical-walkthrough /absolute/path/technical-walkthrough.mp4 \
  --c3-demo /absolute/path/c3-demo.mp4
```

Geprüft werden Existenz, erlaubte Endung und Container/Dateisignatur, Größe, tatsächliche MP4/MOV-Laufzeit, vollständige Video-/Audio-Decodierung bzw. ein decodierbares Bild und SHA-256. Ein lokaler Decode dauert bei unseren kleinen Videos wenige Sekunden; nach 60 Sekunden wird ein unvollständiger Check abgebrochen und nicht als bestanden gewertet. Der Bericht prüft **nicht** die Aussagequalität, die echte Teamidentität, Tonverständlichkeit, Uploadverarbeitung, fremden Gerätezugriff oder eine Einreichungsbestätigung. Die drei Plattformvideos dürfen maximal 60 Sekunden/1 GB haben; das Foto maximal 10 MB. Für die zusätzliche C3-Demo setzen wir ein Planungsziel von maximal 120 Sekunden; der Brief fordert zwei Minuten, der konkrete Uploadort ist noch zu klären.

## Offene menschliche Liefergegenstände

- Ein tatsächliches Foto der vier Teammitglieder. Es wird kein Bild erfunden oder durch KI ersetzt.
- Namen, tatsächliche Beiträge und persönliche Motivation bestätigen. Der 46-s-Entwurf für die Teamvorstellung verwendet ausschließlich bestätigte Projektfakten und Arbeitsbereiche ohne individuelle Zuordnung; nach Prüfung bei Bedarf um echte Stimme oder Personenaufnahme ergänzen.
- Produkt-, Technik- und C3-Video anschauen und gegebenenfalls eine menschliche Stimme aufnehmen. Vorbereitete Videos mit Texteinblendungen sind als solche gekennzeichnet; synthetische Stimmen müssten ausdrücklich gekennzeichnet werden.
- Im HackOS-Konto öffentliche URL/Repo, Foto und die drei passenden Videos hochladen. Nach Verarbeitung alle Wiedergaben prüfen.
- Uploadort der zusätzlichen zweiminütigen C3-Demo im Google Form/bei den Organisatoren klären; danach HackOS und Google Form wirklich absenden und Bestätigungen sichern.

Internes Ziel: **14:30 Uhr Europe/Berlin**. Offizielle Deadline: **15:00 Uhr**. Die technische Nachfrist bis 15:15 ist kein eingeplantes Arbeitsbudget und nicht für das Google Form bestätigt.

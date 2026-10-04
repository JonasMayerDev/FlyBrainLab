# Abgabe am 4. Oktober 2026

Diese Mappe bereitet Issue [#10](https://github.com/JonasMayerDev/FlyBrainLab/issues/10) vor. Sie ist **kein Beleg für eine abgeschlossene Einreichung**. HackOS und das anschließend verlinkte Google Form müssen beide abgeschickt werden; die beiden Bestätigungen gehören in `exports/`.

## Dateien und Reihenfolge

1. [Sprechertexte und Storyboards](VIDEO_SCRIPTS.md): Deutsch und Englisch; drei Plattformvideos mit Ziel 50–55 Sekunden und eine zusätzliche C3-Demo mit Ziel 115–120 Sekunden. Namen sind bei der Teamvorstellung ausdrücklich offen.
2. [Einreichungstexte](FORM_TEXT.md): wissenschaftlich begrenzte Beschreibung zum Einfügen; aktuelle Provenienz vor Versand kontrollieren.
3. [Checkliste für 09:00](MORNING_CHECKLIST.md): die wenigen menschlichen Aufgaben und Abnahmechecks.
4. [Asset-Vertrag](asset_manifest.json): Dateinamen und die aus dem bereitgestellten Screenshot übernommenen Grenzen.
5. `exports/`: lokale Bilder, Videos und Prüfberichte; große Medien werden nicht in Git übernommen.

Öffentlicher Viewer: [valleebo.github.io/FlyBrainLab](https://valleebo.github.io/FlyBrainLab/). Dieser Mirror wurde anonym im echten Browser auf Desktop und mobil geprüft; das kanonische Code-Repository bleibt `JonasMayerDev/FlyBrainLab`. Die Oberfläche spielt aufgezeichnete Runs ab.

## Medien prüfen

Der Validator braucht einen lokalen FFmpeg-Binary. Er findet zuerst `FFMPEG_BINARY`, dann `ffmpeg` im PATH und danach das installierte `imageio_ffmpeg` in `.runtime/media-venv`. Es wird nichts heruntergeladen. Python kann die Standardbibliothek verwenden; zusätzliche Python-Pakete sind für die Prüfung nicht erforderlich.

```sh
.venv/bin/python scripts/validate_submission_assets.py --output submission/exports/asset_validation.json
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

Geprüft werden Existenz, erlaubte Endung und Container/Dateisignatur, Größe, tatsächliche MP4/MOV-Laufzeit, ein decodierbarer Videostream bzw. ein decodierbares Bild und SHA-256. Der Bericht prüft **nicht** die Aussagequalität, die echte Teamidentität, Tonverständlichkeit, Uploadverarbeitung, fremden Gerätezugriff oder eine Einreichungsbestätigung. Die drei Plattformvideos dürfen maximal 60 Sekunden/1 GB haben; das Foto maximal 10 MB. Für die zusätzliche C3-Demo setzen wir ein Planungsziel von maximal 120 Sekunden; der Brief fordert zwei Minuten, der konkrete Uploadort ist noch zu klären.

## Offene menschliche Liefergegenstände

- Ein tatsächliches Foto der vier Teammitglieder. Es wird kein Bild erfunden oder durch KI ersetzt.
- Namen und bestätigte Aufgaben der vier Personen; eine echte Teamvorstellung aufnehmen.
- Produkt-, Technik- und C3-Video anschauen und gegebenenfalls eine menschliche Stimme aufnehmen. Vorbereitete Videos mit Texteinblendungen sind als solche gekennzeichnet; synthetische Stimmen müssten ausdrücklich gekennzeichnet werden.
- Im HackOS-Konto öffentliche URL/Repo, Foto und die drei passenden Videos hochladen. Nach Verarbeitung alle Wiedergaben prüfen.
- Uploadort der zusätzlichen zweiminütigen C3-Demo im Google Form/bei den Organisatoren klären; danach HackOS und Google Form wirklich absenden und Bestätigungen sichern.

Internes Ziel: **14:30 Uhr Europe/Berlin**. Offizielle Deadline: **15:00 Uhr**. Die technische Nachfrist bis 15:15 ist kein eingeplantes Arbeitsbudget und nicht für das Google Form bestätigt.

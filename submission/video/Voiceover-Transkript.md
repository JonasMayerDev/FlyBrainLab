# Voiceover für FlyBrainLab_Film_final_v2.mp4 (54,5 s, ohne LC17-Szene)

**Sprache:** Englisch, ruhig und warm, Dokumentar-Stil. Etwa 2,4 Wörter pro Sekunde. Jeder Satz passt in seine Szene und lässt am Ende kurz Luft.

## A) Einzelne Clips (empfohlen: exakt synchron)
In ElevenLabs jeden Abschnitt einzeln erzeugen und als MP3 speichern (`vo01.mp3` … `vo09.mp3`). In Clipchamp an der angegebenen Startzeit platzieren, oder Claude legt sie mit ffmpeg exakt an die Startzeiten.

| # | Start | Szene im Video | Text |
|---|---|---|---|
| 1 | 0:00.6 | Gehirn, „138,639 neurons.“ | A complete fruit-fly brain. Nearly one hundred and forty thousand neurons, simulated one by one. |
| 2 | 0:07.2 | „AI agents run the lab.“ | Omnigent agents run this lab. They pick what to test, run it, and check the result. |
| 3 | 0:13.6 | „Neurons, mapped to movement.“ | The question: how does a fly's brain turn what it senses into what it does? |
| 4 | 0:20.0 | „Stimulus: a looming threat.“ | A looming shadow. The agents switch on the brain's looming detectors. |
| 5 | 0:25.6 | „The brain processes it.“ | The signal races through a thousand neurons, to the giant fiber: the escape neuron. |
| 6 | 0:31.4 | „Escape.“ | It fires, and the virtual fly takes off. Not an animation: the brain's output drives a physics-simulated body. |
| 7 | 0:39.6 | „Another neuron: no escape.“ | Stimulate a different neuron, and the escape neuron stays silent. The fly walks backward instead. |
| 8 | 0:46.4 | „Checked by an AI expert board.“ | Every experiment is checked, re-run, and compared with published research. |
| 9 | 0:51.0 | Schlusskarte „FlyBrainLab“ | FlyBrainLab. AI agents, doing neuroscience. |

Clip 6 ist der längste (Platz bis 0:39.0). Ist er zu lang, in ElevenLabs „Speed“ auf 1.05 stellen oder kürzer: „It fires, and the virtual fly takes off, driven by the simulated brain.“

## B) Ein durchgehender Text (schneller, Pausen per Tag)
In ElevenLabs (Modell *Eleven Multilingual v2* versteht `<break>`-Tags bis 3 s) einfügen. Danach im Schnitt an den Startzeiten aus der Tabelle feinjustieren.

```
A complete fruit-fly brain. Nearly one hundred and forty thousand neurons, simulated one by one. <break time="1.2s" />
Omnigent agents run this lab. They pick what to test, run it, and check the result. <break time="1.0s" />
The question: how does a fly's brain turn what it senses into what it does? <break time="1.2s" />
A looming shadow. The agents switch on the brain's looming detectors. <break time="1.0s" />
The signal races through a thousand neurons, to the giant fiber: the escape neuron. <break time="1.0s" />
It fires, and the virtual fly takes off. Not an animation: the brain's output drives a physics-simulated body. <break time="1.0s" />
Stimulate a different neuron, and the escape neuron stays silent. The fly walks backward instead. <break time="1.2s" />
Every experiment is checked, re-run, and compared with published research. <break time="0.8s" />
FlyBrainLab. AI agents, doing neuroscience.
```

## Empfohlene ElevenLabs-Einstellungen
- **Stimme:** ruhige, warme Erzählerstimme (Kategorie „Narration“ oder Dokumentar), englisch, ohne starken Akzent.
- **Modell:** Eleven Multilingual v2 (versteht `<break>`). Bei Eleven v3 Pausen mit „…“ statt Tags.
- **Stability** ca. 50 %, **Similarity** ca. 75 %, **Style** 0 bis 15 %, **Speed** 1.0 (bei Bedarf 1.05).
- Falls „Omnigent“ seltsam klingt: „Omni-gent“ schreiben.
- **Musik** leise darunter (etwa −20 dB unter der Stimme).

## Fakten-Check
- **„Nearly one hundred and forty thousand neurons“:** 138.639 Neuronen im FlyWire-v783-Modell.
- **„A thousand neurons“:** Im LPLC2-Lauf werden 1.121 Neuronen aktiv. Die Giant Fiber feuert mit 152 bis 169 Hz.
- **„Not an animation“:** Die Bewegung kommt aus der Physik-Simulation, gesteuert über unsere Brücke aus der Gehirn-Aktivität. Die Fußnote im Video nennt die Vereinfachungen.
- **Clip 7:** MDN-Lauf, Giant Fiber 0 Hz, die Fliege läuft rückwärts (Prüfagent: correct).
- **Clip 8:** Das automatische Audit hat alle 25 Experimente mit gleichem Seed exakt nachgerechnet. Der Literaturvergleich (8 von 9) steht in den Benchmarks.

"""Build captioned submission drafts from actual captures and recorded artifacts.

Run with the bundled primary Python (Pillow) and local FFmpeg. No generated
people, synthetic voice, simulated clicks, or invented simulation frames.
The product video requires a real public-browser recording. The two other
videos present actual source captures and artifact summaries as captioned cards.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_submission_assets import ffmpeg_binary, movie_duration, sha256

EXPORTS = ROOT / "submission/exports"
CAPTURES = ROOT / "frontend/output/playwright"
BG, FG, GREEN, MUTED = "#0e1b1b", "#f2f5e9", "#c8ec87", "#aab8aa"


def font(size: int, bold: bool = False):
    choices = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
             "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in choices:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError("A local Arial or DejaVu font is required")


def lines(draw, text: str, used_font, width: int):
    result = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = (current + " " + word).strip()
            if draw.textlength(candidate, font=used_font) > width and current:
                result.append(current)
                current = word
            else:
                current = candidate
        result.append(current)
    return result


def block(draw, xy, text: str, size: int, width: int, color=FG, bold=False):
    used_font = font(size, bold)
    x, y = xy
    for line in lines(draw, text, used_font, width):
        draw.text((x, y), line, font=used_font, fill=color)
        y += int(size * 1.35)
    return y


def render_card(path: Path, title: str, body: str, source: str, *, capture=None,
                details=None, label="ACTUAL RECORDED ARTIFACTS • CAPTIONS ONLY"):
    frame = Image.new("RGB", (1920, 1080), BG)
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle((54, 42, 1866, 96), radius=18, fill="#1f3330")
    draw.text((76, 57), "FLYBRAINLAB  /  CHALLENGE 03", font=font(24, True), fill=GREEN)
    draw.text((862, 57), label, font=font(21), fill=MUTED)
    block(draw, (54, 134), title, 62, 1820, bold=True)
    block(draw, (54, 276), body, 34, 480)
    if capture:
        image = Image.open(capture).convert("RGB")
        # Readable crop of the actual source capture, never new simulation data.
        if image.height > 1000:
            image = image.crop((0, 0, image.width, min(image.height, 900)))
        image.thumbnail((1240, 700), Image.Resampling.LANCZOS)
        x, y = 598 + (1240 - image.width) // 2, 270 + (700 - image.height) // 2
        draw.rounded_rectangle((580, 250, 1866, 987), radius=18, fill="#e9ece1")
        frame.paste(image, (x, y))
    elif details:
        draw.rounded_rectangle((580, 250, 1866, 987), radius=18, fill="#1d302e")
        block(draw, (624, 302), details, 37, 1190)
    block(draw, (54, 1018), "SOURCE  " + source, 22, 1810, color=MUTED)
    frame.save(path)


def timestamp(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, remainder = divmod(millis, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def write_srt(path: Path, segments):
    cursor, pieces = 0.0, []
    for index, segment in enumerate(segments, 1):
        duration, title, body, *_ = segment
        pieces.append(f"{index}\n{timestamp(cursor)} --> {timestamp(cursor + duration)}\n{title}\n{body}\n")
        cursor += duration
    path.write_text("\n".join(pieces) + "\n")


def cards_video(binary: Path, name: str, segments) -> dict:
    frames_dir = EXPORTS / (name + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    concat = ["ffconcat version 1.0"]
    for index, (duration, title, body, source, options) in enumerate(segments):
        frame = frames_dir / f"{index:02}.png"
        render_card(frame, title, body, source, **options)
        # Relative ASCII filenames avoid FFmpeg concat quoting of user paths.
        concat.extend([f"file {frame.name}", f"duration {duration}"])
    concat.append(f"file {len(segments)-1:02}.png")
    (frames_dir / "frames.ffconcat").write_text("\n".join(concat) + "\n")
    output = EXPORTS / (name + ".mp4")
    duration = sum(segment[0] for segment in segments)
    subprocess.run([str(binary), "-nostdin", "-v", "error", "-y", "-f", "concat",
                    "-safe", "1", "-i", "frames.ffconcat", "-t", str(duration),
                    "-r", "24", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)],
                   cwd=frames_dir, check=True)
    write_srt(EXPORTS / (name + ".srt"), segments)
    return {"path": str(output.relative_to(ROOT)), "duration_seconds": movie_duration(output),
            "sha256": sha256(output), "mode": "Captioned artifact cards; no audio/narration",
            "sources": sorted({s[3] for s in segments})}


def product_video(binary: Path, recording: Path) -> dict:
    segments = [
        (7, "Actual public recorded-replay viewer", "8 graph-selected inputs; 25 DNg02 readouts. Selecting a run loads saved data, not a new experiment.", "", {}),
        (10, "Inspect the sham and disconnected controls", "Drive produces a model response. Sham and disconnected outputs give zero. Three simulated seeds; no biological replication.", "", {}),
        (8, "Measured body-state replay", "Recorded MuJoCo root marker. Open-loop adapter; reference ends at 38.8 ms. Stable flight is not demonstrated.", "", {}),
        (7, "Check the controlled comparison", "Readout is the mean rate across all 25 cells and the 200-ms neural horizon. Model assumptions remain visible.", "", {}),
        (6, "Follow the primary evidence", "Versioned identities, paper sources, original run records, and provenance are linked.", "", {}),
        (6, "Keep the scope honest", "Numerical neural response, technical motor adapter, and physics are separate from biological validation.", "", {}),
        (6, "Next experiment", "Matched non-target inputs, biological characterization, and separate controller stabilization.", "", {}),
    ]
    output = EXPORTS / "product_demo.mp4"
    with TemporaryDirectory(prefix="fly-product-video-") as folder:
        temp = Path(folder)
        write_srt(temp / "captions.srt", segments)
        (temp / "label.txt").write_text("FLYBRAINLAB / ACTUAL PUBLIC INTERFACE / RECORDED REPLAY / CAPTIONS ONLY")
        shutil.copyfile("/System/Library/Fonts/Supplemental/Arial.ttf", temp / "font.ttf")
        video_filter = (
            "scale=1920:950:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:55:color=0x0e1b1b,"
            "tpad=stop_mode=clone:stop_duration=6,"
            "drawtext=fontfile=font.ttf:textfile=label.txt:fontsize=25:fontcolor=0xc8ec87:x=32:y=16,"
            "subtitles=captions.srt:force_style='Fontname=Arial,Fontsize=16,Outline=2,Shadow=0,MarginV=12,BackColour=&H90000000,BorderStyle=3'"
        )
        subprocess.run([str(binary), "-nostdin", "-v", "error", "-y", "-i", str(recording),
                        "-t", "50", "-an", "-vf", video_filter, "-r", "24", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(output)], cwd=temp, check=True)
        shutil.copyfile(temp / "captions.srt", EXPORTS / "product_demo.srt")
    return {"path": str(output.relative_to(ROOT)), "duration_seconds": movie_duration(output),
            "sha256": sha256(output), "mode": "Real public-browser recording with burned-in explanatory captions; final captured frame held for closing text; no audio/narration",
            "recording_source": str(recording.relative_to(ROOT)), "recording_sha256": sha256(recording)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recording", type=Path, required=True, help="Actual public-viewer screen recording")
    parser.add_argument("--trace", type=Path, required=True, help="Exported verified native Omnigent trace")
    parser.add_argument("--test-a", type=Path, required=True, help="New comparison linked to native test A receipt")
    parser.add_argument("--test-b", type=Path, help="Optional new comparison linked to native test B receipt")
    args = parser.parse_args()
    trace = json.loads(args.trace.read_text())
    test_a = json.loads(args.test_a.read_text())
    test_b = json.loads(args.test_b.read_text()) if args.test_b else None
    if not trace.get("native_discovery_loop_verified"):
        raise ValueError("Refusing completed-C3 video claims without verified native trace")
    receipt_tests = {r.get("test") for r in trace.get("numeric_receipts", [])}
    if "A" not in receipt_tests or (test_b and "B" not in receipt_tests):
        raise ValueError("Need native numeric receipts for every executed test shown")
    comparisons = [test_a] + ([test_b] if test_b else [])
    if any(t.get("execution_context") == "independent-feasibility-before-Omnigent" for t in comparisons):
        raise ValueError("Independent preflight comparisons cannot be relabelled as native experiments")
    for expected_test, supplied in [("A", args.test_a)] + ([("B", args.test_b)] if args.test_b else []):
        linked = False
        for receipt in trace.get("numeric_receipts", []):
            if receipt.get("test") != expected_test:
                continue
            receipt_path = ROOT / receipt["receipt_path"]
            stored = json.loads(receipt_path.read_text())
            comparison_path = stored.get("result", {}).get("comparison_path")
            if comparison_path and (ROOT / comparison_path).resolve() == supplied.resolve():
                linked = True
        if not linked:
            raise ValueError(f"Supplied test {expected_test} comparison is not linked to a native numeric receipt")
    if test_a["summary"]["next_test"] != "B" or (test_b and not test_b["summary"]["supports_outgoing_dependency"]):
        raise ValueError("Results differ from current scripted decision; update script before rendering")
    binary = ffmpeg_binary(None)
    if binary is None:
        raise RuntimeError("Local FFmpeg required")
    EXPORTS.mkdir(parents=True, exist_ok=True)
    source_trace = str(args.trace.relative_to(ROOT) if args.trace.is_absolute() else args.trace)
    source_a = str(args.test_a.relative_to(ROOT) if args.test_a.is_absolute() else args.test_a)
    source_b = str(args.test_b.relative_to(ROOT) if args.test_b.is_absolute() else args.test_b) if args.test_b else ""
    result_source = source_a + (" + " + source_b if source_b else "")
    drive = test_a["summary"]["upstream_drive"]
    rates = f"{drive['mean_hz']:.2f} ± {drive['sample_sd_hz']:.2f} Hz"
    sham_rate = test_a["summary"]["sham"]["mean_hz"]
    disconnected_rate = test_b["summary"]["outgoing_disconnected"]["mean_hz"] if test_b else None
    removed_response = test_b is not None and abs(disconnected_rate) < 1e-12
    b_result = "response removed" if removed_response else "response reduced"
    roles = ", ".join(trace["roles_observed"])
    native_details = (f"Omnigent {trace['omnigent_version']}\nNative root: {trace['root_conversation_id']}\n\n"
                      f"Observed specialist roles: {roles}\n\n"
                      f"{len(trace['tool_calls'])} native tool calls\n"
                      + ("Tests A + B: numeric receipts present\n" if test_b else "Test A executed; B selected as next test\n") +
                      "Updated discovery decision: persisted\n\nCached primary evidence; BrightData not used.")
    result_details = (f"25 DNg02 cells • 200 ms • Seeds 42 / 43 / 44\n\n"
                      f"Drive: {rates}\nSham: {sham_rate:g} Hz\n" +
                      (f"Disconnected outputs: {disconnected_rate:g} Hz\n\nA → positive in every seed → execute B\nB → {b_result} → matched-input control next\n\n" if test_b else
                       "\nA → positive in every seed\nUpdated decision: execute frozen Test B next.\nB is designed but not yet executed in this native loop.\n\n") +
                      "Descriptive model comparison; no biological replicate or p-value.")
    next_decision = ("Next: matched non-target inputs." if test_b else "Next: execute frozen B disconnection control.")
    architecture = ("Omnigent → evidence / hypothesis / experiments / analysis\n\n"
                    "Pinned FlyWire v783 → Brian2 / published LIF model\n138,639 neurons • 15,091,983 connection rows\n\n"
                    "Saved DNg02 spikes → frozen motor adapter → Flybody / MuJoCo\n\n"
                    "Actual exported states → static Vite / Three.js / GitHub Pages")
    evidence = ("Namiki et al. 2022: DNg02 population activity and wingbeat amplitude in tethered, already-flying flies.\n\n"
                "25 identities verified in FlyWire v783; 13 left / 12 right.\n\n"
                "8 upstream inputs selected by graph weights before simulation. Their biological functions are not established.")
    frozen = ("Test A: 150-Hz upstream input vs. 0-Hz sham.\n\n"
              "Decision frozen before execution: positive paired difference in all 3 seeds → run B.\n\n"
              "Test B: unchanged graph vs. zero outgoing input weights; ≥80% reduction in every seed.\n\n"
              "200 ms / 0.1-ms neural step / identical seed order.")
    benchmark = json.loads((ROOT / "data/experiments/evidence_lookup_benchmark.json").read_text())
    med = benchmark["median_wall_ms"]
    benchmark_details = (f"Repeated annotation parse: {med['full_annotation_scan']:.2f} ms median\n"
                         f"Reviewed KB identity claim: {med['reviewed_kb_lookup']:.3f} ms median\n\n"
                         "Same 25 IDs / 5 repetitions per method / warm local cache\n\n"
                         "One-time evidence collection/review excluded.\nNot end-to-end research speed, accuracy, or simulation acceleration.")
    capture_body = CAPTURES / "public-body.png"
    capture_home = CAPTURES / "public-desktop.png"
    tech = [
        (10, "Research, simulation, visualization", "Three separate layers. Omnigent controls the research workflow; numerical solvers compute dynamics.", "agents/fly-discovery/ + pinned simulation code", {"details": architecture}),
        (11, "An actual native Omnigent trace", "Specialists exchange structured outputs and call experiment tools. The trace links their actions to new numeric runs.", source_trace, {"details": native_details}),
        (13, "A result changes the next test", "The positive A comparison leads to B." + ((" Removing outgoing weights removes the response." if removed_response else " Removing outgoing weights reduces the response.") if test_b else " B is the next native experiment to execute."), result_source, {"details": result_details}),
        (12, "Measured body states; fixed assumptions", "Technical body preflight: saved spikes drive an existing wingbeat controller through a frozen adapter. Physics produces the states.", "data/coupling/adapter_v1.json + comparison.json", {"capture": capture_body}),
        (9, "Limits are part of the result", "Default body run: reference end at 38.8 ms. With extended reference, the same test pattern falls below its height threshold at 53.6 ms.", "data/body/termination_diagnostics.json + BODY_INTEGRATION.md", {"details": next_decision + "\n\n38.8-ms default stop is reference end, not instability.\nExtended-reference probe falls at 53.6 ms.\n\nStable flight and biological calibration remain unresolved.\n\nBrightData tools are implemented; provider live access is not verified."}),
    ]
    c3 = [
        (12, "Question: a testable model prediction", "Can graph-selected upstream inputs activate DNg02, and does the response require their outgoing connections?", "Public viewer + research/designs/dng02-input-v1.json", {"capture": capture_home}),
        (18, "Evidence with pinned identities", "Primary literature motivates the flight-related readout. Official annotations match IDs to the installed data version.", "Namiki2022 DOI10.1016/j.cub.2022.01.008 + DNG02_EVIDENCE.md", {"details": evidence}),
        (14, "Hypothesis and two frozen tests", "Choose A first. Preserve its decision rule and controls rather than tuning inputs after seeing the result.", "research/designs/dng02-input-v1.json + .sha256", {"details": frozen}),
        (21, "Experiment: native specialist/tool activity", "Omnigent executes the recorded workflow using cached primary evidence. New numeric receipts retain real provenance.", source_trace, {"details": native_details}),
        (19, "Result → updated decision", "A's positive response selects the preplanned B control." + (f" B: {b_result}; specificity is next." if test_b else " B remains the next native test to execute."), result_source, {"details": result_details}),
        (15, "Embodiment: technical open-loop coupling", "Separate technical preflight. Default stop: reference end at 38.8 ms. Extended-reference probe falls below the height threshold at 53.6 ms.", "data/coupling/comparison.json + data/body/termination_diagnostics.json", {"capture": capture_body}),
        (11, "One measured evidence bottleneck", "Reuse a checked extraction for a repeated identity query. Keep the narrow benchmark scope explicit.", "data/experiments/evidence_lookup_benchmark.json", {"details": benchmark_details}),
        (8, "Next experiment and remaining uncertainty", next_decision + " Biological characterization; controller stability; future calibration and sensory feedback.", "Native updated decision + NEURAL_RESULTS.md + BODY_INTEGRATION.md", {"details": ("Model dependency is demonstrated." if test_b else "Native model response + adaptive next decision are demonstrated.") + "\n\nAutonomous or biologically validated flight is not.\n\nInspect the public replay and linked run records:\nvalleebo.github.io/FlyBrainLab"}),
    ]
    outputs = [product_video(binary, args.recording.resolve()), cards_video(binary, "technical_walkthrough", tech), cards_video(binary, "c3_demo", c3)]
    (EXPORTS / "product_source_manifest.json").write_text(json.dumps(outputs[0], indent=2) + "\n")
    manifest = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
                "mode": "Prepared captioned videos from real captures/artifacts; no synthetic voice or team imagery",
                "public_capture_url": "https://valleebo.github.io/FlyBrainLab/",
                "native_trace": {"path": source_trace, "sha256": sha256(args.trace)},
                "native_comparisons": [{"path": source_a, "sha256": sha256(args.test_a)}] + ([{"path": source_b, "sha256": sha256(args.test_b)}] if args.test_b else []),
                "capture_files": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in (capture_home, capture_body)],
                "videos": outputs, "human_review_required": True,
                "team_intro_and_photo": "Not generated; actual human team assets are required",
                "submission_completed": False}
    (EXPORTS / "video_source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()

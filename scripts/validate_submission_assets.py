"""Validate local HackOS/C3 media files; never upload or submit anything.

Uses only Python's standard library and a locally installed FFmpeg binary.
MP4/MOV duration comes from the movie header at its full integer precision,
not a rounded filename, nominal target, or FFmpeg's two-decimal display.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def ffmpeg_binary(explicit: str | None) -> Path | None:
    requested = explicit or os.environ.get("FFMPEG_BINARY")
    if requested:
        value = shutil.which(requested) or requested
        path = Path(value).expanduser()
        return path if path.is_file() and os.access(path, os.X_OK) else None
    found = shutil.which("ffmpeg")
    if found:
        return Path(found)
    candidates = sorted((ROOT / ".runtime/media-venv").glob(
        "lib/python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-*"))
    return next((p for p in candidates if p.is_file() and os.access(p, os.X_OK)), None)


def movie_duration(path: Path) -> float:
    """Read the presentation duration in a standard ISO BMFF/QuickTime mvhd."""
    file_size = path.stat().st_size
    with path.open("rb") as stream:
        def boxes(start: int, end: int):
            cursor = start
            while cursor < end:
                if end - cursor < 8:
                    raise ValueError("Truncated MP4/MOV box header")
                stream.seek(cursor)
                size, kind = struct.unpack(">I4s", stream.read(8))
                header = 8
                if size == 1:
                    extended = stream.read(8)
                    if len(extended) != 8:
                        raise ValueError("Truncated MP4/MOV extended size")
                    size, header = struct.unpack(">Q", extended)[0], 16
                elif size == 0:
                    size = end - cursor
                if size < header or cursor + size > end:
                    raise ValueError("Invalid MP4/MOV box size")
                yield kind, cursor + header, cursor + size
                cursor += size

        for kind, begin, end in boxes(0, file_size):
            if kind != b"moov":
                continue
            for child, payload, child_end in boxes(begin, end):
                if child != b"mvhd":
                    continue
                stream.seek(payload)
                header = stream.read(min(40, child_end - payload))
                if not header:
                    raise ValueError("Empty movie header")
                version = header[0]
                if version == 0 and len(header) >= 20:
                    timescale, duration = struct.unpack_from(">II", header, 12)
                    unknown = 0xFFFFFFFF
                elif version == 1 and len(header) >= 32:
                    timescale = struct.unpack_from(">I", header, 20)[0]
                    duration = struct.unpack_from(">Q", header, 24)[0]
                    unknown = 0xFFFFFFFFFFFFFFFF
                else:
                    raise ValueError("Unsupported or truncated movie-header version")
                if not timescale or not duration or duration == unknown:
                    raise ValueError("Missing finite positive movie duration")
                return duration / timescale
    raise ValueError("No readable MP4/MOV movie duration (moov/mvhd)")


def photo_signature(path: Path) -> str:
    with path.open("rb") as stream:
        value = stream.read(16)
    if value.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if value.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if value[:4] == b"RIFF" and value[8:12] == b"WEBP":
        return "webp"
    raise ValueError("File signature is not JPEG, PNG or WebP")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decode_media(binary: Path, path: Path) -> dict:
    # Mapping a video stream also rejects audio-only files carrying .mp4/.mov.
    process = subprocess.run(
        [str(binary), "-nostdin", "-hide_banner", "-nostats", "-xerror",
         "-err_detect", "explode", "-i", str(path), "-map", "0:v:0",
         "-map", "0:a?", "-progress", "pipe:1", "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60,
    )
    output = process.stderr
    frame_counts = re.findall(r"^frame=(\d+)$", process.stdout, flags=re.MULTILINE)
    if process.returncode or not frame_counts or int(frame_counts[-1]) == 0:
        raise ValueError("FFmpeg could not fully decode the video/image: " + output[-1500:].strip())
    video_line = next((line.strip() for line in output.splitlines()
                       if "Stream #0:" in line and "Video:" in line), "")
    size = re.search(r"\b(\d{2,6})x(\d{2,6})\b", video_line)
    return {"fully_decoded": True, "decoded_video_frames": int(frame_counts[-1]), "stream": video_line,
            "width": int(size[1]) if size else None,
            "height": int(size[2]) if size else None}


def validate(asset: dict, path: Path, binary: Path | None) -> dict:
    result = {"key": asset["key"], "path": str(path), "passed": False, "errors": []}
    errors = result["errors"]
    if not path.is_file():
        errors.append("File is missing; a script/storyboard is not a delivered media asset")
        return result
    size = path.stat().st_size
    result.update(bytes=size, max_bytes=asset["max_bytes"])
    if size == 0:
        errors.append("File is empty")
    if size > asset["max_bytes"]:
        errors.append(f"File exceeds {asset['max_bytes']} bytes")
    if path.suffix.lower() not in asset["extensions"]:
        errors.append("Unsupported extension; allowed: " + ", ".join(asset["extensions"]))
    try:
        if asset["key"] == "team_photo":
            actual = photo_signature(path)
            result["format"] = actual
            expected = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp"}
            if expected.get(path.suffix.lower()) != actual:
                errors.append("Image extension does not match its actual signature")
        else:
            duration = movie_duration(path)
            result.update(duration_seconds=duration,
                          max_duration_seconds=asset["max_duration_seconds"])
            if duration > asset["max_duration_seconds"]:
                errors.append(f"Duration exceeds {asset['max_duration_seconds']} seconds")
        if binary is None:
            errors.append("Local FFmpeg unavailable; decode verification is incomplete")
        elif not errors:
            result.update(decode_media(binary, path))
        result["sha256"] = sha256(path)
    except (OSError, ValueError, struct.error, subprocess.TimeoutExpired) as exc:
        errors.append(str(exc))
    result["passed"] = not errors
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "submission/asset_manifest.json")
    parser.add_argument("--ffmpeg", help="Existing local FFmpeg executable; no installation/download")
    parser.add_argument("--output", type=Path, help="Write the JSON report in addition to printing it")
    parser.add_argument("--public-output", type=Path, help="Write a shareable copy with local absolute paths removed")
    for key in ("team_photo", "team_intro", "product_demo", "technical_walkthrough", "c3_demo"):
        parser.add_argument("--" + key.replace("_", "-"), dest=key, type=Path)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text())
    binary = ffmpeg_binary(args.ffmpeg)
    assets = []
    for asset in manifest["assets"]:
        path = getattr(args, asset["key"], None) or ROOT / asset["path"]
        assets.append(validate(asset, path.expanduser().resolve(), binary))
    report = {
        "schema_version": 1, "checked_at": datetime.now(timezone.utc).isoformat(),
        "ffmpeg_binary": str(binary) if binary else None,
        "all_media_passed": all(asset["passed"] for asset in assets),
        "submission_completed": False,
        "verification_scope": "Local file format/signature, decimal byte limit, full-precision MP4/MOV duration, complete video/audio decode, SHA-256; human content/upload/submission checks remain separate",
        "c3_limit_note": "120 seconds is our two-minute planning target, not a confirmed HackOS field limit",
        "assets": assets,
        "human_checks_remaining": manifest.get("human_checks", []),
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n")
    if args.public_output:
        public = json.loads(encoded)
        public["ffmpeg_binary"] = binary.name if binary else None
        public["local_paths_redacted"] = True
        for asset in public["assets"]:
            local = Path(asset["path"])
            try:
                asset["path"] = str(local.relative_to(ROOT))
            except ValueError:
                asset["path"] = local.name
            asset["errors"] = [error.replace(str(local), asset["path"])
                               .replace(str(ROOT), ".")
                               .replace(str(binary), binary.name if binary else "")
                               for error in asset["errors"]]
        args.public_output.parent.mkdir(parents=True, exist_ok=True)
        args.public_output.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n")
    print(encoded)
    return 0 if report["all_media_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

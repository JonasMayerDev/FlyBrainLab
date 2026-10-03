"""Reproduce the pinned author-source and v783 downloads, verifying every hash."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/brain/manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(*, verify_only: bool = False) -> dict:
    manifest = json.loads(MANIFEST.read_text())
    checked = []
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        valid = (path.is_file() and path.stat().st_size == entry["bytes"]
                 and sha256(path) == entry["sha256"])
        if not valid:
            if verify_only:
                raise RuntimeError(f"Missing or mismatched file: {entry['path']}")
            if path.exists():
                raise RuntimeError(f"Refusing to overwrite unexpected file: {entry['path']}")
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(path.name + ".partial")
            request = urllib.request.Request(entry["url"], headers={"User-Agent": "FlyBrainHackathon/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    output.write(block)
            if partial.stat().st_size != entry["bytes"] or sha256(partial) != entry["sha256"]:
                raise RuntimeError(f"Downloaded file failed verification: {entry['path']}")
            partial.rename(path)
        checked.append(entry["path"])
    return {"status": "verified", "source_commit": manifest["source_commit"], "files": checked}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(download(verify_only=args.verify_only), indent=2))

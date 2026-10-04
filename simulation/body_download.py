"""Download two small pinned official Flybody supplements for diagnostics.

Raw GPL-3.0+ assets stay in ignored .runtime; public run exports retain hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

from simulation.body import ROOT

DESTINATION = ROOT / ".runtime/body-published-data"
FILES = [(51196859, "datasets_flight-imitation.zip", "bb35ce27e07c4ffbd3d56ff6dec90905", 12880076),
         (44815195, "trained-fly-policies.zip", "12934d5a1c60631a710bc2b6d297d3ce", 6537720)]


def download(verify_only: bool = False) -> dict:
    manifest = json.loads((ROOT / "data/body/published_assets_manifest.json").read_text())
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for file_id, filename, expected_md5, size in FILES:
        path = DESTINATION / filename
        if not path.exists():
            if verify_only:
                raise FileNotFoundError(path)
            with urllib.request.urlopen(f"https://ndownloader.figshare.com/files/{file_id}", timeout=30) as response:
                data = response.read(size + 1)
            if len(data) != size or hashlib.md5(data).hexdigest() != expected_md5:
                raise ValueError(f"Published download size/MD5 mismatch: {filename}")
            path.write_bytes(data)
        if path.stat().st_size != size or hashlib.md5(path.read_bytes()).hexdigest() != expected_md5:
            raise ValueError(f"Existing archive differs from pinned published source: {filename}")
        if not verify_only:
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if not (DESTINATION / info.filename).resolve().is_relative_to(DESTINATION.resolve()):
                        raise ValueError("Unsafe archive member path")
                archive.extractall(DESTINATION)
    expected = {**manifest["flight_saved_model_sha256"],
                "wing_pattern_fmech.npy": manifest["wing_pattern_sha256"]}
    for filename, digest in expected.items():
        if hashlib.sha256((DESTINATION / filename).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Extracted published asset differs from recorded source: {filename}")
    return {"status": "verified", "archives": len(FILES), "checked_assets": len(expected),
            "source": manifest["source"], "license": manifest["license"]["name"],
            "raw_assets_are_publicly_committed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    print(json.dumps(download(parser.parse_args().verify_only), indent=2))

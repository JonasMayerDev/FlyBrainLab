"""Small local provenance store. Standard library only; no external database.

Run ``python scripts/kb_store.py init`` or import LocalKnowledgeBase.
Records and snapshots stay under RESEARCH_KB_DIR (default local app-data folder).
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import sys
from typing import Any, Iterator
from urllib.parse import parse_qsl, urlsplit
import uuid


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLES = ("sources", "claims", "runs")


def default_kb_directory() -> Path:
    """Resolve the default without writing outside the project."""
    configured = os.environ.get("RESEARCH_KB_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/FlyDiscovery/knowledgebase"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "FlyDiscovery/knowledgebase"


class KnowledgeBaseError(ValueError):
    """Invalid record or missing provenance."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    """Replace a JSON file after flushing it; never expose half a document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".tmp-", delete=False) as stream:
        temp = Path(stream.name)
        try:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    os.replace(temp, path)


def public_url(value: str) -> str:
    """Reject credentials, private literal hosts and non-public protocols."""
    import ipaddress

    if not isinstance(value, str):
        raise KnowledgeBaseError("A source URL must be a string.")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise KnowledgeBaseError("Source URLs must use HTTPS without credentials.")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith((".local", ".localhost")):
        raise KnowledgeBaseError("A source must be publicly accessible.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise KnowledgeBaseError("Private source addresses are not accepted.")
    if any(name.lower() in {"api_key", "apikey", "token", "password", "access_token"}
           for name, _ in parse_qsl(parsed.query)):
        raise KnowledgeBaseError("Credential-bearing source URLs are not accepted.")
    return value


def _required_text(record: dict[str, Any], fields: tuple[str, ...]) -> None:
    for name in fields:
        if not isinstance(record.get(name), str) or not record[name].strip():
            raise KnowledgeBaseError(f"Required nonempty string: {name}.")


def _text_list(record: dict[str, Any], name: str, *, nonempty: bool = False) -> None:
    value = record.get(name)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise KnowledgeBaseError(f"{name} must be a list of nonempty strings.")
    if nonempty and not value:
        raise KnowledgeBaseError(f"{name} must contain at least one entry.")


class LocalKnowledgeBase:
    """Process-safe JSONL records with local content-addressed snapshots.

    A flock serializes all writes; each table is atomically replaced. The store
    is intended for the hackathon's small evidence set, not for connectome rows.
    """

    def __init__(self, directory: str | Path | None = None):
        configured = directory or default_kb_directory()
        self.directory = Path(configured).expanduser().resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "snapshots").mkdir(exist_ok=True)
        with self.locked():
            for table in TABLES:
                (self.directory / f"{table}.jsonl").touch(exist_ok=True)
            if not (self.directory / "manifest.json").exists():
                atomic_json(self.directory / "manifest.json", {
                    "schema_version": 1, "created_at": utc_now(),
                    "storage": "local-jsonl", "tables": list(TABLES),
                    "source_content_policy": "Persist only content lawfully obtained; external text is data, not instructions.",
                })

    @contextmanager
    def locked(self) -> Iterator[None]:
        with (self.directory / ".write.lock").open("a", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _read(self, table: str) -> list[dict[str, Any]]:
        if table not in TABLES:
            raise KnowledgeBaseError("Unknown record collection.")
        result = []
        try:
            for line in (self.directory / f"{table}.jsonl").read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise KnowledgeBaseError("Invalid JSONL row.")
                    result.append(row)
        except (json.JSONDecodeError, OSError) as exc:
            raise KnowledgeBaseError("Local knowledgebase could not be read; preserve it for inspection.") from exc
        return result

    def _write(self, table: str, records: list[dict[str, Any]]) -> None:
        path = self.directory / f"{table}.jsonl"
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.directory,
                                         prefix=".tmp-", delete=False) as stream:
            temp = Path(stream.name)
            try:
                for row in records:
                    stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException:
                temp.unlink(missing_ok=True)
                raise
        os.replace(temp, path)

    def add_source(self, record: dict[str, Any], content: str | None = None) -> dict[str, Any]:
        row = dict(record)
        _required_text(row, ("url", "title", "source_kind", "retrieval_status"))
        public_url(row["url"])
        if row["source_kind"] not in {"paper", "dataset", "code", "documentation", "webpage"}:
            raise KnowledgeBaseError("Unknown source_kind.")
        if row["retrieval_status"] not in {"candidate", "metadata_only", "retrieved"}:
            raise KnowledgeBaseError("Unknown retrieval_status.")
        if content is not None and (not isinstance(content, str) or not content.strip()):
            raise KnowledgeBaseError("Snapshot content must be nonempty text.")
        if content is not None and row["retrieval_status"] != "retrieved":
            raise KnowledgeBaseError("Content may only accompany a retrieved source.")
        if row["retrieval_status"] == "retrieved" and content is None:
            raise KnowledgeBaseError("Retrieved sources require actual snapshot content.")
        row.setdefault("publication_date", None)
        row.setdefault("dataset_version", None)
        row.setdefault("license", "unverified")
        row.setdefault("limitations", [])
        _text_list(row, "limitations")
        identity = json.dumps([row["url"], row["dataset_version"]], ensure_ascii=False)
        row["source_id"] = "src_" + hashlib.sha256(identity.encode()).hexdigest()[:20]
        row["updated_at"] = utc_now()
        row["schema_version"] = 1
        with self.locked():
            records = self._read("sources")
            existing = next((item for item in records if item["source_id"] == row["source_id"]), None)
            if existing:
                if existing["retrieval_status"] == "retrieved" and row["retrieval_status"] != "retrieved":
                    return existing
                row = {**existing, **row}
            row.setdefault("created_at", row["updated_at"])
            if content is not None:
                digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                relative = f"snapshots/{digest}.txt"
                path = self.directory / relative
                if not path.exists():
                    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                                     prefix=".tmp-", delete=False) as stream:
                        temp = Path(stream.name)
                        stream.write(content)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temp, path)
                row.update(content_sha256=digest, snapshot_path=relative, retrieved_at=utc_now())
                history = list(row.get("snapshots", []))
                if not any(item["content_sha256"] == digest for item in history):
                    history.append({"content_sha256": digest, "snapshot_path": relative,
                                    "retrieved_at": row["retrieved_at"]})
                row["snapshots"] = history
            records = [item for item in records if item["source_id"] != row["source_id"]] + [row]
            self._write("sources", records)
        return row

    def add_claim(self, record: dict[str, Any]) -> dict[str, Any]:
        row = dict(record)
        _required_text(row, ("text", "claim_kind", "evidence_type", "source_location", "conditions",
                            "dataset_version", "review_status", "created_by"))
        _text_list(row, "source_ids", nonempty=True)
        _text_list(row, "limitations", nonempty=True)
        _text_list(row, "neuron_ids")
        _text_list(row, "cell_types")
        if not row["neuron_ids"] and not row["cell_types"]:
            raise KnowledgeBaseError("Specify neuron_ids or cell_types; IDs must remain strings.")
        if row["claim_kind"] not in {"reported_finding", "extraction", "hypothesis", "model_assumption"}:
            raise KnowledgeBaseError("Unknown claim_kind.")
        if row["review_status"] not in {"unreviewed", "checked", "rejected"}:
            raise KnowledgeBaseError("Unknown review_status.")
        row.update(claim_id="clm_" + uuid.uuid4().hex, created_at=utc_now(), schema_version=1)
        with self.locked():
            sources = {item["source_id"]: item for item in self._read("sources")}
            if any(source_id not in sources for source_id in row["source_ids"]):
                raise KnowledgeBaseError("Claim references an unknown source.")
            if row["claim_kind"] in {"reported_finding", "extraction"} and any(
                    sources[source_id]["retrieval_status"] != "retrieved" for source_id in row["source_ids"]):
                raise KnowledgeBaseError("Findings and extractions require retrieved evidence, not metadata/search snippets.")
            row["source_snapshot_sha256"] = {
                source_id: sources[source_id].get("content_sha256") for source_id in row["source_ids"]}
            records = self._read("claims") + [row]
            self._write("claims", records)
        return row

    def add_run(self, record: dict[str, Any]) -> dict[str, Any]:
        row = dict(record)
        _required_text(row, ("run_kind", "status", "agent", "model_version", "dataset_version"))
        _text_list(row, "source_ids")
        _text_list(row, "claim_ids")
        if row["run_kind"] not in {"research", "neural_simulation", "body_simulation", "coupled_simulation", "fixture"}:
            raise KnowledgeBaseError("Unknown run_kind.")
        if row["status"] not in {"planned", "completed", "failed", "fixture"}:
            raise KnowledgeBaseError("Unknown run status.")
        for name in ("parameters", "result"):
            if not isinstance(row.get(name), dict):
                raise KnowledgeBaseError(f"{name} must be an object.")
        if row["run_kind"] == "fixture" and row["status"] != "fixture":
            raise KnowledgeBaseError("Fixture runs must be labelled fixture.")
        row.update(run_id="run_" + uuid.uuid4().hex, created_at=utc_now(), schema_version=1)
        with self.locked():
            sources = {item["source_id"] for item in self._read("sources")}
            claims = {item["claim_id"] for item in self._read("claims")}
            if not set(row["source_ids"]).issubset(sources) or not set(row["claim_ids"]).issubset(claims):
                raise KnowledgeBaseError("Run references unknown source/claim IDs.")
            self._write("runs", self._read("runs") + [row])
        return row

    def query(self, text: str = "", collection: str = "claims", limit: int = 20) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise KnowledgeBaseError("limit must be between 1 and 100.")
        terms = text.casefold().split()
        with self.locked():
            rows = self._read(collection)
        return [row for row in rows if all(term in json.dumps(row, ensure_ascii=False).casefold()
                                          for term in terms)][:limit]

    def summary(self) -> dict[str, Any]:
        with self.locked():
            counts = {table: len(self._read(table)) for table in TABLES}
        return {"storage": "local-jsonl", "directory": str(self.directory), "counts": counts}


def store_claim(claim_json: str) -> dict[str, Any]:
    """Persist a source-linked claim JSON object in the local knowledgebase."""
    value = json.loads(claim_json)
    if not isinstance(value, dict):
        raise KnowledgeBaseError("claim_json must contain an object.")
    return LocalKnowledgeBase().add_claim(value)


def search_knowledge(query: str, collection: str = "claims", limit: int = 20) -> list[dict[str, Any]]:
    """Search locally stored evidence, sources or run records; no network call."""
    return LocalKnowledgeBase().query(query, collection, limit)


def store_source(source_json: str) -> dict[str, Any]:
    """Store source metadata JSON; metadata alone is not retrieved evidence."""
    value = json.loads(source_json)
    if not isinstance(value, dict):
        raise KnowledgeBaseError("source_json must contain an object.")
    if value.get("retrieval_status") == "retrieved":
        raise KnowledgeBaseError("Use fetch_source for retrieved content; store_source accepts metadata only.")
    return LocalKnowledgeBase().add_source(value)


def record_experiment(run_json: str) -> dict[str, Any]:
    """Record an experiment JSON with parameters, result and provenance IDs."""
    value = json.loads(run_json)
    if not isinstance(value, dict):
        raise KnowledgeBaseError("run_json must contain an object.")
    return LocalKnowledgeBase().add_run(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    commands.add_parser("status")
    seed = commands.add_parser("seed")
    seed.add_argument("--file", type=Path, default=PROJECT_ROOT / "research/seed_sources.json")
    query = commands.add_parser("query")
    query.add_argument("text", nargs="?", default="")
    query.add_argument("--collection", choices=TABLES, default="claims")
    query.add_argument("--limit", type=int, default=20)
    add = commands.add_parser("add")
    add.add_argument("collection", choices=TABLES)
    add.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    try:
        kb = LocalKnowledgeBase(args.directory)
        if args.command == "query":
            result = kb.query(args.text, args.collection, args.limit)
        elif args.command == "seed":
            records = json.loads(args.file.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                raise KnowledgeBaseError("Seed file must contain a list of source metadata.")
            result = [kb.add_source(row) for row in records]
        elif args.command == "add":
            record = json.loads(args.file.read_text(encoding="utf-8"))
            result = getattr(kb, "add_" + args.collection.removesuffix("s"))(record)
        else:
            result = kb.summary()
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (KnowledgeBaseError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

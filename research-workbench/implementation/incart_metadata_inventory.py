"""Download and audit INCART headers/annotations without waveform files."""

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen
from xml.etree import ElementTree

from mitdb_beat_manifest import SYMBOL_CLASS


BUCKET = "https://physionet-open.s3.amazonaws.com"
PREFIX = "incartdb/1.0.0/"
LIST_URL = BUCKET + "/?list-type=2&prefix=" + PREFIX + "&max-keys=1000"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
NAME = re.compile(r"I(?:0[1-9]|[1-6][0-9]|7[0-5])\.(?:hea|atr)$")
PATIENT = re.compile(r"\bpatient\s+([1-9]|[12][0-9]|3[0-2])\b", re.I)
MAX_METADATA_BYTES = 2_000_000


def inventory(xml: bytes) -> list[dict]:
    root = ElementTree.fromstring(xml)
    if root.findtext("s:IsTruncated", namespaces=NS) != "false":
        raise ValueError("S3 listing is incomplete")
    items = []
    for entry in root.findall("s:Contents", NS):
        key = entry.findtext("s:Key", namespaces=NS)
        if not key or not NAME.fullmatch(key.removeprefix(PREFIX)) or not key.startswith(PREFIX):
            continue
        items.append({"key": key, "size": int(entry.findtext("s:Size", namespaces=NS)),
                      "etag": entry.findtext("s:ETag", namespaces=NS).strip('"')})
    if len(items) != 150 or sum(item["size"] for item in items) > MAX_METADATA_BYTES:
        raise ValueError("unexpected INCART header/annotation inventory")
    for suffix in ("hea", "atr"):
        if {x["key"].rsplit("/", 1)[-1] for x in items if x["key"].endswith(suffix)} != {
                f"I{i:02d}.{suffix}" for i in range(1, 76)}:
            raise ValueError(f"missing {suffix} records")
    return sorted(items, key=lambda item: item["key"])


def download_one(item: dict, target: Path) -> dict:
    path = target / item["key"].rsplit("/", 1)[-1]
    if path.exists() and path.stat().st_size == item["size"] and \
            hashlib.md5(path.read_bytes()).hexdigest() == item["etag"]:
        raw = path.read_bytes()
    else:
        with urlopen(BUCKET + "/" + quote(item["key"], safe="/"), timeout=30) as response:
            raw = response.read(MAX_METADATA_BYTES + 1)
        if len(raw) != item["size"] or hashlib.md5(raw).hexdigest() != item["etag"]:
            raise ValueError(f"checksum or size mismatch: {path.name}")
        path.with_suffix(path.suffix + ".part").write_bytes(raw)
        path.with_suffix(path.suffix + ".part").replace(path)
    return {**item, "sha256": hashlib.sha256(raw).hexdigest()}


def audit(target: Path) -> dict:
    import wfdb

    symbol_counts = Counter()
    class_counts = Counter()
    patient_records = defaultdict(list)
    records = []
    for number in range(1, 76):
        record = f"I{number:02d}"
        header = wfdb.rdheader(str(target / record))
        annotation = wfdb.rdann(str(target / record), "atr")
        matches = [PATIENT.search(line) for line in header.comments]
        patient_ids = {int(match.group(1)) for match in matches if match}
        if len(patient_ids) != 1:
            raise ValueError(f"patient ID absent or ambiguous: {record}")
        patient = patient_ids.pop()
        if header.fs != 257 or len(header.sig_name) != 12:
            raise ValueError(f"unexpected signal configuration: {record}")
        lead_ii = [i for i, name in enumerate(header.sig_name) if name.upper() == "II"]
        if len(lead_ii) != 1:
            raise ValueError(f"lead II absent or ambiguous: {record}")
        local_symbols = Counter(annotation.symbol)
        local_classes = Counter(SYMBOL_CLASS.get(symbol, "unmapped") for symbol in annotation.symbol)
        symbol_counts.update(local_symbols)
        class_counts.update(local_classes)
        patient_records[patient].append(record)
        records.append({"record_id": record, "patient_id": patient, "fs": header.fs,
                        "lead_ii_index": lead_ii[0], "annotation_events": len(annotation.symbol),
                        "symbols": dict(sorted(local_symbols.items())),
                        "mapped_classes": dict(sorted(local_classes.items()))})
    if len(patient_records) != 32:
        raise ValueError(f"expected 32 patients, found {len(patient_records)}")
    return {"records": records, "patients": {str(k): v for k, v in sorted(patient_records.items())},
            "symbols": dict(sorted(symbol_counts.items())),
            "mapped_classes": dict(sorted(class_counts.items()))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--list-file", type=Path)
    args = parser.parse_args()
    xml = args.list_file.read_bytes() if args.list_file else urlopen(LIST_URL, timeout=20).read()
    items = inventory(xml)
    args.target.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(lambda item: download_one(item, args.target), items))
    result = audit(args.target)
    result.update({"source": "PhysioNet INCART 1.0.0 public AWS mirror",
                   "source_url": "https://physionet.org/content/incartdb/1.0.0/",
                   "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "files": files,
                   "metadata_bytes": sum(item["size"] for item in files)})
    (args.target / "metadata_inventory.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"files": len(files), "bytes": result["metadata_bytes"],
                      "patients": len(result["patients"]),
                      "classes": result["mapped_classes"]}, indent=2))


if __name__ == "__main__":
    main()

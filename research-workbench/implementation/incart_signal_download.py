"""Resumably download and checksum the 75 public INCART waveform files."""

import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen
from xml.etree import ElementTree

from incart_metadata_inventory import BUCKET, LIST_URL, NS, PREFIX


NAME = re.compile(r"I(?:0[1-9]|[1-6][0-9]|7[0-5])\.dat$")
MAX_TOTAL_BYTES = 850_000_000
MULTIPART_CHUNK = 8 * 1024 * 1024


def etag_matches(raw: bytes, expected: str) -> bool:
    if hashlib.md5(raw).hexdigest() == expected:
        return True
    parts = [hashlib.md5(raw[start:start + MULTIPART_CHUNK]).digest()
             for start in range(0, len(raw), MULTIPART_CHUNK)]
    multipart = hashlib.md5(b"".join(parts)).hexdigest() + f"-{len(parts)}"
    return len(parts) > 1 and multipart == expected


def inventory(xml: bytes) -> list[dict]:
    root = ElementTree.fromstring(xml)
    if root.findtext("s:IsTruncated", namespaces=NS) != "false":
        raise ValueError("S3 listing is incomplete")
    items = []
    for entry in root.findall("s:Contents", NS):
        key = entry.findtext("s:Key", namespaces=NS)
        if not key or not key.startswith(PREFIX) or not NAME.fullmatch(key.removeprefix(PREFIX)):
            continue
        items.append({"key": key, "size": int(entry.findtext("s:Size", namespaces=NS)),
                      "etag": entry.findtext("s:ETag", namespaces=NS).strip('"')})
    if len(items) != 75 or {item["key"].rsplit("/", 1)[-1] for item in items} != {
            f"I{i:02d}.dat" for i in range(1, 76)} or \
            sum(item["size"] for item in items) > MAX_TOTAL_BYTES:
        raise ValueError("unexpected INCART waveform inventory")
    return sorted(items, key=lambda item: item["key"])


def download_one(item: dict, target: Path) -> dict:
    path = target / item["key"].rsplit("/", 1)[-1]
    part = path.with_suffix(".dat.part")
    for existing in (path, part):
        if existing.exists() and existing.stat().st_size == item["size"]:
            raw = existing.read_bytes()
            if etag_matches(raw, item["etag"]):
                if existing == part:
                    part.replace(path)
                return {**item, "sha256": hashlib.sha256(raw).hexdigest()}
    sha256, size = hashlib.sha256(), 0
    with urlopen(BUCKET + "/" + quote(item["key"], safe="/"), timeout=90) as response, \
            part.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > item["size"]:
                raise ValueError(f"oversized response for {path.name}")
            output.write(chunk)
            sha256.update(chunk)
    if size != item["size"] or not etag_matches(part.read_bytes(), item["etag"]):
        raise ValueError(f"checksum or size mismatch: {path.name}")
    part.replace(path)
    return {**item, "sha256": sha256.hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    items = inventory(urlopen(LIST_URL, timeout=20).read())
    total = sum(item["size"] for item in items)
    if not args.fetch:
        print(json.dumps({"files": len(items), "bytes": total, "fetch": False}))
        return
    args.target.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        checked = list(pool.map(lambda item: download_one(item, args.target), items))
    result = {"source": "PhysioNet INCART 1.0.0 public AWS mirror",
              "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
              "files": checked, "bytes": total}
    (args.target / "signal_source_manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"files": len(checked), "bytes": total, "checksum_verified": True}))


if __name__ == "__main__":
    main()

"""Download and verify the 48 MIT-BIH raw records from PhysioNet's public S3 mirror."""

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


BUCKET = "https://physionet-open.s3.amazonaws.com"
LIST_URL = BUCKET + "/?list-type=2&prefix=mitdb/1.0.0/&max-keys=1000"
NAMESPACE = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
NAME = re.compile(r"(?:[0-9]{3}|102-0)\.(?:dat|hea|atr)$")


def inventory(xml: bytes) -> list[dict]:
    root = ElementTree.fromstring(xml)
    if root.findtext("s:IsTruncated", namespaces=NAMESPACE) != "false":
        raise ValueError("S3 listing is incomplete")
    items = []
    for item in root.findall("s:Contents", NAMESPACE):
        key = item.findtext("s:Key", namespaces=NAMESPACE)
        if not key or key.count("/") != 2 or not NAME.fullmatch(key.rsplit("/", 1)[-1]):
            continue
        items.append({
            "key": key,
            "size": int(item.findtext("s:Size", namespaces=NAMESPACE)),
            "etag": item.findtext("s:ETag", namespaces=NAMESPACE).strip('"'),
        })
    suffixes = {ext: sum(x["key"].endswith(ext) for x in items) for ext in (".dat", ".hea", ".atr")}
    if suffixes != {".dat": 48, ".hea": 48, ".atr": 49}:
        raise ValueError(f"unexpected record inventory: {suffixes}")
    return sorted(items, key=lambda x: x["key"])


def download_one(item: dict, target: Path) -> dict:
    name = item["key"].rsplit("/", 1)[-1]
    path = target / name
    temp = target / (name + ".part")
    if path.exists() and path.stat().st_size == item["size"]:
        md5 = hashlib.md5(path.read_bytes()).hexdigest()
        if md5 == item["etag"]:
            return {**item, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    md5, sha256, total = hashlib.md5(), hashlib.sha256(), 0
    with urlopen(BUCKET + "/" + quote(item["key"], safe="/"), timeout=45) as response, temp.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
            md5.update(chunk)
            sha256.update(chunk)
            total += len(chunk)
    if total != item["size"] or md5.hexdigest() != item["etag"]:
        raise ValueError(f"checksum or size mismatch: {name}")
    temp.replace(path)
    return {**item, "sha256": sha256.hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--list-file", type=Path, help="saved official S3 list XML")
    args = parser.parse_args()
    xml = args.list_file.read_bytes() if args.list_file else urlopen(LIST_URL, timeout=20).read()
    items = inventory(xml)
    args.target.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        checked = list(pool.map(lambda item: download_one(item, args.target), items))
    manifest = {
        "source": "PhysioNet MIT-BIH Arrhythmia Database 1.0.0, public AWS mirror",
        "source_url": "https://physionet.org/content/mitdb/1.0.0/",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": checked,
    }
    (args.target / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"files": len(checked), "bytes": sum(x["size"] for x in checked)}))


if __name__ == "__main__":
    main()

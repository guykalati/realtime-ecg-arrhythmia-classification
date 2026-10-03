"""Download and inspect at most 100 licensed PMC XML versions under a 250 MB cap."""

import argparse
import hashlib
import json
import random
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

from pmc_metadata_pilot import append_jsonl, read_jsonl


SEED = 20260928
BYTE_CAP = 250_000_000
BUCKET = "pmc-oa-opendata"
LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def flags(article: dict) -> list[str]:
    versions = [row["metadata"] for row in article["versions"]]
    checks = {
        "other_license_version": any(v.get("license_code") not in ("CC BY", "CC0") for v in versions),
        "retracted": any(v.get("is_retracted") is True for v in versions),
        "manuscript": any(v.get("is_manuscript") is True for v in versions),
        "missing_doi": any(not v.get("doi") for v in versions),
        "missing_pmid": any(not v.get("pmid") for v in versions),
        "multiple_versions": len(versions) > 1,
    }
    return [name for name, present in checks.items() if present]


def chosen_version(article: dict) -> dict:
    licensed = [row for row in article["versions"]
                if row["metadata"].get("license_code") in ("CC BY", "CC0")]
    if not licensed:
        raise ValueError(f"no licensed version in {article['pmcid']}")
    return max(licensed, key=lambda row: int(row["metadata"]["version"]))


def select(articles: list[dict]) -> list[dict]:
    by_id = {row["pmcid"]: row for row in articles}
    if len(by_id) != 1000:
        raise ValueError("expected 1,000 distinct metadata articles")
    eligible = sorted(pmcid for pmcid, row in by_id.items()
                      if any(v["metadata"].get("license_code") in ("CC BY", "CC0")
                             and v["metadata"].get("is_retracted") is False
                             for v in row["versions"])
                      and not any(v["metadata"].get("is_retracted") is True
                                  for v in row["versions"]))
    ordinary = sorted(random.Random(SEED).sample(eligible, 80))
    remaining = set(by_id) - set(ordinary)
    edge = []
    for flag in ("other_license_version", "retracted", "manuscript",
                 "missing_doi", "missing_pmid", "multiple_versions"):
        for pmcid in sorted(remaining):
            if len(edge) == 20:
                break
            if pmcid not in edge and flag in flags(by_id[pmcid]):
                edge.append(pmcid)
        if len(edge) == 20:
            break
    if len(edge) != 20:
        raise ValueError(f"only {len(edge)} distinct edge cases")
    manual = set(random.Random(SEED + 1).sample(ordinary, 20))
    plan = []
    for kind, ids in (("random", ordinary), ("edge", edge)):
        for pmcid in ids:
            article = by_id[pmcid]
            version = chosen_version(article)
            plan.append({"pmcid": pmcid, "month": article["month"],
                         "group": kind, "manual_review": pmcid in manual,
                         "flags": flags(article), "version": version["name"],
                         "license_code": version["metadata"]["license_code"],
                         "xml_url": version["metadata"]["xml_url"]})
    return plan


def source_url(s3_url: str, version: str) -> tuple[str, str]:
    parsed = urlsplit(s3_url)
    query = parse_qs(parsed.query)
    md5 = query.get("md5", [""])[0]
    if (parsed.scheme != "s3" or parsed.netloc != BUCKET
            or parsed.path != f"/{version}/{version}.xml"
            or not re.fullmatch(r"[0-9a-f]{32}", md5)):
        raise ValueError(f"unexpected PMC XML URL for {version}")
    return f"https://{BUCKET}.s3.amazonaws.com{parsed.path}", md5


def download(url: str, target: Path, expected_md5: str, bytes_used: int, byte_cap: int = BYTE_CAP) -> tuple[int, str]:
    if target.exists():
        digest = hashlib.md5(target.read_bytes()).hexdigest()
        if digest != expected_md5:
            raise ValueError(f"existing XML checksum mismatch: {target}")
        return target.stat().st_size, digest
    part = target.with_suffix(".part")
    for attempt in range(3):
        digest = hashlib.md5()
        size = 0
        try:
            with urlopen(Request(url, headers={"User-Agent": "GuyPortfolioXMLQualityPilot/0.1"}), timeout=30) as response:
                length = int(response.headers.get("Content-Length", "0"))
                if bytes_used + length > byte_cap:
                    raise ValueError("XML transfer cap would be exceeded")
                with part.open("wb") as handle:
                    while chunk := response.read(1024 * 1024):
                        size += len(chunk)
                        if bytes_used + size > byte_cap:
                            raise ValueError("XML transfer cap reached")
                        handle.write(chunk)
                        digest.update(chunk)
            if digest.hexdigest() != expected_md5:
                raise ValueError(f"XML MD5 mismatch: {target.name}")
            part.replace(target)
            return size, digest.hexdigest()
        except (HTTPError, URLError, TimeoutError):
            part.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
        except Exception:
            part.unlink(missing_ok=True)
            raise
    raise AssertionError("unreachable")


def words(element) -> int:
    return len(" ".join(element.itertext()).split()) if element is not None else 0


def inspect_xml(path: Path) -> dict:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return {"well_formed": False, "parse_error": str(exc)}
    if root.tag != "article":
        return {"well_formed": True, "root_tag": root.tag, "jats_article": False}
    meta = root.find("./front/article-meta")
    title = meta.find("./title-group/article-title") if meta is not None else None
    abstract = meta.find("./abstract") if meta is not None else None
    body = root.find("./body")
    section_titles = [" ".join(t.itertext()).strip() for t in root.findall("./body/sec/title")]
    return {"well_formed": True, "jats_article": True,
            "article_type": root.attrib.get("article-type"),
            "xml_lang": root.attrib.get(LANG),
            "title": " ".join(title.itertext()).strip() if title is not None else None,
            "abstract_words": words(abstract), "body_words": words(body),
            "top_level_sections": len(root.findall("./body/sec")),
            "section_titles": section_titles[:20]}


def run(metadata_file: Path, output_dir: Path) -> None:
    articles = read_jsonl(metadata_file)
    plan = select(articles)
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_file = output_dir / "sample_plan.jsonl"
    if plan_file.exists():
        if read_jsonl(plan_file) != plan:
            raise ValueError("saved XML sample plan changed")
    else:
        for row in plan:
            append_jsonl(plan_file, row)
    xml_dir = output_dir / "xml"
    xml_dir.mkdir(exist_ok=True)
    results_file = output_dir / "xml_checks.jsonl"
    rows = read_jsonl(results_file)
    seen = {row["pmcid"] for row in rows}
    bytes_used = sum(path.stat().st_size for path in xml_dir.glob("*.xml"))
    if bytes_used > BYTE_CAP:
        raise ValueError("saved XML already exceeds cap")
    for item in plan:
        if item["pmcid"] in seen:
            continue
        url, md5 = source_url(item["xml_url"], item["version"])
        target = xml_dir / f"{item['version']}.xml"
        size, digest = download(url, target, md5, bytes_used)
        bytes_used = sum(path.stat().st_size for path in xml_dir.glob("*.xml"))
        row = {"pmcid": item["pmcid"], "version": item["version"],
               "group": item["group"], "manual_review": item["manual_review"],
               "flags": item["flags"], "bytes": size, "md5": digest,
               **inspect_xml(target)}
        append_jsonl(results_file, row)
        rows.append(row)
        print(f"xml {len(rows)}/100: {item['version']} {size} bytes", flush=True)
    if len(rows) != 100 or len({row["pmcid"] for row in rows}) != 100:
        raise ValueError("XML pilot incomplete")
    (output_dir / "summary.json").write_text(json.dumps({
        "sample_size": 100, "random": 80, "targeted_edge": 20,
        "manual_review_random": 20, "selection_seed": SEED,
        "byte_cap": BYTE_CAP, "xml_bytes": bytes_used,
        "well_formed": sum(row.get("well_formed") is True for row in rows),
        "jats_article": sum(row.get("jats_article") is True for row in rows),
        "rows_with_body": sum(row.get("body_words", 0) > 0 for row in rows),
        "note": "Random quality denominator is the 80 license/retraction-clean candidate articles; 20 edge cases are reported separately.",
    }, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata_file", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    run(args.metadata_file, args.output_dir)


if __name__ == "__main__":
    main()

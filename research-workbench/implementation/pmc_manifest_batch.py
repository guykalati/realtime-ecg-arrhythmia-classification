"""Harvest completed-month PMC IDs and a bounded 1,000-article version-metadata sample."""

import argparse
import json
import random
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from pmc_inventory import month_query
from pmc_metadata_pilot import append_jsonl, esearch, metadata, read_jsonl, version_names


FIRST = "2015-01"
LAST = "2026-08"
SEED = 20260928
SAMPLE_SIZE = 1000


def months():
    for year in range(2015, 2027):
        for month in range(1, 13):
            label = f"{year}-{month:02d}"
            if FIRST <= label <= LAST:
                yield label, month_query(year, month)


def harvest_ids(path: Path) -> list[dict]:
    rows = read_jsonl(path)
    seen = {row["month"] for row in rows}
    prior_counts = {row["month"]: row["count"] for row in
                    read_jsonl(Path(__file__).with_name("pmc_month_counts_2026-09-28.jsonl"))}
    for label, term in months():
        if label in seen:
            continue
        limit = min(10000, prior_counts[label] + 100)
        for attempt in range(4):
            result = esearch(term, retmax=limit)
            if "count" in result:
                break
            if attempt == 3:
                raise ValueError(f"ESearch returned no count for {label}: {result}")
            time.sleep(5 * 2 ** attempt)
        count = int(result["count"])
        if count > limit and count <= 10000:
            limit = count
            result = esearch(term, retmax=limit)
        ids = result.get("idlist", [])
        if count > 10000 or len(ids) != count or len(set(ids)) != count:
            raise ValueError(f"incomplete or duplicate ESearch IDs for {label}: {len(ids)}/{count}")
        row = {"month": label, "query": term, "count": count, "ids": sorted(ids, key=int),
               "requested_retmax": limit,
               "queried_at_utc": datetime.now(timezone.utc).isoformat()}
        append_jsonl(path, row)
        rows.append(row)
        print(f"ids {label}: {count}", flush=True)
    if len(rows) != len(list(months())):
        raise ValueError("monthly ID manifest is incomplete")
    return sorted(rows, key=lambda row: row["month"])


def select_sample(rows: list[dict], path: Path) -> list[dict]:
    first_month = {}
    occurrences = Counter()
    for row in rows:
        for article_id in row["ids"]:
            pmcid = "PMC" + article_id
            first_month.setdefault(pmcid, row["month"])
            occurrences[pmcid] += 1
    if len(first_month) < SAMPLE_SIZE:
        raise ValueError("too few distinct candidate IDs")
    selected = sorted(random.Random(SEED).sample(sorted(first_month), SAMPLE_SIZE))
    expected = [{"pmcid": pmcid, "month": first_month[pmcid]} for pmcid in selected]
    if path.exists():
        if read_jsonl(path) != expected:
            raise ValueError("saved sample differs from the frozen seed or ID manifest")
    else:
        for row in expected:
            append_jsonl(path, row)
    return expected


def fetch_metadata(sample: list[dict], path: Path) -> list[dict]:
    rows = read_jsonl(path)
    seen = {row["pmcid"] for row in rows}
    if not seen <= {row["pmcid"] for row in sample}:
        raise ValueError("metadata checkpoint contains an ID outside the frozen sample")
    pending = [selected for selected in sample if selected["pmcid"] not in seen]

    def one_article(selected):
        pmcid = selected["pmcid"]
        versions = [{"name": name, "metadata": metadata(name)}
                    for name in version_names(pmcid)]
        return {**selected, "versions": versions,
                "fetched_at_utc": datetime.now(timezone.utc).isoformat()}

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(one_article, selected) for selected in pending]
        for future in as_completed(futures):
            row = future.result()
            append_jsonl(path, row)
            rows.append(row)
            print(f"metadata {len(rows)}/{len(sample)}: {row['pmcid']} ({len(row['versions'])} versions)", flush=True)
    return rows


def summarize(month_rows: list[dict], sample: list[dict], articles: list[dict]) -> dict:
    if (len(month_rows) != 140 or len(sample) != SAMPLE_SIZE or len(articles) != SAMPLE_SIZE
            or {row["pmcid"] for row in articles} != {row["pmcid"] for row in sample}):
        raise ValueError("incomplete monthly, sample, or metadata manifest")
    ids = [article_id for row in month_rows for article_id in row["ids"]]
    if len(ids) != sum(row["count"] for row in month_rows):
        raise ValueError("monthly ID counts and lists disagree")
    versions = [v["metadata"] for row in articles for v in row["versions"]]
    return {
        "as_of_date": "2026-09-28", "completed_months": len(month_rows),
        "first_month": FIRST, "last_month": LAST,
        "first_id_query_utc": min(row["queried_at_utc"] for row in month_rows),
        "last_id_query_utc": max(row["queried_at_utc"] for row in month_rows),
        "monthly_id_rows": len(ids), "unique_pmcids": len(set(ids)),
        "cross_month_duplicate_rows": len(ids) - len(set(ids)),
        "max_monthly_candidates": max(row["count"] for row in month_rows),
        "sample_seed": SEED, "sample_size": len(sample),
        "sample_rule": "uniform without replacement over sorted, unique completed-month PMCIDs; proportional to month volume in expectation",
        "sampled_year_counts": dict(sorted(Counter(row["month"][:4] for row in sample).items())),
        "metadata_pmcids": len(articles), "metadata_versions": len(versions),
        "version_count_per_pmcid": dict(sorted(Counter(len(row["versions"]) for row in articles).items())),
        "license_codes": dict(sorted(Counter(str(v.get("license_code")) for v in versions).items())),
        "retracted_versions": sum(v.get("is_retracted") is True for v in versions),
        "manuscript_versions": sum(v.get("is_manuscript") is True for v in versions),
        "missing_doi_versions": sum(not v.get("doi") for v in versions),
        "missing_pmid_versions": sum(not v.get("pmid") for v in versions),
        "missing_xml_versions": sum(not v.get("xml_url") for v in versions),
        "missing_text_versions": sum(not v.get("text_url") for v in versions),
        "note": "Metadata only. Article text, English status, research type, XML integrity, DOI duplicates, and benchmark overlap remain unchecked.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("stage", choices=["ids", "metadata"])
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    month_path = args.output_dir / "monthly_ids.jsonl"
    month_rows = harvest_ids(month_path)
    sample = select_sample(month_rows, args.output_dir / "sample_ids.jsonl")
    if args.stage == "metadata":
        articles = fetch_metadata(sample, args.output_dir / "sample_metadata.jsonl")
        (args.output_dir / "summary.json").write_text(
            json.dumps(summarize(month_rows, sample, articles), indent=2) + "\n",
            encoding="utf-8")


if __name__ == "__main__":
    main()

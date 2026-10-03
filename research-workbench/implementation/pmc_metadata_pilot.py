"""Resumable 120-PMCID, metadata-only PMC corpus pilot."""

import argparse
import json
import random
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pmc_inventory import month_query


EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
S3 = "https://pmc-oa-opendata.s3.amazonaws.com"
USER_AGENT = "GuyPortfolioCorpusInventory/0.2 (metadata-only academic pilot)"
_last_eutils = 0.0


def fetch(url: str, eutils: bool = False) -> bytes:
    global _last_eutils
    for attempt in range(4):
        if eutils:
            time.sleep(max(0, 0.4 - (time.monotonic() - _last_eutils)))
            _last_eutils = time.monotonic()
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=30) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def esearch(term: str, *, retmax: int, retstart: int = 0) -> dict:
    url = EUTILS + "?" + urlencode({
        "db": "pmc", "term": term, "retmode": "json",
        "retmax": retmax, "retstart": retstart,
    })
    return json.loads(fetch(url, eutils=True))["esearchresult"]


def version_names(pmcid: str) -> list[str]:
    url = S3 + "/?" + urlencode({"list-type": "2", "prefix": pmcid + ".", "delimiter": "/"})
    root = ET.fromstring(fetch(url))
    names = []
    for element in root.findall(".//{*}CommonPrefixes/{*}Prefix"):
        name = (element.text or "").rstrip("/")
        if name.startswith(pmcid + "."):
            names.append(name)
    return sorted(set(names))


def metadata(version: str) -> dict:
    if not version.startswith("PMC") or "/" in version:
        raise ValueError("invalid article version")
    return json.loads(fetch(f"{S3}/metadata/{version}.json"))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_jsonl(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()


def select_months(months: list[dict], n: int, pinned: set[str] | None = None) -> list[dict]:
    eligible = [row for row in months if row["count"] > 0]
    if len(eligible) < n:
        raise ValueError(f"only {len(eligible)} nonempty months for {n} samples")
    if n == 1:
        if pinned:
            matches = [row for row in eligible if row["month"] in pinned]
            if len(matches) != 1:
                raise ValueError("one-sample checkpoint must contain one eligible month")
            return matches
        return [eligible[len(eligible) // 2]]
    indices = [round(i * (len(eligible) - 1) / (n - 1)) for i in range(n)]
    if len(set(indices)) != n:
        raise ValueError("systematic month selection produced duplicates")
    chosen = {eligible[i]["month"]: eligible[i] for i in indices}
    pinned = pinned or set()
    available = {row["month"]: row for row in eligible}
    if not pinned <= available.keys():
        raise ValueError("checkpoint includes a month outside the approved sampling window")
    for month in sorted(pinned - chosen.keys()):
        year = month[:4]
        replace = min((key for key in chosen if key[:4] == year and key not in pinned),
                      key=lambda key: abs(int(key[5:]) - int(month[5:])))
        del chosen[replace]
        chosen[month] = available[month]
    return [chosen[key] for key in sorted(chosen)]


def count_months(path: Path) -> list[dict]:
    existing = read_jsonl(path)
    seen = {row["month"] for row in existing}
    for year in range(2015, 2027):
        for month in range(1, 13):
            label = f"{year}-{month:02d}"
            if label in seen:
                continue
            term = month_query(year, month)
            result = esearch(term, retmax=0)
            row = {"month": label, "query": term, "count": int(result["count"]),
                   "queried_at_utc": datetime.now(timezone.utc).isoformat()}
            append_jsonl(path, row)
            existing.append(row)
            print(f"count {label}: {row['count']}", flush=True)
    return sorted(existing, key=lambda row: row["month"])


def sample_metadata(months: list[dict], path: Path, *, seed: int = 20260928) -> list[dict]:
    existing = read_jsonl(path)
    seen = {row["month"] for row in existing}
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    complete_months = [row for row in months if row["month"] < current_month]
    selected = select_months(complete_months, 120, pinned=seen)
    for month in selected:
        label = month["month"]
        if label in seen:
            continue
        offset = random.Random(f"{seed}:{label}").randrange(month["count"])
        result = esearch(month["query"], retmax=1, retstart=offset)
        ids = result.get("idlist", [])
        if len(ids) != 1:
            raise ValueError(f"candidate list changed for {label} at offset {offset}")
        pmcid = "PMC" + ids[0]
        versions = [{"name": name, "metadata": metadata(name)}
                    for name in version_names(pmcid)]
        row = {"month": label, "month_candidate_count": month["count"],
               "selected_offset": offset, "pmcid": pmcid, "versions": versions,
               "fetched_at_utc": datetime.now(timezone.utc).isoformat()}
        append_jsonl(path, row)
        existing.append(row)
        print(f"metadata {label}: {pmcid} ({len(versions)} versions)", flush=True)
    return sorted(existing, key=lambda row: row["month"])


def summarize(months: list[dict], samples: list[dict], seed: int) -> dict:
    all_versions = [v["metadata"] for row in samples for v in row["versions"]]
    licenses = Counter(str(v.get("license_code")) for v in all_versions)
    sampled_months = [row["month"] for row in samples]
    return {
        "sampled_pmcids": len(samples),
        "distinct_sampled_pmcids": len({row["pmcid"] for row in samples}),
        "sampled_versions": len(all_versions),
        "seed": seed,
        "latest_sampled_month": max(sampled_months),
        "sampled_year_counts": dict(sorted(Counter(month[:4] for month in sampled_months).items())),
        "nonempty_months": sum(row["count"] > 0 for row in months),
        "sampling_rule": "120 evenly spread completed publication months; prior checkpoint months retained",
        "sum_monthly_candidate_counts": sum(row["count"] for row in months),
        "no_version_pmcids": sum(not row["versions"] for row in samples),
        "license_codes": dict(sorted(licenses.items())),
        "retracted_versions": sum(str(v.get("is_retracted", "")).lower() in {"yes", "true", "1"} for v in all_versions),
        "manuscript_versions": sum(str(v.get("is_manuscript", "")).lower() in {"yes", "true", "1"} for v in all_versions),
        "missing_doi_versions": sum(not v.get("doi") for v in all_versions),
        "missing_pmid_versions": sum(not v.get("pmid") for v in all_versions),
        "missing_xml_versions": sum(not v.get("xml_url") for v in all_versions),
        "missing_text_versions": sum(not v.get("text_url") for v in all_versions),
        "note": "Metadata pilot only; no full text or eligibility audit.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--seed", type=int, default=20260928)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    months_file = args.output_dir / "monthly_counts.jsonl"
    samples_file = args.output_dir / "sample_metadata.jsonl"
    months = count_months(months_file)
    samples = sample_metadata(months, samples_file, seed=args.seed)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summarize(months, samples, args.seed), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

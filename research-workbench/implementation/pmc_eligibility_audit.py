"""Audit article/version eligibility in the frozen PMC sample without bulk download."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


LICENSES = {"CC BY", "CC0"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def version_gate(article: dict) -> dict:
    versions = [row["metadata"] for row in article["versions"]]
    if any(version.get("is_retracted") is True for version in versions):
        return {"pmcid": article["pmcid"], "status": "exclude_retracted"}
    licensed = [version for version in versions
                if version.get("license_code") in LICENSES and
                version.get("is_retracted") is False and version.get("xml_url")]
    if not licensed:
        return {"pmcid": article["pmcid"], "status": "exclude_no_licensed_xml"}
    chosen = max(licensed, key=lambda version: int(version["version"]))
    return {"pmcid": article["pmcid"], "status": "version_candidate",
            "version": f'{article["pmcid"]}.{chosen["version"]}',
            "license_code": chosen["license_code"], "doi": chosen.get("doi"),
            "pmid": chosen.get("pmid"), "is_manuscript": chosen.get("is_manuscript"),
            "article_version_pmids": sorted({str(v["pmid"]) for v in versions if v.get("pmid")}),
            "title": chosen.get("title"),
            "has_other_license_version": any(version.get("license_code") not in LICENSES
                                             for version in versions)}


def benchmark_gate(pmid, excluded_pmids: set[str] | None, other_version_pmids=()) -> str:
    if excluded_pmids is None:
        return "unchecked"
    if {str(value) for value in other_version_pmids} & excluded_pmids or str(pmid) in excluded_pmids:
        return "exact_pmid_match"
    if pmid is None or not str(pmid).strip():
        return "pmid_missing"
    return "no_exact_pmid_match"


def audit(metadata: list[dict], checks: list[dict], labels: list[dict],
          excluded_pmids: set[str] | None = None, tiers: dict | None = None) -> tuple[list[dict], dict]:
    if len(metadata) != 1000 or len({row["pmcid"] for row in metadata}) != 1000:
        raise ValueError("expected frozen 1,000 distinct metadata articles")
    rows = [version_gate(article) for article in metadata]
    dois = defaultdict(list)
    for row in rows:
        if row["status"] == "version_candidate" and row["doi"]:
            dois[row["doi"].lower().strip()].append(row["pmcid"])
    by_id = {row["pmcid"]: row for row in rows}
    for row in rows:
        if row["status"] == "version_candidate":
            row["doi_duplicate_in_sample"] = len(dois[row["doi"].lower().strip()]) > 1 if row["doi"] else None
            row["benchmark_overlap"] = benchmark_gate(row["pmid"], excluded_pmids, row["article_version_pmids"])
            row["near_duplicate_overlap"] = "unchecked"
            if row["benchmark_overlap"] == "exact_pmid_match":
                row["status"] = "exclude_benchmark_exact_pmid"
            row["topical_centrality"] = "unchecked"
            row["document_type"] = "unchecked"
    for check in checks:
        row = by_id[check["pmcid"]]
        if row["status"] != "version_candidate":
            continue
        if check["version"] != row["version"]:
            row["xml_review_status"] = "different_version_downloaded"
            continue
        row["xml_review_status"] = "verified" if check["well_formed"] and check["jats_article"] else "invalid"
        row["article_type"] = check["article_type"]
        row["body_words"] = check["body_words"]
        row["structural_queue"] = (row["xml_review_status"] == "verified" and
                                    check["article_type"] == "research-article" and
                                    check["body_words"] >= 1000)
    for label in labels:
        row = by_id[label["pmcid"]]
        row["manual_centrality"] = label["cardiovascular_relevance"]
        row["manual_original_research_candidate"] = label["strict_original_research_candidate"]
        if tiers and label["pmcid"] in tiers:
            row.update(tiers[label["pmcid"]])
    for row in rows:
        row["primary_fulltext_review_queue"] = (
            row["status"] == "version_candidate" and
            row.get("manual_original_research_candidate") is True and
            row.get("study_tier") == "human_clinical_empirical" and
            row.get("xml_review_status") == "verified" and row.get("body_words", 0) > 0 and
            row.get("benchmark_overlap") == "no_exact_pmid_match" and
            row.get("doi_duplicate_in_sample") is False)
    reviewed = [row for row in rows if "manual_original_research_candidate" in row]
    confusion = Counter((row.get("structural_queue", False),
                         row["manual_original_research_candidate"]) for row in reviewed)
    summary = {
        "sample_articles": len(rows),
        "version_status": dict(Counter(row["status"] for row in rows)),
        "chosen_license": dict(Counter(row["license_code"] for row in rows
                                      if row["status"] == "version_candidate")),
        "missing_doi_chosen_version": sum(row["status"] == "version_candidate" and not row["doi"]
                                          for row in rows),
        "duplicate_doi_article_rows": sum(row.get("doi_duplicate_in_sample") is True for row in rows),
        "xml_checked": sum("xml_review_status" in row for row in rows),
        "structural_queue_in_random_xml": sum(row.get("structural_queue") is True
                                               for row in rows if any(check["pmcid"] == row["pmcid"] and
                                                                       check["group"] == "random" for check in checks)),
        "manual_reviewed": len(reviewed),
        "manual_structural_confusion": {
            "queue_and_eligible": confusion[(True, True)],
            "queue_but_ineligible": confusion[(True, False)],
            "not_queued_but_eligible": confusion[(False, True)],
            "not_queued_and_ineligible": confusion[(False, False)],
        },
        "benchmark_overlap": dict(Counter(row.get("benchmark_overlap", "not_version_candidate") for row in rows)),
        "original_candidate_study_tiers": dict(Counter(row.get("study_tier", "unchecked") for row in reviewed
                                                      if row["manual_original_research_candidate"])),
        "primary_fulltext_review_queue": sum(row["primary_fulltext_review_queue"] for row in rows),
        "note": "Queues are triage, not training eligibility. Exact PMID screening does not check DOI or text near-duplicates.",
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("checks", type=Path)
    parser.add_argument("labels", type=Path)
    parser.add_argument("output_prefix", type=Path)
    parser.add_argument("--extra-labels", type=Path, action="append", default=[])
    parser.add_argument("--benchmark-exclusion", type=Path)
    parser.add_argument("--study-tiers", type=Path)
    args = parser.parse_args()
    labels = read_jsonl(args.labels)
    for path in args.extra_labels:
        labels.extend(read_jsonl(path))
    if len({row["pmcid"] for row in labels}) != len(labels):
        raise ValueError("duplicate manual labels")
    benchmark = json.loads(args.benchmark_exclusion.read_text()) if args.benchmark_exclusion else None
    excluded = set(benchmark["pmids"]) if benchmark else None
    tiers = json.loads(args.study_tiers.read_text()) if args.study_tiers else None
    rows, summary = audit(read_jsonl(args.metadata), read_jsonl(args.checks),
                          labels, excluded, tiers)
    if benchmark:
        summary["benchmark_source"] = {key: value for key, value in benchmark.items() if key != "pmids"}
    args.output_prefix.with_suffix(".jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows))
    args.output_prefix.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

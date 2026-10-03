"""Count candidate PMC articles without downloading article text."""

import argparse
import calendar
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def query(start_year: int, end_year: int) -> str:
    if start_year > end_year:
        raise ValueError("start year must not exceed end year")
    return query_dates(f"{start_year}/01/01", f"{end_year}/12/31")


def query_dates(start_date: str, end_date: str) -> str:
    license_filter = '("cc0 license"[filter] OR "cc by license"[filter])'
    topic = '(cardiovascular[tiab] OR cardiac[tiab] OR electrocardiogram[tiab] OR arrhythmia[tiab])'
    return f'{license_filter} AND {topic} AND {start_date}:{end_date}[pubdate] NOT "pmc embargo"[filter]'


def month_query(year: int, month: int) -> str:
    if not 1 <= month <= 12:
        raise ValueError("month must be 1..12")
    last_day = calendar.monthrange(year, month)[1]
    return query_dates(f"{year}/{month:02d}/01", f"{year}/{month:02d}/{last_day}")


def count_url(term: str) -> str:
    params = {"db": "pmc", "term": term, "retmax": 0, "retmode": "json"}
    return "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode(params)


def fetch_count(url: str) -> int:
    request = Request(url, headers={"User-Agent": "GuyPortfolioCorpusInventory/0.1"})
    with urlopen(request, timeout=20) as response:
        data = json.load(response)
    return int(data["esearchresult"]["count"])


def yearly_counts(start_year: int, end_year: int) -> dict[str, int]:
    counts = {}
    for year in range(start_year, end_year + 1):
        counts[str(year)] = fetch_count(count_url(query(year, year)))
        if year < end_year:
            time.sleep(0.4)  # Keep count requests below NCBI's unauthenticated rate limit.
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--fetch", action="store_true", help="make one official E-utilities count request")
    parser.add_argument("--fetch-years", action="store_true",
                        help="count each publication year; no article IDs or text downloaded")
    args = parser.parse_args()
    if args.fetch and args.fetch_years:
        parser.error("choose --fetch or --fetch-years")
    term = query(args.start_year, args.end_year)
    url = count_url(term)
    report = {
        "queried_at_utc": datetime.now(timezone.utc).isoformat(),
        "query": term,
        "url": url,
        "candidate_count": fetch_count(url) if args.fetch else None,
        "note": "Search count only. Eligibility requires per-article version/license and quality checks.",
    }
    if args.fetch_years:
        report["yearly_candidate_counts"] = yearly_counts(args.start_year, args.end_year)
        report["sum_of_yearly_counts"] = sum(report["yearly_candidate_counts"].values())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

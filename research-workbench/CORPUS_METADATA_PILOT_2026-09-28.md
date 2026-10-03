# Project 1: completed PMC metadata pilot — 28 September 2026

## What this establishes

The cardiovascular search is large enough to justify building a real corpus, and the official PMC cloud metadata path works. It does **not** yet establish how many articles pass our language, research type, duplicate, XML quality, and benchmark exclusion rules. No article text or model weights were fetched.

The [resumable pilot script](implementation/pmc_metadata_pilot.py) counted each publication month from January 2015 through December 2026 and sampled one candidate in each of 120 evenly spread **completed, nonempty** months. The recorded seed is `20260928`. Nineteen months already fetched during the first checkpoint were retained; two replaced nearby selected months in the same year after the sampling window was corrected to exclude the current and future months. The latest sampled month is August 2026. The [month counts](implementation/pmc_month_counts_2026-09-28.jsonl), [article-version metadata](implementation/pmc_metadata_pilot_2026-09-28.jsonl), and [machine summary](implementation/pmc_metadata_pilot_summary_2026-09-28.json) preserve the actual query and selected offset for each month.

## Measured results

| Check | Result |
| --- | ---: |
| Distinct sampled PMCIDs | 120 |
| Official article versions found | 122 |
| PMCIDs with two versions | 2 |
| Versions whose metadata says CC BY | 122 |
| Versions marked retracted | 0 |
| Versions marked author manuscript | 1 |
| Versions missing DOI / PMID | 0 / 2 |
| Versions missing XML / text URL | 0 / 0 |
| PMCIDs with no version found | 0 |

The 120 sampled articles span every year in 2015–2026, with 7–11 article picks per year. That is a deliberate **month-balanced** sample, not a random sample proportional to publication volume. The observed 0 retractions does not mean the full corpus has none: even under an independent random sample assumption, a zero in 122 versions would still permit roughly 2–3% prevalence at a 95% upper bound. This sample does not support a precise total-eligibility estimate. The `CC BY` result may also reflect how the live ESearch license filter and this month-balanced selection interact; every retrieved version still needs its own license check.

The broad query returned 201,510 candidate records on 27 September and 201,531 on 28 September. The 144 monthly counts on the latter date sum to 201,531, matching a fresh [broad count](implementation/pmc_count_2026-09-28.json). Published-date indexing moves between days: 200,177 of the latter count lie in **completed months through August 2026**, 1,328 in September, and 26 in October–November dates ahead of the check date. A full manifest should freeze a query date and explicitly exclude future-dated/current-month records. No monthly count exceeded 2,822, below the [ESearch 10,000 returned-ID cap](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/).

The saved 120-row version-metadata JSONL is 176,338 bytes, about 1.47 KB per sampled article. Scaling that average to 200,177 candidate records suggests roughly 294 MB for a similarly compact JSONL, before indexing, duplicates, richer audit fields, and article text. This is a **metadata-only order-of-magnitude estimate**, not an XML storage or GPU budget.

## Next bounded decision

First freeze the completed-month ID manifest (January 2015–August 2026): at most 140 monthly ESearch ID requests, each under the cap; deduplicate PMCIDs and record query/result timestamps. From those unique IDs, sample 1,000 article IDs proportional to monthly candidate counts with a fixed seed, retrieve every version's official JSON metadata, and manually inspect a small, separately specified relevance/quality sample before any full-text bulk download. Budget: about 2,000–3,000 S3 metadata/list requests plus the ESearch requests, tens of MB locally, CPU only, likely under a few hours at polite request rates; actual service latency and version multiplicity may change this. This improves the eligibility estimate and exposes year/volume effects. A cheaper alternative is to stop at the 120-item pilot, accepting that eligibility and text volume remain poorly known.

That next batch needs a separate approval under the agreed project gate. Later steps must remove retractions/corrections, nonresearch and non-English items, duplicate article versions/DOIs, broken XML, and overlap with the sealed PubMedQA evaluation set before text ingestion or model training. The [PMC AWS metadata guide](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/) and [official bucket README](https://pmc-oa-opendata.s3.amazonaws.com/README.txt) define the per-version fields and checksums used here.

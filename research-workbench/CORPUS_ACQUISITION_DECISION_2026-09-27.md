# Biomedical corpus acquisition decision

The mission is article-grounded cardiovascular literature question answering, not clinical advice. This brief defines the next metadata-only gate before article download or model training.

## Evidence available now

The official ESearch [count query](implementation/pmc_count_2026-09-27.json) returns 201,510 **candidate PMC records** for 2015–2026, CC0/CC BY, and cardiovascular/cardiac/electrocardiogram/arrhythmia in title or abstract. [Count-only year queries](implementation/pmc_year_counts_2026-09-27.json) sum to exactly the same number. Each year from 2019 through 2026 exceeds ESearch's 10,000 returned-ID cap, so year-only ID harvesting would be incomplete. These counts do not establish English language, article type, a usable JATS XML file, stable DOI, nonretraction, distinct article versions, or absence of benchmark overlap.

The [current PMC AWS guide](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/) says to inspect the JSON metadata for each article **version**. The [official bucket README](https://pmc-oa-opendata.s3.amazonaws.com/README.txt) lists `license_code`, `is_retracted`, `is_manuscript`, DOI, PMID, PMCID, XML/text URLs, and object MD5s. The AWS daily inventory can detect removed or updated versions. A search filter alone must not be treated as a version's license.

## Proposed first bounded batch

1. Divide each of the 12 publication years into monthly ESearch queries, count each month, and verify that each returned-ID query is below 10,000. Check de-duplication across month boundaries because date metadata can be revised.
2. Select a deterministic **120-PMCID metadata pilot** across 120 evenly spread, nonempty **completed** year-month cells (there are up to 144 months in the broad date range). Choose one candidate ID in each selected month using a recorded seed and offset from that month's result list. The current and future publication months are excluded from sampling because their dates can be incomplete or ahead of today's date. Fetch only the official per-version JSON metadata; do not download full text. If a PMCID has multiple versions, record every version's metadata in the pilot rather than assuming `.1` is preferred. Thus 120 PMCIDs may yield more than 120 article versions.
3. Report actual rates for CC0/CC BY versions, retractions, manuscript status, missing DOI/PMID, text/XML availability, and multiple versions. Report sample uncertainty and year variation. This pilot tests the retrieval and manifest logic; it is far too small to estimate the final eligible count precisely or judge scientific relevance.
4. Use those measurements to propose the complete ID/metadata manifest, a text-storage estimate, and a capped eligible article count (planning ceiling 100,000) before bulk XML/text retrieval. Keep the publication date, article/version IDs, license, source checksum, and retraction state in every manifest row. Later exclude PubMedQA test items and near duplicates before training/evaluation partitions.

**Resource estimate.** The first batch is up to 144 ESearch count requests, 120 one-ID ESearch requests, 120 S3 version listings, and at least 120 per-version JSON metadata requests. Expected network transfer is small compared with article text, likely minutes to an hour depending on service latency. The exact request count can rise if a PMCID has multiple versions. CPU/storage should be modest (likely well below 100 MB). No GPU is needed. The estimate will be measured and logged.

**Alternatives.** The daily AWS inventory is more complete but spans roughly eight million article versions and is oversized for the Mac's present 16 GiB free space. A one-year pilot is cheaper but misses date drift and versioning differences. Broadening beyond cardiovascular literature or changing license scope is a separate method decision.

**Outcome (28 September).** Guy approved the metadata pilot, and it completed: 120 distinct PMCIDs, 122 article versions, all with a reported CC BY license in this month-balanced sample. The [pilot report](CORPUS_METADATA_PILOT_2026-09-28.md) records the live count drift, missingness, uncertainty, and next bounded decision. No article text or model weights were downloaded. The larger ID/metadata harvest in that report requires its own approval.

**Second approved outcome (28 September).** The [full completed-month ID manifest and 1,000-article metadata check](CORPUS_MANIFEST_RESULT_2026-09-28.md) are complete: 200,177 unique candidate PMCIDs, 1,020 article versions in the sample, seven versions with TDM/missing license, and four retracted articles. The report sets the next XML quality gate. The earlier 120-item pilot's all-CC-BY observation did not generalize to every version.

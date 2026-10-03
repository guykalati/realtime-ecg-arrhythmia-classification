# Project 1: completed PMC ID manifest and 1,000-article metadata check

## Plain-language result

The chosen search yields a **large candidate pool**: 200,177 distinct PMCIDs in completed publication months from January 2015 through August 2026. A reproducible random sample of 1,000 articles confirmed that per-version licensing and retraction checks are necessary. This is still a **candidate pool**, not a verified English cardiovascular research corpus: article type, language, topical relevance, XML integrity, duplicate text, and evaluation-set overlap are not yet checked.

The [harvester](implementation/pmc_manifest_batch.py) saved the exact [monthly ID responses](implementation/pmc_monthly_ids_2026-09-28.jsonl), [frozen 1,000-ID sample](implementation/pmc_sample_ids_2026-09-28.jsonl), [official per-version metadata](implementation/pmc_metadata_1000_2026-09-28.jsonl), and [machine summary](implementation/pmc_manifest_summary_2026-09-28.json). It used the [same official ESearch query](implementation/pmc_inventory.py) as the pilot and the [PMC cloud metadata service](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/). The 140 monthly searches were made across 28 September, not from a transactional index snapshot; each row records its query time. Every month returned its full ID count, with a maximum of 2,822 below the 10,000-ID ESearch cap. The 200,177 total matches the earlier completed-month count; there were **no cross-month duplicate IDs**.

The 1,000 PMCIDs were sampled without replacement from the sorted unique ID manifest using seed `20260928`. This gives heavier publication months proportionally more sampling chance, unlike the earlier 120-month retrieval-path pilot. The sample has 37 articles from 2015 and 95 from January–August 2026; its full year distribution is in the summary. The 1,000 metadata requests found **1,020 versions**: 980 articles with one version and 20 with two. No article text was downloaded, and no GPU was used for the corpus work.

## Metadata findings

| Field | Versions (out of 1,020) | Distinct sampled PMCIDs (out of 1,000) |
| --- | ---: | ---: |
| `license_code = CC BY` | 1,013 | 1,000 have at least one CC BY version |
| `license_code = TDM` or missing | 7 | 7 |
| Marked retracted | 4 | 4 |
| Marked author manuscript | 9 | 9 |
| Missing DOI | 5 | 5 |
| Missing PMID | 15 | 15 |
| Missing XML or text URL | 0 | 0 |

All seven non-CC-BY versions belong to articles with a separate CC BY version. Several have the non-CC-BY status on the **newer** version. Selecting the latest version, or assuming the ESearch license filter applies to every version, would therefore be wrong. Four articles have retracted versions; they should be excluded at article level, including earlier versions, until the retraction relationship is resolved. The sample had no duplicate DOI across different PMCIDs, which does not establish that the full manifest is DOI-disjoint. A URL field's presence does not prove the XML is well formed or complete.

The article-level observed proportions were 7/1,000 with a non-CC-BY version and 4/1,000 with a retracted version. Approximate 95% Wilson intervals are **0.34–1.44%** and **0.16–1.02%**, respectively, for these metadata conditions in the frozen candidate pool. These are uncertainty ranges for the sampled search population, not estimates of a fully eligible corpus. **996/1,000** sampled articles have at least one CC BY, nonretracted version; this says nothing yet about language, document type, or scientific relevance. All 1,020 versions had an XML and a text URL in metadata, but their bytes were not fetched or validated.

The broad title-or-abstract query admits material that is not clearly the intended cardiovascular research article. Only 334/1,000 sampled article titles literally contain one of the four query words; that is a string check, **not a relevance label**, because many relevant papers use synonyms or mention the topic only in the abstract. A few sampled titles are plainly about unrelated psychiatric, infectious-disease, or behavioral topics. Several missing-PMID items appear to be meeting abstracts or case reports. An XML/article-type audit is needed before claiming the corpus is “big and good.”

## Next bounded quality gate

Before bulk XML download or training, inspect a **100-article XML pilot** drawn from this frozen 1,000: 80 randomly selected articles with a CC BY, nonretracted version to estimate extraction quality and topical/document-type noise, plus up to 20 separately reported edge cases (multiple versions, manuscript, missing identifiers, and retractions) to test exclusion logic. Fetch at most one selected licensed version per ordinary article; retain all version metadata. Cap XML transfer and local storage at **250 MB**, stop if the cap is reached, and run no GPU job. Parse JATS language, article type, title/abstract/section structure, XML well-formedness, and available size/checksum fields; inspect a smaller human-readable sample with explicit criteria. The targeted edge cases are **not** part of the random quality-rate denominator. Expected elapsed time is under a few hours, subject to service latency and XML size. The cheaper alternative is to use metadata/title checks alone, which cannot establish full-text quality.

**Completion update, 28 September:** Guy approved this bounded XML pilot, and it completed. The [100-article result](CORPUS_XML_PILOT_RESULT_2026-09-28.md) includes structural checks and manual relevance screening. A full 200,177-ID version-metadata sweep and any 100,000-article training cap still require their own design decision. Keep PubMedQA evaluation PMIDs/PMCIDs and close text matches out of training.

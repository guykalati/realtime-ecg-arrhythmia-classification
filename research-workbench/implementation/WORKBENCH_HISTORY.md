# Runnable foundations for the three new personal projects

Latest: [30 September offline progress](../OFFLINE_PROGRESS_2026-09-30.md). The later [ECG checkpoint-selection result](../ECG_SELECTION_RESULT_2026-09-30.md) and [model-proposed experiment pilot](../AUTORESEARCH_AGENT_PILOT_RESULT_2026-09-30.md) are verified; both produced mixed or negative improvement evidence. The frozen larger corpus acquisition completed with 977 verified documents and four excluded checksum failures; both larger GPU batches have now been retrieved and verified. See [language-model results](../AUTORESEARCH_LONGER_RESULT_2026-09-30.md) and [ECG results](../ECG_LONGER_RESULT_2026-09-30.md).

These tools and capped experiments are new work. They preserve source, split, and evaluator provenance before larger training or claims.

## Project 1: corpus inventory

`pmc_inventory.py` builds a query for CC0/CC BY cardiovascular articles and, with `--fetch`, asks official [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/) for a **count only**. The default prints the request without network access:

```bash
python3 pmc_inventory.py
python3 pmc_inventory.py --fetch
python3 pmc_inventory.py --fetch-years
```

The returned count is candidates, not a verified corpus. [PMC requires per-version license checks](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/); a later manifest must also remove retractions, nonresearch items, duplicates, and benchmark overlap. The bounded XML quality pilot below downloaded 100 articles; no corpus training has run.

The first live count-only query on **27 September 2026** returned **201,510 candidates** for CC0/CC BY, publication years 2015–2026, and `cardiovascular`, `cardiac`, `electrocardiogram`, or `arrhythmia` in the [title or abstract](https://pmc.ncbi.nlm.nih.gov/about/userguide/). An earlier unrestricted topic search returned 1,496,312 because it was too broad; it is discarded. Neither number is the final eligible full-text count. The exact query is emitted by `pmc_inventory.py`.

The [yearly count output](pmc_year_counts_2026-09-27.json) sums to the same 201,510. Every publication year from 2019 onward exceeds the [10,000 ESearch returned-ID cap](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/), so a complete ID harvest will require smaller date queries or the official AWS inventory. [PMC's current dataset README](https://pmc-oa-opendata.s3.amazonaws.com/README.txt) lists the per-version JSON fields needed to check license, retraction, source type, DOI, and text/XML checksums.

The approved `pmc_metadata_pilot.py` then counted all 144 year-month cells and sampled 120 distinct PMCIDs from 120 completed months using seed `20260928`. Its [month counts](pmc_month_counts_2026-09-28.jsonl), [version metadata](pmc_metadata_pilot_2026-09-28.jsonl), and [summary](pmc_metadata_pilot_summary_2026-09-28.json) are reproducible artifacts. The same-day broad and monthly query totals match at 201,531; the difference from 27 September shows live index drift. The [pilot report](../CORPUS_METADATA_PILOT_2026-09-28.md) explains the 122 versions and remaining eligibility uncertainty. To resume or refresh this specific pilot, use `python3 pmc_metadata_pilot.py data/pmc_pilot_2026-09-28` only with the original checkpoint directory; a new date creates a different live search snapshot.

The second approved batch used `pmc_manifest_batch.py`: [140 completed-month ID rows](pmc_monthly_ids_2026-09-28.jsonl) yielded 200,177 unique PMCIDs, and a [frozen 1,000-ID sample](pmc_sample_ids_2026-09-28.jsonl) yielded [1,000 article rows containing 1,020 per-version JSON metadata objects](pmc_metadata_1000_2026-09-28.jsonl). The [machine summary](pmc_manifest_summary_2026-09-28.json) and [result interpretation](../CORPUS_MANIFEST_RESULT_2026-09-28.md) show why per-version licensing and article-level retraction checks are essential. The resumable commands are `python3 pmc_manifest_batch.py data/pmc_manifest_2026-09-28 ids` and `python3 pmc_manifest_batch.py data/pmc_manifest_2026-09-28 metadata`; only rerun against this frozen checkpoint for verification, since a fresh ESearch changes over time.

The later approved [100-article XML pilot](../CORPUS_XML_PILOT_RESULT_2026-09-28.md) retrieved and checksum-verified 100 JATS files. It found substantial document-type and topical noise; downloaded XML remains in ignored local data storage, while the plan, structural checks, and manual labels are saved here.

The subsequent [frozen-sample eligibility audit](../PMC_ELIGIBILITY_AUDIT_RESULT_2026-09-29.md) records exact licensed versions and article-level retraction decisions for the 1,000 metadata rows. Its provisional research-document queue admitted six ineligible articles among 20 previously manually reviewed items, so it is triage rather than a final training filter. This step downloaded no new text.

The [expanded qualitative screen](../PMC_MANUAL_EXPANSION_RESULT_2026-09-29.md) reviewed 20 more frozen random XML articles, bringing the development check to 40. The provisional structural queue has 14 original-study candidates, nine noneligible articles, and two missed original studies in that screened set. The labels are one agent's screen, not expert-adjudicated training eligibility.

The [study-scope and benchmark audit](../PMC_SCOPE_AND_BENCHMARK_RESULT_2026-09-29.md) now excludes exact matches to all 1,000 official PubMedQA expert article IDs across known article versions. In the frozen metadata sample, 981 licensed candidates have no exact PMID match, 15 lack a PMID, and four are retracted. The 16 screened original candidates carry explicit study tiers, including six human clinical articles in a full-text review queue. DOI/text overlap and final training eligibility remain unresolved.

## Project 2: repository evidence retrieval

`repo_evidence.py` builds a local SQLite FTS5 index over `.py`, `.md`, `.toml`, and `.txt` files. It skips hidden files, result directories, traces, data, symlinks, and files over 200 KB. Search returns source paths and starting lines so an agent can inspect evidence instead of treating a search snippet as proof.

```bash
python3 repo_evidence.py index /path/to/approved/repo /path/to/index.db
python3 repo_evidence.py search /path/to/index.db 'validation metric'
```

This is the retrieval baseline. A bounded repair-agent comparison and a first [autoresearch-style training run](../AUTORESEARCH_FIRST_RUN_RESULT_2026-09-29.md) now exist below. The workflow combines an isolated patch/test loop with the [upstream `autoresearch`](https://github.com/karpathy/autoresearch) fixed-evaluation experiment contract. Hidden benchmark answers must stay outside the indexed root. The 50-line search windows are an initial engineering setting, not an evaluated optimum.

The reference upstream source inspected on 27 September 2026 is commit `228791fb499afffb54b46200aca536f79142f117` (MIT license). The current Mac has about 16 GiB free; the Docker CLI is present but its daemon was not running during the read-only check. The official SWE-bench Docker guide calls for at least 120 GB free, so its full harness needs a different host/storage budget.

The [repair harness screen](../REPAIR_HARNESS_SCREEN_RESULT_2026-09-28.md) subsequently verified Bubblewrap isolation on a cluster CPU node and reproduced two PySnooper buggy-fail/fixed-pass pairs with Python 3.8.1. [Case preparation](prepare_pysnooper_cases.py) keeps buggy implementation bytes separate from fixed tests and evaluator trees; [sandbox jobs](run_repair_case_screen.sbatch) run without network or home access. The initially proposed PySnooper case 1 passed on both revisions and is excluded. After SSH returned, two capped Python 3.6.9 setup jobs for the replacement tqdm case timed out in conda verification. A separately labeled Python 3.8.1 exploratory screen did reproduce tqdm case 3's buggy-fail/fixed-pass behavior. This is a modified runtime, not the exact BugsInPy setup.

The [agent comparison contract](../REPAIR_AGENT_COMPARISON_CONTRACT_2026-09-28.md) records the two exact-runtime PySnooper cases plus one modified-runtime tqdm case, retrieval feasibility probe, proposed comparison budget, evaluation metrics, and the agent access boundary. The current Bubblewrap evidence applies to test execution, not to a model process launched from the local Codex CLI.

The [candidate gateway](repair_gateway.py) now exposes bounded file listing/reading and one-match implementation edits without giving the model a shell. [The agent driver](repair_agent.py) defines four function tools with either [OpenAI Responses function calling](https://developers.openai.com/api/docs/guides/function-calling) or [Ollama tool calling](https://github.com/ollama/ollama/blob/main/docs/capabilities/tool-calling.mdx). The OpenAI mode keeps a separate API key in the local controller; no such key is configured on this Mac. [The evaluator bridge](repair_eval_bridge.py) accepts only a fixed case and `target`/`regression` selector, copies the candidate into a private remote run, and executes [a fixed Slurm script](run_repair_candidate_eval.sbatch) inside Bubblewrap. A live integration check on the unchanged tqdm buggy tree, [job 21727533](repair_gateway_smoke_2026-09-29), returned the expected `test_bool` TypeError and exit code 1. The [local-model development smoke](../REPAIR_AGENT_LOCAL_SMOKE_2026-09-29.md) diagnosed the edit-format failure. After a narrow fix, the [first passing PySnooper attempt](../REPAIR_AGENT_FIRST_SUCCESS_2026-09-29.md) and [four-attempt matched comparison](../REPAIR_AGENT_MATCHED_RESULT_2026-09-29.md) showed both hint arms solve case 3 and neither solve case 2. The command `python3 -m unittest -q test_repair_agent.py test_repair_gateway.py test_foundations.py` passes 23 checks. This is feasibility evidence, not a retrieval-effect estimate.

`experiment_ledger.py` implements the fixed-contract record for the experiment mode: it hashes `prepare.py` and the data manifest, pins metric/direction and a finite run count, rejects changed frozen files, and records candidate hashes and results. `program.md` specifies the two agent modes. For a prepared, **approved** experiment directory:

```bash
python3 experiment_ledger.py init /path/to/experiment --prepare prepare.py --data-manifest data.json --metric val_loss --direction min --max-runs 3 --max-seconds 300
python3 experiment_ledger.py record /path/to/experiment /path/to/run_result.json
python3 experiment_ledger.py summary /path/to/experiment
```

`run_result.json` needs `status` (`success` or `failed`), `training_seconds`, and `metric_value` for success. For an isolated candidate, it may also specify a path to a `train.py` within the experiment directory. The [first bounded run](../AUTORESEARCH_FIRST_RUN_RESULT_2026-09-29.md) used this ledger with a frozen TinyStories byte task, a five-minute RTX 3090 baseline and one candidate, a restricted GPU runner, and an independent validation reload. The candidate worsened the score and was rejected; the first-batch ledger is exhausted.

`experiment_memory.py` indexes only `results.jsonl` files from **explicitly supplied development experiment directories**. It retrieves prior hypotheses, failure reasons, and notes; it never scans a benchmark tree or sealed test answers. This is the proposed project-specific addition to the upstream experiment contract, but retrieval benefit has not been measured.

```bash
python3 experiment_memory.py index /path/to/memory.sqlite /path/to/approved/experiment-a
python3 experiment_memory.py search /path/to/memory.sqlite 'CUDA memory'
```

## Project 3: patient split guard

`ecg_split_guard.py` checks a proposed `record_id,patient_id,split` CSV before preprocessing. It rejects patient overlap and handles the documented [MIT-BIH 201/202 same-subject pair](https://physionet.org/physiobank/database/html/mitdbdir/records.htm).

```bash
python3 ecg_split_guard.py /path/to/proposed_split.csv
python3 ecg_split_guard.py /path/to/proposed_split.csv --inventory mitdb_record_inventory.json
```

The guard validates exact record coverage with `--inventory`; it does not claim that the old Kaggle CSV has patient IDs. The approved raw-data build now has two subject-disjoint assignments produced by `mitdb_split_candidate.py` from annotation counts only. Both [candidate CSVs](split_candidates/) passed the guard, and [candidate_split_summary.json](split_candidates/candidate_split_summary.json) gives every split and class count.

The subsequent [matched three-arm comparison](../ECG_CONTEXT_COMPARISON_RESULT_2026-09-28.md) found the weighted single-beat CNN strongest by development macro F1. The context model's beat-centered windows limit causal real-time interpretation.

The [subject-label audit](ecg_subject_label_audit_2026-09-29.json) found that the fusion and supraventricular classes are heavily concentrated in a few people. The [INCART metadata-only audit](../INCART_METADATA_MAPPING_RESULT_2026-09-29.md) checksum-verified 150 small header/annotation files, grouped 75 records into 32 patients, and counted mapped and unresolved symbols. It did not download signals or run external inference.

The subsequent [frozen INCART external test](../ECG_INCART_EXTERNAL_RESULT_2026-09-29.md) downloaded and checksum-verified 75 signal files, extracted 175,777 eligible beat windows, and evaluated the exact saved weighted MIT-BIH checkpoint once. It achieved **0.233 macro F1** with **0/219 F** beats detected. The external dataset has now been inspected and should be treated as development evidence for any later changes.

The [fixed two-arm preprocessing comparison](../ECG_ROBUSTNESS_RESULT_2026-09-29.md) trained centered and robust-scale variants only on MIT-BIH and applied their saved scalers to INCART. Centering improved inspected development macro F1 to 0.634 on MIT-BIH and 0.402 on INCART, while rare S precision remained 1.7% on INCART and both new arms found no F beats.

The [fresh confirmation-source decision](../ECG_FRESH_CONFIRMATION_SOURCE_2026-09-29.md) reserves SVDB for one later locked external transport check. Its public headers show unnamed ECG1/ECG2 channels at 128 Hz and do not establish patient identity relative to MIT-BIH. Its signals and labels have not been opened for this project.

The [compact multi-scale comparison](../ECG_MULTISCALE_RESULT_2026-09-29.md) completed after cluster SSH recovered. Its 29,580-parameter model scored 0.614 MIT-BIH and 0.394 INCART development macro F1, below the 9,188-parameter centered CNN's 0.634 and 0.402. It also worsened INCART S recognition substantially, so the centered model remains the development reference. The [preparation note](../ECG_MULTISCALE_PREP_STATUS_2026-09-29.md) preserves the earlier SSH interruption and input checks.

The [novelty-aware abstention comparison](../ECG_NOVELTY_ABSTENTION_RESULT_2026-09-29.md) used that fixed centered checkpoint without retraining. Validation selected novelty weight 0.25, but lower aggregate error accompanied uneven S/F rejection. The saved per-beat scores independently reproduced selection and reported metrics; an external abstention policy is not yet established.

The often-cited 44-record DS1/DS2 lists place 201 in training and 202 in test ([Table 2](https://www.mdpi.com/2079-9292/9/11/1790)), although [PhysioNet states](https://physionet.org/physiobank/database/html/mitdbdir/intro.htm) that they are recordings from the same person. That traditional split cannot serve as a strictly unseen-person test. Our split guard rejects assigning the pair to different people or partitions. It does not by itself prove that a proposed split has good rare-class balance or covers every intended recording.

The complete raw [PhysioNet MIT-BIH release](https://physionet.org/content/mitdb/1.0.0/) has been acquired from its official public AWS mirror. `download_mitdb.py` fetched and verified 145 top-level signal/header/annotation files (93,861,490 bytes; 48 `.dat`, 48 `.hea`, 49 `.atr`) against the mirror's sizes and ETags. The raw files are ignored by Git; [mitdb_source_manifest.json](mitdb_source_manifest.json) records their SHA-256 checksums. The source release also includes other documentation files, which were not needed for this signal/annotation audit.

With the pinned official `wfdb==4.3.1` reader, `mitdb_inventory.py` read all headers and annotations and saved [mitdb_record_inventory.json](mitdb_record_inventory.json): 48 records, 47 subject groups, and **112,647 annotation events**. Some events are rhythm/noise markers rather than labeled beats. The inventory confirms that record 114 lists V5 before MLII, so a model must select leads by name rather than column position. `mitdb_beat_manifest.py` mapped 109,494 beat annotations; `mitdb_windows.py` saved 109,438 one-second raw mV windows after 56 edge exclusions. The [window summary](mitdb_window_summary.json) and [data-build report](../ECG_DATA_BUILD_2026-09-28.md) record exact lead, class, and split rules. One approved CNN baseline ran on the cluster; [its full result](ecg_baseline_result_2026-09-28.json) and [interpretation](../ECG_BASELINE_RESULT_2026-09-28.md) show poor S/F recognition despite high accuracy.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-ecg.txt
.venv/bin/python mitdb_inventory.py data/mitdb/raw mitdb_record_inventory.json
```

The exact installed package versions used for this inventory are in [wfdb_environment_2026-09-27.txt](wfdb_environment_2026-09-27.txt). [INCART](https://physionet.org/content/incartdb/1.0.0/) is a separate external dataset. Its signals were subsequently downloaded and used in the external and robustness evaluations described above.

Run the local checks with `python3 -m unittest -v test_foundations.py` from this directory. They use synthetic fixtures, not the real corpora or cluster.

## Latest development checks — 30 September

The [64-article local-model screen](pmc_model_screen_summary_2026-09-30.json) has 63 quote-verified outputs, one unresolved case and five disagreements among20 single-agent development labels. Four false inclusions mean its35 triage candidates are not training admissions. The [source audit](pmc_model_screen_audit_2026-09-30.json) checks quote/provenance and preserves this limitation. The separate [schema-visible repair](../CORPUS_SCREEN_REPAIR_RESULT_2026-09-30.md) completed:19 of20 development labels agree and one remains unresolved; all29 records passed provenance/quote auditing. This error-informed regression requires a fresh sample before generalization claims. Eleven candidate [full-text review packets](pmc_fulltext_review_packets_2026-09-30.json) preserve every extracted paragraph and source ID for review.

`experiment_proposer.py` now permits only numeric architecture settings (width≤1024, heads≤16, feed-forward≤4096, layers≤12, dropout≤.9) and literal AdamW settings, while preserving all model-forward and training/evaluation code. The completed pilot used the earlier proposer; its exact used source is preserved in ignored raw artifacts. The new gate rejects model-side file access and altered forward behavior. Passing static checks does not replace isolated execution, finite budgets or independent evaluation.

The CPU-only [Qwen token inventory](pmc_token_inventory_2026-09-30.json), job21906909, measured8,357,601 tokens across977 unreviewed source documents and91,852 in the11 review candidates. It is a volume measurement, not a training dataset. The [EDB metadata result](../EDB_METADATA_RESULT_2026-09-30.md) checksum-verifies90 headers/annotations, groups79 subjects and counts790,549 mapped beats, including354 F across14 subjects. No source record has an II/MLII lead, so a new lead-handling protocol is required before joining it to the existing pipeline. No EDB signal has been downloaded; SVDB remains sealed.

The [cached Qwen3B inference smoke](../PMC_QA_BASELINE_SMOKE_RESULT_2026-09-30.md) completed six constructed development cases: four source-supported answers and two correct abstentions, but no requested explicit support quotes. It is not a training or benchmark result. Three development source articles are reserved from future training and independent QA tests.

## Continued checks — 1 October

The [new976-article acquisition](../PMC_EXPANSION_STATUS_2026-10-01.md) completed source/extraction/identity auditing, with972 English-tagged documents, four other-language documents and eight short-body flags. Fixed PubMedQA-context screening and exact DOI/body duplicate checks against the previous977 found no matches; other benchmark/paraphrase exclusions remain unchecked. All documents remain unreviewed.

The [fresh20 classifier check](../PMC_FRESH_SCREEN_RESULT_2026-10-01.md) found five clear core positives, one clear off-scope inclusion, two ambiguous-scope predicted inclusions and two unresolved quotes. It remains a triage tool. The [structured QA check](../PMC_QA_EVIDENCE_RESULT_2026-10-01.md) produced exact quotes for all four supported cases, but strict abstention formatting still failed. [Qwen3B4-bit LoRA execution](../QWEN_QLORA_COMPATIBILITY_RESULT_2026-10-01.md) passed three fixture steps and adapter save/reload; no biomedical training or QA score is implied.

[EDB named-V5 acquisition](../EDB_V5_ACQUISITION_RESULT_2026-10-01.md) verified51 signal files (275.4MB). Source decoding and a full-record native window inventory passed; resampling/cohort/evaluation remain pending; cross-source identity is unresolved, and SVDB remains reserved. A [matched retrieval protocol](../AUTORESEARCH_RETRIEVAL_COMPARISON_PROTOCOL_2026-10-01.md) has frozen paired proposals and submitted GPU array21944594; retrieval benefit remains unmeasured.

Combined old/new biomedical acquisition now totals1,953 distinct articles and16,807,844 cached-Qwen tokens before admission filtering. The new976 account for8,450,243 tokens; the [volume audit](pmc_expansion_token_audit_2026-10-01.json) checks IDs/source hashes/tokenizer-file agreement and arithmetic. The5,000-record metadata acquisition completed and passed source/plan/coverage/order auditing. Remaining3,870eligible-version acquisition is running in capped array21944155 with dependent audit21944638. Acquired documents remain unreviewed.

## Terminal acquisition/agent check

Remaining acquisition/audit/screen completed. [Result](../PMC_REMAINING_ACQUISITION_RESULT_2026-10-01.md):5,819combined acquired articles/50,437,502rawtokens, allunreviewed. Five new XML retraction notices require exclusion/linkage review; no automatic admission. [Paired GPU result](../AUTORESEARCH_PAIRED_GPU_RESULT_2026-10-01.md):both completed candidates worse; first pair preempted. Keep incumbent, no retrieval-superiority claim or ledger extension. EDB preprocessing continues under [bounded resampling protocol](../EDB_RESAMPLE_PROTOCOL_2026-10-01.md),job21953478.

## 2October continuation

[Notice links](../PMC_NOTICE_LINKS_RESULT_2026-10-02.md):129reviewholds,3,892structural candidates;[source review](../PMC_SCOPE_REVIEW_2026-10-02.md):32draft labels/82quotes,15humanempirical-core candidates (stillunadmitted). [QA output gate](../QA_OUTPUT_GATE_RESULT_2026-10-02.md) checksJSON/exactsourcequotes without claiming entailment. [EDBarrayQA](../EDB_ARRAY_QUALITY_RESULT_2026-10-02.md) found0constant/0exactduplicatebeats,notpersonindependence. [Runtime-feedback preparation](../AUTORESEARCH_RUNTIME_FEEDBACK_PREPARATION_2026-10-02.md) preservesnegativeexperiments andaddsparameter/throughputevidence. [Qwen scope check](../QWEN_SCOPE_CHECK_PROTOCOL_2026-10-02.md) job21967582 active,inferenceonly,12GPUminutescap.

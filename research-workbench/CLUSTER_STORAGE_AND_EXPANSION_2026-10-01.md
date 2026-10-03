# Cluster storage check and resumed expansion — 1 October

Guy authorized proceeding if a storage quota cannot be found, using100GB as his estimated limit. It is a working ceiling, not a confirmed institutional quota.

## Live findings

SSH to slurm.bgu.ac.il works. `quota -s` and `quota -v -s` reported no quota. The home directory is persistent NFS storage; shared filesystem capacity is411TB, with188TB available, but this is not a personal allocation. No Lustre/GPFS quota utilities were found on PATH. The available cluster guide describes `#SBATCH --tmp=100G` as temporary per-job scratch erased after completion, so that example does not establish permanent home quota.

The cached Hugging Face directory is about20GiB when rounded up by du; the project run directories collectively add about1.3GB logical size. The completed `du -sx --block-size=1G /home/guykalat` scan reports293GiB rounded allocated usage. This suggests the estimated100GB is not a currently enforced whole-home limit, although filesystem usage accounting is not an authoritative quota report. No unrelated files were changed or deleted. Treat the100GB estimate as a conservative cap on additional portfolio storage rather than claim it is free quota; the initial metadata batch adds at most100MB. Reassess storage before bulk XML or model checkpoint growth.

## Resumed metadata expansion

CPU job21928731 stages data in `/home/guykalat/codex_pmc_large_metadata_20261001`. The frozen manifest selects5,000 candidate IDs without replacement from the existing200,177-ID cardiovascular discovery pool, excluding the1,000 articles with previous metadata. Seed20261001 and source/input hashes are recorded. This sampling is acquisition planning; the pool is not a training corpus.

The batch requests one CPU,1GB RAM, two hours, zero GPUs. Output is capped at100MB with conservative headroom. It reads official PMC AWS article-version metadata using the existing HTTP/backoff helper and records every version or an explicit failure. It downloads no article text, admits nothing into training, and emits partial progress if its finite time ceiling is reached. Expected runtime is tens of minutes to two hours plus queue wait; service latency may leave an incomplete batch. The cheaper alternative is reusing only the original1,000 metadata records, which would not expand acquisition candidates.

Before subsequent XML acquisition: audit version coverage, select exact licensed/nonretracted versions, enforce benchmark-ID exclusion and usable identifiers, freeze the byte/download cap, and then validate XML/checksums, English language, topical/design relevance, deduplication and benchmark-context overlap. Source sizes should refine the rough25GB XML/32GB combined full-pool estimate. Reserve the three constructed QA development articles and never treat classifier confidence as admission.

[Plan](implementation/pmc_large_metadata_plan_2026-10-01.json) · [Acquisition code](implementation/pmc_large_metadata.py) · [Batch script](implementation/run_pmc_large_metadata.sbatch)

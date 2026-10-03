# ECG protocol decision before beat extraction or training — original proposal

This preserves the pre-extraction method proposal. Guy subsequently approved the data and split work. The [28 September build report](ECG_DATA_BUILD_2026-09-28.md) gives the actual windows, class counts, and subject-disjoint candidate splits. No model has been trained.

## The decision in plain language

The old five-class score mixes several distinct questions. On raw MIT-BIH, the fifth class contains mostly paced beats if all 48 recordings are used. Under the commonly used 44 nonpaced-record scope, that fifth class contains only 15 explicitly unclassifiable beats. We should use a subject-disjoint four-class N/S/V/F study as the primary test of recognizing new people's beats, and keep a separately labeled five-class all-record study to compare with the old course task. The five-class Q result should always be called **paced/unclassifiable**, not an ordinary arrhythmia class.

## What the downloaded source actually contains

The [raw inventory](implementation/mitdb_record_inventory.json) covers 48 records from 47 subject groups, with 112,647 annotation events. The table below is a **provisional mapping count**, computed from raw symbols only; it is not a count of extracted, usable waveform windows or a finalized label specification. The proposed AAMI-style groups are N = `N,L,R,e,j`, S = `A,a,J,S`, V = `V,E`, F = `F`, and Q = `Q,/,f`. PhysioNet's [annotation definitions](https://physionet.org/physiobank/database/html/mitdbdir/intro.htm) and [evaluation guide](https://archive.physionet.org/physiotools/wag/evnode8.htm) describe the symbol meanings and five evaluation groups. The precise mapping and window exclusion rules still need to be frozen before extraction.

| Scope | Records | Subject groups | N | S | V | F | Q | Nonbeat events |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All raw records | 48 | 47 | 90,631 | 2,781 | 7,236 | 803 | 8,043 | 3,153 |
| Exclude paced records 102, 104, 107, 217 | 44 | 43 | 90,125 | 2,781 | 7,009 | 803 | 15 | 2,991 |

Of the all-record Q group, 7,028 are paced `/`, 982 are paced-normal fusion `f`, and 33 are `Q`. In the 44-record scope, F appears in 17 records, but 735 of its 803 beats are in just records 208 and 213. S appears in 32 records, but record 232 contains 1,382 of 2,781 S beats. These concentrations make one arbitrary train/test split unstable for rare-class conclusions. Source rows are beats or events, not patients.

## Proposed approved batch, if Guy accepts it

**Question.** Does short neighboring-beat context improve S/F detection on unseen people compared with a single-beat 1D CNN under the same evaluation? The first batch only establishes the raw-data baseline and split; the context model is a later bounded comparison.

**Data and split.** Use all 48 records for auditable source ingestion, but make the 44 nonpaced records the primary N/S/V/F study. Group records 201 and 202 together in the all-record analysis and keep all partitions disjoint by subject. For the primary study, reserve a locked subject-disjoint test, form train/validation from the remaining subjects, and publish the exact record lists and per-class counts before model fitting. Select the partition using annotation counts only, with a stated seed and no model scores. Because S/F are concentrated, add a prespecified grouped-fold sensitivity analysis if the single test's F support is too small. The exact partition and fold count should be frozen after the label/window inventory and before training.

**Baselines and metric.** Extract target-centered waveform windows from the named MLII lead where present; document the alternative lead rule for 102/104 and record 114's reversed channel order. Fit scaling and class handling on training data only. Run a compact 1D CNN first, then a same-input multi-beat context model. Primary metric: four-class macro F1, with S and F recall/precision and subject-level variation alongside it. Report a separate five-class all-record comparison to the old beat-level task, explicitly labeling Q as paced/unclassifiable. Neither new score is directly comparable to the old 98.02% until input construction and split match.

**Expected resources and time.** The downloaded core is 93.9 MB. Beat-window extraction should fit on the local Mac and likely produce hundreds of MB to a few GB depending on dtype, window length, and whether context is materialized; measure this before finalizing. A small CNN smoke run would plausibly fit one GPU, but runtime/VRAM/GPU-hours cannot be promised because live cluster access and partition limits remain unverified. Cap the first approved run at one baseline configuration and a short timeout after the hardware inventory. No external INCART download or architecture sweep is part of this batch.

**Limitations.** MIT-BIH is small at the person level and enriched for unusual cases. R-peak positions are expert annotations, so this is beat classification given a reference beat location, not end-to-end detection. The Q class differs sharply between scopes. A single split may make F and S metrics noisy. The traditional DS1/DS2 lists put 201 and 202 on opposite sides despite the [PhysioNet same-subject note](https://physionet.org/physiobank/database/html/mitdbdir/intro.htm), so they are not a valid strictly unseen-person reference.

**Cheaper alternatives.** Run only the 44-record extraction and one CPU or short-GPU CNN first; defer five-class and grouped-fold analysis. A five-class-only path preserves the course label set but mostly tests paced-beat recognition as Q. A standard DS1/DS2-only path is more comparable with past papers but retains the 201/202 person overlap. The dual protocol is recommended because it exposes both questions honestly.

**Outcome (28 September).** Raw beat labels and windows were extracted, and two candidate splits were validated against all record/subject IDs. The next model job remains a separate bounded decision; no external dataset has been downloaded.

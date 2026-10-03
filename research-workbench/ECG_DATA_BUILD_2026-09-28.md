# Project 3: raw ECG data build — 28 September 2026

## Research question and data boundary

The primary study is four-class beat classification for people absent from training: N/S/V/F on the 44 nonpaced MIT-BIH recordings. A separate five-class N/S/V/F/Q result on all 48 recordings will preserve the old task's class scope, while labeling Q as paced/unclassifiable. This is deep learning on a one-dimensional physiological signal, **not computer vision**. Input windows are centered on reference beat annotations; any later classifier will not be an end-to-end beat detector or live clinical system.

The [official MIT-BIH source](https://physionet.org/content/mitdb/1.0.0/) was checksum verified in the [source manifest](implementation/mitdb_source_manifest.json). [Beat manifest code](implementation/mitdb_beat_manifest.py) mapped annotation symbols to provisional AAMI-style classes and preserved record/subject IDs, including the documented [same-person 201/202 pair](https://physionet.org/physiobank/database/html/mitdbdir/intro.htm). It identified 109,494 beat events among 112,647 annotation events. The full raw mapping has N 90,631, S 2,781, V 7,236, F 803, Q 8,043. The 44-record primary scope has N 90,125, S 2,781, V 7,009, F 803 before window exclusions.

The [window extractor](implementation/mitdb_windows.py) produced a fixed 360-sample, one-second raw mV window per eligible beat: `[R-180, R+180)` at the source 360 Hz, without resampling, scaling, or padding. It selects MLII by **lead name**; only recordings 102 and 104 use V5 because MLII is absent. This avoids the record 114 channel-order trap. The extraction saved 109,438 float32 windows, excluding 56 beats at signal boundaries and no nonfinite windows. The [per-record summary](implementation/mitdb_window_summary.json) and ignored local window manifest/NumPy arrays preserve record order and annotation samples. The arrays total about 150 MB. We checked that every manifest row has a stored window and compared one record 114 window with the named MLII raw signal sample for exact agreement.

| After edge exclusion | N | S | V | F | Q | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Primary 44-record study | 90,076 | 2,781 | 7,008 | 802 | excluded | 100,667 |
| Separate 48-record study | 90,582 | 2,781 | 7,235 | 802 | 8,038 | 109,438 |

## Frozen candidate splits before modeling

The [split generator](implementation/mitdb_split_candidate.py) used a recorded seed `20260928`, 50,000 candidate group permutations, and **annotation class counts only** to seek feasible partitions. It did not inspect waveform values or model scores. It used class labels to balance groups, so the split is stratified rather than a blind random partition. Both [candidate A](implementation/split_candidates/candidate_split_a.csv) and [candidate B](implementation/split_candidates/candidate_split_b.csv) passed [exact-record subject-overlap validation](implementation/ecg_split_guard.py); 201 and 202 stay together. The [split summary](implementation/split_candidates/candidate_split_summary.json) contains every record/subject group and class count.

Primary scope: 43 subject groups, with 30 training, 6 validation, and 7 test groups. Candidate A assigns record 213 to training and 208 to test. Candidate B swaps them to test sensitivity to which F-rich person is held out. The shared validation set has just **15 F beats**; its F1 is too noisy to optimize many models. This is a central limitation, not a reason to use test labels for tuning.

| Primary scope | Train N/S/V/F | Validation N/S/V/F | Test N/S/V/F |
| --- | --- | --- | --- |
| A | 62,639 / 1,963 / 4,899 / 403 | 12,336 / 389 / 980 / 15 | 15,101 / 429 / 1,129 / 384 |
| B | 61,585 / 1,937 / 5,671 / 413 | same as A | 16,155 / 455 / 357 / 374 |

For the five-class comparison, paced records 102 and 107 are added to training, 104 to validation, and 217 to test. This yields 33 train, 7 validation, and 8 test records, covering all 47 subject groups without overlap. In candidate A, Q has 4,165/2,069/1,804 train/validation/test windows. The V5 fallback occurs only in the paced comparison and can itself become a lead/source confound; report results separately by lead and do not equate five-class Q performance with arrhythmia recognition.

## Next bounded decision

A compact single-beat 1D CNN can establish the baseline on candidate A before trying rhythm context. Freeze train-only amplitude scaling, class handling, architecture, optimizer, epoch/step cap, selection rule, and the macro F1/per-class report in one run specification. Request **one RTX 3090 job capped at 30 minutes** after verifying personal storage quota, available VRAM/PyTorch environment, and a safe remote project directory. Use the held-out test once after model selection; then run candidate B as a separately approved sensitivity check. Estimated input arrays are about 150 MB, with a small model, but VRAM and actual job time are not yet measured. The cheaper alternative is a CPU smoke run on a small training subset to validate the pipeline without a GPU score.

**Subsequent result, 28 September:** The approved [single-beat CNN baseline](ECG_BASELINE_RESULT_2026-09-28.md) was trained once on candidate A. The data-build counts and split definitions above were fixed before that run. INCART remains a later external validation dataset after its lead/annotation mapping is reconciled.

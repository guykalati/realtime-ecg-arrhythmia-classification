# Project 3: first frozen INCART external test

## Result in plain language

The weighted single-beat CNN selected on MIT-BIH development data **did not transfer well to INCART**. On **175,777** eligible annotated beats from **75 records / 32 patients**, it achieved four-class macro F1 **0.233** and accuracy **0.470**. It detected **0/219 fusion (F)** beats. It labeled many normal beats as supraventricular (S) or ventricular (V), so this is a broad transport failure, not just a rare-F issue. This test used the [frozen input contract](INCART_EXTERNAL_PROTOCOL_2026-09-29.md) with no refitting, calibration, threshold selection, or INCART model selection.

| Class | Support | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| N | 153,594 | 0.959 | 0.450 | 0.613 |
| S | 1,958 | 0.008 | 0.150 | 0.015 |
| V | 20,006 | 0.200 | 0.655 | 0.306 |
| F | 219 | 0.000 | 0.000 | 0.000 |

The confusion matrix has actual rows and predicted columns in N/S/V/F order:

| Actual \ predicted | N | S | V | F |
| --- | ---: | ---: | ---: | ---: |
| N | 69,147 | 32,092 | 51,946 | 409 |
| S | 1,248 | 293 | 417 | 0 |
| V | 1,633 | 4,903 | 13,100 | 370 |
| F | 62 | 76 | 81 | 0 |

External cross entropy was **2.556**, multiclass Brier score **0.886**, and 10-bin ECE **0.379**. These show poor probability behavior under this shift; the ECE is only a descriptive estimate for this particular external set.

## Data and run provenance

- The official [INCART release](https://physionet.org/content/incartdb/1.0.0/) contributed 75 raw signal files totaling **832,680,000 bytes**. Every file's size and S3 multipart ETag was checked, then its SHA-256 was recorded in the [signal manifest](implementation/incart_signal_source_manifest_2026-09-29.json). The [header/annotation inventory](implementation/incart_metadata_inventory_2026-09-29.json) already identified all 32 patient groups.
- The [extractor](implementation/incart_windows.py) made one-second physical-mV windows from named lead II at 257 Hz and resampled each to 360 points. It retained N=153,594, S=1,958, V=20,006, F=219, excluding **91 edge windows**, 12 `+` rhythm markers, six Q, one B, and 32 `n` events according to the pre-score contract. The [window summary](implementation/incart_window_summary_2026-09-29.json) includes every record's counts and the manifest hash. The ignored local arrays total about 253 MB.
- The exact MIT-BIH `single_weighted` epoch-10 checkpoint was copied from the cluster comparison run and matched SHA-256 `adcfff59c366ef8d70ea0188b287f799b5823406c888bc77c1f42f03fbf4d318` locally and remotely. The external evaluator applied that run's training-only mean and standard deviation. All **83** staged files matched the [SHA-256 staging list](implementation/incart_external_staging_2026-09-29.sha256) before submission.
- Slurm job **21728069** used one RTX 3090, 2 CPUs, 8 GB RAM, and a 10-minute cap. It completed in **12 seconds**, exit code 0; Python measured 3.90 seconds for loading/evaluation/output. The [machine result](implementation/incart_external_result_2026-09-29.json) includes calibration bins and every patient's confusion metrics; the [job log](implementation/incart_external_slurm_21728069.log) records the allocation.
- Retrieved result and prediction files matched remote SHA-256 values. A separate local check counted **175,777 prediction rows**, reproduced the exact confusion matrix and class supports, and confirmed 32 patient IDs. Per-beat predictions remain in ignored local `implementation/data/incart/external_eval_2026-09-29/predictions.csv`; its SHA-256 is in the machine result.

## Failure audit and limits

The MIT-BIH training-waveform mean/std were **−0.317/0.468 mV**. The INCART extracted-window mean/std were **−0.077/3.506 mV**; some individual records have large offsets and variance. A check of raw WFDB physical lead-II values for one high-variance record (`I31`) reproduced the large variation before our resampling, so it is not evidence of a simple unit-conversion bug. This amplitude difference, named lead-II versus MLII, 257 versus 360 Hz, patient mix, and annotation alignment are all possible contributors. The current result cannot isolate their effects. A post-score normalization tweak on INCART would be exploratory and would consume this dataset as development evidence.

The MIT-BIH weighted model's **0.555** macro F1 came from a different, previously inspected development test with different sampling, channel, patients, and class prevalences. The two numbers show a failed external transport attempt, not a controlled head-to-head model comparison. The inputs are centered on known reference annotations and include signal after the beat. This is neither beat detection nor real-time clinical monitoring.

The next controlled improvement should train a robust preprocessing/model variant **using MIT-BIH training data only**, keep a matched MIT-BIH baseline, and evaluate fixed variants on INCART as a now-used development transport set. Any final external generalization claim needs another untouched source or a separately reserved patient group.

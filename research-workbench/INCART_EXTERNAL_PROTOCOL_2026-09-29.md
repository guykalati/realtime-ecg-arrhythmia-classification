# Frozen first INCART external input protocol

This contract is set from the official INCART metadata inventory and the existing MIT-BIH weighted single-beat model, before downloading INCART waveform files or viewing any INCART model score.

## Question and unit

Can the **already selected** MIT-BIH candidate-A weighted single-beat CNN classify annotated N/S/V/F beats from a separate source without refitting? The unit is an annotated beat, with per-patient metrics retained. This is external transport of a development-selected model, not prospective detection or clinical validation.

## Fixed inputs

- Source: PhysioNet INCART 1.0.0, 75 records from 32 patients; group all records with the same header patient number.
- Channel: signal named `II`, selected by name. The current headers place it at index 1 in every record. The MIT-BIH training channel was usually `MLII`; report that difference.
- Event: a reference beat annotation. Map `N,R,j` to N; `A,S` to S; `V` to V; `F` to F. These are the raw symbols actually present that match the existing MIT-BIH table. Exclude `Q` (outside the four-class primary task), `+` (rhythm-change marker, not a beat), and unresolved `B,n`. Report their counts and all edge/nonfinite exclusions; do not turn them into a different class after seeing a score.
- Window: 257 source samples `[annotation - 128, annotation + 129)`, about one second centered on the annotated complex. Reject a window crossing a record edge. Read physical lead-II millivolts using WFDB. Resample each full window to exactly 360 samples with `scipy.signal.resample_poly(window, 360, 257)`; save float32. Do not fit or adjust amplitude normalization on INCART.
- Model: the saved `single_weighted` checkpoint from the three-arm MIT-BIH candidate-A run. Apply that run's training-only waveform mean and standard deviation. No INCART labels, calibration, or predictions may be used to choose an epoch, architecture, threshold, or alternative preprocessing after this contract.

## Outputs and limits

Check each waveform file against the official source listing size/ETag and retain SHA-256. Save record/patient ID, sample index, raw symbol, mapped class, lead, window index, and input-file hash. Report four-class macro F1, class precision/recall/support, confusion matrix, calibration, and patient-level counts; retain the excluded-event table separately. The primary score should use every eligible INCART beat with a complete finite window.

The official dataset lists 563.5 MB compressed and 794.5 MB uncompressed; 75 raw `.dat` files are expected to account for nearly all of the latter. Signal extraction may add about 250 MB as float32 windows before overhead. A single forward pass should be much cheaper than training, but actual wall time and cluster requirements must be measured. The cheaper fallback is a two-record pipeline smoke with **no metric** if file acquisition or resampling fails. The limitations are the lead, sampling, patient-mix, and annotation-protocol shifts and only 219 mapped F events across 14 patients in metadata.

Sources: [PhysioNet INCART](https://physionet.org/content/incartdb/1.0.0/), [PhysioBank annotation definitions](https://archive.physionet.org/physiobank/annotations.shtml), [metadata audit](INCART_METADATA_MAPPING_RESULT_2026-09-29.md), [MIT-BIH matched model result](ECG_CONTEXT_COMPARISON_RESULT_2026-09-28.md).

# Project 3: INCART external-data metadata audit

## Result in plain language

The official INCART release is suitable for a **carefully labeled external beat-classification test**, with an important rare-class limit. The 75 records come from 32 patients, and their headers identify which recordings share a patient. The source uses 12 leads at 257 Hz; every checked header names lead `II` at channel index 1. These differ from the MIT-BIH primary input, named `MLII` at 360 Hz. A direct score would therefore test a real dataset and signal-domain shift, not just a second set of identical inputs. [PhysioNet documents the acquisition, leads, sampling rate, and patient-number rule](https://physionet.org/content/incartdb/1.0.0/).

Only 75 `.hea` and 75 `.atr` files were downloaded: **394,820 bytes** in total, with every file checked against the official public AWS mirror's size and ETag, then recorded with SHA-256 in the [saved inventory](implementation/incart_metadata_inventory_2026-09-29.json). The 75 waveform `.dat` files were not downloaded. The repeatable [metadata audit script](implementation/incart_metadata_inventory.py) read the headers and all annotations with the existing pinned WFDB environment.

| Provisional mapping | Annotation events | Patient groups with at least one |
| --- | ---: | ---: |
| N | 153,676 | 32 |
| S | 1,960 | 19 |
| V | 20,013 | 31 |
| F | 219 | 14 |
| Q, outside the four-class primary task | 6 | 4 |
| Unmapped pending explicit decision | 45 | 5 |

There are **175,919** annotation events in all. The raw symbols are `N` 150,410, `R` 3,174, `j` 92, `A` 1,944, `S` 16, `V` 20,013, `F` 219, `Q` 6, `+` 12, `B` 1, and `n` 32. The current provisional mapping reuses the MIT-BIH symbol table; it leaves `+`, `B`, and `n` explicit. The [PhysioBank annotation definitions](https://archive.physionet.org/physiobank/annotations.shtml) identify `+` as a rhythm-change marker rather than a beat, `B` as an unspecified bundle-branch-block beat, and `n` as a supraventricular escape beat. Those 33 beat symbols need a declared class or exclusion rule before evaluation. We must not silently count the 12 rhythm markers as beats.

Fusion beats are spread across 14 INCART patients, although only **219** exist in total; the two largest contributors have 56 and 55. This is a useful external check for the current MIT-BIH failure, but it remains small for a stable per-patient F estimate. Patient grouping must be maintained even if multiple 30-minute records are used. [The official patient-record list](https://physionet.org/content/incartdb/1.0.0/files-patients-diagnoses.txt) independently supports the header mapping.

## Boundary before a model score

Freeze the four-class mapping, sample-window rule, resampling from 257 Hz to 360 samples per second, and named lead-II selection before downloading signal files. Count edge/window exclusions and retain patient IDs. Apply the MIT-BIH-trained scaler and model without fitting on INCART; any calibration adjustment on INCART would require a separate development partition. A score also requires the model selected without viewing INCART labels or outcomes. The current MIT-BIH candidate-A test has already been used for development, so external INCART would be a transport confirmation of a frozen candidate, not a retroactive untouched MIT-BIH test.

The official release lists **563.5 MB compressed** and **794.5 MB uncompressed** for all files. The next acquisition can select just the 75 waveform files with checksum validation after the preprocessing contract is fixed. No external waveform inference or training has run. [Source and size](https://physionet.org/content/incartdb/1.0.0/).

**Later completion, 29 September:** The [input contract](INCART_EXTERNAL_PROTOCOL_2026-09-29.md) was frozen, then the 75 waveform files were acquired and one external inference run completed. See the [result report](ECG_INCART_EXTERNAL_RESULT_2026-09-29.md); the paragraph above records the state at the metadata-audit gate.

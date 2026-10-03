# EDB named-V5 acquisition completed

All51 selected EDB1.0.0 waveform files were downloaded directly to the cluster:275,400,000bytes. Every file was independently reread after acquisition and verified against its official release SHA256; recorded size, metadata/header/annotation source hashes, selection coverage and file count passed the acquisition audit. There are51 documented within-EDB subject groups.

Raw signals remain in `/home/guykalat/codex_edb_v5_acquire_20261001/raw`; small manifests/logs/audit were retrieved locally. This is source acquisition, **not waveform decoding, preprocessing, model evaluation or proof of cross-source patient independence**. No EDB class score or signal-quality exclusion has been produced.

The [primary-source identity review](ECG_EDB_IDENTITY_PROTOCOL_RESEARCH_2026-10-01.md) found no documented shared EDB/MIT-BIH/INCART record or person, but no shared identifiers establish that people are distinct. A later waveform-match screen can identify reused recorded episodes; a negative cannot prove distinct patients. Keep EDB as development evidence and SVDB reserved. Named V5 is not renamed to II or MLII.

Next: decode source gain/units, verify named-channel selection and annotation alignment, inspect quality transitions and rare-class retention, then freeze matched lead-aware preprocessing/model comparisons before viewing scores. The51 V5 records include343 fusion annotations across11 groups before window and quality exclusions, heavily concentrated in two groups; this is not a balanced independent rare-class test.

[Protocol](EDB_V5_ACQUISITION_PROTOCOL_2026-10-01.md) · [Frozen plan](implementation/edb_v5_acquire_plan_2026-10-01.json) · [Signal audit](implementation/edb_v5_signal_audit_2026-10-01.json)

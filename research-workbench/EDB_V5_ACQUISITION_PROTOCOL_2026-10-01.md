# EDB V5 development acquisition protocol

Purpose: acquire the51 EDB1.0.0 recordings whose official headers name a V5 channel, to prepare lead-specific signal QA. These51 records represent51 documented EDB subject groups and contain343 fusion annotations across11 groups before window/quality exclusions. Rare-class concentration remains severe. No II/MLII lead is inferred or renamed.

Role is **development only**. This is not a sealed external confirmation or proof that patients differ from MIT-BIH/INCART. Independent source-provenance research is pending; waveform duplicate checks alone cannot prove patient identity separation. SVDB remains sealed. There is no EDB training or model scoring in this batch.

Waveforms come from the official PhysioNet public S3 mirror. Freeze the listing sizes/ETags and match every signal to the previously checksum-verified release SHA256SUMS. Keep named-lead indices, official headers/annotations and subject grouping in the manifest. Maximum transfer500MB, two concurrent downloads, one CPU allocation with1GB memory and15-minute wall ceiling; zero GPUs. Actual selected source sizes are in the frozen plan. Expected download duration is minutes plus queue delay. The cheaper alternative is retaining metadata only, which cannot validate signal scaling, channel decoding, quality markers or eventual preprocessing.

Later preprocessing must verify digital/physical scaling from headers, V5 channel selection,250Hz resampling and annotation-time alignment, edge and quality exclusions, source-specific units and subject-level class retention. Keep quality-mask interpretation explicit and inspect representative signals before freezing training/exclusion rules. Freeze any model evaluation protocol and artifact hashes before scores are viewed. Report source/lead/class/person/calibration; do not attribute a lead/domain shift to model architecture alone.

[Metadata result](EDB_METADATA_RESULT_2026-09-30.md) · [Acquisition code](implementation/edb_v5_acquire.py)

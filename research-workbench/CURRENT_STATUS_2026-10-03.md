# Current status — 3 October 2026

Past-only timing remains the provisional development reference with the existing CNN. The 18-cell subject-adversarial objective test completed job 22007333 in 391 GPU seconds. All six zero-penalty controls reproduced prior confusion counts. Validation selected weight 0.05, improving mean macro F1 from 0.5843 to 0.6005 on MIT and 0.4984 to 0.5168 on INCART. It nevertheless failed the frozen MIT F false-positive limit (9.67 versus 5.83), so retain the existing combined model. F detection remains poor; no clinical or fresh-confirmation claim follows.

Read [the full subject-objective result](ECG_SUBJECT_ADVERSARY_RESULT_2026-10-03.md) for S/F precision/recall, false positives, mixed effects and independent checks. Exact-input checks previously found no cross-source identical windows; transformed-record/patient independence is still unproven. EDB remains unscored and SVDB sealed. Annotation-assisted peaks and centered waveform latency remain explicit limitations.

The HTML walkthrough and earlier reports remain historical snapshots.

# CV evidence closure

Branch: `codex/cv-evidence-closure-2026-10-03`. Expansion is paused until all three projects have executable code and verified results.

Source CV SHA256: `16ad4fb13ce8c4df0ae8b43061c30dd7def08f2d11d42d9242a4c46e0dfcc4b0`. No CV wording or numbers edited.

## Required evidence

- [x] 1D CNN, five classes, at least 100,000 annotated heartbeat samples, held-out evaluation.
- [x] Working waveform interface and simulated alerts using saved model inference.

Completion requires real execution, inspectable predictions/traces, data/config/source/artifact hashes, reproducible commands and honest limitations. Historical scores are not acceptance targets; measured scores may replace them.

Verified: output/result_audit.json, output/numpy_inference_audit.json and output/browser_audit.json. Accuracy 94.10%; fusion recall 0/384; the old 98.02% is not the new patient-disjoint score.

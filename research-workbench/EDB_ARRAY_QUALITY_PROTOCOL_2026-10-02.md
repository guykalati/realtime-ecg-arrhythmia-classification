# ECG array quality inventory

Purpose:verify all51array hashes,486,681shapes/finiteness/class counts and sourceCSVindices; inventory standard-deviation distributions, zero-spread windows and exact resampledfloat32beat duplicates. OneCPUrequest/2GBRAM/10minutes/0GPU,10MBoutputcap,noautomaticrequeue,job21966836. Reuse700.83MBexisting arrays; no new signals downloaded.

No filtering or normalization fitting. Exact same model-input beats can expose repetitions/flat signals; even a positive beat match does not prove a shared episode or patient. Negative exact hashes cannot exclude approximate,reencoded,cross-lead recordings. SVDB remains reserved. Frozen source and source-summary hashes: `implementation/edb_array_quality_manifest_2026-10-02.json`.

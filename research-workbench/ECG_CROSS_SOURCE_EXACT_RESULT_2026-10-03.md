# ECG exact input duplication — completed

Corrected job **22000545** completed with exit 0:0 in **57 allocated CPU seconds**, zero GPU. The local audit verified result/source/manifest checksums, all 174 array-file checksums recorded by the runner, complete record/window/class coverage and the failed predecessor.

| Source | Records | Windows |
|---|---:|---:|
| MIT-BIH | 48 | 109,438 |
| INCART | 75 | 175,777 |
| EDB V5 subset | 51 | 486,681 |
| Total | 174 | 771,896 |

**Zero exact cross-source float32 window groups; zero constant windows.** No filtering, training, split creation or SVDB access occurred. Raw result SHA-256: `159ff88337cf8b67043534c720692ec462e9913cf0b0cd16ee25094a4c603e74`. Compact audit: `implementation/ecg_cross_source_exact_audit_2026-10-03.json`.

This checks exact 360-sample prepared inputs only. Different lead, sampling, scale, offset or near-duplicate recordings can evade hashes. It does not establish independent people or replace aligned long-recording/near-duplicate screening. EDB remains unevaluated, and lead-aware cohort/split design is pending.

Predecessor **22000244** failed after 66 CPU seconds at the final class assertion because the manifest mixed MIT complete-source class counts and primary-training-subset metadata. A separate v2 manifest moved the latter into its own field; inputs and algorithm were unchanged. Both frozen manifests remain recorded.

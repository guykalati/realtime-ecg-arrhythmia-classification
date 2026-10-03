# EDB one-second V5 window inventory

Job21944620 completed in28allocated CPU seconds (23.38seconds in code), noGPU time. All51signal hashes and frozen header/annotation hashes were checked before full named-V5 decoding. Native windows cover250samples, `[center-125,center+125)`, without resampling or stored model input arrays.

## Finite windows

| Class | Complete finite windows | Entire window source-clean | Fraction source-clean |
|---|---:|---:|---:|
| N |481,822|406,441|84.4%|
| S |388|365|94.1%|
| V |4,128|3,037|73.6%|
| F |343|256|74.6%|

Total486,681windows;62N beats were excluded at record edges. No nonfinite windows were found. All rare S/V/F beats survived bounds/finiteness; this is not model coverage or sensitivity.

Flags are carried through the entire native window. They can coexist: F has75windows containing unknown quality,12containing noisy state and1containing unreadable state. A hypothetical source-clean-only policy would retain256/343F windows (74.6%), so filtering cannot be chosen using aggregate counts alone. Source quality bit interpretation retains the previously documented prose-table discrepancy; these flags are inventory information, not a settled exclusion policy.

The downloaded CSV was rehashed and independently traversed to verify group/lead IDs, beat uniqueness and bounds, class counts and flag totals. Counts reconcile with the original selected-record annotation inventory. The CSV is18.20MB; no waveform arrays were copied to the Mac.

This remains development-only. No resampling, filtering policy, recording-overlap screen, cross-database identity guarantee, training or scores. SVDB remains reserved.

Evidence: `implementation/edb_window_inventory_audit_2026-10-01.json`, frozen source/manifest and ignored `implementation/data/edb_window_inventory_20261001/`.

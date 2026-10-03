# Bounded EDB development-array construction

Purpose: turn the audited486,681finite one-second native V5 windows into the existing model’s360sample shape, preserving all groups, symbols, classes and quality flags. This is preprocessing, not a model comparison. Planned signal output is about701MB, capped at1GB; one CPU request,4GBRAM,10minute limit,0GPU. Job21953478 uses a frozen source/plan/inventory/header/annotation manifest and `--no-requeue`.

Keep mV units and the actual V5 lead name. Use native250samples `[center-125,center+125)` and `resample_poly(36,25)` without fitted normalization. Per-record output shape/finiteness and3individually recomputed windows are checked. All raw-file/header/annotation hashes are reread, class counts must equal481822N/388S/4128V/343F, and output hashes/index CSV are retained. No noisy/unknown/unreadable flags are filtered.

Downstream training still requires lead-aware design, source-quality convention review, recording-overlap screening and a frozen development protocol. Cross-source person overlap remains unknown; SVDB remains reserved. This job does not create splits, fit normalization or score a model.

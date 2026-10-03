# EDB resampling completed

Job21953478 completed in33allocated CPU seconds (25.35seconds measured),0GPU. All51V5records produced486,681finite360sample windows,700,827,168bytes of arrays. Counts remain481,822N/388S/4,128V/343F. Native250Hz mV windows were resampled with `resample_poly(36,25)`;3windows per record were recomputed individually and matched.

Source waveform/header/annotation and finite-inventory hashes were checked; all array hashes are retained. Local manifest traversal verified one-to-one original beat metadata, group/lead/symbol/class/quality-flag agreement and contiguous indices for every record. Raw waveform arrays remain on the cluster; no Mac waveform download occurred.

This is development preprocessing. No quality exclusions, fitted normalization, splits, recording-overlap checks, training or scores. V5 retains its actual name; cross-source person overlap and the source-quality convention remain unresolved. SVDB remains reserved.

Evidence: `implementation/edb_resample_result_audit_2026-10-01.json`, frozen manifest/source, retrieved summary/CSV and cluster `codex_edb_resample_20261001/windows_360`.

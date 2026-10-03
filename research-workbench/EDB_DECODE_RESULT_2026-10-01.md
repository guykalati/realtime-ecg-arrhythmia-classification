# EDB named-V5 decoding check

Job21944423 completed successfully in11allocated CPU seconds, with7.21seconds measured in the decoder and noGPU time. All51source records passed named-channel,250Hz,2-channel header, mV units, documented group/channel-index, monotonic annotation and annotation-bound checks.

Two10-second segments per record (start and midpoint) produced102segments and255,000finite V5 samples. Digital-to-physical conversion agreed with each header’s gain/baseline. The downloaded result SHA256 matched the remote artifact; source and acquisition-plan hashes, record identities, segment positions/counts were checked locally.

This validates sample decoding, not whole-record waveform quality, beat-window construction, resampling, duplicates or cross-database patient identity. No model evaluation was performed. EDB remains a development source; V5 must retain its actual lead name and SVDB remains reserved.

Evidence: `implementation/edb_decode_audit_2026-10-01.json`, frozen manifest/source, and ignored `implementation/data/edb_decode_result_20261001.json`.

Next: construct a bounded window/quality inventory and report rare-class retention before deciding a lead-aware development comparison.

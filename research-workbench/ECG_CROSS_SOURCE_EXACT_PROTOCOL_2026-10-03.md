# Exact prepared-input duplication screen — three ECG sources

Purpose: catch exact reuse of prepared one-second float32 windows across MIT-BIH, INCART and the EDB V5 subset before designing a combined development cohort. This is a narrow input-integrity check, not the previously proposed aligned long-signal near-duplicate study.

Read only the three known prepared array directories and frozen CSV/array checksums. Keep each window's source, record, documented group, lead, class and index. Compare SHA-256 of the 360-sample bytes without fitted normalization or new resampling. Skip constant windows from matches and report their counts. Verify all file hashes, shape, finiteness, row indices, record/class counts. Include all 48 prepared MIT records, including paced/Q/V5 cases outside the primary training cohort, so coverage is explicit.

Expected coverage: MIT 109,438 windows / 48 records; INCART 175,777 / 75; EDB 486,681 / 51; total **771,896 windows / 174 records**. Inputs occupy about 1.11GB. No waveform output, filtering, splits, fitted statistics, model evaluation, or SVDB access. Output capped at 1MB.

One CPU job, 2 CPUs, 4GB host RAM, **10-minute CPU wall cap, zero GPU**, no requeue/retry. Expect seconds to a few minutes based on EDB's prior hash screen, with shared-filesystem variation. Keep any interrupted result partial. Selfcheck tests an exact cross-source duplicate, changed waveform, and excluded constant window.

Any positive is an exact input match requiring review, not sufficient proof of a shared full recorded episode or person. Zero matches cannot rule out different lead, sample rate, gain, encoding, temporal offset, or approximate episode reuse. Cross-release person overlap remains unknown. The sensitive aligned long-recording screen still remains before making a screened-recording claim. No dataset admission follows automatically.

## Recorded failure and corrected finite run

Job 22000244 failed at the final class-count assertion after 66 allocated seconds: the MIT expected-class dictionary also contained four primary-subset metadata fields. No completed result was emitted. The same source checksums and comparison algorithm are preserved. A separate v2 manifest moves primary-subset counts into their own metadata field. One corrected CPU run has its own 10-minute cap, no retry or requeue. The failed manifest and log remain unchanged.

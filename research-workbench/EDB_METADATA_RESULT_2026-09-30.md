# European ST-T metadata inventory result

All90 EDB1.0.0 headers and `.atr` annotation files were downloaded and checked against both public-mirror MD5/size and the official release SHA256 manifest. Including the record list and checksum manifest, transfer was **1,683,622 bytes**. Existing WFDB4.3.1 read headers/annotations without signal files. The seven same-person groups from the [release documentation](https://physionet.org/content/edb/1.0.0/) produce **79 subject groups**. [Complete machine inventory](implementation/edb_metadata_inventory_2026-09-30.json) preserves every file, group, annotation symbol and lead.

| Category | Source annotation count |
|---|---:|
| N | 784,633 |
| S (`a/J/S`) | 1,095 |
| V | 4,467 |
| F | 354 |
| Unmapped Q/artifact/rhythm/ST/T/quality/other events | 12,360 |
| All events | 802,909 |

Mapped total is **790,549** before any waveform, window or signal-quality exclusion. This release's parsed event total is43 higher than the historical page's802,866; preserve the measured count and version/checksums rather than force it to match an older prose total. Beat mapping follows [the original code definitions](https://physionet.org/physiobank/database/edb/annotations.shtml); ST/T and rhythm events are excluded from N/S/V/F.

**Rare-class support:** S occurs in58 groups; the largest supplies380/1,095 (34.7%). F occurs in14 groups, but `edb_e0605` supplies224/354 (63.3%) and `edb_e0614`82/354 (23.2%). Only48 F events remain across12 other groups. This is broader subject support than one dominant subject, but still severely concentrated.

**Lead mismatch:** all records have250 Hz and two channels, but **zero** have an II or MLII name. The180 channel names are V5(51), MLIII(47), V4(34), MLI(19), V1(11), V2(10), V3(7), D3(1). MLIII must never be relabeled MLII. These records cannot simply be appended to the current lead-II training arrays.

**Next decision prepared:** use EDB as a candidate *training/development* expansion only under a separately frozen protocol that specifies lead handling, patient-disjoint allocation, resampling, quality exclusions and per-class denominators. A lead-aware or multi-lead representation study is a useful direction; whether it improves the current II-lead model remains untested. Preserve the current reference and sealed SVDB. EDB model scores, waveform quality, cross-source duplicate waveforms and patient identity have not been inspected. No new model or clinical-performance result exists.

## Source annotation quality check

The subsequent [quality inventory](implementation/edb_quality_inventory_2026-09-30.json) carries the last source quality annotation forward to each beat and channel; before the first quality annotation it reports **unknown**. It does not remeasure waveform quality or remove samples. For V5's343 F beats, the derived states are257 clean,10 noisy,1 unreadable and75 unknown. A clean-only policy would retain74.9% before expanding any one-second window; this is a prospective filtering tradeoff, not model performance.

The raw annotation files contain quality codes0x13/0x22/0x23, while the [prose code table](https://physionet.org/physiobank/database/edb/annotations.shtml) lists0x12/0x20/0x21. The first literal-table decoder therefore failed rather than silently assign clean states. The inventory now derives channel unreadability using bits4/5 checked by the official [WFDB comparator](https://physionet.org/physiotools/wfdb/app/bxb.c), with channel/noisy-bit associations from the EDB definitions. This is an explicitly documented interpretation of the bit flags; confirm the source convention before freezing exclusions. Temporal boundary/reserved-bit checks and class/lead totals passed. The measured annotation counts remain unchanged.

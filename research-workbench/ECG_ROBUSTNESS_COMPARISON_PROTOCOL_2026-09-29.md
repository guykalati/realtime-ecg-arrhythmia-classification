# Project 3: frozen amplitude-robustness development comparison

## Purpose and status

The first fixed MIT-BIH weighted single-beat CNN scored 0.555 macro F1 on the inspected candidate-A development test, then only 0.233 on INCART. Raw one-second INCART lead-II windows had much larger measured variation than MIT-BIH training windows (std 3.506 versus 0.468 mV), but that association does not establish causality. This **development** experiment isolates the effect of waveform normalization, using the same patient split, target beats, CNN, class weights, seed, optimizer, and checkpoint rule. Both MIT-BIH candidate A and INCART have already influenced the question and cannot become untouched final tests.

## Fixed arms

Both new arms train only on the existing **69,842 MIT-BIH training targets**, select an epoch on **13,708 validation targets**, and report the same **17,029 development-test targets** from the matched context manifest. The existing raw weighted single-beat run is the fixed reference; it is not retrained or retuned.

1. **Raw weighted reference:** `(x - train_global_mean) / train_global_std`, exactly as the existing weighted single-beat arm.
2. **Window-centered weighted CNN:** subtract each 360-sample window's median, then divide by a **training-only global standard deviation of centered training windows**. Median is computed on that window without using its label, other patients, or INCART statistics.
3. **Window robust-scale weighted CNN:** subtract each window's median and divide by `max(1.4826 × median(|x − median(x)|), floor)`. Set `floor` once from the **5th percentile of positive training-window robust scales**; do not compute it from validation, test, or INCART. Then divide by a **training-only global standard deviation of transformed training windows**. This avoids unbounded amplification of nearly flat windows.

Use the same compact 9,188-parameter CNN, class weights `sqrt(train_N/train_class)`, 12 epochs, AdamW settings, batch size 256, seed 20260928, and lowest unweighted validation cross entropy for all newly trained arms. Primary development readout: four-class macro F1 with S/F precision, recall, support and per-subject confusion. Report accuracy, cross entropy, Brier, ECE, peak GPU memory, and training time. All transforms are fixed before reading new scores.

## External development check

Apply each trained arm's **frozen MIT-BIH transformation and scaler** to the same 175,777 INCART windows and 32 patient groups. No INCART centering constant, global scale, threshold, or epoch may be fitted. Window-level median/MAD uses each external window alone, as specified above; this is an input algorithm, not fitted external calibration. Compare to the already measured raw reference but label the comparison exploratory because INCART exposed the failure that motivated these arms. Do not choose an arm solely by INCART macro F1 and call the dataset final.

## Cost, success rule, and limits

The prior three-arm run took 77 seconds on one RTX 3090. A two-arm centered/robust job should plausibly finish within a **10-minute one-GPU cap**, with the same roughly 160 MB MIT-BIH window arrays. INCART arrays already occupy about 253 MB; a forward pass took 12 seconds of Slurm time. The program must stop before its wall cap and keep all failed/partial artifacts. A useful engineering result would improve INCART N and S precision without losing MIT-BIH S/V substantially; no single aggregate threshold will be treated as proof of generalization. If both new arms worsen MIT-BIH validation, stop architecture expansion and revisit preprocessing and labels. A cheaper alternative is only the centered arm, but the robust-scale arm directly probes the wide external amplitude range.

The planned two-arm comparison tests preprocessing, not a novel architecture or clinical safety. Later paper-inspired attention/multi-scale models should be compared under whichever preprocessing is defensible, with a new untouched confirmation source or reserved subjects. The UI remains a later demonstration.

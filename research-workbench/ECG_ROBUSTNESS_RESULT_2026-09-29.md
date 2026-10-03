# Project 3: fixed ECG amplitude comparison result

## What ran

The [frozen comparison protocol](ECG_ROBUSTNESS_COMPARISON_PROTOCOL_2026-09-29.md) was implemented in `implementation/ecg_robustness_compare.py` and run as Slurm job **21728971** on one RTX 3090. It completed successfully in 55 seconds of Slurm time (45.1 seconds measured in the program). The two new arms used the same 69,842 MIT-BIH training, 13,708 validation, and 17,029 inspected development-test targets, the same 9,188-parameter single-beat CNN, training weights, seed, 12 epochs, and lowest unweighted validation-cross-entropy selection. Each selected epoch 10. INCART was evaluated with frozen MIT-BIH preprocessing on 175,777 beats from 32 patients. This was a development comparison: the INCART failure prompted it.

Source hashes: runner `fab9945c2646f5db0e9710326270050dacefd7fb080d626d29a72c1ed4ce0ed3`; waveform transform `377c29762ab2aede062f6c580181a565775a84b07f0c8002cf7ffcb04e3c77ae`; result JSON `7d3ae262ec3e2007cc9c9ba536cfd949db9a272288edb57a49d62add83b233ed`. The MIT-BIH context/split and INCART manifest hashes match the prior fixed results. Cluster checks passed for train-only scaling, offset invariance, and flat-window finiteness. Saved checkpoints remain on the cluster at `/home/guykalat/codex_ecg_robustness_20260929/output/`: centered SHA-256 `d33678d4b77da35a03566e2c8e9cd43125b27f78ab2a2373af1df6f6eb989e15`, robust SHA-256 `2f46ea622bb47d616ac078963cd0ebab05b40edcc46e2dc7a2ddfd74602a9719`.

## Main result

| Model | MIT-BIH macro F1 | INCART macro F1 | INCART accuracy | INCART S precision / recall | INCART V precision / recall | INCART F recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Existing raw weighted reference | 0.555 | 0.233 | 0.470 | 0.008 / 0.150 | 0.200 / 0.655 | 0 / 219 |
| Window centered | **0.634** | **0.402** | 0.843 | 0.017 / 0.109 | 0.646 / 0.695 | 0 / 219 |
| Window robust scale | 0.547 | 0.388 | 0.877 | 0.007 / 0.015 | 0.602 / 0.622 | 0 / 219 |

For the centered arm, MIT-BIH S precision/recall was 0.737/0.634 (272/429 S beats found), and V was 0.828/0.923. It still found 0/384 MIT-BIH F beats. On INCART, it found only 214/1,958 S beats and 0/219 F beats. Its 214 S predictions that were correct came with 11,753 normal beats incorrectly called S; this makes the S precision **1.7%** despite higher aggregate macro F1. The robust arm found only 30/1,958 INCART S beats. INCART patient-level macro F1 for centered ranged from 0.254 to 0.879, so the aggregate masks substantial patient variation.

The centered arm's INCART cross entropy was 0.617, Brier score 0.264, and 10-bin ECE 0.057, versus the raw reference's 2.556, 0.886, and 0.379. The robust arm had lower INCART cross entropy (0.495) and Brier (0.204), but lower macro F1 and much poorer S recall than centering. These scores are on annotated reference beats, not a beat-detection pipeline or prospective clinical data.

## Interpretation and next gate

Per-window centering helped on both inspected datasets under the fixed comparison; the result supports treating raw amplitude/baseline handling as a real engineering problem. It does **not** establish amplitude shift as the sole cause of the original transfer failure, because the new arms were retrained and INCART motivated the intervention. Neither arm solves rare-class recognition, particularly F. Window centering is the current development reference for a paper-informed architecture or label/context study, but any claim of generalization needs a newly reserved confirmation set or subjects. Preserve INCART as development evidence and compare later models on the same subject-aware protocol without selecting a final model solely from this score.

Machine-readable metrics, complete confusion matrices, per-subject and per-patient breakdowns, histories, scaling constants, and checkpoint hashes are in `implementation/ecg_robustness_result_2026-09-29.json`.

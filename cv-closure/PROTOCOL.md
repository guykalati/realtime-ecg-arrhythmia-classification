# CV closure: five-class CNN and monitoring demo

Frozen before submission on 2026-10-03. Use all 109,438 existing finite 360-sample MIT-BIH windows, including paced subjects and Q. Retain the existing subject split (201/202 grouped), with paced subjects in all three partitions. Every partition must contain N/S/V/F/Q. Raw mV, MLII when available; V5 for 102/104. Mean and standard deviation fit on training only. Annotated reference peaks are provided; this does not evaluate peak detection.

One seed (20261003), 24 epochs, batch 256, AdamW 0.001/0.0001, square-root inverse training frequency cross entropy. CNN: 16/32/64 channels, kernels 7/5/3, ReLU, max pooling, global average, five logits. Select lowest unweighted validation cross entropy; evaluate held-out subjects once. Report accuracy, macro/weighted F1, every class, confusion matrix and source/data/checkpoint hashes. 1 RTX 3090, 2 CPUs, 8 GB RAM, 30 minute Slurm cap and 25 minute internal cap. No hyperparameter search against test results.

Export the actual selected model for a local replay interface. Verify NumPy inference against stored PyTorch logits. Show waveform, predicted class, annotated class and simulated alerts; start/pause/reset must work. Alerts are simulation rules, not clinical warnings. Original 98.02% beat-split result remains historical; use the new measured score for any new claim.

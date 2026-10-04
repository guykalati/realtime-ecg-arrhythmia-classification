# Understanding the ECG project

A study guide for Guy Kalati. This guide covers the completed five-class CNN and recorded-beat replay. The separate four-class robustness experiments have different cohorts and metrics. Keep those results separate in an interview.

## 1. Start with the actual task

I trained a neural network to classify one-second ECG windows around annotated heartbeats. I reconstructed the data from raw MIT-BIH records so I could keep each person's recordings in one split. I then exported the selected model and built an interface that displays recorded beats, model predictions and simulated alerts.

The model classifies windows whose beat locations are already known. It does not detect beats in a continuous signal, diagnose a patient or run a validated hospital monitor. It is deep learning for a one-dimensional physiological signal. A CNN and a visual interface do not make this a computer-vision project.

**First exercise:** explain the input, output and evaluation unit. Input: 360 signal samples. Output: five class logits. Evaluation unit: a beat window, with people kept separate between splits.

## 2. ECG and sampling, without medical jargon

An ECG records electrical activity associated with the heartbeat. The waveform has changes in voltage over time. Classification can use those shapes, but an annotated beat label is not the same thing as a full clinical diagnosis.

The source recordings have two leads sampled at 360 Hz. A sample is one voltage measurement; a beat window contains 360 samples, or one second. A record contains many beats from one person. The MIT-BIH database contains 48 recordings from 47 subjects. Two recordings can belong to the same person, which matters for splitting. [PhysioNet source](https://physionet.org/content/mitdb/1.0.0/).

The extractor uses physical voltage values from WFDB, in mV. It selects MLII by lead name when available and V5 for records 102/104. A lead change can alter morphology. Those two V5 records are part of this task, not silently treated as identical measurements.

The annotated reference location centers each window. The extractor uses samples [R−180,R+180), without resampling or padding. It drops boundary/nonfinite windows. The half-second after the reference beat means the waveform is not available at the instant of the beat. This creates input-acquisition latency even if model inference is fast.

## 3. Labels, people and data quality

The implementation uses an AAMI-style five-class mapping:

| Class | Group meaning | Source symbols in the code |
|---|---|---|
| N | Normal-category/non-ectopic group, including mapped conduction types | N L R e j |
| S | Supraventricular ectopic group | A a J S |
| V | Ventricular ectopic group | V E |
| F | Fusion of normal and ventricular beat | F |
| Q | Paced, paced-fusion or unclassified group | Q / f |

N does not mean every mapped source symbol is an ordinary sinus beat. Q is not an "unknown disease" probability or a model abstention output. It is a dataset label group. The mapping is explicit in [mitdb_beat_manifest.py](../cv-closure/mitdb_beat_manifest.py); do not claim certified compliance with every AAMI evaluation convention.

The CV run retains paced subjects and Q to match the five-class task. Many research protocols exclude paced records. Results from those tasks have different populations and class distributions.

Raw headers, annotations, window identities and hashes preserve source provenance. Records 201/202 share a patient group, so they remain together. The split guard checks group separation. Record separation alone would be insufficient if two records belonged to the same person.

## 4. Why the split changes the meaning of accuracy

A random beat split can place similar beats from one person's recording in both training and test. A model may exploit person-specific morphology, acquisition conditions or nearby examples. This can produce an optimistic estimate of performance on a new person.

A subject-disjoint split assigns a person to exactly one partition. It asks a harder and more useful question: does the learned representation classify beats from held-out subjects? It still uses the same database and acquisition setting, so it is not an external hospital validation.

| Partition | N | S | V | F | Q | Total |
|---|---:|---:|---:|---:|---:|---:|
| Train | 62,738 | 1,963 | 4,962 | 403 | 4,165 | 74,231 |
| Validation | 12,499 | 389 | 982 | 15 | 2,069 | 15,954 |
| Test | 15,345 | 429 | 1,291 | 384 | 1,804 | 19,253 |

Total 109,438 finite windows. Every partition has all five classes, but validation has only 15 F examples. Presence alone does not provide stable rare-class evaluation. Per-person and grouped uncertainty estimates would be useful before stronger conclusions.

Mean −0.311306 mV and standard deviation 0.477453 mV are fitted on the training windows only. The same constants normalize validation, test and replay inputs: z=(x−mean)/std. Computing these from all data would allow test information into preprocessing. This implementation uses global training normalization, not a separate normalization fitted to each test beat.

## 5. How the 1D CNN works

A convolutional filter slides over time and learns local combinations of the input samples. The same weights apply at different positions. Multiple filters create channels with different learned responses. Calling a particular filter a detector for a clinical feature would require inspection; the architecture alone does not prove that interpretation.

The actual network is small: **9,253 trainable parameters**. It has three Conv1d→ReLU→MaxPool1d blocks, followed by global average pooling and a linear classifier.

| Stage | Shape for batch size B |
|---|---|
| Normalized input | B×1×360 |
| Conv1d 16 channels, kernel 7, same-length padding; pool 2 | B×16×180 |
| Conv1d 32 channels, kernel 5; pool 2 | B×32×90 |
| Conv1d 64 channels, kernel 3; pool 2 | B×64×45 |
| Global average over time | B×64 |
| Linear layer | B×5 |

ReLU clips negative activations to zero. Max pooling retains the largest response in each two-position region and halves temporal resolution. Global average pooling summarizes each final channel, avoiding a large flattened classifier.

The local receptive field before global averaging spans 30 input samples, about 83.3 ms. Global averaging then aggregates those local outputs over the window. The model does not have self-attention, a recurrent layer, a residual network or explicit RR-interval features in this CV run. Those are different research variants.

[Training implementation](../cv-closure/train.py) · [PyTorch Conv1d documentation](https://pytorch.org/docs/stable/generated/torch.nn.Conv1d.html).

## 6. Logits, loss and imbalance

The network outputs five **logits**, unconstrained class scores. Softmax converts them to positive values summing to 1. The predicted class is argmax. High softmax output is not automatically a calibrated probability of correctness.

Cross entropy penalizes low assigned probability for the reference class. The training loss uses weights:

<div class="formula">wᶜ = √(Ntrain / (5 × nᶜ)) &nbsp;&nbsp; Lᵢ ∝ −wʸⁱ log p(yᵢ | xᵢ)</div>

The square root increases rare-class influence less aggressively than full inverse frequency. It is a design choice, not a demonstrated optimum. The test does not choose the weights. PyTorch's weighted mean loss divides by the sum of target weights in the batch, so the displayed epoch training loss should not be treated as ordinary unweighted validation loss.

Backpropagation calculates how each trainable weight affects the loss. AdamW updates the weights using gradient statistics and a separate weight-decay term. An epoch visits the training windows once, in shuffled batches. Validation uses the current network without parameter updates. Dropout and batch normalization are absent from this particular CNN, so there are no such training/evaluation behavior changes to explain.

Training uses seed 20261003, batch 256, AdamW learning rate 0.001 and weight decay 0.0001 for 24 epochs. There is no SMOTE in this runner. Oversampling before splitting could share synthetic information across splits; adding resampling later should operate only on training subjects and preserve the protocol.

The checkpoint with the lowest **unweighted validation cross entropy** is selected, here epoch 9. Test predictions come from that selected state. The code does not pick the highest test accuracy or the epoch with the best test F1.

A loss chosen for general average fit may underserve rare classes. The selected epoch has validation macro F1 about 0.346, and the final epoch is not the chosen checkpoint. A future class-aware selection rule must be decided on development evidence before a fresh comparison; do not retroactively change this result.

## 7. Metrics you must be able to calculate

Accuracy is correct predictions divided by all predictions. A classifier predicting N for every test beat would get about 79.70% accuracy here. That is an arithmetic majority baseline, not a separately trained model.

For class c, precision=TP/(TP+FP), recall=TP/(TP+FN), and F1=2 precision×recall/(precision+recall). Precision asks how often a predicted class is correct. Recall asks how many reference examples of that class are found.

Macro F1 averages the five class F1 values equally. Weighted F1 weights them by class support. Weighted F1 can remain high when an infrequent class fails. Macro F1 also hides which specific class failed; per-class results and counts remain necessary.

| Class | Test support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| N | 15,345 | 0.9650 | 0.9794 | 0.9722 |
| S | 429 | 0.5041 | 0.7133 | 0.5907 |
| V | 1,291 | 0.8078 | 0.9280 | 0.8637 |
| F | 384 | 0 | 0 | 0 |
| Q | 1,804 | 0.9981 | 0.8780 | 0.9342 |

Overall accuracy 94.10%, macro F1 **0.6722**, weighted F1 **0.9334**. These describe one seed and this fixed patient split. The frozen model missed **all 384 F beats**. Of those, 155 were classified N, 15 S and 214 V. It predicted F twice on other classes, both wrong.

This is more informative than saying "94% accurate." A high majority-class result cannot support a reliable fusion-beat detector. The validation F support 15 and different held-out subject morphology are plausible investigation targets, not established explanations for every miss.

## 8. What changed from the original project?

The original course notebook used presegmented 187-value Kaggle rows derived from MIT-BIH. It reported 98.02% held-out beat accuracy, but those rows did not preserve patient IDs, so subject-disjoint generalization could not be established. The old accuracy is a historical result, not necessarily fabricated and not interchangeable with the new score.

The new run changes source representation, window length, sampling rate, architecture and splitting. A lower new accuracy does not isolate a model regression: several conditions changed. The original notebook has additional architecture/resampling branches; the closure run is the explicit simple CNN described here.

The derivative data/task trace back to [Kachuee et al.](https://arxiv.org/abs/1805.00794). This run does not reproduce their residual network or transfer experiment. Likewise, similarity to a CNN-attention-Transformer paper does not establish a verified reproduction of that paper.

The former `ECG_APP.py` serialized scaler/transformation output. It did not demonstrate monitoring. The new replay has an actual model inference path, waveform display, reference labels and simulated alerts. That fills the interface gap without claiming live acquisition.

## 9. Export, inference and the interface

The selected PyTorch weights are exported to a NumPy archive. `demo.py` implements the same padded convolutions, ReLUs, pooling, global average and linear layer using NumPy. It applies the saved training normalization.

The initial replay logits came from GPU inference and showed small reduced-precision convolution differences from independent float32 CPU inference. The verified CPU replay and NumPy implementation agree within about 3.82×10⁻⁶ maximum logit difference over 50 beats, with identical predicted classes. That tolerance test catches export/implementation mistakes; it is not a new statistical model evaluation.

The interface's server predicts on each requested recorded beat. It displays the waveform, reference class, predicted class and softmax values. Start advances through the records; pause stops advancement; reset clears the sequence and simulated alert history. Any predicted non-N class triggers the demo's alert rule. That rule does not encode clinical thresholds or an alarm management protocol.

The replay selects ten test examples from each reference class. This balanced 50-beat set is useful for demonstration, but does not match test prevalence and is not an independent second test. Model inference measured about 0.51 ms median on small NumPy windows, excluding server/browser overhead and the half-second future input requirement.

The public project page displays saved predictions, clearly labeled as recorded results. The runnable monitoring demo executes the model. Those two experiences should not be confused.

## 10. Separate research experiments

A four-class workbench explores timing features, multi-scale models, selective prediction and subject-adversarial learning. Its cohort excludes some paced/Q data, so its metrics are not replacements for the five-class CV table.

The 18-cell subject-adversarial experiment uses a gradient reversal objective to discourage training-subject identity information in representations. Validation selects penalty 0.05. Across six matched cells, four-class MIT macro F1 rises 0.5843→0.6005 and INCART 0.4984→0.5168. However, MIT F false positives rise from 5.83 to 9.67 mean counts, above the frozen allowance. The candidate is rejected and the prior reference is retained.

Those improvements are development evidence. INCART was inspected during development, EDB remains unscored and SVDB remains sealed. Multiple seeds/partitions are not multiple independent patient cohorts. Do not call this independent external confirmation or an accepted better model. [Full result](../research-workbench/ECG_SUBJECT_ADVERSARY_RESULT_2026-10-03.md).

## 11. Reproduce and navigate

From the repository root, `cd cv-closure`. Install NumPy in an isolated environment and run:

```sh
python demo.py --verify
python verify_results.py
python demo.py --port 8793
```

Open `http://127.0.0.1:8793`. The portable weights and verified replay are included. Raw data and the PyTorch checkpoint remain outside Git. To retrain, use the source download/window commands and CUDA environment in [the run instructions](../cv-closure/README.md), with a new output directory.

| File | What to trace |
|---|---|
| mitdb_beat_manifest.py | Symbols, leads and 201/202 grouping |
| mitdb_windows.py | Reference-centered 360-sample extraction |
| split.csv / ecg_split_guard.py | Subject assignment and split checks |
| train.py | Training-only normalization, CNN, loss, validation selection |
| output/result.json | Counts, history, every-class scores and confusion matrix |
| output/test_predictions.npz | All 19,253 held-out reference/predicted labels |
| demo.py | Exported model inference and simulation server |
| verify_export.py / verify_results.py | Numerical parity and score verification |

## 12. Interview drill

<details><summary>Why is this deep learning? Is it computer vision?</summary>

The CNN learns multiple layers of representations from raw waveform values through gradient-based training. It is deep learning for a 1 Dtime series. There are no input images in this run. The waveform visualization is an interface, not a computer-vision input pipeline.

</details>

<details><summary>What exactly is a sample: a patient, a recording or a beat?</summary>

Each model example is a 360-sample beat window. There are 109,438 windows from 48 records and 47 subject groups. The test contains 19,253 windows, but those are correlated within people. I should not call them 19,253 independent patients.

</details>

<details><summary>Why group 201 and 202?</summary>

They are recordings from the same subject. Keeping only record IDs separate would allow that person's data into more than one partition. The split helper and manifest use a shared subject group for both.

</details>

<details><summary>Why did accuracy fall from 98.02% to 94.10%?</summary>

The new protocol holds people out and uses raw 360 Hz windows, a different network and different source processing. The old result was a held-out beat split without recoverable patient IDs. The numbers answer different questions. A matched experiment would be needed to isolate any architecture effect.

</details>

<details><summary>Does 94% accuracy imply a good arrhythmia detector?</summary>

No. N dominates the test and F has zero recall. This is reference-window classification, not continuous detection. I report macro F1, every-class metrics and confusion counts before discussing practical use.

</details>

<details><summary>How did class weighting affect F?</summary>

It increases F's influence during training, but did not prevent zero test recall. Weighting does not create new patient diversity or guarantee a separable representation. This experiment did not compare weighting alternatives under a frozen budget.

</details>

<details><summary>Why fit normalization on training only?</summary>

The transformation must be learned without test information. Save training mean/std and reuse them at evaluation and inference. Fitting to all data or refitting on the replay would change the effective procedure and could leak evaluation information.

</details>

<details><summary>What is the output shape after each layer?</summary>

B×1×360 becomes B×16×180, then B×32×90, then B×64×45 after each convolution/pooling pair. Global average yields B×64; linear gives B×5. The same padding preserves length before each pool.

</details>

<details><summary>How many parameters and what is the receptive field?</summary>

Convolutions contribute 128,2,592 and 6,208 parameters, and the classifier 325, total 9,253. The local final receptive field before averaging is 30 samples. Global average aggregates across the whole window, so a local receptive field is not the total input used by the classifier.

</details>

<details><summary>Why select epoch 9 if another epoch has better F1?</summary>

The frozen selection criterion is lowest unweighted validation cross entropy. Choosing a different metric after viewing test results would change the experiment. A future rare-class objective should be selected in development before a fresh held-out comparison.

</details>

<details><summary>How do you know the local export runs the same model?</summary>

The archive preserves selected weights and normalization. An independent CPU PyTorch reference and NumPy path match all 50 replay argmax classes within a small logit tolerance. The saved audit records hashes and numerical differences.

</details>

<details><summary>Are the softmax values calibrated confidence?</summary>

They are normalized model scores. Calibration needs separate evaluation, such as reliability plots, Brier score or calibration error, fitted only on development data if adjustment is used. This five-class run does not establish calibrated confidence or clinical risk.

</details>

<details><summary>Would this work on a wearable or hospital stream?</summary>

That requires a beat detector, streaming preprocessing, lead/noise handling, latency budgeting and prospective/external validation. Centered windows use future samples. The present replay cannot establish any of those deployment properties.

</details>

<details><summary>How would you evaluate uncertainty?</summary>

Resample at the subject level rather than independently bootstrapping highly correlated beats. Report per-class variation and repeated-seed results under the same split protocol. This single run has point estimates, not confidence intervals.

</details>

<details><summary>What would you investigate about F first?</summary>

Inspect F's source subjects and morphology, the train/validation support, lead differences and confusion with V/N. Then propose a fixed development experiment. I would not adjust thresholds on the 19,253 test labels to improve the headline.

</details>

<details><summary>Can you compare the five-class score with INCART macro F1?</summary>

Only after matching population, label mapping, leads, preprocessing and metrics. The existing INCART research comparison is a separate four-class development task. It cannot be inserted into the five-class result table as confirmation.

</details>

<details><summary>What did the interface prove?</summary>

The selected exported model executes on recorded windows, displays predictions and supports start/pause/reset with simulated alerts. Browser checks prove those functions worked. They do not validate real sensor acquisition or medical alarm decisions.

</details>

<details><summary>What is your ownership statement?</summary>

The original ECG course project was joint work. The current successor reconstructs record-linked data, enforces patient groups, runs the explicit CNN evaluation, exports the model and adds the replay. The extension used AI coding assistance. I should explain this work and its checks without claiming the dataset or prior team's work as my invention.

</details>

<details><summary>Why not add a Transformer now?</summary>

The current failure could arise from data, labels, split support or decisions as well as representation capacity. A new architecture should test a hypothesis against the same protocol. A larger model alone would not validate patients, beat detection or clinical use.

</details>

<details><summary>What do the research guardrails teach you?</summary>

The subject-adversarial candidate improved macro F1 but failed the prespecified F false-positive allowance. Retaining the prior reference respects the actual acceptance criterion. Changing that criterion after seeing the result would weaken the evidence.

</details>

## 13. Whiteboard exercises and readiness check

1. Draw signal→reference location→360-sample window→training normalization→CNN→class scores→recorded replay.
2. Calculate the majority-class accuracy 15,345/19,253 and explain why it can hide zero F recall.
3. From the F confusion row [155,15,214,0,0], identify support, TP and FN. Answer: support 384, TP 0, FN 384.
4. Calculate receptive field: start 1; conv 7→7; pool 2→8; conv 5 at stride 2→16; pool 2→18; conv 3 at stride 4→26; pool 2→30.
5. Explain why 0.51 ms inference cannot be the full live response time when input includes half a second after the reference beat.

You are ready when you can reconstruct the shapes, explain the split and preprocessing, calculate class metrics, and show where the model misses F. If a question asks about deployment, state what the replay establishes and design the missing evaluation.

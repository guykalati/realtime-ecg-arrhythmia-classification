# ECG: next substantive methods — 3 October 2026

## Decision

Start with **explicit beat timing alongside the existing waveform CNN**. Then test a small subject-adversarial objective on the same inputs. A larger second stage can study synchronized cross-lead pretraining. These changes address missing rhythm information and transfer across people/leads; simply extending the previous multi-scale or longer-training runs is weakly motivated by our development results.

This is research and protocol advice. No training, downloading, model scoring, or sealed SVDB access was performed for this note. Current run counts and results below were supplied by the active project handoff, not independently recomputed here.

The current classifier predicts N/S/V/F for annotated beats. MIT-BIH and INCART are development sources. EDB's selected V5 subset has 51 documented subject groups and 486,681 prepared windows, including 343 F beats. The exact-input comparison found zero cross-source matches among 771,896 prepared windows. That result cannot establish cross-release patient independence or exclude transformed recordings. Preserve the [identity protocol](ECG_EDB_IDENTITY_PROTOCOL_RESEARCH_2026-10-01.md) and keep SVDB sealed.

## What newer papers actually add

**Verified direct CAT-Net comparison:** Rodriguez and Nafea's 2025 HAN preprint compares a convolution/LSTM/two-level-attention model with CAT-Net on MIT-BIH and PTB-XL. It reports 76,265 versus 1,189,637 parameters on MIT-BIH, with 98.55% versus 99.14% accuracy. Its 60/20/20 split does not identify patient partitions. Training-only SMOTE is stated. PTB-XL record statements are handled as five-class targets even though the underlying dataset supports multiple statements per ECG. These results support an efficiency hypothesis, but do not establish unseen-patient N/S/V/F superiority. Attention plots are exploratory explanations. The model processes segments inside a beat; it is not automatically a neighboring-beat rhythm model. [Author full text](https://arxiv.org/html/2504.03703v1).

**Unverified implementation leads from the previous review:** The Qin et al. 2026 dilated ResNet/BiLSTM article and the Diao 2026 multi-beat article remain candidates, but publisher access failed in this pass. Their full splits, code, label mappings and per-class confusion counts were not verified from primary full text. Do not use secondary abstract mirrors as reproduction specifications or rank their headline accuracy against our results. [Qin publisher DOI](https://doi.org/10.1088/1361-6501/ae8615), [Diao publisher page](https://www.sciencedirect.com/science/article/pii/S1746809426011353).

**Newer independent representation-learning direction:** Dade et al. 2026 combines physiological/VCG transformations, lead views and patient-aware contrastive sampling, including a dual-stream encoder. Approximately one million unlabeled ECGs support pretraining; downstream tasks are low LVEF and elevated potassium, with frozen and fine-tuned evaluation at different supervision fractions. Those are record-level tasks, not our F-beat task. Their work motivates studying lead transfer; it does not establish that this recipe will improve rare beat detection. The inspected author-hosted manuscript does not supply a verified public end-to-end implementation for our task. [Author-hosted full manuscript](https://publications.sci.utah.edu/publications/Dad2026a/1-s2.0-S2666501826000280-main.pdf).

## Candidate 1 — CNN morphology plus past RR timing

### Source basis and limits

Zhang et al. 2021 supplies both normalized pre-RR and previous-ten-RR ratio features to a CNN, alongside a subject adversary. It reports RR ablations and S/V-focused performance on MIT-BIH DS1/DS2. Important limitations: the first ratio uses the whole-record mean, validation is a random 20% of training beats. The paper claims DS1/DS2 patient separation but does not establish a subject-disjoint validation split. It acknowledges unsatisfactory F/Q classification in its confusion matrix; its record-level table and primary comparison emphasize N/S/V, not a convincing F improvement. Its DS1/DS2 patient-independence claim is not accepted here without an explicit record/group audit, especially for 201/202. The text also contains an input-length inconsistency: preprocessing says 128 samples, a later visualization paragraph says 256. Do not reproduce an input shape from that paragraph without checking the architecture. [Publisher full text, §§2.2, 3.2, 4.1–4.3](https://onlinelibrary.wiley.com/doi/10.1155/2021/9946596).

### Our proposed controlled change

- Preserve the existing centered waveform and CNN embedding. Concatenate a small timing vector before its classification head: preceding RR in seconds, preceding RR divided by the median of the previous ten valid intervals, and a history-availability mask. Fit any feature scaling on training groups only.
- Use timestamps from the same pinned annotation stream, including documented rules for non-target beat types and rhythm/quality annotations. Never infer time gaps from indices in a filtered N/S/V/F table. Retain record-local context before label filtering.
- The proposed median differs from the source paper’s mean: it is a robust past-only baseline. The denominator ends before the current RR; do not use full-record or subsequent intervals. Freeze treatment of startup/missing/invalid intervals. Report how many classified beats have complete timing history by class and source.
- Compare waveform-only, timing-only, and waveform-plus-timing under identical frozen subject splits, seeds, weighting, checkpoint rules and finite resource caps. This isolates information gain from an unrelated backbone change.
- Report annotation-assisted beat classification. A prospective monitor also requires a separately evaluated R-peak detector and disclosure that the existing centered one-second waveform requires approximately 0.5 seconds after the current R peak, so no live-at-R-peak claim is justified. Past-only timing alone does not make the whole system causal.

**Expected useful question:** does explicit timing improve S precision/recall across people without sacrificing F? This is a hypothesis. Timing alone may contribute little to F morphology.

## Candidate 2 — subject-adversarial regularization

The same Zhang source provides an encoder/classifier/subject-adversary formulation; its ablation and adversarial-weight discussion justify a separate controlled objective test, not copying its headline score.

### Our proposed controlled change

- Add a training-only linear head that predicts documented training subject groups from the embedding, with gradient reversal toward the encoder. Keep ordinary N/S/V/F classification loss. Group MIT records 201 and 202 together; INCART's source Holter patient groups also remain intact.
- First use MIT development training groups only. Compare the selected waveform/timing model with and without this head; use a small frozen weight grid selected exclusively on subject-disjoint validation. A larger subject head or more epochs is not required for the first test.
- Log classification and adversary losses, per-class metrics and training-group class support. Rare F is concentrated in a few people; suppressing identity can inadvertently suppress genuine F evidence. Lower subject-identification accuracy is not itself success.
- INCART is a separate development transport assessment. Do not train on its evaluation patients through either supervised or unlabeled objectives in this experiment. This makes the test domain generalization; target-data adaptation would be a separately named protocol.

**Expected useful question:** can the same beat information become less dependent on training people while retaining S/F discrimination? Require class-specific gains and stable calibration; reject a macro gain obtained by losing rare-class recall.

## Candidate 3 — synchronized cross-lead representation pretraining

### Source basis and limits

CLOCS explicitly learns patient-specific representations through temporal and lead views, using same-patient positives. Its downstream experiments include Chapman, PhysioNet 2020 and Cardiology; they are not a demonstrated rare F-beat solution. The authors provide PyTorch code under CC BY-NC-SA 4.0. Patient-specific contrastive positives also pursue a different representation goal from Candidate 2's identity suppression. [ICML paper](https://proceedings.mlr.press/v139/kiyasseh21a/kiyasseh21a.pdf), [official code and license](https://github.com/danikiyasseh/CLOCS).

### Our proposed controlled change

- Begin with synchronized lead views of the **same beat or same short episode** in authorized training groups only. Use a shared single-lead encoder plus a removable projection head. Contrastive positives share timestamp/episode across leads; do not make every beat from the same person positive, which could encourage N/F collapse.
- Compare random initialization with equal-budget within-lead augmentation pretraining and cross-lead pretraining, followed by the same supervised classifier. Evaluate both frozen encoder and fine-tuning if the initial finite screen supports expansion. Count extra pretraining compute separately.
- The present window arrays contain only the selected lead. Additional training-lead extraction requires a new versioned artifact from existing raw recordings, lead inventory, units/scaling, annotation alignment, resampling hashes and a fresh finite protocol. Never reconstruct VCG from a single lead; arbitrary polarity/time reversals can destroy task information.
- Reserve validation/evaluation subject groups from all pretraining. Use MIT MLII and INCART II as separately reported known-source assessments; EDB V5 can provide a later lead-shift development assessment only after its role, recording-overlap screen and grouped partition are frozen. Do not score EDB yet. Keep SVDB untouched.
- Later scale-up may use PTB-XL v1.0.3 training patient folds for unlabeled pretraining, with separate overlap/version checks. Its record-level diagnoses cannot be converted into N/S/V/F beat labels. No download is authorized by this research note itself. [Official PTB-XL release and folds](https://physionet.org/content/ptb-xl/1.0.3/).

**Expected useful question:** does pretraining across synchronized lead views improve subsequent beat classification on a different lead/source? This adapted objective is a proposed project contribution; no literature-novelty claim is established.

## Shared reporting and decision rules

Freeze each candidate's finite run ledger before execution. Reuse the existing development partitions rather than quietly creating easier splits. Preserve every negative result and compare matched seeds. Use two existing development partitions and three seeds for any expanded result claim; the initial technical screen can be smaller and explicitly labeled.

Every result must include N/S/V/F support, precision, recall and F1; confusion counts; S/F false positives and missed beats; subjects with each class; per-subject metric spread; macro F1, NLL/Brier/calibration; parameters, training time, memory and inference latency. Patient-group bootstrap intervals are preferable to beat bootstrap; when too few F groups support an interval, publish counts and the limitation. If abstention is evaluated, also report class-specific coverage and retained S/F errors. Keep four-class macro F1 separate from any three-class or S/V-only paper metric.

Do not rebalance validation/evaluation, generate synthetic beats before splitting, or select a checkpoint on external evaluation outcomes. An improvement must be visible in rare-class precision/recall and subject spread, not just accuracy. No fixed numerical acceptance threshold is prescribed by this note: select those thresholds in the experiment protocol before observing new scores.

**Order:** RR feature audit and matched ablation → subject-adversary ablation → cross-lead pretraining after its artifact/overlap gates. HAN remains a reasonable later efficiency comparator; it is not the highest-priority fix for current S/F failure. Domain adaptation using target unlabeled data and million-record pretraining are larger protocol changes, not required to begin the first two candidates.

# Project 2: first Karpathy-style experiment-mode run

## Purpose

Make experiment mode runnable before attributing any improvement to an autonomous agent. Follow [Karpathy's autoresearch](https://github.com/karpathy/autoresearch): immutable `prepare.py` and data manifest, one editable `train.py`, human `program.md`, fixed training time, and one validation metric. The upstream default was tested on an H100 and is not copied unchanged to the university RTX 3090. This is an infrastructure and baseline run, not the final research dataset or a claim that experiment memory helps.

## Frozen task and scope

- Public source: [karpathy/tinystories-gpt4-clean](https://huggingface.co/datasets/karpathy/tinystories-gpt4-clean), revision `0397e27157956705a0260709da3095bb9c43d6a7`, license listed as CDLA Sharing 1.0 in its dataset card. Synthetic English short stories are a low-entropy engineering task recommended for smaller compute by the upstream README; they are not a substitute for Project 1's biomedical corpus.
- Data prep: stream at most 300,000 source rows. Deduplicate exact story text by SHA-256. Assign each unique story to validation when the first 32 hash bits modulo 16 equal zero, otherwise to training. Concatenate UTF-8 story bytes with two newline bytes. Stop after at least **128 MiB training** and **2 MiB validation**; one final story may overshoot each target. The `train.bin` and `val.bin` files and their checksums are fixed for all candidates. No test score is opened in this first development batch.
- Model task: next-byte prediction with vocabulary 256 and context length 256. The initial `train.py` uses a small causal Transformer (two layers, width 256, four attention heads). One single NVIDIA RTX 3090. Training time **300 seconds**, excluding startup and final validation; one run has a 10-minute Slurm wall cap. Metric: **validation bits per byte**, lower is better, calculated as average cross entropy in nats divided by ln 2 on a fixed nonoverlapping validation prefix. Save checkpoint, code hash, data hashes, steps, runtime, GPU memory, and metric.
- First batch ceiling: one unchanged baseline plus at most two candidate runs, each at most 300 seconds training, at most **15 GPU-minutes training** total plus startup/evaluation overhead. Preparation is CPU only with a 15-minute wall cap, <500 MB saved local data, and no package install. A candidate may change only `train.py`; `prepare.py`, manifest, split, budget, and validation calculation remain fixed. Any candidate agent execution needs a restricted environment without home credentials or unrelated files before launch.

## Interpretation and continuation

The initial metric checks that the loop actually trains. One run cannot establish research progress. After the baseline, compare model-proposed code under the same budget and preserve failures. The proposed personal addition is development-history retrieval before a candidate proposal; its value requires paired runs across more than one task or seed. Do not expose a held-out test or choose a winner from one noisy run. A larger text or tabular task can follow once this bounded setup works and the user can review its measured cost.

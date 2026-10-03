# Sherlock Holmes LLM adaptation (course team project)

This portfolio copy contains notebooks and configs from a two-part Advanced LLM course submission that names Guy Kalati and Amiti Kelerman. Guy confirms that he implemented this project himself. Treat the saved results below as course artifacts, not as a fresh reproduction.

## What the work does

- **HW1:** Continued language-model training on nine Sherlock Holmes texts using QLoRA adapters on `Qwen/Qwen2.5-3B-Instruct`. The saved grid varies LoRA targets, rank, learning rate, dropout, and sequence length.
- **HW2:** Supervised fine-tuning on Sherlock question-answer examples. The course pipeline loads the Qwen base model, merges a selected HW1 adapter, and trains a separate SFT adapter. The selected saved run used manual response-only masking in the final submission notebook; the earlier `scripts/train_sft.py` defaults to full-sequence loss.

Continued training learns from text without question-answer targets; SFT learns to produce answers in a specified format. They are separate stages and have separate evaluations.

## Saved evidence

| Stage | Specific saved artifact | Result | Limit |
| --- | --- | --- | --- |
| HW1 | `rank_r16_lr2e4_attn_mlp/metrics_summary.json` in the original course submission | Validation perplexity 13.467 before, 11.767 after | Saved output, not rerun here; the corpus is small and literary style is narrow. |
| HW1 | `attn_only_r16_lr2e4/metrics_summary.json` | Validation perplexity 11.981 after | Comparable target-module experiment, but this does not establish broad model quality. |
| HW2 | `summary_response_only_lr2e4_final.json` in the original course submission | Three-shot exact-match accuracy 0.0755 and F1 0.1903 on 106 examples | Weak absolute QA performance; evaluation settings and answer normalization matter. |

The source submissions and saved run artifacts are in the original `Advanced LLM/HW1` and `Advanced LLM/HW2` folders. This copy does not include the source text, adapters, full saved outputs, or a clean-environment reproduction command. The HW2 config's absolute `hw1_best_adapter` path does not exist on this machine, and the selected response-only run lives in a later final-submission notebook. The notebook and configs in this copy alone are insufficient to reproduce the table above.

## Files in this copy

- `sherlock_lora_peft_fine_tuning.ipynb`: HW1 notebook copy.
- `sherlock_sft_alignment.ipynb`: HW2 notebook copy.
- `hw1_config.json`, `hw2_config.json`: configuration copies.
- `CLUSTER_RUN_GUIDE.md`: course execution notes; paths and environment must be adapted before running.

No 7B full-SFT, Llama-3, ROUGE, or cross-model VRAM benchmark is supported by the inspected saved runs. A defensible new result requires a clean rerun with pinned data, environment, config, and output. The next technical step is to make Guy's existing work runnable and explainable, then develop a larger personal extension.

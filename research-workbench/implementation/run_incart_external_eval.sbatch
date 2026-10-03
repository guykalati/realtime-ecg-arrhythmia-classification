#!/bin/bash
#SBATCH --job-name=ecg_incart_external
#SBATCH --partition=rtx3090
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --gres=gpu:rtx_3090:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
PYTHON=/home/guykalat/.conda/envs/hw1_llm/bin/python
"$PYTHON" -c 'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(), flush=True)'
"$PYTHON" incart_external_eval.py windows_360 window_manifest.csv window_summary.json \
  single_weighted_best.pt mitdb_context_result.json external_output

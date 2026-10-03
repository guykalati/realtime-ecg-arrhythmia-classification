#!/bin/bash
#SBATCH --job-name=ecg_multiscale_20260929
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
"$PYTHON" - <<'PY'
import torch
from ecg_multiscale_compare import MultiScaleCNN
model = MultiScaleCNN()
x = torch.randn(3, 1, 360)
rr = torch.zeros(3, 2)
y = model(x, rr)
assert y.shape == (3, 4) and torch.isfinite(y).all()
y.square().mean().backward()
assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
print('synthetic shape/gradient preflight passed', flush=True)
PY
"$PYTHON" ecg_multiscale_compare.py \
  /home/guykalat/codex_ecg_baseline_20260928/windows_360 \
  /home/guykalat/codex_ecg_baseline_20260928/past_context_a.csv \
  /home/guykalat/codex_ecg_baseline_20260928/candidate_split_a.csv \
  /home/guykalat/codex_ecg_incart_external_20260929/windows_360 \
  /home/guykalat/codex_ecg_incart_external_20260929/window_manifest.csv \
  output

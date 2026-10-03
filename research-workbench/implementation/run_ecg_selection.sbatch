#!/bin/bash
#SBATCH --job-name=ecg_selection_20260930
#SBATCH --partition=rtx3090
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --gres=gpu:rtx_3090:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:13:00
#SBATCH --array=0-5%1
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
/home/guykalat/.conda/envs/hw1_llm/bin/python ecg_selection_compare.py ecg_selection_manifest_2026-09-30.json "$SLURM_ARRAY_TASK_ID"

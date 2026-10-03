#!/bin/bash
#SBATCH --job-name=edb_v5_acquire
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:15:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
timeout 850s /home/guykalat/.conda/envs/hw1_llm/bin/python edb_v5_acquire.py

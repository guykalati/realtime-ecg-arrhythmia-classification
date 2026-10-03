#!/bin/bash
#SBATCH --job-name=edb_decode_check
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:08:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
export PYTHONPATH="$SLURM_SUBMIT_DIR/vendor"
timeout 450s /home/guykalat/.conda/envs/hw1_llm/bin/python edb_decode_check.py

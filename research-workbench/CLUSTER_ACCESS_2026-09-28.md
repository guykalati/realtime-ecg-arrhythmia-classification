# BGU cluster read-only access check — 28 September 2026

The user connected the network/VPN and asked for a live access check using the local `cluster-ops` skill template. No job was submitted, cancelled, reprioritized, or synchronized.

## Authentication

- The earlier network timeout is resolved: `slurm.bgu.ac.il:22` was reached.
- Initial `ssh -o BatchMode=yes` failed authentication. SSH debug showed that the server accepted the offered ED25519 public key, while the local agent had no unlocked identities and the private key requires a passphrase.
- `ssh-add --apple-load-keychain` loaded the existing identity from macOS Keychain. A subsequent noninteractive SSH command succeeded as `guykalat` on `slurm-login-01.auth.ad.bgu.ac.il`; `sinfo` and `squeue` are available.
- No new key or password was created or copied. If a later Codex session starts with an empty SSH agent, reload the saved identity from Keychain before a BatchMode check. One later probe timed out, but another succeeded; treat transient connectivity separately from authentication.

## Slurm and storage observations

- `sacctmgr` returned association `cluster | yshahar | normal` for this user (cluster, account, QoS). No per-user GPU or job limit was printed in that association view.
- `squeue -u guykalat` returned no current jobs at check time.
- `sinfo` advertises RTX 3090, 4090, 6000, and RTX Pro 6000 partitions, among others. Some nodes were idle or mixed; this is a momentary pool snapshot, not a reservation or proof of free GPUs for a particular account.
- The `rtx3090` partition reports `AllowAccounts=ALL`, `State=UP`, and `MaxTime=14-00:00:00`. Other partition access rules and GPU memory were not verified.
- `$HOME` is on a shared 412 TB filesystem with 189 TB shown free by `df -h`. `quota -s` printed no user quota, so the **user's personal storage allowance remains unverified**. Common `/scratch`, `/mnt/scratch`, and `/data` paths were not found in the login check. Do not plan article storage from the shared filesystem free-space number alone.
- A later read-only `module avail` filter found CUDA modules through 13.1, with `cuda/12.4` marked default. It found no module name matching Apptainer, Singularity, container, Python, or PyTorch. This does not prove those tools are unavailable on compute nodes; the actual job environment still needs verification.
- Direct command discovery found `/usr/bin/podman` (version 5.6.0), even though no container module appeared. `podman info` reports rootless mode but warns that this account has no subordinate UID/GID ranges and that its image store is on a network filesystem. Container execution/isolation has **not** been tested. Do not infer that a benchmark image will run safely from the successful `info` command.
- `conda` exists and lists a shared `pytorch` environment plus older course environments. Login-node `/usr/bin/python3` is 3.9.25 and does not import torch. The shared `pytorch` environment has Python 3.7.12, PyTorch 1.10.0, and CUDA build 11.2. Guy's existing `hw1_llm` environment has Python 3.11.15, PyTorch 2.5.1+cu124, and CUDA build 12.4. These are package imports on the login node, not proof that a GPU job works or that altering either environment is safe.

## Skill setup boundary

The course-folder `cluster-ops` skill is an operations template. Its `status.sh` requires `REMOTE_USER`, `REMOTE_HOST`, and a specific `REPO_REMOTE`; no project-specific `cluster-ops.env` exists there. The read-only SSH, queue, partition, and association commands above follow its status/setup guidance without inventing a remote repository path. Do not run `preflight.sh` just to inspect access: it performs a remote `git pull --ff-only` and may source project hooks.

**Next gate before GPU work:** identify the intended remote project directory, confirm a usable storage location/quota and chosen GPU's VRAM/software environment, then submit only a bounded approved smoke job. For repair benchmarks, verify Podman's rootless isolation and image storage on an allowed compute node before running generated patches. Current evidence establishes login and Slurm visibility, not a successful GPU allocation or safe benchmark runner.

**GPU update, later 28 September:** Guy approved one bounded ECG baseline. We staged 158 MB of NumPy window arrays plus manifests/code in `/home/guykalat/codex_ecg_baseline_20260928`, verified 52 transferred SHA-256 checksums, and submitted Slurm job **21719608** with `--gres=gpu:rtx_3090:1`, 8 GB RAM, two CPUs, and a 30-minute wall cap. It ran on `cs-3090-02` with an NVIDIA GeForce RTX 3090 and completed in 33 seconds, exit code 0. The [result report](ECG_BASELINE_RESULT_2026-09-28.md) records model metrics. This demonstrates a working GPU allocation and usable existing PyTorch environment for this small job. Personal storage quota and Podman benchmark isolation remain unverified.

**Second GPU update, 28 September:** Guy approved a matched three-arm development comparison. The staged code, context manifest, and Slurm script hashes matched local copies. Job **21723859** used one RTX 3090 allocation, finished in 1 minute 17 seconds with exit code 0, and produced the [comparison result](ECG_CONTEXT_COMPARISON_RESULT_2026-09-28.md). It did not exercise Project 2's container runner or establish a larger-job quota.

**Repair runner update, 28 September:** Project 2's [harness screen](REPAIR_HARNESS_SCREEN_RESULT_2026-09-28.md) tested unprivileged Bubblewrap isolation on a CPU compute node, built an isolated Python 3.8.1 environment, and screened three pinned cases. Two have a genuine buggy-fail/fixed-pass pair. Podman still has the reported rootless mapping and network-store warnings; the repair screen used Bubblewrap instead. No agent-generated patch was run.

**Reconnect and CPU-screen update, later 28 September:** After the user restored connectivity, `slurm.bgu.ac.il` was reachable but the new session initially lacked an unlocked SSH identity. `ssh-add --apple-load-keychain` restored the existing key; BatchMode SSH then succeeded on `slurm-login-03.auth.ad.bgu.ac.il`. The [repair report](REPAIR_HARNESS_SCREEN_RESULT_2026-09-28.md) records the subsequent tqdm CPU jobs, including two capped Python 3.6.9 conda setup timeouts and a successful, clearly modified Python 3.8.1 exploratory fail/pass screen. A separate fixed-revision regression screen passed for all three development cases. Cluster connectivity and the earlier Python 3.8.1 Bubblewrap runner are working; an agent read-isolation boundary has not been established.

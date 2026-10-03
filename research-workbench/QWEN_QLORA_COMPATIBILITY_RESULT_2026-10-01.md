# Qwen3B QLoRA compatibility check

Job21938213 successfully ran three optimizer steps on a41-token **nonmedical software fixture** using cached Qwen2.5-3B-Instruct with NF4 double quantization, bf16 compute and rank16 LoRA on q/k/v/o attention projections. Gradients were finite and nonzero; fixture losses were4.515,4.194,3.992. Those values are execution evidence, not validation loss, generalization or medical-QA improvement.

The adapter was saved and loaded into a fresh wrapper on the same unchanged quantized base. Maximum before/after logit difference was0.0. This is a persistence check, not an independent evaluation process. Source and all saved adapter file hashes passed the local artifact audit; rank/target modules were checked against adapter configuration.

Runtime16.49seconds; peak allocated CUDA memory2,983,230,976bytes (~2.78GiB). Versions: torch2.5.1+cu124, transformers4.56.2, peft0.19.1, bitsandbytes0.46.1. Existing cache was used; no package installation or model download occurred. Deprecation/checkpoint warnings were preserved and did not prevent completion.

No biomedical corpus was admitted or trained, no QA cases entered this fixture, and the original course training baseline was not reproduced. Larger-sequence/batch memory and throughput remain unmeasured. Freeze corpus/evaluation/data/model hashes and budgets before actual domain adaptation.

[Manifest](implementation/qwen_qlora_compatibility_manifest_2026-10-01.json) · [Artifact audit](implementation/qwen_qlora_compatibility_audit_2026-10-01.json) · [Source](implementation/qwen_qlora_compatibility.py)

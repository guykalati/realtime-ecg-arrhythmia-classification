# Project 2: first passing model-generated repair

## Result

One fresh, no-retrieval-hint PySnooper case 3 attempt succeeded. The installed local `gemma4:12b-it-qat` model, operating through the candidate-only gateway, changed one implementation line in `pysnooper/pysnooper.py`: `open(output_path, 'a')` became `open(output, 'a')`. It did not edit tests or receive a shell or evaluator files. This is a development engineering success on one visible bug, **not** evidence of retrieval benefit or general bug-repair ability.

The source candidate was the frozen buggy commit `6e3d797be3fa0a746fb5b1b7c7fea78eb926c208`, verified against the [case manifest](implementation/repair_case_manifest_2026-09-29.json). Retrieval was off. The controller/gateway SHA-256 values for this run were `c850591caacde566501f13fdc2125c7a051b313f51184a731f9b764fe9f15499` and `88a2443e2a70062d506abacebe1476b371180e829cb1c7aa9b130d82a3f4135c`. The [saved model/tool trace](implementation/repair_agent_success_pysnooper3_2026-09-29.json) records eight tool calls and 23,158 reported prompt-plus-generation tokens. This exceeds the soft 20,000-token pre-call cutoff because one final model response can overshoot it; it is not an API-billing figure.

| Check | Slurm job | Result |
| --- | ---: | --- |
| Model-requested target on unchanged candidate | 21728898 | Expected failure |
| Model-requested target after edit | 21728915 | 1 passed |
| Independent final target | 21728916 | 1 passed |
| Independent final regression file | 21728918 | 5 passed |

All test jobs ran through the fixed Python 3.8.1, no-network Bubblewrap evaluator on cluster CPU. The final candidate and logs remain in `/private/tmp/guy-repair-agent-smoke-20260929-pysnooper3-nohint-6/`; the candidate differs from its frozen source only in that one implementation line. The local Ollama server was stopped after the run. The offline gateway/controller suite passed 23 checks before this attempt.

## Next measurement boundary

This was the same case used during tool-interface development. Do not count it as a held-out benchmark solve. Freeze the current controller, exact-runtime cases, provider/model, candidate copies, retrieval hints, budgets, and metrics before a matched retrieval-on/off run. With only two PySnooper cases, a result would be a feasibility demonstration, not a statistically persuasive retrieval study. The user-owned extension remains the separate Karpathy-style experiment mode and a measured repository-evidence memory contribution.

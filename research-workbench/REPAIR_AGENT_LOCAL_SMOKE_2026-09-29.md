# Project 2 local repair-agent development smoke — 29 September 2026

## Purpose and scope

Exercise the candidate-only function gateway, local model tool calling, and fixed cluster evaluator on one frozen PySnooper case. This is engineering development, not a retrieval comparison or benchmark score. The user authorized continued project and cluster work; this smoke used one case, one installed local 11.9B-parameter model (`gemma4:12b-it-qat`), no retrieval hint, and CPU-only cluster tests.

## Frozen case

- Candidate: PySnooper case 3 buggy commit `6e3d797be3fa0a746fb5b1b7c7fea78eb926c208`.
- Target: `tests/test_pysnooper.py::test_file_output`; regression: `tests/test_pysnooper.py`.
- Runtime: Python 3.8.1. The unchanged candidate fails the target with `NameError: name 'output_path' is not defined`.
- Candidate, task, and hint hashes are in [the manifest](implementation/repair_case_manifest_2026-09-29.json). The hint was disabled in both attempts.

## Observations

1. Initial full loop: the model used nine candidate tool calls and found the relevant source. Its two `replace_text` calls supplied literal backslash-n strings instead of actual newlines, so exact-match edits were rejected. No candidate file changed. The loop stopped at 23,056 reported prompt-plus-generation tokens, over the soft 20,000-token pre-call cutoff. Independent final CPU jobs **21727720** and **21727721** both completed; target and regression failed on the unchanged candidate. The result trace is in `/private/tmp/guy-repair-agent-smoke-20260929-pysnooper3-nohint-2/agent_result.json`.
2. The gateway then gained safe exact-match failure feedback, and the instructions asked for the smallest unique replacement. A fresh retry called the target test once: CPU job **21727725** completed and reproduced the expected `NameError`. The local Ollama service later stopped accepting connections before the model returned a repair; this retry has **no agent result or benchmark outcome**. Its partial test log is in `/private/tmp/guy-repair-agent-smoke-20260929-pysnooper3-nohint-4/test_1/summary.json`. The candidate remained unchanged.
3. A controller fix now returns `transport_error` with completed tool events if model transport fails and skips duplicate final cluster checks when the candidate is unchanged. This fix has an offline fake-transport test; it was not re-exercised against the live service.
4. A directly managed Ollama server removed the availability issue for a third fresh development attempt. The model again found the source but passed literal backslash-n sequences in two multiline edit arguments; both exact-match calls were rejected. It exhausted the soft token budget at 23,053 reported tokens without changing the candidate. Final target and regression CPU jobs **21727730** and **21727731** completed and failed as expected. The complete trace is in `/private/tmp/guy-repair-agent-smoke-20260929-pysnooper3-nohint-5/agent_result.json`. The managed server was stopped after this run.

After these attempts, the gateway gained a narrow fallback: when a multiline exact match is absent and replacing literal backslash-n with real newlines produces one unique match, it normalizes both old and new strings before editing. This addresses the observed tool-format failure without allowing an approximate match. The complete offline gateway/controller suite passes **20 tests**. This revised edit behavior has not had a live model run. The live cluster bridge previously passed an unchanged-candidate smoke for tqdm case 3 (job **21727533**). The OpenAI Responses provider is implemented but has not run because no separate `OPENAI_API_KEY` is configured. Codex credentials are not used as an API key.

## Interpretation

The application-owned tool boundary held: model calls could read only the candidate, edit only implementation Python, and request only named tests. The local model did not solve this case in either completed attempt. The interrupted attempt is incomplete because of model service availability. These attempts are not independent benchmark trials; the prompt and feedback changed between them. Before a retrieval-on/off comparison, the revised edit tool needs a live engineering check, then the final controller should be frozen with matched budgets and fresh candidates for each arm.

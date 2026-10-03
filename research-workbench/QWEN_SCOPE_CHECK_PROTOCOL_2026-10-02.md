# Cached-Qwen scope triage development check

Purpose:determine whether cachedQwen2.5-3B can help triage the3,892structural candidates.32source cases were sampled/frozen before single-Codex full-narrative draft labels;32label hashes and82quote/provenance checks passed before inference. These are development labels, not independent expert gold or a held-out clinical benchmark. Seven centrality labels are uncertain; retain those rather than silently forcing binary negatives.

Input:model sees title/abstract/opening/methods/conclusion excerpts only, no reviewer evidence/rationale/tier labels. Maximum3,584inputtokens; suffix truncation and actual input are recorded. Reviewer saw full narrative, model may see partial source, so omissions are reported. Study population and cardiac centrality are separate decisions. Exact20–360character sourcequotes required; failedJSON/schema/enum/quotes become unresolved, not negative or admitted.

One deterministic greedy generation percase,32callcap,512newtokens,0retries,0training. Cached model/tokenizer/config hashes pinned, offline, no download. OneRTX3090 request,12GBhostRAM,12allocatedGPUminute cap (660second executable timeout),noautomaticrequeue. Expectedminutes,queuewaitunknown. Cheaper alternative:retain manual32only, which cannot test automated triage.

No automatic admission or large corpus run follows. After terminal output, independently verify coverage/hashes/source spans and report raw validity, draft-label agreement by tier/centrality, uncertain cases and missing context. This cannot show improved QA, dataset accuracy or clinical efficacy. Frozen manifest:`implementation/qwen_scope_check_manifest_2026-10-02.json`.

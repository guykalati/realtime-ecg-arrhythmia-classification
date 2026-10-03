# Article-QA output validation

`implementation/qa_output_gate.py` rejects malformed/duplicate-keyJSON, wrong schema or field types, missing evidence, and quotes absent from the supplied passage. It canonicalizes a recognizable JSON abstention’s optional final period, preserving a normalization flag. Rejection yields an explicit rejected status and abstention; it must not be counted as a correct model abstention or successful answer.

The old6constructed model outputs replay as4quote-validated answers,1normalizedJSONabstention and1rejection of the nonJSONreply. Original model-output audit/format failures remain unchanged. No model was run and no independent accuracy improved. An adversarial check deliberately confirms that a real quote can accompany a wrong answer:exact-span validation does not verify answer entailment or endpoint fidelity.

Eight focused source-span/schema/abstention/adversarial checks plus duplicate-key rejection passed via the executable self-check. Evidence: `implementation/qa_output_gate_replay_v2_2026-10-02.json`; earlier replay is preserved.

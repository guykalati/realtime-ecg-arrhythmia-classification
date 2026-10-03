# Python coding agent (course team assignment)

This portfolio copy preserves the Part 2 coding-agent script from a joint Advanced LLM assignment. Guy Kalati reports that his partner implemented most of the original assignment. A new version can become Guy's own project through a substantial implementation he builds and can explain; the original assignment remains a joint baseline.

## Current implementation

`agent.py` contains an in-memory file store, `list_files`, `read_file`, `write_file`, `run_python`, and `search_files` tools, an OpenAI-compatible client configured for local Ollama, a tool-dispatch function, a bounded agent loop, and four sample tasks. `run_python` uses Python `exec` and is only a toy demonstration; it is not an isolated execution sandbox for untrusted code.

The original course folder also has a separate Part 3 MCP-connected simulated trading agent and saved traces. That code and those traces are not in this portfolio copy.

## Evidence and run status

The original Part 2 course folder has JSON traces for four sample tasks. A local, model-free smoke check passed for listing files, writing and executing a simple Python file, searching, and dispatching tools. A fresh end-to-end agent run has not been completed for this portfolio copy; it requires the specified Python dependencies and an accessible Ollama model.

The saved Part 3 trading traces include incorrect money conversions and unsupported final summaries. They are useful failure examples, not evidence of a reliable autonomous workflow.

## What is not implemented here

This repository does not contain a document corpus, chunking, embeddings, a retriever, a RAG evaluation set, RAGAS execution, or measured retrieval latency. Previously advertised context precision, recall, faithfulness, and sub-second latency numbers are unsupported and have been removed. A future RAG system must be built and evaluated as a new contribution before those terms or metrics appear in a CV.

## Files

- `agent.py`: Part 2 coding-agent loop and local tools.
- `Assignment 3.pdf`: assignment specification.
- `rag_agentic_system_report.pdf`: course report; read alongside the actual code and traces.

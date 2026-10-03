# First scan of the three CV projects — 27 September 2026

## Scope and outcome

This scan checked the current CV against local source files, saved outputs, and selected primary external sources. It corrected the three **old portfolio-copy READMEs**. It did not edit the CV, alter original course submissions, run model training, submit cluster jobs, or choose a personal extension. The thesis was read only through the supplied handoff and is outside this scan's main work.

The immediate result is a provenance boundary: the LLM project has real saved Qwen2.5-3B QLoRA and SFT artifacts but weak QA performance; the second project is a coding-agent assignment rather than an implemented RAG system; the ECG project has a saved beat-classification result but neither a verified patient-separated test nor a monitoring app.

## 1. LLM domain adaptation and fine-tuning

| Question | First-scan finding |
| --- | --- |
| CV says | A two-stage continued-pretraining and SFT pipeline with QLoRA experiments on Qwen2.5-3B; attention plus MLP adapters improved validation perplexity. |
| Artifacts support | HW1 `hw1_config.json` selects `Qwen/Qwen2.5-3B-Instruct`, nine Sherlock books, 4-bit NF4, and seven named adapter experiments. The saved rank-16 attention+MLP run reports validation perplexity 13.467 before and 11.767 after; attention-only reports 11.981 after. Both corresponding CSV logs reach step 200. HW2's `train_sft.py` can merge an HW1 adapter and train SFT; the selected manual response-only run is in a later final-submission notebook. Its saved evaluation reports three-shot exact-match accuracy 0.0755 and F1 0.1903 on 106 questions. The prediction file has 212 rows for zero- and three-shot configurations. |
| Personally did | Guy clarified on 27 September that he implemented this project himself, although the course submission names two students. The immediate gap is technical mastery and reproducibility, not reconstruction of an individual implementation split. |
| Missing | A clean rerun, portable environment and data manifest, run-to-result index, systematic QA error analysis, and a verified individual extension. The current HW2 config points to a nonexistent absolute HW1 adapter path; its default SFT script uses full-sequence loss, so it is not a direct command for the selected manual response-only run. The old README's 7B/full-SFT/Llama/ROUGE benchmark table had no matching inspected run and was removed. |
| Candidate new work | First reproduce one original run and one comparison, then improve the actual QA bottleneck using a fixed question set, response-only masking check, failure categories, and a controlled data or training change. The exact extension is a later joint decision. |

**Plain-language meaning:** HW1 made the model more likely to predict held-out Sherlock text. HW2 tried to make it answer Sherlock questions. Better text perplexity did not translate into strong exact-answer performance in the saved evaluation. Those are different tasks and should be explained separately.

Key local sources: [HW1 config](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW1/hw1_config.json>), [HW1 saved metrics directory](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW1/submission_report/final_submission_package/run_metrics_and_logs>), [HW2 training script](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW2/scripts/train_sft.py>), [HW2 final submission notebook](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW2/submission_package/HW2_318366150_313466112/HW2_sherlock_sft_cluster.ipynb>), [HW2 saved evaluation](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW2/submission_package/runs/evaluation>).

## 2. Coding agent and claimed RAG evaluation

| Question | First-scan finding |
| --- | --- |
| CV says | A coding agent plus retrieval-strategy evaluation with RAGAS: context precision 0.94, recall 0.92, faithfulness 0.95, and sub-second latency. |
| Artifacts support | HW3 Part 2 contains a 387-line local coding agent with five file/code tools, a tool-call loop, four tasks, and four saved task traces. HW3 Part 3 is a separate MCP-connected simulated trading agent with saved traces. The old portfolio copy contains only the Part 2 `agent.py`, assignment PDF, and report. The Part 3 traces include plainly wrong cents-to-dollar summaries; final answers cannot be trusted without checking tool outputs. |
| Personally did | The original assignment was joint; Guy reports that his partner did most of it and rates current mastery about 0/5. Guy intends to build a substantial new version himself. The old code is the joint baseline, while new authored code and evidence can support the future personal project. |
| Missing | No inspected chunker, corpus, embeddings, retriever, RAGAS run, question set, or latency benchmark. The RAG/RAGAS claims are unsupported. A fresh full agent run also remains open. |
| Candidate new work | Combine document retrieval with an agent around one useful mission. Build retrieval with citations and fixed questions, then add safe tools and task-level evaluation. The specific mission is Guy's next choice; both RAG and agent behavior must be built and measured. |

**Plain-language meaning:** the existing code asks a local model to use tools on files. It does not look up passages from documents to ground answers. RAGAS metrics require actual retrieved contexts, model answers, and an evaluation procedure; the current portfolio copy has none.

Key local sources: [Part 2 agent](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW3/HW_RAG/part2/agent.py>), [Part 2 traces](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW3/HW_RAG/part2/traces>), [Part 3 agent](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW3/HW_RAG/part3/agent.py>).

## 3. ECG heartbeat classification

| Question | First-scan finding |
| --- | --- |
| CV says | A five-class 1D CNN trained on about 100,000 annotated heartbeats, 98.02% held-out accuracy, and a prototype monitoring and simulated-alert interface. |
| Artifacts support | The local notebook loads 87,554 training and 21,892 test rows (187 waveform values plus a class label). Its saved 1D CNN report has accuracy 0.9802, macro F1 0.8967, weighted F1 0.9796, and fusion-class recall 0.6852 on 21,892 test beats. Other saved model outputs have different results. `ECG_APP.py` is an 18-line scaler-to-JSON converter and requires a missing `ecg_scaler.pkl`; it is not an interface. The public team repository lists the notebook, presentation, README, and requirements, with no monitoring-app source in its visible file list. |
| Personally did | This was a three-person course project. The public repo names Rotem Even Zur, Nevo Levi, and Guy Kalati. Guy intends to keep ECG and build a much stronger personal version; the original baseline remains team work. |
| Missing | Original CSVs in this portfolio copy, the scaler, a clean CNN rerun, record or patient identifiers for the current split, an evaluation protocol separating patients, and a working demo. The old portfolio README's live-dashboard and latency claims were removed. |
| Candidate new work | Keep ECG in the active set. Rebuild examples from record-linked raw data, establish a record/patient-separated baseline, compare a compact baseline with justified stronger models, and investigate larger compatible datasets. A demonstration follows the modeling and evaluation work. |

**Plain-language meaning:** the saved 98.02% asks how well the model classifies beats in the supplied test CSV. The CSV columns used here do not show which person each beat came from. Therefore this result does not establish performance on a new patient. A high overall accuracy can also hide weaker fusion and supraventricular detection.

Key local sources: [ECG notebook](</Users/gyklty/Desktop/Guy/Job - Guy/old/Projects/realtime-ecg-arrhythmia-classification/ECG_MITBIH.ipynb>), [ECG utility](</Users/gyklty/Desktop/Guy/Job - Guy/old/Projects/realtime-ecg-arrhythmia-classification/ECG_APP.py>), [original course folder](</Users/gyklty/Desktop/Guy/גיא/תואר ראשון/שנה ד/Semester_H/ML industry>), [public team repository](https://github.com/RotemEZ/ECG-Arrhythmia-Classification).

## Lightweight run and repair record

- **Passed:** Parsed both HW3 agent files and the ECG utility as Python source; ran the Part 2 agent's local tools with a stub model client. Listing, writing, executing `hello.py` and a corrected `buggy.py`, search, and dispatch behaved as expected. This checks the tool layer, not autonomous task completion.
- **Passed:** Read HW1 saved JSON plus CSV logs and confirmed the two cited experiments have 200-step logs. Read HW2 saved evaluation and verified 106 questions in each of the zero- and three-shot summaries, with 212 prediction rows total. Parsed the ECG notebook and checked the cited classification output.
- **Not run:** Full LLM training, agent inference, and ECG model training. This host's default Python lacks `openai`, `fastmcp`, TensorFlow, PyTorch, and the LLM stack. The Ollama endpoint was inaccessible from the sandbox, and the ECG notebook uses hard-coded Colab paths to CSVs absent from the portfolio copy. No model result has been newly reproduced.
- **Repaired:** Replaced the three clean old portfolio-copy READMEs with evidence-bounded descriptions. The exact corrected drafts are saved beside this report. Original course submissions and the CV remain untouched.

## Current research that changes the next decision

1. **LLM:** Current [Hugging Face TRL SFT documentation](https://huggingface.co/docs/trl/sft_trainer) distinguishes assistant-only and completion-only loss; non-response labels must be masked, typically as `-100`. [PEFT quantization guidance](https://huggingface.co/docs/peft/v0.15.0/en/developer_guides/quantization) describes QLoRA-style all-linear targeting. These are candidate controls for a future experiment, not evidence that a newer setting will improve this dataset. The weak 106-question QA result makes data and error analysis the first research question.
2. **Agent/RAG:** [Ragas lists separate retrieval, answer, and agent metrics](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/). [Context precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/) evaluates retrieved-chunk ranking; [faithfulness](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/faithfulness/) checks whether an answer's claims follow from its retrieved context. The current agent traces cannot yield those RAG scores. A practical RAG extension needs a versioned corpus and questions before metric selection; an agent extension needs task success and tool-use checks.
3. **ECG:** [PhysioNet](https://physionet.org/content/mitdb/1.0.0/) identifies 48 recordings from 47 subjects, about 110,000 beat annotations, and an attribution license. The original [de Chazal et al. inter-patient study](https://citeseerx.ist.psu.edu/document?doi=1b6daa11728616118be91a3369c1c6ca3147115b&repid=rep1&type=pdf) split 44 non-pacemaker recordings into two groups of 22. This does not prove the notebook's CSV split leaks patients, but it shows why patient/record separation must be established before comparing a new model with published work. The public team's [repository file list](https://github.com/RotemEZ/ECG-Arrhythmia-Classification) does not show the advertised live app.

## Proposed order for our later planning discussion

1. Make one of Guy's LLM runs reproducible and explainable. Its code and saved experiment trail are the strongest of these three, even though the SFT result is weak.
2. Combine RAG with an agent around one useful mission, then define fixed retrieval and task-success evaluations before adding frameworks.
3. Develop ECG as a personal deep-learning project, beginning with record-linked data and a valid split. Expand data, task, and model scope only after the baseline is comparable and the labels are compatible. Treat the UI as a later demonstration.

For each candidate experiment, agree on its question, dataset/full or sample size, split, baseline, expected runtime and hardware use, success criterion, and cheaper alternative **before** running it. This scan does not authorize those runs. No Wayfinder map or tickets were created; that planning step remains for the joint discussion after Guy chooses the project 2 mission.

## 27 September clarification: all three projects remain active

Guy clarified that he implemented project 1 himself. Projects 2 and 3 began as joint assignments; he now wants substantial personally implemented successors to both. Technical reproducibility and honest separation of the old baseline from new work remain necessary. ECG is retained. The goal is larger and better missions, datasets, and models where each change answers a clear question; a UI is secondary.

## Direction selected after the first scan

Guy selected both a repository repair agent and an ML experiment copilot for project 2, with the experiment loop patterned on Karpathy's `autoresearch` and an additional personal contribution. He delegated project 1 corpus selection and asked for a bigger, better task. He retained project 3 and asked for the original paper, subsequent work, and a further contribution. The source-backed proposal is in [PROJECT_DIRECTION_2026-09-27.md](PROJECT_DIRECTION_2026-09-27.md); the ECG paper comparison is being recorded separately. These are choices for new personal work, not claims that the new results exist yet.

## Implementation update — 27 September 2026

The [new implementation workbench](implementation/README.md) contains a count-only PMC query, local repository evidence search, a bounded experiment ledger and human-authored `program.md`, and an ECG patient-split guard. The PMC title/abstract query returned 201,510 candidate CC0/CC BY records; none have been accepted into a training corpus. The full MIT-BIH raw signal/header/annotation set was downloaded from PhysioNet's public mirror and verified against sizes and checksums. Its WFDB inventory finds 48 records, 47 subject groups, and 112,647 annotation events, including non-beat symbols. No new model was trained, no patient split was chosen, and no RAG/agent task-level result has been measured.

A likely cluster reference is [the `cluster-ops` template](</Users/gyklty/Desktop/Guy/גיא/תואר שני/Semester B/Advanced LLM/HW1/Cluster/skills for claude code/cluster-ops-template/SKILL.md>). It provides Slurm status, job inspection, preflight, result sync, and postmortem scripts, but it is an unconfigured template in the HW1 course folder, not an installed Codex skill for these projects. Its `references` folder is empty despite the setup document mentioning a BGU guide. Older HW1/HW2 run guides describe RTX 3090 course jobs; they do not verify current access or limits. Obtain a live read-only resource inventory before sizing any new run, and agree on the question, data, hardware, runtime, and cheaper alternative before submitting jobs.

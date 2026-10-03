# Source notice inventory

Purpose: after acquisition auditing revealed5new XML retraction notices, inventory structured article-meta relationships and notice type/title flags across all5,819acquired documents. Reread every document/source XML SHA. Output is raw evidence for review, with article IDs, XML hashes, notice flags and unmodified relationship attributes, not admission decisions.

One CPU request,2GBRAM,10minute limit,0GPU,10MBoutput cap, no automatic requeue. A previously verified copy of old977XML/documents is staged on the cluster (about159MBtransfer), with unchanged hashes; no redownload or corpus extension. Existing new XML remains in place.

Structured related-article/related-object nodes can represent several relationships; a relation alone is not proof of retraction. Type/title keyword flags do not resolve linked IDs, substitute for registry refresh or detect all notices in unstructured text. All records remain unreviewed. Source manifest: `implementation/pmc_notice_inventory_manifest_2026-10-01.json`.

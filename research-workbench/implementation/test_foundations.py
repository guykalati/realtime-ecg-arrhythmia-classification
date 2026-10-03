import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import ecg_split_guard
import incart_metadata_inventory
import incart_signal_download
import experiment_ledger
import experiment_memory
import mitdb_beat_manifest
import mitdb_windows
import pmc_inventory
import pmc_eligibility_audit
import pmc_manifest_batch
import pmc_metadata_pilot
import pmc_xml_pilot
import pmc_xml_expansion
import repo_evidence


class FoundationChecks(unittest.TestCase):
    def test_expansion_preserves_sections_tables_and_excludes_bibliography(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'sample.xml'
            path.write_text('<article><front><article-meta><abstract><p>Abstract evidence.</p>'
                            '</abstract></article-meta></front><body><sec><title>Methods</title>'
                            '<p>Patient evidence.</p><table-wrap><caption>Measured values.</caption>'
                            '<table><tr><td>7</td></tr></table></table-wrap></sec></body>'
                            '<back><ref-list><ref>Bibliography excluded.</ref></ref-list></back></article>')
            result = pmc_xml_expansion.extract(path)
            self.assertEqual(result['abstract'], 'Abstract evidence.')
            self.assertEqual([p['kind'] for p in result['paragraphs']], ['p', 'table-wrap'])
            self.assertTrue(all(p['section'] == ['Methods'] for p in result['paragraphs']))
            self.assertIn('7', result['paragraphs'][1]['text'])
            self.assertNotIn('Bibliography', str(result))
        self.assertEqual(pmc_xml_expansion.shingles('A b c d e f'),
                         {'a b c d e', 'b c d e f'})

    def test_benchmark_exclusion_matches_integer_pmids_and_keeps_unknowns_explicit(self):
        self.assertEqual(pmc_eligibility_audit.benchmark_gate(123, {"123"}), "exact_pmid_match")
        self.assertEqual(pmc_eligibility_audit.benchmark_gate(124, {"123"}), "no_exact_pmid_match")
        self.assertEqual(pmc_eligibility_audit.benchmark_gate(None, {"123"}), "pmid_missing")
        self.assertEqual(pmc_eligibility_audit.benchmark_gate(123, None), "unchecked")
        self.assertEqual(pmc_eligibility_audit.benchmark_gate(124, {"123"}, ["123"]), "exact_pmid_match")

    def test_pmc_version_gate_excludes_article_retraction_and_chooses_licensed_version(self):
        def version(number, license_code, retracted=False):
            return {"metadata": {"version": number, "license_code": license_code,
                                 "is_retracted": retracted, "xml_url": "s3://xml",
                                 "doi": "10.1/example"}}

        article = {"pmcid": "PMC1", "versions": [version(1, "CC BY"), version(2, "TDM")]}
        self.assertEqual(pmc_eligibility_audit.version_gate(article)["version"], "PMC1.1")
        article["versions"].append(version(3, "TDM", retracted=True))
        self.assertEqual(pmc_eligibility_audit.version_gate(article)["status"],
                         "exclude_retracted")

    def test_incart_patient_header_rule_and_nonbeat_marker_remain_explicit(self):
        self.assertEqual(incart_metadata_inventory.PATIENT.search("# patient 32").group(1), "32")
        self.assertNotIn("+", mitdb_beat_manifest.SYMBOL_CLASS)
        self.assertNotIn("B", mitdb_beat_manifest.SYMBOL_CLASS)
        self.assertNotIn("n", mitdb_beat_manifest.SYMBOL_CLASS)

    def test_incart_signal_downloader_validates_multipart_etag(self):
        raw = b"a" * incart_signal_download.MULTIPART_CHUNK + b"b" * 3
        first = hashlib.md5(raw[:incart_signal_download.MULTIPART_CHUNK]).digest()
        second = hashlib.md5(raw[incart_signal_download.MULTIPART_CHUNK:]).digest()
        etag = hashlib.md5(first + second).hexdigest() + "-2"
        self.assertTrue(incart_signal_download.etag_matches(raw, etag))
        self.assertFalse(incart_signal_download.etag_matches(raw, "0" * 32 + "-2"))

    def test_beat_label_boundary_keeps_escape_beats_and_pacing_distinct(self):
        self.assertEqual(mitdb_beat_manifest.SYMBOL_CLASS["e"], "N")
        self.assertEqual(mitdb_beat_manifest.SYMBOL_CLASS["j"], "N")
        self.assertEqual(mitdb_beat_manifest.SYMBOL_CLASS["A"], "S")
        self.assertEqual(mitdb_beat_manifest.SYMBOL_CLASS["/"], "Q")
        self.assertNotIn("+", mitdb_beat_manifest.SYMBOL_CLASS)
        self.assertEqual(mitdb_windows.bounds(180), (0, 360))
        self.assertEqual(mitdb_windows.bounds(181), (1, 361))

    def test_pmc_count_request_is_only_a_licensed_candidate_count(self):
        term = pmc_inventory.query(2015, 2026)
        params = parse_qs(urlparse(pmc_inventory.count_url(term)).query)
        self.assertEqual(params["db"], ["pmc"])
        self.assertEqual(params["retmax"], ["0"])
        self.assertIn('"cc0 license"[filter]', params["term"][0])
        self.assertIn('"cc by license"[filter]', params["term"][0])
        self.assertIn("cardiovascular[tiab]", params["term"][0])

    def test_pmc_month_selection_preserves_checkpoint_and_excludes_future(self):
        months = [{"month": f"2026-{month:02d}", "count": 1} for month in range(1, 13)]
        completed = [row for row in months if row["month"] < "2026-09"]
        selected = pmc_metadata_pilot.select_months(completed, 4, pinned={"2026-04"})
        self.assertEqual(len(selected), 4)
        self.assertIn("2026-04", {row["month"] for row in selected})
        self.assertTrue(all(row["month"] < "2026-09" for row in selected))
        self.assertEqual(pmc_metadata_pilot.select_months(completed, 1, pinned={"2026-04"})[0]["month"], "2026-04")

    def test_pmc_manifest_sample_deduplicates_month_overlap(self):
        rows = [
            {"month": "2015-01", "ids": [str(i) for i in range(1, 1002)]},
            {"month": "2015-02", "ids": ["1001", "1002"]},
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample.jsonl"
            sample = pmc_manifest_batch.select_sample(rows, path)
            self.assertEqual(len(sample), 1000)
            self.assertEqual(len({row["pmcid"] for row in sample}), 1000)
            self.assertEqual(sample, pmc_manifest_batch.select_sample(rows, path))

    def test_xml_pilot_guards_source_and_reads_jats_structure(self):
        url = "s3://pmc-oa-opendata/PMC123.1/PMC123.1.xml?md5=" + "a" * 32
        self.assertEqual(pmc_xml_pilot.source_url(url, "PMC123.1")[1], "a" * 32)
        with self.assertRaises(ValueError):
            pmc_xml_pilot.source_url(url, "PMC124.1")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample.xml"
            path.write_text('<article article-type="research-article" xml:lang="en">'
                            '<front><article-meta><title-group><article-title>Heart study'
                            '</article-title></title-group><abstract>One result.</abstract>'
                            '</article-meta></front><body><sec><title>Methods</title>'
                            '<p>Two samples.</p></sec></body></article>')
            result = pmc_xml_pilot.inspect_xml(path)
            self.assertEqual((result["jats_article"], result["xml_lang"], result["article_type"]),
                             (True, "en", "research-article"))
            self.assertGreater(result["body_words"], 0)

    def test_repo_search_has_line_citations_and_skips_hidden_and_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "module.py").write_text("def repair_bug():\n    return 42\n")
            (root / ".env").write_text("SECRET=repair_bug\n")
            (root / "results").mkdir()
            (root / "results" / "answer.md").write_text("repair_bug hidden answer\n")
            db = root / "index.db"
            self.assertEqual(repo_evidence.build_index(root, db), 1)
            hits = repo_evidence.search(db, "repair bug")
            self.assertEqual([(h["path"], h["line"]) for h in hits], [("module.py", 1)])
            self.assertEqual(repo_evidence.search(db, "SECRET"), [])

    def test_patient_leak_and_known_duplicate_subject_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "split.csv"

            def write(rows):
                with path.open("w", newline="") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(["record_id", "patient_id", "split"])
                    writer.writerows(rows)

            write([["100", "p1", "train"], ["101", "p1", "test"]])
            with self.assertRaisesRegex(ValueError, "crosses"):
                ecg_split_guard.validate(path)
            write([["201", "p201", "train"], ["202", "p202", "test"]])
            with self.assertRaisesRegex(ValueError, "same subject"):
                ecg_split_guard.validate(path)
            write([["201", "p201", "train"], ["202", "p201", "train"], ["100", "p100", "test"]])
            self.assertEqual(ecg_split_guard.validate(path)["patients"], 2)
            inventory = Path(temp) / "inventory.json"
            inventory.write_text(json.dumps({"records": [
                {"record_id": "201", "subject_group": "201-202"},
                {"record_id": "202", "subject_group": "201-202"},
                {"record_id": "100", "subject_group": "100"},
            ]}))
            self.assertEqual(ecg_split_guard.validate(path, inventory)["records"], 3)
            write([["201", "p201", "train"], ["202", "p201", "train"]])
            with self.assertRaisesRegex(ValueError, "does not cover inventory"):
                ecg_split_guard.validate(path, inventory)

    def test_experiment_contract_blocks_frozen_file_changes_and_extra_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "prepare.py").write_text("EVAL = 'fixed'\n")
            (root / "data.json").write_text('{"split": "fixed"}\n')
            (root / "train.py").write_text("print('candidate')\n")
            with self.assertRaisesRegex(ValueError, "inside the experiment"):
                experiment_ledger.initialize(root, Path("../outside.py"), Path("data.json"),
                                             "val_loss", "min", 1, 300)
            experiment_ledger.initialize(root, Path("prepare.py"), Path("data.json"),
                                         "val_loss", "min", 2, 300)
            item = experiment_ledger.record(root, {
                "status": "success", "metric_value": 0.42,
                "training_seconds": 25, "hypothesis": "smaller batch",
            })
            self.assertEqual(item["run"], 1)
            self.assertEqual(experiment_ledger.summary(root)["best"]["metric_value"], 0.42)
            candidate = root / "candidate" / "train.py"
            candidate.parent.mkdir()
            candidate.write_text("print('isolated candidate')\n")
            item = experiment_ledger.record(root, {
                "status": "success", "metric_value": 0.5,
                "training_seconds": 25, "candidate_file": "candidate/train.py",
            })
            self.assertEqual(item["train_sha256"], experiment_ledger.digest(candidate))
            with self.assertRaisesRegex(ValueError, "exhausted"):
                experiment_ledger.record(root, {"status": "failed", "training_seconds": 1})
            (root / "prepare.py").write_text("EVAL = 'changed'\n")
            with self.assertRaisesRegex(ValueError, "frozen prepare changed"):
                experiment_ledger.record(root, {
                    "status": "failed", "training_seconds": 1,
                })

    def test_experiment_memory_reads_only_explicit_development_ledgers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            development = root / "development"
            development.mkdir()
            (development / "results.jsonl").write_text(json.dumps({
                "run": 1, "status": "failed", "metric_value": None,
                "train_sha256": "a" * 64, "hypothesis": "longer context",
                "failure_reason": "CUDA memory exhausted", "notes": "reduce batch size",
            }) + "\n")
            (root / "sealed_test_answers.txt").write_text("secret answer")
            db = root / "memory.sqlite"
            self.assertEqual(experiment_memory.build_index([development], db), 1)
            self.assertEqual(experiment_memory.search(db, "memory")[0]["run"], 1)
            self.assertEqual(experiment_memory.search(db, "secret"), [])
            named = development / 'results_frozen.jsonl'
            named.write_text((development / 'results.jsonl').read_text())
            self.assertEqual(experiment_memory.build_index([named], db), 1)
            self.assertEqual(experiment_memory.search(db, 'memory')[0]['source'], str(named.resolve()))
            with self.assertRaises(ValueError):
                experiment_memory.build_index([root / 'sealed_test_answers.txt'], db)


if __name__ == "__main__":
    unittest.main()

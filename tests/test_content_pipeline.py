import json
import tempfile
import unittest
from pathlib import Path

from tools.content_pipeline.generate_candidates import load_batch, validate_candidates
from tools.content_pipeline.review_record import create_review_record
from tools.content_pipeline.validate_content import build_quality_report, build_release_manifest, similarity_report


class ContentPipelineTests(unittest.TestCase):
    def test_quality_report_covers_current_content_and_release_manifest_hashes_files(self):
        root = Path(".").resolve()
        report = build_quality_report(root / "packages" / "content", root)
        self.assertEqual(report["summary"]["cards"], 22)
        self.assertEqual(report["summary"]["errors"], 0)
        release = build_release_manifest(root / "packages" / "content", root)
        self.assertEqual(release["counts"]["cards"], 22)
        self.assertEqual(len(release["files"]), 22 + 22 + 1 + 1 + 3 + 1)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in release["files"]))

    def test_report_flags_duplicate_names_in_a_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory) / "batch.json"
            batch.write_text(json.dumps({"cards": [{"name": "同じ名前"}, {"name": "同じ名前"}]}), encoding="utf-8")
            report = build_quality_report(Path("packages/content"), Path("."), batch)
            self.assertGreaterEqual(report["summary"]["warnings"], 1)

    def test_batch_definition_and_candidate_validation_require_review_for_similarity(self):
        batch = load_batch(Path("tools/content_pipeline/batches/high-priestess-books-001.json"))
        cards = [
            {"name": f"候補{i}", "subtitle": "静かな書庫", "manifestationForm": "place", "centralParadox": "答えと迷い", "uprightCore": "観察と選別", "reversedCore": "情報過多"}
            for i in range(1, batch["requestedCount"] + 1)
        ]
        result = validate_candidates({"cards": cards}, batch)
        self.assertEqual(result["status"], "automatically-validated")
        pairs = similarity_report(cards)
        self.assertTrue(pairs)
        self.assertTrue(all(pair["reviewRequired"] for pair in pairs))

    def test_review_record_hashes_candidate_and_requires_human_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.json"
            candidate.write_text('{"cards": []}\n', encoding="utf-8")
            record = create_review_record(candidate, "batch-example")
            self.assertEqual(len(record["candidateSha256"]), 64)
            self.assertEqual(record["decision"], "needs-review")
            self.assertTrue(record["publishedRequiresHumanApproval"])

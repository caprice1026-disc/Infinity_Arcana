import json
import unittest
from pathlib import Path

from packages.core.infinite_arcana_core.content import load_content
from packages.core.infinite_arcana_core.records import ReadingRecord


class CoreContentTests(unittest.TestCase):
    def test_loads_manifest_content_and_spreads(self):
        content = load_content(Path("packages/content"))
        self.assertEqual(len(content.archetypes), 22)
        self.assertEqual(len(content.cards), 22)
        self.assertEqual({"single-card", "past-present-future", "situation-obstacle-advice"}, set(content.spreads))

    def test_reading_record_round_trips_as_versioned_json(self):
        record = ReadingRecord(
            id="reading-1",
            request_version="1.0.0",
            content_release_id="release-2026-07-19-knowledge-vol-1",
            seed="seed-1",
            spread_id="single-card",
            draws=[{"positionId": "guidance", "cardId": "babel-library", "orientation": "upright"}],
        )
        restored = json.loads(json.dumps(record.to_dict()))
        self.assertEqual(restored["schemaVersion"], "1.0.0")
        self.assertEqual(restored["draws"][0]["cardId"], "babel-library")
        self.assertEqual(restored["drawPolicyId"], "balanced-two-stage-v1")
        self.assertEqual(restored["randomAlgorithm"], "sha256-counter-v1")

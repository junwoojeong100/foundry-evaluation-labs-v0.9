from __future__ import annotations

import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools.media.success_video import SCENES
from tools.media.workshop_video import redact, stamp

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs" / "media" / "complete-rag"


class MediaTests(unittest.TestCase):
    def test_redaction_covers_names_emails_ids_paths_and_report_urls(self):
        text = (
            "EXAMPLE USER learner@example.com "
            "12345678-1234-1234-1234-123456789abc "
            "https://ai.azure.com/nextgen/private/report "
            + str(ROOT / "results" / "example.json")
        )
        cleaned = redact(text, ["Example User"])
        self.assertNotIn("EXAMPLE USER", cleaned)
        self.assertNotIn("learner@example.com", cleaned)
        self.assertNotIn("12345678-1234", cleaned)
        self.assertNotIn("https://ai.azure.com", cleaned)
        self.assertNotIn(str(ROOT), cleaned)
        self.assertIn("[redacted]", cleaned)

    def test_success_chapters_are_bilingual_and_include_relevance(self):
        self.assertEqual(len(SCENES), 7)
        self.assertEqual(len({scene["id"] for scene in SCENES}), 7)
        self.assertEqual(sum(scene["seconds"] for scene in SCENES) + 14, 174)
        for scene in SCENES:
            for language in ("en", "ko"):
                self.assertEqual(len(scene[language]), 2)
                self.assertTrue(all(scene[language]))
        dialogue = next(scene for scene in SCENES if scene["id"] == "success-03-prompt")
        self.assertIn("user follow-ups", dialogue["en"][1])
        self.assertIn("Relevance", dialogue["en"][1])
        self.assertEqual(stamp(65.25), "00:01:05,250")

    def test_current_videos_subtitles_and_posters_match_the_manifest(self):
        manifest = json.loads((MEDIA / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["videos"]), {"en", "ko"})
        for language, entry in manifest["videos"].items():
            with self.subTest(language=language):
                data = (MEDIA / entry["file"]).read_bytes()
                self.assertEqual(data[4:8], b"ftyp")
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
                self.assertEqual(len(data), entry["bytes"])
                self.assertGreater(len(data), 100000)
                self.assertLess(len(data), 50 * 1024 * 1024)
                self.assertEqual(entry["duration_seconds"], 174)
                self.assertEqual(len(entry["chapters"]), 7)
                subtitle = (MEDIA / f"completion-summary.{language}.srt").read_text(encoding="utf-8")
                self.assertEqual(subtitle.count(" --> "), 7)
                self.assertIn("Relevance", subtitle)
                self.assertIn("LAB_ACCEPTANCE_PASSED", subtitle)
                self.assertNotRegex(subtitle, r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
                previous_end = 7
                for chapter, scene in zip(entry["chapters"], SCENES):
                    self.assertEqual(chapter["start"], previous_end)
                    self.assertEqual(chapter["duration"], scene["seconds"])
                    self.assertIn(stamp(chapter["start"]), subtitle)
                    previous_end += chapter["duration"]
                self.assertEqual(previous_end + 7, 174)
                poster = (MEDIA / f"completion-summary.{language}.png").read_bytes()
                self.assertEqual(poster[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", poster[16:24]), (1920, 1080))
                atoms, offset = [], 0
                while offset + 8 <= len(data):
                    size, kind = struct.unpack(">I4s", data[offset:offset + 8])
                    if size == 1:
                        size = struct.unpack(">Q", data[offset + 8:offset + 16])[0]
                    self.assertGreaterEqual(size, 8)
                    atoms.append(kind)
                    offset += size
                self.assertLess(atoms.index(b"moov"), atoms.index(b"mdat"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import hashlib
import json
import re
import struct
import unittest
from pathlib import Path

from tools.media.workshop_video import SCENES, redact, stamp
from tools.media.rag_video import SCENES as RAG_SCENES

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs" / "media"


class MediaTests(unittest.TestCase):
    def test_optional_rag_videos_are_additional_bilingual_artifacts(self):
        folder = MEDIA / "optional-rag"
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["videos"]), {"en", "ko"})
        self.assertEqual(len(RAG_SCENES), 6)
        self.assertEqual(sum(scene["seconds"] for scene in RAG_SCENES) + 14, 150)
        for language, entry in manifest["videos"].items():
            data = (folder / entry["file"]).read_bytes()
            self.assertEqual(data[4:8], b"ftyp")
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
            self.assertEqual(len(data), entry["bytes"])
            self.assertLess(len(data), 50 * 1024 * 1024)
            self.assertEqual(entry["duration_seconds"], 150)
            self.assertEqual(len(entry["chapters"]), 6)
            subtitle = (folder / f"rag-summary.{language}.srt").read_text(encoding="utf-8")
            self.assertEqual(subtitle.count(" --> "), 6)
            self.assertIn("REVIEW_REQUIRED", subtitle)
            self.assertNotRegex(subtitle, r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
            poster = (folder / f"rag-summary.{language}.png").read_bytes()
            self.assertEqual(struct.unpack(">II", poster[16:24]), (1920, 1080))

    def test_redaction_covers_case_variants_emails_ids_and_report_urls(self):
        text = (
            "EXAMPLE USER learner@example.com "
            "12345678-1234-1234-1234-123456789abc "
            "https://ai.azure.com/nextgen/private/report"
        )
        cleaned = redact(text, ["Example User"])
        self.assertNotIn("EXAMPLE USER", cleaned)
        self.assertNotIn("learner@example.com", cleaned)
        self.assertNotIn("12345678-1234", cleaned)
        self.assertNotIn("https://ai.azure.com", cleaned)
        self.assertIn("[redacted]", cleaned)

    def test_chapters_are_bilingual_and_critical_distinctions_are_explicit(self):
        self.assertEqual(len(SCENES), 10)
        self.assertEqual(len({scene["id"] for scene in SCENES}), 10)
        self.assertEqual(sum(scene["seconds"] for scene in SCENES) + 14, 230)
        for scene in SCENES:
            for language in ("en", "ko"):
                self.assertEqual(len(scene[language]), 2)
                self.assertTrue(all(scene[language]))
        smoke = next(scene for scene in SCENES if scene["id"] == "04-smoke")
        self.assertIn("one new paid model call", smoke["en"][1])
        baseline = next(scene for scene in SCENES if scene["id"] == "05-baseline")
        self.assertIn("not regenerated", baseline["en"][1])
        gate = next(scene for scene in SCENES if scene["id"] == "09-gate")
        self.assertIn("not human approval", gate["en"][1])
        self.assertEqual(stamp(65.25), "00:01:05,250")

    def test_published_videos_subtitles_and_posters_match_the_manifest(self):
        manifest = json.loads((MEDIA / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["videos"]), {"en", "ko"})
        for language, entry in manifest["videos"].items():
            with self.subTest(language=language):
                video = MEDIA / entry["file"]
                data = video.read_bytes()
                self.assertEqual(data[4:8], b"ftyp")
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
                self.assertEqual(len(data), entry["bytes"])
                self.assertGreater(len(data), 100000)
                self.assertLess(len(data), 50 * 1024 * 1024)
                self.assertEqual(entry["duration_seconds"], 230)
                self.assertEqual(len(entry["chapters"]), 10)
                subtitle = (MEDIA / f"workshop-summary.{language}.srt").read_text(encoding="utf-8")
                self.assertEqual(subtitle.count(" --> "), 10)
                self.assertIn("BLOCK", subtitle)
                self.assertNotRegex(subtitle, r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
                previous_end = 7
                for chapter, scene in zip(entry["chapters"], SCENES):
                    self.assertEqual(chapter["start"], previous_end)
                    self.assertEqual(chapter["duration"], scene["seconds"])
                    self.assertIn(stamp(chapter["start"]), subtitle)
                    previous_end += chapter["duration"]
                self.assertEqual(previous_end + 7, entry["duration_seconds"])
                poster = (MEDIA / f"workshop-summary.{language}.png").read_bytes()
                self.assertEqual(poster[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", poster[16:24]), (1920, 1080))
                atoms = []
                offset = 0
                while offset + 8 <= len(data):
                    size, kind = struct.unpack(">I4s", data[offset:offset + 8])
                    if size == 1:
                        size = struct.unpack(">Q", data[offset + 8:offset + 16])[0]
                    self.assertGreaterEqual(size, 8)
                    atoms.append(kind)
                    offset += size
                self.assertIn(b"moov", atoms)
                self.assertIn(b"mdat", atoms)
                self.assertLess(atoms.index(b"moov"), atoms.index(b"mdat"))


if __name__ == "__main__":
    unittest.main()

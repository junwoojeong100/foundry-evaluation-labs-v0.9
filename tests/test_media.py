from __future__ import annotations

import hashlib
import io
import json
import struct
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.media import workshop_video as media
from tools.media.success_video import SCENES
from tools.media.workshop_video import redact, stamp

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs" / "media" / "complete-rag"


class MediaTests(unittest.TestCase):
    def test_recording_context_reads_only_structured_run_artifacts(self):
        identity = {"subscriptionId": "test-sub", "tenantId": "test-tenant", "account": "learner@example.com"}
        current = {"id": "test-sub", "name": "Test subscription", "user": {"name": "learner@example.com"}}
        records = [
            identity, {"name": "test-group", "id": "/test-group"},
            {"name": "test-account"}, {"report_url": "https://ai.azure.com/nextgen/test/build/evaluations/test"},
        ]
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(media, "ROOT", Path(temporary)),
            patch.object(media, "load", side_effect=records) as load,
            patch.object(media.subprocess, "check_output", side_effect=[json.dumps(current), "Test learner\n"]),
        ):
            context = media.project_context()
        self.assertEqual(context["subscription"], "test-sub")
        self.assertEqual(
            [call.args[0].name for call in load.call_args_list],
            ["azure-identity.json", "azure-resource-group.json", "azure-foundry-account.json", "judge.json"],
        )
        self.assertNotIn("08-portal-compare", context["urls"])

    def test_comparison_scene_requires_a_valid_explicit_url_before_loading_context(self):
        invalid = (
            None, "", "http://ai.azure.com/project/compare/test",
            "https://example.com/project/compare/test",
            "https://ai.azure.com/project/compare/",
            "https://ai.azure.com/project/evaluations?next=/compare/test",
            "https://ai.azure.com/project/compare/test\n",
        )
        for url in invalid:
            with self.subTest(url=url), patch.object(media, "project_context") as context:
                with self.assertRaisesRegex(ValueError, "--comparison-url"):
                    media.prepare("08-portal-compare", comparison_url=url)
                context.assert_not_called()

    def test_comparison_scene_preserves_the_supplied_url_without_a_terminal_fallback(self):
        url = "https://ai.azure.com/nextgen/test/compare/recorded?tid=test-tenant"
        context = {"redact": [], "urls": {}}
        with tempfile.TemporaryDirectory() as temporary, redirect_stdout(io.StringIO()):
            private = Path(temporary)
            media.save(private / "work/server.json", {"url": "http://127.0.0.1:8765"})
            media.prepare("08-portal-compare", private=private, context=context, comparison_url=url)
            capture = media.load(private / "work/capture-config.json")
            saved = media.load(private / "context.json")
        self.assertEqual(capture["kind"], "portal")
        self.assertEqual(capture["url"], url)
        self.assertEqual(saved["urls"]["08-portal-compare"], url)
        self.assertEqual(context["urls"], {})

    def test_prepare_cli_forwards_the_comparison_url(self):
        url = "https://ai.azure.com/nextgen/test/compare/recorded"
        with (
            patch("sys.argv", ["workshop_video.py", "prepare", "08-portal-compare", "--comparison-url", url]),
            patch.object(media.os, "umask"),
            patch.object(media, "prepare") as prepare,
        ):
            media.main()
        prepare.assert_called_once_with("08-portal-compare", comparison_url=url)

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

    def test_provisioning_summary_requires_the_original_creation_recording(self):
        scene = SCENES[0]
        self.assertEqual(scene["recording_id"], "rerun-00-group")
        self.assertEqual(scene["kind"], "recorded")
        with patch.object(media, "project_context") as context:
            with self.assertRaisesRegex(ValueError, "pre-recorded footage"):
                media.prepare(scene["id"], scenes=SCENES)
            context.assert_not_called()

    def test_recorder_accepts_quality_block_but_not_failed_calibration(self):
        for command, allowed in (
            ("python advanced_lab.py accept", True),
            ("python advanced_lab.py calibrate", False),
        ):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as temporary:
                private = Path(temporary)
                media.save(private / "context.json", {"group": "test", "subscription": "test", "redact": []})
                media.save(private / "work/terminal.json", {"lines": [], "status": "Ready"})
                scenes = [{"id": "decision", "kind": "terminal", "commands": [command]}]
                with (
                    patch.object(media.subprocess, "Popen") as popen,
                    patch.object(media.time, "sleep"),
                    redirect_stdout(io.StringIO()),
                ):
                    popen.return_value.stdout = io.StringIO("LAB_ACCEPTANCE_BLOCKED\n")
                    popen.return_value.wait.return_value = 2
                    if allowed:
                        media.run_scene("decision", scenes=scenes, private=private)
                    else:
                        with self.assertRaisesRegex(RuntimeError, "exit 2"):
                            media.run_scene("decision", scenes=scenes, private=private)
                state = media.load(private / "work/terminal.json")
                if allowed:
                    self.assertEqual(state["status"], "BLOCK is a quality decision, not an execution error")
                else:
                    self.assertIn("Execution error", state["status"])

    def test_render_uses_original_recording_timing_and_dated_cards(self):
        scene = SCENES[0]
        with tempfile.TemporaryDirectory() as temporary:
            private = Path(temporary) / "private"
            output = Path(temporary) / "output"
            raw = private / "raw" / "original.webm"
            media.save(private / "rerun-00-group.recording.json", {
                "path": str(raw), "started_at_ms": 10000, "ready_offset_ms": 1000,
                "action_end_offset_ms": 19000,
            })
            media.save(private / "rerun-00-group.commands.json", [{
                "started_at_ms": 12000, "finished_at_ms": 22000,
            }])
            with (
                patch.object(media, "card") as card,
                patch.object(media, "overlay"),
                patch.object(media, "probe", return_value={"format": {"duration": "20"}}),
                patch.object(media, "ffmpeg", side_effect=lambda args: Path(args[-1]).write_bytes(b"test-video")) as ffmpeg,
                redirect_stdout(io.StringIO()),
            ):
                media.render(
                    scenes=[scene], private=private, output=output,
                    prefix="test", topic="success", recorded_on="2026-09-28",
                )
            manifest = media.load(output / "manifest.json")
            self.assertEqual(manifest["recorded_on"], "2026-09-28")
            for language in ("en", "ko"):
                chapter = manifest["videos"][language]["chapters"][0]
                self.assertEqual(chapter["source_recording_id"], "rerun-00-group")
                self.assertEqual(chapter["scene"], scene["id"])
            segments = [call.args[0] for call in ffmpeg.call_args_list if str(raw) in call.args[0]]
            self.assertEqual(len(segments), 2)
            self.assertTrue(all(args[:4] == ["-ss", "1.000", "-t", "16.000"] for args in segments))
            self.assertTrue(all(call.kwargs["recorded_on"] == "2026-09-28" for call in card.call_args_list))

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
                    self.assertEqual(chapter["source_recording_id"], scene.get("recording_id", scene["id"]))
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

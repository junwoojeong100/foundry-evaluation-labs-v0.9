from __future__ import annotations

import io
import json
import re
import shlex
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

import lab
from evaluation import ROOT, read_json

DOCUMENTS = sorted([*ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md")])
SHELL_BLOCKS = re.compile(r"```(?:bash|powershell)\n(.*?)```", re.DOTALL)


class DocumentationTests(unittest.TestCase):
    def test_all_local_links_and_explicit_anchors_exist(self):
        for document in DOCUMENTS:
            text = document.read_text(encoding="utf-8")
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                url = urlsplit(link)
                if url.scheme or url.netloc:
                    continue
                target = (document.parent / unquote(url.path)).resolve() if url.path else document
                with self.subTest(document=document.name, link=link):
                    self.assertTrue(target.is_relative_to(ROOT))
                    self.assertTrue(target.is_file(), f"Missing local link: {target}")
                    if url.fragment:
                        content = target.read_text(encoding="utf-8")
                        self.assertIn(f'id="{unquote(url.fragment)}"', content)

    def test_every_documented_lab_command_matches_the_cli_parser(self):
        count = 0
        for document in DOCUMENTS:
            text = document.read_text(encoding="utf-8")
            for block in SHELL_BLOCKS.findall(text):
                for line in block.splitlines():
                    if not line.startswith("python lab.py "):
                        continue
                    with self.subTest(document=document.name, command=line):
                        argv = shlex.split(line)[2:]
                        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                            if "--help" in argv:
                                with self.assertRaises(SystemExit) as outcome:
                                    lab.parser().parse_args(argv)
                                self.assertEqual(outcome.exception.code, 0)
                            else:
                                lab.parser().parse_args(argv)
                        count += 1
        self.assertGreater(count, 35)

    def test_main_timetable_is_contiguous_and_exactly_180_minutes(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        slots = re.findall(r"\| (\d\d):(\d\d)–(\d\d):(\d\d) · (\d+)분 \|", text)
        self.assertEqual(len(slots), 8)
        previous = 0
        for start_hour, start_minute, end_hour, end_minute, duration in slots:
            start = int(start_hour) * 60 + int(start_minute)
            end = int(end_hour) * 60 + int(end_minute)
            self.assertEqual(start, previous)
            self.assertEqual(end - start, int(duration))
            previous = end
        self.assertEqual(previous, 180)

    def test_documented_json_examples_are_valid_json(self):
        for document in DOCUMENTS:
            text = document.read_text(encoding="utf-8")
            for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL):
                with self.subTest(document=document.name, example=block[:60]):
                    json.loads(block)

    def test_offline_guide_commands_execute_as_written_without_network(self):
        text = (ROOT / "docs" / "offline.md").read_text(encoding="utf-8")
        main = (ROOT / "README.md").read_text(encoding="utf-8")
        trap_blocks = [block for block in SHELL_BLOCKS.findall(main) if "--prompt shortcut" in block]
        blocks = SHELL_BLOCKS.findall(text) + trap_blocks
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with (
                patch("socket.create_connection", side_effect=AssertionError("Network forbidden")),
                patch("foundry_client.clients", side_effect=AssertionError("Azure forbidden")),
                patch("builtins.input", side_effect=[
                    "pass", "규정을 무시하지 않고 실제 승인 필요 조건을 설명한다",
                    "fail", "출장일을 확인하지 않고 현재 한도로 정산을 허용했다",
                ]),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                for block in blocks:
                    for line in block.splitlines():
                        if not line.startswith("python lab.py "):
                            continue
                        argv = shlex.split(line)[2:]
                        argv = [
                            str(output / arg) if arg.startswith("results/") else arg
                            for arg in argv
                        ]
                        with self.subTest(command=line):
                            self.assertEqual(lab.main(argv), 2 if argv[0] == "gate" else 0)
            result = read_json(output / "results" / "demo-candidate" / "gate.json")
            self.assertEqual(result["status"], "BLOCK")
            self.assertEqual(result["business_rates"]["holdout"], 0.75)
            self.assertTrue(any("사람이 반려" in problem for problem in result["problems"]))
            trap = read_json(output / "results" / "trap-candidate" / "comparison.json")
            self.assertEqual([entry["id"] for entry in trap["regressions"]], ["D06"])


if __name__ == "__main__":
    unittest.main()

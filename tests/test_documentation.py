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
from evaluation import ROOT, read_cases, read_json

DOCUMENTS = sorted([*ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md")])
SHELL_BLOCKS = re.compile(r"```(?:bash|powershell)\n(.*?)```", re.DOTALL)


def lab_commands(document: Path) -> list[list[str]]:
    return [
        shlex.split(line)[2:]
        for block in SHELL_BLOCKS.findall(document.read_text(encoding="utf-8"))
        for line in block.splitlines()
        if line.startswith("python lab.py ")
    ]


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
            for argv in lab_commands(document):
                with self.subTest(document=document.name, command=argv):
                    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                        if "--help" in argv:
                            with self.assertRaises(SystemExit) as outcome:
                                lab.parser().parse_args(argv)
                            self.assertEqual(outcome.exception.code, 0)
                        else:
                            lab.parser().parse_args(argv)
                    count += 1
        self.assertGreater(count, 35)

    def test_main_path_is_checkpoint_driven_without_a_time_limit(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("시간 제한 없이", text)
        self.assertIn("(docs/setup.md)", text)
        self.assertIn("(docs/cleanup.md)", text)
        self.assertEqual(re.findall(r'<a id="lab-(\d+)"></a>', text), [str(i) for i in range(7)])
        self.assertNotRegex(text, r"\d{2}:\d{2}[–-]\d{2}:\d{2}")
        for document in DOCUMENTS:
            with self.subTest(document=document.name):
                content = document.read_text(encoding="utf-8")
                self.assertNotIn("3시간", content)
                self.assertNotIn("180분", content)

    def test_documented_json_examples_are_valid_json(self):
        for document in DOCUMENTS:
            text = document.read_text(encoding="utf-8")
            for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL):
                with self.subTest(document=document.name, example=block[:60]):
                    json.loads(block)

    def test_setup_smoke_is_one_committed_extra_case_not_dev_or_holdout(self):
        commands = lab_commands(ROOT / "docs" / "setup.md")
        runs = [lab.parser().parse_args(argv) for argv in commands if argv[0] == "run"]
        self.assertEqual(len(runs), 1)
        run = runs[0]
        self.assertEqual(run.mode, "live")
        self.assertIsNotNone(run.data)
        self.assertNotIn(run.data.name, ("dev.jsonl", "holdout.jsonl"))
        self.assertEqual(run.out, Path("results/setup-smoke"))
        cases = read_cases(ROOT / run.data)
        self.assertEqual(len(cases), 1)
        for split in ("dev", "holdout"):
            for experiment_case in read_cases(ROOT / "data" / f"{split}.jsonl"):
                self.assertNotEqual(cases[0]["id"], experiment_case["id"])
                self.assertNotEqual(cases[0]["query"], experiment_case["query"])
        self.assertIn(["judge", "results/setup-smoke"], commands)
        self.assertIn(["inspect", "results/setup-smoke", cases[0]["id"]], commands)

    def test_setup_uses_one_deployment_for_answers_and_judging(self):
        text = (ROOT / "docs" / "setup.md").read_text(encoding="utf-8")
        configs = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL)]
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0]["model_deployment"], "eval-model")
        self.assertEqual(configs[0]["judge_deployment"], "eval-model")
        self.assertEqual(configs[0], read_json(ROOT / "config.example.json"))

    def test_human_judgments_precede_baseline_judge_scores(self):
        for document, folder in (
            (ROOT / "README.md", "results/baseline"),
            (ROOT / "docs" / "offline.md", "results/demo-baseline"),
        ):
            commands = lab_commands(document)
            before_judge = commands[:commands.index(["judge", folder])]
            for case_id in ("D01", "D04", "D06"):
                with self.subTest(document=document.name, case_id=case_id):
                    self.assertIn(["inspect", folder, case_id], before_judge)

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

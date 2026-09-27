from __future__ import annotations

import io
import json
import os
import re
import shlex
import subprocess
import sys
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
        for anchor in (
            "prepare", "setup-tools", "setup-sign-in", "setup-project",
            "setup-permissions", "setup-model", "setup-config", "setup-smoke",
            "command-status", "finish",
        ):
            self.assertIn(f'<a id="{anchor}"></a>', text)
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

    def test_main_path_uses_live_only_and_one_lab_command_per_block(self):
        commands = lab_commands(ROOT / "README.md")
        runs = [lab.parser().parse_args(argv) for argv in commands if argv[0] == "run"]
        self.assertEqual(
            [run.out for run in runs],
            [Path("results") / name for name in ("setup-smoke", "baseline", "candidate", "holdout", "my-case")],
        )
        self.assertTrue(all(run.mode == "live" for run in runs))
        for document in (ROOT / "README.md", ROOT / "docs" / "setup.md", ROOT / "docs" / "offline.md"):
            for block in SHELL_BLOCKS.findall(document.read_text(encoding="utf-8")):
                with self.subTest(document=document.name, block=block):
                    self.assertLessEqual(sum(line.startswith("python lab.py ") for line in block.splitlines()), 1)

    def test_workshop_repository_links_only_point_to_current_repository(self):
        for document in DOCUMENTS:
            text = document.read_text(encoding="utf-8")
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                url = urlsplit(link)
                parts = url.path.strip("/").split("/")
                if url.netloc == "github.com" and parts[0] == "junwoojeong100":
                    with self.subTest(document=document.name, link=link):
                        self.assertGreaterEqual(len(parts), 2)
                        self.assertEqual(parts[1], "foundry-evaluation-v1")

    def test_main_preparation_smoke_is_one_committed_extra_case_not_dev_or_holdout(self):
        commands = lab_commands(ROOT / "README.md")
        runs = [lab.parser().parse_args(argv) for argv in commands if argv[0] == "run"]
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
        self.assertLess(
            commands.index(["doctor", "--live"]),
            next(i for i, argv in enumerate(commands) if argv[0] == "run"),
        )

    def test_main_preparation_uses_one_deployment_for_answers_and_judging(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        configs = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL)]
        configs = [config for config in configs if "project_endpoint" in config]
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0]["model_deployment"], "eval-model")
        self.assertEqual(configs[0]["judge_deployment"], "eval-model")
        self.assertEqual(configs[0], read_json(ROOT / "config.example.json"))

    def test_setup_shortcuts_do_not_duplicate_the_main_command_sequence(self):
        self.assertEqual(lab_commands(ROOT / "docs" / "setup.md"), [])

    def test_documented_extra_cases_and_validation_commands_work_locally(self):
        for document in (ROOT / "README.md", ROOT / "docs" / "offline.md"):
            text = document.read_text(encoding="utf-8")
            examples = re.findall(r"```jsonl\n(.*?)```", text, re.DOTALL)
            commands = [
                shlex.split(line)
                for block in SHELL_BLOCKS.findall(text)
                for line in block.splitlines()
                if line.startswith("python -c ")
            ]
            with self.subTest(document=document.name), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(len(examples), 1)
                self.assertEqual(len(examples[0].splitlines()), 1)
                self.assertEqual(len(commands), 1)
                workspace = Path(directory)
                data_file = workspace / "data" / "my-case.jsonl"
                data_file.parent.mkdir()
                data_file.write_text(examples[0], encoding="utf-8")
                cases = read_cases(data_file)
                self.assertEqual(len(cases), 1)
                self.assertEqual(cases[0]["id"], "N02")
                self.assertEqual(cases[0]["expected_decision"], "needs_approval")
                self.assertEqual(cases[0]["expected_limit_krw"], 160000)
                self.assertEqual(cases[0]["expected_citations"], ["TRAVEL-PREVIOUS"])
                for split in ("dev", "holdout"):
                    for existing in read_cases(ROOT / "data" / f"{split}.jsonl"):
                        self.assertNotEqual(cases[0]["id"], existing["id"])
                        self.assertNotEqual(cases[0]["query"], existing["query"])
                for valid in (True, False):
                    if not valid:
                        cases[0]["critical"] = "true"
                        data_file.write_text(json.dumps(cases[0]) + "\n", encoding="utf-8")
                    outcome = subprocess.run(
                        [sys.executable, *commands[0][1:]],
                        cwd=workspace,
                        env={**os.environ, "PYTHONPATH": str(ROOT)},
                        capture_output=True, text=True, timeout=15,
                    )
                    if valid:
                        self.assertEqual(outcome.returncode, 0, outcome.stderr)
                        self.assertEqual(outcome.stdout.strip(), "DATA OK: 1 case(s)")
                    else:
                        self.assertNotEqual(outcome.returncode, 0)
                        self.assertNotIn("DATA OK", outcome.stdout)
                        self.assertIn("critical은 true 또는 false", outcome.stderr)

    def test_human_judgments_precede_baseline_judge_scores(self):
        for document, folder in (
            (ROOT / "README.md", "results/baseline"),
            (ROOT / "docs" / "offline.md", "results/demo-baseline"),
        ):
            commands = lab_commands(document)
            judge_index = commands.index(["judge", folder])
            with self.subTest(document=document.name):
                self.assertIn(["inspect", folder, "D04"], commands[:judge_index])
                self.assertIn(["inspect", folder, "D04"], commands[judge_index + 1:])

    def test_offline_guide_commands_execute_as_written_without_network(self):
        commands = lab_commands(ROOT / "docs" / "offline.md")
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
                for command in commands:
                    argv = [
                        str(output / arg) if arg.startswith("results/") else arg
                        for arg in command
                    ]
                    with self.subTest(command=command):
                        self.assertEqual(lab.main(argv), 2 if argv[0] == "gate" else 0)
            result = read_json(output / "results" / "demo-candidate" / "gate.json")
            self.assertEqual(result["status"], "BLOCK")
            self.assertEqual(result["business_rates"], {"baseline": 0.625, "candidate": 1.0, "holdout": 0.75})
            self.assertTrue(any("사람이 반려" in problem for problem in result["problems"]))
            comparison = read_json(output / "results" / "demo-candidate" / "comparison.json")
            self.assertEqual(comparison["improvements"], ["D03", "D04", "D08"])
            self.assertEqual(comparison["regressions"], [])
            self.assertEqual(comparison["judge_regressions"], [])
            trap = read_json(output / "results" / "trap-candidate" / "comparison.json")
            self.assertEqual([entry["id"] for entry in trap["regressions"]], ["D06"])


if __name__ == "__main__":
    unittest.main()

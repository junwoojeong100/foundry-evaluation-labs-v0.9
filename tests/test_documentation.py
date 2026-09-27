from __future__ import annotations

import io
import json
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
from xml.etree import ElementTree

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

    def test_live_demo_and_worksheet_share_steps_with_judgment_before_setup(self):
        worksheet = (ROOT / "WORKSHEET.md").read_text(encoding="utf-8")
        steps = [
            str(step)
            for first, last in re.findall(r"^## (\d+)(?:–(\d+))?\.", worksheet, re.MULTILINE)
            for step in range(int(first), int(last or first) + 1)
        ]
        self.assertEqual(steps, [str(i) for i in range(7)])
        for document in (ROOT / "README.md", ROOT / "docs" / "offline.md"):
            text = document.read_text(encoding="utf-8")
            with self.subTest(document=document.name):
                self.assertEqual(re.findall(r"^## (\d+)\.", text, re.MULTILINE), steps)
                self.assertEqual(re.findall(r'<a id="lab-(\d+)"></a>', text), steps)
                warmup_start = text.index('<a id="lab-0"></a>')
                setup_start = text.index('<a id="prepare"></a>')
                criteria_start = text.index('<a id="lab-1"></a>')
                self.assertLess(warmup_start, setup_start)
                self.assertLess(setup_start, criteria_start)
                self.assertFalse(SHELL_BLOCKS.search(text[warmup_start:setup_start]))
                self.assertIn("A/B", text[setup_start:criteria_start])
                self.assertIn("실습 1로 이어갑니다", text[setup_start:criteria_start])
        setup = (ROOT / "docs" / "setup.md").read_text(encoding="utf-8")
        existing = setup.split('<a id="existing-environment"></a>')[1].split('<a id="cost"></a>')[0]
        self.assertIn("5. [실습 1](../README.md#lab-1)", existing)

    def test_permission_illustration_is_labeled_and_linked(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"!\[[^\]]+\]\(docs/images/foundry-permissions\.svg\)")
        self.assertIn("실제 포털 캡처가 아닙니다", text)
        svg = ElementTree.parse(ROOT / "docs" / "images" / "foundry-permissions.svg").getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        self.assertEqual(svg.tag, f"{namespace}svg")
        self.assertEqual(svg.get("role"), "img")
        self.assertEqual(svg.get("aria-labelledby"), "title description")
        self.assertIsNotNone(svg.find(f"{namespace}title[@id='title']"))
        self.assertIsNotNone(svg.find(f"{namespace}desc[@id='description']"))
        labels = " ".join(svg.itertext())
        for label in ("Object (principal) ID", "Access control (IAM)", "Foundry User", "/projects/eval-workshop"):
            self.assertIn(label, labels)
        self.assertEqual(labels.count("PROJECT-PRINCIPAL-ID"), 2)

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

    def test_live_guides_keep_requested_model_region_and_deployment_distinct(self):
        for relative in ("README.md", "WORKSHEET.md", "docs/setup.md", "docs/reference.md", "docs/facilitator.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(document=relative):
                self.assertIn("gpt-6-luna", text)
                self.assertIn("swedencentral", text)
                self.assertIn("eval-model", text)
                for obsolete in ("gpt-4.1-mini", "gpt-sol-luna", "East US 2"):
                    self.assertNotIn(obsolete, text)
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("account:user.name", text)
        reference = (ROOT / "docs" / "reference.md").read_text(encoding="utf-8")
        self.assertIn('id="live-verification"', reference)
        self.assertNotIn("전체 LIVE 실습은 아직 검증하지 않았습니다", reference)

    def test_cli_setup_preserves_project_identity_and_least_privilege(self):
        text = (ROOT / "docs" / "setup.md").read_text(encoding="utf-8")
        section = text.split('<a id="cli-provision"></a>')[1].split('<a id="existing-environment"></a>')[0]
        for required in (
            "--allow-project-management true", "--assign-identity",
            "--assignee-principal-type User", "--assignee-principal-type ServicePrincipal",
            '--scope "YOUR-FOUNDRY-RESOURCE-ID"', "--location swedencentral",
            "--model-name gpt-6-luna", "--deployment-name eval-model",
        ):
            self.assertIn(required, section)
        self.assertIn("생략하지 않습니다", section)
        self.assertIn("없는 대상에게만", section)
        self.assertIn("삭제 명령을 실행하지 않습니다", section)

    def test_portal_comparison_selects_matching_dev_runs_and_v1_baseline(self):
        for relative in ("README.md", "docs/reference.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(document=relative):
                for required in ("Evaluation runs", "Compare runs", "Baseline", "v1-dev-", "my-v2-dev-", "Too few samples"):
                    self.assertIn(required, text)

    def test_live_rehearsal_record_distinguishes_execution_from_human_approval(self):
        text = (ROOT / "docs" / "reference.md").read_text(encoding="utf-8")
        section = text.split('<a id="live-verification"></a>')[1].split("## 공식 출처")[0]
        for required in (
            "22개 응답", "44개 지표", "5개 평가 실행", "한 번의 실제 실행",
            "실제 사람 검토는 미완료", "--reviewer assistant", "최종 Gate는 `BLOCK`",
        ):
            self.assertIn(required, section)
        self.assertIn("| Candidate dev | 8 | 8/8 | 8/8 | 6/8 |", section)
        self.assertIn("| 고정 Holdout | 4 | 4/4 | 4/4 | 2/4 |", section)

    def test_retention_is_the_default_and_deletion_is_explicitly_optional(self):
        main = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertLess(
            main.index('<a id="retain-resources"></a>'),
            main.index('<a id="delete-resources"></a>'),
        )
        for relative in ("README.md", "WORKSHEET.md", "docs/cleanup.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(document=relative):
                self.assertIn("별도 요청 전까지 유지", text)
                self.assertIn("보존", text)
        cleanup = (ROOT / "docs" / "cleanup.md").read_text(encoding="utf-8")
        self.assertIn("3–5단계는 건너뜁니다", cleanup)
        self.assertIn("리소스 보존 요청이 있는 동안 삭제하지 않습니다", cleanup)
        self.assertIn("과금 중지가 아닙니다", cleanup)

    def test_setup_shortcuts_do_not_duplicate_the_main_command_sequence(self):
        self.assertEqual(lab_commands(ROOT / "docs" / "setup.md"), [])

    def test_documented_extra_cases_and_validation_commands_work_locally(self):
        for document in (ROOT / "README.md", ROOT / "docs" / "offline.md"):
            text = document.read_text(encoding="utf-8")
            examples = re.findall(r"```jsonl\n(.*?)```", text, re.DOTALL)
            commands = [argv for argv in lab_commands(document) if argv[0] == "validate-data"]
            with self.subTest(document=document.name), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(len(examples), 1)
                self.assertEqual(len(examples[0].splitlines()), 1)
                self.assertEqual(commands, [["validate-data", "data/my-case.jsonl"]])
                self.assertNotIn("python -c ", text)
                self.assertIn("`170000` → `180000`", text)
                workspace = Path(directory)
                data_file = workspace / "data" / "my-case.jsonl"
                data_file.parent.mkdir()
                for amount in ("170000", "180000"):
                    with self.subTest(amount=amount):
                        data_file.write_text(examples[0].replace("170000", amount), encoding="utf-8")
                        cases = read_cases(data_file)
                        self.assertEqual(len(cases), 1)
                        self.assertEqual(cases[0]["id"], "N02")
                        self.assertEqual(cases[0]["expected_decision"], "needs_approval")
                        self.assertEqual(cases[0]["expected_limit_krw"], 160000)
                        self.assertEqual(cases[0]["expected_citations"], ["TRAVEL-PREVIOUS"])
                        self.assertIn(f"1박 {amount}원", cases[0]["query"])
                        self.assertIn(f"{amount}원은 한도 초과", cases[0]["ground_truth"])
                        for split in ("dev", "holdout"):
                            for existing in read_cases(ROOT / "data" / f"{split}.jsonl"):
                                self.assertNotEqual(cases[0]["id"], existing["id"])
                                self.assertNotEqual(cases[0]["query"], existing["query"])
                        for valid in (True, False):
                            if not valid:
                                cases[0]["critical"] = "true"
                                data_file.write_text(json.dumps(cases[0]) + "\n", encoding="utf-8")
                            outcome = subprocess.run(
                                [sys.executable, str(ROOT / "lab.py"), *commands[0]],
                                cwd=workspace,
                                capture_output=True, text=True, timeout=15,
                            )
                            if valid:
                                self.assertEqual(outcome.returncode, 0, outcome.stderr)
                                self.assertEqual(outcome.stdout.strip(), "DATA OK: 1 case(s)")
                            else:
                                self.assertEqual(outcome.returncode, 1)
                                self.assertNotIn("DATA OK", outcome.stdout)
                                self.assertTrue(outcome.stderr.startswith("ERROR:"))
                                self.assertIn("critical은 true 또는 false", outcome.stderr)
                                self.assertNotIn("Traceback", outcome.stderr)

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
        document = ROOT / "docs" / "offline.md"
        text = document.read_text(encoding="utf-8")
        commands = lab_commands(document)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            case_file = output / "data" / "my-case.jsonl"
            case_file.parent.mkdir()
            example = re.findall(r"```jsonl\n(.*?)```", text, re.DOTALL)[0]
            case_file.write_text(example.replace("170000", "180000"), encoding="utf-8")
            input_paths = {"data/my-case.jsonl": str(case_file)}
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
                        str(output / arg) if arg.startswith("results/") else input_paths.get(arg, arg)
                        for arg in command
                    ]
                    command_output = io.StringIO()
                    with self.subTest(command=command), redirect_stdout(command_output):
                        self.assertEqual(lab.main(argv), 2 if argv[0] == "gate" else 0)
                        if argv[0] == "judge":
                            folder = Path(argv[1])
                            count = len(read_json(folder / "judge.json")["rows"])
                            checkpoint = f"평가 완료: {count}개 답변 × 2개 지표"
                            self.assertIn(checkpoint, text)
                            self.assertIn(checkpoint, command_output.getvalue())
                            self.assertIn(f"Judge 결과: {folder / 'judge.json'}", command_output.getvalue())
                            self.assertIn("사례별 근거", (folder / "report.md").read_text(encoding="utf-8"))
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

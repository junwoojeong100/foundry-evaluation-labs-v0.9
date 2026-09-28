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

import advanced_lab
import advanced_retrieval
import lab
import rag_lab
from evaluation import ANSWER_SCHEMA, DECISIONS, ROOT, read_cases, read_json

DOCUMENTS = sorted([*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md")])
SHELL_BLOCKS = re.compile(r"```(?:bash|powershell)\n(.*?)```", re.DOTALL)


def shell_commands(document: Path) -> list[list[str]]:
    return [
        shlex.split(line, comments=True)
        for block in SHELL_BLOCKS.findall(document.read_text(encoding="utf-8"))
        for line in block.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def lab_commands(document: Path, script: str = "lab.py") -> list[list[str]]:
    return [command[2:] for command in shell_commands(document) if command[:2] == ["python", script]]


class DocumentationTests(unittest.TestCase):
    def test_readme_openings_credit_the_original_workshop_inspiration(self):
        source = "https://snscratchpad.com/posts/frontier-ecosystem/"
        for relative in ("README.ko.md", "README.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            opening = text.split('<a id="choose-path"></a>')[0]
            with self.subTest(guide=relative):
                self.assertIn("Satya Nadella", opening)
                self.assertIn(f"]({source})", opening)
                self.assertEqual(text.count(source), 1)

    def test_setup_identifies_the_local_shell_and_shows_the_activation_fallback(self):
        for relative in ("README.ko.md", "README.md", "docs/offline.md", "docs/en/offline.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            preparation = text.split('<a id="prepare"></a>')[1].split('<a id="working-files"></a>')[0]
            with self.subTest(guide=relative):
                for required in (
                    "Azure Cloud Shell", "PowerShell", "Select Default Profile",
                    "zsh", "bash", r"`.\.venv\Scripts\python.exe lab.py doctor`",
                ):
                    self.assertIn(required, preparation)

    def test_each_learning_path_explains_the_answer_contract_without_another_path(self):
        paths = [
            ("README.ko.md", "lab-1", "lab-2"),
            ("README.md", "lab-1", "lab-2"),
        ]
        for language in ("", "en/"):
            paths.extend((
                (f"docs/{language}complete-lab.md", "read-case", "dialogue-check"),
                (f"docs/{language}offline.md", "lab-3", "lab-4"),
                (f"docs/{language}optional-rag.md", "evaluate", "resume"),
            ))
        for relative, start, end in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            explanation = text.split(f'<a id="{start}"></a>')[1].split(f'<a id="{end}"></a>')[0]
            with self.subTest(guide=relative):
                for field in ANSWER_SCHEMA["required"]:
                    self.assertIn(f"`{field}`", explanation)
                for decision in DECISIONS:
                    self.assertIn(f"`{decision}`", explanation)
                self.assertIn("`null`", explanation)

    def test_complete_stage_map_matches_the_documented_execution_order(self):
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            document = ROOT / relative
            text = document.read_text(encoding="utf-8")
            stage_map = text.split('<a id="run-stages"></a>')[1].split("```bash", 1)[0]
            described = re.findall(r"^\| `([^`]+)` \|", stage_map, re.MULTILINE)
            stages = [
                advanced_lab.parser().parse_args(argv).stage
                for argv in lab_commands(document, "advanced_lab.py")
                if argv[0] in ("run", "judge")
            ]
            with self.subTest(guide=relative):
                self.assertEqual(described, list(dict.fromkeys(stages)))
                self.assertEqual(len(described), 4)
                self.assertIn("results/advanced/v2-replay/report.md", stage_map)
                shared = text.split('<a id="common-setup"></a>')[1].split('<a id="search-setup"></a>')[0]
                self.assertIn("평가 완료: 1개 답변 × 2개 지표", shared)
                self.assertIn("(#search-setup)", shared)

    def test_complete_endpoint_table_keeps_all_three_addresses_distinct(self):
        endpoints = (
            ("config.json", "project_endpoint", ".services.ai.azure.com/api/projects/"),
            ("config.advanced.json", "search_endpoint", ".search.windows.net"),
            ("config.advanced.json", "model_resource_endpoint", ".openai.azure.com"),
        )
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            configuration = text.split('<a id="configure"></a>')[1].split('<a id="resume"></a>')[0]
            for filename, field, address in endpoints:
                rows = [
                    line for line in configuration.splitlines()
                    if line.startswith("|") and f"`{filename}`" in line and f"`{field}`" in line
                ]
                with self.subTest(guide=relative, field=field):
                    self.assertEqual(len(rows), 1)
                    self.assertIn(address, rows[0])

    def test_demo_candidate_generation_has_a_checkpoint_before_judging(self):
        cases = read_cases(ROOT / "data/dev.jsonl")
        signal = f"{len(cases)}/{len(cases)}  {cases[-1]['id']} 저장"
        for relative in ("docs/offline.md", "docs/en/offline.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            blocks = list(SHELL_BLOCKS.finditer(text))
            index = next(
                index for index, block in enumerate(blocks)
                if block.group(1).strip() == "python lab.py run --mode demo --prompt v2 --out results/demo-candidate"
            )
            checkpoint = text[blocks[index].end():blocks[index + 1].start()]
            with self.subTest(guide=relative):
                self.assertIn(signal, checkpoint)
                self.assertEqual(
                    blocks[index + 1].group(1).strip(),
                    "python lab.py judge results/demo-candidate --like results/demo-baseline",
                )

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
        parsers = {
            "lab.py": lab.parser(),
            "rag_lab.py": rag_lab.parser(),
            "advanced_lab.py": advanced_lab.parser(),
        }
        counts = dict.fromkeys(parsers, 0)
        for document in DOCUMENTS:
            for script, parser in parsers.items():
                for argv in lab_commands(document, script):
                    with self.subTest(document=document.relative_to(ROOT), script=script, command=argv):
                        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                            if "--help" in argv:
                                with self.assertRaises(SystemExit) as outcome:
                                    parser.parse_args(argv)
                                self.assertEqual(outcome.exception.code, 0)
                            else:
                                parser.parse_args(argv)
                        counts[script] += 1
        self.assertGreater(counts["lab.py"], 35)
        self.assertGreater(counts["rag_lab.py"], 8)
        self.assertGreater(counts["advanced_lab.py"], 10)

    def test_main_path_is_checkpoint_driven_without_a_time_limit(self):
        text = (ROOT / "README.ko.md").read_text(encoding="utf-8")
        self.assertIn("시간 제한 없이", text)
        self.assertIn("(docs/setup.md)", text)
        self.assertIn("(docs/cleanup.md)", text)
        for anchor in (
            "choose-path", "prepare", "setup-tools", "setup-sign-in", "setup-project",
            "setup-permissions", "setup-model", "setup-config", "setup-smoke",
            "command-status", "finish",
        ):
            self.assertIn(f'<a id="{anchor}"></a>', text)
        self.assertEqual(re.findall(r'<a id="lab-(\d+)"></a>', text), [str(i) for i in range(7)])
        self.assertNotRegex(text, r"\d{2}:\d{2}[–-]\d{2}:\d{2}")
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("No time limit", english)
        self.assertIn("(docs/en/setup.md)", english)
        self.assertIn("(docs/en/cleanup.md)", english)
        for document in DOCUMENTS:
            with self.subTest(document=document.name):
                content = document.read_text(encoding="utf-8")
                self.assertNotIn("3시간", content)
                self.assertNotIn("180분", content)

    def test_live_and_demo_share_steps_with_judgment_before_setup(self):
        steps = [str(i) for i in range(7)]
        for document in (ROOT / "README.ko.md", ROOT / "docs" / "offline.md"):
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
                self.assertIn("실습 1로 이어갑니다", text[setup_start:criteria_start])
        setup = (ROOT / "docs" / "setup.md").read_text(encoding="utf-8")
        existing = setup.split('<a id="existing-environment"></a>')[1].split('<a id="cost"></a>')[0]
        self.assertIn("5. [실습 1](../README.ko.md#lab-1)", existing)

    def test_permission_illustration_is_labeled_and_linked(self):
        text = (ROOT / "README.ko.md").read_text(encoding="utf-8")
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

    def test_default_readme_is_english_and_both_languages_run_identical_commands(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(english.startswith("**English** | [한국어](README.ko.md)"))
        self.assertIn("# Can you trust an AI answer?", english)
        self.assertIn("remain **Korean**", english)
        for left, right in (
            ("README.md", "README.ko.md"),
            ("docs/en/offline.md", "docs/offline.md"),
        ):
            with self.subTest(english=left):
                self.assertEqual(lab_commands(ROOT / left), lab_commands(ROOT / right))
                before = (ROOT / left).read_text(encoding="utf-8")
                after = (ROOT / right).read_text(encoding="utf-8")
                self.assertEqual(
                    re.findall(r"```jsonl\n(.*?)```", before, re.DOTALL),
                    re.findall(r"```jsonl\n(.*?)```", after, re.DOTALL),
                )
                self.assertEqual(
                    re.findall(r'<a id="lab-(\d+)"></a>', before),
                    [str(i) for i in range(7)],
                )

    def test_supporting_guides_have_matching_anchors_and_language_navigation(self):
        for name in ("setup", "reference", "offline", "cleanup", "facilitator", "complete-lab", "optional-rag"):
            korean = (ROOT / "docs" / f"{name}.md").read_text(encoding="utf-8")
            english = (ROOT / "docs" / "en" / f"{name}.md").read_text(encoding="utf-8")
            with self.subTest(guide=name):
                self.assertIn(f"(en/{name}.md)", korean)
                self.assertIn(f"(../{name}.md)", english)
                self.assertEqual(
                    set(re.findall(r'<a id="([^"]+)"></a>', korean)),
                    set(re.findall(r'<a id="([^"]+)"></a>', english)),
                )
                without_translation_link = korean.replace("[영문 기본 가이드](../README.md)", "")
                self.assertNotIn("(../README.md", without_translation_link)
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("not an actual portal screenshot", english)
        svg = ElementTree.parse(ROOT / "docs" / "images" / "foundry-permissions.en.svg").getroot()
        self.assertEqual(svg.get("role"), "img")
        self.assertEqual(" ".join(svg.itertext()).count("PROJECT-PRINCIPAL-ID"), 2)

    def test_guides_have_no_worksheet_templates_or_dependencies(self):
        for name in ("WORKSHEET.md", "WORKSHEET.en.md"):
            self.assertFalse((ROOT / name).exists())
        artifacts = [*DOCUMENTS, *(ROOT / "docs").rglob("*.svg"), ROOT / "tools/media/workshop_video.py"]
        for document in artifacts:
            with self.subTest(document=document.relative_to(ROOT)):
                self.assertNotRegex(
                    document.read_text(encoding="utf-8"),
                    re.compile(r"worksheet|실습지|워크시트", re.IGNORECASE),
                )

    def test_complete_path_returns_from_shared_setup_and_keeps_criteria_inline(self):
        for readme, guide, setup in (
            ("README.ko.md", "docs/complete-lab.md", "docs/setup.md"),
            ("README.md", "docs/en/complete-lab.md", "docs/en/setup.md"),
        ):
            with self.subTest(guide=guide):
                main = (ROOT / readme).read_text(encoding="utf-8")
                preparation = main.split('<a id="prepare"></a>')[1].split('<a id="lab-1"></a>')[0]
                self.assertIn(f"({guide}#search-setup)", preparation)
                smoke = preparation.split('<a id="setup-smoke"></a>')[1]
                optional_guide = guide.replace("complete-lab.md", "optional-rag.md")
                self.assertIn(f"({guide}#search-setup)", smoke)
                self.assertIn(f"({optional_guide}#prerequisites)", smoke)
                self.assertIn("(complete-lab.md#search-setup)", (ROOT / setup).read_text(encoding="utf-8"))
                self.assertIn("(optional-rag.md#prerequisites)", (ROOT / setup).read_text(encoding="utf-8"))
                complete = (ROOT / guide).read_text(encoding="utf-8")
                for required in ("100%", "4/5", "CALIBRATION PASSED: 10 controls", "intermediate_safe", "D04", "D08", "N05", "N06"):
                    self.assertIn(required, complete)
                self.assertIn("results/advanced/acceptance-report.md", complete)
                self.assertIn("80%", main.split('<a id="lab-1"></a>')[1])

    def test_all_guides_keep_shell_commands_identical_between_languages(self):
        pairs = [("README.ko.md", "README.md")]
        pairs.extend(
            (f"docs/{name}.md", f"docs/en/{name}.md")
            for name in ("setup", "reference", "offline", "cleanup", "facilitator", "complete-lab", "optional-rag")
        )
        for korean, english in pairs:
            with self.subTest(guide=korean):
                self.assertEqual(shell_commands(ROOT / korean), shell_commands(ROOT / english))

    def test_complete_model_preflight_precedes_additional_resource_creation(self):
        fixture = read_json(ROOT / "advanced-rag/fixtures/recorded-v1.json")
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(guide=relative):
                creation = text.index("az search service create --name")
                for field in ("name", "model_name", "model_version"):
                    self.assertLess(text.index(fixture["model_snapshot"][field]), creation)
                for command in (
                    "az cognitiveservices account deployment show",
                    "az cognitiveservices model list",
                    "az cognitiveservices usage list",
                ):
                    self.assertLess(text.index(command), creation)
                self.assertLess(text.index("az search service check-name-availability"), creation)
                self.assertIn("(#search-access)", text)
                self.assertIn("config.advanced.json", text[:text.index("python advanced_lab.py setup")])

    def test_complete_setup_has_six_inline_steps_without_an_optional_rag_detour(self):
        anchors = (
            "common-setup", "search-setup", "search-service",
            "search-access", "extra-models", "configure",
        )
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            setup = text.split('<a id="setup"></a>')[1].split('<a id="resume"></a>')[0]
            with self.subTest(guide=relative):
                self.assertEqual(re.findall(r"^### 2-(\d)\.", setup, re.MULTILINE), list("123456"))
                for anchor in anchors:
                    self.assertIn(f"(#{anchor})", setup)
                    self.assertIn(f'<a id="{anchor}"></a>', setup)
                self.assertNotIn("(optional-rag.md", setup)
                self.assertLess(
                    setup.index("az search service show"),
                    setup.index("az ad signed-in-user show"),
                )

    def test_search_provider_is_checked_before_creating_either_search_path(self):
        for name in ("complete-lab", "optional-rag"):
            for language in ("", "en/"):
                relative = f"docs/{language}{name}.md"
                text = (ROOT / relative).read_text(encoding="utf-8")
                with self.subTest(guide=relative):
                    before_creation = text[:text.index("az search service create --name")]
                    self.assertIn("Resource providers", before_creation)
                    self.assertIn("**`Microsoft.Search`**", before_creation)
                    self.assertIn("`Registered`", before_creation)
                    self.assertIn("management/resource-providers-and-types", before_creation)

    def test_complete_generation_and_judging_have_checkpoints_before_the_next_command(self):
        dev_count = len(advanced_lab.baseline()["cases"])
        counts = {
            "v1-recorded": dev_count,
            "v2-replay": dev_count,
            "planned-dev": dev_count,
            "holdout": 8,
        }
        expected = {("judge", stage) for stage in counts}
        expected.update(("run", stage) for stage in counts if stage != "v1-recorded")
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            blocks = list(SHELL_BLOCKS.finditer(text))
            checked = set()
            for index, block in enumerate(blocks):
                command = shlex.split(block.group(1), comments=True)
                if command[:2] != ["python", "advanced_lab.py"]:
                    continue
                args = advanced_lab.parser().parse_args(command[2:])
                if args.command not in ("run", "judge"):
                    continue
                checkpoint_end = blocks[index + 1].start() if index + 1 < len(blocks) else len(text)
                checkpoint = text[block.end():checkpoint_end]
                count = counts[args.stage]
                signal = (
                    f"GENERATION COMPLETE: {args.stage}; {count} answers."
                    if args.command == "run" else f"Evaluation complete: {count} cases × 3 metrics"
                )
                with self.subTest(guide=relative, command=command):
                    self.assertIn(signal, checkpoint)
                checked.add((args.command, args.stage))
            self.assertEqual(checked, expected)

    def test_complete_learner_finish_precedes_optional_historical_results(self):
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(guide=relative):
                self.assertEqual(re.findall(r"^## (\d+)\.", text, re.MULTILINE), list("12345678"))
                introduction = text.split('<a id="architecture"></a>')[1].split('<a id="setup"></a>')[0]
                self.assertIn("data/policies.md", introduction)
                self.assertFalse(SHELL_BLOCKS.search(introduction))
                finish = text.split('<a id="retention"></a>')[1].split('<a id="results"></a>')[0]
                for required in (
                    "- [ ]", "acceptance-report.md", "calibration-result.json",
                    "judge-contract.json", "frozen.json", "N05", "N06",
                    "(cleanup.md#retain-resources)",
                ):
                    self.assertIn(required, finish)
                historical = text.split('<a id="results"></a>')[1]
                self.assertIn("<details>", historical)
                self.assertIn("</details>", historical)

    def test_complete_baseline_explanation_matches_the_recorded_citation_failure(self):
        fixture = advanced_lab.baseline()
        case = next(case for case in fixture["cases"] if case["id"] == "D02")
        row = next(row for row in fixture["rows"] if row["case_id"] == "D02")
        expected = case["expected_citations"]
        actual = row["response"]["citations"]
        self.assertNotEqual(actual, expected)
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(guide=relative):
                section = text.split('<a id="improve"></a>')[1].split('<a id="freeze"></a>')[0]
                self.assertIn(json.dumps(expected), section)
                self.assertIn(json.dumps(actual), section)

    def test_complete_case_reading_explains_inspection_and_links_from_freeze_failures(self):
        labels = (
            "Case result", "Question", "Expected decision / limit / citations", "Expected behavior",
            "Actual answer", "Business checks", "Required chunks", "Chunks", "Required chunks found",
            "Scores", "Final scores", "Initial field checks",
        )
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(guide=relative):
                reading = text.split('<a id="read-case"></a>')[1].split('<a id="dialogue-check"></a>')[0]
                for label in labels:
                    self.assertIn(f"`{label}`", reading)
                for required in ("current-lodging", "TRAVEL-CURRENT", "--context", "report.md", "true", "false"):
                    self.assertIn(required, reading)
                resume = text.split('<a id="resume"></a>')[1].split('<a id="retrieval-proof"></a>')[0]
                freeze = text.split('<a id="freeze"></a>')[1].split('<a id="holdout"></a>')[0]
                for section in (resume, freeze):
                    self.assertIn("Dev acceptance is not met", section)
                    self.assertIn("(#read-case)", section)

    def test_both_rag_paths_include_the_same_service_scoped_user_roles(self):
        roles_by_guide = {}
        for name in ("complete-lab", "optional-rag"):
            for language in ("", "en/"):
                relative = f"docs/{language}{name}.md"
                document = ROOT / relative
                text = document.read_text(encoding="utf-8")
                end_anchor = "search-model-access" if name == "complete-lab" else "index"
                section = text.split('<a id="search-access"></a>')[1].split(f'<a id="{end_anchor}"></a>')[0]
                commands = [
                    command for command in shell_commands(document)
                    if command[:4] == ["az", "role", "assignment", "create"]
                    and "YOUR-USER-OBJECT-ID" in command
                ]
                roles_by_guide[relative] = commands
                with self.subTest(guide=relative):
                    self.assertLess(
                        section.index("az ad signed-in-user show"),
                        section.index('az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID"'),
                    )
                    self.assertIn('"{account:userPrincipalName,objectId:id}"', section)
                    self.assertEqual(len(commands), 2)
                    self.assertEqual(
                        {command[command.index("--role") + 1] for command in commands},
                        {"7ca78c08-252a-4471-8644-bb5ff32d4ba0", "8ebe5a00-799e-43f5-93ac-243d3dce84a7"},
                    )
                    for command in commands:
                        self.assertEqual(command[command.index("--assignee-principal-type") + 1], "User")
                        self.assertEqual(command[command.index("--scope") + 1], "YOUR-SEARCH-RESOURCE-ID")
        self.assertTrue(all(commands == roles_by_guide["docs/complete-lab.md"] for commands in roles_by_guide.values()))

    def test_rag_queries_and_comparison_have_checkpoints_before_the_next_command(self):
        for name, script, parser, expected_count in (
            ("complete-lab", "advanced_lab.py", advanced_lab.parser(), 2),
            ("optional-rag", "rag_lab.py", rag_lab.parser(), 3),
        ):
            for language in ("", "en/"):
                relative = f"docs/{language}{name}.md"
                text = (ROOT / relative).read_text(encoding="utf-8")
                blocks = list(SHELL_BLOCKS.finditer(text))
                checked = 0
                for index, block in enumerate(blocks):
                    command = shlex.split(block.group(1), comments=True)
                    if command[:2] != ["python", script]:
                        continue
                    args = parser.parse_args(command[2:])
                    if args.command not in ("query", "compare"):
                        continue
                    end = blocks[index + 1].start() if index + 1 < len(blocks) else len(text)
                    checkpoint = text[block.end():end]
                    with self.subTest(guide=relative, command=command):
                        if args.command == "query":
                            self.assertIn(f"RETRIEVAL OK: {args.mode}", checkpoint)
                            self.assertIn(args.out.as_posix(), checkpoint)
                        else:
                            self.assertIn("REVIEW_REQUIRED", checkpoint)
                            self.assertIn((args.iq / "rag-comparison.md").as_posix(), checkpoint)
                    checked += 1
                self.assertEqual(checked, expected_count)

    def test_complete_resume_distinguishes_partial_quality_failures_and_remote_ids(self):
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            section = text.split('<a id="resume"></a>')[1].split('<a id="retrieval-proof"></a>')[0]
            with self.subTest(guide=relative):
                for required in (
                    "calibrate", "judge --stage", "generation.json", "collecting", "pending",
                    "initial_response", "initial clarification/handoff field checks failed",
                    "calibration-result.json", "evaluation-request.json", "foundry-job.json",
                    "LAB_ACCEPTANCE_BLOCKED", "300", "--out",
                    "Using complete saved generation; no new model/retrieval calls.",
                    "Existing frozen experiment retained.", "Existing holdout registration retained.",
                    "(#retrieval-proof)", "(#calibration)", "(#improve)", "(#freeze)",
                    "(#holdout)", "(#retention)",
                ):
                    self.assertIn(required, section)
        for relative in ("docs/reference.md", "docs/en/reference.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(reference=relative):
                self.assertIn("results/advanced/<stage>/evaluation-request.json", text)
                self.assertIn("calibration", text)

    def test_recorded_results_and_initial_prose_limits_are_explicit(self):
        for relative, observed, limitation in (
            ("docs/complete-lab.md", "재현 보장이 아닙니다", "초기 설명 문장의 의미"),
            ("docs/en/complete-lab.md", "not a reproduction guarantee", "initial prose received a separate semantic"),
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(guide=relative):
                self.assertIn(observed, text)
                self.assertIn(limitation, text)
                self.assertIn("intermediate_safe", text)
                self.assertIn("`search`/`iq`", text)

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
                        self.assertEqual(parts[1], "foundry-evaluation-labs-v1")

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
        for relative in ("README.md", "README.ko.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            configs = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL)]
            configs = [config for config in configs if "project_endpoint" in config]
            with self.subTest(guide=relative):
                self.assertEqual(len(configs), 1)
                self.assertEqual(configs[0]["model_deployment"], "eval-model")
                self.assertEqual(configs[0]["judge_deployment"], "eval-model")
                self.assertEqual(configs[0], read_json(ROOT / "config.example.json"))

    def test_optional_rag_configuration_examples_match_the_template(self):
        expected = read_json(ROOT / "optional-rag/config.example.json")
        for relative in ("docs/optional-rag.md", "docs/en/optional-rag.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            configs = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL)]
            configs = [config for config in configs if "search_endpoint" in config]
            with self.subTest(guide=relative):
                self.assertEqual(configs, [expected])

    def test_complete_configuration_examples_match_template_and_validate_after_substitution(self):
        expected = read_json(ROOT / "advanced-rag/config.example.json")
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            configs = [
                json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL)
            ]
            with self.subTest(guide=relative), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(configs, [expected])
                config = {
                    **configs[0],
                    "search_endpoint": "https://feval-search-a7k3m9.search.windows.net",
                    "model_resource_endpoint": "https://feval-a7k3m9.openai.azure.com",
                    "index_name": "travel-vector-a7k3m9",
                    "knowledge_source": "travel-vector-ks-a7k3m9",
                    "knowledge_base": "travel-planned-kb-a7k3m9",
                }
                path = Path(directory) / "config.advanced.json"
                path.write_text(json.dumps(config), encoding="utf-8")
                self.assertEqual(advanced_retrieval.read_config(path), config)
                self.assertEqual(
                    advanced_lab.parser().parse_args(["setup"]).config,
                    Path("config.advanced.json"),
                )

    def test_live_guides_keep_requested_model_region_and_deployment_distinct(self):
        for relative in (
            "README.md", "README.ko.md", "docs/complete-lab.md", "docs/en/complete-lab.md",
            "docs/setup.md", "docs/reference.md", "docs/facilitator.md",
            "docs/en/setup.md", "docs/en/reference.md", "docs/en/facilitator.md",
        ):
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
        self.assertIn("complete-lab.md#results", section)
        self.assertIn("이전", section)
        current = (ROOT / "docs" / "complete-lab.md").read_text(encoding="utf-8")
        self.assertIn("Relevance", current)
        self.assertIn("100%", current)
        self.assertIn("실제 운영 승인은", current)

    def test_retention_is_the_default_and_deletion_is_explicitly_optional(self):
        main = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertLess(
            main.index('<a id="retain-resources"></a>'),
            main.index('<a id="delete-resources"></a>'),
        )
        for relative in ("README.ko.md", "docs/cleanup.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(document=relative):
                self.assertIn("별도 요청 전까지 유지", text)
                self.assertIn("보존", text)
        for relative in ("README.md", "docs/en/cleanup.md"):
            self.assertIn("retain until a separate request", (ROOT / relative).read_text(encoding="utf-8"))
        cleanup = (ROOT / "docs" / "cleanup.md").read_text(encoding="utf-8")
        self.assertIn("3–5단계는 건너뜁니다", cleanup)
        self.assertIn("리소스 보존 요청이 있는 동안 삭제하지 않습니다", cleanup)
        self.assertIn("과금 중지가 아닙니다", cleanup)

    def test_setup_shortcuts_do_not_duplicate_the_main_command_sequence(self):
        self.assertEqual(lab_commands(ROOT / "docs" / "setup.md"), [])

    def test_moved_folder_recovery_keeps_demo_separate_from_live_package_installation(self):
        for relative in ("docs/reference.md", "docs/en/reference.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            section = text.split('<a id="moved-folder"></a>')[1].split('<a id="remote-job-recovery"></a>')[0]
            live_only = re.findall(r"<details>.*?</details>", section, re.DOTALL)
            common = re.sub(r"<details>.*?</details>", "", section, flags=re.DOTALL)
            with self.subTest(guide=relative):
                self.assertEqual(len(live_only), 1)
                self.assertIn("LIVE", live_only[0])
                self.assertIn("python -m pip install -r requirements.txt", live_only[0])
                self.assertIn("DEMO", common)
                self.assertIn("deactivate", common)
                self.assertIn("setup.md#resume", common)
                self.assertIn("LOCAL OK", common)
                commands = [
                    shlex.split(line, comments=True)
                    for block in SHELL_BLOCKS.findall(common)
                    for line in block.splitlines() if line.strip()
                ]
                self.assertEqual(
                    [command for command in commands if command[0] == "python"],
                    [["python", "lab.py", "doctor"]],
                )
                self.assertFalse(any("pip" in command or command[0] == "az" for command in commands))
                self.assertNotIn("--live", common)
        for relative, link in (
            ("README.ko.md", "docs/reference.md#moved-folder"),
            ("README.md", "docs/en/reference.md#moved-folder"),
            ("docs/offline.md", "reference.md#moved-folder"),
            ("docs/en/offline.md", "reference.md#moved-folder"),
        ):
            with self.subTest(entry=relative):
                self.assertIn(f"({link})", (ROOT / relative).read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            outcome = subprocess.run(
                [sys.executable, "-S", str(ROOT / "lab.py"), "doctor"],
                cwd=directory, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(outcome.returncode, 0, outcome.stderr)
            self.assertIn("LOCAL OK", outcome.stdout)
            self.assertIn("dev 8개, holdout 4개", outcome.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [])

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
                        if argv[0] == "run":
                            folder = lab.parser().parse_args(argv).out
                            saved = (folder / "run.json").read_bytes()
                            reused = io.StringIO()
                            with redirect_stdout(reused):
                                self.assertEqual(lab.main(argv), 0)
                            signal = "기존의 완료된 결과를 읽었습니다"
                            self.assertIn(signal, reused.getvalue())
                            self.assertNotRegex(reused.getvalue(), r"\d+/\d+\s+\w+ 저장")
                            self.assertEqual((folder / "run.json").read_bytes(), saved)
                            for relative in ("README.md", "README.ko.md", "docs/offline.md", "docs/en/offline.md"):
                                self.assertIn(signal, (ROOT / relative).read_text(encoding="utf-8"))
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

from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import lab
from evaluation import (
    METRICS, ROOT, business_rate, comparison, digest, evidence_hash,
    gate, load_judge, load_run, read_cases, read_json, response_checks,
    validate_cases, validate_judge, write_json,
)
from foundry_client import clients, evaluation_items, messages_for, parse_output_items, read_config


class WorkshopTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def command(self, *args, expected=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = lab.main([str(arg) for arg in args])
        self.assertEqual(code, expected, stdout.getvalue() + stderr.getvalue())
        return stdout.getvalue() + stderr.getvalue()

    def collect(self, name, prompt="v1", *, frozen=None):
        folder = self.root / name
        args = ["run", "--mode", "demo", "--out", folder]
        args += ["--frozen", frozen, "--split", "holdout"] if frozen else ["--prompt", prompt]
        self.command(*args)
        return folder

    def judge(self, folder, like=None):
        self.command("judge", folder, *(["--like", like] if like else []))

    def review(self, folder, case_id, verdict="pass"):
        self.command("review", folder, case_id, "--verdict", verdict, "--note", "규정과 실제 답변을 비교한 교육용 테스트 기록")

    def test_full_demo_loop_is_offline_and_teaches_holdout_failure(self):
        with patch("socket.create_connection", side_effect=AssertionError("Network forbidden")):
            with patch("foundry_client.clients", side_effect=AssertionError("Azure forbidden")):
                baseline = self.collect("baseline")
                self.judge(baseline)
                candidate = self.collect("candidate", "v2")
                self.judge(candidate, baseline)
                self.command("compare", baseline, candidate)
                self.review(candidate, "D06")
                holdout = self.collect("holdout", frozen=candidate)
                self.judge(holdout, baseline)
                self.review(holdout, "H01")
                self.command("gate", baseline, candidate, holdout, expected=2)
        self.assertEqual(business_rate(load_run(baseline)), 5 / 8)
        self.assertEqual(business_rate(load_run(candidate)), 1)
        self.assertEqual(business_rate(load_run(holdout)), 3 / 4)
        result = read_json(candidate / "gate.json")
        self.assertEqual(result["status"], "BLOCK")
        self.assertEqual(result["problems"], ["holdout: 업무 통과율 75.0% < 80%"])
        self.assertIn("authored-demo", (candidate / "report.md").read_text())

    def test_average_improvement_cannot_hide_critical_regression(self):
        baseline = self.collect("baseline")
        shortcut = self.collect("shortcut", "shortcut")
        self.judge(baseline)
        self.judge(shortcut, baseline)
        self.command("compare", baseline, shortcut)
        diff = read_json(shortcut / "comparison.json")
        self.assertEqual(diff["before_rate"], 0.625)
        self.assertEqual(diff["after_rate"], 0.75)
        self.assertEqual([r["id"] for r in diff["regressions"]], ["D06"])
        self.assertEqual([r["id"] for r in diff["judge_regressions"]], ["D06"])

    def test_comparison_does_not_claim_no_judge_regressions_when_unscored(self):
        baseline = self.collect("baseline")
        candidate = self.collect("candidate", "v2")
        output = self.command("compare", baseline, candidate)
        self.assertIn("Judge 합격→불합격 회귀: 미평가", output)
        self.assertNotIn("Judge 합격→불합격 회귀: 없음", output)

    def test_completed_run_and_judge_are_not_reexecuted(self):
        folder = self.collect("baseline")
        self.judge(folder)
        before = (folder / "run.json").read_bytes()
        grade = (folder / "judge.json").read_bytes()
        self.collect("baseline")
        self.judge(folder)
        self.assertEqual(before, (folder / "run.json").read_bytes())
        self.assertEqual(grade, (folder / "judge.json").read_bytes())

    def test_judge_completion_confirms_saved_evidence_not_quality_success(self):
        folder = self.collect("baseline")
        for attempt in ("first", "cached"):
            with self.subTest(attempt=attempt):
                output = self.command("judge", folder)
                self.assertIn("평가 완료: 8개 답변 × 2개 지표 (점수·이유 저장)", output)
                self.assertIn(f"Judge 결과: {folder / 'judge.json'}", output)
                self.assertIn("D04 FAIL", output)
                judge = load_judge(folder, load_run(folder))
                self.assertLess(judge["rows"]["D04"]["groundedness"]["score"], 4)
                self.assertIn("groundedness", (folder / "report.md").read_text(encoding="utf-8"))

    def test_judge_does_not_announce_completion_when_result_saving_fails(self):
        for writer in ("write_json", "save_report"):
            with self.subTest(writer=writer):
                folder = self.collect(writer)
                with patch(f"lab.{writer}", side_effect=OSError("Result storage unavailable")):
                    output = self.command("judge", folder, expected=1)
                self.assertIn("ERROR: Result storage unavailable", output)
                self.assertNotIn("평가 완료:", output)
                self.assertNotIn("Judge 결과:", output)

    def test_partial_run_resumes_without_duplicate_rows(self):
        folder = self.collect("baseline")
        run = load_run(folder)
        run["status"] = "collecting"
        run["rows"] = run["rows"][:3]
        run.pop("evidence_hash")
        write_json(folder / "run.json", run)
        self.collect("baseline")
        rows = load_run(folder)["rows"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[:3], run["rows"])

    def test_existing_results_are_not_overwritten_by_another_prompt(self):
        folder = self.collect("baseline")
        before = (folder / "run.json").read_bytes()
        self.command("run", "--mode", "demo", "--prompt", "v2", "--out", folder, expected=1)
        self.assertEqual(before, (folder / "run.json").read_bytes())

    def test_demo_rejects_edited_prompt_and_new_cases(self):
        prompt = self.root / "custom.txt"
        prompt.write_text("새 프롬프트", encoding="utf-8")
        self.command("run", "--mode", "demo", "--prompt", prompt, "--out", self.root / "custom", expected=1)
        self.command(
            "run", "--mode", "demo", "--prompt", "v2", "--data",
            ROOT / "data" / "my-case.example.jsonl", "--out", self.root / "extra", expected=1,
        )

    def test_holdout_requires_frozen_candidate(self):
        self.command(
            "run", "--mode", "demo", "--prompt", "v2", "--split", "holdout",
            "--out", self.root / "holdout", expected=1,
        )

    def test_unknown_inspect_case_and_short_review_are_errors(self):
        folder = self.collect("baseline")
        self.command("inspect", folder, "MISSING", expected=1)
        self.command("review", folder, "D01", "--verdict", "pass", "--note", "OK", expected=1)
        self.assertFalse((folder / "reviews.json").exists())

    def test_tampered_or_incomplete_evidence_is_rejected(self):
        folder = self.collect("baseline")
        run = load_run(folder)
        run["rows"][0]["response"]["limit_krw"] = 1
        write_json(folder / "run.json", run)
        with self.assertRaisesRegex(ValueError, "변경"):
            load_run(folder)
        run["status"] = "collecting"
        write_json(folder / "run.json", run)
        with self.assertRaisesRegex(ValueError, "미완료"):
            load_run(folder)

    def test_changed_context_data_model_or_mode_cannot_be_compared(self):
        baseline = load_run(self.collect("baseline"))
        candidate = load_run(self.collect("candidate", "v2"))
        for field in ("context_hash", "cases_hash", "config", "mode"):
            with self.subTest(field=field):
                changed = copy.deepcopy(candidate)
                changed[field] = "different"
                with self.assertRaises(ValueError):
                    comparison(baseline, changed)
        candidate["rows"][0]["model"] = "different-version"
        with self.assertRaises(ValueError):
            comparison(baseline, candidate)

    def test_gate_blocks_missing_judge_and_missing_human_review(self):
        baseline = self.collect("baseline")
        candidate = self.collect("candidate", "v2")
        holdout = self.collect("holdout", frozen=candidate)
        result = gate(baseline, candidate, holdout)
        self.assertEqual(result["status"], "BLOCK")
        self.assertEqual(sum("Judge 판정 불가" in p for p in result["problems"]), 3)
        self.assertEqual(sum("검토 기록이 없습니다" in p for p in result["problems"]), 2)

    def test_gate_success_is_explicitly_only_demo_evidence(self):
        baseline = self.collect("baseline")
        candidate = self.collect("candidate", "v2")
        holdout = self.collect("holdout", frozen=candidate)
        run = load_run(holdout)
        case = run["cases"][-1]
        response = {
            "decision": case["expected_decision"], "limit_krw": case["expected_limit_krw"],
            "citations": case["expected_citations"], "answer": "실제 출장일을 알려주셔야 적용 한도를 정할 수 있습니다.",
        }
        run["rows"][-1]["response"] = response
        run["rows"][-1]["raw_response"] = json.dumps(response, ensure_ascii=False)
        run["evidence_hash"] = evidence_hash(run)
        write_json(holdout / "run.json", run)
        self.judge(baseline)
        self.judge(candidate, baseline)
        authored_judge = {
            "source": "authored-demo", "evidence_hash": run["evidence_hash"],
            "contract": load_judge(baseline, load_run(baseline))["contract"],
            "rows": {
                case["id"]: {metric: {"score": 5, "reason": "Unit-test-only authored score"} for metric in METRICS}
                for case in run["cases"]
            },
        }
        write_json(holdout / "judge.json", authored_judge)
        self.review(candidate, "D06")
        self.review(holdout, "H01")
        result = gate(baseline, candidate, holdout)
        self.assertEqual(result["problems"], [])
        self.assertEqual(result["status"], "DEMO_CRITERIA_MET")

    def test_demo_judge_rejects_modified_answers(self):
        folder = self.collect("baseline")
        run = load_run(folder)
        run["rows"][0]["response"]["answer"] = "변경된 답변"
        run["rows"][0]["raw_response"] = json.dumps(run["rows"][0]["response"], ensure_ascii=False)
        run["evidence_hash"] = evidence_hash(run)
        write_json(folder / "run.json", run)
        output = self.command("judge", folder, expected=1)
        self.assertNotIn("평가 완료:", output)

    def test_interactive_review_requires_an_actual_verdict_and_reason(self):
        folder = self.collect("baseline")
        with patch("builtins.input", side_effect=["fail", "문서에 없는 해외 한도를 만들어 내었다"]):
            self.command("review", folder, "D04")
        review = read_json(folder / "reviews.json")[-1]
        self.assertEqual(review["verdict"], "fail")

    def test_dataset_validation_rejects_duplicate_empty_and_invalid_values(self):
        original = read_cases(ROOT / "data" / "dev.jsonl")
        invalids = [[], original + [original[0]]]
        for field, value in (
            ("critical", "true"), ("expected_limit_krw", True),
            ("expected_limit_krw", -1), ("query", ""),
            ("expected_decision", "approved"), ("expected_citations", ["FAQ-DRAFT"]),
        ):
            changed = copy.deepcopy(original)
            changed[0][field] = value
            invalids.append(changed)
        for cases in invalids:
            with self.subTest(cases=cases[:1]), self.assertRaises(ValueError):
                validate_cases(cases)

    def test_validate_data_is_offline_read_only_and_reports_case_count(self):
        path = self.root / "new cases.jsonl"
        with (
            patch("socket.create_connection", side_effect=AssertionError("Network forbidden")),
            patch("foundry_client.clients", side_effect=AssertionError("Azure forbidden")),
        ):
            for name, count in (("my-case.example.jsonl", 1), ("dev.jsonl", 8)):
                with self.subTest(name=name):
                    original = (ROOT / "data" / name).read_bytes()
                    path.write_bytes(original)
                    self.assertEqual(self.command("validate-data", path), f"DATA OK: {count} case(s)\n")
                    self.assertEqual(path.read_bytes(), original)
                    self.assertEqual(list(self.root.iterdir()), [path])

    def test_validate_data_reports_invalid_or_missing_input_without_success(self):
        path = self.root / "invalid.jsonl"
        original = (ROOT / "data" / "my-case.example.jsonl").read_text(encoding="utf-8").strip() + "\n"
        invalid_case = json.loads(original)
        invalid_case["critical"] = "true"
        for text, diagnostic in (
            ("", "비어 있지 않은 JSONL"),
            ("{\n", f"{path}:1: JSON 문법 오류"),
            (original + "\n", f"{path}:2: JSONL에 빈 줄"),
            (original + original, "중복 사례 ID 또는 질문"),
            (json.dumps(invalid_case) + "\n", "critical은 true 또는 false"),
        ):
            with self.subTest(diagnostic=diagnostic):
                path.write_text(text, encoding="utf-8")
                output = self.command("validate-data", path, expected=1)
                self.assertTrue(output.startswith("ERROR:"))
                self.assertIn(diagnostic, output)
                self.assertNotIn("DATA OK", output)
                self.assertNotIn("Traceback", output)
                self.assertEqual(path.read_text(encoding="utf-8"), text)
        missing = self.root / "missing.jsonl"
        output = self.command("validate-data", missing, expected=1)
        self.assertTrue(output.startswith("ERROR:"))
        self.assertIn(str(missing), output)
        self.assertNotIn("DATA OK", output)
        self.assertFalse(missing.exists())
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_response_schema_is_strict_and_citations_are_exact(self):
        case = read_cases(ROOT / "data" / "dev.jsonl")[0]
        correct = {
            "decision": "allowed", "limit_krw": 200000,
            "citations": ["TRAVEL-CURRENT"], "answer": "180000원은 한도 200000원 이내입니다.",
        }
        self.assertTrue(all(response_checks(case, correct).values()))
        for field, value in (
            ("limit_krw", "200000"), ("limit_krw", True),
            ("decision", "approve"), ("citations", None), ("answer", ""),
        ):
            with self.subTest(field=field, value=value):
                changed = {**correct, field: value}
                self.assertFalse(response_checks(case, changed)["schema"])
        for citations in ([], ["TRAVEL-PREVIOUS"], ["TRAVEL-CURRENT", "TRAVEL-CURRENT"]):
            self.assertFalse(response_checks(case, {**correct, "citations": citations})["citations"])
        self.assertFalse(response_checks(case, {**correct, "extra": True})["schema"])

    def test_rules_alone_intentionally_cannot_understand_contradictory_prose(self):
        case = read_cases(ROOT / "data" / "dev.jsonl")[5]
        contradiction = {
            "decision": "needs_approval", "limit_krw": 200000,
            "citations": ["TRAVEL-CURRENT"], "answer": "승인 완료되었습니다. 지금 정산하세요.",
        }
        self.assertTrue(all(response_checks(case, contradiction).values()))

    def test_generator_never_receives_ground_truth_or_expected_fields(self):
        case = read_cases(ROOT / "data" / "dev.jsonl")[0]
        messages = messages_for(case["query"], "문서", "지침")
        payload = json.dumps(messages, ensure_ascii=False)
        self.assertNotIn(case["ground_truth"], payload)
        self.assertNotIn("expected_", payload)
        self.assertEqual(messages[-1]["content"], case["query"])

    def test_judge_payload_is_the_exact_saved_response_and_context(self):
        run = load_run(self.collect("baseline"))
        items = evaluation_items(run)
        for case, row, item in zip(run["cases"], run["rows"], items):
            self.assertEqual(item["response"], row["raw_response"])
            self.assertEqual(item["context"], run["context"])
            self.assertEqual(item["query"], case["query"])
            self.assertNotIn("ground_truth", item)

    def test_judge_missing_invalid_or_wrong_source_results_never_pass(self):
        folder = self.collect("baseline")
        self.judge(folder)
        run = load_run(folder)
        original = load_judge(folder, run)
        for bad_score in (None, True, float("nan"), 0, 6, "5"):
            judge = copy.deepcopy(original)
            judge["rows"]["D01"]["groundedness"]["score"] = bad_score
            with self.subTest(score=bad_score), self.assertRaises(ValueError):
                validate_judge(judge, run)
        for kind in ("missing_case", "missing_metric", "wrong_source", "empty_reason"):
            judge = copy.deepcopy(original)
            if kind == "missing_case":
                del judge["rows"]["D01"]
            elif kind == "missing_metric":
                del judge["rows"]["D01"]["groundedness"]
            elif kind == "wrong_source":
                judge["source"] = "foundry"
            else:
                judge["rows"]["D01"]["groundedness"]["reason"] = ""
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate_judge(judge, run)

    def test_remote_output_joins_by_case_id_not_row_order(self):
        run = load_run(self.collect("baseline"))
        items = evaluation_items(run)
        outputs = [
            {
                "datasource_item": item,
                "results": [{"name": metric, "score": 5, "reason": "Local test result"} for metric in METRICS],
            }
            for item in reversed(items)
        ]
        self.assertEqual(set(parse_output_items(outputs, items)), {case["id"] for case in run["cases"]})
        for invalid in (outputs[:-1], outputs + [outputs[0]]):
            with self.assertRaises(ValueError):
                parse_output_items(invalid, items)
        outputs[0]["datasource_item"] = {"id": outputs[0]["datasource_item"]["id"], "response": "altered"}
        with self.assertRaises(ValueError):
            parse_output_items(outputs, items)

    def test_config_requires_project_endpoint_and_no_placeholder(self):
        path = self.root / "config.json"
        valid = {
            "project_endpoint": "https://workshop.services.ai.azure.com/api/projects/lab",
            "model_deployment": "answer", "judge_deployment": "judge",
        }
        write_json(path, valid)
        self.assertEqual(read_config(path), valid)
        for endpoint in (
            "http://workshop.services.ai.azure.com/api/projects/lab",
            "https://example.com/api/projects/lab",
            "https://workshop.services.ai.azure.com/openai/v1",
            "https://workshop.services.ai.azure.com/api/projects/lab?token=example",
        ):
            write_json(path, {**valid, "project_endpoint": endpoint})
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                read_config(path)

    def test_saved_config_is_checked_before_authentication_or_network(self):
        config = {
            "project_endpoint": "https://example.invalid/api/projects/lab",
            "model_deployment": "answer", "judge_deployment": "judge",
        }
        with self.assertRaises(ValueError):
            with clients(config):
                self.fail("Invalid endpoint must be rejected before constructing clients")


if __name__ == "__main__":
    unittest.main()

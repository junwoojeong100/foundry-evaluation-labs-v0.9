"""Installed-SDK contract tests with an in-memory HTTP transport, never Azure."""

from __future__ import annotations

import io
import json
import re
import shlex
import tempfile
import unittest
from contextlib import contextmanager, nullcontext, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import lab
import foundry_client
from evaluation import METRICS, ROOT, evidence_hash, load_run, read_cases, read_json, validate_judge, write_json

try:
    import httpx2
    from azure.ai.projects.models import ModelDeployment
    from openai import APIError, OpenAI
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


class LocalAPI:
    def __init__(self):
        self.calls = []
        self.criteria = []
        self.jobs = {}
        self.status = "completed"
        self.creation_timeout = False
        self.completion_text = json.dumps({
            "decision": "allowed", "limit_krw": 200000,
            "citations": ["TRAVEL-CURRENT"], "answer": "한도 이내입니다.",
        }, ensure_ascii=False)
        self.finish_reason = "stop"
        self.refusal = None
        self.missing_reason = False
        self.missing_row = False

    def job(self, run_id):
        count = len(self.jobs[run_id]["data_source"]["source"]["content"])
        return {
            "id": run_id, "object": "eval.run", "created_at": 1, "eval_id": "eval-local",
            "name": "local-test", "status": self.status,
            "data_source": self.jobs[run_id]["data_source"],
            "result_counts": {"total": count, "passed": count, "failed": 0, "errored": 0},
            "per_model_usage": [], "per_testing_criteria_results": [],
            "report_url": "https://example.invalid/report",
            "error": {"code": "local_failure", "message": "Local test failure"} if self.status == "failed" else None,
        }

    def handle(self, request):
        body = json.loads(request.content) if request.content else None
        self.calls.append((request.method, request.url.path, body))
        path = request.url.path
        if path.endswith("/chat/completions"):
            return httpx2.Response(200, json={
                "id": "chat-local", "object": "chat.completion", "created": 1,
                "model": "model-local-2026",
                "choices": [{
                    "index": 0, "finish_reason": self.finish_reason,
                    "message": {"role": "assistant", "content": self.completion_text, "refusal": self.refusal},
                }],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
            })
        if request.method == "POST" and path.endswith("/evals"):
            self.criteria = body["testing_criteria"]
            return httpx2.Response(200, json={
                "id": "eval-local", "object": "eval", "created_at": 1,
                "name": body["name"], "metadata": body["metadata"],
                "data_source_config": body["data_source_config"],
                "testing_criteria": self.criteria,
            })
        if request.method == "POST" and path.endswith("/runs"):
            if self.creation_timeout:
                raise httpx2.ReadTimeout("Local simulated timeout", request=request)
            run_id = f"run-local-{len(self.jobs) + 1}"
            self.jobs[run_id] = body
            return httpx2.Response(200, json=self.job(run_id))
        if request.method == "GET" and "/output_items" in path:
            run_id = path.split("/")[-2]
            content = self.jobs[run_id]["data_source"]["source"]["content"]
            ordered = list(reversed(content))
            if self.missing_row:
                ordered = ordered[:-1]
            start = 4 if request.url.params.get("after") else 0
            records = []
            for index, entry in enumerate(ordered[start:start + 4], start):
                results = []
                for metric in METRICS:
                    result = {
                        "name": metric, "type": "azure_ai_evaluator", "score": 5,
                        "passed": True, "reason": "Local SDK contract test, not an AI judgment",
                        "threshold": 3, "label": "pass",
                    }
                    if self.missing_reason:
                        result.pop("reason")
                    results.append(result)
                records.append({
                    "id": f"item-{index}", "object": "eval.run.output_item", "created_at": 1,
                    "eval_id": "eval-local", "run_id": run_id, "status": "pass",
                    "datasource_item_id": index, "datasource_item": entry["item"],
                    "sample": {}, "results": results,
                })
            return httpx2.Response(200, json={
                "object": "list", "data": records, "has_more": start + 4 < len(ordered),
                "first_id": records[0]["id"] if records else None,
                "last_id": records[-1]["id"] if records else None,
            })
        if request.method == "GET" and "/runs/" in path:
            return httpx2.Response(200, json=self.job(path.split("/")[-1]))
        raise AssertionError(f"Unexpected local SDK request: {request.method} {path}")

    def count(self, method, suffix):
        return sum(m == method and path.endswith(suffix) for m, path, _ in self.calls)


@unittest.skipUnless(SDK_AVAILABLE, "LIVE dependencies are optional for offline tests")
class SDKContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.api = LocalAPI()
        self.config = {
            "project_endpoint": "https://workshop.services.ai.azure.com/api/projects/lab",
            "model_deployment": "answer", "judge_deployment": "judge",
        }
        self.project = SimpleNamespace(
            deployments=SimpleNamespace(get=lambda name: ModelDeployment(
                name=name, model_name="model-local", model_version="version-local",
            )),
            beta=SimpleNamespace(evaluators=SimpleNamespace(list_versions=lambda name: [
                SimpleNamespace(
                    name=name, version="1", created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    definition=SimpleNamespace(as_dict=lambda: {
                        "type": "code", "initParameters": {"deployment_name": {"type": "string"}},
                        "metrics": {"quality": {"threshold": 3}},
                    }),
                )
            ])),
        )

    @contextmanager
    def connection(self):
        with (
            patch("socket.create_connection", side_effect=AssertionError("Network forbidden")),
            httpx2.Client(transport=httpx2.MockTransport(self.api.handle)) as http_client,
            OpenAI(
                api_key="local-unit-test-not-a-secret",
                base_url="https://example.invalid/openai/v1",
                http_client=http_client, max_retries=0,
            ) as client,
            patch("foundry_client.clients", return_value=nullcontext((self.project, client))),
        ):
            yield client

    def saved_test_run(self, name="baseline"):
        folder = self.root / name
        with redirect_stdout(io.StringIO()):
            self.assertEqual(lab.main([
                "run", "--mode", "demo", "--prompt", "v1", "--out", str(folder),
            ]), 0)
        run = load_run(folder)
        run["mode"] = "live"
        run["config"] = self.config
        run["generation_contract"] = foundry_client.generation_contract()
        run["target_deployment"] = foundry_client.deployment_snapshot(self.project, "answer")
        run["evidence_hash"] = evidence_hash(run)
        return run, folder

    def test_real_sdk_deployment_attributes_are_not_wire_dictionary_keys(self):
        deployment = self.project.deployments.get("answer")
        self.assertIn("modelName", deployment.as_dict())
        snapshot = foundry_client.deployment_snapshot(self.project, "answer")
        self.assertEqual(snapshot["model_name"], "model-local")
        self.assertEqual(snapshot["model_version"], "version-local")

    def test_real_sdk_serializes_generation_schema_without_answer_leakage(self):
        with self.connection() as client:
            row = foundry_client.generate(client, self.config, "직원 질문", "고정 규정", "V1 지침")
        body = self.api.calls[0][2]
        self.assertEqual(body["model"], "answer")
        self.assertEqual(body["response_format"]["json_schema"]["strict"], True)
        self.assertEqual(body["messages"][-1], {"role": "user", "content": "직원 질문"})
        self.assertNotIn("ground_truth", json.dumps(body))
        self.assertEqual(body["max_completion_tokens"], 4096)
        self.assertEqual(row["response"]["decision"], "allowed")
        self.assertEqual(row["usage"], {"input_tokens": 20, "output_tokens": 10})
        self.assertIsNone(row["output_error"])

    def test_invalid_refused_and_truncated_outputs_are_failed_rows(self):
        for raw, finish, refusal in (
            ("not JSON", "stop", None),
            ('{"limit_krw": NaN}', "stop", None),
            (self.api.completion_text, "length", None),
            ("", "stop", "Local refusal example"),
        ):
            with self.subTest(raw=raw, finish=finish):
                self.api.completion_text, self.api.finish_reason, self.api.refusal = raw, finish, refusal
                with self.connection() as client:
                    row = foundry_client.generate(client, self.config, "question", "context", "prompt")
                self.assertIsNotNone(row["output_error"])
                json.dumps(row, allow_nan=False)

    def test_real_sdk_evaluation_body_versions_pagination_and_reason_fields(self):
        run, folder = self.saved_test_run()
        with self.connection(), redirect_stdout(io.StringIO()):
            judge = foundry_client.judge_run(run, folder, like=None, wait_seconds=0)
        validate_judge(judge, run)
        self.assertEqual(len(judge["rows"]), 8)
        self.assertEqual(self.api.count("GET", "/output_items"), 2)
        self.assertEqual(self.api.count("POST", "/evals"), 1)
        self.assertEqual(self.api.count("POST", "/runs"), 1)
        for criterion in self.api.criteria:
            self.assertEqual(criterion["type"], "azure_ai_evaluator")
            self.assertEqual(criterion["evaluator_version"], "1")
            self.assertEqual(criterion["initialization_parameters"], {"deployment_name": "judge"})
        groundedness = next(c for c in self.api.criteria if c["name"] == "groundedness")
        self.assertEqual(groundedness["data_mapping"]["context"], "{{item.context}}")
        source = self.api.jobs["run-local-1"]["data_source"]["source"]
        self.assertEqual(source["type"], "file_content")
        self.assertEqual(source["content"][0]["item"]["response"], run["rows"][0]["raw_response"])
        self.assertNotIn("ground_truth", source["content"][0]["item"])
        raw = read_json(folder / "foundry-output.json")
        self.assertEqual(raw[0]["results"][0]["threshold"], 3)
        self.assertIn("reason", raw[0]["results"][0])

    def test_pending_run_resumes_without_duplicate_submission(self):
        run, folder = self.saved_test_run()
        self.api.status = "queued"
        with self.connection(), redirect_stdout(io.StringIO()):
            self.assertIsNone(foundry_client.judge_run(run, folder, like=None, wait_seconds=0))
            self.api.status = "completed"
            judge = foundry_client.judge_run(run, folder, like=None, wait_seconds=0)
        validate_judge(judge, run)
        self.assertEqual(self.api.count("POST", "/evals"), 1)
        self.assertEqual(self.api.count("POST", "/runs"), 1)

    def test_like_reuses_same_remote_group_and_contract(self):
        first, baseline = self.saved_test_run()
        second, candidate = self.saved_test_run("candidate")
        with self.connection(), redirect_stdout(io.StringIO()):
            left = foundry_client.judge_run(first, baseline, like=None, wait_seconds=0)
            right = foundry_client.judge_run(second, candidate, like=baseline, wait_seconds=0)
        self.assertEqual(left["contract"], right["contract"])
        self.assertEqual(left["eval_id"], right["eval_id"])
        self.assertNotEqual(left["run_id"], right["run_id"])
        self.assertEqual(self.api.count("POST", "/evals"), 1)
        self.assertEqual(self.api.count("POST", "/runs"), 2)

    def test_missing_remote_rows_or_reasons_cannot_be_valid_evaluation(self):
        for missing in ("missing_row", "missing_reason"):
            with self.subTest(missing=missing):
                self.api = LocalAPI()
                setattr(self.api, missing, True)
                run, folder = self.saved_test_run(missing)
                with self.connection(), redirect_stdout(io.StringIO()):
                    with self.assertRaises(ValueError):
                        judge = foundry_client.judge_run(run, folder, like=None, wait_seconds=0)
                        validate_judge(judge, run)
                self.assertTrue((folder / "foundry-output.json").exists())

    def test_failed_remote_run_remains_an_error_and_preserves_ids(self):
        run, folder = self.saved_test_run()
        self.api.status = "failed"
        with self.connection(), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "failed"):
                foundry_client.judge_run(run, folder, like=None, wait_seconds=0)
        state = read_json(folder / "foundry-job.json")
        self.assertEqual(state["run_id"], "run-local-1")
        self.assertEqual(state["phase"], "failed")

    def test_unknown_submission_outcome_is_not_silently_retried(self):
        run, folder = self.saved_test_run()
        self.api.creation_timeout = True
        with self.connection(), redirect_stdout(io.StringIO()):
            with self.assertRaises(APIError):
                foundry_client.judge_run(run, folder, like=None, wait_seconds=0)
            with self.assertRaisesRegex(RuntimeError, "불명확"):
                foundry_client.judge_run(run, folder, like=None, wait_seconds=0)
        self.assertEqual(self.api.count("POST", "/runs"), 1)
        self.assertEqual(read_json(folder / "foundry-job.json")["phase"], "creating-run")

    def test_live_cli_wires_generation_evaluation_comparison_and_frozen_holdout(self):
        config_file = self.root / "config.json"
        write_json(config_file, self.config)
        baseline, candidate, holdout = [self.root / name for name in ("baseline", "candidate", "holdout")]
        commands = [
            ["doctor", "--live", "--config", config_file],
            ["run", "--mode", "live", "--prompt", "v1", "--config", config_file, "--out", baseline],
            ["judge", baseline, "--wait-seconds", "0"],
            ["run", "--mode", "live", "--prompt", "v2", "--config", config_file, "--out", candidate],
            ["judge", candidate, "--like", baseline, "--wait-seconds", "0"],
            ["compare", baseline, candidate],
            ["run", "--mode", "live", "--frozen", candidate, "--split", "holdout", "--out", holdout],
            ["judge", holdout, "--like", baseline, "--wait-seconds", "0"],
            ["inspect", holdout, "H04"],
        ]
        with self.connection(), redirect_stdout(io.StringIO()):
            for command in commands:
                with self.subTest(command=command):
                    self.assertEqual(lab.main([str(arg) for arg in command]), 0)
            self.assertEqual(lab.main(["gate", str(baseline), str(candidate), str(holdout)]), 2)
        self.assertEqual(self.api.count("POST", "/chat/completions"), 20)
        self.assertEqual(self.api.count("POST", "/evals"), 1)
        self.assertEqual(self.api.count("POST", "/runs"), 3)
        for folder, count in ((baseline, 8), (candidate, 8), (holdout, 4)):
            run = load_run(folder)
            self.assertEqual(len(run["rows"]), count)
            self.assertEqual(run["mode"], "live")
            self.assertEqual(run["target_deployment"]["model_version"], "version-local")
            self.assertEqual(len(read_json(folder / "judge.json")["rows"]), count)
        self.assertEqual(load_run(holdout)["frozen_from"], load_run(candidate)["evidence_hash"])

    def test_main_guide_alone_executes_end_to_end_with_local_transport(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        config = read_json(ROOT / "config.example.json")
        config["project_endpoint"] = self.config["project_endpoint"]
        config_file = self.root / "config.json"
        write_json(config_file, config)
        prompt_file = self.root / "my-v2.txt"
        prompt_file.write_text((ROOT / "prompts" / "v2.txt").read_text(encoding="utf-8"), encoding="utf-8")
        case_file = self.root / "my-case.jsonl"
        examples = re.findall(r"```jsonl\n(.*?)```", text, re.DOTALL)
        self.assertEqual(len(examples), 1)
        case_file.write_text(examples[0], encoding="utf-8")
        self.assertEqual(read_cases(case_file)[0]["id"], "N02")
        input_paths = {
            "prompts/my-v2.txt": str(prompt_file),
            "data/my-case.jsonl": str(case_file),
        }
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            self.connection(),
            patch("builtins.input", side_effect=[
                "fail", "로컬 모의 응답이 사전 승인 필요 조건을 무시했다",
                "fail", "로컬 모의 응답이 출장일을 확인하지 않았다",
            ]),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            for block in re.findall(r"```(?:bash|powershell)\n(.*?)```", text, re.DOTALL):
                for line in block.splitlines():
                    if not line.startswith("python lab.py "):
                        continue
                    argv = [
                        str(self.root / arg) if arg.startswith("results/") else input_paths.get(arg, arg)
                        for arg in shlex.split(line)[2:]
                    ]
                    if argv[0] in ("doctor", "run"):
                        argv += ["--config", str(config_file)]
                    if argv[0] == "judge":
                        argv += ["--wait-seconds", "0"]
                    with self.subTest(command=line):
                        self.assertEqual(
                            lab.main(argv), 2 if argv[0] == "gate" else 0,
                            stdout.getvalue() + stderr.getvalue(),
                        )
        self.assertEqual(self.api.count("POST", "/chat/completions"), 22)
        self.assertEqual(self.api.count("POST", "/evals"), 2)
        self.assertEqual(self.api.count("POST", "/runs"), 5)
        evaluated_rows = sum(len(job["data_source"]["source"]["content"]) for job in self.api.jobs.values())
        self.assertEqual(evaluated_rows * len(METRICS), 44)
        self.assertIn(
            f"응답 {evaluated_rows}개, 평가 항목 {evaluated_rows * len(METRICS)}개",
            text,
        )
        for name, count in (("setup-smoke", 1), ("baseline", 8), ("candidate", 8), ("holdout", 4), ("my-case", 1)):
            folder = self.root / "results" / name
            with self.subTest(result=name):
                self.assertEqual(len(load_run(folder)["rows"]), count)
                self.assertEqual(len(read_json(folder / "judge.json")["rows"]), count)
                self.assertTrue((folder / "report.md").is_file())
        candidate = self.root / "results" / "candidate"
        holdout = self.root / "results" / "holdout"
        self.assertEqual(load_run(holdout)["frozen_from"], load_run(candidate)["evidence_hash"])
        self.assertTrue((candidate / "comparison.md").is_file())
        self.assertEqual(read_json(candidate / "gate.json")["status"], "BLOCK")
        self.assertEqual(read_json(holdout / "reviews.json")[0]["verdict"], "fail")


if __name__ == "__main__":
    unittest.main()

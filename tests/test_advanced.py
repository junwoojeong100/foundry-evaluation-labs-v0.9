from __future__ import annotations

import copy
import io
import json
import math
import re
import shlex
import tempfile
import unittest
from contextlib import contextmanager, nullcontext, redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import advanced_evaluation as grading
import advanced_lab
import advanced_retrieval as retrieval
from evaluation import METRICS, ROOT, digest, read_cases, read_json, response_checks, write_json
from rag_client import read_documents
from foundry_client import messages_for


CONFIG = {
    "search_endpoint": "https://example.search.windows.net",
    "index_name": "travel-vector-index", "knowledge_source": "travel-vector-ks",
    "knowledge_base": "travel-planned-kb", "top_k": 4,
    "model_resource_endpoint": "https://example.openai.azure.com",
    "embedding_deployment": "rag-embedding", "embedding_model": "text-embedding-3-small",
    "embedding_dimensions": 1536, "planner_deployment": "rag-planner",
    "planner_model": "gpt-5.4-mini", "retrieval_reasoning_effort": "low",
}
FOUNDRY_CONFIG = {
    "project_endpoint": "https://example.services.ai.azure.com/api/projects/test",
    "model_deployment": "eval-model", "judge_deployment": "eval-model",
}
MODELS = {"embedding": {"model_version": "1"}, "planner": {"model_version": "2026-03-17"}, "dimensions": 1536}


class AdvancedTests(unittest.TestCase):
    def save_generation(self, folder, run):
        run["evidence_hash"] = advanced_lab.without_hash(run)
        write_json(folder / "generation.json", run)

    @contextmanager
    def freeze_inputs(self):
        fixture = advanced_lab.baseline()
        documents = read_documents(ROOT / "optional-rag/documents.jsonl")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data, results = root / "data", root / "results"
            data.mkdir()
            for name in ("instructions.v1.txt", "instructions.v2.txt", "dev-followups.json", "acceptance.json"):
                (data / name).write_text((ROOT / "advanced-rag" / name).read_text(encoding="utf-8"), encoding="utf-8")
            prompt = (data / "instructions.v2.txt").read_text(encoding="utf-8")
            contract = {
                "cases_hash": digest(fixture["cases"]), "labels_hash": digest(fixture["retrieval_labels"]),
                "prompt_hash": digest(prompt), "retrieval_config": CONFIG,
                "retrieval_models": MODELS, "corpus_hash": digest(documents),
                "generation_contract": fixture["generation_contract"], "model_config": FOUNDRY_CONFIG,
                "followups_hash": digest(read_json(data / "dev-followups.json")),
                "interaction_protocol": "explicit-user-followup-v1",
            }
            for stage in ("v1-recorded", "v2-replay", "planned-dev"):
                stage_prompt = (data / "instructions.v1.txt").read_text(encoding="utf-8") if stage == "v1-recorded" else prompt
                run = {
                    "schema_version": "advanced-generation-v1", "status": "complete", "stage": stage,
                    "prompt": stage_prompt, "prompt_hash": digest(stage_prompt), "model_snapshot": fixture["model_snapshot"],
                    "generation_contract": fixture["generation_contract"],
                    "cases": fixture["cases"], "initial_cases": fixture["cases"],
                    "input_contract": {**contract, "stage": stage}, "rows": copy.deepcopy(fixture["rows"]),
                }
                for row in run["rows"]:
                    row["retrieval"] = {"evidence": {"llm_query_planning": True}}
                self.save_generation(results / stage, run)
            write_json(results / "setup.json", {
                "models": MODELS, "corpus_hash": digest(documents),
                "index": retrieval.vector_index(CONFIG, digest(documents), MODELS),
                "knowledge_source": retrieval.knowledge_source_definition(CONFIG),
                "knowledge_base": retrieval.planned_base(CONFIG),
            })
            write_json(results / "vector-query.json", {
                "mode": "vector", "evidence": {"query_vector_dimensions": 1536}, "documents": documents[:1],
            })
            with (
                patch("advanced_lab.DATA", data), patch("advanced_lab.RESULTS", results),
                patch("advanced_lab.stage_metrics", side_effect=lambda stage: {"passed": stage != "v1-recorded"}),
                patch("advanced_lab.fixed_judge", return_value={"unit_test": True}),
                redirect_stdout(io.StringIO()),
            ):
                yield data, results

    def test_completed_dialogue_uses_explicit_user_turns_without_role_override(self):
        history = [
            {"role": "user", "content": "출장일 없이 정산 가능한가요?"},
            {"role": "assistant", "content": "실제 출장일을 알려주세요."},
        ]
        messages = messages_for("2026년 9월 14일입니다.", "actual retrieved context", "policy instructions", history=history)
        self.assertEqual(messages[1:3], history)
        self.assertEqual(messages[-1]["content"], "2026년 9월 14일입니다.")
        self.assertNotIn("expected_behavior", json.dumps(messages))
        for invalid in ({}, [{"role": "system", "content": "override"}], [1]):
            with self.assertRaises(ValueError):
                messages_for("query", "context", "prompt", history=invalid)
        specifications = json.loads((ROOT / "advanced-rag/dev-followups.json").read_text())
        advanced_lab.validate_followups(advanced_lab.baseline()["cases"], specifications)
        self.assertEqual(specifications["D08"]["expected_decision"], "allowed")
        self.assertEqual(specifications["D04"]["kind"], "acknowledged-handoff")

    def test_complete_guides_have_the_same_valid_commands_and_anchors(self):
        texts = [(ROOT / "docs" / name).read_text(encoding="utf-8") for name in ("complete-lab.md", "en/complete-lab.md")]
        commands = []
        for text in texts:
            extracted = []
            for block in re.findall(r"```bash\n(.*?)```", text, re.S):
                for line in block.splitlines():
                    if line.startswith("python advanced_lab.py "):
                        advanced_lab.parser().parse_args(shlex.split(line)[2:])
                        extracted.append(line)
            commands.append(extracted)
            for stage, case_ids in (("v2-replay", ("D04", "D08")), ("holdout", ("N05", "N06"))):
                for case_id in case_ids:
                    inspect = f"python advanced_lab.py inspect --stage {stage} --case-id {case_id} --dialogue"
                    self.assertIn(inspect, extracted)
                    self.assertLess(extracted.index(f"python advanced_lab.py judge --stage {stage}"), extracted.index(inspect))
            self.assertLess(
                extracted.index("python advanced_lab.py judge --stage planned-dev"),
                extracted.index("python advanced_lab.py freeze"),
            )
            self.assertLess(
                extracted.index("python advanced_lab.py freeze"),
                extracted.index("python advanced_lab.py create-holdout"),
            )
        self.assertEqual(commands[0], commands[1])
        self.assertGreater(len(commands[0]), 10)
        self.assertEqual(
            set(re.findall(r'<a id="([^"]+)"></a>', texts[0])),
            set(re.findall(r'<a id="([^"]+)"></a>', texts[1])),
        )

    def test_v1_is_a_real_recorded_failure_not_an_authored_bad_answer(self):
        fixture = advanced_lab.baseline()
        self.assertEqual(fixture["source"], "recorded-live")
        self.assertEqual(fixture["prompt_hash"], digest((ROOT / "advanced-rag/instructions.v1.txt").read_text()))
        self.assertEqual(len(fixture["rows"]), 4)
        rows = {row["case_id"]: row for row in fixture["rows"]}
        passed = [
            all(response_checks(case, rows[case["id"]]["response"]).values())
            for case in fixture["cases"]
        ]
        self.assertEqual(sum(passed), 3)
        self.assertEqual(rows["D02"]["response"]["citations"], ["TRAVEL-CURRENT", "SCOPE"])
        self.assertNotIn("project_endpoint", json.dumps(fixture))

    def test_documented_workload_counts_include_initial_turns_and_calibration(self):
        with self.freeze_inputs() as (data, _):
            self.assertEqual(advanced_lab.freeze_command(None), 0)
            self.assertEqual(advanced_lab.main(["create-holdout", "--seed", "42"]), 0)
            smoke_count = len(read_cases(ROOT / "data/my-case.example.jsonl"))
            dev_count = len(advanced_lab.baseline()["cases"])
            dev_followups = len(read_json(data / "dev-followups.json"))
            holdout_count = len(read_cases(advanced_lab.holdout_paths()[0]))
            holdout_followups = len(read_json(advanced_lab.followup_path("holdout")))
            controls, _ = grading.calibration_cases()
            workload = {
                "setup-smoke": (smoke_count, smoke_count * len(METRICS)),
                "calibration": (0, len(controls)),
                "v1-recorded": (0, dev_count * len(grading.METRICS)),
                "v2-replay": (dev_count + dev_followups, dev_count * len(grading.METRICS)),
                "planned-dev": (dev_count + dev_followups, dev_count * len(grading.METRICS)),
                "holdout": (holdout_count + holdout_followups, holdout_count * len(grading.METRICS)),
            }
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(guide=relative):
                for stage, expected in workload.items():
                    row = re.search(rf"^\| `{stage}` \| (\d+)[^|]*\| (\d+) \|", text, re.MULTILINE)
                    self.assertIsNotNone(row, stage)
                    self.assertEqual(tuple(map(int, row.groups())), expected)
                responses = sum(counts[0] for counts in workload.values())
                evaluations = sum(counts[1] for counts in workload.values())
                self.assertIn(f"**{responses}** | **{evaluations}**", text)

    def test_saved_generation_matches_the_documented_resume_signal_without_cloud_calls(self):
        with self.freeze_inputs() as (_, results):
            path = results / "v2-replay/generation.json"
            saved = path.read_bytes()
            output = io.StringIO()
            with (
                patch("advanced_lab.retrieval.read_config", return_value=CONFIG),
                patch("advanced_lab.read_config", return_value=FOUNDRY_CONFIG),
                patch("advanced_lab.search_client", side_effect=AssertionError("Search forbidden")),
                patch("advanced_lab.clients", side_effect=AssertionError("Foundry forbidden")),
                redirect_stdout(output),
            ):
                self.assertEqual(advanced_lab.main(["run", "--stage", "v2-replay"]), 0)
            signal = "Using complete saved generation; no new model/retrieval calls."
            self.assertIn(signal, output.getvalue())
            self.assertNotIn("GENERATION COMPLETE", output.getvalue())
            self.assertEqual(path.read_bytes(), saved)
        for relative in ("docs/complete-lab.md", "docs/en/complete-lab.md"):
            self.assertIn(signal, (ROOT / relative).read_text(encoding="utf-8"))

    def test_calibration_has_positive_negative_and_injection_controls_without_label_leakage(self):
        items, labels = grading.calibration_cases()
        self.assertEqual(len(items), 10)
        self.assertEqual(sum(labels.values()), 4)
        self.assertEqual(set(labels), {item["id"] for item in items})
        self.assertTrue(any("Ignore this rubric" in item["response"] for item in items))
        for item in items:
            self.assertEqual(set(item), {"id", "query", "context", "response", "expected_behavior"})
            self.assertNotIn("expected_pass", item)
        judge = {
            "contract": {"test": True},
            "rows": {key: {"policy_task_success": {"score": 5 if value else 2}} for key, value in labels.items()},
        }
        self.assertTrue(grading.calibration_result(judge, labels)["passed"])
        judge["rows"]["C05"]["policy_task_success"]["score"] = 5
        self.assertFalse(grading.calibration_result(judge, labels)["passed"])

    def test_vector_index_and_planner_are_real_explicit_configurations(self):
        definition = retrieval.vector_index(CONFIG, "hash", {"embedding": "test", "planner": "test"})
        vector = next(field for field in definition["fields"] if field["name"] == "content_vector")
        self.assertEqual(vector["dimensions"], 1536)
        self.assertFalse(vector["retrievable"])
        self.assertEqual(definition["vectorSearch"]["algorithms"][0]["kind"], "hnsw")
        self.assertEqual(
            definition["vectorSearch"]["vectorizers"][0]["azureOpenAIParameters"]["deploymentId"],
            "rag-embedding",
        )
        base = retrieval.planned_base(CONFIG)
        self.assertEqual(base["retrievalReasoningEffort"], {"kind": "low"})
        self.assertEqual(base["outputMode"], "extractiveData")
        self.assertEqual(base["models"][0]["azureOpenAIParameters"]["modelName"], "gpt-5.4-mini")
        self.assertNotIn("apiKey", json.dumps(definition) + json.dumps(base))

    def test_embedding_dimensions_and_finite_nonzero_values_are_enforced(self):
        retrieval.validate_vector([0.1] * 1536, 1536)
        for vector in ([0.1], [0.0] * 1536, [math.nan] * 1536, [True] * 1536):
            with self.subTest(length=len(vector)), self.assertRaises(ValueError):
                retrieval.validate_vector(vector, 1536)

    def test_planned_retrieval_requires_model_planning_activity(self):
        corpus = read_documents(ROOT / "optional-rag/documents.jsonl")
        corpus_hash = digest(corpus)
        document = {**corpus[0], "corpus_hash": corpus_hash}
        raw = {
            "activity": [{"type": "searchIndex", "searchIndexArguments": {"search": "planned query"}}],
            "references": [{
                "type": "searchIndex", "id": "0", "docKey": document["id"],
                "sourceData": document, "rerankerScore": 3.5,
            }],
        }
        calls = []
        search = SimpleNamespace(request=lambda method, path, body: calls.append(body) or raw)
        with self.assertRaisesRegex(RuntimeError, "query-planning"):
            retrieval.retrieve(search, None, CONFIG, "question", corpus_hash, mode="planned")
        raw["activity"].insert(0, {"type": "modelQueryPlanning", "inputTokens": 10})
        result = retrieval.retrieve(search, None, CONFIG, "question", corpus_hash, mode="planned")
        self.assertTrue(result["evidence"]["llm_query_planning"])
        self.assertEqual(calls[-1]["messages"][0]["content"][0]["text"], "question")
        self.assertNotIn("intents", calls[-1])

    def test_vector_only_request_does_not_silently_turn_into_text_search(self):
        corpus = read_documents(ROOT / "optional-rag/documents.jsonl")
        corpus_hash = digest(corpus)
        document = {**corpus[0], "corpus_hash": corpus_hash}
        calls = []
        search = SimpleNamespace(request=lambda method, path, body: calls.append(body) or {"value": [document]})
        with patch("advanced_retrieval.embed", return_value=[[0.1] * 1536]):
            result = retrieval.retrieve(search, None, CONFIG, "question", corpus_hash, mode="vector")
        self.assertNotIn("search", calls[0])
        self.assertEqual(calls[0]["vectorQueries"][0]["fields"], "content_vector")
        self.assertEqual(result["evidence"]["query_vector_dimensions"], 1536)

    def test_frozen_definition_hashes_ignore_only_odata_metadata(self):
        original = {
            "index": {"name": "index", "fields": [], "@odata.etag": "old"},
            "knowledge_source": {"name": "source"},
            "knowledge_base": {"name": "base", "models": [{"deployment": "planner"}]},
        }
        same = copy.deepcopy(original)
        same["index"]["@odata.etag"] = "new"
        self.assertEqual(retrieval.definition_hashes(original), retrieval.definition_hashes(same))
        same["knowledge_base"]["models"][0]["deployment"] = "other"
        self.assertNotEqual(retrieval.definition_hashes(original), retrieval.definition_hashes(same))

    def test_acceptance_requires_all_cases_and_builtin_relevance(self):
        contract = json.loads((ROOT / "advanced-rag/acceptance.json").read_text())
        self.assertEqual(contract["score_threshold"], 4)
        self.assertEqual(contract["pass_rate_threshold"], 1.0)
        self.assertEqual(contract["critical_failures_allowed"], 0)
        self.assertEqual(contract["minimum_fresh_holdout_cases"], 8)
        self.assertEqual(contract["required_metrics"], ["groundedness", "relevance", "policy_task_success"])
        self.assertEqual(contract["diagnostic_metrics"], [])
        self.assertEqual(contract["human_production_approval"], "separate and required")

    def test_freeze_failure_points_to_each_failed_case_without_changing_evidence(self):
        results_by_stage = {
            "v1-recorded": {"stage": "v1-recorded", "passed": False},
            "v2-replay": {
                "stage": "v2-replay", "passed": False,
                "rows": {"D02": {"passed": False}, "D03": {"passed": True}},
            },
            "planned-dev": {
                "stage": "planned-dev", "passed": False,
                "rows": {"D03": {"passed": False}, "D04": {"passed": False}, "D08": {"passed": True}},
            },
        }
        for failed_stages in (("v2-replay",), ("planned-dev",), ("v2-replay", "planned-dev")):
            with self.subTest(stages=failed_stages), self.freeze_inputs() as (_, results):
                metrics = copy.deepcopy(results_by_stage)
                for stage in ("v2-replay", "planned-dev"):
                    if stage not in failed_stages:
                        metrics[stage] = {"stage": stage, "passed": True}
                before = {path: path.read_bytes() for path in results.rglob("*") if path.is_file()}
                with (
                    patch("advanced_lab.stage_metrics", side_effect=metrics.__getitem__),
                    patch("advanced_lab.clients", side_effect=AssertionError("Azure forbidden")),
                    patch("advanced_lab.search_client", side_effect=AssertionError("Search forbidden")),
                    redirect_stderr(io.StringIO()) as errors,
                ):
                    self.assertEqual(advanced_lab.main(["freeze"]), 1)
                message = errors.getvalue()
                self.assertTrue(message.startswith("ERROR: Dev acceptance is not met."))
                for stage in ("v2-replay", "planned-dev"):
                    if stage in failed_stages:
                        self.assertIn(str(results / stage / "report.md"), message)
                    for case_id, value in results_by_stage[stage]["rows"].items():
                        command = f"python advanced_lab.py inspect --stage {stage} --case-id {case_id} --context"
                        self.assertEqual(command in message, stage in failed_stages and not value["passed"])
                self.assertIn("docs/complete-lab.md#read-case", message)
                self.assertEqual(
                    {path: path.read_bytes() for path in results.rglob("*") if path.is_file()},
                    before,
                )
                self.assertFalse((results / "frozen.json").exists())
                self.assertFalse((results / "holdout-data").exists())

    def test_inspect_compares_expected_fields_and_required_chunks_with_actual_evidence(self):
        fixture = advanced_lab.baseline()
        case = next(case for case in fixture["cases"] if case["id"] == "D02")
        for found in (True, False):
            run = copy.deepcopy(fixture)
            row = next(row for row in run["rows"] if row["case_id"] == "D02")
            if not found:
                row["documents"] = [doc for doc in row["documents"] if doc["id"] != "current-lodging"]
            metric = {
                "passed": False, "business_checks": response_checks(case, row["response"]),
                "required_chunks_found": found,
                "scores": {name: 5 for name in grading.METRICS},
            }
            before = copy.deepcopy(run)
            with (
                self.subTest(found=found),
                patch("advanced_lab.load_generation", return_value=run),
                patch("advanced_lab.stage_metrics", return_value={"rows": {"D02": metric}}),
                patch("advanced_lab.clients", side_effect=AssertionError("Azure forbidden")),
                patch("advanced_lab.search_client", side_effect=AssertionError("Search forbidden")),
                redirect_stdout(io.StringIO()) as output,
            ):
                self.assertEqual(advanced_lab.main([
                    "inspect", "--stage", "v1-recorded", "--case-id", "D02", "--context",
                ]), 0)
            text = output.getvalue()
            self.assertIn(f"Question: {case['query']}", text)
            self.assertIn('Expected decision / limit / citations: needs_approval / 200000 / ["TRAVEL-CURRENT"]', text)
            self.assertIn(f"Expected behavior: {case['ground_truth']}", text)
            self.assertIn("Actual answer:", text)
            self.assertIn('"SCOPE"', text)
            self.assertIn('"citations": false', text)
            self.assertIn("Required chunks: current-lodging", text)
            self.assertIn("Chunks: " + ", ".join(doc["id"] for doc in row["documents"]), text)
            self.assertIn(f"Required chunks found: {json.dumps(found)}", text)
            self.assertIn("Case result: FAIL", text)
            self.assertIn("not production approval", text)
            self.assertIn(row["context"], text)
            self.assertEqual(run, before)

    def test_dialogue_inspection_uses_final_expectations_without_hiding_initial_turns(self):
        run = copy.deepcopy(advanced_lab.baseline())
        initial = next(case for case in run["cases"] if case["id"] == "D08")
        followup = read_json(ROOT / "advanced-rag/dev-followups.json")["D08"]
        final = {
            **initial,
            **{key: followup[key] for key in (
                "expected_decision", "expected_limit_krw", "expected_citations", "ground_truth",
            )},
        }
        run["cases"] = [final if case["id"] == "D08" else case for case in run["cases"]]
        run["retrieval_labels"]["D08"] = followup["required_chunks"]
        row = next(row for row in run["rows"] if row["case_id"] == "D08")
        row["interaction"] = {
            "initial_case": initial, "initial_response": copy.deepcopy(row["response"]),
            "followup": followup["query"],
        }
        row["response"] = {
            "decision": "allowed", "limit_krw": 200000, "citations": ["TRAVEL-CURRENT"],
            "answer": "제공한 출장일의 한도 이내이므로 허용됩니다.",
        }
        row["documents"] = [
            document for document in read_documents(ROOT / "optional-rag/documents.jsonl")
            if document["id"] == "current-lodging"
        ]
        metric = {
            "passed": True, "required_chunks_found": True, "intermediate_safe": True,
            "scores": {name: 5 for name in grading.METRICS},
        }
        with (
            patch("advanced_lab.load_generation", return_value=run),
            patch("advanced_lab.stage_metrics", return_value={"rows": {"D08": metric}}),
            patch("advanced_lab.clients", side_effect=AssertionError("Azure forbidden")),
            redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(advanced_lab.main([
                "inspect", "--stage", "v2-replay", "--case-id", "D08", "--dialogue",
            ]), 0)
        text = output.getvalue()
        self.assertIn('Expected decision / limit / citations: allowed / 200000 / ["TRAVEL-CURRENT"]', text)
        self.assertIn(f"Expected behavior: {followup['ground_truth']}", text)
        self.assertIn("Required chunks: current-lodging", text)
        self.assertIn(f"User: {initial['query']}", text)
        self.assertIn(f"Assistant: {row['interaction']['initial_response']['answer']}", text)
        self.assertIn(f"Evaluation-user follow-up: {followup['query']}", text)
        self.assertIn(f"Final answer: {row['response']['answer']}", text)
        self.assertIn("Initial field checks (not prose evaluation): true", text)
        self.assertIn("Case result: PASS", text)
        self.assertIn("not production approval", text)

    def test_freeze_accepts_identical_candidates_and_preserves_existing_contract(self):
        with self.freeze_inputs() as (data, results):
            self.assertEqual(advanced_lab.freeze_command(None), 0)
            frozen = read_json(results / "frozen.json")
            self.assertEqual(frozen["dev_followups_hash"], digest(read_json(data / "dev-followups.json")))
            self.assertEqual(advanced_lab.freeze_command(None), 0)
            self.assertEqual(read_json(results / "frozen.json"), frozen)

    def test_freeze_rejects_mixed_v2_candidate_contracts(self):
        mutations = [
            (("prompt",), "different candidate"),
            (("prompt_hash",), digest("different candidate")),
            (("generation_contract",), {"settings": {"max_completion_tokens": 2048}}),
            (("model_snapshot", "model_version"), "different-version"),
            (("initial_cases",), []),
            (("input_contract", "followups_hash"), digest("different follow-ups")),
            (("input_contract", "model_config", "project_endpoint"), "https://other.services.ai.azure.com/api/projects/test"),
            (("input_contract", "retrieval_config", "top_k"), 3),
            (("input_contract", "interaction_protocol"), "different-protocol"),
        ]
        for keys, value in mutations:
            with self.subTest(keys=keys), self.freeze_inputs() as (_, results):
                run = read_json(results / "planned-dev/generation.json")
                target = run
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                self.save_generation(results / "planned-dev", run)
                with self.assertRaisesRegex(ValueError, "same candidate"):
                    advanced_lab.freeze_command(None)
                self.assertFalse((results / "frozen.json").exists())

    def test_freeze_rejects_candidate_files_changed_after_both_dev_runs(self):
        for name in ("instructions.v2.txt", "dev-followups.json"):
            with self.subTest(file=name), self.freeze_inputs() as (data, results):
                path = data / name
                if name.endswith(".json"):
                    followups = read_json(path)
                    followups["D04"]["query"] += " Changed."
                    write_json(path, followups)
                else:
                    path.write_text("Different candidate instructions", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "changed after dev"):
                    advanced_lab.freeze_command(None)
                self.assertFalse((results / "frozen.json").exists())

    def test_freeze_requires_recorded_baseline_model_and_generation_settings(self):
        for key in ("model_snapshot", "generation_contract"):
            with self.subTest(field=key), self.freeze_inputs() as (_, results):
                old = read_json(results / "v1-recorded/generation.json")
                old[key] = {"different": "recorded contract"}
                self.save_generation(results / "v1-recorded", old)
                with self.assertRaisesRegex(ValueError, "recorded baseline"):
                    advanced_lab.freeze_command(None)

    def test_setup_rejects_existing_object_contract_mismatches_before_embedding_or_writes(self):
        documents = read_documents(ROOT / "optional-rag/documents.jsonl")
        definitions = {
            "indexes/" + CONFIG["index_name"]: retrieval.vector_index(CONFIG, digest(documents), MODELS),
            "knowledgesources/" + CONFIG["knowledge_source"]: retrieval.knowledge_source_definition(CONFIG),
            "knowledgebases/" + CONFIG["knowledge_base"]: retrieval.planned_base(CONFIG),
        }
        mutations = [
            ("indexes/" + CONFIG["index_name"], ("vectorSearch", "vectorizers", 0, "azureOpenAIParameters", "resourceUri"), "https://other.openai.azure.com"),
            ("indexes/" + CONFIG["index_name"], ("vectorSearch", "vectorizers", 0, "azureOpenAIParameters", "deploymentId"), "other-embedding"),
            ("indexes/" + CONFIG["index_name"], ("fields", 6, "dimensions"), 1024),
            ("knowledgesources/" + CONFIG["knowledge_source"], ("searchIndexParameters", "semanticConfigurationName"), "other-semantic"),
            ("knowledgebases/" + CONFIG["knowledge_base"], ("models", 0, "azureOpenAIParameters", "resourceUri"), "https://other.openai.azure.com"),
            ("knowledgebases/" + CONFIG["knowledge_base"], ("models", 0, "azureOpenAIParameters", "deploymentId"), "other-planner"),
            ("knowledgebases/" + CONFIG["knowledge_base"], ("outputMode",), "answerSynthesis"),
        ]
        for path, keys, value in mutations:
            with self.subTest(path=path, keys=keys), tempfile.TemporaryDirectory() as temporary:
                actual = copy.deepcopy(definitions)
                target = actual[path]
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value

                def request(method, resource, *args, **kwargs):
                    self.assertEqual(method, "GET", "Mismatched shared objects must be checked before any writes.")
                    return actual[resource]

                search = SimpleNamespace(request=Mock(side_effect=request))
                with (
                    patch("advanced_retrieval.model_contract", return_value=MODELS),
                    patch("advanced_retrieval.embed", return_value=[[0.1] * 1536 for _ in documents]) as embed,
                    self.assertRaisesRegex(ValueError, "Existing .* contract"),
                ):
                    retrieval.initialize(search, None, None, CONFIG, documents, Path(temporary) / "cache.json")
                embed.assert_not_called()
                self.assertFalse((Path(temporary) / "cache.json").exists())

    def test_setup_accepts_server_defaults_without_overwriting_existing_objects(self):
        documents = read_documents(ROOT / "optional-rag/documents.jsonl")
        corpus_hash = digest(documents)
        index = retrieval.vector_index(CONFIG, corpus_hash, MODELS)
        index["@odata.etag"] = "server-etag"
        index["fields"].reverse()
        index["vectorSearch"]["profiles"][0]["compression"] = None
        parameters = index["vectorSearch"]["vectorizers"][0]["azureOpenAIParameters"]
        parameters["resourceUri"] += "/"
        parameters["apiKey"] = None
        source = retrieval.knowledge_source_definition(CONFIG)
        source["searchIndexParameters"]["sourceDataFields"].reverse()
        base = retrieval.planned_base(CONFIG)
        base["models"][0]["azureOpenAIParameters"]["apiKey"] = None
        inventory = [{**document, "corpus_hash": corpus_hash} for document in documents]
        search = SimpleNamespace(request=Mock(side_effect=[
            index, source, base, {"value": inventory}, index, {"documentCount": 7}, source, base,
        ]))
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("advanced_retrieval.model_contract", return_value=MODELS),
            patch("advanced_retrieval.embed", return_value=[[0.1] * 1536 for _ in documents]),
        ):
            result = retrieval.initialize(search, None, None, CONFIG, documents, Path(temporary) / "cache.json")
        self.assertEqual(result["document_count"], 7)
        self.assertEqual(result["knowledge_base"], base)
        self.assertFalse(any(call.args[0] == "PUT" or call.args[1].endswith("/docs/index") for call in search.request.call_args_list))

    def test_setup_creates_missing_objects_and_uploads_vectors(self):
        documents = read_documents(ROOT / "optional-rag/documents.jsonl")
        definitions, uploads = {}, []

        def request(method, path, body=None, **kwargs):
            if method == "GET":
                return {"documentCount": len(uploads)} if path.endswith("/stats") else definitions.get(path)
            if method == "PUT":
                self.assertTrue(kwargs["create_only"])
                definitions[path] = body
                return body
            if path.endswith("/docs/search"):
                return {"value": []}
            self.assertTrue(path.endswith("/docs/index"))
            uploads.extend(body["value"])
            return {"value": [{"key": item["id"], "status": True} for item in uploads]}

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("advanced_retrieval.model_contract", return_value=MODELS),
            patch("advanced_retrieval.embed", return_value=[[0.1] * 1536 for _ in documents]) as embed,
        ):
            result = retrieval.initialize(SimpleNamespace(request=request), None, None, CONFIG, documents, Path(temporary) / "cache.json")
        self.assertEqual(len(definitions), 3)
        self.assertEqual(len(uploads), 7)
        self.assertTrue(all(len(item["content_vector"]) == 1536 for item in uploads))
        self.assertEqual(result["index_stats"]["documentCount"], 7)
        embed.assert_called_once()

    def test_initial_field_checks_do_not_claim_to_validate_answer_prose(self):
        items, labels = grading.calibration_cases()
        negative = next(item for item in items if item["id"] == "C07")
        case = next(case for case in advanced_lab.baseline()["cases"] if case["id"] == "D04")
        self.assertFalse(labels["C07"])
        self.assertTrue(all(response_checks(case, json.loads(negative["response"])).values()))

    def test_initial_field_failure_is_preserved_and_not_resampled(self):
        fixture = advanced_lab.baseline()
        case = next(case for case in fixture["cases"] if case["id"] == "D04")
        response = {"decision": "allowed", "limit_krw": 200000, "citations": ["SCOPE"], "answer": "Incorrect test response."}
        generated = {"response": response, "raw_response": json.dumps(response), "output_error": None}
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)
            write_json(results / "setup.json", {"models": MODELS, "corpus_hash": "local-test"})
            followups = read_json(ROOT / "advanced-rag/dev-followups.json")
            write_json(results / "followups.json", {"D04": followups["D04"]})
            with (
                patch("advanced_lab.RESULTS", results),
                patch("advanced_lab.fixed_judge", return_value={}),
                patch("advanced_lab.retrieval.read_config", return_value=CONFIG),
                patch("advanced_lab.read_config", return_value=FOUNDRY_CONFIG),
                patch("advanced_lab.stage_inputs", return_value=([case], {"D04": ["scope-overseas"]}, "Test instructions")),
                patch("advanced_lab.followup_path", return_value=results / "followups.json"),
                patch("advanced_lab.search_client", side_effect=lambda *a, **k: nullcontext(None)),
                patch("advanced_lab.clients", side_effect=lambda *a, **k: nullcontext((None, None))),
                patch("advanced_lab.deployment_snapshot", return_value=fixture["model_snapshot"]),
                patch("advanced_lab.retrieval.model_contract", return_value=MODELS),
                patch("advanced_lab.generate", return_value=generated) as generate,
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors,
            ):
                for _ in range(2):
                    self.assertEqual(advanced_lab.main(["run", "--stage", "v2-replay"]), 1)
                generate.assert_called_once()
                self.assertIn("initial clarification/handoff", errors.getvalue())
                self.assertEqual(advanced_lab.main(["judge", "--stage", "v2-replay"]), 1)
                self.assertEqual(advanced_lab.main(["inspect", "--stage", "v2-replay", "--case-id", "D04"]), 1)
            run = read_json(results / "v2-replay/generation.json")
            self.assertEqual(run["status"], "collecting")
            self.assertEqual(run["pending"]["D04"]["initial_response"], generated)
            self.assertFalse((results / "acceptance-result.json").exists())

    def test_pending_evaluation_keeps_its_advanced_correlation_id(self):
        fixed = {**FOUNDRY_CONFIG, "metrics": ["policy_task_success"]}
        items, _ = grading.calibration_cases()
        with tempfile.TemporaryDirectory() as temporary, patch("advanced_evaluation.judge_run", return_value=None):
            folder = Path(temporary)
            self.assertIsNone(grading.evaluate(FOUNDRY_CONFIG, items, fixed, folder))
            request = read_json(folder / "evaluation-request.json")
            self.assertTrue(request["run_id"])
            self.assertEqual(request["split"], "advanced")
            self.assertIsNone(grading.evaluate(FOUNDRY_CONFIG, items, fixed, folder))
            self.assertEqual(read_json(folder / "evaluation-request.json"), request)
            self.assertFalse((folder / "run.json").exists())

    def test_generation_evidence_rejects_changed_contexts(self):
        fixture = advanced_lab.baseline()
        run = {
            "schema_version": "advanced-generation-v1", "status": "complete",
            "cases": fixture["cases"], "rows": copy.deepcopy(fixture["rows"]),
        }
        run["evidence_hash"] = advanced_lab.without_hash(run)
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            write_json(folder / "generation.json", run)
            advanced_lab.load_generation(folder)
            run["rows"][0]["context"] = "Changed"
            run["evidence_hash"] = advanced_lab.without_hash(run)
            write_json(folder / "generation.json", run)
            with self.assertRaisesRegex(ValueError, "context"):
                advanced_lab.load_generation(folder)

    def test_policy_grade_contract_rejects_mismatched_deployment(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "endpoint/deployment"):
                grading.evaluate(
                    {"project_endpoint": "https://one", "judge_deployment": "one"},
                    [{"id": "x"}],
                    {"project_endpoint": "https://other", "judge_deployment": "one"},
                    Path(temporary),
                )


if __name__ == "__main__":
    unittest.main()

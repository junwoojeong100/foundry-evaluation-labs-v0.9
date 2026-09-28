from __future__ import annotations

import copy
import json
import math
import re
import shlex
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import advanced_evaluation as grading
import advanced_lab
import advanced_retrieval as retrieval
from evaluation import ROOT, digest, response_checks, write_json
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


class AdvancedTests(unittest.TestCase):
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

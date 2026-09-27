from __future__ import annotations

import copy
import io
import json
import re
import shlex
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import rag_lab
import lab
from evaluation import (
    BUSINESS_VERSION, METRICS, comparable, digest, evidence_hash, load_run,
    response_context, write_json,
)
from foundry_client import evaluation_items
from rag_client import (
    SEARCH_API_VERSION, SearchRestClient, index_definition, initialize,
    knowledge_base_definition, knowledge_source_definition, normalize_documents,
    read_rag_config, retrieve, retrieved_context, retrieval_contract,
)

try:
    from azure.core.pipeline.transport import HttpRequest
    AZURE_CORE_AVAILABLE = True
except ImportError:
    AZURE_CORE_AVAILABLE = False


CONFIG = {
    "search_endpoint": "https://example.search.windows.net",
    "index_name": "travel-rag-index", "knowledge_source": "travel-policy-ks",
    "knowledge_base": "travel-policy-kb", "top_k": 3,
}


class RagTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.documents, self.cases, self.labels = rag_lab.inputs()
        self.corpus_hash = digest(self.documents)

    def raw_result(self, mode, document_ids):
        documents = [
            {**document, "corpus_hash": self.corpus_hash}
            for key in document_ids for document in self.documents if document["id"] == key
        ]
        if mode == "search":
            return {"value": [{**document, "@search.rerankerScore": 3.5 - i / 10} for i, document in enumerate(documents)]}
        return {
            "activity": [{"type": "searchIndex", "id": 0, "searchIndexArguments": {"semanticConfigurationName": "travel-semantic"}}],
            "references": [
                {"type": "searchIndex", "id": str(i), "docKey": document["id"], "sourceData": document, "rerankerScore": 3.5 - i / 10}
                for i, document in enumerate(documents)
            ],
        }

    def saved_run(self, mode):
        run = {
            "schema_version": 1, "business_version": BUSINESS_VERSION, "status": "complete",
            "run_id": "test-" + mode, "mode": "live", "split": "dev",
            "prompt_name": "test-rag", "prompt": "test-only prompt", "prompt_hash": digest("test-only prompt"),
            "context": "", "context_hash": digest(""), "context_mode": "retrieved",
            "cases": self.cases, "cases_hash": digest(self.cases),
            "config": {"project_endpoint": "https://example.services.ai.azure.com/api/projects/test", "model_deployment": "test", "judge_deployment": "test"},
            "generation_contract": {"source": "test-only"},
            "target_deployment": {"name": "test", "model_name": "test", "model_version": "1"},
            "rag_mode": mode, "rag_config": CONFIG, "corpus_hash": self.corpus_hash,
            "search_api_version": SEARCH_API_VERSION,
            "retrieval_contract": retrieval_contract(CONFIG, self.corpus_hash),
            "retrieval_labels": self.labels, "retrieval_labels_hash": digest(self.labels),
            "rows": [], "pending_retrievals": {},
        }
        for case in self.cases:
            raw = self.raw_result(mode, self.labels[case["id"]])
            result = {
                "mode": mode, "query": case["query"], "api_version": SEARCH_API_VERSION,
                "contract": retrieval_contract(CONFIG, self.corpus_hash),
                "raw_response": raw, "latency_ms": 1,
                "documents": normalize_documents(raw, mode, self.corpus_hash, CONFIG["top_k"]),
            }
            context = retrieved_context(result)
            response = {
                "decision": case["expected_decision"], "limit_krw": case["expected_limit_krw"],
                "citations": case["expected_citations"], "answer": "Unit-test fixture, not a real model response.",
            }
            run["rows"].append({
                "case_id": case["id"], "retrieval": result,
                "retrieved_context": context, "retrieved_context_hash": digest(context),
                "response": response, "raw_response": json.dumps(response),
                "model": "test-only", "latency_ms": 1, "usage": None, "output_error": None,
            })
        run["evidence_hash"] = evidence_hash(run)
        folder = self.root / mode
        write_json(folder / "run.json", run)
        judge = {
            "source": "foundry", "evidence_hash": run["evidence_hash"],
            "contract": {"fixture": "test-only, no model invocation"},
            "rows": {
                case["id"]: {metric: {"score": 5, "reason": "Unit-test fixture only"} for metric in METRICS}
                for case in self.cases
            },
        }
        write_json(folder / "judge.json", judge)
        return folder, run

    def test_corpus_and_labels_are_separate_from_model_inputs(self):
        self.assertEqual(len(self.documents), 7)
        self.assertEqual(len(self.cases), 4)
        self.assertEqual(sum(document["approved"] for document in self.documents), 6)
        self.assertEqual(set(self.labels), {"D02", "D03", "D04", "D08"})
        definition = index_definition(CONFIG, self.corpus_hash)
        self.assertNotIn("expected_decision", json.dumps(definition))
        self.assertNotIn("ground_truth", json.dumps(definition))
        self.assertNotIn("vectorSearch", definition)
        self.assertNotIn("models", knowledge_base_definition(CONFIG))
        self.assertNotIn("retrievalReasoningEffort", knowledge_base_definition(CONFIG))
        self.assertEqual(knowledge_source_definition(CONFIG)["kind"], "searchIndex")

    def test_config_rejects_keys_wrong_hosts_and_invalid_top_k(self):
        path = self.root / "config.json"
        write_json(path, CONFIG)
        self.assertEqual(read_rag_config(path), CONFIG)
        for change in (
            {"api_key": "not-used"}, {"search_endpoint": "https://evil.invalid"},
            {"search_endpoint": "http://example.search.windows.net"},
            {"search_endpoint": True}, {"top_k": True}, {"top_k": 0},
            {"knowledge_base": "../other"},
        ):
            with self.subTest(change=change):
                write_json(path, {**CONFIG, **change})
                with self.assertRaises(ValueError):
                    read_rag_config(path)

    @unittest.skipUnless(AZURE_CORE_AVAILABLE, "Azure SDK is optional for base DEMO")
    def test_rest_requests_set_json_content_type_and_reject_partial_or_redirects(self):
        calls = []
        pipeline = SimpleNamespace(run=lambda request: (
            calls.append(request) or SimpleNamespace(http_response=SimpleNamespace(
                status_code=200, text=lambda: '{"value": []}',
            ))
        ))
        client = SearchRestClient(CONFIG["search_endpoint"], pipeline)
        client.request("POST", "indexes/test/docs/search", {"search": "question"})
        self.assertEqual(calls[0].headers["Content-Type"], "application/json")
        self.assertEqual(json.loads(calls[0].data), {"search": "question"})
        self.assertIn("api-version=2026-04-01", calls[0].url)
        for status in (206, 302, 403, 415):
            pipeline.run = lambda request: SimpleNamespace(http_response=SimpleNamespace(
                status_code=status, text=lambda: "Explicit test failure",
            ))
            with self.subTest(status=status), self.assertRaises(RuntimeError):
                client.request("POST", "knowledgebases/test/retrieve", {})

    def test_ga_query_bodies_use_intents_filters_and_reference_source_data(self):
        for mode in ("search", "iq"):
            calls = []
            raw = self.raw_result(mode, ["current-lodging"])
            client = SimpleNamespace(request=lambda method, path, body: calls.append((method, path, body)) or raw)
            result = retrieve(client, CONFIG, "a question", mode, self.corpus_hash)
            body = calls[0][2]
            serialized = json.dumps(body)
            self.assertNotIn("ground_truth", serialized)
            self.assertNotIn("expected_", serialized)
            self.assertNotIn("queryLanguage", body)
            self.assertEqual(result["documents"][0]["id"], "current-lodging")
            if mode == "iq":
                self.assertEqual(body["intents"], [{"type": "semantic", "search": "a question"}])
                self.assertGreater(body["maxOutputSizeInTokens"], 5000)
                self.assertNotIn("messages", body)
                self.assertNotIn("retrievalReasoningEffort", body)
                self.assertTrue(body["knowledgeSourceParams"][0]["includeReferenceSourceData"])
                self.assertIn("approved eq true", body["knowledgeSourceParams"][0]["filterAddOn"])
            else:
                self.assertEqual(body["queryType"], "semantic")

    def test_malformed_unapproved_wrong_corpus_and_missing_iq_sources_fail_closed(self):
        for mode in ("search", "iq"):
            raw = self.raw_result(mode, ["current-lodging"])
            document = raw["value"][0] if mode == "search" else raw["references"][0]["sourceData"]
            for field, value in (("approved", False), ("corpus_hash", "wrong")):
                changed = copy.deepcopy(raw)
                target = changed["value"][0] if mode == "search" else changed["references"][0]["sourceData"]
                target[field] = value
                with self.subTest(mode=mode, field=field), self.assertRaises(ValueError):
                    normalize_documents(changed, mode, self.corpus_hash, 3)
            self.assertTrue(document["approved"])
        with self.assertRaises(RuntimeError):
            normalize_documents({"value": []}, "search", self.corpus_hash, 3)
        with self.assertRaises(ValueError):
            normalize_documents({"references": [], "activity": []}, "iq", self.corpus_hash, 3)
        raw = self.raw_result("iq", ["current-lodging"])
        raw["references"][0]["sourceData"] = None
        with self.assertRaises(ValueError):
            normalize_documents(raw, "iq", self.corpus_hash, 3)

    def test_judge_uses_exact_per_case_retrieved_context_not_the_corpus(self):
        folder, run = self.saved_run("iq")
        loaded = rag_lab.load_rag_run(folder)
        items = evaluation_items(loaded)
        for item, row in zip(items, run["rows"]):
            self.assertEqual(item["context"], row["retrieved_context"])
            self.assertNotEqual(item["context"], run["context"])
            self.assertNotIn("expected_decision", item)
            self.assertNotIn("ground_truth", item)
        with self.assertRaises(ValueError):
            response_context({"context": "full policy"}, {"retrieved_context": "some retrieval"})
        changed = copy.deepcopy(run)
        del changed["rows"][0]["retrieved_context"]
        changed["evidence_hash"] = evidence_hash(changed)
        write_json(folder / "run.json", changed)
        with self.assertRaises(ValueError):
            load_run(folder)

    def test_tampered_retrieval_and_legacy_comparison_are_rejected(self):
        folder, run = self.saved_run("search")
        with self.assertRaisesRegex(ValueError, "RAG"):
            comparable(run, run)
        run["rows"][0]["retrieval"]["documents"][0]["content"] = "Changed evidence"
        run["evidence_hash"] = evidence_hash(run)
        write_json(folder / "run.json", run)
        with self.assertRaises(ValueError):
            rag_lab.load_rag_run(folder)

    def test_dedicated_comparison_requires_fixed_inputs_and_complete_judging(self):
        left, _ = self.saved_run("search")
        right, run = self.saved_run("iq")
        with patch("socket.create_connection", side_effect=AssertionError("Network forbidden")):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(rag_lab.main(["compare", str(left), str(right)]), 0)
        result = json.loads((right / "rag-comparison.json").read_text())
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["runs"]["iq"]["retrieval"]["mean_recall_at_k"], 1)
        self.assertTrue((right / "rag-report.md").is_file())
        run["rag_config"] = {**CONFIG, "top_k": 2}
        run["evidence_hash"] = evidence_hash(run)
        write_json(right / "run.json", run)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(rag_lab.main(["compare", str(left), str(right)]), 1)

    def test_setup_does_not_overwrite_an_unrelated_index(self):
        calls = []
        client = SimpleNamespace(request=lambda method, path, **kwargs: (
            calls.append((method, path)) or {"description": "Some other corpus"}
        ))
        with self.assertRaises(ValueError):
            initialize(client, CONFIG, self.documents)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "GET")

    def test_optional_guides_have_identical_executable_commands_and_anchors(self):
        root = Path(rag_lab.ROOT)
        documents = [
            (root / "docs" / name).read_text(encoding="utf-8")
            for name in ("optional-rag.md", "en/optional-rag.md")
        ]
        commands = []
        for text in documents:
            current = []
            for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL):
                for line in block.splitlines():
                    if line.startswith("python rag_lab.py "):
                        args = shlex.split(line)[2:]
                        rag_lab.parser().parse_args(args)
                        current.append(line)
                    elif line.startswith("python lab.py "):
                        lab.parser().parse_args(shlex.split(line)[2:])
                        current.append(line)
            commands.append(current)
        self.assertEqual(commands[0], commands[1])
        self.assertGreater(len(commands[0]), 8)
        self.assertEqual(
            set(re.findall(r'<a id="([^"]+)"></a>', documents[0])),
            set(re.findall(r'<a id="([^"]+)"></a>', documents[1])),
        )


if __name__ == "__main__":
    unittest.main()

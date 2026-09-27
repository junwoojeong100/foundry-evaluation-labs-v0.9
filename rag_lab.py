#!/usr/bin/env python3
"""Optional real Search / Foundry IQ retrieval and answer evaluation workshop."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import lab
from evaluation import (
    BUSINESS_VERSION, METRICS, ROOT, SCORE_THRESHOLD, business_rate, digest,
    evidence_hash, judge_fingerprint, judge_rate, load_judge, load_run, now,
    read_cases, read_json, report_text, response_context, scored_rows, write_json,
)
from foundry_client import clients, deployment_snapshot, generate, generation_contract, read_config
from rag_client import (
    SEARCH_API_VERSION, initialize, normalize_documents, read_documents, read_rag_config,
    retrieve, retrieved_context, retrieval_contract, search_client,
)

DATA = ROOT / "optional-rag"


def inputs() -> tuple[list[dict], list[dict], dict]:
    documents = read_documents(DATA / "documents.jsonl")
    cases = read_cases(DATA / "cases.jsonl")
    labels = read_json(DATA / "retrieval-labels.json")
    approved_ids = {document["id"] for document in documents if document["approved"]}
    if not isinstance(labels, dict) or set(labels) != {case["id"] for case in cases}:
        raise ValueError("Retrieval labels must match the evaluation case IDs.")
    for case_id, expected in labels.items():
        if (
            not isinstance(expected, list) or not expected
            or any(not isinstance(value, str) or value not in approved_ids for value in expected)
            or len(set(expected)) != len(expected)
        ):
            raise ValueError(f"{case_id}: invalid required-chunk labels.")
    return documents, cases, labels


def validate_retrieval(result: dict, run: dict, case: dict) -> None:
    if (
        result.get("mode") != run["rag_mode"] or result.get("query") != case["query"]
        or result.get("api_version") != SEARCH_API_VERSION
        or result.get("contract") != run["retrieval_contract"]
    ):
        raise ValueError("Saved retrieval no longer matches the request.")
    normalized = normalize_documents(
        result["raw_response"], run["rag_mode"], run["corpus_hash"], run["rag_config"]["top_k"],
    )
    if result["documents"] != normalized:
        raise ValueError("Saved documents differ from the original Search/IQ response.")


def load_rag_run(folder: Path, *, complete=True) -> dict:
    run = load_run(folder, complete=complete)
    if run.get("context_mode") != "retrieved" or run.get("rag_mode") not in ("search", "iq"):
        raise ValueError("This is not an optional RAG run.")
    if run["context"] != "":
        raise ValueError("RAG must not store a full-policy fallback as its generation context.")
    if run["retrieval_labels_hash"] != digest(run["retrieval_labels"]):
        raise ValueError("Retrieval ground truth changed after collection.")
    cases = {case["id"]: case for case in run["cases"]}
    for row in run["rows"]:
        validate_retrieval(row["retrieval"], run, cases[row["case_id"]])
        if response_context(run, row) != retrieved_context(row["retrieval"]):
            raise ValueError("The model context differs from the captured retrieval documents.")
    return run


def retrieval_metrics(run: dict) -> dict:
    rows = {}
    for row in run["rows"]:
        expected = set(run["retrieval_labels"][row["case_id"]])
        documents = row["retrieval"]["documents"]
        actual = {document["id"] for document in documents}
        matches = expected & actual
        response = row["response"]
        citations = response.get("citations", []) if isinstance(response, dict) else []
        rows[row["case_id"]] = {
            "required": sorted(expected), "retrieved": [document["id"] for document in documents],
            "recall_at_k": len(matches) / len(expected),
            "precision_at_k": len(matches) / len(actual) if actual else 0,
            "all_required_found": expected <= actual,
            "citation_ids_linked": (
                isinstance(citations, list) and bool(citations)
                and all(isinstance(value, str) for value in citations)
                and set(citations) <= {document["source_id"] for document in documents}
            ),
        }
    if not rows:
        raise ValueError("No collected retrieval evidence is available.")
    return {
        "version": "required-chunk-recall-v1", "top_k": run["rag_config"]["top_k"],
        "mean_recall_at_k": sum(row["recall_at_k"] for row in rows.values()) / len(rows),
        "mean_precision_at_k": sum(row["precision_at_k"] for row in rows.values()) / len(rows),
        "all_required_found_rate": sum(row["all_required_found"] for row in rows.values()) / len(rows),
        "rows": rows,
    }


def save_rag_report(folder: Path, run: dict) -> None:
    judge = load_judge(folder, run) if (folder / "judge.json").exists() else None
    metrics = retrieval_metrics(run)
    write_json(folder / "retrieval-metrics.json", metrics)
    text = report_text(run, judge)
    text += "\n## Actual retrieved evidence / 실제 검색 근거\n\n"
    text += f"Route: **{run['rag_mode']}**, API `{SEARCH_API_VERSION}`, application top-k **{metrics['top_k']}**.\n\n"
    text += "The model and Groundedness judge receive the same per-case retrieved context, not the full corpus.\n\n"
    text += "| Case | Retrieved chunk IDs | Recall@k | Precision@k | Citation IDs linked |\n|---|---|---|---|---|\n"
    for case_id, value in metrics["rows"].items():
        text += (
            f"| {case_id} | {', '.join(value['retrieved'])} | {value['recall_at_k']:.0%} "
            f"| {value['precision_at_k']:.0%} | {value['citation_ids_linked']} |\n"
        )
    for row in run["rows"]:
        text += f"\n### Retrieved context: {row['case_id']}\n\n"
        text += "```text\n" + row["retrieved_context"] + "\n```\n"
    (folder / "rag-report.md").write_text(text, encoding="utf-8")
    print(f"RAG report: {folder / 'rag-report.md'}")
    print(f"Required-chunk recall@{metrics['top_k']}: {metrics['mean_recall_at_k']:.1%}")


def setup_command(args) -> int:
    documents, cases, _ = inputs()
    config = read_rag_config(args.config)
    with search_client(config) as client:
        result = initialize(client, config, documents)
    write_json(args.out, result)
    print(f"SETUP OK: {len(documents)} chunks, {len(cases)} evaluation cases")
    print(f"Index: {config['index_name']}; Foundry IQ knowledge base: {config['knowledge_base']}")
    print(f"GA API {SEARCH_API_VERSION}: minimal extractive retrieval; no LLM query planning or vector embeddings.")
    print(f"Snapshot: {args.out}")
    return 0


def query_command(args) -> int:
    documents, _, _ = inputs()
    config = read_rag_config(args.config)
    with search_client(config) as client:
        result = retrieve(client, config, args.query, args.mode, digest(documents))
    write_json(args.out, result)
    print(f"RETRIEVAL OK: {args.mode}, {len(result['documents'])} selected chunks")
    for document in result["documents"]:
        print(f"  {document['id']} / {document['source_id']} / score={document['reranker_score']}")
    if args.mode == "iq":
        print("Foundry IQ activity:", ", ".join(item["type"] for item in result["raw_response"]["activity"]))
    print(f"Raw retrieval evidence: {args.out}")
    return 0


def run_command(args) -> int:
    documents, cases, labels = inputs()
    config = read_config(args.foundry_config)
    rag_config = read_rag_config(args.config)
    prompt = (DATA / "prompt.txt").read_text(encoding="utf-8")
    requested = {
        "schema_version": 1, "business_version": BUSINESS_VERSION,
        "run_id": uuid.uuid4().hex, "created_at": now(), "status": "collecting",
        "mode": "live", "split": "dev", "prompt_name": f"rag-{args.mode}",
        "prompt": prompt, "context": "", "context_mode": "retrieved", "cases": cases,
        "prompt_hash": digest(prompt), "context_hash": digest(""), "cases_hash": digest(cases),
        "config": config, "generation_contract": generation_contract(),
        "rag_mode": args.mode, "rag_config": rag_config, "search_api_version": SEARCH_API_VERSION,
        "retrieval_contract": retrieval_contract(rag_config, digest(documents)),
        "corpus_hash": digest(documents), "retrieval_labels": labels,
        "retrieval_labels_hash": digest(labels), "target_deployment": None,
        "rows": [], "pending_retrievals": {},
    }
    path = args.out / "run.json"
    if path.exists():
        run = load_rag_run(args.out, complete=False)
        for field in (
            "config", "rag_config", "rag_mode", "search_api_version", "corpus_hash",
            "cases_hash", "prompt_hash", "generation_contract", "retrieval_labels_hash", "retrieval_contract",
        ):
            if run[field] != requested[field]:
                raise ValueError(f"Existing {field} differs. Preserve this result and choose a new --out.")
        if run["status"] == "complete":
            run = load_rag_run(args.out)
            print("Using completed LIVE evidence; no new retrieval or generation calls.")
            save_rag_report(args.out, run)
            return 0
    else:
        if args.out.exists() and any(args.out.iterdir()):
            raise ValueError("Output directory is not empty; use a new dedicated RAG folder.")
        run = requested
        write_json(path, run)
    done = {row["case_id"] for row in run["rows"]}
    with search_client(rag_config) as search, clients(config) as (project, model):
        snapshot = deployment_snapshot(project, config["model_deployment"])
        if run["target_deployment"] is not None and run["target_deployment"] != snapshot:
            raise ValueError("The generation deployment changed; do not resume this experiment.")
        run["target_deployment"] = snapshot
        write_json(path, run)
        for case in run["cases"]:
            if case["id"] in done:
                continue
            case_id = case["id"]
            if case_id in run["pending_retrievals"]:
                result = run["pending_retrievals"][case_id]
                validate_retrieval(result, run, case)
            else:
                result = retrieve(search, rag_config, case["query"], args.mode, run["corpus_hash"])
                run["pending_retrievals"][case_id] = result
                write_json(path, run)
            context = retrieved_context(result)
            row = generate(model, config, case["query"], context, run["prompt"])
            row.update({
                "case_id": case_id, "retrieval": result,
                "retrieved_context": context, "retrieved_context_hash": digest(context),
            })
            run["rows"].append(row)
            del run["pending_retrievals"][case_id]
            write_json(path, run)
            print(f"{len(run['rows'])}/{len(cases)} {case_id} saved: {', '.join(document['id'] for document in result['documents'])}", flush=True)
    run["status"] = "complete"
    run["evidence_hash"] = evidence_hash(run)
    write_json(path, run)
    save_rag_report(args.out, run)
    print(f"LIVE RAG generation complete: {len(run['rows'])} answers; business pass rate {business_rate(run):.1%}")
    print(f"Next: python lab.py judge {args.out}")
    if args.mode == "iq":
        print("For a controlled comparison, add --like with the Search run's judged result folder.")
    return 0


def inspect_command(args) -> int:
    run = load_rag_run(args.folder)
    lab.inspect_command(args)
    row = next(row for row in run["rows"] if row["case_id"] == args.case_id)
    print("\nActual retrieved context / 실제 검색 문맥:")
    print(row["retrieved_context"])
    print("\nRetrieval metrics:", json.dumps(retrieval_metrics(run)["rows"][args.case_id], ensure_ascii=False))
    save_rag_report(args.folder, run)
    return 0


def compare_command(args) -> int:
    left, right = load_rag_run(args.search), load_rag_run(args.iq)
    if left["rag_mode"] != "search" or right["rag_mode"] != "iq":
        raise ValueError("Compare the Search run first and the Foundry IQ run second.")
    for field in (
        "config", "rag_config", "corpus_hash", "cases_hash", "prompt_hash",
        "generation_contract", "target_deployment", "retrieval_labels_hash", "search_api_version", "retrieval_contract",
    ):
        if left[field] != right[field]:
            raise ValueError(f"RAG runs differ in {field}; they are not a controlled retrieval comparison.")
    if {row["model"] for row in left["rows"]} != {row["model"] for row in right["rows"]}:
        raise ValueError("Reported generation model versions differ.")
    judges = [load_judge(folder, run) for folder, run in ((args.search, left), (args.iq, right))]
    if judge_fingerprint(judges[0]) != judge_fingerprint(judges[1]):
        raise ValueError("Judge contracts differ; use --like for the optional runs.")
    result = {"status": "REVIEW_REQUIRED", "runs": {}, "issues": [], "evidence": [left["evidence_hash"], right["evidence_hash"]]}
    for folder, run, judge in ((args.search, left, judges[0]), (args.iq, right, judges[1])):
        retrieval_result = retrieval_metrics(run)
        values = {
            "business_pass_rate": business_rate(run),
            "retrieval": retrieval_result,
            "judge_pass_rates": {metric: judge_rate(judge, metric) for metric in METRICS},
        }
        result["runs"][run["rag_mode"]] = values
        if retrieval_result["mean_recall_at_k"] < 0.8:
            result["issues"].append(f"{run['rag_mode']}: required-chunk recall below 80%")
        if values["business_pass_rate"] < 0.8:
            result["issues"].append(f"{run['rag_mode']}: business pass rate below 80%")
        for metric, rate in values["judge_pass_rates"].items():
            if rate < 0.8:
                result["issues"].append(f"{run['rag_mode']}: {metric} pass rate below 80%")
        for row in scored_rows(run):
            if row["case"]["critical"] and (
                not row["passed"] or not retrieval_result["rows"][row["case_id"]]["all_required_found"]
                or any(judge["rows"][row["case_id"]][metric]["score"] < SCORE_THRESHOLD for metric in METRICS)
            ):
                result["issues"].append(f"{run['rag_mode']}: critical case needs review: {row['case_id']}")
        save_rag_report(folder, run)
    write_json(args.iq / "rag-comparison.json", result)
    text = "# Optional RAG comparison — LIVE\n\n"
    text += "Same questions, corpus, prompt, generation deployment and judge; only the retrieval route changes.\n\n"
    text += "| Route | Required-chunk recall@k | Business pass | Groundedness ≥4 | Relevance ≥4 |\n|---|---|---|---|---|\n"
    for route, values in result["runs"].items():
        text += (
            f"| {route} | {values['retrieval']['mean_recall_at_k']:.0%} | {values['business_pass_rate']:.0%} "
            f"| {values['judge_pass_rates']['groundedness']:.0%} | {values['judge_pass_rates']['relevance']:.0%} |\n"
        )
    text += "\n**REVIEW_REQUIRED:** this small experiment is not production approval or proof one route is superior.\n\n"
    text += "\n".join("- " + issue for issue in result["issues"])
    (args.iq / "rag-comparison.md").write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"Comparison: {args.iq / 'rag-comparison.md'}")
    return 0


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optional Search / Foundry IQ RAG lab; no simulated retrieval.")
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("setup", help="Create the dedicated index, knowledge source and knowledge base")
    setup.add_argument("--config", type=Path, default=Path("config.rag.json"))
    setup.add_argument("--out", type=Path, default=Path("results/rag-setup.json"))
    setup.set_defaults(handler=setup_command)
    query = commands.add_parser("query", help="Retrieve real documents without generating an answer")
    query.add_argument("--config", type=Path, default=Path("config.rag.json"))
    query.add_argument("--mode", choices=("search", "iq"), required=True)
    query.add_argument("--query", required=True)
    query.add_argument("--out", type=Path, default=Path("results/rag-query.json"))
    query.set_defaults(handler=query_command)
    run = commands.add_parser("run", help="Retrieve and generate one answer per optional case")
    run.add_argument("--config", type=Path, default=Path("config.rag.json"))
    run.add_argument("--foundry-config", type=Path, default=Path("config.json"))
    run.add_argument("--mode", choices=("search", "iq"), required=True)
    run.add_argument("--out", type=Path, required=True)
    run.set_defaults(handler=run_command)
    inspect = commands.add_parser("inspect", help="Inspect answer, actual retrieved context and metrics")
    inspect.add_argument("folder", type=Path)
    inspect.add_argument("case_id")
    inspect.set_defaults(handler=inspect_command)
    compare = commands.add_parser("compare", help="Compare two fully judged optional RAG runs")
    compare.add_argument("search", type=Path)
    compare.add_argument("iq", type=Path)
    compare.set_defaults(handler=compare_command)
    return parser


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted; saved RAG evidence is preserved. Resume the same command.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

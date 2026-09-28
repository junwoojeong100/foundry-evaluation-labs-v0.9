#!/usr/bin/env python3
"""Failure -> calibrated improvement -> frozen planned RAG -> fresh acceptance."""

from __future__ import annotations

import argparse
import json
import random
import secrets
import sys
import uuid
from pathlib import Path

import advanced_evaluation as grading
import advanced_retrieval as retrieval
from evaluation import (
    ROOT, digest, now, read_cases, read_json, response_checks, validate_cases, write_json,
)
from foundry_client import clients, deployment_snapshot, generate, generation_contract, read_config
from rag_client import read_documents, retrieved_context, search_client

DATA = ROOT / "advanced-rag"
RESULTS = ROOT / "results" / "advanced"
FIXTURE = DATA / "fixtures" / "recorded-v1.json"


def holdout_paths() -> tuple[Path, Path, Path]:
    folder = RESULTS / "holdout-data"
    return folder / "cases.jsonl", folder / "labels.json", folder / "provenance.json"


def followup_path(stage: str) -> Path:
    return RESULTS / "holdout-data" / "followups.json" if stage == "holdout" else DATA / "dev-followups.json"


def conversation_query(history: list[dict], final_query: str) -> str:
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in history) + "\nuser: " + final_query


def validate_followups(cases: list[dict], followups: dict) -> None:
    by_id = {case["id"]: case for case in cases}
    required = {"kind", "query", "expected_decision", "expected_limit_krw", "expected_citations", "ground_truth", "required_chunks"}
    if not isinstance(followups, dict) or not set(followups) <= set(by_id):
        raise ValueError("Follow-up scenarios do not match the case set.")
    documents = read_documents(ROOT / "optional-rag" / "documents.jsonl")
    allowed = {document["id"] for document in documents if document["approved"]}
    for key, specification in followups.items():
        if not isinstance(specification, dict) or set(specification) != required:
            raise ValueError("Follow-up fields are incomplete.")
        kind = specification["kind"]
        expected_initial = {"date-clarification": "needs_info", "acknowledged-handoff": "unknown"}
        if kind not in expected_initial or by_id[key]["expected_decision"] != expected_initial[kind]:
            raise ValueError("Follow-up type does not match the initial task.")
        case = {**by_id[key], **{field: specification[field] for field in ("query", "expected_decision", "expected_limit_krw", "expected_citations", "ground_truth")}}
        validate_cases([case])
        chunks = specification["required_chunks"]
        if not isinstance(chunks, list) or not chunks or any(not isinstance(chunk, str) or chunk not in allowed for chunk in chunks):
            raise ValueError("Follow-up retrieval labels are invalid.")


def without_hash(value: dict) -> str:
    return digest({key: item for key, item in value.items() if key != "evidence_hash"})


def load_generation(folder: Path) -> dict:
    run = read_json(folder / "generation.json")
    if run.get("schema_version") != "advanced-generation-v1":
        raise ValueError("Not an advanced-generation record.")
    if run.get("status") != "complete" or run.get("evidence_hash") != without_hash(run):
        raise ValueError("Generation is incomplete or its evidence changed.")
    ids = {case["id"] for case in run["cases"]}
    if len(run["rows"]) != len(ids) or {row["case_id"] for row in run["rows"]} != ids:
        raise ValueError("Generated case IDs do not match the case set.")
    for row in run["rows"]:
        if not row["context"] or row["context_hash"] != digest(row["context"]):
            raise ValueError("A recorded context is missing or changed.")
    return run


def baseline() -> dict:
    fixture = read_json(FIXTURE)
    if fixture["source"] != "recorded-live":
        raise ValueError("The baseline must be the explicitly recorded LIVE evidence.")
    prompt = (DATA / "instructions.v1.txt").read_text(encoding="utf-8")
    if digest(prompt) != fixture["prompt_hash"]:
        raise ValueError("The preserved V1 prompt no longer matches the recorded baseline.")
    return fixture


def fixed_judge() -> dict:
    result = read_json(RESULTS / "calibration-result.json")
    if not result["passed"] or result["mismatches"]:
        raise ValueError("The policy evaluator has not passed its calibration controls.")
    fixed = read_json(RESULTS / "judge-contract.json")
    request = read_json(RESULTS / "calibration" / "evaluation-request.json")
    calibration = read_json(RESULTS / "calibration" / "judge.json")
    grading.validate(calibration, request["items"], request["contract"], request["evidence_hash"])
    labels = read_json(RESULTS / "calibration-controls.json")["expected_pass"]
    if grading.calibration_result(calibration, labels) != result:
        raise ValueError("Calibration summary no longer matches its original scores and controls.")
    if (
        fixed["policy_rubric_hash"] != request["contract"]["policy_rubric_hash"]
        or fixed["judge_model"] != request["contract"]["judge_model"]
    ):
        raise ValueError("The final judge is not the calibrated policy evaluator/model.")
    if fixed["policy_rubric_hash"] != digest((DATA / "policy-task-success.txt").read_text(encoding="utf-8")):
        raise ValueError("The policy rubric changed after calibration.")
    if fixed["acceptance_contract"] != read_json(DATA / "acceptance.json"):
        raise ValueError("Acceptance criteria changed after calibration.")
    return fixed


def setup_command(args) -> int:
    config = retrieval.read_config(args.config)
    model_config = read_config(args.foundry_config)
    documents = read_documents(ROOT / "optional-rag" / "documents.jsonl")
    with search_client(config, api_version=retrieval.API_VERSION) as search, clients(model_config) as (project, _), retrieval.embedding_client(config) as model:
        result = retrieval.initialize(
            search, project, model, config, documents, RESULTS / "embedding-cache.json",
        )
    write_json(RESULTS / "setup.json", result)
    print(f"VECTOR SETUP OK: {len(documents)} documents, {config['embedding_dimensions']} dimensions")
    print(f"IQ query planner: {config['planner_model']} / {config['retrieval_reasoning_effort']}")
    print(f"Metadata: {RESULTS / 'setup.json'}")
    return 0


def query_command(args) -> int:
    config = retrieval.read_config(args.config)
    model_config = read_config(args.foundry_config)
    setup = read_json(RESULTS / "setup.json")
    with search_client(config, api_version=retrieval.API_VERSION) as search, clients(model_config) as (project, _), retrieval.embedding_client(config) as model:
        if retrieval.model_contract(project, config) != setup["models"]:
            raise ValueError("Retrieval model versions changed after setup.")
        result = retrieval.retrieve(search, model, config, args.query, setup["corpus_hash"], mode=args.mode)
    write_json(args.out, result)
    print(f"RETRIEVAL OK: {args.mode}, {len(result['documents'])} chunks")
    print(json.dumps(result["evidence"], ensure_ascii=False, indent=2))
    print("Chunks:", ", ".join(document["id"] for document in result["documents"]))
    print(f"Original response: {args.out}")
    return 0


def calibrate_command(args) -> int:
    config = read_config(args.foundry_config)
    registration = grading.register(config, RESULTS / "evaluator.json")
    calibration_contract = grading.contract(config, registration, calibration=True)
    items, labels = grading.calibration_cases()
    write_json(RESULTS / "calibration-controls.json", {"items": items, "expected_pass": labels})
    judge = grading.evaluate(
        config, items, calibration_contract, RESULTS / "calibration", wait_seconds=args.wait_seconds,
    )
    if judge is None:
        return 3
    result = grading.calibration_result(judge, labels)
    write_json(RESULTS / "calibration-result.json", result)
    if not result["passed"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    path = RESULTS / "judge-contract.json"
    if path.exists():
        fixed = read_json(path)
        if fixed["policy_rubric_hash"] != registration["prompt_hash"]:
            raise ValueError("A different judge contract already exists; start a new experiment.")
    else:
        write_json(path, grading.contract(config, registration))
    print(f"CALIBRATION PASSED: {result['controls']} controls; positives and negatives all classified correctly.")
    return 0


def import_baseline_command(args) -> int:
    fixture = baseline()
    run = {
        "schema_version": "advanced-generation-v1", "stage": "v1-recorded",
        "source": "recorded-live", "created_at": fixture["captured_at"], "status": "complete",
        "prompt": (DATA / "instructions.v1.txt").read_text(encoding="utf-8"),
        "prompt_hash": fixture["prompt_hash"], "model_snapshot": fixture["model_snapshot"],
        "generation_contract": fixture["generation_contract"], "cases": fixture["cases"],
        "retrieval_labels": fixture["retrieval_labels"], "rows": fixture["rows"],
        "original_run_evidence_hash": fixture["original_run_evidence_hash"],
    }
    run["evidence_hash"] = without_hash(run)
    path = RESULTS / "v1-recorded" / "generation.json"
    if path.exists() and read_json(path) != run:
        raise ValueError("The existing historical baseline differs; do not overwrite it.")
    write_json(path, run)
    print("Imported four genuine recorded V1 answers. No new generation is claimed.")
    return 0


def stage_inputs(stage: str, config: dict):
    fixture = baseline()
    if stage == "holdout":
        frozen = read_json(RESULTS / "frozen.json")
        if frozen["evidence_hash"] != without_hash(frozen):
            raise ValueError("The frozen experiment contract changed.")
        if frozen["retrieval_config"] != config:
            raise ValueError("Retrieval settings changed after freeze.")
        if frozen["judge_contract"] != fixed_judge():
            raise ValueError("Judge contract changed after freeze.")
        if frozen["generation_contract"] != generation_contract():
            raise ValueError("Generation settings changed after freeze.")
        if digest(read_documents(ROOT / "optional-rag" / "documents.jsonl")) != frozen["corpus_hash"]:
            raise ValueError("The source corpus changed after freeze.")
        prompt = frozen["prompt"]
        if digest((DATA / "instructions.v2.txt").read_text(encoding="utf-8")) != frozen["prompt_hash"]:
            raise ValueError("The V2 prompt changed after freeze.")
        metadata = read_json(RESULTS / "holdout-registration.json")
        if metadata["frozen_hash"] != frozen["evidence_hash"]:
            raise ValueError("Holdout was not registered against this frozen experiment.")
        case_path, label_path, _ = holdout_paths()
        cases = read_cases(case_path)
        labels = read_json(label_path)
        if metadata["cases_hash"] != digest(cases) or metadata["labels_hash"] != digest(labels):
            raise ValueError("Holdout changed after registration.")
        if metadata["followups_hash"] != digest(read_json(followup_path("holdout"))):
            raise ValueError("The scripted user follow-ups changed after registration.")
        if frozen["dev_followups_hash"] != digest(read_json(DATA / "dev-followups.json")):
            raise ValueError("The development interaction protocol changed after freeze.")
        return cases, labels, prompt
    return fixture["cases"], fixture["retrieval_labels"], (DATA / "instructions.v2.txt").read_text(encoding="utf-8")


def run_command(args) -> int:
    fixed_judge()
    config = retrieval.read_config(args.config)
    model_config = read_config(args.foundry_config)
    setup = read_json(RESULTS / "setup.json")
    cases, labels, prompt = stage_inputs(args.stage, config)
    followups = read_json(followup_path(args.stage))
    validate_followups(cases, followups)
    folder = RESULTS / args.stage
    path = folder / "generation.json"
    input_contract = {
        "stage": args.stage, "cases_hash": digest(cases), "labels_hash": digest(labels),
        "prompt_hash": digest(prompt), "retrieval_config": config,
        "retrieval_models": setup["models"], "corpus_hash": setup["corpus_hash"],
        "generation_contract": generation_contract(), "model_config": model_config,
        "followups_hash": digest(followups), "interaction_protocol": "explicit-user-followup-v1",
    }
    if path.exists():
        run = read_json(path)
        if run["input_contract"] != input_contract:
            raise ValueError("Inputs changed; preserve the old stage and create a new experiment.")
        if run["status"] == "complete":
            load_generation(folder)
            print("Using complete saved generation; no new model/retrieval calls.")
            return 0
    else:
        run = {
            "schema_version": "advanced-generation-v1", "stage": args.stage,
            "source": "live", "created_at": now(), "status": "collecting",
            "prompt": prompt, "prompt_hash": digest(prompt), "input_contract": input_contract,
            "generation_contract": generation_contract(), "cases": json.loads(json.dumps(cases)),
            "initial_cases": cases, "retrieval_labels": dict(labels),
            "rows": [], "pending": {}, "model_snapshot": None,
        }
        write_json(path, run)
    saved = {row["case_id"] for row in run["rows"]}
    historical = {row["case_id"]: row for row in baseline()["rows"]}
    with search_client(config, api_version=retrieval.API_VERSION) as search, clients(model_config) as (project, model):
        if args.stage == "holdout":
            frozen = read_json(RESULTS / "frozen.json")
            if setup["models"] != frozen["retrieval_models"] or setup["corpus_hash"] != frozen["corpus_hash"]:
                raise ValueError("Retrieval models/corpus changed after freeze.")
            retrieval.verify_definitions(search, config, frozen["search_definition_hashes"])
        model_snapshot = deployment_snapshot(project, model_config["model_deployment"])
        if run["model_snapshot"] is not None and run["model_snapshot"] != model_snapshot:
            raise ValueError("The answer model version changed.")
        if model_snapshot != baseline()["model_snapshot"]:
            raise ValueError("Use the same answer model deployment/version as the recorded V1 baseline.")
        if retrieval.model_contract(project, config) != setup["models"]:
            raise ValueError("Embedding/planning model versions changed.")
        run["model_snapshot"] = model_snapshot
        write_json(path, run)
        for case in cases:
            key = case["id"]
            if key in saved:
                continue
            pending = run["pending"].setdefault(key, {})
            if args.stage == "v2-replay":
                context = historical[key]["context"]
                documents = historical[key]["documents"]
                retrieval_record = {"mode": "replayed-identical-context", "documents": documents}
            else:
                if "initial_retrieval" not in pending:
                    pending["initial_retrieval"] = retrieval.retrieve(
                        search, model, config, case["query"], setup["corpus_hash"], mode="planned",
                    )
                    write_json(path, run)
                retrieval_record = pending["initial_retrieval"]
                context = retrieved_context(retrieval_record)
                documents = retrieval_record["documents"]
            final_case = dict(case)
            final_query = case["query"]
            history = None
            interaction = None
            if key in followups:
                specification = followups[key]
                if "initial_response" not in pending:
                    pending["initial_response"] = generate(model, model_config, case["query"], context, prompt)
                    write_json(path, run)
                initial = pending["initial_response"]
                checks = response_checks(case, initial["response"])
                if initial.get("output_error") or not all(checks.values()):
                    raise ValueError(f"{key}: the initial clarification/handoff behavior failed; it cannot be hidden by a later answer.")
                history = [
                    {"role": "user", "content": case["query"]},
                    {"role": "assistant", "content": initial["response"]["answer"]},
                ]
                interaction = {
                    "initial_case": case, "initial_context": context, "initial_context_hash": digest(context),
                    "initial_response": initial["response"], "initial_checks": checks,
                    "followup": specification["query"], "kind": specification["kind"],
                    "source": "explicit scripted user turn from evaluation data, not a fact invented by the assistant",
                }
                final_query = specification["query"]
                if args.stage != "v2-replay":
                    if "final_retrieval" not in pending:
                        pending["final_retrieval"] = retrieval.retrieve(
                            search, model, config, final_query, setup["corpus_hash"],
                            mode="planned", history=history,
                        )
                        write_json(path, run)
                    retrieval_record = pending["final_retrieval"]
                    context = retrieved_context(retrieval_record)
                    documents = retrieval_record["documents"]
                for field in ("expected_decision", "expected_limit_krw", "expected_citations", "ground_truth"):
                    final_case[field] = specification[field]
                final_case["query"] = conversation_query(history, final_query)
                run["retrieval_labels"][key] = specification["required_chunks"]
                run["cases"] = [final_case if item["id"] == key else item for item in run["cases"]]
            response = generate(model, model_config, final_query, context, prompt, history=history)
            run["rows"].append({
                "case_id": key, "query": final_case["query"], "context": context, "context_hash": digest(context),
                "documents": documents, "retrieval": retrieval_record,
                "expected_behavior": grading.expected_behavior(final_case), "interaction": interaction,
                "generation_user_query": final_query, "generation_history": history, **response,
            })
            run["pending"].pop(key, None)
            write_json(path, run)
            print(f"{len(run['rows'])}/{len(cases)} {key} saved", flush=True)
    run["status"] = "complete"
    run["evidence_hash"] = without_hash(run)
    write_json(path, run)
    print(f"GENERATION COMPLETE: {args.stage}; {len(run['rows'])} answers.")
    return 0


def evaluation_items(run: dict) -> list[dict]:
    return [{
        "id": row["case_id"], "query": row["query"], "context": row["context"],
        "response": row["raw_response"], "expected_behavior": row["expected_behavior"],
    } for row in run["rows"]]


def judge_command(args) -> int:
    run = load_generation(RESULTS / args.stage)
    config = read_config(args.foundry_config)
    fixed = fixed_judge()
    items = evaluation_items(run)
    like = None if args.stage == "v1-recorded" else RESULTS / "v1-recorded"
    judge = grading.evaluate(
        config, items, fixed, RESULTS / args.stage, like=like, wait_seconds=args.wait_seconds,
    )
    return 3 if judge is None else 0


def stage_metrics(stage: str) -> dict:
    folder = RESULTS / stage
    run = load_generation(folder)
    request = read_json(folder / "evaluation-request.json")
    judge = read_json(folder / "judge.json")
    if request["items"] != evaluation_items(run):
        raise ValueError("Judge input does not match the actual generated answers/contexts.")
    grading.validate(judge, request["items"], fixed_judge(), request["evidence_hash"])
    rows = {row["case_id"]: row for row in run["rows"]}
    criterion = read_json(DATA / "acceptance.json")
    required = criterion["required_metrics"]
    score_threshold = criterion["score_threshold"]
    values, critical_failures = {}, []
    for case in run["cases"]:
        row = rows[case["id"]]
        checks = response_checks(case, row["response"])
        if row.get("output_error"):
            checks = dict.fromkeys(checks, False)
        retrieved = {document["id"] for document in row["documents"]}
        expected = set(run["retrieval_labels"][case["id"]])
        scores = {metric: judge["rows"][case["id"]][metric]["score"] for metric in grading.METRICS}
        complete = expected <= retrieved
        passed = all(checks.values()) and complete and all(scores[metric] >= score_threshold for metric in required)
        interaction = row.get("interaction")
        intermediate_safe = not interaction or all(
            response_checks(interaction["initial_case"], interaction["initial_response"]).values()
        )
        passed = passed and intermediate_safe
        values[case["id"]] = {"business_checks": checks, "required_chunks_found": complete, "scores": scores, "intermediate_safe": intermediate_safe, "passed": passed}
        if case["critical"] and not passed:
            critical_failures.append(case["id"])
    count = len(values)
    rates = {
        "business": sum(all(row["business_checks"].values()) for row in values.values()) / count,
        "retrieval": sum(row["required_chunks_found"] for row in values.values()) / count,
        **{metric: sum(row["scores"][metric] >= score_threshold for row in values.values()) / count for metric in grading.METRICS},
    }
    accepted = not critical_failures and all(
        rates[name] >= criterion["pass_rate_threshold"] for name in ("business", "retrieval", *required)
    ) and all(row["intermediate_safe"] for row in values.values())
    return {"stage": stage, "cases": count, "rates": rates, "critical_failures": critical_failures, "passed": accepted, "rows": values}


def freeze_command(args) -> int:
    baseline_result = stage_metrics("v1-recorded")
    replay = stage_metrics("v2-replay")
    planned = stage_metrics("planned-dev")
    if baseline_result["passed"]:
        raise ValueError("The starting evidence has no failure; do not manufacture one.")
    if not replay["passed"] or not planned["passed"]:
        raise ValueError("Dev acceptance is not met. Diagnose dev failures before freezing or opening a holdout.")
    old = load_generation(RESULTS / "v1-recorded")
    improved = load_generation(RESULTS / "v2-replay")
    initial_hashes = [
        row["interaction"]["initial_context_hash"] if row.get("interaction") else row["context_hash"]
        for row in improved["rows"]
    ]
    if [row["context_hash"] for row in old["rows"]] != initial_hashes:
        raise ValueError("The controlled starting contexts must match the recorded baseline.")
    run = load_generation(RESULTS / "planned-dev")
    for row in run["rows"]:
        if not row["retrieval"]["evidence"].get("llm_query_planning"):
            raise ValueError("Final dev run lacks actual query-planning evidence.")
    setup = read_json(RESULTS / "setup.json")
    if (
        run["input_contract"]["retrieval_models"] != setup["models"]
        or run["input_contract"]["corpus_hash"] != setup["corpus_hash"]
    ):
        raise ValueError("Dev retrieval configuration no longer matches the setup.")
    vector_probe = read_json(RESULTS / "vector-query.json")
    if vector_probe["mode"] != "vector" or vector_probe["evidence"]["query_vector_dimensions"] != 1536 or not vector_probe["documents"]:
        raise ValueError("A successful actual vector-only retrieval probe is required.")
    vector = next(field for field in setup["index"]["fields"] if field["name"] == retrieval.VECTOR_FIELD)
    if vector["dimensions"] != 1536 or not setup["index"]["vectorSearch"]["vectorizers"]:
        raise ValueError("A configured vector index/vectorizer is required.")
    record = {
        "frozen_at": now(), "prompt": run["prompt"], "prompt_hash": run["prompt_hash"],
        "judge_contract": fixed_judge(), "acceptance": read_json(DATA / "acceptance.json"),
        "retrieval_config": run["input_contract"]["retrieval_config"],
        "retrieval_models": setup["models"], "corpus_hash": setup["corpus_hash"],
        "search_definition_hashes": retrieval.definition_hashes(setup),
        "generation_contract": run["generation_contract"], "model_snapshot": run["model_snapshot"],
        "dev_cases": run["cases"], "dev_evidence_hash": run["evidence_hash"],
        "dev_initial_cases": run["initial_cases"],
        "dev_followups_hash": digest(read_json(DATA / "dev-followups.json")),
        "baseline_result": baseline_result, "replay_result": replay, "planned_dev_result": planned,
    }
    path = RESULTS / "frozen.json"
    if path.exists():
        existing = read_json(path)
        comparable = {key: value for key, value in existing.items() if key not in ("frozen_at", "evidence_hash")}
        if comparable != {key: value for key, value in record.items() if key != "frozen_at"}:
            raise ValueError("The frozen contract differs; do not replace it.")
        print("Existing frozen experiment retained.")
        return 0
    record["evidence_hash"] = without_hash(record)
    write_json(path, record)
    print(f"FROZEN: {record['evidence_hash']}")
    print("Only now create/register the new holdout. Do not edit the prompt, judge, or retrieval configuration.")
    return 0


def register_holdout_command(args) -> int:
    frozen = read_json(RESULTS / "frozen.json")
    if frozen["evidence_hash"] != without_hash(frozen):
        raise ValueError("Frozen contract changed.")
    case_path, label_path, _ = holdout_paths()
    cases = read_cases(case_path)
    labels = read_json(label_path)
    if len(cases) < frozen["acceptance"]["minimum_fresh_holdout_cases"]:
        raise ValueError("The held-out acceptance set is too small.")
    old_cases = frozen["dev_cases"] + frozen["dev_initial_cases"]
    old_ids = {case["id"] for case in old_cases}
    old_queries = {" ".join(case["query"].casefold().split()) for case in old_cases}
    if any(case["id"] in old_ids or " ".join(case["query"].casefold().split()) in old_queries for case in cases):
        raise ValueError("Holdout overlaps the development cases.")
    documents = read_documents(ROOT / "optional-rag" / "documents.jsonl")
    allowed = {document["id"] for document in documents if document["approved"]}
    if set(labels) != {case["id"] for case in cases} or any(
        not isinstance(values, list) or not values or not set(values) <= allowed for values in labels.values()
    ):
        raise ValueError("Holdout retrieval labels are invalid.")
    validate_followups(cases, read_json(followup_path("holdout")))
    record = {
        "registered_at": now(), "frozen_hash": frozen["evidence_hash"],
        "cases_hash": digest(cases), "labels_hash": digest(labels),
        "followups_hash": digest(read_json(followup_path("holdout"))),
        "source": "authored after freezing; not used to tune this candidate",
    }
    path = RESULTS / "holdout-registration.json"
    if path.exists():
        existing = read_json(path)
        if any(existing[key] != record[key] for key in ("frozen_hash", "cases_hash", "labels_hash", "followups_hash")):
            raise ValueError("A different holdout was already registered.")
        print("Existing holdout registration retained.")
        return 0
    write_json(path, record)
    print(f"HOLDOUT REGISTERED: {len(cases)} new cases, against frozen {record['frozen_hash'][:12]}")
    return 0


def create_holdout_command(args) -> int:
    frozen = read_json(RESULTS / "frozen.json")
    if frozen["evidence_hash"] != without_hash(frozen):
        raise ValueError("Frozen contract changed.")
    case_path, label_path, provenance_path = holdout_paths()
    if case_path.exists() or label_path.exists() or followup_path("holdout").exists():
        raise ValueError("Holdout files already exist. Do not resample them to obtain a pass.")
    seed = secrets.randbits(64) if args.seed is None else args.seed
    rng = random.Random(seed)
    city = rng.choice(["울산", "전주", "포항", "여수", "창원"])
    overseas = rng.choice(["베를린", "시드니", "밴쿠버", "로마", "싱가포르"])
    current = f"2026년 {rng.choice([9, 10, 11, 12])}월 {rng.randint(2, 27)}일"
    previous = f"2026년 {rng.choice([2, 3, 4, 5, 6])}월 {rng.randint(2, 27)}일"
    below_current = rng.randrange(142000, 199000, 1000)
    above_current = rng.randrange(206000, 259000, 1000)
    below_previous = rng.randrange(111000, 159000, 1000)
    above_previous = rng.randrange(162000, 198000, 1000)
    unclear = rng.choice([163000, 172000, 181000, 188000, 197000])
    specifications = [
        ("current-within", f"{current} {city} 국내 출장의 숙박비가 1박 {below_current}원입니다. 공식 한도 안에서 정산할 수 있나요?",
         "allowed", 200000, "TRAVEL-CURRENT", "current-lodging",
         f"실제 출장일의 현재 한도는 200000원이다. {below_current}원은 한도 이내이므로 허용된다."),
        ("current-over", f"{current} 국내 출장 호텔비가 1박 {above_current}원입니다. 재무팀 사전 승인은 없는데 바로 청구 가능한가요?",
         "needs_approval", 200000, "TRAVEL-CURRENT", "current-lodging",
         f"{above_current}원은 현재 한도 200000원을 초과하므로 재무팀 사전 승인이 필요하다. 승인 사실을 만들어 내면 안 된다."),
        ("previous-within", f"{previous} 국내 출장에서 1박 {below_previous}원을 지출했습니다. 10월에 정산하면 어떤 한도를 적용하고 허용되나요?",
         "allowed", 160000, "TRAVEL-PREVIOUS", "previous-lodging",
         f"정산일이 아니라 실제 출장일의 과거 한도 160000원을 적용한다. {below_previous}원은 허용된다."),
        ("previous-over", f"{previous} 국내 숙박비는 1박 {above_previous}원이었습니다. 사전 승인은 없으며 지금 정산하려고 합니다. 가능한가요?",
         "needs_approval", 160000, "TRAVEL-PREVIOUS", "previous-lodging",
         f"과거 한도 160000원을 적용한다. {above_previous}원은 초과이므로 재무팀 사전 승인이 필요하다."),
        ("overseas", f"다음 {overseas} 해외 출장에서 호텔비로 쓸 수 있는 회사의 원화 상한이 얼마인가요?",
         "unknown", None, "SCOPE", "scope-overseas",
         "제공된 공식 문서에는 해외 숙박 한도가 없다. 국내 금액을 대입하거나 금액을 추측하지 말고 재무팀 확인을 안내한다."),
        ("missing-date", f"정산 서류를 다음 주에 내려고 합니다. 국내 출장 호텔 영수증은 1박 {unclear}원인데 허용되는 금액인가요?",
         "needs_info", None, "SCOPE", "scope-date",
         "다음 주는 정산 시점이지 실제 출장일이 아니다. 실제 출장일을 먼저 묻고 한도나 허용 여부를 미리 단정하지 않는다."),
        ("air-class", f"{current} 국내 출장 항공편을 비즈니스석으로 예약하려 합니다. 규정상 허용되나요?",
         "not_allowed", None, "TRAVEL-CURRENT", "current-air",
         "국내선은 이코노미석만 허용한다. 비즈니스석은 금지이며 숙박 한도는 이 질문에 해당하지 않는다."),
        ("boundary", f"{current} {city} 출장의 국내 숙박비가 정확히 1박 200000원입니다. 한도 초과 승인을 따로 받아야 하나요?",
         "allowed", 200000, "TRAVEL-CURRENT", "current-lodging",
         "현재 한도는 200000원 이하이므로 정확히 같은 금액도 허용된다. 한도 초과에 따른 사전 승인은 필요하지 않다."),
    ]
    cases, labels = [], {}
    for number, (category, query, decision, limit, citation, chunk, truth) in enumerate(specifications, 1):
        case_id = f"N{number:02}"
        cases.append({
            "id": case_id, "category": category, "critical": True, "query": query,
            "expected_decision": decision, "expected_limit_krw": limit,
            "expected_citations": [citation], "ground_truth": truth,
        })
        labels[case_id] = [chunk]
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases), encoding="utf-8",
    )
    write_json(label_path, labels)
    followups = {
        "N05": {
            "kind": "acknowledged-handoff",
            "query": f"그렇다면 금액은 추측하지 말고, {overseas} 출장 호텔비 상한을 재무팀에 문의할 때 전달할 정보와 확인할 질문을 정리해 주세요.",
            "expected_decision": "unknown", "expected_limit_krw": None,
            "expected_citations": ["SCOPE"], "required_chunks": ["scope-overseas"],
            "ground_truth": "사용자가 금액 추측 대신 재무팀 확인 절차를 요청했다. 정책에 없는 금액을 만들지 않고 출장지·기간·예정 금액 등 문의에 도움이 되는 정보와 적용 한도 확인 질문을 구체적으로 안내한다.",
        },
        "N06": {
            "kind": "date-clarification",
            "query": f"실제 숙박한 날짜는 {current}입니다. 앞서 말한 1박 {unclear}원의 정산 가능 여부를 이 날짜 기준으로 알려주세요.",
            "expected_decision": "allowed", "expected_limit_krw": 200000,
            "expected_citations": ["TRAVEL-CURRENT"], "required_chunks": ["current-lodging"],
            "ground_truth": f"사용자가 제공한 실제 출장일에는 현재 한도 200000원이 적용된다. {unclear}원은 한도 이내이므로 허용되며 한도 초과 승인은 필요하지 않다.",
        },
    }
    write_json(followup_path("holdout"), followups)
    write_json(provenance_path, {
        "created_at": now(), "frozen_contract_hash": frozen["evidence_hash"], "seed": seed,
        "cases_hash": digest(cases), "labels_hash": digest(labels),
        "followups_hash": digest(followups),
        "coverage": [item[0] for item in specifications],
        "note": "Created only after the prompt, judge and planned retrieval contract were frozen.",
    })
    print("Created eight fresh balanced cases after freeze; no model has answered them yet.")
    return register_holdout_command(args)


def accept_command(args) -> int:
    frozen = read_json(RESULTS / "frozen.json")
    run = load_generation(RESULTS / "holdout")
    stage_inputs("holdout", run["input_contract"]["retrieval_config"])
    if run["prompt_hash"] != frozen["prompt_hash"] or run["model_snapshot"] != frozen["model_snapshot"]:
        raise ValueError("Holdout did not use the frozen candidate.")
    if (
        run["generation_contract"] != frozen["generation_contract"]
        or run["input_contract"]["retrieval_models"] != frozen["retrieval_models"]
        or run["input_contract"]["corpus_hash"] != frozen["corpus_hash"]
    ):
        raise ValueError("Holdout generation/retrieval inputs differ from the frozen contract.")
    result = stage_metrics("holdout")
    result["status"] = "LAB_ACCEPTANCE_PASSED" if result["passed"] else "LAB_ACCEPTANCE_BLOCKED"
    result["human_production_approval"] = "PENDING — not granted by this automated lab"
    result["frozen_hash"] = frozen["evidence_hash"]
    write_json(RESULTS / "acceptance-result.json", result)
    stages = [stage_metrics(name) for name in ("v1-recorded", "v2-replay", "planned-dev")] + [result]
    text = "# " + result["status"] + "\n\n"
    text += "Every V2 case must pass all declared criteria, including builtin Relevance at 4/5. No failed metric is excluded.\n\n"
    text += "| Stage | Business | Retrieval | Groundedness | Policy task success | Relevance (required) |\n|---|---|---|---|---|---|\n"
    for stage in stages:
        rates = stage["rates"]
        text += f"| {stage['stage']} | {rates['business']:.0%} | {rates['retrieval']:.0%} | {rates['groundedness']:.0%} | {rates['policy_task_success']:.0%} | {rates['relevance']:.0%} |\n"
    text += "\n**Human production approval remains pending. A small held-out lab pass is not production certification.**\n"
    (RESULTS / "acceptance-report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["passed"] else 2


def inspect_command(args) -> int:
    run = load_generation(RESULTS / args.stage)
    matches = [row for row in run["rows"] if row["case_id"] == args.case_id]
    if not matches:
        raise ValueError("This case is not present in the selected stage.")
    row = matches[0]
    metric = stage_metrics(args.stage)["rows"][args.case_id]
    print(f"{args.stage} / {args.case_id}")
    if args.dialogue and row.get("interaction"):
        interaction = row["interaction"]
        print("User:", interaction["initial_case"]["query"])
        print("Assistant:", interaction["initial_response"]["answer"])
        print("Evaluation-user follow-up:", interaction["followup"])
        print("Final answer:", row["response"]["answer"])
        print("Final scores:", json.dumps(metric["scores"], ensure_ascii=False))
        print("Initial behavior checks:", json.dumps(metric["intermediate_safe"]))
        return 0
    print(json.dumps(row["response"], ensure_ascii=False, indent=2))
    print("Business checks:", json.dumps(metric["business_checks"], ensure_ascii=False))
    print("Scores:", json.dumps(metric["scores"], ensure_ascii=False))
    print("Chunks:", ", ".join(document["id"] for document in row["documents"]))
    print("Context hash:", row["context_hash"])
    if args.context:
        print(row["context"])
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Advanced, versioned failure-to-acceptance RAG lab.")
    root.add_argument("--config", type=Path, default=Path("config.advanced.json"))
    root.add_argument("--foundry-config", type=Path, default=Path("config.json"))
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("setup").set_defaults(handler=setup_command)
    query = sub.add_parser("query")
    query.add_argument("--mode", choices=("vector", "hybrid", "planned"), required=True)
    query.add_argument("--query", required=True)
    query.add_argument("--out", type=Path, required=True)
    query.set_defaults(handler=query_command)
    calibration = sub.add_parser("calibrate")
    calibration.add_argument("--wait-seconds", type=int, default=300)
    calibration.set_defaults(handler=calibrate_command)
    sub.add_parser("baseline").set_defaults(handler=import_baseline_command)
    run = sub.add_parser("run")
    run.add_argument("--stage", choices=("v2-replay", "planned-dev", "holdout"), required=True)
    run.set_defaults(handler=run_command)
    judge = sub.add_parser("judge")
    judge.add_argument("--stage", choices=("v1-recorded", "v2-replay", "planned-dev", "holdout"), required=True)
    judge.add_argument("--wait-seconds", type=int, default=300)
    judge.set_defaults(handler=judge_command)
    sub.add_parser("freeze").set_defaults(handler=freeze_command)
    create = sub.add_parser("create-holdout")
    create.add_argument("--seed", type=int)
    create.set_defaults(handler=create_holdout_command)
    sub.add_parser("register-holdout").set_defaults(handler=register_holdout_command)
    sub.add_parser("accept").set_defaults(handler=accept_command)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--stage", choices=("v1-recorded", "v2-replay", "planned-dev", "holdout"), required=True)
    inspect.add_argument("--case-id", required=True)
    inspect.add_argument("--context", action="store_true")
    inspect.add_argument("--dialogue", action="store_true")
    inspect.set_defaults(handler=inspect_command)
    return root


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if getattr(args, "wait_seconds", 0) < 0:
            raise ValueError("wait-seconds cannot be negative.")
        return args.handler(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted. Saved evidence is retained; resume the identical command.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

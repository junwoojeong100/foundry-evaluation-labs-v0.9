"""The only network-facing part of the workshop. Imported only in live mode."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from evaluation import ANSWER_SCHEMA, METRICS, SCORE_THRESHOLD, read_json, response_context, write_json

OUTPUT_INSTRUCTIONS = """
JSON 객체만 반환합니다.
decision: allowed(허용), needs_approval(사전 승인 필요), not_allowed(금지),
unknown(규정에 없음), needs_info(질문 정보 부족) 중 하나.
limit_krw: 적용되는 숙박 한도를 원 단위 정수로 표현하거나, 결정할 수 없으면 null.
citations: 판단 근거 문서 ID의 배열. answer: 사용자에게 보여 줄 한국어 설명.
"""
GENERATION_SETTINGS = {"max_completion_tokens": 4096}


def generation_contract() -> dict:
    return {
        "settings": GENERATION_SETTINGS, "output_instructions": OUTPUT_INSTRUCTIONS,
        "schema": ANSWER_SCHEMA,
    }


def reject_non_json_number(value: str):
    raise ValueError(f"표준 JSON 숫자가 아닙니다: {value}")


def read_config(path: Path) -> dict:
    return validate_config(read_json(path))


def validate_config(config: dict) -> dict:
    keys = {"project_endpoint", "model_deployment", "judge_deployment"}
    if not isinstance(config, dict) or set(config) != keys:
        raise ValueError("config.example.json의 세 필드를 사용하세요.")
    if any(
        not isinstance(value, str) or not value.strip() or value != value.strip()
        or "YOUR-" in value or "<" in value or ">" in value
        for value in config.values()
    ):
        raise ValueError("예시 값을 실제 endpoint와 배포 이름으로 바꾸세요.")
    endpoint = urlparse(config["project_endpoint"])
    if (
        endpoint.scheme != "https" or not endpoint.hostname
        or not endpoint.hostname.endswith(".services.ai.azure.com")
        or not endpoint.path.startswith("/api/projects/")
        or not endpoint.path.removeprefix("/api/projects/").strip("/")
        or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment
        or endpoint.port not in (None, 443)
    ):
        raise ValueError("Foundry 프로젝트 endpoint가 필요합니다: https://ACCOUNT.services.ai.azure.com/api/projects/PROJECT")
    return config


@contextmanager
def clients(config: dict):
    validate_config(config)
    try:
        from azure.ai.projects import AIProjectClient
        from azure.core.exceptions import AzureError
        from azure.identity import AzureCliCredential
        from openai import APIError
    except ImportError as exc:
        raise RuntimeError("LIVE 의존성이 없습니다. python -m pip install -r requirements.txt 를 실행하세요.") from exc
    try:
        with (
            AzureCliCredential(process_timeout=30) as credential,
            AIProjectClient(endpoint=config["project_endpoint"], credential=credential) as project,
            project.get_openai_client(timeout=60.0, max_retries=0) as client,
        ):
            yield project, client
    except (AzureError, APIError) as exc:
        raise RuntimeError(f"Azure 호출 실패 ({type(exc).__name__}): {exc}\n복구: docs/reference.md") from exc


def validate_history(history: list[dict] | None) -> list[dict]:
    if history is not None and not isinstance(history, list):
        raise ValueError("Conversation history must be an array.")
    turns = [] if history is None else history
    if any(
        not isinstance(turn, dict) or set(turn) != {"role", "content"} or turn["role"] not in ("user", "assistant")
        or not isinstance(turn["content"], str) or not turn["content"].strip()
        for turn in turns
    ):
        raise ValueError("Conversation history must contain user/assistant text turns only.")
    return turns


def messages_for(query: str, context: str, prompt: str, *, history: list[dict] | None = None) -> list[dict]:
    turns = validate_history(history)
    return [
        {"role": "system", "content": prompt + "\n" + OUTPUT_INSTRUCTIONS + "\n<reference>\n" + context + "\n</reference>"},
        *turns,
        {"role": "user", "content": query},
    ]


def generate(client, config: dict, query: str, context: str, prompt: str, *, history: list[dict] | None = None) -> dict:
    started = time.monotonic()
    completion = client.chat.completions.create(
        model=config["model_deployment"],
        messages=messages_for(query, context, prompt, history=history),
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "policy_answer", "strict": True, "schema": ANSWER_SCHEMA},
        },
        **GENERATION_SETTINGS,
    )
    if not completion.choices:
        raise RuntimeError("모델 응답에 choices가 없습니다. 응답 수집을 중단합니다.")
    choice = completion.choices[0]
    raw = choice.message.content or ""
    output_error = None
    if choice.message.refusal:
        output_error = f"모델 거절: {choice.message.refusal}"
    elif choice.finish_reason != "stop":
        output_error = f"불완전한 출력: finish_reason={choice.finish_reason}"
    try:
        response = json.loads(raw, parse_constant=reject_non_json_number)
    except ValueError:
        response = None
        output_error = output_error or "모델 출력이 유효한 JSON이 아닙니다."
    usage = None
    if completion.usage is not None:
        usage = {
            "input_tokens": completion.usage.prompt_tokens,
            "output_tokens": completion.usage.completion_tokens,
        }
    return {
        "response": response, "raw_response": raw, "output_error": output_error,
        "latency_ms": round((time.monotonic() - started) * 1000, 2),
        "usage": usage, "model": completion.model,
    }


def deployment_snapshot(project, name: str) -> dict:
    deployment = project.deployments.get(name)
    snapshot = {
        key: getattr(deployment, key, None)
        for key in ("name", "model_name", "model_version", "type")
    }
    if not snapshot["model_name"] or not snapshot["model_version"]:
        raise ValueError(f"{name}: 모델/버전 정보를 확인할 수 없습니다. Foundry 모델 배포 이름을 확인하세요.")
    return snapshot


def evaluator_contract(project, config: dict) -> dict:
    criteria, definitions = [], {}
    for metric in METRICS:
        name = f"builtin.{metric}"
        versions = list(project.beta.evaluators.list_versions(name=name))
        if not versions:
            raise RuntimeError(f"평가기 카탈로그에 {name}이 없습니다.")
        chosen = max(versions, key=lambda version: (version.created_at, version.version))
        definitions[name] = {
            "name": chosen.name, "version": chosen.version,
            "definition": chosen.definition.as_dict(),
        }
        mapping = {"query": "{{item.query}}", "response": "{{item.response}}"}
        if metric == "groundedness":
            mapping["context"] = "{{item.context}}"
        criteria.append({
            "type": "azure_ai_evaluator", "name": metric,
            "evaluator_name": name, "evaluator_version": chosen.version,
            "initialization_parameters": {"deployment_name": config["judge_deployment"]},
            "data_mapping": mapping,
        })
    return {
        "source": "foundry", "project_endpoint": config["project_endpoint"],
        "judge_deployment": config["judge_deployment"],
        "judge_model": deployment_snapshot(project, config["judge_deployment"]),
        "criteria": criteria, "definitions": definitions,
        "local_score_threshold": SCORE_THRESHOLD, "response_scope": "whole-json",
    }


def evaluation_items(run: dict) -> list[dict]:
    rows = {row["case_id"]: row for row in run["rows"]}
    return [
        {
            "id": case["id"], "query": case["query"], "context": response_context(run, rows[case["id"]]),
            "response": rows[case["id"]]["raw_response"],
        }
        for case in run["cases"]
    ]


def parse_output_items(outputs: list[dict], items: list[dict], *, metrics=METRICS) -> dict:
    expected = {item["id"]: item for item in items}
    parsed = {}
    for output in outputs:
        source = output.get("datasource_item")
        if isinstance(source, dict) and isinstance(source.get("item"), dict):
            source = source["item"]
        if not isinstance(source, dict) or not isinstance(source.get("id"), str) or source["id"] not in expected:
            raise ValueError("Foundry 출력에 원본 사례 ID가 없습니다. foundry-output.json을 확인하세요.")
        case_id = source["id"]
        if case_id in parsed or any(source.get(key) != value for key, value in expected[case_id].items()):
            raise ValueError(f"Foundry 출력의 원본 데이터가 다르거나 중복되었습니다: {case_id}")
        results = output.get("results")
        if not isinstance(results, list):
            raise ValueError(f"{case_id}: Foundry 평가 결과가 없습니다.")
        values = {}
        for result in results:
            if not isinstance(result, dict):
                raise ValueError(f"{case_id}: 잘못된 평가 결과입니다.")
            name = result.get("name")
            if name not in metrics or name in values:
                raise ValueError(f"{case_id}: 중복 또는 예상하지 못한 평가기 {name}")
            values[name] = {"score": result.get("score"), "reason": result.get("reason")}
        parsed[case_id] = values
    if set(parsed) != set(expected):
        raise ValueError("Foundry 평가 결과가 일부 누락되었습니다. 누락을 통과로 처리하지 않습니다.")
    return parsed


def judge_run(
    run: dict, folder: Path, *, like: Path | None, wait_seconds: int,
    contract_override: dict | None = None, items_override: list[dict] | None = None,
    metrics=METRICS,
) -> dict | None:
    state_path = folder / "foundry-job.json"
    items = evaluation_items(run) if items_override is None else items_override
    if (
        not items or any(not isinstance(item, dict) for item in items)
        or any(set(item) != set(items[0]) for item in items)
        or any(not isinstance(value, str) for item in items for value in item.values())
        or len({item.get("id") for item in items}) != len(items)
    ):
        raise ValueError("Evaluation items must have matching string fields and unique case IDs.")
    with clients(run["config"]) as (project, client):
        if state_path.exists():
            state = read_json(state_path)
            if state["evidence_hash"] != run["evidence_hash"]:
                raise ValueError("이미 다른 응답으로 시작한 Foundry 작업입니다.")
            if contract_override is not None and state["contract"] != contract_override:
                raise ValueError("저장된 평가 계약이 요청한 고정 계약과 다릅니다.")
            if like is not None:
                reference = read_json(like / "foundry-job.json")
                if state["eval_id"] != reference["eval_id"]:
                    raise ValueError("진행 중인 작업의 평가 그룹을 --like로 변경할 수 없습니다.")
        else:
            if like is not None:
                reference = read_json(like / "foundry-job.json")
                contract = reference["contract"]
                if contract_override is not None and contract != contract_override:
                    raise ValueError("--like의 평가 계약이 요청한 고정 계약과 다릅니다.")
                if (
                    contract["project_endpoint"] != run["config"]["project_endpoint"]
                    or contract["judge_deployment"] != run["config"]["judge_deployment"]
                ):
                    raise ValueError("--like 실행의 프로젝트/Judge 모델 배포가 다릅니다.")
                if deployment_snapshot(project, run["config"]["judge_deployment"]) != contract["judge_model"]:
                    raise ValueError("Judge 모델 배포 버전이 바뀌었습니다. 같은 실험으로 비교할 수 없습니다.")
                eval_id = reference["eval_id"]
                if not eval_id:
                    raise ValueError("--like 실행의 Foundry 평가 그룹이 아직 없습니다.")
            else:
                contract = contract_override if contract_override is not None else evaluator_contract(project, run["config"])
                eval_id = None
            state = {
                "evidence_hash": run["evidence_hash"], "contract": contract,
                "eval_id": eval_id, "run_id": None, "phase": "ready",
            }
            write_json(state_path, state)
        if not state["eval_id"]:
            if state["phase"] == "creating-eval":
                raise RuntimeError("평가 그룹 생성 결과가 불명확합니다. 자동 재생성하지 않습니다. docs/reference.md의 원격 ID 복구를 따르세요.")
            state["phase"] = "creating-eval"
            write_json(state_path, state)
            keys = ("id", "query", "response", "context") if items_override is None else tuple(items[0])
            fields = {key: {"type": "string"} for key in keys}
            evaluation = client.evals.create(
                name=f"straightforward-{run['run_id'][:8]}",
                metadata={"workshop_run": run["run_id"]},
                data_source_config={
                    "type": "custom",
                    "item_schema": {"type": "object", "properties": fields, "required": list(fields)},
                    "include_sample_schema": False,
                },
                testing_criteria=state["contract"]["criteria"],
            )
            state["eval_id"] = evaluation.id
            state["phase"] = "ready"
            write_json(state_path, state)
            print(f"Foundry eval_id: {evaluation.id}", flush=True)
        if not state["run_id"]:
            if state["phase"] == "creating-run":
                raise RuntimeError("평가 실행 생성 결과가 불명확합니다. 자동 재제출하지 않습니다. docs/reference.md의 원격 ID 복구를 따르세요.")
            state["phase"] = "creating-run"
            write_json(state_path, state)
            job = client.evals.runs.create(
                eval_id=state["eval_id"],
                name=f"{run['prompt_name']}-{run['split']}-{run['run_id'][:8]}",
                metadata={"workshop_run": run["run_id"]},
                data_source={
                    "type": "jsonl",
                    "source": {"type": "file_content", "content": [{"item": item} for item in items]},
                },
            )
            state["run_id"] = job.id
            state["phase"] = "submitted"
            write_json(state_path, state)
        print(f"Foundry eval_id={state['eval_id']} run_id={state['run_id']}", flush=True)
        deadline = time.monotonic() + wait_seconds
        while True:
            job = client.evals.runs.retrieve(run_id=state["run_id"], eval_id=state["eval_id"])
            if state["phase"] != job.status:
                print(f"Foundry 상태: {job.status}", flush=True)
            state["phase"] = job.status
            state["report_url"] = job.report_url
            write_json(state_path, state)
            if job.status in ("completed", "failed", "canceled", "cancelled"):
                break
            if time.monotonic() >= deadline:
                print("아직 처리 중입니다. 방금 실행한 명령 전체로 조회를 재개하세요. 새 작업은 생성하지 않습니다.")
                return None
            time.sleep(min(5, max(0, deadline - time.monotonic())))
        if job.status != "completed":
            raise RuntimeError(f"Foundry 평가 {job.status}: {job.error}. 원본 ID를 보존했습니다.")
        outputs = [
            item.model_dump(mode="json")
            for item in client.evals.runs.output_items.list(
                run_id=state["run_id"], eval_id=state["eval_id"], limit=100
            )
        ]
        write_json(folder / "foundry-output.json", outputs)
        return {
            "source": "foundry", "evidence_hash": run["evidence_hash"],
            "contract": state["contract"], "rows": parse_output_items(outputs, items, metrics=metrics),
            "eval_id": state["eval_id"], "run_id": state["run_id"],
            "report_url": job.report_url,
        }

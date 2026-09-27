"""Local evaluation contracts. This module never calls a model or the network."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUSINESS_VERSION = "business-v1"
METRICS = ("groundedness", "relevance")
SCORE_THRESHOLD = 4
PASS_RATE = 0.8
DECISIONS = ("allowed", "needs_approval", "not_allowed", "unknown", "needs_info")
CHECKS = ("schema", "decision", "limit", "citations")
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "limit_krw": {"type": ["integer", "null"]},
        "citations": {"type": "array", "items": {"type": "string"}},
        "answer": {"type": "string"},
    },
    "required": ["decision", "limit_krw", "citations", "answer"],
    "additionalProperties": False,
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def read_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def validate_cases(cases: list[dict]) -> None:
    if not isinstance(cases, list) or not cases:
        raise ValueError("평가 데이터는 비어 있지 않은 JSONL이어야 합니다.")
    ids, queries = set(), set()
    required = {
        "id", "category", "critical", "query", "expected_decision",
        "expected_limit_krw", "expected_citations", "ground_truth",
    }
    for case in cases:
        if not isinstance(case, dict) or set(case) != required:
            raise ValueError(f"사례 필드를 확인하세요. 필요한 필드: {sorted(required)}")
        for key in ("id", "category", "query", "ground_truth"):
            if not isinstance(case[key], str) or not case[key].strip():
                raise ValueError(f"사례의 {key}는 빈 문자열일 수 없습니다.")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,39}", case["id"]):
            raise ValueError(f"사례 ID는 영문자로 시작하는 영문/숫자/_/-입니다: {case['id']}")
        if type(case["critical"]) is not bool:
            raise ValueError(f"{case['id']}: critical은 true 또는 false입니다.")
        if case["expected_decision"] not in DECISIONS:
            raise ValueError(f"{case['id']}: expected_decision을 확인하세요.")
        limit = case["expected_limit_krw"]
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError(f"{case['id']}: expected_limit_krw는 정수 또는 null입니다.")
        citations = case["expected_citations"]
        if (
            not isinstance(citations, list) or not citations
            or any(not isinstance(c, str) or c not in {"TRAVEL-CURRENT", "TRAVEL-PREVIOUS", "SCOPE"} for c in citations)
            or len(set(citations)) != len(citations)
        ):
            raise ValueError(f"{case['id']}: expected_citations에 공식 문서 ID를 넣으세요.")
        query = " ".join(case["query"].casefold().split())
        if case["id"] in ids or query in queries:
            raise ValueError(f"중복 사례 ID 또는 질문: {case['id']}")
        ids.add(case["id"])
        queries.add(query)


def read_cases(path: Path) -> list[dict]:
    cases = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{path}:{number}: JSONL에 빈 줄을 넣지 마세요.")
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: JSON 문법 오류: {exc.msg}") from exc
    validate_cases(cases)
    return cases


def response_checks(case: dict, response) -> dict[str, bool]:
    valid = (
        isinstance(response, dict)
        and set(response) == set(ANSWER_SCHEMA["required"])
        and response["decision"] in DECISIONS
        and (
            response["limit_krw"] is None
            or (type(response["limit_krw"]) is int and response["limit_krw"] >= 0)
        )
        and isinstance(response["citations"], list)
        and all(isinstance(c, str) and c for c in response["citations"])
        and isinstance(response["answer"], str)
        and bool(response["answer"].strip())
    )
    if not valid:
        return dict.fromkeys(CHECKS, False)
    citations = response["citations"]
    return {
        "schema": True,
        "decision": response["decision"] == case["expected_decision"],
        "limit": response["limit_krw"] == case["expected_limit_krw"],
        "citations": (
            len(citations) == len(set(citations))
            and set(citations) == set(case["expected_citations"])
        ),
    }


def scored_rows(run: dict) -> list[dict]:
    by_id = {r["case_id"]: r for r in run["rows"]}
    rows = []
    for case in run["cases"]:
        row = by_id[case["id"]]
        checks = response_checks(case, row["response"])
        if row.get("output_error"):
            checks = dict.fromkeys(CHECKS, False)
        rows.append({**row, "case": case, "checks": checks, "passed": all(checks.values())})
    return rows


def evidence_hash(run: dict) -> str:
    return digest({k: v for k, v in run.items() if k != "evidence_hash"})


def load_run(folder: Path, *, complete: bool = True) -> dict:
    run = read_json(folder / "run.json")
    if not isinstance(run, dict) or run.get("schema_version") != 1:
        raise ValueError(f"{folder}: 지원하지 않는 run.json 형식입니다.")
    if run.get("business_version") != BUSINESS_VERSION:
        raise ValueError(f"{folder}: 업무 평가기 버전이 다릅니다.")
    validate_cases(run["cases"])
    for key in ("cases", "context", "prompt"):
        if run[f"{key}_hash"] != digest(run[key]):
            raise ValueError(f"{folder}: 저장된 {key}가 변경되었습니다. 새 실행 이름을 쓰세요.")
    ids = [r["case_id"] for r in run["rows"]]
    expected = {case["id"] for case in run["cases"]}
    if len(ids) != len(set(ids)) or not set(ids) <= expected:
        raise ValueError(f"{folder}: 중복되거나 알 수 없는 응답 ID입니다.")
    if complete:
        if run["status"] != "complete" or set(ids) != expected:
            raise ValueError(f"{folder}: 응답 수집이 미완료입니다. 같은 run 명령으로 재개하세요.")
        if run.get("evidence_hash") != evidence_hash(run):
            raise ValueError(f"{folder}: 결과가 저장 이후 변경되었습니다.")
    return run


def judge_fingerprint(judge: dict) -> str:
    return digest(judge["contract"])


def validate_judge(judge: dict, run: dict) -> None:
    if judge.get("evidence_hash") != run["evidence_hash"]:
        raise ValueError("다른 응답을 평가한 judge 결과입니다.")
    expected_source = "authored-demo" if run["mode"] == "demo" else "foundry"
    if judge.get("source") != expected_source:
        raise ValueError("예제 점수와 실제 Foundry 점수를 혼합할 수 없습니다.")
    expected_ids = {case["id"] for case in run["cases"]}
    rows = judge.get("rows")
    if not isinstance(rows, dict) or set(rows) != expected_ids:
        raise ValueError("Judge 결과의 사례 ID가 누락되거나 추가되었습니다.")
    if not isinstance(judge.get("contract"), dict) or not judge["contract"]:
        raise ValueError("Judge의 고정된 평가 계약이 없습니다.")
    for case_id, values in rows.items():
        if not isinstance(values, dict) or set(values) != set(METRICS):
            raise ValueError(f"{case_id}: groundedness/relevance 결과가 모두 필요합니다.")
        for metric, result in values.items():
            if not isinstance(result, dict):
                raise ValueError(f"{case_id}/{metric}: 잘못된 점수 형식입니다.")
            score = result.get("score")
            if type(score) not in (int, float) or not math.isfinite(score) or not 1 <= score <= 5:
                raise ValueError(f"{case_id}/{metric}: 1~5 사이의 유효한 점수가 없습니다.")
            if not isinstance(result.get("reason"), str) or not result["reason"].strip():
                raise ValueError(f"{case_id}/{metric}: 판정 이유가 없습니다.")


def load_judge(folder: Path, run: dict) -> dict:
    judge = read_json(folder / "judge.json")
    validate_judge(judge, run)
    return judge


def business_rate(run: dict) -> float:
    rows = scored_rows(run)
    return sum(row["passed"] for row in rows) / len(rows)


def judge_rate(judge: dict, metric: str) -> float:
    rows = judge["rows"]
    return sum(values[metric]["score"] >= SCORE_THRESHOLD for values in rows.values()) / len(rows)


def comparable(before: dict, after: dict) -> None:
    for field in ("mode", "split", "cases_hash", "context_hash", "business_version", "config", "generation_contract", "target_deployment"):
        if before[field] != after[field]:
            raise ValueError(f"통제 비교 불가: {field}가 다릅니다. 같은 데이터/근거/모델/모드를 사용하세요.")
    before_models = {r["model"] for r in before["rows"]}
    after_models = {r["model"] for r in after["rows"]}
    if len(before_models) != 1 or before_models != after_models:
        raise ValueError("실제 응답 모델 버전이 달라 프롬프트만의 변화로 비교할 수 없습니다.")


def comparison(before: dict, after: dict, left_judge=None, right_judge=None) -> dict:
    comparable(before, after)
    left = {r["case_id"]: r for r in scored_rows(before)}
    right = {r["case_id"]: r for r in scored_rows(after)}
    improvements, regressions, judge_regressions = [], [], []
    for case_id in left:
        if not left[case_id]["passed"] and right[case_id]["passed"]:
            improvements.append(case_id)
        lost_checks = [
            key for key in CHECKS
            if left[case_id]["checks"][key] and not right[case_id]["checks"][key]
        ]
        if lost_checks:
            regressions.append({"id": case_id, "checks": lost_checks})
    if (left_judge is None) != (right_judge is None):
        raise ValueError("두 실행의 judge가 모두 있어야 AI 점수를 비교할 수 있습니다.")
    if left_judge is not None:
        validate_judge(left_judge, before)
        validate_judge(right_judge, after)
        if judge_fingerprint(left_judge) != judge_fingerprint(right_judge):
            raise ValueError("Judge 모델/평가기 버전이 다릅니다. judge --like로 같은 계약을 재사용하세요.")
        for case_id in left:
            lost = [
                metric for metric in METRICS
                if left_judge["rows"][case_id][metric]["score"] >= SCORE_THRESHOLD
                and right_judge["rows"][case_id][metric]["score"] < SCORE_THRESHOLD
            ]
            if lost:
                judge_regressions.append({"id": case_id, "metrics": lost})
    return {
        "before_rate": business_rate(before),
        "after_rate": business_rate(after),
        "improvements": improvements,
        "regressions": regressions,
        "judge_regressions": judge_regressions,
        "judge_compared": left_judge is not None,
    }


def cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def report_text(run: dict, judge=None) -> str:
    rows = scored_rows(run)
    passed = sum(row["passed"] for row in rows)
    source = "DEMO / 사람이 작성한 예제 / API 호출 없음" if run["mode"] == "demo" else "LIVE / 실제 모델 응답"
    lines = [
        f"# {run['prompt_name']} / {run['split']}", "", f"**{source}**", "",
        f"업무 규칙 통과: **{passed}/{len(rows)} ({passed / len(rows):.1%})**",
        f"프롬프트: `{run['prompt_hash'][:12]}` · 데이터: `{run['cases_hash'][:12]}`", "",
        "| 사례 | 유형 | 중요 | 규칙 | 실패한 검사 | Groundedness | Relevance |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        grades = judge["rows"][row["case_id"]] if judge else {}
        scores = [str(grades[m]["score"]) if m in grades else "미평가" for m in METRICS]
        failed = ", ".join(k for k, ok in row["checks"].items() if not ok) or "-"
        lines.append(
            f"| {row['case_id']} | {cell(row['case']['category'])} | "
            f"{'P0' if row['case']['critical'] else '-'} | "
            f"{'PASS' if row['passed'] else 'FAIL'} | {failed} | {scores[0]} | {scores[1]} |"
        )
    if judge:
        lines.extend(["", f"Judge 출처: **{judge['source']}**. 실습 합격선은 각 점수 **4/5 이상**."])
        for metric in METRICS:
            lines.append(f"- {metric}: {judge_rate(judge, metric):.1%} 통과")
    else:
        lines.extend(["", "**Judge 미평가**: 업무 규칙 통과만으로 답변 품질을 확정하지 않습니다."])
    lines.extend(["", "## 유형별 업무 통과", "", "| 유형 | 통과/전체 |", "|---|---|"])
    categories = sorted({r["case"]["category"] for r in rows})
    for category in categories:
        group = [r for r in rows if r["case"]["category"] == category]
        lines.append(f"| {cell(category)} | {sum(r['passed'] for r in group)}/{len(group)} |")
    if run["mode"] == "live":
        times = sorted(r["latency_ms"] for r in rows if r["latency_ms"] is not None)
        inputs = sum(r["usage"]["input_tokens"] for r in rows if r["usage"] is not None)
        outputs = sum(r["usage"]["output_tokens"] for r in rows if r["usage"] is not None)
        coverage = sum(r["usage"] is not None for r in rows)
        lines.extend(["", "## 운영 신호", ""])
        if times:
            lines.append(f"- 응답 생성 p95: {times[math.ceil(0.95 * len(times)) - 1]:.0f} ms (표본 {len(times)}개)")
        lines.append(f"- 생성 토큰: 입력 {inputs}, 출력 {outputs} (usage가 있는 {coverage}/{len(rows)}개만 집계)")
        lines.append("- Judge 토큰/비용은 위 합계에 포함하지 않습니다. 청구액은 Azure에서 확인합니다.")
    lines.extend(["", "## 사례별 근거", ""])
    for row in rows:
        case = row["case"]
        lines.extend([
            f"### {case['id']} — {case['category']}", "",
            f"**질문:** {case['query']}", "",
            f"**기대 행동:** {case['ground_truth']}", "",
            "```json", json.dumps(row["response"], ensure_ascii=False, indent=2), "```", "",
        ])
        if row.get("output_error"):
            lines.extend([f"**출력 오류:** {row['output_error']}", "", "```text", row["raw_response"], "```", ""])
        if judge:
            for metric in METRICS:
                value = judge["rows"][case["id"]][metric]
                lines.append(f"**{metric} {value['score']}/5:** {value['reason']}")
            lines.append("")
    return "\n".join(lines) + "\n"


def review_problems(folder: Path, run: dict) -> list[str]:
    path = folder / "reviews.json"
    if not path.exists():
        return [f"{folder.name}: 사람의 검토 기록이 없습니다."]
    reviews = read_json(path)
    if not isinstance(reviews, list) or not reviews:
        return [f"{folder.name}: 사람의 검토 기록이 비어 있습니다."]
    latest = {}
    ids = {c["id"] for c in run["cases"]}
    for review in reviews:
        if (
            not isinstance(review, dict)
            or review.get("evidence_hash") != run["evidence_hash"]
            or review.get("case_id") not in ids
            or review.get("verdict") not in ("pass", "fail")
            or review.get("reviewer", "human") not in ("human", "assistant")
            or not isinstance(review.get("note"), str)
            or len(review["note"].strip()) < 5
        ):
            return [f"{folder.name}: 유효하지 않거나 다른 응답의 검토 기록입니다."]
        if review.get("reviewer", "human") == "human":
            latest[review["case_id"]] = review
    if not latest:
        return [f"{folder.name}: AI 보조 검토만 있습니다. 사람의 검토 기록이 필요합니다."]
    rejected = [case_id for case_id, review in latest.items() if review["verdict"] == "fail"]
    return [f"{folder.name}: 사람이 반려한 사례 {', '.join(rejected)}"] if rejected else []


def gate(before_folder: Path, after_folder: Path, holdout_folder: Path) -> dict:
    before, after, holdout = [load_run(p) for p in (before_folder, after_folder, holdout_folder)]
    diff = comparison(before, after)
    problems = []
    if before["split"] != "dev" or holdout["split"] != "holdout":
        raise ValueError("Gate에는 dev baseline/candidate와 별도의 holdout 실행이 필요합니다.")
    for field in ("mode", "prompt_hash", "context_hash", "config", "generation_contract", "target_deployment"):
        if after[field] != holdout[field]:
            raise ValueError(f"Holdout의 {field}가 candidate와 다릅니다. --frozen을 사용하세요.")
    if {r["model"] for r in after["rows"]} != {r["model"] for r in holdout["rows"]}:
        raise ValueError("Holdout에서 실제 응답 모델 버전이 달라졌습니다.")
    if holdout.get("frozen_from") != after["evidence_hash"]:
        raise ValueError("이 candidate를 고정한 holdout이 아닙니다. --frozen을 사용하세요.")
    before_ids = {c["id"] for c in before["cases"]}
    before_queries = {" ".join(c["query"].casefold().split()) for c in before["cases"]}
    if any(
        c["id"] in before_ids or " ".join(c["query"].casefold().split()) in before_queries
        for c in holdout["cases"]
    ):
        raise ValueError("Dev와 holdout에 같은 ID 또는 질문이 들어 있습니다.")
    if diff["regressions"]:
        problems.append("업무 규칙 회귀: " + ", ".join(r["id"] for r in diff["regressions"]))
    judges = []
    for folder, run in ((before_folder, before), (after_folder, after), (holdout_folder, holdout)):
        try:
            judges.append(load_judge(folder, run))
        except (OSError, ValueError) as exc:
            problems.append(f"{folder.name}: Judge 판정 불가 — {exc}")
            judges.append(None)
    if all(j is not None for j in judges):
        if len({judge_fingerprint(j) for j in judges}) != 1:
            problems.append("Judge 모델/평가기 계약이 일치하지 않습니다.")
        else:
            diff = comparison(before, after, judges[0], judges[1])
            if diff["judge_regressions"]:
                problems.append("Judge 합격→불합격 회귀: " + ", ".join(r["id"] for r in diff["judge_regressions"]))
    for folder, run, judge in ((after_folder, after, judges[1]), (holdout_folder, holdout, judges[2])):
        if business_rate(run) < PASS_RATE:
            problems.append(f"{folder.name}: 업무 통과율 {business_rate(run):.1%} < {PASS_RATE:.0%}")
        critical_failures = [r["case_id"] for r in scored_rows(run) if r["case"]["critical"] and not r["passed"]]
        if critical_failures:
            problems.append(f"{folder.name}: P0 실패 {', '.join(critical_failures)}")
        if judge is not None:
            for metric in METRICS:
                rate = judge_rate(judge, metric)
                if rate < PASS_RATE:
                    problems.append(f"{folder.name}: {metric} 통과율 {rate:.1%} < {PASS_RATE:.0%}")
                failed_p0 = [
                    c["id"] for c in run["cases"]
                    if c["critical"] and judge["rows"][c["id"]][metric]["score"] < SCORE_THRESHOLD
                ]
                if failed_p0:
                    problems.append(f"{folder.name}: P0 {metric} 실패 {', '.join(failed_p0)}")
        problems.extend(review_problems(folder, run))
    status = "BLOCK"
    if not problems:
        status = "DEMO_CRITERIA_MET" if after["mode"] == "demo" else "READY_FOR_HUMAN_REVIEW"
    return {
        "status": status, "mode": after["mode"], "problems": problems,
        "business_rates": {"baseline": business_rate(before), "candidate": business_rate(after), "holdout": business_rate(holdout)},
        "thresholds": {"business_pass_rate": PASS_RATE, "judge_score": SCORE_THRESHOLD, "judge_pass_rate": PASS_RATE},
        "evidence": [r["evidence_hash"] for r in (before, after, holdout)],
        "note": "교육용 기준입니다. DEMO는 모델 품질 증거가 아니며, LIVE 통과도 실제 배포 승인이 아닙니다.",
    }

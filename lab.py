#!/usr/bin/env python3
"""Small workshop CLI: run -> judge -> inspect -> compare -> review -> gate."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from contextlib import nullcontext
from pathlib import Path

from evaluation import (
    BUSINESS_VERSION, METRICS, ROOT, SCORE_THRESHOLD,
    business_rate, comparison, digest, evidence_hash, gate, judge_fingerprint,
    load_judge, load_run, now, read_cases, read_json, report_text,
    scored_rows, validate_judge, write_json,
)


def demo_entries(run: dict) -> list[dict]:
    manifest = read_json(ROOT / "examples" / "manifest.json")
    key = f"{run['prompt_name']}-{run['split']}"
    if key not in manifest["fixtures"]:
        raise ValueError("DEMO는 제공된 v1/dev, v2/dev, v2/holdout, shortcut/dev만 재생합니다. 새 프롬프트/질문은 LIVE에서 실행하세요.")
    contract = manifest["fixtures"][key]
    for field in ("prompt_hash", "cases_hash", "context_hash"):
        if run[field] != contract[field]:
            raise ValueError(f"DEMO의 {field}가 원본과 다릅니다. 수정 효과는 LIVE에서 측정하세요.")
    entries = [
        json.loads(line)
        for line in (ROOT / "examples" / f"{key}.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    if digest(entries) != contract["fixture_hash"]:
        raise ValueError(f"DEMO 예제 파일이 변경되었습니다: {key}")
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)) or set(ids) != {case["id"] for case in run["cases"]}:
        raise ValueError("DEMO 사례 ID가 데이터셋과 일치하지 않습니다.")
    by_id = {entry["id"]: entry for entry in entries}
    for row in run["rows"]:
        expected = by_id[row["case_id"]]["response"]
        if row["response"] != expected or row["raw_response"] != json.dumps(expected, ensure_ascii=False):
            raise ValueError("DEMO 응답이 원본 예제와 다릅니다. 작성된 점수를 다른 답변에 적용하지 않습니다.")
    return entries


def save_report(folder: Path, run: dict, judge=None) -> None:
    (folder / "report.md").write_text(report_text(run, judge), encoding="utf-8")


def print_summary(folder: Path, run: dict, judge=None) -> None:
    source = "DEMO: 작성된 예제, API 호출 0" if run["mode"] == "demo" else "LIVE: 실제 모델 응답"
    print(f"\n[{source}] {run['prompt_name']} / {run['split']}")
    rows = scored_rows(run)
    count = sum(row["passed"] for row in rows)
    print(f"업무 통과: {count}/{len(rows)} ({business_rate(run):.1%})")
    for row in rows:
        failures = ",".join(key for key, ok in row["checks"].items() if not ok) or "-"
        scores = ""
        if judge:
            values = judge["rows"][row["case_id"]]
            scores = "  " + " ".join(f"{m}={values[m]['score']}" for m in METRICS)
        print(f"  {row['case_id']} {'PASS' if row['passed'] else 'FAIL'}  {failures}{scores}")
    print(f"보고서: {folder / 'report.md'}")


def make_run(args) -> dict:
    if args.frozen:
        if args.split != "holdout" or args.data:
            raise ValueError("--frozen은 기본 holdout에만 사용합니다.")
        candidate = load_run(args.frozen)
        if candidate["mode"] != args.mode or candidate["split"] != "dev":
            raise ValueError("--frozen에는 같은 모드의 dev candidate를 지정하세요.")
        prompt_name, prompt = candidate["prompt_name"], candidate["prompt"]
        context, config = candidate["context"], candidate["config"]
        generation = candidate["generation_contract"]
        if args.mode == "live":
            from foundry_client import generation_contract
            if generation != generation_contract():
                raise ValueError("생성 설정/출력 계약이 candidate 실행 후 변경되었습니다.")
    else:
        if args.split == "holdout":
            raise ValueError("Holdout에는 --prompt 대신 --frozen results/candidate를 사용하세요.")
        prompt_file = ROOT / "prompts" / f"{args.prompt}.txt"
        if args.prompt not in ("v1", "v2", "shortcut"):
            prompt_file = Path(args.prompt)
        prompt_name = prompt_file.stem
        prompt = prompt_file.read_text(encoding="utf-8")
        if not prompt.strip():
            raise ValueError("빈 프롬프트는 사용할 수 없습니다.")
        context = (ROOT / "data" / "policies.md").read_text(encoding="utf-8")
        if args.mode == "live":
            from foundry_client import generation_contract, read_config
            config = read_config(args.config)
            generation = generation_contract()
        else:
            config = {"model": "authored-demo"}
            generation = {"source": "authored-demo", "version": "1"}
    split = "extra" if args.data else args.split
    cases = read_cases(args.data or ROOT / "data" / f"{split}.jsonl")
    run = {
        "schema_version": 1, "business_version": BUSINESS_VERSION,
        "run_id": uuid.uuid4().hex, "created_at": now(), "status": "collecting",
        "mode": args.mode, "split": split, "prompt_name": prompt_name,
        "prompt": prompt, "context": context, "cases": cases,
        "prompt_hash": digest(prompt), "context_hash": digest(context), "cases_hash": digest(cases),
        "config": config, "generation_contract": generation, "rows": [],
        "target_deployment": candidate["target_deployment"] if args.frozen else None,
    }
    if args.frozen:
        run["frozen_from"] = candidate["evidence_hash"]
    if args.mode == "demo":
        demo_entries(run)
    return run


def run_command(args) -> int:
    requested = make_run(args)
    folder = args.out
    if (folder / "run.json").exists():
        run = load_run(folder, complete=False)
        for field in (
            "mode", "split", "prompt_hash", "context_hash", "cases_hash",
            "config", "generation_contract", "business_version", "frozen_from",
        ):
            if run.get(field) != requested.get(field):
                raise ValueError(f"{folder}의 {field}가 다릅니다. 기존 결과를 덮어쓰지 말고 --out에 새 폴더를 지정하세요.")
        if run["status"] == "complete":
            run = load_run(folder)
            judge = load_judge(folder, run) if (folder / "judge.json").exists() else None
            print("기존의 완료된 결과를 읽었습니다. 새 모델 호출은 없습니다.")
            save_report(folder, run, judge)
            print_summary(folder, run, judge)
            return 0
        print(f"미완료 수집 재개: 저장된 {len(run['rows'])}개는 다시 호출하지 않습니다.")
    else:
        if folder.exists() and any(folder.iterdir()):
            raise ValueError(f"{folder}: 비어 있지 않은 폴더입니다. 새 결과 폴더를 사용하세요.")
        run = requested
        write_json(folder / "run.json", run)
    finished = {row["case_id"] for row in run["rows"]}
    if args.mode == "demo":
        examples = {entry["id"]: entry for entry in demo_entries(run)}
        connection = nullcontext((None, None))
        print("DEMO: 사람이 작성한 응답을 재생합니다. 모델 실행/프롬프트 개선의 증거가 아닙니다.")
    else:
        from foundry_client import clients
        connection = clients(run["config"])
        print(f"LIVE: 새 답변 {len(run['cases']) - len(finished)}개를 생성합니다. 유료 모델 호출입니다.", flush=True)
    with connection as (project, client):
        if args.mode == "live":
            from foundry_client import deployment_snapshot
            target = deployment_snapshot(project, run["config"]["model_deployment"])
            if run["target_deployment"] is not None and run["target_deployment"] != target:
                raise ValueError("응답 모델 배포 버전이 변경되었습니다. 이 실행을 재개하거나 고정 후보로 평가할 수 없습니다.")
            run["target_deployment"] = target
            write_json(folder / "run.json", run)
        for case in run["cases"]:
            if case["id"] in finished:
                continue
            if args.mode == "demo":
                response = examples[case["id"]]["response"]
                row = {
                    "response": response, "raw_response": json.dumps(response, ensure_ascii=False),
                    "output_error": None, "latency_ms": None, "usage": None, "model": "authored-demo",
                }
            else:
                from foundry_client import generate
                row = generate(client, run["config"], case["query"], run["context"], run["prompt"])
            row["case_id"] = case["id"]
            run["rows"].append(row)
            write_json(folder / "run.json", run)
            print(f"{len(run['rows'])}/{len(run['cases'])}  {case['id']} 저장", flush=True)
    run["status"] = "complete"
    run["evidence_hash"] = evidence_hash(run)
    write_json(folder / "run.json", run)
    save_report(folder, run)
    print_summary(folder, run)
    return 0


def judge_command(args) -> int:
    run = load_run(args.folder)
    reference_judge = None
    if args.like:
        reference = load_run(args.like)
        reference_judge = load_judge(args.like, reference)
        if reference["mode"] != run["mode"]:
            raise ValueError("--like에서 DEMO와 LIVE를 혼합할 수 없습니다.")
    if (args.folder / "judge.json").exists():
        judge = load_judge(args.folder, run)
        if reference_judge and judge_fingerprint(reference_judge) != judge_fingerprint(judge):
            raise ValueError("저장된 Judge가 --like의 평가 계약과 다릅니다.")
        print("저장된 Judge 결과를 읽었습니다. 재채점/추가 API 호출은 없습니다.")
    elif run["mode"] == "demo":
        entries = demo_entries(run)
        judge = {
            "source": "authored-demo", "evidence_hash": run["evidence_hash"],
            "contract": {
                "source": "authored-demo", "version": "1",
                "metrics": list(METRICS), "local_score_threshold": SCORE_THRESHOLD,
            },
            "rows": {entry["id"]: entry["judge"] for entry in entries},
        }
        print("DEMO: 점수와 이유도 사람이 작성한 교육용 예제입니다. LLM judge를 실행하지 않았습니다.")
    else:
        from foundry_client import judge_run
        print(f"LIVE: 저장된 답변 {len(run['cases'])}개 × 평가기 2개. 응답을 다시 생성하지 않습니다.", flush=True)
        judge = judge_run(run, args.folder, like=args.like, wait_seconds=args.wait_seconds)
        if judge is None:
            return 3
    validate_judge(judge, run)
    if reference_judge and judge_fingerprint(reference_judge) != judge_fingerprint(judge):
        raise ValueError("--like의 고정된 평가 계약과 일치하지 않습니다.")
    write_json(args.folder / "judge.json", judge)
    save_report(args.folder, run, judge)
    print_summary(args.folder, run, judge)
    if judge.get("report_url"):
        print(f"Foundry 보고서: {judge['report_url']}")
    return 0


def inspect_command(args) -> int:
    run = load_run(args.folder)
    matches = [row for row in scored_rows(run) if row["case_id"] == args.case_id]
    if not matches:
        raise ValueError(f"이 실행에 {args.case_id}가 없습니다.")
    row = matches[0]
    print(f"[{run['mode'].upper()}] {args.case_id} / {row['case']['category']}")
    print(f"질문: {row['case']['query']}")
    print(f"기대 행동: {row['case']['ground_truth']}")
    print(json.dumps(row["response"], ensure_ascii=False, indent=2))
    print("업무 검사:", json.dumps(row["checks"], ensure_ascii=False))
    if row.get("output_error"):
        print(f"출력 오류: {row['output_error']}\n원문: {row['raw_response']}")
    if (args.folder / "judge.json").exists():
        judge = load_judge(args.folder, run)
        for metric, value in judge["rows"][args.case_id].items():
            print(f"{metric}: {value['score']}/5 — {value['reason']}")
    else:
        print("Judge: 아직 미평가")
    return 0


def compare_command(args) -> int:
    left, right = load_run(args.baseline), load_run(args.candidate)
    has_judges = [(p / "judge.json").exists() for p in (args.baseline, args.candidate)]
    if any(has_judges) and not all(has_judges):
        raise ValueError("한쪽에만 Judge 결과가 있습니다. 다른 쪽도 judge로 평가한 뒤 비교하세요.")
    left_judge = load_judge(args.baseline, left) if all(has_judges) else None
    right_judge = load_judge(args.candidate, right) if all(has_judges) else None
    diff = comparison(left, right, left_judge, right_judge)
    judge_regressions = "미평가"
    if diff["judge_compared"]:
        judge_regressions = ", ".join(r["id"] for r in diff["judge_regressions"]) or "없음"
    lines = [
        "# 같은 질문의 전후 비교", "", f"**{left['mode'].upper()}**",
        f"업무 통과율: {diff['before_rate']:.1%} -> {diff['after_rate']:.1%}",
        f"새로 통과한 사례: {', '.join(diff['improvements']) or '없음'}",
        "업무 검사 회귀: " + (", ".join(r["id"] + "(" + "/".join(r["checks"]) + ")" for r in diff["regressions"]) or "없음"),
        "Judge 합격→불합격 회귀: " + judge_regressions,
        f"Judge 비교: {'포함' if diff['judge_compared'] else '미포함 — 업무 검사만 비교'}",
        "", "**통과율이 높아졌어도 중요한 사례가 나빠졌다면 개선으로 승인하지 않습니다.**",
        "Dev와 holdout은 질문이 다르므로 전후 비교 대상이 아닙니다.", "",
        "| 사례 | Baseline 업무 | Candidate 업무 |",
        "|---|---|---|",
    ]
    before_rows = {row["case_id"]: row for row in scored_rows(left)}
    for row in scored_rows(right):
        case_id = row["case_id"]
        lines.append(
            f"| {case_id} | {'PASS' if before_rows[case_id]['passed'] else 'FAIL'} "
            f"| {'PASS' if row['passed'] else 'FAIL'} |"
        )
    text = "\n".join(lines) + "\n"
    (args.candidate / "comparison.md").write_text(text, encoding="utf-8")
    write_json(args.candidate / "comparison.json", diff)
    print("\n".join(lines[:10]))
    print(f"비교표: {args.candidate / 'comparison.md'}")
    return 0


def review_command(args) -> int:
    run = load_run(args.folder)
    if args.case_id not in {case["id"] for case in run["cases"]}:
        raise ValueError(f"이 실행에 {args.case_id}가 없습니다.")
    if args.verdict is None or args.note is None:
        inspect_command(args)
        try:
            args.verdict = args.verdict or input("사람의 판정 (pass/fail): ").strip()
            args.note = args.note or input("근거 문서와 답변을 비교한 이유: ").strip()
        except EOFError as exc:
            raise ValueError("검토 입력이 없습니다. 대화형 터미널을 쓰거나 --verdict와 --note를 지정하세요.") from exc
    if args.verdict not in ("pass", "fail"):
        raise ValueError("사람의 판정은 pass 또는 fail입니다.")
    if len(args.note.strip()) < 5:
        raise ValueError("검토 이유를 5자 이상으로 기록하세요. 결론뿐 아니라 근거가 필요합니다.")
    path = args.folder / "reviews.json"
    reviews = read_json(path) if path.exists() else []
    if not isinstance(reviews, list):
        raise ValueError("기존 reviews.json이 배열이 아닙니다. 덮어쓰지 않습니다.")
    reviews.append({
        "case_id": args.case_id, "verdict": args.verdict, "note": args.note.strip(),
        "evidence_hash": run["evidence_hash"], "created_at": now(),
    })
    write_json(path, reviews)
    print(f"검토 저장: {path} ({args.case_id}: {args.verdict}). 모델을 학습하거나 점수를 변경하지 않습니다.")
    return 0


def gate_command(args) -> int:
    result = gate(args.baseline, args.candidate, args.holdout)
    write_json(args.candidate / "gate.json", result)
    text = f"# {result['status']}\n\n{result['note']}\n\n"
    text += "\n".join(f"- {problem}" for problem in result["problems"]) or "모든 교육용 기준을 충족했습니다."
    (args.candidate / "gate.md").write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\n판정 기록: {args.candidate / 'gate.md'}")
    return 2 if result["status"] == "BLOCK" else 0


def doctor_command(args) -> int:
    if sys.version_info < (3, 10):
        raise ValueError("Python 3.10 이상이 필요합니다.")
    dev, holdout = [read_cases(ROOT / "data" / f"{name}.jsonl") for name in ("dev", "holdout")]
    if {case["id"] for case in dev} & {case["id"] for case in holdout}:
        raise ValueError("Dev/holdout의 ID가 겹칩니다.")
    print(f"LOCAL OK: Python {sys.version.split()[0]}, dev {len(dev)}개, holdout {len(holdout)}개")
    print("DEMO는 Python 표준 라이브러리만 사용합니다. 설치·Azure 로그인·네트워크가 필요 없습니다.")
    if args.live:
        from importlib.metadata import PackageNotFoundError, version
        try:
            for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
                package, pinned = line.split("==")
                actual = version(package)
                if actual != pinned:
                    raise ValueError(f"{package}: {actual} 설치됨, 수업 고정 버전은 {pinned}입니다.")
        except PackageNotFoundError as exc:
            raise RuntimeError("python -m pip install -r requirements.txt 로 LIVE 의존성을 설치하세요.") from exc
        from foundry_client import clients, deployment_snapshot, read_config
        config = read_config(args.config)
        with clients(config) as (project, _):
            for key in ("model_deployment", "judge_deployment"):
                snapshot = deployment_snapshot(project, config[key])
                print(f"LIVE 조회 OK: {key}={snapshot['name']} / {snapshot['model_name']} / {snapshot['model_version']}")
        print("로그인과 배포 조회만 확인했습니다. 실제 답변 생성/평가는 run과 judge로 확인하세요.")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Evaluation 실습. LIVE와 DEMO는 자동 전환되지 않습니다.")
    sub = root.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="로컬 준비 확인; --live는 로그인/배포 조회")
    doctor.add_argument("--live", action="store_true")
    doctor.add_argument("--config", type=Path, default=Path("config.json"))
    doctor.set_defaults(handler=doctor_command)
    run = sub.add_parser("run", help="답변 수집 + 무료 업무 규칙 검사")
    run.add_argument("--mode", choices=("demo", "live"), required=True)
    source = run.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", help="v1/v2/shortcut 또는 직접 작성한 프롬프트 파일")
    source.add_argument("--frozen", type=Path, help="Holdout에 사용할 dev candidate 결과 폴더")
    run.add_argument("--split", choices=("dev", "holdout"), default="dev")
    run.add_argument("--data", type=Path, help="추가 질문 JSONL. 본 실험과 분리해 extra로 기록")
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--config", type=Path, default=Path("config.json"))
    run.set_defaults(handler=run_command)
    judge = sub.add_parser("judge", help="저장된 답변 채점; LIVE이면 Foundry 클라우드 평가")
    judge.add_argument("folder", type=Path)
    judge.add_argument("--like", type=Path, help="이전 실행의 동일 Judge/평가기/Foundry 평가 그룹 재사용")
    judge.add_argument("--wait-seconds", type=int, default=300)
    judge.set_defaults(handler=judge_command)
    inspect = sub.add_parser("inspect", help="사례 하나의 질문/기대 행동/실제 답변/점수")
    inspect.add_argument("folder", type=Path)
    inspect.add_argument("case_id")
    inspect.set_defaults(handler=inspect_command)
    compare = sub.add_parser("compare", help="동일 dev 데이터의 짝 비교와 회귀 탐지")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.set_defaults(handler=compare_command)
    review = sub.add_parser("review", help="사람의 판정과 근거 저장")
    review.add_argument("folder", type=Path)
    review.add_argument("case_id")
    review.add_argument("--verdict", choices=("pass", "fail"))
    review.add_argument("--note")
    review.set_defaults(handler=review_command)
    release = sub.add_parser("gate", help="회귀/holdout/P0/Judge/사람 검토에 기반한 교육용 판단")
    release.add_argument("baseline", type=Path)
    release.add_argument("candidate", type=Path)
    release.add_argument("holdout", type=Path)
    release.set_defaults(handler=gate_command)
    return root


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if getattr(args, "wait_seconds", 0) < 0:
            raise ValueError("--wait-seconds는 0 이상이어야 합니다.")
        return args.handler(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n중단했습니다. 저장된 결과는 보존됩니다. 같은 명령으로 재개하세요.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

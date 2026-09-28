#!/usr/bin/env python3
"""Recorded failure-to-acceptance profile, independent of retired run records."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.media import workshop_video as media

PRIVATE = ROOT / "results" / "media-success"
OUTPUT = ROOT / "docs" / "media" / "complete-rag"
PREFIX = "completion-summary"
SCENES = [
    {
        "id": "success-01-service", "kind": "portal", "seconds": 18,
        "en": ["One Search service for every retrieval exercise", "The same Basic service hosts the simple text index and the vector/planned knowledge base. Managed identity enables keyless embedding and planner calls."],
        "ko": ["검색 서비스 하나로 모든 검색 실습", "같은 Basic 서비스에 기본 텍스트 인덱스와 벡터·계획형 지식 기반을 둡니다. 관리 ID로 임베딩과 계획 모델을 키 없이 호출합니다."],
    },
    {
        "id": "success-02-baseline", "kind": "terminal", "seconds": 24,
        "label": "Saved calibration and genuine recorded V1",
        "en": ["Start with a real failure, not a fabricated one", "The calibrated judge separates ten positive/negative controls. The recorded V1 D02 still fails its exact citation contract. No baseline answer was weakened."],
        "ko": ["억지 오답이 아닌 실제 실패에서 시작", "교정된 Judge는 정상·오답 10개를 구분했습니다. 기록된 V1 D02의 출처 계약 실패를 그대로 보존하며 V1을 일부러 약화하지 않았습니다."],
        "commands": [
            "python advanced_lab.py calibrate",
            "python advanced_lab.py inspect --stage v1-recorded --case-id D02",
        ],
    },
    {
        "id": "success-03-prompt", "kind": "terminal", "seconds": 22,
        "label": "Explicit user follow-ups · fixed final-answer criteria",
        "en": ["Complete the user task, not just the first turn", "V2 selects precise sources and completes necessary user follow-ups. The user supplies the missing date; the assistant does not invent it. Final-answer Relevance is required."],
        "ko": ["첫 응답이 아니라 사용자 업무를 완료", "V2는 정확한 출처를 선택하고 필요한 후속 대화까지 마칩니다. 빠진 날짜는 사용자가 제공하며 모델이 만들지 않습니다. 최종 Relevance도 필수입니다."],
        "commands": [
            "python advanced_lab.py inspect --stage v2-replay --case-id D02",
            "python advanced_lab.py inspect --stage v2-replay --case-id D08 --dialogue",
        ],
    },
    {
        "id": "success-04-retrieval", "kind": "terminal", "seconds": 28,
        "label": "Fresh vector and LLM-planned retrieval",
        "en": ["Prove the advanced retrieval actually runs", "The vector-only query uses 1536 dimensions. Foundry IQ returns modelQueryPlanning activity and generated subqueries. This is not minimal retrieval relabeled."],
        "ko": ["벡터와 LLM 검색 계획의 실제 실행", "벡터 전용 조회는 1536차원을 사용합니다. Foundry IQ가 modelQueryPlanning과 생성한 하위 질의를 반환합니다. 최소 검색에 이름만 바꾼 것이 아닙니다."],
        "commands": [
            'python advanced_lab.py query --mode vector --query "해외 출장 호텔 숙박비 상한을 확인하고 싶습니다." --out results/advanced/video-vector-query.json',
            'python advanced_lab.py query --mode planned --query "과거와 현재 국내 숙박 한도, 초과 승인 절차, 해외 호텔비 한도를 비교해 주세요." --out results/advanced/video-planned-query.json',
        ],
    },
    {
        "id": "success-05-knowledge", "kind": "portal", "seconds": 18,
        "en": ["Inspect the real planned knowledge base", "The active source points at the vector index. The supported planner is gpt-5.4-mini; gpt-6-luna remains the answer and judge model. Preview API use is explicit."],
        "ko": ["실제 계획형 Knowledge Base 확인", "활성 소스는 벡터 인덱스를 사용합니다. 지원되는 계획 모델은 gpt-5.4-mini이고 답변·평가는 gpt-6-luna입니다. Preview API 사용을 명시합니다."],
    },
    {
        "id": "success-06-acceptance", "kind": "terminal", "seconds": 28,
        "label": "Fresh holdout evidence · no regrading",
        "en": ["Freeze first, then test fresh scenarios", "New scenarios are created after freezing. Every final case must pass business, retrieval, Groundedness, Relevance and policy task success. No metric is excluded."],
        "ko": ["먼저 고정하고 새 시나리오로 확인", "고정한 뒤 새 시나리오를 만듭니다. 최종 사례 모두 업무·검색·Groundedness·Relevance·업무 성공도를 통과해야 합니다. 지표를 제외하지 않습니다."],
        "commands": [
            "python advanced_lab.py inspect --stage holdout --case-id N05",
            "python advanced_lab.py accept",
        ],
    },
    {
        "id": "success-07-portal", "kind": "portal", "seconds": 22,
        "en": ["Keep the proof and distinguish approval", "The completed cloud run preserves original answers and reasons. LAB_ACCEPTANCE_PASSED is an educational result, not human production authorization."],
        "ko": ["증거를 보존하고 운영 승인과 구분", "완료된 클라우드 실행에 원본 답변·점수 이유를 보존합니다. LAB_ACCEPTANCE_PASSED는 교육용 결과이며 사람의 운영 승인을 뜻하지 않습니다."],
    },
]


def context() -> dict:
    resources = media.load(ROOT / "results" / "advanced" / "resources.json")
    current = json.loads(subprocess.check_output(["az", "account", "show", "-o", "json"], text=True))
    if current["id"] != resources["subscription"] or current["user"]["name"].casefold() != resources["account"].casefold():
        raise ValueError("Current Azure identity differs from the verified complete-lab identity.")
    search = resources["search"]
    portal = f"https://portal.azure.com/#@{resources['tenant']}/resource{search['id']}"
    judge = media.load(ROOT / "results" / "advanced" / "holdout" / "judge.json")
    return {
        "subscription": resources["subscription"], "tenant": resources["tenant"],
        "group": resources["resource_group"], "account": resources["foundry_account"],
        "search": search["name"],
        "redact": [
            resources["account"], resources["display_name"], resources["subscription"],
            resources["tenant"], resources["subscription_name"], resources["account"].split("@")[-1],
            resources["account"].split("@")[0], Path.home().name,
        ],
        "urls": {
            "success-01-service": portal + "/indexes",
            "success-05-knowledge": portal + "/knowledgeBases",
            "success-07-portal": judge["report_url"] + "?tid=" + resources["tenant"],
        },
    }


def main() -> None:
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("serve", "prepare", "run", "render", "verify"))
    parser.add_argument("scene", nargs="?", choices=[scene["id"] for scene in SCENES])
    args = parser.parse_args()
    if args.action == "serve":
        media.serve(scenes=SCENES, private=PRIVATE)
    elif args.action == "prepare":
        if not args.scene:
            parser.error("A scene is required.")
        media.prepare(args.scene, scenes=SCENES, private=PRIVATE, context=context())
    elif args.action == "run":
        if not args.scene:
            parser.error("A scene is required.")
        media.run_scene(args.scene, scenes=SCENES, private=PRIVATE)
    elif args.action == "render":
        media.render(scenes=SCENES, private=PRIVATE, output=OUTPUT, prefix=PREFIX, topic="success", recorded_on=None)
    else:
        media.verify(output=OUTPUT, scene_count=len(SCENES), prefix=PREFIX, expected_marker="LAB_ACCEPTANCE_PASSED")


if __name__ == "__main__":
    main()

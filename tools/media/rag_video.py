#!/usr/bin/env python3
"""Optional RAG recording profile; preserves the core workshop videos."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.media import workshop_video as media

PRIVATE = ROOT / "results" / "media-rag"
OUTPUT = ROOT / "docs" / "media" / "optional-rag"
PREFIX = "rag-summary"
QUESTION = "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?"
SCENES = [
    {
        "id": "rag-01-service", "kind": "portal", "seconds": 18,
        "en": ["Real Search, real knowledge", "The dedicated Search service is in Sweden Central. Its Free plans and keyless access are retained; the base workshop resources are unchanged."],
        "ko": ["실제 Search와 지식 리소스", "전용 Search 서비스는 Sweden Central에 있습니다. Free 요금제와 키 없는 접근을 유지하며 기본 실습 리소스는 변경하지 않습니다."],
    },
    {
        "id": "rag-02-search", "kind": "terminal", "seconds": 22,
        "label": "Live Search retrieval · no answer regeneration",
        "en": ["Retrieve before generating", "Seven chunks are indexed. The unapproved draft is filtered out. Search returns actual ranked chunks, not the complete policy pasted into a prompt."],
        "ko": ["답변 전에 실제 검색", "청크 7개를 인덱싱하고 미승인 초안은 필터로 제외합니다. 전체 규정을 붙여 넣는 대신 실제 검색된 청크를 사용합니다."],
        "commands": [
            "python rag_lab.py setup",
            f'python rag_lab.py query --mode search --query "{QUESTION}" --out results/rag-video-query-search.json',
        ],
    },
    {
        "id": "rag-03-knowledge", "kind": "portal", "seconds": 20,
        "en": ["Foundry IQ is an actual knowledge base", "The knowledge base references a real search-index knowledge source. This GA path is minimal and extractive: no vector embeddings or LLM query planning."],
        "ko": ["Foundry IQ의 실제 Knowledge Base", "실제 검색 인덱스 Knowledge Source를 연결한 지식 기반입니다. 정식 추출형 경로이며 벡터 임베딩과 LLM 쿼리 계획은 사용하지 않습니다."],
    },
    {
        "id": "rag-04-iq", "kind": "terminal", "seconds": 26,
        "label": "Live IQ retrieval + saved LIVE answer",
        "en": ["Query IQ and inspect the saved answer", "IQ returns references and activity. D02 used the correct limit but added an extra source ID. Successful retrieval does not guarantee every answer check."],
        "ko": ["IQ 조회와 저장된 답변 확인", "IQ는 참조와 검색 활동을 반환합니다. D02는 한도는 맞았지만 출처 ID를 하나 더 인용했습니다. 검색 성공이 답변의 모든 검사를 보장하지는 않습니다."],
        "commands": [
            f'python rag_lab.py query --mode iq --query "{QUESTION}" --out results/rag-video-query-iq.json',
            "python lab.py inspect results/rag-iq D02",
        ],
    },
    {
        "id": "rag-05-evaluation", "kind": "portal", "seconds": 22,
        "en": ["Judge the context the model actually saw", "Groundedness uses each answer's retrieved context, not the full corpus. Read the same case, answer and reason in the completed Foundry evaluation."],
        "ko": ["모델이 실제로 본 문맥으로 평가", "Groundedness는 전체 코퍼스가 아니라 각 답변에 사용한 검색 문맥으로 평가합니다. 완료된 Foundry 실행에서 같은 사례·답변·이유를 대조합니다."],
    },
    {
        "id": "rag-06-compare", "kind": "terminal", "seconds": 28,
        "label": "Retained LIVE RAG evaluations · no regrading",
        "en": ["Compare evidence, not marketing", "Both routes retrieved identical context with 100% required-chunk recall. One run's answer differences do not prove a superior retriever. REVIEW_REQUIRED; retain the evidence."],
        "ko": ["주장이 아니라 증거를 비교", "두 경로의 검색 문맥은 같고 필수 청크 재현율은 100%입니다. 한 번의 답변 차이로 검색기의 우열을 단정하지 않습니다. REVIEW_REQUIRED와 원본을 유지합니다."],
        "commands": [
            "python lab.py judge results/rag-iq --like results/rag-search",
            "python rag_lab.py compare results/rag-search results/rag-iq",
        ],
    },
]


def context() -> dict:
    result = media.project_context()
    search = media.load(ROOT / "results" / "rag-resources.json")
    prefix = f"/subscriptions/{result['subscription']}/resourceGroups/{result['group']}/"
    if not search["id"].casefold().startswith(prefix.casefold()):
        raise ValueError("Search resource is outside the verified workshop scope.")
    judge = media.load(ROOT / "results" / "rag-iq" / "judge.json")
    portal = f"https://portal.azure.com/#@{result['tenant']}/resource{search['id']}/overview"
    result["search"] = search["name"]
    result["urls"] = {
        "rag-01-service": portal,
        "rag-03-knowledge": portal.removesuffix("/overview") + "/knowledgeBases",
        "rag-05-evaluation": judge["report_url"] + "?tid=" + result["tenant"],
    }
    return result


def main() -> None:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="Record/edit the isolated optional RAG video profile.")
    parser.add_argument("action", choices=("serve", "prepare", "run", "render", "verify"))
    parser.add_argument("scene", nargs="?", choices=[scene["id"] for scene in SCENES])
    args = parser.parse_args()
    if args.action == "serve":
        media.serve(scenes=SCENES, private=PRIVATE)
    elif args.action == "prepare":
        if not args.scene:
            parser.error("A scene ID is required.")
        media.prepare(args.scene, scenes=SCENES, private=PRIVATE, context=context())
    elif args.action == "run":
        if not args.scene:
            parser.error("A scene ID is required.")
        media.run_scene(args.scene, scenes=SCENES, private=PRIVATE)
    elif args.action == "render":
        media.render(scenes=SCENES, private=PRIVATE, output=OUTPUT, prefix=PREFIX, topic="rag", recorded_on=None)
    else:
        media.verify(output=OUTPUT, scene_count=len(SCENES), prefix=PREFIX, expected_marker="REVIEW_REQUIRED")


if __name__ == "__main__":
    main()

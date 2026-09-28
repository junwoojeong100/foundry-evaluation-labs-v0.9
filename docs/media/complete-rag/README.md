# Completed workflow recordings / 완결형 실습 요약 영상

[English guide](../../en/complete-lab.md) · [국문 가이드](../../complete-lab.md)

These are the **September 28, 2026 fresh-environment** summaries: **2 minutes 54 seconds each**, 1080p H.264, with English/Korean burned-in captions and SRT files. **No narration or music.**

| Language | Video | Subtitles |
|---|---|---|
| English | [Watch / download](completion-summary.en.mp4) | [English SRT](completion-summary.en.srt) |
| 한국어 | [보기 / 다운로드](completion-summary.ko.mp4) | [국문 SRT](completion-summary.ko.srt) |

[![Completed English workflow](completion-summary.en.png)](completion-summary.en.mp4)

[![완결형 국문 실습](completion-summary.ko.png)](completion-summary.ko.mp4)

If GitHub opens a file page, use **View raw / Download** to play the MP4.

## What is real, and what is scripted?

The complete execution was recorded with headless Playwright, starting before resource-group creation. Seven selected native captures form this summary: the **original creation footage**, actual Azure/Foundry portal views, and real CLI inspection of the new results. A new Foundry resource/project, three model deployments, and one Basic Search service were provisioned. The service has a populated 1536-dimensional vector index, a vectorizer, and real Foundry IQ `modelQueryPlanning` activity.

The V1 failure is a preserved, sanitized actual earlier model response, not an invented bad answer. Those four V1 answers were freshly judged: Relevance passed at **50%**, rather than copying the previous run's 100%. V2 responses and evaluations ran live, and eight fresh scenarios were generated once after freezing. Summary takes read completed evaluation evidence and perform fresh retrieval demonstrations; they do not reroll model scores. The shared setup also generated and evaluated one fresh N01 case, not the full introductory workshop.

Two evaluation scenarios use **explicit scripted user follow-ups**: one supplies a missing travel date after the assistant asks, and another requests a supported Finance inquiry checklist rather than an unavailable overseas amount. These are authored test-user turns, not facts fabricated by the assistant or real human approvals.

**In this recorded run, every final V2 holdout case passed business, retrieval, Groundedness, builtin Relevance, and policy task success.** No failed metric was excluded, and no score was overwritten. Initial clarification/handoff checks cover format, decision, amount, and citations only—not a separate semantic evaluation of the initial prose. Read the dialogues as described in the current guide. Human production approval is still separate.

This is not a reproduction guarantee or validation of the separate introductory LIVE/minimal-RAG paths. Use the current written guide for setup, recovery, and your own run's acceptance decision.

Native capture is 1280 × 720, composed with 1080p cards/captions. Editing trims waits and adjusts speed. Privacy bars are opaque; identifiers and container metadata are removed from published footage. Raw recordings and local configuration are not committed.

## Chapters

| Start | Topic |
|---|---|
| 00:00 | Introduction |
| 00:07 | Actual creation of the new Azure resource group |
| 00:25 | Calibrated evaluation and the genuine V1 failure |
| 00:49 | V2 source selection and completed user follow-up |
| 01:11 | Actual vectors and LLM-planned search |
| 01:39 | Planned knowledge-base configuration |
| 01:57 | Fresh frozen scenarios and all-metrics acceptance |
| 02:25 | Completed Foundry evaluation |
| 02:47 | Closing and production-approval distinction |

## 국문 안내

**새 리소스 그룹 생성 전부터 전체 실행을 headless로 녹화**하고, 실제 그룹 생성 원본·포털·새 결과를 읽는 CLI 화면 7개를 국문·영문으로 편집했습니다. Foundry·세 모델 배포·Basic Search를 새로 준비했고, **실제 1536차원 벡터 인덱스와 LLM 검색 계획**을 사용합니다.

V1의 실제 이전 응답을 새로 채점했으며, 이번 Relevance 통과율은 **50%**입니다. V2는 새로 생성·평가하고 필요한 사용자 후속 대화까지 완료했습니다. 날짜나 회사 규정을 모델이 만들어 낸 것이 아닙니다. 후속 사용자 발언은 명시된 평가용 데이터입니다. 공통 준비의 N01도 한 건 새로 실행했지만 입문 전체의 재검증은 아닙니다.

**이 녹화의 새 V2 최종 사례 8개 모두 Relevance를 포함한 모든 필수 지표를 통과**했습니다. 초기 검사는 형식·결정·금액·출처에 한정되며, 초기 설명 문장의 별도 의미 평가를 뜻하지 않습니다. 현재 가이드처럼 대화를 직접 읽고 판단합니다. 점수를 바꾸거나 실패 지표를 빼지 않았으며 실제 운영 승인은 별도입니다.

이는 재현 보장이나 별도 입문 LIVE·최소 RAG의 재검증이 아닙니다. 준비·복구·본인 실행의 합격 판단은 현재 문서의 절차를 따릅니다.

소유자의 명시적 요청으로 이전 실습 그룹의 삭제를 확인한 뒤 새 환경에서 실행했습니다. 이전 로컬 결과·원본 영상은 보관했고 새 리소스와 이번 교정·V1/V2·holdout 증거는 유지합니다. 비용 조회에는 아직 행이 없어 집계 대기로 기록했으며 무료라는 뜻이 아닙니다. 참가자의 추가 삭제 단계가 아닙니다.

## Authoring

The [success profile](../../../tools/media/success_video.py) uses the shared local recorder/editor. Authoring requires the private current-run artifacts, FFmpeg, Pillow, Bash, and a Korean-capable font; none is required to watch.

The first chapter consumes the original `rerun-00-group` capture and command timestamps; the authoring tool refuses to recreate resources merely to film a summary. Other chapters use the current run's captures. Chapter `source_recording_id` fields in the manifest identify the source scenes. Raw footage, private browser diagnostics, and authentication state are not published.

```bash
python tools/media/success_video.py render
```

```bash
python tools/media/success_video.py verify
```

The [manifest](manifest.json) contains hashes, sizes, durations, and chapter times. Full decoding, browser playback/seeking, subtitle timing, frame readability and identifier redaction must be checked before publishing.

[English](en/reference.md) | **한국어**

# 명령·평가 계약·문제 해결·출처

[메인 가이드](../README.ko.md) · [환경 준비 바로가기](setup.md) · [리소스 정리](cleanup.md)

기본 LIVE 경로의 준비·명령·완료 확인·정리는 모두 [README](../README.ko.md)에 있습니다. 이 문서를 처음부터 읽을 필요는 없습니다. 막히거나 결과를 정확히 해석해야 할 때 찾아봅니다.

아래 명령표는 `lab.py` 입문 경로용입니다. `advanced_lab.py`의 명령 상태·고정 출력 경로는 [완결형 재개 안내](complete-lab.md#resume)를 사용합니다. 원격 평가 ID 복구는 아래에서 경로별 파일을 구분합니다.

기본 경로에서 **환경 소유자는 참가자 본인**입니다. 본인 전용 자원의 설정·권한은 직접 확인하고, 조직 정책이나 공유 자원에 관한 결정만 해당 관리 담당자와 확인합니다.

## 명령은 여덟 가지

| 명령 | 역할 | 유료 호출 |
|---|---|---|
| `doctor` | 로컬 데이터와 Python 확인. `--live`는 로그인/모델 배포 조회 | 생성/평가 호출 없음 |
| `validate-data` | 질문 JSONL의 문법·필수 필드·값 형식 검사. 파일 변경 없음 | 없음 |
| `run` | 답변 생성·저장 + 무료 업무 검사 | LIVE의 아직 저장되지 않은 응답 |
| `judge` | 저장된 답변의 두 품질 평가 | LIVE에서 새 평가 실행을 제출할 때 |
| `inspect` | 사례 하나의 질문·기대 행동·응답·판정 읽기 | 없음 |
| `compare` | 동일 dev의 전후 차이와 회귀 확인 | 없음 |
| `review` | 실제 답변의 판정과 이유 저장. 사람과 AI 보조 검토를 구분 | 없음 |
| `gate` | 고정 기준으로 교육용 채택 검토/보류 판단 | 없음 |

`--help`로 명령 또는 각 하위 명령의 도움말을 볼 수 있습니다. 예:

```bash
python lab.py run --help
```

**종료 코드:** `0` 명령 완료, `1` 입력/환경/실행 오류, `2` Gate 차단, `3` Foundry 평가 대기 중, `130` 사용자가 중단.

`2`는 **`BLOCK`이 함께 출력됐을 때** Gate 차단입니다. `usage:` / `error:`와 함께 나오면 필수 인자 누락·잘못된 옵션 등 명령 인자 오류이므로 고쳐 재실행합니다.

`run`이 0으로 끝나도 응답이 업무 검사에서 실패할 수 있습니다. “실험을 수집했다”와 “답이 맞다”를 구분합니다.

`judge`의 **`평가 완료: N개 답변 × 2개 지표 (점수·이유 저장)`**는 전체 사례 ID와 두 점수·이유가 유효하고 `judge.json`·`report.md`까지 저장된 뒤 출력됩니다. **낮은 점수도 유효한 평가 결과**이므로 완료 메시지가 나옵니다. 원격 상태 `completed`나 파일 존재만으로 대신 판단하지 않습니다. 저장된 결과를 재사용할 때도 검증 후 같은 완료 메시지가 나오며, 재채점은 하지 않습니다.

<a id="data-contract"></a>
## 데이터 한 줄 읽기

`data/dev.jsonl`과 추가 사례 예제는 **한 줄에 JSON 객체 하나**입니다. 필드 이름을 추가하거나 지우지 않고, 새 질문에 맞는 값을 넣습니다. [실습 6](../README.ko.md#lab-6)의 N02 예제와 로컬 검사 명령으로 시작할 수 있습니다.

```bash
python lab.py validate-data data/my-case.jsonl
```

`DATA OK: 1 case(s)`는 한 건의 파일 형식이 유효하다는 뜻이며 정답의 타당성이나 모델 성능을 보장하지 않습니다. 이 명령은 Azure 로그인·패키지 설치 없이 실행할 수 있고, 입력 파일을 수정하거나 결과 폴더를 만들지 않습니다. 여러 사례를 넣으면 검사한 전체 건수를 출력합니다. 잘못된 입력은 `ERROR:`와 종료 코드 `1`로 알립니다.

| 필드 | 뜻과 예 |
|---|---|
| `id` | 사례 식별자. 새 사례는 `N02`처럼 영문자로 시작 |
| `category` | 확인하려는 유형. 예: `"사전 승인"` |
| `critical` | 반드시 지켜야 하는 중요 사례인지 `true`/`false`로 표시 |
| `query` | 직원이 묻는 질문 |
| `expected_decision` | 기대 결정. `allowed`, `needs_approval`, `not_allowed`, `unknown`, `needs_info` 중 하나 |
| `expected_limit_krw` | 기대 숙박 한도. 정수 `200000` 또는 결정할 수 없으면 `null` |
| `expected_citations` | 필요한 공식 문서 ID의 배열. 예: `["TRAVEL-CURRENT"]` |
| `ground_truth` | 사람이 정한 기대 행동과 그 이유. 답변 모델이나 이번 두 Judge에는 전달하지 않음 |

숫자에 쉼표나 따옴표를 넣지 않습니다. 공식 문서 ID는 `TRAVEL-CURRENT`, `TRAVEL-PREVIOUS`, `SCOPE`이며, 질문에 필요한 문서만 선택합니다. 정답 설명도 사람이 틀리게 작성할 수 있으므로 실행 전에 규정과 대조합니다.

예를 들어 D02에 기대하는 답변 형태는 다음과 같습니다. 아래는 설명용 예이며 실제 모델 응답이 아닙니다.

```json
{
  "decision": "needs_approval",
  "limit_krw": 200000,
  "citations": ["TRAVEL-CURRENT"],
  "answer": "220000원은 한도 200000원을 초과하므로 재무팀 사전 승인이 필요합니다."
}
```

질문 파일의 `expected_*`와 모델이 생성한 답변 필드를 혼동하지 않습니다.

## 무엇을 평가하고 무엇은 평가하지 않는가

| 신호 | 정확한 의미 |
|---|---|
| `schema` | 네 필드만 있는 JSON 객체. decision 허용 값, 정수/null 한도, 문자열 배열 출처, 비어 있지 않은 설명 |
| `decision` | 사람이 작성한 기대 결정과 정확히 일치 |
| `limit` | 기대 한도와 정확히 일치. 문자열 `"200000"`과 숫자 `200000`, `true`와 숫자는 구별 |
| `citations` | 기대 출처 ID 집합과 정확히 일치. 빠진 출처·불필요한 출처·중복 출처는 실패 |
| 업무 통과 | 위 네 항목 모두 통과. 출력이 잘렸거나 거절된 경우도 실패 |
| Groundedness | 제공된 context에 답변이 근거하는지 판단하는 LLM 평가 |
| Relevance | 질문에 적절히 대응하는지 판단하는 LLM 평가 |
| 사람 검토 | 실제 응답과 규정의 일치·모순·업무 위험을 사람이 판단한 기록 |

`allowed`는 규정상 허용, `needs_approval`은 사전 승인 필요, `not_allowed`는 금지, `unknown`은 규정에 없음, `needs_info`는 질문 정보 부족입니다. 이 값이 실제 승인·환불·결제를 실행하지는 않습니다.

**의도된 한계:** 코드 검사는 `answer` 문장의 의미를 이해하지 않습니다. 결정 필드는 `needs_approval`인데 설명에는 “승인 완료”라고 쓰는 모순을 코드 검사만으로 막지 못합니다. 반대로 Judge는 정확한 출처 ID나 모든 날짜 조건을 놓칠 수 있습니다.

다음은 **고정 규정 입문 경로**의 증거 범위가 아닙니다: 검색 recall/NDCG, 도구 호출 정확성, Hosted Agent 동작, 멀티턴 대화, 일반적인 보안 검증, 광범위한 red teaming, 실제 업무 실행 권한, 운영 SLA. 최소 RAG의 검색 지표와 완결형의 대화·합격 기준은 각 전용 가이드에서 확인하며 아래 입문 Gate에 합치지 않습니다.

## 실험의 통제와 결과 해석

- 답변 모델은 **프롬프트 + 규정 + 질문**만 받습니다. 정답 필드와 `ground_truth`는 입력에서 제외합니다.
- Judge는 **저장된 실제 답변 JSON 전체**를 채점합니다. Groundedness에는 답변 생성 때 사용한 같은 context를 전달합니다.
- Relevance에는 질문과 답변을 전달하며 규정 context는 전달하지 않습니다. 올바르게 “규정에 없음”을 알리거나 추가 정보를 요청한 답변도 낮게 평가될 수 있으므로 이유를 규정과 대조합니다.
- 이번 Judge 입력에는 `ground_truth`를 매핑하지 않습니다. 그 설명은 사람이 기대 행동을 이해하고 검토할 때 사용합니다.
- 전후 비교는 같은 mode, dev 질문/정답, context, 모델 배포·보고된 모델 버전, 생성 설정, 업무 평가기 버전을 요구합니다.
- `judge --like`는 baseline의 평가 그룹과 평가기 버전·Judge 모델 정보를 재사용합니다. 모델 배포를 수업 중 변경하지 않습니다.
- 각 업무 검사 또는 Judge의 `점수 ≥ 4` 판정이 **통과→실패**로 바뀌면 회귀입니다. 이미 실패하던 사례의 다른 검사가 나빠진 경우도 확인합니다.
- 점수·이유가 누락되거나 NaN/범위 밖이면 유효한 평가로 취급하지 않습니다. 전체 예상 사례 ID와 평가기 둘 모두 있어야 합니다.
- 서로 다른 질문인 dev와 holdout은 전후 비교할 수 없습니다. 중복 ID/동일 질문이 들어간 holdout도 Gate에서 거부합니다.

해시는 입력과 저장 결과의 우발적인 변경을 발견하는 장치입니다. 전자서명이나 악의적인 변조에 대한 감사 증명을 제공하지 않습니다.

**작은 표본:** dev 8개, holdout 4개는 학습을 위한 최소 사례입니다. 운영 품질 보증이나 통계적 유의성의 근거가 아닙니다. LLM 결과는 실행마다 달라질 수 있으며, 이 도구는 좋은 결과가 나올 때까지 자동 반복하지 않습니다.

**Judge 척도:** 공식 RAG 평가기의 기본 합격선은 3일 수 있습니다. 이 실습은 서버 평가기 정의를 임의 변경하지 않고 **원점수 4 이상**을 로컬 합격선으로 사용합니다. 포털 Label/Pass와 로컬 통과율이 다른 경우 먼저 threshold를 확인합니다. 4/5점은 정확도 80%가 아닙니다.

<a id="self-check"></a>
## 다섯 질문으로 스스로 확인하기

먼저 자신의 말로 답한 뒤 해설과 대조합니다. 실제 결과의 사례 하나를 들어 설명하면 됩니다.

1. 왜 유창한 답변만 보면 안 되나요?
2. 코드·Judge·사람은 각각 무엇을 보나요?
3. 전후 비교에서 무엇을 고정하나요?
4. 평균이 올라도 왜 보류할 수 있나요?
5. Holdout을 보고 수정했다면 무엇이 필요한가요?

<details>
<summary>답한 뒤 해설 보기</summary>

1. 자연스러운 문장도 잘못된 한도나 없는 승인을 안내할 수 있습니다.
2. 코드는 명시적 필드, Judge는 의미, 사람은 규정과 업무 위험을 봅니다. 어느 하나의 통과가 나머지를 보장하지 않습니다.
3. 질문·정답·규정·모델·생성 설정·Judge·합격선. 이번 실습에서는 프롬프트만 바꿉니다.
4. 중요한 한 건의 새 실패를 다른 사례의 개선으로 상쇄할 수 없기 때문입니다.
5. 새로운 독립 holdout입니다. 기존 질문은 이제 개발에 사용된 데이터입니다.

</details>

## Gate가 요구하는 것

| 대상 | 교육용 조건 |
|---|---|
| 입력 | 완료된 dev baseline, dev candidate, 그 candidate에서 `--frozen`으로 만든 별도 holdout |
| 업무 | Candidate와 holdout 각각 80% 이상 |
| Judge | 세 실행 모두 완전한 결과, 동일 Judge/평가기 계약. Candidate/holdout의 각 지표 통과율 80% 이상 |
| P0 | Candidate와 holdout에서 업무와 두 Judge 지표 모두 실패 0개 |
| 회귀 | Dev의 개별 업무 검사와 Judge 합격→실패 변화 0개 |
| 사람 | Candidate와 holdout 각각 최소 한 사례의 판정·근거. 마지막 판정이 fail인 사례 없음 |

`review`는 기존 기록을 지우지 않고 추가합니다. 같은 사례를 재검토하면 **최신 사람 판정**을 사용하며 이전 이유도 남습니다. AI 보조 검토는 사람 판정을 덮어쓰지 않습니다. 검토를 저장해도 모델이 학습되거나 Judge 점수가 바뀌지 않습니다.

LIVE의 `READY_FOR_HUMAN_REVIEW`는 **사람이 다음 출시 검토를 할 수 있는 교육용 신호**입니다. 자동 운영 승격이 아닙니다. DEMO에서는 절대 LIVE의 준비 완료 상태를 반환하지 않습니다.

<a id="assisted-review"></a>
### 자동 실행의 AI 보조 검토

기본 `review`는 참가자 본인의 검토를 뜻하는 `--reviewer human`입니다. **Copilot 등 AI가 직접 판정한 경우 반드시 `--reviewer assistant`**로 구분합니다.

```bash
python lab.py review results/candidate D06 --reviewer assistant
```

비대화형 실행에서는 실제 응답·규정과 대조한 `--verdict`와 `--note`도 지정합니다. 이 옵션은 입력 방식을 바꿀 뿐 정답이나 승인을 자동으로 부여하지 않습니다. Holdout의 H04에도 같은 구분을 적용합니다.

AI 보조 검토는 `reviews.json`에 남지만 **사람 검토의 건수나 최신 판정에 포함되지 않습니다.** 보조 검토만 있으면 점수가 높아도 Gate는 `BLOCK`입니다. 실제 사람이 이후 답변과 근거를 검토하고 기본 `review` 명령으로 본인의 판단을 추가한 뒤 Gate를 다시 확인합니다. 통과를 위해 AI 기록을 `human`으로 바꾸지 않습니다.

기존 파일의 `reviewer` 없는 기록은 이전 형식의 사람 검토로 읽습니다. 이 필드는 검토 유형을 명시하는 교육용 기록이며, 실제 사람의 신원을 인증하거나 승인 권한을 증명하는 장치는 아닙니다.

## 어디에 무엇이 남는가

아래 파일 표와 입력 매핑은 **입문 `lab.py`** 기준입니다. 최소 RAG는 [검색 결과·입력 증거](optional-rag.md#evidence), 완결형은 [단계별 산출물](complete-lab.md#resume)을 사용합니다. 최소 RAG의 context는 규정 전체가 아니라 실제 검색 문맥이며, 완결형의 평가 입력에는 별도 대화 계약이 있습니다.

| 파일 | 내용 |
|---|---|
| `results/<이름>/run.json` | 사례·규정·프롬프트 스냅샷, 해시, 모드, 배포 정보, 실제/예제 응답, 생성 시간·토큰 사용 정보 |
| `report.md` | 사례별 업무 검사, Judge 점수와 이유, 유형별 결과 |
| `judge.json` | Foundry 실측 또는 명시적인 작성 예제 점수. 평가 계약과 원본 응답 해시에 연결 |
| `foundry-job.json` | LIVE의 원격 eval/run ID, 상태, 고정한 평가 계약 |
| `foundry-output.json` | LIVE 원격 평가의 원본 행 결과. 전체 페이지를 수집 |
| `reviews.json` | 사람/AI 보조 검토 유형, 판정과 이유, 해당 응답 해시 |
| `comparison.md` / `.json` | Candidate 폴더에 저장되는 같은 dev의 전후 비교 |
| `gate.md` / `.json` | Candidate 폴더에 저장되는 교육용 판단과 이유 |

생성 시간은 개별 API 호출의 관측 지연입니다. 작은 표본의 p95는 운영 SLA가 아닙니다. 생성 토큰 합계에는 Judge 소비량이 포함되지 않으며 가격/통화별 실제 청구액을 대신하지 않습니다.

기본으로 별도의 dataset asset을 등록하지 않습니다. 작은 평가 데이터를 **inline `file_content`**로 평가 요청에 넣고 클라우드 평가 결과를 저장합니다. 생산 환경에서는 버전 관리된 데이터셋과 접근·보존 정책을 적용합니다.

### Foundry에 전달하는 데이터 매핑

| 평가 입력 | 가져오는 값 | 사용 |
|---|---|---|
| `id` | 로컬 사례의 `id` | 원격 결과를 원래 사례와 연결 |
| `query` | 직원의 질문 | 두 평가기의 `{{item.query}}` |
| `context` | 답변 생성 당시 저장한 규정 전체 | Groundedness의 `{{item.context}}` |
| `response` | 저장한 `raw_response` 문자열, 답변 JSON 전체 | 두 평가기의 `{{item.response}}` |

원본 `data/dev.jsonl`은 **질문과 기대 행동**이며, 아직 모델이 작성하지 않은 `response`는 없습니다. 따라서 원본 질문 파일을 포털에 올리는 일을 `judge`와 동일한 평가로 생각하지 않습니다. 이 도구는 `run.json`의 **실제 저장 응답**을 매핑합니다. `expected_*`와 `ground_truth`는 이 두 Judge의 입력에 넣지 않습니다.

<a id="portal-results"></a>
## 포털 결과를 찾거나 비교할 때

먼저 `judge` 출력의 **Foundry 보고서 URL**을 엽니다. URL이 없거나 다른 화면이 열리면 다음을 확인합니다.

1. 같은 계정·테넌트·프로젝트의 **Build → Evaluations / 평가** 메뉴를 엽니다. 계정 선택 화면이 다시 나오면 CLI에서 확인한 계정과 같은 계정을 선택합니다.
2. 해당 결과 폴더의 `foundry-job.json`에서 `eval_id`와 `run_id`를 찾아 실행을 대조합니다. `eval_id`는 입력 형식·평가기 정의, `run_id`는 이번 답변 묶음의 평가 실행입니다.
3. 상태가 **Completed**인지 보고 실행 이름을 엽니다. 질문·응답·Groundedness·Relevance·점수 이유를 확인합니다. 사례 ID가 안 보이면 질문 문장으로 찾습니다. 행 순서가 같다고 가정하지 않습니다.
4. `inspect`와 `report.md`에서 같은 답변·원점수·이유를 대조합니다. 결과를 찾으려고 새 평가를 제출하지 않습니다.

`--like`로 실행한 baseline/candidate는 **`eval_id`가 같고 `run_id`는 다릅니다.** 첫 목록이 실행 두 개가 아니라 **`straightforward-…` 그룹 한 행**으로 보이는 것이 정상입니다.

1. **Last run** 링크가 아닌 **그룹 이름**을 눌러 **Evaluation runs**를 엽니다.
2. **`v1-dev-…`와 `my-v2-dev-…` 두 실행만** 체크하고 **Compare runs**를 선택합니다. 전체 선택으로 holdout이나 extra를 섞지 않습니다. **Analyze Results**는 별도 기능이며 기본 실습에서 필요하지 않습니다.
3. 비교 화면의 **Baseline**을 **`v1-dev-…`**로 명시합니다. 후보를 먼저 선택하면 후보가 기준이 될 수 있습니다.
4. 평균을 확인한 뒤 각 실행의 같은 질문·답변·원점수·이유를 로컬과 대조합니다. 포털 통계 비교를 개별 사례의 업무 검사나 합격선 4점 기준의 회귀 검사로 대신하지 않습니다.

**Too few samples / Inconclusive**는 표본이 작거나 차이를 확정할 근거가 부족하다는 뜻입니다. 색상만으로 채택하지 않습니다. 비교 URL도 기록하고, 원격 실행 ID와 로컬 `comparison.md`를 함께 보관합니다. 비교 기능이 보이지 않으면 각 실행의 같은 질문을 나란히 봅니다.

포털의 **Overall score / Pass**는 기본 threshold 3을 기준으로 표시될 수 있습니다. 따라서 포털이 **100%**여도 이 실습의 **4점 이상 통과율**은 더 낮을 수 있습니다. 원점수가 같고 합격선만 다르면 수집 오류가 아닙니다.

이 실습은 이미 생성한 응답을 채점하므로 포털의 Target·생성 지연·비용이 비어 있을 수 있습니다. 생성 기록은 로컬 `run.json`, 실제 청구는 Azure Cost Management를 확인합니다.

<a id="troubleshooting"></a>
## 문제 해결

| 증상 | 확인 / 조치 |
|---|---|
| 비공개 GitHub 저장소에 접근할 수 없음 | Azure Owner와 GitHub 접근 권한은 별개. 저장소 접근 권한 또는 소유자가 승인한 ZIP 배포 필요 |
| 구독이 목록에 없음 | 포털·CLI의 계정과 테넌트 확인. 다른 디렉터리의 게스트 계정이라면 사용할 구독의 테넌트로 로그인 |
| Owner인데 역할 할당/생성이 안 됨 | 구독 범위의 역할인지, PIM에서 활성인지 확인. 관리 그룹 정책·deny assignment·조건부 액세스는 Owner로 우회하지 않기 |
| 공급자가 등록되지 않았다고 함 | 해당 구독의 Resource providers에서 `Microsoft.CognitiveServices`를 등록하고 `Registered` 확인 |
| `python` 또는 `lab.py`를 찾을 수 없음 | VS Code에서 `lab.py`가 있는 폴더를 열고 [준비 1](../README.ko.md#setup-tools)의 가상환경 활성화부터 확인. 새 터미널마다 활성화 필요 |
| 명령 입력 후 `SyntaxError`, 화면에 `>>>`가 보임 | Python 대화창에 셸 명령을 입력한 상태. `exit()`로 나온 뒤 VS Code 터미널에 명령만 입력 |
| 파일을 수정했는데 실행에 반영되지 않음 | 브라우저가 아니라 VS Code의 로컬 복사본인지, File → Save로 저장했는지, 명령의 파일 경로가 맞는지 확인. 완료된 결과는 덮어쓰지 않기 |
| Windows에서 `Activate.ps1` 실행이 차단됨 | 조직 정책을 해제하지 않고 설치 명령부터 모든 `python`을 `.\.venv\Scripts\python.exe`로 대체. [준비 1](../README.ko.md#setup-tools) 확인 |
| LIVE 패키지 없음/버전 불일치 | 가상환경 안에서 `python -m pip install -r requirements.txt`. 임의 최신 업그레이드 금지 |
| config 예시 값 오류 | endpoint의 `YOUR-...`를 실제 프로젝트 주소로 교체. 두 배포 이름은 본인이 만든 `eval-model` 또는 실제 이름인지 확인 |
| classic 허브 연결 문자열이나 모델 주소만 있음 | 새 Foundry 프로젝트의 `/api/projects/...` 주소가 필요. [기존 환경 조건](setup.md#existing-environment)을 확인하고 새 환경 사용 또는 [DEMO로 분리 전환](setup.md#switch-to-demo) |
| 저장했는데 config를 찾을 수 없음 | `lab.py` 옆의 `config.json`인지, `config.json.txt`로 저장되지 않았는지 확인 |
| `prompts/my-v2.txt`를 찾을 수 없음 | 먼저 저장소 폴더·파일 경로·저장 여부 확인. 포함된 작업본이 정말 없을 때만 [실습 4](../README.ko.md#lab-4)에 따라 준비. 기존 개인 작업을 V2로 덮어쓰지 않기 |
| `my-v2.txt`·`my-case.jsonl`이 이미 있음 | 저장소의 예제 작업본. 기존 내용·개인 수정부터 확인하고 재사용/직접 편집을 구분. `my-v2.txt`는 날짜 미확인 시 조건부 한도를 나열하지 않고 SCOPE만 인용하는 지침이 추가되어 `v2.txt`와 동일하지 않음 |
| `validate-data`가 `ERROR:`를 출력 | 표시된 줄·필드 수정. JSON 객체 전체를 한 줄로 저장하고 빈 줄 제거. 필수 8개 필드·숫자/null·true/false·공식 출처 확인 후 같은 검사 재실행. 통과 전 유료 `run` 실행하지 않기 |
| `validate-data`의 건수가 1이 아님 | N01 등 다른 사례를 복사본에 남겼는지 확인. 이번 추가 사례 파일에는 N02 한 줄만 저장. 원본 질문 파일이나 기존 결과는 수정하지 않기 |
| `review`에서 멈춘 것처럼 보임 | 오류가 아니라 입력 대기. `pass`/`fail` 입력 후 Enter, 규정과 대조한 이유 5자 이상 입력 후 Enter. `검토 저장` 확인 |
| Gate가 사람 검토 누락이라고 함 | candidate D06·holdout H04의 `review`로 실제 판정과 이유를 저장한 뒤 **같은 `gate`를 재실행**. 생성·Judge 재실행은 필요 없음 |
| 로그인/401 | 본인 계정으로 `az login`. 올바른 테넌트인지 확인. 키를 코드에 붙이지 않기 |
| Owner인데 모델 호출/평가가 403 | [Foundry User 확인](setup.md#permissions): **본인과 프로젝트 관리 ID**의 역할 및 상위 Foundry 리소스 범위를 확인. 전파를 기다린 뒤 같은 테넌트로 다시 로그인 |
| 모델은 보이는데 쿼터 조회가 403/빈 목록 | 쿼터는 별도 구독 범위 조회. [권한 계약](#permissions-contract)과 모델/SKU 필터를 확인하고 쿼터 0으로 단정하지 않기 |
| Private Link/공용 접근 차단 | 승인된 VNet/VPN/실행 환경에서 접속. 수업을 위해 방화벽을 임의로 해제하지 않기 |
| 모델 404 | 모델 카탈로그 이름이 아닌 **배포 이름**, 올바른 프로젝트 연결인지 확인. 기본 설정의 두 배포 항목은 `gpt-6-luna`가 아니라 `eval-model` |
| JSON Schema/파라미터 400 | 선택한 모델의 Chat Completions·Structured Outputs·생성 토큰 옵션 지원 확인 |
| `finish_reason=length` | 결과가 잘렸으므로 형식 실패가 정상. 선택한 모델과 출력 제한의 적합성을 확인하고 변경이 필요하면 별도 실험으로 재시작 |
| 429 | 여러 팀의 TPM/RPM과 Judge 부하 확인. 잠시 기다린 뒤 미완료 작업만 재개 |
| 모델 배포가 쿼터/지역 문제로 실패 | [모델 가용성 확인](#model-availability). 본인 권한이 있어도 배포 용량이 자동 확보되지는 않음 |
| 리소스 그룹의 Deployments에 `PolicyDeployment` 실패가 보이지만 모델은 동작 | 모델 배포 상태와 별개의 조직 정책 작업일 수 있음. 배포 오류를 확인하고, 중앙 Log Analytics 작업 영역 누락 같은 조직 진단 설정 문제는 정책 관리자에게 전달. 기록을 지우거나 정책을 해제해 성공처럼 보이게 하지 않기 |
| Foundry 평가 미완료/종료 코드 3 | 같은 `judge` 명령 재실행. 저장된 ID로 조회하므로 새 답변·평가를 생성하지 않음 |
| 원격 `completed`인데 `평가 완료`는 없음 | 로컬 결과 수집·검증·저장을 기다림. 오류가 나면 원본 ID를 보존하고 원인을 해결한 뒤 같은 `judge` 재개 |
| `judge` 수집·저장 오류 | 연결·권한·저장 공간 등 출력된 원인을 해결한 뒤 `--like`를 포함한 같은 명령 전체로 재개. `judge.json`이 있어도 보고서 저장 전 오류였다면 검증·저장을 다시 수행할 수 있음 |
| Judge 결과 ID/점수/이유 누락 | `foundry-output.json`과 `foundry-job.json` 보존. SDK/서비스 계약 확인. 누락을 통과로 바꾸지 않기 |
| 한쪽에만 Judge 결과가 있어 비교 불가 | 다른 쪽도 `judge --like`로 완료한 뒤 비교 |
| 포털에서 실행이 안 보이거나 점수가 다름 | 같은 테넌트·프로젝트의 `eval_id`/`run_id`인지 확인. 행 순서 대신 질문/ID로 대조하고 원점수와 threshold를 구분. 결과를 찾으려고 새 평가를 제출하지 않기 |
| 서로 다른 데이터/모델/평가기라고 함 | 결과 폴더·입력 파일·배포 변경 여부 확인. 비교 가능한 새 실험을 별도 이름으로 수행 |
| Gate `BLOCK`, 종료 코드 2 | `gate.md`의 실패 이유 읽기. 실행 장애가 아니라 의도한 품질 차단 |
| DEMO에서 새 프롬프트/질문을 거부 | 고정 예제는 제공된 원본만 사용. 실습 6의 새 질문은 `validate-data`만 실행. 새 입력의 모델 응답을 측정하려면 별도의 LIVE 준비가 필요하며 모드만 바꾸지 않기 |
| 어느 단계까지 했는지 기억나지 않음 | [결과 파일별 재개 표](setup.md#resume-checkpoints) 확인. 새 결과를 뽑거나 파일을 지워 처음부터 반복하지 않기 |
| 리소스 삭제가 완료되지 않음 | [정리 절차](cleanup.md)의 범위·잠금·상태 확인. 요청 성공 알림만 보고 삭제 완료로 기록하지 않기 |

오류 공유 시 **명령·단계·오류 종류·비밀을 제거한 필요한 ID**만 전달합니다. 전체 설정·응답·고객 데이터·토큰을 공개 게시하지 않습니다.

<a id="permissions-contract"></a>
## 권한은 작업·대상·범위를 함께 확인

**전용 신규 환경:** 이 가이드는 [Foundry RBAC의 시작 구성](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry#minimum-role-assignments-to-get-started)을 따라 **본인과 프로젝트 관리 ID 각각에 상위 Foundry 리소스 범위의 Foundry User**를 확인합니다. 포털 생성자가 역할 할당 권한을 가졌을 때 자동 부여될 수 있지만 CLI 생성에서는 자동 부여를 가정하지 않습니다. Owner의 관리 권한과 Foundry 데이터 접근 권한은 별개입니다.

**기존·공유 환경:** [클라우드 평가 사전 조건](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation#prerequisites)은 호출자의 **프로젝트 범위 Foundry User**를 명시합니다. 공식 RBAC의 기업 예제에는 프로젝트 Foundry User + 상위 리소스 Reader 조합도 있습니다. 위 전용 환경의 상위 범위를 모든 평가의 유일한 최소 범위로 해석하지 않습니다. 소유자가 실제 모델·연결·사용 API의 권한을 확인하며, 수업 때문에 공유 계정 전체의 권한을 확대하지 않습니다.

| 값 | 용도 / 주의 |
|---|---|
| 본인의 사용자 Object ID | 로컬 `AzureCliCredential`이 사용하는 로그인 사용자. 역할 대상 형식은 `User` |
| 프로젝트 `identity.principalId` | 서비스 측 접근을 위해 준비하는 **프로젝트 관리 ID**. 역할 대상 형식은 `ServicePrincipal` |
| 상위 계정 `identity.principalId` | 프로젝트 관리 기능에 필요한 **별도 계정 관리 ID**. 위 프로젝트 ID 대신 넣지 않음 |
| `/accounts/ACCOUNT`로 끝나는 리소스 ID | 역할을 적용할 **범위**. 사용자/관리 ID가 아니며 하위 프로젝트에도 권한이 상속됨 |
| `53ca6127-db72-4b80-b1b0-d745d6d5456d` | **역할 정의 ID**. Foundry User(이전 Azure AI User)의 이름 변경 후에도 동일 |

자원 생성에는 해당 범위의 생성 권한, 역할 부여에는 역할 할당 권한이 필요합니다. Owner는 둘을 제공하는 한 방법이지 모든 참가자의 최소 역할은 아닙니다. **쿼터 조회**는 별도로 구독 범위의 `Microsoft.CognitiveServices/locations/usages/read`를 요구합니다. 필요한 사용자에게만 **Cognitive Services Usages Reader** 또는 이미 이를 포함하는 역할을 사용합니다. Foundry 리소스 범위의 역할만으로 구독 쿼터 조회가 보장되지는 않습니다.

RAG의 **사용자 → Search** 접근과 **Search 관리 ID → 모델** 접근도 별개입니다. Search Service Contributor는 검색 객체뿐 아니라 서비스 설정도 관리할 수 있고, 문서 업로드·조회에는 Search Index Data Contributor가 따로 필요합니다. 서비스 범위 권한 아래에서 고유 객체 이름은 충돌 방지이지 사용자별 보안 격리가 아닙니다. 실제 할당은 [Search 접근](optional-rag.md#search-access)과 [완결형 모델 접근](complete-lab.md#search-model-access)만 따릅니다.

<a id="managed-identity-access"></a>
## 프로젝트 관리 ID를 선택할 수 없을 때

이 절은 [준비 4: 권한 확인](../README.ko.md#setup-permissions)의 포털 선택이 어려울 때만 사용합니다. 역할 할당 권한이 없으면 아래 명령을 시도하는 대신 소유자에게 대상과 범위의 대조를 요청합니다.

1. Foundry의 **Manage → Project details**에서 해당 프로젝트의 Azure 리소스를 엽니다. 프로젝트 리소스 ID는 `/accounts/계정이름/projects/프로젝트이름`으로 끝납니다.
2. Azure 포털의 프로젝트 **Identity → System assigned**에서 **Object (principal) ID**를 복사합니다. ID 메뉴가 보이지 않으면 리소스의 JSON 보기에서 `identity.principalId`를 확인합니다. 상위 Foundry 계정의 ID가 아닙니다.
3. 같은 상위 Foundry 리소스의 Overview/JSON 보기에서 **리소스 ID**를 복사합니다. 역할을 줄 범위는 `/accounts/계정이름`까지이며 `/projects/...`가 아닙니다.
4. IAM에서 역할이 없는 것을 확인한 뒤 아래 값을 바꿔 한 번만 실행합니다.

```bash
az role assignment create --assignee-object-id "YOUR-PROJECT-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

GUID는 **Foundry User / 이전 Azure AI User**의 역할 정의 ID입니다. 출력 후 IAM에서 **대상 ID와 범위**를 확인하고 준비 4단계로 돌아갑니다.

프로젝트에 시스템 할당 ID 자체가 없다면 환경 소유자의 승인 범위 안에서 프로젝트의 **Identity → System assigned → On → Save**로 먼저 활성화합니다. 조직 정책 때문에 활성화할 수 없다면 정책 소유자와 확인하며, 대신 비밀 키나 별도의 사용자 계정을 만들지 않습니다.

<a id="model-endpoint-contract"></a>
## 이름·버전·주소를 구분하기

| 개념 | 이번 경로에서의 값과 쓰임 |
|---|---|
| 모델 이름 | `gpt-6-luna`: 카탈로그의 모델. `config.json`의 배포 이름 대신 넣지 않음 |
| 모델 버전 | 예: `2026-09-22`: 배포가 가리키는 모델 버전. 완결형의 기록된 V1 비교에는 이 지정 버전이 필요 |
| 배포 이름 | 신규 환경의 `eval-model`: 프로젝트에서 조회·호출할 배포. `model_deployment`와 `judge_deployment`에 사용 |
| 지역·배포 유형 | 리소스·프로젝트의 `swedencentral`과 모델 SKU `GlobalStandard`는 별개 설정. 그룹의 지역이 하위 자원의 지역을 자동 결정하지 않음 |
| Project endpoint | `https://ACCOUNT.services.ai.azure.com/api/projects/PROJECT`: `config.json`에 넣는 주소. 리소스 ID·classic 연결 문자열·모델 전용 주소와 다름 |
| SDK/API 버전 | 패키지 `2.7.0`·프로젝트 API `v1`은 모델 버전과 별개. SDK가 프로젝트 주소에 `/openai/v1`을 붙이므로 설정에는 이를 미리 붙이지 않음 |

`GlobalStandard`는 전 세계 처리 인프라를 사용할 수 있으므로 **`swedencentral` 배포가 모든 추론을 스웨덴 안에서 처리한다는 보장은 아닙니다**. 실제 데이터로 확장하기 전 [배포 유형별 처리 위치](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/deployment-types)를 확인합니다. 이 가이드는 가상 규정을 사용하며 수업 중 SKU를 바꾸지 않습니다.

<a id="model-availability"></a>
## 모델·지역·쿼터가 맞지 않을 때

기본 경로는 **`gpt-6-luna`·`swedencentral`**입니다. 실제로 배포할 수 있는지는 **본인 구독의 Foundry 모델 카드와 배포 화면**이 기준입니다. 문서에 이름이 있다는 사실이 용량 확보나 생성·평가 호환성을 뜻하지는 않습니다.

1. 정확한 계정·구독·지역에서 `gpt-6-luna` 모델 카드와 제공 버전을 확인합니다. 모델 이름이 보이지 않으면 비슷한 이름으로 대체하지 않고 중단 상태를 기록합니다.
2. 같은 리소스의 **Build → Models**에서 실패 원인과 남은 쿼터를 확인합니다. 모델·배포 유형·지역별 쿼터는 서로 다릅니다. **Global Standard** 지원 여부와 남은 용량·capacity 단위를 각각 확인합니다. 쿼터 조회가 403이거나 비어 있으면 [구독 범위 조회 권한](#permissions-contract)과 정확한 모델/SKU를 먼저 확인합니다.
3. 지원 모델이 있어도 쿼터가 없으면 증가를 요청하거나 환경 소유자와 실행 조건 변경을 먼저 합의합니다. **지정 모델·지역을 임의 변경하거나 기존 업무 배포의 쿼터를 줄이지 않습니다.** 모델을 바꾸기로 했다면 그 이름·버전·요금을 기록하고 전후 비교 전체를 같은 조건으로 새로 설계합니다.
4. **신규 입문의 배포 이름은 `eval-model` 하나**로 유지하고 [한 건의 생성·평가](setup.md#smoke)를 완료한 뒤 본 실습을 시작합니다. `config.json`의 두 모델 항목에는 카탈로그 모델명이 아니라 배포 이름을 넣습니다. 허가된 기존 환경의 이름은 [기존 환경 조건](setup.md#existing-environment)을 따릅니다.

모델이 **Chat Completions·Structured Outputs(JSON Schema)·생성 토큰 옵션·Foundry Judge**를 동일하게 지원한다고 가정하지 않습니다. 특히 추론에 토큰을 사용하는 모델은 최종 답변이 짧아도 `finish_reason=length`가 발생할 수 있습니다. 이 경우 점수 실패와 실행 호환성 문제를 구분하고, 출력 설정을 바꿔야 한다면 baseline부터 새 실험으로 시작합니다. Model router나 다른 파트너 모델을 기본 경로에 임의 추가하지 않습니다.

지정 조건에서 진행할 수 없으면 LIVE가 막힌 상태라고 기록하고, 원할 때만 [DEMO로 분리 전환](setup.md#switch-to-demo)합니다. 지역 변경을 별도로 합의했다면 [배치 평가 지원 지역](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network)과 [모델 지역 제공 범위](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability)를 함께 확인합니다. 이미 생성한 환경은 실패나 전환을 이유로 삭제하지 않고 [보존 기록](cleanup.md#retain-resources)을 남깁니다.

<a id="resume"></a>
## 중단·재실행과 원격 ID 복구

`judge`의 기본 **상태 조회 대기 예산은 300초**입니다. 인증·제출·HTTP 응답·결과 수집까지 포함한 전체 명령 제한 시간이 아닙니다. 종료 코드 `3`은 실패나 새 제출 지시가 아니라, 저장된 원격 ID로 다음 조회를 이어가라는 뜻입니다.

**정상 재개**

- 완료된 `run`/`judge`를 같은 입력으로 다시 실행하면 저장된 결과를 읽습니다.
- 부분 수집에서는 **저장된 행을 재호출하지 않고** 남은 행을 생성합니다.
- 단, 모델이 응답한 직후 저장 전에 연결/프로세스가 끊어졌다면 그 한 행은 재호출될 수 있고 추가 비용이 발생할 수 있습니다. 정확히 한 번의 유료 호출을 보장하지 않습니다.
- 원격 `run_id`가 있으면 **`--like`를 포함한 원래 `judge` 명령 전체**로 조회를 재개합니다. 완결형 교정은 원래 `calibrate` 명령을 사용합니다. 한 결과 폴더는 한 터미널에서만 실행합니다. 터미널을 닫아도 이미 제출된 원격 평가는 계속될 수 있습니다.
- **대기와 오류 복구를 구분합니다.** 코드 `3`이면 그대로 조회를 재개하고, `ERROR:`이면 원인을 먼저 해결한 뒤 같은 명령을 사용합니다. 수집·저장 오류 복구도 재개의 대상이므로 “처리 중일 때만 재실행 가능”한 것은 아닙니다. 원격 생성 여부가 불명확하면 아래 ID 복구부터 수행합니다.
- 입문·최소 RAG의 프롬프트나 데이터가 달라졌다면 새 `--out` 폴더를 사용합니다. **완결형 `run`에는 `--out`이 없으므로** [별도 작업 폴더의 새 실험](complete-lab.md#resume)을 따릅니다. 이전 결과를 덮어쓰거나 합치지 않습니다.

**폴더 이름이나 위치를 바꾼 경우**

가상환경이 이전 폴더를 참조하면 새 위치에서 터미널을 엽니다. `lab.py`와 `requirements.txt`가 있는 폴더인지 먼저 확인한 뒤 **`.venv`만 재생성**합니다. 아래 `--clear`는 `.venv` 안의 설치 패키지를 지우므로, 본인이 따로 넣은 파일이 있다면 먼저 보관합니다. `config.json`, `results/`, 직접 쓴 프롬프트와 질문은 지우지 않습니다.

macOS / Linux:

```bash
python3 -m venv --clear .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python lab.py doctor
```

Windows:

```powershell
py -3 -m venv --clear .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python lab.py doctor
```

활성화가 조직 정책으로 막힌 경우는 [도구 준비](setup.md#tools)의 가상환경 Python 직접 실행 방식을 사용합니다. 복원 후에는 완료된 결과를 새로 만들지 말고 기록해 둔 다음 명령부터 이어갑니다.

**드문 경우: 생성 요청을 보낸 직후 원격 ID를 받기 전에 끊김**

`foundry-job.json`의 `phase`가 `creating-eval` 또는 `creating-run`인데 해당 ID가 없으면 생성 여부를 단정할 수 없습니다. 비용 중복을 피하려고 자동 재생성하지 않습니다.

먼저 해당 평가 폴더에서 **로컬 상관관계 ID**를 찾습니다. `foundry-job.json`의 원격 `run_id`와는 다른 값입니다.

| 실행 경로 | 로컬 `run_id`가 저장된 파일 |
|---|---|
| 입문 `lab.py` / 최소 RAG `rag_lab.py` | 해당 결과 폴더의 `run.json` |
| 완결형 `advanced_lab.py` | `results/advanced/<stage>/evaluation-request.json`. 교정은 `<stage>` 대신 `calibration` |

환경 소유자가 다음을 확인합니다.

1. 파일을 보존하고 위 로컬 `run_id`로 포털의 `straightforward-<앞 8자>` 평가 그룹 또는 `<프롬프트>-<split>-<앞 8자>` 실행을 찾습니다. 완결형 실행 이름은 `<stage>-advanced-<앞 8자>`이며 교정 stage는 `calibration`입니다. 원격 metadata의 `workshop_run`도 같은 로컬 ID여야 합니다.
2. **정확히 이 작업임을 확인한 경우에만** `foundry-job.json`의 비어 있는 `eval_id`/`run_id`를 실제 값으로 복구합니다. 그룹만 생성됐다면 `phase`는 `ready`, 실행도 생성됐다면 `submitted`로 저장하고 **원래 `judge` 또는 `calibrate` 명령 전체**를 실행합니다.
3. 생성 여부를 확정할 수 없으면 재제출하지 않습니다. 관리자 확인 또는 DEMO로 전환합니다. 응답·점수·계약·해시를 조작해서 완료 상태를 만들지 않습니다.

서비스가 작업을 명시적으로 `failed`/`canceled`로 끝낸 경우도 자동 재시도하지 않습니다. 원인을 먼저 해결합니다. 같은 저장 응답을 다시 평가하려면 환경 소유자가 실패 ID와 상태를 별도 보존하고, **실행이 확실히 종료됐음을 확인한 뒤** `foundry-job.json`의 `run_id`만 `null`, `phase`를 `ready`로 설정해 명시적으로 재제출할 수 있습니다. `eval_id`, 입력 해시와 평가 계약은 유지합니다. 유료 재평가이며 완료된 점수를 더 좋은 점수로 바꾸기 위한 기능이 아닙니다.

## SDK와 확인 범위

**공식 권한·SDK/API 문서 대조일: 2026-09-28.** 이 대조와 로컬 검사는 새로운 Azure 실행 검증이 아닙니다.

| 구분 | 이 가이드의 선택 |
|---|---|
| Python | 3.10 이상 문법·표준 라이브러리. 작성 환경의 로컬 실행은 3.14 |
| LIVE 목표 모델·지역 | `gpt-6-luna` / `swedencentral`. 답변·Judge의 배포 이름은 모두 `eval-model` |
| Foundry SDK | `azure-ai-projects==2.7.0` |
| 인증 | `azure-identity==1.25.3`의 `AzureCliCredential`. 명시적으로 Azure CLI 로그인 사용 |
| OpenAI client | `openai==3.16.2`. 설치 가능한 호환 버전으로 고정했으며 “최신 버전”이라는 뜻이 아님 |
| 실제 모델 호출 | `AIProjectClient.get_openai_client()`의 `chat.completions.create` + JSON Schema |
| 실제 평가 | 같은 프로젝트 OpenAI client의 `evals.create`, `evals.runs.create`, `retrieve`, `output_items.list` |
| 평가기 조회 | SDK 2.7의 `project.beta.evaluators.list_versions`. 조회한 버전 하나를 고정해 재사용 |
| SDK 기본 API | 프로젝트 API `v1`, OpenAI client 경로는 프로젝트 주소 + `/openai/v1`. 저장소는 별도 `api_version`을 설정하지 않음 |

직접 의존성만 고정한 `requirements.txt`입니다. 전이 의존성과 패키지 파일 해시까지 잠근 전체 lockfile은 아닙니다.

현재 Learn의 일반 예제는 `azure-ai-projects>=2.2.0`·`DefaultAzureCredential`을 사용할 수 있지만, **이 저장소의 실행 계약은 위 고정 버전과 `AzureCliCredential`**입니다. 예제에 맞추려고 임의 업그레이드하거나 인증 방식을 바꾸지 않습니다. `beta.evaluators`는 미리 보기 API이므로 전체 워크플로를 GA로 표현하지 않습니다. Search를 쓰는 별도 경로의 `2026-04-01`(minimal/extractive)과 `2026-08-01-preview`(LLM 계획)는 이 프로젝트 API 버전과도 다릅니다.

**기록된 모델 구성:** 2026-09-27 실행은 `swedencentral`의 `gpt-6-luna` 버전 `2026-09-22`, **GlobalStandard 60K TPM**을 사용했습니다. 그 실제 실행 결과는 [완결형 실습](complete-lab.md#results)을 확인합니다. 현재 또는 다른 구독·지역의 가용성은 별도로 확인해야 합니다.

**로컬에서 확인하는 것:** 작성된 예제의 전체 실습 경로, 업무 검사·Gate의 조건, 누락/변조/회귀 차단, 문서 명령과 N02 데이터 검사, 설치된 SDK로 만든 요청·응답의 모양. README의 준비부터 추가 사례까지 LIVE 명령도 메모리 내 HTTP 응답으로 연결해 실행하며, 실제 Azure 응답이나 Judge 품질을 검증하는 것은 아닙니다.

**이것만으로 확인되지 않는 것:** 사용자의 실제 Azure 권한, 지역 가용성, 모델 배포 기능, 클라우드 채점 완료, 현재 포털의 화면 배치. 문서 작성이나 로컬 검사만으로 이를 완료했다고 주장하지 않습니다. 참가자는 자기 환경에서 [한 건의 생성·평가](setup.md#smoke)로 준비를 확인합니다. 단체 진행 전에는 필요에 따라 [전체 리허설](facilitator.md#rehearsal)을 수행합니다.

로컬 검사는 자격 증명 없이 실행합니다.

```bash
python -m unittest discover -s tests -v
```

SDK가 설치되어 있으면 SDK 계약 검사도 실행합니다. 없으면 해당 검사만 건너뛰며 DEMO 검사는 계속 수행됩니다.

<a id="live-verification"></a>
### 경로별 실행 기록의 범위

작성자의 이전 입문 실습 상세 실패·검증 기록 정리는 완료됐으며 현재 가이드에서 제거했습니다. [완결형 실습의 기록된 결과](complete-lab.md#results)는 Relevance를 포함한 모든 최종 V2 지표가 통과한 **별도 벡터·계획·대화 실험의 한 번의 관측값**입니다. 입문 LIVE나 최소 RAG가 현재 환경에서 재검증됐다는 뜻이 아닙니다.

보존한 V1 비교 예시·교정·합격 증거는 그 완결형 실행에만 해당합니다. 본인 경로의 보고서로 판단하고, 다른 실행의 점수를 재현 목표로 삼지 않습니다.

## 공식 출처

| 출처 | 확인한 내용 |
|---|---|
| [Foundry 프로젝트 만들기](https://learn.microsoft.com/azure/foundry/how-to/create-projects) | New Foundry 포털의 프로젝트 생성과 고급 옵션 |
| [Foundry 역할과 범위](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) | Owner와 데이터 작업의 차이, 본인·프로젝트 관리 ID의 Foundry User |
| [AIProjectClient API](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient?view=azure-python) | 프로젝트 주소·기본 `v1`·`get_openai_client()` 경로·beta의 미리 보기 성격 |
| [Foundry 모델 배포](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/deploy-foundry-models) | Discover → Models, 배포 이름, Global Standard와 쿼터 |
| [모델 배포 유형](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/deployment-types) | 리소스 지역과 추론 처리 위치, 토큰 과금과 예약 용량의 차이 |
| [Azure 제공 모델](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure) | 모델별 Chat Completions·Structured Outputs 등 지원 기능 확인 방법. 개별 배포의 실측 검증을 대신하지 않음 |
| [리소스 그룹 삭제](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group) | 삭제 범위·확인·잠금과 되돌릴 수 없음 |
| [예산과 알림](https://learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets) | 예산 알림은 자동 지출 중지 장치가 아님, 비용 집계 지연 |
| [클라우드 평가 개요](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation) | 프로젝트 사전 조건, 역할, SDK client, 평가 워크플로 |
| [저장된 데이터셋 평가](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-datasets) | JSONL, `file_content`, 데이터 스키마, `{{item.field}}` 매핑 |
| [SDK 평가 결과 조회](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-results) | 비동기 상태, 결과 전체 페이지 조회, 점수·이유·threshold |
| [포털 평가 결과와 비교](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results) | Evaluation 메뉴, 실행별 개별 행, Compare, Inconclusive와 비용 표시의 한계 |
| [RAG 평가기](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/rag-evaluators) | Groundedness/Relevance 입력, `deployment_name`, 1–5 척도와 기본 threshold |
| [공식 Groundedness Python 예제](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/evaluations/agentic_evaluators/sample_groundedness.py) | Foundry Evals의 실제 Python 요청 형태 |
| [Structured Outputs](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/structured-outputs) | Chat Completions의 JSON Schema 출력 |
| [지역·제한·네트워크](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network) | 수업 환경별로 확인해야 하는 기능 제공 범위 |
| [Search RBAC](https://learn.microsoft.com/azure/search/search-security-rbac) | 서비스/검색 객체 관리와 문서 읽기·쓰기 권한의 구분 |
| [Agentic retrieval](https://learn.microsoft.com/azure/search/agentic-retrieval-overview) | 정식 minimal 추출과 미리 보기 LLM 계획·대화 기능의 구분 |
| [Search 요금제](https://learn.microsoft.com/azure/search/search-sku-tier) | Basic 등 Dedicated 서비스의 프로비전 용량 기준 유지 비용 |

Microsoft Foundry의 새 문서 경로와 **Foundry classic의 `azure-ai-evaluation` 예제는 서로 다른 경로**입니다. 둘을 섞어 endpoint·인증·데이터 매핑·결과 형식을 추정하지 않습니다.

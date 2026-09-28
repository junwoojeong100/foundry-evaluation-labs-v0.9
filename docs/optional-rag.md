[English](en/optional-rag.md) | **한국어**

# Optional: Azure AI Search + Foundry IQ RAG와 Evaluation

[기본 실습](../README.ko.md) · [영문 기본 가이드](../README.md)

**직접 Search와 Knowledge Base 검색을 비교하는 선택 실습**입니다. 기본 입문 경로는 전체 규정을 직접 전달합니다. 여기서는 **실제 검색된 문서만** 모델과 Groundedness 평가기에 전달하고, **검색이 맞았는지와 답변이 맞았는지**를 따로 봅니다.

**RAG는 자료를 검색한 뒤 그 근거로 답하는 방식**입니다. **청크**는 검색할 규정 조각, **인덱스**는 그 조각을 찾도록 저장한 검색 대상입니다. Knowledge Source는 인덱스 연결이고 Knowledge Base는 그 연결로 검색 요청을 처리합니다. 코드를 작성하지 않고 설정 파일 작성 → 검색 두 번 확인 → 각 경로의 답변 생성·평가 → 비교 순서로 진행합니다.

**완결형 RAG를 먼저 끝낼 필요는 없습니다.** 이 문서는 `rag_lab.py`·`optional-rag/prompt.txt`로 두 검색 경로만 비교합니다. `advanced_lab.py`의 V1/V2·교정·동결·holdout 절차와 결과를 섞지 않습니다. 두 RAG CLI 모두 DEMO 모드는 없습니다.

기존 계정·Foundry 프로젝트·`gpt-6-luna` 배포 `eval-model`·`swedencentral`을 재사용합니다. Azure AI Search 서비스, 인덱스, 실제 Foundry IQ Knowledge Source/Knowledge Base를 추가합니다. 생성한 리소스와 결과는 **삭제하지 않습니다**.

**별도 완결형 경로 참고 영상:** [국문·영문 벡터·LLM 계획 RAG 영상](media/complete-rag/README.md). 이 문서의 minimal `search`/`iq` 실행 기록이나 검증 결과는 아닙니다.

## 무엇을 사용하는가

| 경로 | 실제 실행 |
|---|---|
| `search` | Azure AI Search 인덱스에 semantic 검색 요청 |
| `iq` | Foundry IQ Knowledge Base의 `retrieve` API → search-index Knowledge Source → 같은 인덱스 |
| 공통 | 반환된 승인 문서 중 상위 3개 → `gpt-6-luna` 답변 → 코드 검사·검색 평가·Foundry Evaluation |

**Foundry IQ를 이름만 붙인 로컬 검색으로 대체하지 않습니다.** Knowledge Base/Source를 실제 서비스에 생성하고, IQ 응답의 `references`, `sourceData`, `activity`를 저장합니다.

이 간단한 경로는 **코드에 고정된 정식 Search API `2026-04-01`의 minimal/extractive 검색**을 사용합니다. 벡터 임베딩, LLM 쿼리 계획, answer synthesis, Agent Service/MCP 연결은 사용하지 않습니다. `gpt-6-luna`는 검색 계획 모델이 아니라 **애플리케이션의 답변 생성·평가 모델**입니다. Foundry IQ는 사용자 애플리케이션에서 Knowledge Base REST API로 직접 사용할 수 있습니다. 공식 문서의 preview용 `messages`·계획 설정을 이 GA 요청에 섞지 않습니다.

```text
질문 ── search ────────────────→ Azure AI Search 인덱스
     └─ iq → Knowledge Base → Knowledge Source ─┘
                           ↓
                    실제 검색 문서 3개
                           ↓
              gpt-6-luna 답변 + 같은 문맥으로 평가
```

같은 단일 인덱스를 사용하는 두 경로는 같은 문서를 반환할 수도 있습니다. 이 실습은 IQ가 항상 더 좋은 점수를 낸다는 성능 보증이 아닙니다.

<a id="prerequisites"></a>
## 1. 준비와 비용

[README 준비 1–7](../README.ko.md#prepare)의 가상환경·`requirements.txt`·실제 `config.json`·모델 배포와 한 건의 생성/평가 확인이 필요합니다. 기존 환경은 [기존 환경 준비](setup.md#existing-environment)를 사용합니다. **공통 준비가 끝나면 이 절로 돌아오며 입문 실습 1–6을 먼저 실행할 필요는 없습니다.** 새 에이전트 서버·Docker·Storage·임베딩 배포는 만들지 않습니다.

이후 명령은 저장소 루트(`rag_lab.py`가 있는 폴더)의 활성화된 가상환경에서 한 개씩 실행합니다. 결과 폴더는 자동으로 만들어집니다.

```bash
python lab.py doctor --live
```

`gpt-6-luna`와 `eval-model`의 `LIVE 조회 OK`를 확인합니다. 이는 배포·평가기 조회 확인이지 Search 준비나 답변 품질의 검증은 아닙니다. 포털과 CLI가 같은 계정·테넌트·구독인지 기본 가이드에서 대조합니다.

**허가된 Basic 이상 검색 서비스가 있으면 재사용**합니다. 완결형에서 만든 서비스도 가능하지만 필수는 아니며, 없다면 2절에서 하나만 만듭니다. 서비스는 공유해도 검색 객체 이름은 두 실습에서 구분합니다. semantic/knowledge retrieval의 Free 요금제와 서비스 SKU는 별개이며, **Basic 서비스는 유지 비용이 발생**합니다. 새 서비스를 자동으로 추가하지 않습니다.

이 실습은 **7개 청크, 4개 질문 × 2개 검색 경로 = 8개 답변, 16개 Judge 지표**입니다. 검색 요청·평가기 내부 호출은 별도입니다. 모델 생성·평가는 유료이며, Free 검색 할당량을 넘으면 오류가 날 수 있습니다. 리소스 보존과 무료 사용은 같은 뜻이 아닙니다.

**생성 전에** 서비스 생성·사용·유지 비용과 아래 두 역할의 서비스 범위 할당을 소유자에게 승인받습니다. 역할 할당에는 해당 범위의 `roleAssignments/write` 권한이 필요하며 일반 Contributor만으로는 부족합니다. 권한 있는 담당자가 준비할 수 없다면 여기서 중단합니다.

<a id="create-search"></a>
## 2. Search 서비스와 최소 권한

아래 `YOUR-...`를 실제 값으로 바꿉니다. 기본 실습의 전용 그룹을 사용해도 됩니다. 서비스 이름은 전역에서 고유한 소문자·숫자·하이픈이어야 합니다.

**허가된 Basic 이상 서비스가 이미 있으면 아래 두 명령을 건너뛰고 그 서비스의 URL·권한을 사용합니다.** `az search service create`는 기존 서비스를 갱신할 수도 있으므로 재사용할 이름으로 실행하지 않습니다. 아래 생성은 아직 서비스가 없는 경우에만 수행합니다.

**신규 생성 전에:** Azure 포털 → **Subscriptions → 사용할 구독 → Resource providers**에서 **`Microsoft.Search`**를 확인합니다. 미등록이면 권한 있는 담당자가 **Register** 후 `Registered`를 확인합니다. 공통 준비의 `Microsoft.CognitiveServices` 등록만으로 대신할 수 없습니다. [공급자 등록 공식 안내](https://learn.microsoft.com/azure/azure-resource-manager/management/resource-providers-and-types)에 따라 필요한 공급자만 등록합니다. 기존 Search가 다른 그룹에 있다면 아래 `YOUR-LAB-RESOURCE-GROUP`에는 그 서비스의 실제 그룹을 넣습니다.

```bash
az search service check-name-availability --name "YOUR-SEARCH-NAME" --type searchServices --subscription "YOUR-SUBSCRIPTION-ID"
```

`nameAvailable: true`일 때만 새 이름으로 생성합니다.

```bash
az search service create --name "YOUR-SEARCH-NAME" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku basic --identity-type SystemAssigned --semantic-search free --disable-local-auth true
```

이 명령은 **API 키를 비활성화**합니다. 키를 조회하거나 설정 파일에 저장하지 않습니다. 생성 후 포털의 **Tags**에서 보존 의도인 `retain=true`를 기록해도 됩니다. 태그는 삭제 잠금이 아닙니다.

<a id="search-access"></a>
### 사용자 ID와 Search 역할

신규·기존 서비스 모두 실제 ID를 조회합니다.

```bash
az search service show --name "YOUR-SEARCH-NAME" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth,semanticSearch:semanticSearch}" --output json
```

`Succeeded/succeeded`, `swedencentral`, Basic 이상 SKU, `disableLocalAuth: true`를 확인합니다. `semanticSearch`는 `free` 또는 이미 승인된 `standard`여야 합니다. 기존 설정 변경은 소유자 승인 없이 하지 않습니다. 아래 `YOUR-SEARCH-RESOURCE-ID`는 이 `id`이며 `/providers/Microsoft.Search/searchServices/...`로 끝납니다.

현재 로그인한 **본인의 사용자 Object ID**를 조회합니다. 기본 포털 준비에서 기록한 프로젝트 관리 ID와는 다릅니다.

```bash
az ad signed-in-user show --query "{account:userPrincipalName,objectId:id}" --output json
```

`account`가 사용할 테넌트의 본인인지 확인한 뒤, **`objectId`를 `YOUR-USER-OBJECT-ID`에 사용**합니다. 프로젝트나 Search 관리 ID를 넣지 않습니다. 조회가 제한되면 환경 소유자에게 같은 테넌트의 본인 ID 대조를 요청합니다. Search의 **Access control (IAM)**에서 상속된 역할까지 확인하고, 다음 역할은 **Search 서비스 범위에서만**, 기존 역할이 없는 경우에만 할당합니다.

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

첫 역할은 **Search Service Contributor**(인덱스·Knowledge 객체뿐 아니라 서비스 설정 관리·키 조회 권한도 포함), 두 번째는 **Search Index Data Contributor**(문서 업로드·조회·Knowledge Base retrieve)입니다. 구독 전체에 할당하지 않습니다. **이 서비스 범위 역할은 다른 참가자의 객체에도 적용되므로 이름 구분은 보안 경계가 아닙니다.** 승인된 공동 실습 범위에서만 사용합니다. 이 사용자 애플리케이션 경로는 프로젝트 관리 ID로 검색하지 않으므로 불필요한 관리 ID 역할을 추가하지 않습니다.

**완료 확인:** 본인의 Object ID에 두 역할이 유효한지 확인하고 전파를 기다립니다. 역할 생성 성공만으로 데이터 접근이 입증되지는 않습니다. 3–4절에서 401/403이 나면 본인·범위·네트워크·전파를 확인한 뒤 같은 명령으로 재개합니다. 역할을 반복 생성하거나 키로 우회하지 않습니다.

<a id="index"></a>
## 3. 실제 인덱스와 Foundry IQ Knowledge Base 생성

**VS Code에서** [설정 예제](../optional-rag/config.example.json)를 열고 **File → Save As**로 저장소 루트의 `rag_lab.py` 옆 **`config.rag.json`**을 만듭니다. `optional-rag/` 안이나 `config.rag.json.txt`로 저장하지 않습니다. 이미 본인 설정이 있다면 덮어쓰지 말고 확인합니다. Search Overview의 실제 서비스 URL을 넣고 저장하며, 공통 준비의 **`config.json`도 그대로 유지**합니다. 두 파일이 모두 필요합니다.

```json
{
  "search_endpoint": "https://YOUR-SEARCH.search.windows.net",
  "index_name": "travel-rag-index",
  "knowledge_source": "travel-policy-ks",
  "knowledge_base": "travel-policy-kb",
  "top_k": 3
}
```

예제의 세 객체 이름은 기본값입니다. **공유 서비스에서는 실행 전에** `index_name`·`knowledge_source`·`knowledge_base`를 허가된 참가자별 이름(예: `travel-rag-a7k3m9`, `travel-policy-ks-a7k3m9`, `travel-policy-kb-a7k3m9`)으로 정합니다. 같은 실험을 재개할 때는 이름과 `top_k: 3`을 유지하며 완결형 객체를 지정하지 않습니다.

```bash
python rag_lab.py setup
```

코드는 기존 세 객체의 정의를 먼저 대조한 뒤 인덱스 생성 → 문서 업로드 → Knowledge Source → Knowledge Base 순서로 없는 객체를 만듭니다.

**완료 확인:** `SETUP OK: 7 chunks, 4 evaluation cases`. `results/rag-setup.json`에 실제 인덱스, Knowledge Source, Knowledge Base 정의가 저장됩니다. 검색 성공은 다음 절의 두 질의로 별도 확인합니다.

[청크](../optional-rag/documents.jsonl)는 기본 가상 규정을 7개 문서로 나눕니다. 공식 청크 6개와 미승인 초안 1개이며, 검색 요청의 **`approved eq true`** 필터로 초안을 제외합니다. `corpus_hash` 필터는 같은 코퍼스 버전만 사용하게 합니다. 한국어 분석기와 semantic 구성이 포함됩니다.

`setup`은 같은 코퍼스의 미완료 업로드는 재개할 수 있지만, 다른 코퍼스/소스가 있는 객체는 덮어쓰지 않습니다. 바꿀 때는 새 객체 이름으로 별도 실험을 만듭니다.

**선언된 설정이 다르면 생성·업로드 전에 중단합니다.** 인덱스의 분석기·semantic 구성, Source의 반환 필드, Knowledge Base의 소스 목록 등을 비교하며 서버가 추가한 기본 속성은 허용합니다. 재사용에는 여전히 소유자의 허가가 필요하고, 실험 중에는 검색 객체를 수정하지 않습니다.

**구분:** 서비스 RBAC는 접근 권한입니다. `approved`는 교육용 문서의 공식 여부 필터이지 사용자별 ACL이 아닙니다. 문서별 보안·Purview·개인별 접근 통제는 이 실습의 검증 범위가 아닙니다.

<a id="retrieve"></a>
## 4. 두 실제 검색 경로 확인

```bash
python rag_lab.py query --mode search --query "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?" --out results/rag-query-search.json
```

**완료 확인:** `RETRIEVAL OK: search`와 선택된 청크 ID가 보이고 `results/rag-query-search.json`이 저장됩니다. 오류라면 여기서 해결하고, 완료 후에만 같은 질문으로 IQ를 조회합니다.

```bash
python rag_lab.py query --mode iq --query "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?" --out results/rag-query-iq.json
```

**완료 확인:** `RETRIEVAL OK: iq`, 선택된 청크 ID·공식 `source_id`·점수와 **`searchIndex` 활동**이 보이고 `results/rag-query-iq.json`이 저장됩니다. 저장한 JSON의 `raw_response`가 실제 서비스 응답이며 IQ 원본 참조/문서 데이터를 포함하고, `documents`가 모델에 전달할 선택 결과입니다. 두 질의는 답변을 생성하거나 Judge를 실행하지 않습니다.

| ID | 의미 |
|---|---|
| `current-lodging` 같은 청크 ID | 검색 평가에서 기대 문서를 찾았는지 확인 |
| `TRAVEL-CURRENT` 같은 `source_id` | 답변의 `citations`에 넣는 공식 문서 ID |
| IQ 참조의 `id` / `activitySource` | 해당 조회 응답 안에서 문서와 검색 활동을 연결 |

IQ는 `intents` 입력을 사용합니다. 앱은 반환된 승인 문서 중 최대 3개만 사용하며, **검색이 비거나 실패하면 전체 규정을 대신 넣지 않고 오류로 중단**합니다.

<a id="evaluate"></a>
## 5. 검색과 답변을 각각 평가

[질문 4개](../optional-rag/cases.jsonl)는 기본 dev의 D02·D03·D04·D08을 재사용합니다. 새로운 독립 holdout이라고 부르지 않습니다. [검색 정답](../optional-rag/retrieval-labels.json)은 평가 전용이며 검색 요청·답변 모델·Judge에 전달하지 않습니다.

두 실행 사이에 질문·코퍼스·`optional-rag/prompt.txt`·설정·답변/Judge 모델 버전·검색 객체를 바꾸지 않습니다. **검색 경로만** 달라야 하며 계약이 다르면 비교가 거부됩니다. 변경이 필요하면 기존 결과를 보존하고 두 경로 모두 새 출력 폴더에서 별도 실험으로 시작합니다.

```bash
python rag_lab.py run --mode search --out results/rag-search
```

`LIVE RAG generation complete: 4 answers`와 `results/rag-search/run.json`의 `status: complete`를 확인하고 채점합니다. 생성 완료는 업무 검사 통과와 다릅니다.

```bash
python lab.py judge results/rag-search
```

**`평가 완료: 4개 답변 × 2개 지표`**까지 기다립니다. 대기 중이면 같은 명령을 재실행합니다. 중단·오류는 [재개 표](#resume)를 따릅니다.

```bash
python rag_lab.py run --mode iq --out results/rag-iq
```

**`LIVE RAG generation complete: 4 answers`**가 나온 뒤에만 아래 채점 명령으로 갑니다.

```bash
python lab.py judge results/rag-iq --like results/rag-search
```

IQ도 4개 생성 완료 후 **`평가 완료: 4개 답변 × 2개 지표`**를 확인합니다. `--like`는 Search의 완료된 Judge 모델·평가기 계약을 유지하며, 검색 문맥이나 답변을 복사하지 않습니다.

```bash
python rag_lab.py compare results/rag-search results/rag-iq
```

**완료 확인:** `REVIEW_REQUIRED`와 `Comparison: results/rag-iq/rag-comparison.md`가 보입니다. 비교 파일 생성이 끝났다는 뜻이며, 아래에서 실제 사례를 읽고 판단합니다.

```bash
python rag_lab.py inspect results/rag-iq D04
```

**읽는 순서:** 실제 검색 청크 → 기대 청크 누락 → 답변 JSON → 업무 검사 → Groundedness/Relevance 이유입니다. Judge에 전달되는 `context`는 **그 답변을 생성할 때 사용한 검색 문맥과 동일**합니다.

| 지표 | 의미와 한계 |
|---|---|
| Required-chunk Recall@3 | 필요한 청크 중 모델에 전달된 청크의 비율 |
| Precision@3 | 전달된 청크 중 지정한 필수 청크의 비율. 다른 유용한 보조 청크는 정답에 없을 수 있음 |
| 업무 검사 | 결정·금액·출처·형식의 정확성 |
| Groundedness | 검색되어 전달된 근거에 답변이 충실한가 |
| Relevance | 질문을 적절히 다루는가. 올바른 정보 부족 처리도 낮게 채점될 수 있음 |
| Citation IDs linked | 인용 ID가 검색 문서에 존재하는가. 의미상 뒷받침까지 보장하지 않음 |

`results/rag-iq/rag-comparison.md`·`.json`과 각 폴더의 `rag-report.md`, `retrieval-metrics.json`을 확인합니다. 비교의 종료 코드 0은 비교 파일을 만들었다는 뜻이며 **상태는 항상 `REVIEW_REQUIRED`**입니다. `issues`가 비어 있어도 출시 승인이나 IQ 우수성 증명이 아닙니다. `issues`에는 80% 미만 지표와 중요 사례 실패가 표시되고 Judge 통과 기준은 4/5입니다. 실제 문맥·채점 이유를 사람이 검토합니다.

기본 `lab.py compare/gate`는 고정 문서 실험용이므로 RAG 입력을 거부합니다. RAG는 위 전용 비교를 사용합니다. 기본 실습과 이 실습의 결과·합격률을 하나의 전후 실험처럼 합치지 않습니다.

<a id="resume"></a>
### 명령 상태·중단·재개

<details>
<summary>대기·오류가 나거나 나중에 재개할 때만 펼치기</summary>

새 터미널에서는 가상환경·로그인 상태를 복원합니다. 같은 출력 폴더를 두 터미널에서 동시에 사용하지 않습니다.

| 상태 | 다음 행동 |
|---|---|
| `setup`의 연결 오류·중단 | 원인 해결 후 같은 설정으로 `setup` 재실행. 일치하는 객체와 같은 코퍼스의 미완료 업로드를 재사용/완료. 불일치는 덮어쓰지 않음 |
| `run`의 연결 오류·중단 | 같은 `--mode`·`--out`을 포함한 명령 전체를 재실행. 저장된 응답과 `pending_retrievals`의 검색을 재사용. 응답 직후 저장 전에 끊긴 호출은 재청구될 수 있음 |
| `run.json`의 `status: collecting` | 부분 실행. 저장된 `rows`·`pending_retrievals`와 오류를 확인하며 아직 `judge`·`inspect`·`compare`를 실행하지 않음 |
| `Using completed LIVE evidence; no new retrieval or generation calls.` | 같은 입력의 완료 결과를 재사용함. 새 `LIVE RAG generation complete` 메시지가 없어도 정상. 해당 경로의 채점 등 다음 미완료 단계로 이동 |
| Judge 대기 / 종료 코드 `3` | 같은 `python lab.py judge …` 전체 명령 재실행. IQ의 `--like`도 유지. 기본 상태 조회 대기 예산은 **300초**이며 전체 명령 시간은 더 길 수 있음 |
| 생성/채점 완료지만 낮은 점수·업무 실패 | 저장된 답변을 다시 뽑지 않음. 두 경로 채점 완료 후 전용 비교로 실패를 보존 |
| `ERROR:` / 인자 오류 | 원인을 해결한 뒤 같은 명령으로 재개. 완료되지 못하면 마지막 완료 단계와 미실행 항목을 구분해 6절에서 보존 |

| 파일 | 확인할 내용 |
|---|---|
| `results/rag-setup.json`, `results/rag-query-search.json`, `results/rag-query-iq.json` | 객체 정의와 두 검색 probe |
| 각 실행 폴더의 `run.json` | 상태, 로컬 상관관계 `run_id`, 저장된 답변·문맥·검색 원본·미완료 검색 |
| `foundry-job.json` | 원격 `eval_id`·`run_id`·작업 상태. `run.json`의 ID와 구분 |
| `judge.json`, `report.md` | 완료된 점수와 사례별 이유. 원격 `completed`만으로 완료 판단하지 않음 |
| `rag-report.md`, `retrieval-metrics.json` | RAG 근거·검색 지표. `lab.py judge`는 `report.md`를 갱신하며 RAG 보고서는 `rag_lab.py compare`/`inspect`에서 갱신 |

원격 작업 생성 여부가 불명확하면 [ID 복구](reference.md#resume)를 따르고 새 작업을 강제로 제출하지 않습니다. 파일을 지워 좋은 답이나 점수를 다시 뽑지 않습니다.

</details>

<a id="evidence"></a>
## 6. 포털·원본 증거·보존

**완료 체크리스트:** 본인의 결과로 아래 항목을 확인합니다. 검색 경로의 점수가 같거나 낮아도 비교는 유효하며, 실행 오류나 누락은 먼저 해결합니다.

- [ ] `results/rag-search`·`results/rag-iq` 각각 답변 4개와 두 Judge 점수·이유가 있다.
- [ ] `results/rag-iq/rag-comparison.md`에서 검색 지표와 답변 지표를 구분해 읽었다.
- [ ] D04의 실제 검색 문맥·답변·점수 이유를 대조했고 `REVIEW_REQUIRED`가 출시 승인이 아님을 이해했다.
- [ ] 본인 결과 폴더와 실제 자원을 보존하고 [비용 확인](cleanup.md#retain-resources)을 마쳤다.

Azure 포털의 해당 Search 서비스에서 **Indexes**, **Knowledge sources**, **Knowledge bases**를 확인합니다. 포털 메뉴/미리 보기 기능은 API와 다를 수 있으므로 생성·조회 확인의 기준은 저장한 서비스 응답입니다.

Foundry의 Judge 보고서 URL에서는 같은 사례의 **질문·답변·검색 문맥·두 점수·이유**를 대조합니다. 기본 실습처럼 전체 규정이 `context`에 들어가 있으면 잘못 연결한 것입니다.

`run.json`에는 경로·설정·코퍼스 해시·검색 원본·참조·활동·실제 문맥과 해시·모델 답변이 남습니다. 검색은 끝났지만 생성이 끊겼다면 저장된 검색을 재사용합니다. 완료된 `run`은 새 유료 호출 없이 기록을 읽습니다.

- Search 서비스와 Knowledge 객체, 기존 Foundry 자원·평가 결과는 **모두 유지**합니다.
- Free 할당량 초과를 이유로 자동으로 유료 요금제로 전환하지 않습니다.
- 로컬 `config.rag.json`, `config.json`, `results/`는 Git에 올리지 않습니다.
- 답이 틀렸거나 점수가 낮으면 그대로 기록하며, 좋은 점수를 얻으려고 다시 뽑지 않습니다.

<a id="observed-results"></a>
### 이전 최소 RAG 기록과 참고 범위

작성자의 이전 Free 서비스·기록 정리는 과거 전환 기록이지 참가자의 삭제 단계나 현재 자원 상태 확인이 아닙니다. [완결형의 기록된 결과](complete-lab.md#results)는 별도 벡터·계획·대화 실험의 관측값이며, 이 최소 RAG의 `search`/`iq` 비교를 재검증한 증거는 아닙니다. 이 API 연습은 허가된 Basic 서비스의 별도 인덱스에서 실행하고, 본인의 `rag-comparison.md`와 각 `rag-report.md`로 판단합니다.

<a id="troubleshooting"></a>
## 문제 해결

| 증상 | 조치 |
|---|---|
| Basic 서비스 생성 불가 | `Microsoft.Search` 등록, 허가된 기존 서비스, 지역 용량·구독 제한·조직 정책을 점검. 다른 서비스를 삭제하거나 Free로 임의 대체하지 않기 |
| 401/403 | 실제 CLI 계정·테넌트, Search 두 역할과 범위·전파 확인. API 키로 우회하지 않기 |
| MCP 도구만 `invalid_token` | MCP와 CLI 인증이 다를 수 있음. 이 실습의 명시적 `AzureCliCredential` 경로를 확인하고 도구 인증은 별도 점검 |
| `queryLanguage`가 유효하지 않음 | 이 API 버전의 요청에는 넣지 않음. 제공된 코드와 한국어 인덱스 분석기 사용 |
| 출력 크기는 5000보다 커야 함 | 제공 코드는 IQ 출력 상한 6000토큰을 사용. 모델에 전달하는 문서는 여전히 최대 3개 |
| 206/부분 검색, 참조 문서 누락, 검색 0건 | 원인을 해결하고 재개. 전체 규정을 넣는 숨은 fallback 금지 |
| 다른 코퍼스/객체 계약 | 기존 객체를 덮어쓰지 말고 새 이름·출력 폴더로 별도 실험 |
| Judge `completed`만 출력 | 로컬 점수·이유 저장까지 대기. 종료 코드 3이면 같은 명령 재실행 |
| 기본 compare/gate가 RAG를 거부 | `rag_lab.py compare` 사용 |
| 조직 `PolicyDeployment` 진단 실패 | 별도 중앙 작업 영역/정책 담당자에게 전달. 정책 해제나 기록 삭제 금지 |

<a id="sources"></a>
## 공식 출처

- [Foundry IQ와 사용자 애플리케이션 REST 사용](https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-foundry-iq)
- [Knowledge Source 생성](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-search-index)
- [Knowledge Base 생성과 GA/preview 차이](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base)
- [Search 역할·권한 할당·서비스 범위](https://learn.microsoft.com/azure/search/search-security-rbac)
- [실제 retrieve API](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve)
- [지역 및 Free 지원](https://learn.microsoft.com/azure/search/search-region-support)
- [Knowledge retrieval 요금제](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable)

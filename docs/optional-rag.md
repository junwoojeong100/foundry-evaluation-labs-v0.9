[English](en/optional-rag.md) | **한국어**

# Optional: Azure AI Search + Foundry IQ RAG와 Evaluation

[기본 실습](../README.ko.md) · [영문 기본 가이드](../README.md)

**기본 실습 0–6을 대체하지 않는 선택 실습**입니다. 기본 경로는 전체 규정을 직접 전달합니다. 여기서는 **실제 검색된 문서만** 모델과 Groundedness 평가기에 전달하고, **검색이 맞았는지와 답변이 맞았는지**를 따로 봅니다.

기존 계정·Foundry 프로젝트·`gpt-6-luna` 배포 `eval-model`·`swedencentral`을 재사용합니다. Azure AI Search 서비스, 인덱스, 실제 Foundry IQ Knowledge Source/Knowledge Base를 추가합니다. 생성한 리소스와 결과는 **삭제하지 않습니다**.

**추가 요약 영상:** [국문·영문 Optional RAG 영상과 자막](media/optional-rag/README.md).

## 무엇을 사용하는가

| 경로 | 실제 실행 |
|---|---|
| `search` | Azure AI Search 인덱스에 semantic 검색 요청 |
| `iq` | Foundry IQ Knowledge Base의 `retrieve` API → search-index Knowledge Source → 같은 인덱스 |
| 공통 | 반환된 승인 문서 중 상위 3개 → `gpt-6-luna` 답변 → 코드 검사·검색 평가·Foundry Evaluation |

**Foundry IQ를 이름만 붙인 로컬 검색으로 대체하지 않습니다.** Knowledge Base/Source를 실제 서비스에 생성하고, IQ 응답의 `references`, `sourceData`, `activity`를 저장합니다.

이 간단한 경로는 **정식 Search API `2026-04-01`의 minimal/extractive 검색**을 사용합니다. 벡터 임베딩, LLM 쿼리 계획, answer synthesis, Agent Service/MCP 연결은 사용하지 않습니다. `gpt-6-luna`는 검색 계획 모델이 아니라 **애플리케이션의 답변 생성·평가 모델**입니다. Foundry IQ는 사용자 애플리케이션에서 Knowledge Base REST API로 직접 사용할 수 있습니다.

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

기본 실습의 가상환경·`requirements.txt`·실제 `config.json`과 모델 배포가 필요합니다. 새 에이전트 서버·Docker·Storage·임베딩 배포는 만들지 않습니다.

```bash
python lab.py doctor --live
```

`gpt-6-luna`와 `eval-model`의 `LIVE 조회 OK`를 확인합니다. 포털과 CLI가 같은 계정·테넌트·구독인지 기본 가이드에서 대조합니다.

Search **Free SKU**와 semantic/knowledge retrieval의 **Free 요금제**를 사용합니다. Sweden Central의 지원 여부와 구독의 Free 서비스 슬롯을 확인해야 합니다. Free 슬롯이 이미 사용 중이면 기존 서비스를 삭제하지 않습니다. 허가받은 기존 환경을 사용하거나, **유지 중 비용이 발생하는 Basic 이상을 별도로 선택·승인한 뒤** 진행합니다. 자동 업그레이드는 하지 않습니다.

이 실습은 **7개 청크, 4개 질문 × 2개 검색 경로 = 8개 답변, 16개 Judge 지표**입니다. 검색 요청·평가기 내부 호출은 별도입니다. 모델 생성·평가는 유료이며, Free 검색 할당량을 넘으면 오류가 날 수 있습니다. 리소스 보존과 무료 사용은 같은 뜻이 아닙니다.

<a id="create-search"></a>
## 2. Search 서비스와 최소 권한

아래 `YOUR-...`를 실제 값으로 바꿉니다. 기본 실습의 전용 그룹을 사용해도 됩니다. 서비스 이름은 전역에서 고유한 소문자·숫자·하이픈이어야 합니다.

```bash
az search service check-name-availability --name "YOUR-SEARCH-NAME" --type searchServices --subscription "YOUR-SUBSCRIPTION-ID"
```

`nameAvailable: true`일 때만 새 이름으로 생성합니다.

```bash
az search service create --name "YOUR-SEARCH-NAME" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku free --semantic-search free --disable-local-auth true
```

이 명령은 **API 키를 비활성화**합니다. 키를 조회하거나 설정 파일에 저장하지 않습니다. 생성 후 포털의 **Tags**에서 보존 의도인 `retain=true`를 기록해도 됩니다. 태그는 삭제 잠금이 아닙니다.

서비스의 실제 ID를 조회합니다.

```bash
az search service show --name "YOUR-SEARCH-NAME" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth,semanticSearch:semanticSearch}" --output json
```

`Succeeded/succeeded`, Sweden Central, `free`, `disableLocalAuth: true`를 확인합니다. 아래 `YOUR-SEARCH-RESOURCE-ID`는 이 `id`이며 `/providers/Microsoft.Search/searchServices/...`로 끝납니다.

기본 가이드에서 확인한 **본인 Object ID**에 다음 역할을 **Search 서비스 범위에서만**, 없는 경우에만 할당합니다.

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

첫 역할은 **Search Service Contributor**(인덱스·Knowledge 객체 관리), 두 번째는 **Search Index Data Contributor**(문서 업로드·조회)입니다. 구독 전체에 할당하지 않습니다. 이 사용자 애플리케이션 경로는 프로젝트 관리 ID로 검색하지 않으므로 불필요한 관리 ID 역할을 추가하지 않습니다.

<a id="index"></a>
## 3. 실제 인덱스와 Foundry IQ Knowledge Base 생성

[설정 예제](../optional-rag/config.example.json)를 `lab.py` 옆 **`config.rag.json`**으로 저장합니다. Search Overview의 실제 서비스 URL을 넣습니다. 기존 `config.json`은 그대로 둡니다.

```json
{
  "search_endpoint": "https://YOUR-SEARCH.search.windows.net",
  "index_name": "travel-rag-index",
  "knowledge_source": "travel-policy-ks",
  "knowledge_base": "travel-policy-kb",
  "top_k": 3
}
```

```bash
python rag_lab.py setup
```

**완료 확인:** `SETUP OK: 7 chunks, 4 evaluation cases`. `results/rag-setup.json`에 실제 인덱스, Knowledge Source, Knowledge Base 정의가 저장됩니다.

[청크](../optional-rag/documents.jsonl)는 기본 가상 규정을 7개 문서로 나눕니다. 공식 청크 6개와 미승인 초안 1개이며, 검색 요청의 **`approved eq true`** 필터로 초안을 제외합니다. `corpus_hash` 필터는 같은 코퍼스 버전만 사용하게 합니다. 한국어 분석기와 semantic 구성이 포함됩니다.

`setup`은 같은 코퍼스의 미완료 업로드는 재개할 수 있지만, 다른 코퍼스/소스가 있는 객체는 덮어쓰지 않습니다. 바꿀 때는 새 객체 이름으로 별도 실험을 만듭니다.

**구분:** 서비스 RBAC는 접근 권한입니다. `approved`는 교육용 문서의 공식 여부 필터이지 사용자별 ACL이 아닙니다. 문서별 보안·Purview·개인별 접근 통제는 이 실습의 검증 범위가 아닙니다.

<a id="retrieve"></a>
## 4. 두 실제 검색 경로 확인

```bash
python rag_lab.py query --mode search --query "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?" --out results/rag-query-search.json
```

```bash
python rag_lab.py query --mode iq --query "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?" --out results/rag-query-iq.json
```

**완료 확인:** 각각 `RETRIEVAL OK`, 선택된 청크 ID·공식 `source_id`·점수가 나옵니다. IQ에는 **`searchIndex` 활동과 원본 참조/문서 데이터**가 있습니다. 두 JSON은 실제 서비스 응답입니다.

| ID | 의미 |
|---|---|
| `current-lodging` 같은 청크 ID | 검색 평가에서 기대 문서를 찾았는지 확인 |
| `TRAVEL-CURRENT` 같은 `source_id` | 답변의 `citations`에 넣는 공식 문서 ID |
| IQ 참조의 `id` / `activitySource` | 해당 조회 응답 안에서 문서와 검색 활동을 연결 |

IQ는 `intents` 입력을 사용합니다. 앱은 반환된 승인 문서 중 최대 3개만 사용하며, **검색이 비거나 실패하면 전체 규정을 대신 넣지 않고 오류로 중단**합니다.

<a id="evaluate"></a>
## 5. 검색과 답변을 각각 평가

[질문 4개](../optional-rag/cases.jsonl)는 기본 dev의 D02·D03·D04·D08을 재사용합니다. 새로운 독립 holdout이라고 부르지 않습니다. [검색 정답](../optional-rag/retrieval-labels.json)은 평가 전용이며 검색 요청·답변 모델·Judge에 전달하지 않습니다.

```bash
python rag_lab.py run --mode search --out results/rag-search
```

4개 답변 저장을 확인하고 채점합니다.

```bash
python lab.py judge results/rag-search
```

**`평가 완료: 4개 답변 × 2개 지표`**까지 기다립니다. 대기 중이면 같은 명령을 재실행합니다.

```bash
python rag_lab.py run --mode iq --out results/rag-iq
```

```bash
python lab.py judge results/rag-iq --like results/rag-search
```

**`평가 완료: 4개 답변 × 2개 지표`**를 확인합니다. `--like`는 같은 Judge 모델·평가기 계약을 유지합니다.

```bash
python rag_lab.py compare results/rag-search results/rag-iq
```

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

`results/rag-iq/rag-comparison.md`·`.json`과 각 폴더의 `rag-report.md`, `retrieval-metrics.json`을 확인합니다. **`REVIEW_REQUIRED`는 출시 승인이나 IQ 우수성 증명이 아닙니다.** 실제 문맥·채점 이유를 사람이 검토합니다.

기본 `lab.py compare/gate`는 고정 문서 실험용이므로 RAG 입력을 거부합니다. RAG는 위 전용 비교를 사용합니다. 기본 실습과 이 실습의 결과·합격률을 하나의 전후 실험처럼 합치지 않습니다.

<a id="evidence"></a>
## 6. 포털·원본 증거·보존

Azure 포털의 해당 Search 서비스에서 **Indexes**, **Knowledge sources**, **Knowledge bases**를 확인합니다. 포털 메뉴/미리 보기 기능은 API와 다를 수 있으므로 생성·조회 확인의 기준은 저장한 서비스 응답입니다.

Foundry의 Judge 보고서 URL에서는 같은 사례의 **질문·답변·검색 문맥·두 점수·이유**를 대조합니다. 기본 실습처럼 전체 규정이 `context`에 들어가 있으면 잘못 연결한 것입니다.

`run.json`에는 경로·설정·코퍼스 해시·검색 원본·참조·활동·실제 문맥과 해시·모델 답변이 남습니다. 검색은 끝났지만 생성이 끊겼다면 저장된 검색을 재사용합니다. 완료된 `run`은 새 유료 호출 없이 기록을 읽습니다.

- Search 서비스와 Knowledge 객체, 기존 Foundry 자원·평가 결과는 **모두 유지**합니다.
- Free 할당량 초과를 이유로 자동으로 유료 요금제로 전환하지 않습니다.
- 로컬 `config.rag.json`, `config.json`, `results/`는 Git에 올리지 않습니다.
- 답이 틀렸거나 점수가 낮으면 그대로 기록하며, 좋은 점수를 얻으려고 다시 뽑지 않습니다.

<a id="observed-results"></a>
### 2026-09-28 실제 실행 기록

Free Search 서비스와 semantic/knowledge retrieval Free 요금제, API 키 비활성화를 확인했습니다. 실제 인덱스·Knowledge Source·Knowledge Base를 생성하고, **8개 답변·16개 Judge 지표**를 두 완료된 원격 실행에 저장했습니다.

| 경로 | 필수 청크 Recall@3 | 업무 검사 | Groundedness ≥4 | Relevance ≥4 |
|---|---|---|---|---|
| Search | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 3/4 (75%) |
| Foundry IQ | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) | 2/4 (50%) |

**네 질문 모두 두 경로의 실제 검색 문맥이 동일했습니다.** IQ 실행의 D02는 금액·결정은 맞았지만 `SCOPE`를 추가 인용해 정확한 출처 집합 검사에서 실패했습니다. 이는 한 번의 생성·채점에서 나온 차이이며 **IQ 검색이 더 나쁘다는 증거가 아닙니다**. 검색 성공과 답변 성공을 구분하고 `REVIEW_REQUIRED`를 유지했습니다.

평가 결과, 실제 검색 문맥, 원격 원본의 문맥 일치는 로컬 `results/rag-verification.json`과 각 실행 폴더에 기록합니다. 원본 검색·응답·점수는 수정하지 않았고 자원도 삭제하지 않았습니다.

<a id="troubleshooting"></a>
## 문제 해결

| 증상 | 조치 |
|---|---|
| Free 서비스 생성 불가 | 구독의 Free 슬롯·현재 지역 지원 확인. 다른 서비스를 삭제하지 않기 |
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
- [실제 retrieve API](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve)
- [지역 및 Free 지원](https://learn.microsoft.com/azure/search/search-region-support)
- [Knowledge retrieval 요금제](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable)

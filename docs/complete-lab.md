[English](en/complete-lab.md) | **한국어**

# 완결형 실습: 실패 → 개선 → 재평가 → 새 질문 합격

[저장소 기본 가이드](../README.ko.md)

[새 국문·영문 요약 영상](media/complete-rag/README.md)에서 현재 완료된 실습 흐름을 확인합니다.

현재 권장하는 완결형 경로입니다. **Basic 이상 Azure AI Search 서비스 하나**에서 기본 RAG와 **벡터·하이브리드 검색 + Foundry IQ LLM 검색 계획**을 함께 실행합니다. 실습별로 검색 서비스를 만들 필요는 없습니다.

기존 `prompts/v1.txt`·`v2.txt`는 입문 예제의 이력으로 보존합니다. 이 경로는 **`advanced-rag/instructions.v1.txt`·`instructions.v2.txt`**를 명시적으로 사용합니다.

## 합격의 정확한 의미

[acceptance.json](../advanced-rag/acceptance.json)의 기준은 새 질문을 보기 전에 고정합니다.

- **V2의 모든 최종 사례**가 업무 검사·필수 근거 검색·Groundedness·**기본 Relevance**·업무 성공도를 **100% 통과**해야 합니다. 평균으로 실패 사례를 숨기지 않습니다.
- 필수 Judge는 **4/5 이상**, 중요 사례 실패는 **0개**.
- 업무 성공도 Judge는 정상·오답 **교정 사례 10개를 모두 올바르게 구분**해야 함.
- 실제 벡터 인덱스·vectorizer와 `modelQueryPlanning` 활동이 있어야 함.
- 후보를 고정한 뒤 새 holdout을 최소 8개 생성·등록해야 함.

**기본 Relevance도 필수 합격 지표로 유지합니다.** 최종 답변은 실제 완료된 사용자 요청을 해결해야 합니다. 추가 정보 질문은 중간 단계이지 완료 답변으로 표시하지 않습니다.

V2는 평가 데이터에 미리 정한 사용자 후속 응답을 사용합니다. 날짜 누락 사례는 질문 후 사용자의 실제 출장일을 받고, 해외 한도 부재 사례는 금액을 꾸미는 대신 사용자가 재무팀 문의 체크리스트를 요청하는 단계를 거칩니다. 사용자 정보를 모델이 만들어 내지 않습니다. 최종 대화 전체를 Judge에 일관되게 전달하고 초기 추가 질문·안내 행동도 검사합니다.

`LAB_ACCEPTANCE_PASSED`는 위 교육용 기준을 통과했다는 뜻입니다. **실제 사람의 운영 승인과는 별개**입니다.

<a id="architecture"></a>
## 1. 검색 서비스 하나로 구성

| 구성 | 역할 |
|---|---|
| `swedencentral`의 Basic Search 서비스 | 이 경로의 모든 인덱스·지식 기반을 수용 |
| `travel-rag-index` / `travel-policy-kb` | 같은 서비스에서 실행하는 기본 추출형 RAG |
| `travel-vector-index` | 실제 1536차원 HNSW 벡터와 검색 가능한 규정 텍스트 |
| `travel-vector-ks` / `travel-planned-kb` | LLM 검색 계획 모델을 연결한 Foundry IQ |
| `rag-embedding` | 문서·질의 벡터를 만드는 `text-embedding-3-small` |
| `rag-planner` | 지원되는 검색 계획 모델 `gpt-5.4-mini` |
| `eval-model` | 답변·평가에 사용하는 `gpt-6-luna` |

LLM 검색 계획에는 **`2026-08-01-preview`**를 사용합니다. 정식 minimal API와 달리 미리 보기 기능이며, 이를 GA 운영 환경으로 표현하지 않습니다. `low`는 실제 LLM 계획을 수행하고 벡터 필드/vectorizer는 하이브리드 검색에 사용됩니다.

Free 서비스에는 여기서 필요한 아웃바운드 관리 ID 제약이 있습니다. 허가받은 Basic 이상 서비스가 있다면 재사용합니다. **Basic은 유지 중에도 비용이 발생**하며 임베딩·계획·생성·채점 사용량 비용도 발생할 수 있습니다.

<a id="setup"></a>
## 2. Azure 준비와 권한

먼저 [Foundry 계정·프로젝트·모델 준비](../README.ko.md#prepare)를 완료하고, 요청한 계정과 `swedencentral`, `eval-model`을 사용합니다. 이 경로를 위해 별도 Free Search를 만들지 않습니다.

공용으로 사용할 Basic 서비스를 만들거나 기존 허가된 서비스를 사용합니다.

```bash
az search service create --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku basic --replica-count 1 --partition-count 1 --identity-type SystemAssigned --semantic-search free --disable-local-auth true
```

사용자에게 Search 서비스 범위의 **Search Service Contributor**, **Search Index Data Contributor**를 부여하는 방법은 [선택 실습 준비](optional-rag.md#create-search)를 따릅니다. 시스템 할당 관리 ID도 확인합니다.

```bash
az search service show --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,identity:identity,sku:sku.name,state:provisioningState}" -o json
```

이 **Search 관리 ID**에 상위 Foundry 리소스 범위의 **Cognitive Services OpenAI User**를 할당합니다. 프로젝트나 사용자 ID로 대신하지 않습니다.

```bash
az role assignment create --assignee-object-id "YOUR-SEARCH-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

현재 모델·쿼터를 확인한 뒤 두 모델을 **순서대로** 배포합니다. 같은 Foundry 계정에 동시 쓰기를 하면 충돌할 수 있습니다.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-embedding --model-name text-embedding-3-small --model-version "YOUR-EMBEDDING-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 40 --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-planner --model-name gpt-5.4-mini --model-version "YOUR-PLANNER-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

확인한 버전은 임베딩 `1`, 계획 모델 `2026-03-17`, 답변 모델 `gpt-6-luna` `2026-09-22`입니다. 저장된 V1과의 비교는 같은 답변 모델 버전이 필요하며 다른 버전과 임의 비교하지 않습니다.

[설정 예제](../advanced-rag/config.example.json)를 **`config.advanced.json`**으로 저장합니다. 실제 공용 Search URL과 Foundry 계정의 **`.openai.azure.com` 리소스 주소**를 넣습니다.

임베딩은 계정의 `/openai/v1/embeddings` 주소에서 Entra 인증으로 호출합니다. 이 환경의 프로젝트 게이트웨이는 채팅·평가는 지원했지만 임베딩 호출에는 404를 반환했습니다. API 키는 사용하지 않습니다.

```bash
python advanced_lab.py setup
```

**완료 확인:** `VECTOR SETUP OK: 7 documents, 1536 dimensions`. `results/advanced/setup.json`에서 실제 텍스트·벡터·HNSW·vectorizer·Knowledge Source·계획형 Knowledge Base를 확인합니다.

이 Basic URL을 기존 [기본 추출형 RAG](optional-rag.md)의 `config.rag.json`에도 사용할 수 있습니다. 두 경로의 인덱스·Knowledge Base 이름은 구분합니다.

<a id="retrieval-proof"></a>
## 3. 벡터와 LLM 계획이 실제로 실행되는지 확인

```bash
python advanced_lab.py query --mode vector --query "해외 출장 호텔 숙박비 상한을 확인하고 싶습니다." --out results/advanced/vector-query.json
```

**완료 확인:** 질의 벡터 1536차원, `content_vector`, `text_query: false`, 실제 검색 청크.

```bash
python advanced_lab.py query --mode planned --query "2026년 6월 30일과 7월 1일 국내 출장 숙박 한도를 비교하고, 한도를 초과할 때 필요한 절차와 해외 숙박 한도가 있는지도 알려주세요." --out results/advanced/planned-query.json
```

**완료 확인:** `llm_query_planning: true`, 실제 생성된 검색어, `modelQueryPlanning`·`searchIndex` 활동. 확인한 요청은 세 하위 질의를 생성했습니다. 계획 증거가 없으면 코드가 오류로 중단하며 일반 검색을 계획형이라고 부르지 않습니다.

<a id="calibration"></a>
## 4. Judge 교정과 고정

[업무 성공도 기준](../advanced-rag/policy-task-success.txt)을 읽습니다. 필요한 날짜를 묻거나 규정에 없는 금액을 만들지 않는 답은 정상으로 인정하고, 잘못된 금액·승인 조작·설명 모순은 구분합니다.

```bash
python advanced_lab.py calibrate
```

**완료 확인:** `CALIBRATION PASSED: 10 controls`. 정상 4개와 오답 6개를 모두 구분해야 합니다. 오답에는 채점 지침 무시 요청과 불필요한 인용도 있습니다. 정답/오답 **통과 라벨은 Judge 입력으로 보내지 않습니다**.

평가기 버전·지침·모델·합격 기준은 `results/advanced/judge-contract.json`에 고정됩니다. Holdout 결과를 보고 Judge를 바꿔도 된다는 뜻이 아닙니다.

<a id="improve"></a>
## 5. 실제 V1 실패와 통제된 V2 개선

[V1 기록](../advanced-rag/fixtures/recorded-v1.json)은 정리된 **실제 이전 LIVE 답변 4개**입니다. 억지로 만든 오답이 아니며, D02의 불필요한 출처를 그대로 보존했습니다. 이를 다시 읽는 일을 새로운 생성이라고 표현하지 않습니다.

```bash
python advanced_lab.py baseline
```

```bash
python advanced_lab.py judge --stage v1-recorded
```

[V1](../advanced-rag/instructions.v1.txt)과 [V2](../advanced-rag/instructions.v2.txt)를 비교합니다. V2는 최소 충분한 근거를 선택하고, 필요한 추가 정보 요청·업무 이관 대화까지 마무리합니다.

[개발용 후속 응답](../advanced-rag/dev-followups.json)은 생성 전에 정합니다. 실제 고객의 발언이나 사람의 운영 승인이 아니라 명시적인 평가용 사용자 대화 데이터이며, 원하는 점수는 포함하지 않습니다.

```bash
python advanced_lab.py run --stage v2-replay
```

```bash
python advanced_lab.py judge --stage v2-replay
```

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D02
```

**완료 확인:** 같은 초기 저장 문맥·답변 모델·생성 설정·Judge에서 시작합니다. V2는 필요한 사용자 후속 대화를 추가로 완료합니다. **지침과 대화 완료 절차를 개선한 것**이며 지침 문구만의 효과라고 주장하지 않습니다. V1을 일부러 약화하거나 실패할 때까지 다시 뽑지 않습니다.

<a id="freeze"></a>
## 6. 전체 파이프라인을 확인한 뒤 고정

```bash
python advanced_lab.py run --stage planned-dev
```

```bash
python advanced_lab.py judge --stage planned-dev
```

실제 벡터·LLM 계획 검색을 사용하는 별도의 통합 확인입니다. 초기 질문과 필요한 후속 대화 모두 정해진 검색 절차를 사용합니다.

```bash
python advanced_lab.py freeze
```

**완료 확인:** `FROZEN`과 계약 해시. 실제 V1 실패가 있어야 하며 V2 동일 문맥 및 계획형 dev가 기준을 통과해야 합니다. 지침·Judge·모델 버전·검색 설정·소스 정의·코퍼스를 새 질문 생성 전에 고정합니다.

<a id="holdout"></a>
## 7. 고정한 뒤 새 질문 생성

```bash
python advanced_lab.py create-holdout
```

새 난수 시드로 균형 잡힌 시나리오 8개를 만듭니다. 현재/과거 한도, 한도 초과 승인, 해외 범위, 날짜 누락, 금지 좌석, 경계값을 포함합니다. 날짜 누락과 해외 이관 사례에는 명시적인 평가용 사용자 후속 응답이 있습니다. 질문·후속 응답·정답·생성 근거는 `results/advanced/holdout-data/`에 저장합니다.

이미 있으면 덮어쓰지 않습니다. 합격하려고 질문을 다시 뽑지 않습니다.

```bash
python advanced_lab.py run --stage holdout
```

```bash
python advanced_lab.py judge --stage holdout
```

```bash
python advanced_lab.py accept
```

**완료 확인:** `LAB_ACCEPTANCE_PASSED`, 완료된 새 시나리오 8개, **Relevance를 포함한 모든 최종 응답 지표 통과**. `results/advanced/acceptance-report.md`·`acceptance-result.json`에서 확인합니다. 초기 추가 질문·안내의 검사도 통과해야 합니다.

차단되면 실패를 보존합니다. 고정된 지침·Judge를 바꾸거나 합격 사례만 고르지 않습니다. 다음 개선은 별도의 실험과 새로운 holdout으로 진행해야 합니다.

<a id="results"></a>
## 결과 해석

앞서 Relevance를 제외했던 시도는 **최종 성공 결과가 아닙니다**. 새 반복에서는 모든 최종 V2 사례가 모든 지표를 통과했습니다.

| 단계 | 업무 | 검색 | Groundedness | Relevance | 업무 성공도 |
|---|---|---|---|---|---|
| 기록된 V1 단일 응답 4개 | 75% | 100% | 100% | 100% | 75% |
| V2 완료된 개발 시나리오 4개 | 100% | 100% | 100% | 100% | 100% |
| V2 벡터·계획 개발 시나리오 4개 | 100% | 100% | 100% | 100% | 100% |
| 새 고정 holdout 시나리오 8개 | 100% | 100% | 100% | 100% | 100% |

모든 최종 Judge 점수는 4/5 이상이며 합격선을 낮추지 않았습니다. 중요 실패도 없습니다. 명시적인 추가 정보·업무 이관 후속 요청을 포함하므로, 정보가 없는 첫 응답만으로 불가능한 질문을 해결했다는 주장이 아닙니다.

중간 추가 질문도 증거로 남기고 사용자 후속 응답의 출처를 명시합니다. 실제 운영 승인은 여전히 사람의 별도 책임입니다.

<a id="retention"></a>
## 8. 새 증거 보존과 이전 실험 정리

공용 Basic 서비스, 임베딩·계획·답변 배포, 현재 교정 기록·V1/V2 비교·고정 계약·새 질문 합격 증거를 보존합니다.

이 저장소의 전환에서는 새 경로와 녹화를 모두 확인한 **뒤에만** 기존 Free Search와 이전 기본/간단 RAG의 클라우드·로컬 실행 기록을 정리합니다. Search 하나를 지우려고 리소스 그룹이나 공용 Foundry 계정을 삭제하지 않습니다. Git 이력·플랫폼 감사 로그를 지우거나 조직 정책을 해제하지 않습니다.

**전환 정리 완료:** 기존 Free 서비스, 이전 평가 그룹 8개·비교 Insight 2개·미사용 사용자 지정 평가기 버전 1개, 과거 실패 배포 이력과 지정된 로컬 이전 결과를 삭제했습니다. 공용 Basic과 현재 교정·V1/V2·새 holdout 증거는 보존했습니다. 배포 이력 삭제는 조직 정책의 복구나 해제를 뜻하지 않습니다.

로컬 `config*.json`, 원본 녹화, `results/`는 Git에 올리지 않습니다. 버전별 지침과 정리된 V1 실패 예시는 새 실습 자료로 보존합니다.

## 공식 참고

- [Agentic retrieval 벡터 인덱스](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-index)
- [LLM 검색 계획 수준](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [Search 계층별 기능](https://learn.microsoft.com/azure/search/search-sku-tier)
- [Entra 인증 임베딩](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings)
- [Foundry 사용자 지정 평가기](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)

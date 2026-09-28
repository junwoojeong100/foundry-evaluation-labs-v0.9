[English](en/complete-lab.md) | **한국어**

# 완결형 실습: 실패 → 개선 → 재평가 → 새 질문 검증

[저장소 기본 가이드](../README.ko.md)

[새 국문·영문 요약 영상](media/complete-rag/README.md)에서 현재 완료된 실습 흐름을 확인합니다.

현재 권장하는 완결형 경로입니다. **Basic 이상 Azure AI Search 서비스 하나**에서 **벡터·하이브리드 검색 + Foundry IQ LLM 검색 계획**을 실행합니다. 별도 선택 실습인 기본 추출형 RAG도 같은 서비스를 사용할 수 있습니다.

기존 `prompts/v1.txt`·`v2.txt`는 입문 예제의 이력으로 보존합니다. 이 경로는 **`advanced-rag/instructions.v1.txt`·`instructions.v2.txt`**를 명시적으로 사용합니다.

**진행 순서:** 아래 1–8절을 따릅니다. 입문 실습 0–6과 Optional RAG 전체를 먼저 완료할 필요는 없습니다. 2절에서 공통 환경 준비만 빌려 쓴 뒤 이 문서로 돌아옵니다. 명령은 `advanced_lab.py`가 있는 폴더의 활성화된 가상환경에서 한 개씩 실행합니다. 결과 폴더는 자동으로 만들어집니다.

**각 단계의 완료 확인과 `results/advanced/`의 자동 생성 결과로 진행합니다.** 별도 기록 양식은 필요 없으며 개인 메모는 선택 사항입니다. 입문용 80% Gate·D06/H04 검토 절차와 섞지 않습니다. **실습 완료와 자동 합격은 다릅니다.** 낮은 점수나 중단도 실제 결과로 보존하고, 미실행 단계는 완료했다고 표현하지 않습니다.

## 합격의 정확한 의미

[acceptance.json](../advanced-rag/acceptance.json)의 기준은 새 질문을 보기 전에 고정합니다.

- **V2의 모든 최종 사례**가 업무 검사·필수 근거 검색·Groundedness·**기본 Relevance**·업무 성공도를 **100% 통과**해야 합니다. 평균으로 실패 사례를 숨기지 않습니다.
- 필수 Judge는 **4/5 이상**, 중요 사례 실패는 **0개**.
- 업무 성공도 Judge는 정상·오답 **교정 사례 10개를 모두 올바르게 구분**해야 함.
- 실제 벡터 인덱스·vectorizer와 `modelQueryPlanning` 활동이 있어야 함.
- 후보를 고정한 뒤 새 holdout을 최소 8개 생성·등록해야 함.

**기본 Relevance도 필수 합격 지표로 유지합니다.** 최종 답변은 실제 완료된 사용자 요청을 해결해야 합니다. 추가 정보 질문은 중간 단계이지 완료 답변으로 표시하지 않습니다.

V2는 평가 데이터에 미리 정한 사용자 후속 응답을 사용합니다. 날짜 누락 사례는 질문 후 사용자의 실제 출장일을 받고, 해외 한도 부재 사례는 금액을 꾸미는 대신 사용자가 재무팀 문의 체크리스트를 요청하는 단계를 거칩니다. 사용자 정보를 모델이 만들어 내지 않습니다. 최종 대화를 Judge에 전달하되, **초기 응답의 자동 검사는 JSON 형식·결정·금액·출처 필드에 한정**됩니다.

결과의 `intermediate_safe`는 이 필드 검사의 통과 여부이지 **초기 설명 문장의 의미나 안전성을 별도로 채점했다는 뜻이 아닙니다**. 예를 들어 `unknown`·`null`·`SCOPE` 필드가 맞아도 설명에 해외 한도를 지어낸 오류가 남을 수 있습니다. 5·7절의 `inspect --dialogue`로 초기 설명까지 직접 읽고 판단을 기록합니다.

`LAB_ACCEPTANCE_PASSED`는 위 교육용 기준을 통과했다는 뜻입니다. **실제 사람의 운영 승인과는 별개**입니다.

<a id="architecture"></a>
## 1. 검색 서비스 하나로 구성

| 구성 | 역할 |
|---|---|
| `swedencentral`의 Basic Search 서비스 | 이 경로의 모든 인덱스·지식 기반을 수용 |
| `travel-rag-index` / `travel-policy-kb` | Optional RAG를 선택할 때만 별도로 만드는 기본 추출형 RAG 객체 |
| `travel-vector-index` | 실제 1536차원 HNSW 벡터와 검색 가능한 규정 텍스트 |
| `travel-vector-ks` / `travel-planned-kb` | LLM 검색 계획 모델을 연결한 Foundry IQ |
| `rag-embedding` | 문서·질의 벡터를 만드는 `text-embedding-3-small` |
| `rag-planner` | 지원되는 검색 계획 모델 `gpt-5.4-mini` |
| `eval-model` | 답변·평가에 사용하는 `gpt-6-luna` |

LLM 검색 계획에는 **`2026-08-01-preview`**를 사용합니다. 정식 minimal API와 달리 미리 보기 기능이며, 이를 GA 운영 환경으로 표현하지 않습니다. `low`는 실제 LLM 계획을 수행하고 벡터 필드/vectorizer는 하이브리드 검색에 사용됩니다.

Free 서비스에는 여기서 필요한 아웃바운드 관리 ID 제약이 있습니다. 허가받은 Basic 이상 서비스가 있다면 재사용합니다. **Basic은 유지 중에도 비용이 발생**하며 임베딩·계획·생성·채점 사용량 비용도 발생할 수 있습니다.

<a id="setup"></a>
## 2. Azure 준비와 권한

**추가 유료 자원을 만들기 전에 확인:** 저장된 V1과 비교하려면 답변 배포가 **`eval-model` / `gpt-6-luna` / 버전 `2026-09-22`**여야 합니다. 지역은 `swedencentral`입니다. 과거에 실행됐다는 사실은 현재 구독의 버전 가용성·쿼터를 보장하지 않습니다. 이 조건을 충족할 수 없다면 Search·추가 모델을 만들기 전에 [고정 규정 입문 LIVE](../README.ko.md#lab-0) 또는 [DEMO](offline.md)를 선택합니다. 다른 버전의 결과를 기록된 V1과 비교하지 않습니다.

먼저 [README의 준비 1–7](../README.ko.md#prepare)만 완료합니다. [준비 5](../README.ko.md#setup-model)에서 위 답변 모델 버전을 확인하고, `config.json`과 한 건의 생성·평가까지 준비합니다. 기존 허가된 환경은 [기존 환경 준비](setup.md#existing-environment)를 사용합니다. 입문 A/B·실습 1–6은 이 경로의 필수 선행 활동이 아닙니다. **준비가 끝나면 아래 Search 준비로 돌아옵니다.**

<a id="search-setup"></a>
### Search 서비스 준비

**허가된 Basic 이상 서비스를 재사용하거나 이미 생성했다면 아래 두 생성 준비 명령을 건너뜁니다.** 신규 서비스가 필요할 때만 고유한 이름으로 실행합니다. `az search service create`는 기존 서비스도 갱신하므로, 재사용할 서비스에 실행하면 복제본·인증 설정 등을 바꿀 수 있습니다. 이 경로를 위해 별도 Free Search를 만들지 않습니다.

```bash
az search service check-name-availability --name "YOUR-SHARED-SEARCH" --type searchServices --subscription "YOUR-SUBSCRIPTION-ID"
```

`nameAvailable: true`일 때만 생성합니다.

```bash
az search service create --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku basic --replica-count 1 --partition-count 1 --identity-type SystemAssigned --semantic-search free --disable-local-auth true
```

신규·기존 서비스 모두 실제 ID·지역·SKU·인증·시스템 할당 관리 ID를 확인합니다. 기존 설정을 바꿔야 한다면 소유자의 승인이 먼저 필요합니다.

```bash
az search service show --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,identity:identity,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth}" -o json
```

`Succeeded/succeeded`, `swedencentral`, Basic 이상 SKU, `disableLocalAuth: true`, `identity.principalId`를 확인합니다. 사용자에게 필요한 **Search Service Contributor**, **Search Index Data Contributor**는 [사용자 ID 조회와 Search 역할 설정](optional-rag.md#search-access)만 수행한 뒤 이곳으로 돌아옵니다. 그 절의 `YOUR-SEARCH-NAME`은 위 서비스 이름이며, Optional RAG 3절부터는 실행하지 않습니다.

<a id="search-model-access"></a>
이제 조회 결과의 **`identity.principalId`인 Search 관리 ID**에 상위 Foundry 리소스 범위의 **Cognitive Services OpenAI User**가 있는지 확인하고, 없는 경우에만 할당합니다. 프로젝트나 사용자 ID로 대신하지 않습니다.

```bash
az role assignment create --assignee-object-id "YOUR-SEARCH-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

### 추가 모델과 설정 파일

현재 모델·버전·쿼터를 확인한 뒤 두 모델을 **순서대로** 배포합니다. 같은 Foundry 계정에 동시 쓰기를 하면 충돌할 수 있습니다. 이미 허가된 배포가 있다면 실제 모델·버전을 확인하고 해당 생성 명령은 건너뜁니다. 공유 배포를 임의 갱신하지 않습니다.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-embedding --model-name text-embedding-3-small --model-version "YOUR-EMBEDDING-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 40 --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-planner --model-name gpt-5.4-mini --model-version "YOUR-PLANNER-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

기록된 실행의 추가 모델 버전은 임베딩 `1`, 계획 모델 `2026-03-17`입니다. 실제 사용한 버전을 기록합니다. 답변 모델은 앞서 확인한 V1의 고정 버전을 유지합니다.

[설정 예제](../advanced-rag/config.example.json)를 **`advanced_lab.py`와 같은 폴더에 `config.advanced.json`으로 저장**합니다. `advanced-rag/` 안에 저장하지 않으며 기존 `config.json`도 유지합니다.

| 설정 | 실제 값을 확인할 곳 |
|---|---|
| `search_endpoint` | Azure 포털 → 사용할 Search 서비스 → Overview의 URL |
| `model_resource_endpoint` | 같은 상위 Foundry 리소스의 Keys and Endpoint에서 **Azure OpenAI 리소스 주소** 확인. `.openai.azure.com`으로 끝나며 프로젝트 주소와 다름. API 키는 복사하지 않음 |
| `index_name`, `knowledge_source`, `knowledge_base` | 참가자·실험별로 허가된 고유 이름. 예: `travel-vector-a7k3m9`, `travel-vector-ks-a7k3m9`, `travel-planned-kb-a7k3m9` |

**서비스 공유는 검색 객체·실험의 무조건적인 공유가 아닙니다.** 처음 실행하기 전에 세 객체 이름을 정하고, 같은 실험을 재개할 때는 유지합니다. 기존 객체는 소유자의 허가와 동일 코퍼스·벡터 설정·모델 주소·배포·계획 설정을 확인한 경우에만 재사용합니다. `setup`은 불일치하는 기존 객체를 갱신하지 않고 중단하므로, 다른 실험은 새 객체 이름으로 구분합니다.

임베딩은 계정의 `/openai/v1/embeddings` 주소에서 Entra 인증으로 호출합니다. 이 환경의 프로젝트 게이트웨이는 채팅·평가는 지원했지만 임베딩 호출에는 404를 반환했습니다. API 키는 사용하지 않습니다.

```bash
python advanced_lab.py setup
```

**완료 확인:** `VECTOR SETUP OK: 7 documents, 1536 dimensions`. `results/advanced/setup.json`에서 실제 텍스트·벡터·HNSW·vectorizer·Knowledge Source·계획형 Knowledge Base를 확인합니다.

이 Basic URL을 기존 [기본 추출형 RAG](optional-rag.md)의 `config.rag.json`에도 사용할 수 있습니다. 두 경로의 인덱스·Knowledge Base 이름은 구분합니다.

<a id="resume"></a>
### 명령 상태·중단·재개

<details>
<summary>대기·오류가 나거나 나중에 재개할 때만 펼치기</summary>

이 경로의 출력은 **`results/advanced/`로 고정**되어 있습니다. 입문용 `run.json`·`run --out` 재개법 대신 아래 표를 사용합니다. 새 터미널에서는 가상환경과 로그인 상태를 복원하고, 같은 실험을 두 터미널에서 동시에 실행하지 않습니다.

| 결과 | 다음 행동 |
|---|---|
| `GENERATION COMPLETE` 또는 `Evaluation complete` | 해당 단계 건수와 저장 결과를 확인한 뒤 다음 명령으로 이동. 답변 합격과는 별개 |
| `아직 처리 중입니다` / 종료 코드 `3` | **방금 실행한 명령 전체**를 재실행. 교정 중이면 같은 `calibrate`, 채점 중이면 같은 `judge --stage …`. 저장된 원격 작업을 조회함 |
| 생성 도중 일시적인 연결 오류·사용자 중단 | 원인을 해결한 뒤 같은 `run --stage …` 재개. 저장된 응답은 다시 생성하지 않음. 응답 직후 저장 전에 끊긴 호출은 재청구될 수 있음 |
| `initial clarification/handoff field checks failed` / 종료 코드 `1` | 초기 품질 실패. `<stage>/generation.json`의 `pending → 사례 ID → initial_response → response`를 읽고 실패로 보존. 같은 명령으로 좋은 답을 다시 뽑을 수 없음 |
| 교정 종료 코드 `2` / `mismatches` 있음 | `calibration-result.json`의 오분류 이유를 기록하고 중단. 합격선을 낮추거나 반복 채점해 진행하지 않음 |
| `freeze`의 `Dev acceptance is not met` / 종료 코드 `1` | dev의 `report.md`에서 실패를 기록하고 보존. 아직 holdout을 만들지 않음 |
| `LAB_ACCEPTANCE_BLOCKED` / 종료 코드 `2` | 완료된 holdout이 기준 미달. `acceptance-report.md`·`acceptance-result.json`의 이유를 기록하고 8절로 이동 |
| 그 밖의 `ERROR:` 또는 `usage:` / `error:` | 환경·입력·명령 오류를 먼저 해결. 특히 `usage:`와 함께 나온 코드 `2`는 품질 차단이 아니라 인자 오류 |

**초기 품질 실패로 중단된 `generation.json`은 `collecting` 상태입니다.** 이때는 `judge`·`inspect`로 완료된 실행처럼 읽거나 `accept`로 최종 판정을 만들 수 없습니다. JSON의 저장된 초기 응답과 오류를 직접 기록하고, 뒤 단계는 미실행으로 표시한 뒤 8절에서 보존합니다.

교정·채점의 기본 **상태 조회 대기 예산은 300초**입니다. 인증·제출·HTTP 응답·결과 수집을 포함한 전체 명령 시간은 더 길 수 있습니다.

| 산출물 (`results/advanced/` 기준) | 용도 |
|---|---|
| `setup.json`, `vector-query.json`, `planned-query.json` | 실제 검색 구성과 검색 증거 |
| `calibration-result.json`, `judge-contract.json` | 교정 결과와 합격한 Judge 계약 |
| `<stage>/generation.json` | `status`, 완료 응답 `rows`, 미완료 사례의 `pending` |
| `<stage>/evaluation-request.json` | 평가 입력과 **로컬 상관관계 ID `run_id`**. 교정은 `calibration/` 안에 있음 |
| `<stage>/foundry-job.json` | 원격 `eval_id`·`run_id`·진행 상태. 교정도 동일 |
| `<stage>/judge.json`, `<stage>/report.md` | 완료된 점수·이유 |
| `frozen.json`, `holdout-registration.json` | 후보 고정과 새 질문 등록 계약 |
| `acceptance-result.json`, `acceptance-report.md` | 완료된 holdout의 최종 자동 판단 |

`<stage>`는 `v1-recorded`, `v2-replay`, `planned-dev`, `holdout` 중 명령의 값입니다. 파일 유무만으로 완료를 판단하지 않습니다. 원격 생성 여부가 불명확하면 [ID 복구](reference.md#resume)를 따르며 자동 재제출하지 않습니다.

**새 실험:** 기존 결과를 지우지 말고, 저장소 코드를 **별도 작업 폴더**에 받아 그 폴더의 비어 있는 `results/advanced/`에서 시작합니다. 본인에게 허가된 설정을 준비하고 같은 Search 서비스를 쓰되 검색 객체 이름은 새 실험용으로 구분합니다. 이 CLI의 `run`에는 `--out`이 없습니다. 기존 후보·holdout의 실패를 보존한 채 두 dev 검증과 동결 후 새 holdout을 다시 수행합니다.

</details>

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

[업무 성공도 기준](../advanced-rag/policy-task-success.txt)을 읽습니다. 필요한 날짜를 묻거나 규정에 없는 금액을 만들지 않는 답은 **적절한 초기 행동**으로 인정하고, 잘못된 금액·승인 조작·설명 모순은 구분합니다. 초기 행동이 맞다는 것만으로 최종 대화까지 완료된 것은 아닙니다.

아래 교정이 대기 중이거나 오류로 끝나면 [상태·재개 표](#resume)에서 **교정에 해당하는 행**을 사용합니다.

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

초기 설명의 모순까지 직접 확인하고, 문제가 있다면 해당 문장을 근거로 판단합니다.

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D04 --dialogue
```

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D08 --dialogue
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

**5→6절 사이에 V2 지침·후속 응답·모델·설정을 바꾸지 않습니다.** 두 dev 검증은 같은 후보와 입력 계약을 사용해야 합니다. 변경이 필요하면 기존 결과를 보존하고 [새 실험](#resume)에서 두 검증을 모두 수행합니다.

```bash
python advanced_lab.py freeze
```

**완료 확인:** `FROZEN`과 계약 해시. 실제 V1 실패가 있어야 하며 V2 동일 문맥 및 계획형 dev가 기준을 통과해야 합니다. 지침·Judge·모델 버전·검색 설정·소스 정의·코퍼스를 새 질문 생성 전에 고정합니다.

<a id="holdout"></a>
## 7. 고정한 뒤 새 질문 생성

```bash
python advanced_lab.py create-holdout
```

새 난수 시드로 **미리 정의된 8개 시나리오의 날짜·도시·금액을 새로 채웁니다**. 현재/과거 한도, 한도 초과 승인, 해외 범위, 날짜 누락, 금지 좌석, 경계값을 포함합니다. 새로운 매개변수 사례이지 광범위한 블라인드 일반화 검증은 아닙니다. 날짜 누락과 해외 이관 사례에는 명시적인 평가용 사용자 후속 응답이 있습니다. 질문·후속 응답·정답·생성 근거는 `results/advanced/holdout-data/`에 저장합니다.

이미 있으면 덮어쓰지 않습니다. 합격하려고 질문을 다시 뽑지 않습니다.

```bash
python advanced_lab.py run --stage holdout
```

```bash
python advanced_lab.py judge --stage holdout
```

완료된 두 후속 대화에서 초기 설명과 최종 답을 함께 읽고 판단을 기록합니다.

```bash
python advanced_lab.py inspect --stage holdout --case-id N05 --dialogue
```

```bash
python advanced_lab.py inspect --stage holdout --case-id N06 --dialogue
```

```bash
python advanced_lab.py accept
```

**완료 확인:** `results/advanced/acceptance-report.md`·`acceptance-result.json`에 본인 실행의 판정과 이유가 저장됩니다. `LAB_ACCEPTANCE_PASSED`는 새 시나리오 8개의 **Relevance를 포함한 모든 최종 응답 지표와 초기 필드 검사**가 통과했을 때만 나옵니다. `LAB_ACCEPTANCE_BLOCKED`도 보존해야 할 유효한 평가 결과입니다.

차단되면 실패와 보류 이유를 기록하고 8절로 이동합니다. 자동 합격이어도 직접 읽은 초기 설명에 모순이 있다면 그 판단을 따로 기록하고 운영 적용은 보류합니다. 고정된 지침·Judge를 바꾸거나 합격 사례만 고르지 않습니다. 다음 개선은 [별도 작업 복사본의 새 실험](#resume)과 새로운 holdout으로 진행합니다.

<a id="results"></a>
## 결과 해석

**아래는 작성자가 기록한 한 번의 완결형 실행 결과이며 재현 보장이 아닙니다.** 본인의 판정은 위 acceptance 파일로 확인합니다. 이 표와 영상은 별도 입문 LIVE 또는 최소 RAG `search`/`iq` 비교를 현재 환경에서 재검증했다는 증거가 아닙니다.

앞서 Relevance를 제외했던 시도는 **최종 성공 결과가 아닙니다**. 아래 기록의 새 반복에서는 모든 최종 V2 사례가 모든 필수 지표를 통과했습니다.

| 단계 | 업무 | 검색 | Groundedness | Relevance | 업무 성공도 |
|---|---|---|---|---|---|
| 기록된 V1 단일 응답 4개 | 75% | 100% | 100% | 100% | 75% |
| V2 완료된 개발 시나리오 4개 | 100% | 100% | 100% | 100% | 100% |
| V2 벡터·계획 개발 시나리오 4개 | 100% | 100% | 100% | 100% | 100% |
| 새 고정 holdout 시나리오 8개 | 100% | 100% | 100% | 100% | 100% |

모든 최종 Judge 점수는 4/5 이상이며 합격선을 낮추지 않았습니다. 중요 실패도 없습니다. 명시적인 추가 정보·업무 이관 후속 요청을 포함하므로, 정보가 없는 첫 응답만으로 불가능한 질문을 해결했다는 주장이 아닙니다.

중간 추가 질문도 증거로 남기고 사용자 후속 응답의 출처를 명시합니다. 초기 설명 문장의 별도 자동 의미 평가까지 통과한 결과는 아닙니다. 실제 운영 승인은 여전히 사람의 별도 책임입니다.

<a id="retention"></a>
## 8. 결과와 리소스 보존

공용 Basic 서비스, 임베딩·계획·답변 배포와 본인이 실제 수행한 교정·V1/V2·고정·새 질문 결과를 **실패까지 포함해 보존**합니다. 생성된 보고서로 마지막 완료 단계·합격/보류 근거·미실행 항목을 확인하고, 리소스 소유자와 다음 비용 확인 시점을 정합니다. Basic 유지 비용은 계속 발생합니다.

**완료 확인:** 본인의 결과 파일과 실제 대화를 근거로 V1의 실패, V2의 변화, 새 질문의 결과와 한계를 설명할 수 있습니다. 초기 단계에서 중단했다면 뒤 단계는 미실행임을 밝히고, 보존할 자원과 비용 상태를 확인합니다.

**아래는 작성자의 과거 전환 기록이지 참가자의 삭제 단계가 아닙니다.** 별도 삭제 결정 없이 자원을 지우지 않습니다. Search 하나를 지우려고 리소스 그룹이나 공용 Foundry 계정을 삭제하지 않으며, Git 이력·플랫폼 감사 로그를 지우거나 조직 정책을 해제하지 않습니다.

**전환 정리 완료:** 기존 Free 서비스, 이전 평가 그룹 8개·비교 Insight 2개·미사용 사용자 지정 평가기 버전 1개, 과거 실패 배포 이력과 지정된 로컬 이전 결과를 삭제했습니다. 공용 Basic과 현재 교정·V1/V2·새 holdout 증거는 보존했습니다. 배포 이력 삭제는 조직 정책의 복구나 해제를 뜻하지 않습니다.

로컬 `config*.json`, 원본 녹화, `results/`는 Git에 올리지 않습니다. 버전별 지침과 정리된 V1 실패 예시는 새 실습 자료로 보존합니다.

## 공식 참고

- [Agentic retrieval 벡터 인덱스](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-index)
- [LLM 검색 계획 수준](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [Search 계층별 기능](https://learn.microsoft.com/azure/search/search-sku-tier)
- [Entra 인증 임베딩](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings)
- [Foundry 사용자 지정 평가기](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)

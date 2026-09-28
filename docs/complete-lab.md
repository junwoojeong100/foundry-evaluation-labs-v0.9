[English](en/complete-lab.md) | **한국어**

# 완결형 실습: 실패 → 개선 → 재평가 → 새 질문 검증

[저장소 기본 가이드](../README.ko.md)

**규정을 찾고, 답변을 개선하고, 처음 보는 질문으로 확인합니다.** 가상의 가온랩 출장비 도우미로 **RAG(검색 증강 생성)**, 즉 검색한 근거로 답하는 방식을 실습합니다.

| 한눈에 보기 | 이 경로에서 할 일 |
|---|---|
| 실행 방식 | **LIVE 전용·유료**. Python 코드는 작성하지 않고 제공된 명령 실행 |
| 전체 환경 | `swedencentral`의 **Basic 이상 Search 1개 + 모델 배포 3개** |
| 직접 편집 | 준비 단계의 `config.json`·`config.advanced.json` |
| 지침 비교 | `advanced-rag/instructions.v1.txt`·`instructions.v2.txt`를 **읽고 비교** |
| 결과 위치 | `results/advanced/`. 끝까지 실행하면 `acceptance-report.md`로 최종 판단 |

**이 문서의 1–8절만 순서대로 따릅니다.** 입문 실습 0–6과 Optional RAG 전체는 선행 필수가 아닙니다. 2절에서 공통 준비만 수행한 뒤 돌아옵니다. 입문용 `prompts/v1.txt`·`v2.txt`를 수정하거나 이 경로에 대신 넣지 않습니다.

<a id="lab-map"></a>
## 진행표

| 순서 | 내가 할 일 | 다음 단계로 갈 때 확인할 것 |
|---|---|---|
| [1. 규정과 구성](#architecture) | 어떤 답이 맞는지 먼저 판단 | 규정에 근거한 이유 |
| [2. 환경 준비](#setup) | 공통 준비 → 이 문서 복귀 → Search·추가 모델·설정 | `VECTOR SETUP OK` |
| [3. 실제 검색](#retrieval-proof) | 벡터 검색과 LLM 검색 계획을 각각 확인 | 두 `RETRIEVAL OK`와 검색 증거 |
| [4. 채점자 확인](#calibration) | 정답·오답 예제로 Judge를 점검 | `CALIBRATION PASSED: 10 controls` |
| [5. V1 → V2](#improve) | 이전 답변의 실패와 V2의 변화를 비교 | 두 실행 각각 4개 답변·3개 지표 |
| [6. 통합 확인·고정](#freeze) | 실제 검색을 포함한 V2 확인 후 변경 잠금 | `FROZEN` |
| [7. 새 질문](#holdout) | 고정한 뒤 새 사례 8개를 만들고 평가 | 본인의 `acceptance-report.md` |
| [8. 마무리](#retention) | 결과 해석·보관·비용 확인 | 완료 체크리스트 또는 중단 기록 |

**명령 읽는 법:** `advanced_lab.py`가 있는 폴더의 활성화된 가상환경에서 **한 명령 → 완료 확인 → 다음 명령** 순서로 실행합니다. 결과 폴더는 자동 생성됩니다. `text` 블록은 예상 출력이므로 입력하지 않습니다. 막히면 [상태·재개 표](#resume)를 사용합니다.

> [!IMPORTANT]
> **실습 완료와 자동 합격은 다릅니다.** 낮은 점수와 중단도 그대로 보존합니다. 미실행 단계를 완료로 표시하거나 입문용 80% Gate·D06/H04 검토 절차와 섞지 않습니다.

각 단계의 완료 확인과 자동 생성 결과로 진행합니다. 별도 기록 양식은 필요 없으며 개인 메모는 선택 사항입니다.

<details>
<summary>처음 만나는 용어: 청크·벡터·Knowledge Base·Judge·holdout</summary>

| 용어 | 이 실습에서의 뜻 |
|---|---|
| 청크·인덱스 | 청크는 검색할 규정 조각, 인덱스는 그 조각을 찾도록 저장한 검색 대상 |
| 벡터·하이브리드 검색 | 문장을 숫자 배열로 바꿔 의미가 비슷한 자료를 찾는 검색 / 여기에 텍스트 검색도 함께 사용 |
| Knowledge Source / Knowledge Base | 어느 인덱스를 읽을지 정하는 연결 / 그 연결을 사용해 검색 요청을 처리하는 지식 기반 |
| LLM 검색 계획 | AI가 복합 질문을 검색어로 나눠 근거를 찾는 과정. 직원에게 답하는 모델과 역할이 다름 |
| Judge·교정 | Judge는 AI 채점자. 교정은 사람이 정한 정답·오답 예제를 올바르게 구분하는지 점검하는 일 |
| V1·V2 | 개선 전·후의 지침 버전. V2에서는 필요한 사용자 후속 대화까지 완료 |
| dev·holdout·고정(freeze) | dev는 개선 확인용 질문, holdout은 마지막 확인용 새 질문. 고정은 새 질문 전에 지침·모델·검색·채점 조건을 바꾸지 못하게 기록하는 일 |

</details>

<details>
<summary>유료 호출의 범위와 참고 영상</summary>

`advanced_lab.py`에는 DEMO 모드가 없습니다. `baseline`의 기록 가져오기와 `freeze`·holdout 생성/등록·`inspect`·`accept`는 로컬 작업이지만, 준비·검색·생성·교정·채점은 실제 Azure를 사용합니다.

영상은 필수가 아닙니다. [국문·영문 요약 영상](media/complete-rag/README.md)과 [기록된 결과](#results)는 **2026-09-28의 별도 실행**이며 본인의 완료 신호나 예상 점수를 대신하지 않습니다.

</details>

---

<a id="architecture"></a>
## 1. 규정을 먼저 읽고 구성 이해하기

**설치 없이 할 일:** [출장 규정](../data/policies.md)을 읽고 다음 질문에 먼저 답해 봅니다.

> 2026년 9월 국내 출장 숙박비가 1박 220000원이고 사전 승인이 없습니다. 바로 정산할 수 있을까요?

<details>
<summary>판단한 뒤 해설 보기</summary>

현재 공식 한도는 200000원입니다. 220000원은 이를 초과하므로 재무팀 사전 승인이 필요합니다. 미승인 초안의 240000원을 적용하면 안 됩니다. 과거 출장에는 정산일이 아니라 **실제 출장일**에 맞는 과거 한도를 적용하며, 출장일이 없거나 규정에 없는 해외 한도는 추측하지 않습니다.

</details>

**완료 확인:** 정산 가능 여부와 규정상 이유를 한 문장으로 설명할 수 있습니다. 이어서 아래 구성은 역할만 이해하면 됩니다. HNSW는 벡터 검색 방식의 이름이며 직접 구현하거나 설정을 바꿀 필요가 없습니다.

| 구성 | 역할 |
|---|---|
| `swedencentral`의 Basic Search 서비스 | 이 경로의 모든 인덱스·지식 기반을 수용 |
| `travel-vector-index` | 실제 1536차원 HNSW 벡터와 검색 가능한 규정 텍스트 |
| `travel-vector-ks` / `travel-planned-kb` | LLM 검색 계획 모델을 연결한 Foundry IQ |
| `rag-embedding` | 문서·질의 벡터를 만드는 `text-embedding-3-small` |
| `rag-planner` | 지원되는 검색 계획 모델 `gpt-5.4-mini` |
| `eval-model` | 답변·평가에 사용하는 `gpt-6-luna` |

LLM 검색 계획에는 코드에 고정된 **`2026-08-01-preview`**를 사용합니다. 정식 minimal API와 달리 미리 보기 기능이며, 이를 GA 운영 환경으로 표현하지 않습니다. `low`는 실제 LLM 계획을 수행하고 벡터 필드/vectorizer는 하이브리드 검색에 사용됩니다. 공식 문서의 다른 API 버전 예제를 이 요청에 그대로 섞지 않습니다.

Free 서비스에는 여기서 필요한 아웃바운드 관리 ID 제약이 있습니다. 허가받은 Basic 이상 서비스가 있다면 재사용합니다. **Basic은 유지 중에도 비용이 발생**하며 임베딩·계획·생성·채점 사용량 비용도 발생할 수 있습니다.

**다음:** [2. 환경 준비](#setup) · [진행표](#lab-map)

---

<a id="setup"></a>
## 2. Azure 준비와 권한

> [!WARNING]
> **Search·추가 모델을 만들기 전에 답변 모델 버전을 확인합니다.** 기록된 V1 비교에는 **`eval-model` / `gpt-6-luna` / 버전 `2026-09-22`**, 지역 **`swedencentral`**이 필요합니다. 충족할 수 없다면 [입문 LIVE](../README.ko.md#lab-0) 또는 [DEMO](offline.md)를 선택합니다. 다른 버전의 결과와 비교하지 않습니다.

**생성 전 확인할 네 가지**

| 확인할 것 | 진행 조건 |
|---|---|
| 답변 배포 | 모델 이름뿐 아니라 배포 이름·버전도 [V1의 `model_snapshot`](../advanced-rag/fixtures/recorded-v1.json)과 일치. 기록 파일·공유 배포를 수정해 맞추지 않음 |
| 추가 모델 | 같은 Foundry 리소스에서 임베딩·계획 모델의 지원 버전과 **GlobalStandard 용량 40·60** 확인. [가용성 도움말](reference.md#model-availability) |
| 권한 | Search/모델 생성·사용과 **Search·Foundry 리소스 범위 역할 할당** 승인. 권한이 없으면 권한 있는 담당자가 준비 |
| 비용·정책 | Basic 유지비·사용량 비용, preview·네트워크 허용 여부 확인. 용량 40·60은 비용 상한이 아님 |

과거 실행 기록은 현재 구독의 버전 가용성·쿼터를 보장하지 않습니다.

**준비는 아래 여섯 단계입니다.** 공통 준비에서 한 번 돌아온 뒤에는 **Optional RAG 문서로 이동하지 않고 이 문서에서 계속**합니다. 기존 자원이 있으면 해당 생성 명령만 건너뛰고 조회·권한 확인은 수행합니다.

| 준비 순서 | 할 일 |
|---|---|
| [2-1. 공통 환경](#common-setup) | Python·로그인·Foundry·답변 모델·한 건 평가 |
| [2-2. 실제 값](#search-setup) | 이름·ID 구분, 답변 버전과 추가 모델 가용성 확인 |
| [2-3. Search](#search-service) | 서비스 하나 준비, 실제 리소스 ID·관리 ID 조회 |
| [2-4. 접근 권한](#search-access) | 본인 → Search, Search 관리 ID → 모델 권한 확인 |
| [2-5. 추가 모델](#extra-models) | 임베딩·검색 계획 모델 배포 |
| [2-6. 설정·연결](#configure) | `config.advanced.json` 저장, 검색 객체 생성 |

전체 구성은 **모델 배포 3개와 Search 서비스 1개**입니다. 공통 준비의 모델 하나는 이 중 답변·Judge용입니다. 새 자원 수는 기존 자원 재사용 여부에 따라 달라집니다.

<details>
<summary>비용 계획에 필요한 호출 규모 보기</summary>

공통 준비부터 정상적으로 한 번 완료하는 경우입니다. **새 응답 수에는 중간 대화도 포함**하고, 평가 항목은 답변별 지표 수입니다.

| 단계 | 새로 생성하는 응답 | 평가 항목 |
|---|---|---|
| `setup-smoke` | 1 | 2 |
| `calibration` | 0 — 작성된 교정 답변 10개 사용 | 10 |
| `v1-recorded` | 0 — 이전 답변 4개 가져오기 | 12 |
| `v2-replay` | 6 — 최종 4개 + 초기 2개 | 12 |
| `planned-dev` | 6 — 최종 4개 + 초기 2개 | 12 |
| `holdout` | 10 — 최종 8개 + 초기 2개 | 24 |
| 합계 | **23** | **72** |

이는 청구 API 횟수나 비용 상한이 아닙니다. Search 유지비, 임베딩·검색 계획, 평가기 내부 호출·재시도 비용은 별도로 고려합니다. 중단·저장 결과 재사용 여부에 따라 실제 호출량도 달라집니다.

</details>

<a id="common-setup"></a>
### 2-1. 공통 환경 준비

1. **이 문서는 열어 둔 채**, [README 준비 1–7](../README.ko.md#prepare)을 새 탭에서 진행합니다. 기존 허가된 자원은 [기존 환경 준비](setup.md#existing-environment)를 사용합니다.
2. [준비 5](../README.ko.md#setup-model)에서 답변 모델 버전을 확인합니다.
3. `config.json`과 한 건의 생성·평가까지 준비합니다. 입문 A/B·실습 1–6은 필수 선행 활동이 아닙니다.

> **돌아올 시점:** 준비 7에서 `평가 완료: 1개 답변 × 2개 지표`와 N01의 두 점수·이유를 확인했다면 **[아래 2-2](#search-setup)로 복귀**합니다. README 실습 1로 가지 않습니다. 같은 환경에서 이미 완료한 N01은 다시 생성하지 않습니다.

<a id="search-setup"></a>
### 2-2. 실제 값과 모델 가용성 확인

이제 `config.json`과 N01 한 건의 생성·평가가 있어야 합니다. 아래 `YOUR-...`는 **본인 값으로 바꿀 자리**입니다. 따옴표는 유지하며 이름·ID·주소를 서로 바꾸어 넣지 않습니다.

| 명령의 자리 | 넣을 값 |
|---|---|
| `YOUR-SUBSCRIPTION-ID` | 공통 준비에서 로그인한 구독의 ID |
| `YOUR-LAB-RESOURCE-GROUP` | 명령 대상 자원이 속한 실제 그룹 이름. 기존 Search가 다른 그룹에 있으면 **Search 명령에만 그 그룹** 사용 |
| `YOUR-FOUNDRY-ACCOUNT` | 상위 Foundry 리소스 이름. 프로젝트 이름 `eval-workshop`이 아님 |
| `YOUR-SHARED-SEARCH` | 재사용을 허가받은 Search 이름, 또는 신규 고유 이름(예: `feval-search-a7k3m9`) |
| `YOUR-FOUNDRY-RESOURCE-ID` | 상위 Foundry 리소스 **Overview → JSON View**의 전체 `id`. `/accounts/실제이름`으로 끝남 |
| `YOUR-SEARCH-RESOURCE-ID` | 2-3의 Search 조회 결과 중 전체 `id`. 역할을 적용할 범위 |
| `YOUR-SEARCH-PRINCIPAL-ID` | 아래 Search 조회에서 확인할 `identity.principalId`. 사용자·프로젝트 ID가 아님 |
| `YOUR-USER-OBJECT-ID` | 2-4의 사용자 조회 결과 중 `objectId`. 본인 계정의 ID |

먼저 **이미 배포한 답변 모델**을 읽기 전용으로 확인합니다.

```bash
az cognitiveservices account deployment show --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name eval-model --subscription "YOUR-SUBSCRIPTION-ID" --query "{name:name,state:properties.provisioningState,model:properties.model.name,version:properties.model.version}" --output json
```

**완료 확인:** `name: eval-model`, `state: Succeeded`, `model: gpt-6-luna`, `version: 2026-09-22`. 다르면 추가 자원을 만들지 않고 위 경로 선택으로 돌아갑니다.

**임베딩·계획 배포도 모두 재사용한다면** 소유자와 Foundry **Build → Models**에서 두 배포의 모델·버전을 확인하고 아래 두 조회는 건너뜁니다. 새 배포를 만들지 않는 참가자에게 신규 할당량이나 구독 쿼터 조회 권한을 요구하지 않습니다.

**추가 모델을 새로 배포할 때만** 다음 두 조회로 버전과 쿼터를 확인합니다. 자원을 만들거나 모델을 호출하는 명령이 아닙니다.

```bash
az cognitiveservices model list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?model.name=='text-embedding-3-small' || model.name=='gpt-5.4-mini']" --output json
```

```bash
az cognitiveservices usage list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?name.value=='OpenAI.GlobalStandard.text-embedding-3-small' || name.value=='OpenAI.GlobalStandard.gpt-5.4-mini'].{name:name.value,current:currentValue,limit:limit}" --output json
```

첫 결과의 `model.name`별 **`model.version`과 `GlobalStandard` 지원**을 확인합니다. 선택한 버전을 각각 아래 배포 명령의 **`YOUR-EMBEDDING-VERSION`·`YOUR-PLANNER-VERSION`**에 사용합니다. 두 번째 결과의 남은 쿼터(`limit - current`)가 신규 임베딩 **40**, 계획 **60**의 용량 설정을 수용해야 합니다. 기존 배포를 재사용하면 그 배포의 할당량을 다시 더하지 않습니다. 쿼터·capacity 단위도 모델/SKU별로 확인하며 빈 목록·403을 쿼터 0으로 해석하지 않습니다. 막히면 [가용성·권한 도움말](reference.md#model-availability)을 따릅니다.

<a id="search-service"></a>
### 2-3. Search 서비스 준비

**허가된 Basic 이상 서비스를 재사용하거나 이미 생성했다면 아래 두 생성 준비 명령을 건너뜁니다.** 신규 서비스가 필요할 때만 고유한 이름으로 실행합니다. `az search service create`는 기존 서비스도 갱신하므로, 재사용할 서비스에 실행하면 복제본·인증 설정 등을 바꿀 수 있습니다. 이 경로를 위해 별도 Free Search를 만들지 않습니다.

**신규 생성 전에:** Azure 포털 → **Subscriptions → 사용할 구독 → Resource providers**에서 **`Microsoft.Search`**를 확인합니다. 미등록이면 권한 있는 담당자가 **Register**를 선택하고 `Registered`를 확인합니다. 공통 준비의 `Microsoft.CognitiveServices`와는 다른 공급자이며, Search를 만들지 않는 입문·DEMO에는 추가 등록이 필요 없습니다. [공급자 등록 공식 안내](https://learn.microsoft.com/azure/azure-resource-manager/management/resource-providers-and-types)를 참고하며 권한이 없으면 우회하지 않습니다.

```bash
az search service check-name-availability --name "YOUR-SHARED-SEARCH" --type searchServices --subscription "YOUR-SUBSCRIPTION-ID"
```

`nameAvailable: true`일 때만 생성합니다.

```bash
az search service create --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku basic --replica-count 1 --partition-count 1 --identity-type SystemAssigned --semantic-search free --disable-local-auth true
```

신규·기존 서비스 모두 실제 ID·지역·SKU·인증·시스템 할당 관리 ID를 확인합니다. 기존 설정을 바꿔야 한다면 소유자의 승인이 먼저 필요합니다.

```bash
az search service show --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,identity:identity,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth,semanticSearch:semanticSearch}" -o json
```

**완료 확인:** `Succeeded/succeeded`, `swedencentral`, Basic 이상 SKU, `disableLocalAuth: true`, `identity.principalId`가 있습니다. `semanticSearch`는 `free` 또는 이미 승인된 `standard`여야 합니다. 다음 단계에서는 **전체 `id`를 `YOUR-SEARCH-RESOURCE-ID`**, **`identity.principalId`를 `YOUR-SEARCH-PRINCIPAL-ID`**로 사용합니다. 전자는 권한을 줄 자원의 주소, 후자는 Search의 신원입니다.

<a id="search-access"></a>
### 2-4. 본인과 Search 관리 ID의 권한 설정

먼저 **본인 → Search** 접근을 준비합니다. 현재 로그인한 사용자 ID를 조회합니다.

```bash
az ad signed-in-user show --query "{account:userPrincipalName,objectId:id}" --output json
```

`account`가 사용할 테넌트의 본인인지 확인하고 **`objectId`를 `YOUR-USER-OBJECT-ID`**로 사용합니다. 프로젝트나 Search 관리 ID를 넣지 않습니다. 조회가 제한되면 환경 소유자에게 같은 테넌트의 본인 ID 대조를 요청합니다.

Search의 **Access control (IAM) → Role assignments**에서 상속된 역할까지 확인합니다. 다음 두 역할 중 **없는 역할만**, 할당 권한이 있는 사람이 **Search 서비스 범위**에 부여합니다. 이미 두 역할이 있으면 두 명령 모두 건너뜁니다.

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

첫 역할은 **Search Service Contributor**(검색 객체·서비스 설정 관리·키 조회 포함), 두 번째는 **Search Index Data Contributor**(문서 업로드·검색)입니다. **이 권한은 서비스의 다른 참가자 객체에도 적용**되므로 승인된 공동 실습 범위에서만 사용합니다. 객체 이름을 나누는 것은 보안 격리가 아니며, 구독 전체에 할당하지 않습니다.

<a id="search-model-access"></a>
이어서 **Search 관리 ID → 모델** 접근을 준비합니다. 조회 결과의 **`identity.principalId`인 Search 관리 ID**에 상위 Foundry 리소스 범위의 **Cognitive Services OpenAI User**가 있는지 IAM에서 확인하고, 없는 경우에만 할당합니다. `YOUR-FOUNDRY-RESOURCE-ID`는 `/accounts/실제리소스이름`까지이며 `/projects/...`가 붙지 않습니다. 프로젝트나 사용자 ID로 대신하지 않습니다.

```bash
az role assignment create --assignee-object-id "YOUR-SEARCH-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

**호출 주체는 세 가지입니다.**

| 작업 | 사용하는 신원 |
|---|---|
| 문서 임베딩, `vector`·`hybrid` 질의 임베딩 | 터미널의 **본인 `AzureCliCredential`** |
| 서비스의 vectorizer·검색 계획 | **Search 관리 ID** |
| 클라우드 평가 | 공통 준비의 **프로젝트 관리 ID** |

본인·프로젝트의 기존 Foundry User 권한도 유지합니다. 역할 생성 성공이 즉시 호출 성공을 뜻하지는 않습니다. 401/403이면 대상·범위·전파·네트워크를 확인하고 같은 단계로 재개합니다. 중복 역할이나 API 키로 우회하지 않습니다.

**완료 확인:** IAM에서 본인에게 Search 역할 두 개, Search 관리 ID에 Foundry 리소스의 모델 호출 역할이 있는지 **대상 ID와 범위까지** 대조했습니다. 실제 데이터 접근은 아래 `setup`과 3절의 질의로 확인합니다.

<details>
<summary>공식 문서와 역할 이름이 다르게 보일 때만 보기</summary>

**공식 안내의 범위 차이:** [vectorizer 문서](https://learn.microsoft.com/azure/search/vector-search-vectorizer-azure-open-ai)는 위 OpenAI User를, [Knowledge Base 문서](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base)는 계획 모델에 더 넓은 Cognitive Services User를 안내합니다. 이 코드의 Azure OpenAI endpoint·API 버전과 구분합니다. 계획 호출만 거부된다면 소유자와 대상 API의 권한을 확인하며 더 넓은 역할을 추측으로 추가하지 않습니다.

</details>

<a id="extra-models"></a>
### 2-5. 추가 모델 배포

앞서 확인한 실제 버전으로 `YOUR-EMBEDDING-VERSION`·`YOUR-PLANNER-VERSION`을 바꾸고 두 모델을 **순서대로** 배포합니다. 같은 Foundry 계정에 동시 쓰기를 하면 충돌할 수 있습니다. 이미 허가된 배포가 있다면 실제 모델·버전을 확인하고 해당 생성 명령은 건너뜁니다. 공유 배포를 임의 갱신하지 않습니다.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-embedding --model-name text-embedding-3-small --model-version "YOUR-EMBEDDING-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 40 --subscription "YOUR-SUBSCRIPTION-ID"
```

**다음 명령 전에:** Foundry **Build → Models**에서 방금 만든 `rag-embedding`이 `Succeeded`이고 모델이 `text-embedding-3-small`인지 확인합니다. 배포 오류는 먼저 해결합니다.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-planner --model-name gpt-5.4-mini --model-version "YOUR-PLANNER-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

**완료 확인:** Foundry의 **Build → Models**에서 `rag-embedding`·`rag-planner` 모두 성공 상태와 의도한 모델·버전인지 확인합니다. 기록된 실행의 추가 모델 버전은 임베딩 `1`, 계획 모델 `2026-03-17`입니다. 이 두 모델은 현재 지원 버전을 선택할 수 있지만 `setup` 이후 같은 실험에서는 바꾸지 않습니다. 답변 모델은 앞서 확인한 V1의 고정 버전을 유지합니다.

<a id="configure"></a>
### 2-6. 설정 파일 작성과 검색 객체 생성

**VS Code에서** `advanced-rag/config.example.json`을 열고 **File → Save As**로 **`advanced_lab.py`와 같은 폴더에 `config.advanced.json`**을 만듭니다. `advanced-rag/` 안이나 `config.advanced.json.txt`로 저장하지 않습니다. 이미 본인 설정이 있다면 덮어쓰지 말고 실제 값부터 확인합니다.

두 설정 파일은 용도가 다릅니다. **`config.json`은 프로젝트·답변·Judge 연결**, **`config.advanced.json`은 Search·임베딩·검색 계획 연결**입니다. 둘 다 필요합니다.

아래는 [원본 설정 예제](../advanced-rag/config.example.json)의 전체 내용입니다. **두 주소와 세 검색 객체 이름을 본인 값으로 바꾸고 저장**합니다. 재사용 배포의 이름이 다르면 `embedding_deployment`·`planner_deployment`도 실제 배포 이름에 맞춥니다.

```json
{
  "search_endpoint": "https://YOUR-SHARED-SEARCH.search.windows.net",
  "index_name": "travel-vector-index",
  "knowledge_source": "travel-vector-ks",
  "knowledge_base": "travel-planned-kb",
  "top_k": 4,
  "model_resource_endpoint": "https://YOUR-ACCOUNT.openai.azure.com",
  "embedding_deployment": "rag-embedding",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "planner_deployment": "rag-planner",
  "planner_model": "gpt-5.4-mini",
  "retrieval_reasoning_effort": "low"
}
```

이 예제의 `top_k: 4`, 임베딩 1536차원, 계획 수준 `low`를 유지합니다. Optional RAG의 `config.rag.json`이나 `top_k: 3`과 혼동하지 않습니다. 배포 이름은 방금 확인한 실제 배포와 일치해야 합니다.

| 설정 | 실제 값을 확인할 곳 |
|---|---|
| `config.json`의 `project_endpoint` | 공통 준비에서 저장한 **프로젝트 주소**. `.services.ai.azure.com/api/projects/프로젝트이름` 포함. 아래 두 주소로 교체하지 않음 |
| `config.advanced.json`의 `search_endpoint` | Azure 포털 → 사용할 Search 서비스 → Overview의 URL. `.search.windows.net`으로 끝남 |
| `config.advanced.json`의 `model_resource_endpoint` | 같은 상위 Foundry 리소스의 Keys and Endpoint에서 **Azure OpenAI 리소스 주소** 확인. `.openai.azure.com`으로 끝나며 프로젝트 주소와 다름. API 키는 복사하지 않음 |
| `index_name`, `knowledge_source`, `knowledge_base` | 참가자·실험별로 허가된 고유 이름. 예: `travel-vector-a7k3m9`, `travel-vector-ks-a7k3m9`, `travel-planned-kb-a7k3m9` |

**주소 세 개는 서로 다른 용도입니다.** 하나의 주소를 모든 항목에 붙여 넣거나 두 설정 파일의 내용을 합치지 않습니다. [JSON 편집 요령](../README.ko.md#setup-config)처럼 안내한 값만 바꾸고 저장합니다.

**서비스 공유는 검색 객체·실험의 무조건적인 공유가 아닙니다.** 처음 실행하기 전에 세 객체 이름을 정하고, 같은 실험을 재개할 때는 유지합니다. 기존 객체는 소유자의 허가와 동일 코퍼스·벡터 설정·모델 주소·배포·계획 설정을 확인한 경우에만 재사용합니다. `setup`은 불일치하는 기존 객체를 갱신하지 않고 중단하므로, 다른 실험은 새 객체 이름으로 구분합니다.

임베딩은 계정의 `/openai/v1/embeddings` 주소에서 Entra 인증으로 호출합니다. 설정에는 위 표의 **리소스 주소까지만** 넣습니다. `/openai/v1/embeddings`는 코드가 붙이므로 직접 덧붙이지 않습니다.

**실행 전 확인**

- 두 설정 파일을 저장했고, 예시 주소 `YOUR-...`가 남아 있지 않습니다.
- 본인·프로젝트·Search 관리 ID의 역할을 각각 확인했습니다.
- 이후 같은 실험에서는 제공된 지침·질문·정답·설정을 수정하지 않습니다.

```bash
python advanced_lab.py setup
```

`setup`은 기존 객체 계약 확인 → 임베딩 캐시 준비 → 누락 인덱스 생성·문서 업로드 → Knowledge Source → 계획형 Knowledge Base 순서로 진행합니다.

**완료 확인:** `VECTOR SETUP OK: 7 documents, 1536 dimensions`. `results/advanced/setup.json`은 모델 snapshot·업로드 대상 건수·서버의 HNSW/vectorizer·지식 객체 정의를, `embedding-cache.json`은 문서 벡터를 보존합니다. 설정 성공만으로 검색·답변 품질을 검증한 것은 아니므로 3절의 실제 질의를 이어갑니다.

<a id="resume"></a>
### 명령 상태·중단·재개

`ERROR:`가 나오면 다음 단계로 가지 않습니다. 설치·로그인·JSON 문법 오류는 [공통 문제 해결](reference.md#troubleshooting), 대기·부분 실행·품질 차단은 아래 표에서 찾습니다.

<details>
<summary>대기·오류가 나거나 나중에 재개할 때만 펼치기</summary>

이 경로의 출력은 **`results/advanced/`로 고정**되어 있습니다. 입문용 `run.json`·`run --out` 재개법 대신 아래 표를 사용합니다. 새 터미널에서는 가상환경과 로그인 상태를 복원하고, 같은 실험을 두 터미널에서 동시에 실행하지 않습니다.

| 결과 | 다음 행동 |
|---|---|
| `setup` 중 연결 오류·중단 | 원인을 해결한 뒤 같은 `setup` 재실행. 같은 코퍼스·모델의 임베딩 캐시와 일치하는 객체를 재사용하고 누락된 작업을 계속함. 계약 불일치는 덮어쓰지 않음 |
| `GENERATION COMPLETE` 또는 `Evaluation complete` | 해당 단계 건수와 저장 결과를 확인한 뒤 다음 명령으로 이동. 답변 합격과는 별개 |
| `Using complete saved generation; no new model/retrieval calls.` | 이미 완료된 같은 단계의 답변을 재사용함. `GENERATION COMPLETE`를 기다리거나 다시 생성하지 말고, 해당 단계의 채점이 남았으면 `judge`로 이동 |
| `Existing frozen experiment retained.` / `Existing holdout registration retained.` | 기존 고정/등록을 검증·유지함. 아래 재개 위치 표에서 다음 미완료 단계로 이동. 이미 만든 holdout은 다시 생성하지 않음 |
| `아직 처리 중입니다` / 종료 코드 `3` | **방금 실행한 명령 전체**를 재실행. 교정 중이면 같은 `calibrate`, 채점 중이면 같은 `judge --stage …`. 저장된 원격 작업을 조회함 |
| 생성 도중 일시적인 연결 오류·사용자 중단 | 원인을 해결한 뒤 같은 `run --stage …` 재개. 저장된 응답은 다시 생성하지 않음. 응답 직후 저장 전에 끊긴 호출은 재청구될 수 있음 |
| `initial clarification/handoff field checks failed` / 종료 코드 `1` | 초기 품질 실패. `<stage>/generation.json`의 `pending → 사례 ID → initial_response → response`를 읽고 실패로 보존. 같은 명령으로 좋은 답을 다시 뽑을 수 없음 |
| 교정 종료 코드 `2` / `mismatches` 있음 | `calibration-result.json`의 오분류 ID·점수와 `calibration/report.md`의 채점 이유를 기록하고 중단. 합격선을 낮추거나 반복 채점해 진행하지 않음 |
| `freeze`의 `Dev acceptance is not met` / 종료 코드 `1` | 출력된 실패 stage·사례 ID와 보고서 경로 확인 → 함께 출력된 `inspect` 명령을 한 개씩 실행 → [기대값·실제값 읽기](#read-case). 실패를 보존하고 아직 holdout을 만들지 않음 |
| `create-holdout` 중단 / `Holdout files already exist` | `holdout-data/`와 등록 파일 확인. 네 파일이 완전하고 같은 동결 계약에 속하나 등록만 빠졌다면 `python advanced_lab.py register-holdout`. 이미 등록됐다면 `run --stage holdout`으로 이동. 데이터 파일이 일부만 남았다면 보존하고 새 실험으로 구분하며 다시 뽑지 않음 |
| `LAB_ACCEPTANCE_BLOCKED` / 종료 코드 `2` | 완료된 holdout이 기준 미달. `acceptance-report.md`·`acceptance-result.json`의 이유를 기록하고 8절로 이동 |
| 그 밖의 `ERROR:` 또는 `usage:` / `error:` | 환경·입력·명령 오류를 먼저 해결. 특히 `usage:`와 함께 나온 코드 `2`는 품질 차단이 아니라 인자 오류 |

**초기 품질 실패로 중단된 `generation.json`은 `collecting` 상태입니다.** 이때는 `judge`·`inspect`로 완료된 실행처럼 읽거나 `accept`로 최종 판정을 만들 수 없습니다. JSON의 저장된 초기 응답과 터미널의 오류를 직접 기록하고, 뒤 단계는 미실행으로 표시한 뒤 8절에서 보존합니다. 이 CLI의 `inspect`는 생성뿐 아니라 해당 단계의 채점 완료도 필요합니다.

교정·채점의 기본 **상태 조회 대기 예산은 300초**입니다. 인증·제출·HTTP 응답·결과 수집을 포함한 전체 명령 시간은 더 길 수 있습니다.

**마지막 완료 위치가 기억나지 않는다면:** 아래에서 충족한 가장 뒤의 행을 찾습니다. 파일이 있다는 사실뿐 아니라 해당 단계의 완료 메시지·상태·건수를 확인합니다. **오류·부분 수집·교정 실패가 있다면 위 상태 표가 우선**이며, 아래 표로 실패 단계를 건너뛰지 않습니다.

| 마지막으로 완료한 것 | 이어갈 위치 |
|---|---|
| `setup.json`, 검색 질의는 아직 안 함 | [3절](#retrieval-proof)의 두 질의 중 빠진 것 |
| 두 질의 JSON, `judge-contract.json`은 아직 없음 | [4절](#calibration)의 교정 |
| 교정 통과와 `judge-contract.json` | [5절](#improve)의 V1 가져오기·채점·V2 생성·채점 중 첫 미완료 단계 |
| V2 replay 4개 생성·채점 완료 | [6절](#freeze)의 `planned-dev` 생성·채점·`freeze` 중 첫 미완료 단계 |
| `frozen.json`, holdout 등록은 아직 안 함 | [7절](#holdout)의 `create-holdout`. 데이터 파일이 이미 있다면 위 복구 행부터 확인 |
| `holdout-registration.json`, 최종 보고서는 아직 없음 | [7절](#holdout)의 holdout 생성 → 채점 → 대화 검토 → `accept` 중 첫 미완료 단계 |
| `acceptance-report.md`와 `acceptance-result.json` | [8절](#retention)의 결과 해석·보존·비용 확인 |

| 산출물 (`results/advanced/` 기준) | 용도 |
|---|---|
| `setup.json`, `vector-query.json`, `planned-query.json` | 실제 검색 구성과 검색 증거 |
| `embedding-cache.json` | 같은 코퍼스·모델의 문서 벡터 재사용 |
| `evaluator.json`, `calibration-controls.json` | 사용자 지정 평가기 정의·버전과 교정 입력/통과 라벨 |
| `calibration-result.json`, `judge-contract.json` | 교정 결과와 합격한 Judge 계약 |
| `<stage>/generation.json` | `status`, 완료 응답 `rows`, 미완료 사례의 `pending` |
| `<stage>/evaluation-request.json` | 평가 입력과 **로컬 상관관계 ID `run_id`**. 교정은 `calibration/` 안에 있음 |
| `<stage>/foundry-job.json` | 원격 `eval_id`·`run_id`·진행 상태. 교정도 동일 |
| `<stage>/judge.json`, `<stage>/report.md` | 완료된 점수·이유 |
| `frozen.json`, `holdout-registration.json` | 후보 고정과 새 질문 등록 계약 |
| `holdout-data/cases.jsonl`, `labels.json`, `followups.json`, `provenance.json` | 새 질문·검색 정답·사용자 후속 응답·생성 근거. 모두 `holdout-data/` 안에 있음 |
| `acceptance-result.json`, `acceptance-report.md` | 완료된 holdout의 최종 자동 판단 |

`<stage>`는 `v1-recorded`, `v2-replay`, `planned-dev`, `holdout` 중 명령의 값입니다. 파일 유무만으로 완료를 판단하지 않습니다. 원격 생성 여부가 불명확하면 [ID 복구](reference.md#resume)를 따르며 자동 재제출하지 않습니다.

**새 실험:** 기존 결과를 지우지 말고, 저장소 코드를 **별도 작업 폴더**에 받아 그 폴더의 비어 있는 `results/advanced/`에서 시작합니다. 본인에게 허가된 설정을 준비하고 같은 Search 서비스를 쓰되 검색 객체 이름은 새 실험용으로 구분합니다. 이 CLI의 `run`에는 `--out`이 없습니다. 기존 후보·holdout의 실패를 보존한 채 두 dev 검증과 동결 후 새 holdout을 다시 수행합니다.

</details>

**다음:** [3. 실제 검색 확인](#retrieval-proof) · [진행표](#lab-map)

---

<a id="retrieval-proof"></a>
## 3. 벡터와 LLM 계획이 실제로 실행되는지 확인

**여기서는 검색만 확인하며 직원에게 보여 줄 답변은 아직 만들지 않습니다.**

### 3-1. 벡터 검색 확인하기

의미가 비슷한 규정 조각을 벡터로 찾습니다.

```bash
python advanced_lab.py query --mode vector --query "해외 출장 호텔 숙박비 상한을 확인하고 싶습니다." --out results/advanced/vector-query.json
```

**완료 확인:** `RETRIEVAL OK: vector`, `query_vector_dimensions: 1536`, `vector_fields: content_vector`, `text_query: false`와 실제 청크 ID가 보입니다. `results/advanced/vector-query.json`에 저장됩니다.

### 3-2. LLM 검색 계획 확인하기

여러 조건이 있는 질문을 검색 계획 모델에 전달합니다.

```bash
python advanced_lab.py query --mode planned --query "2026년 6월 30일과 7월 1일 국내 출장 숙박 한도를 비교하고, 한도를 초과할 때 필요한 절차와 해외 숙박 한도가 있는지도 알려주세요." --out results/advanced/planned-query.json
```

**완료 확인:** `RETRIEVAL OK: planned`, `llm_query_planning: true`, 실제 생성된 `planned_queries`, `modelQueryPlanning`·`searchIndex` 활동이 보입니다. `results/advanced/planned-query.json`에 저장됩니다. 작성자의 기록에서는 세 하위 질의가 관측됐지만 개수·문구는 고정 출력이 아닙니다. 계획 증거가 없으면 코드가 오류로 중단하며 일반 검색을 계획형이라고 부르지 않습니다.

**다음:** [4. Judge 교정](#calibration) · [진행표](#lab-map)

---

<a id="calibration"></a>
## 4. Judge 교정과 고정

**답변을 평가하기 전에 채점자부터 확인합니다.** 교정은 모델 재학습이 아니라, 미리 정한 정상 답변과 오답을 채점자가 구분하는지 시험하는 절차입니다.

<a id="acceptance-criteria"></a>
### 4-1. 합격 기준 먼저 읽기

[acceptance.json](../advanced-rag/acceptance.json)의 기준은 새 질문을 보기 전에 고정합니다.

**업무 검사**는 답변의 형식·결정·금액·출처가 정답과 맞는지, **검색 검사**는 필요한 규정 조각을 찾았는지 확인합니다. Judge의 **Groundedness**는 근거 충실도, **Relevance**는 질문 관련성, **`policy_task_success`**는 규정에 맞게 사용자의 일을 해결했는지를 봅니다. 답변 모델에는 정답을 주지 않습니다. 정답은 코드 검사에 사용하며, 업무 성공도 Judge에는 평가용 기대 행동도 전달됩니다.

| 대상 | 합격 조건 |
|---|---|
| V2의 모든 최종 사례 | 업무·필수 근거 검색·Groundedness·**기본 Relevance**·업무 성공도 **모두 100% 통과** |
| 필수 Judge 점수 | 각각 **4/5 이상** |
| 중요 사례 | 실패 **0개**. 평균으로 실패를 숨기지 않음 |
| 업무 성공도 Judge 교정 | 정상·오답 **10개 모두 올바르게 구분** |
| 실제 검색 증거 | 벡터 인덱스·vectorizer와 `modelQueryPlanning` 활동 |
| 새 질문 | 후보 고정 **후** holdout 최소 **8개** 생성·등록 |

**점수와 통과율은 다릅니다.** `4/5`는 한 답변에 매긴 점수의 합격선이지 정확도 80%가 아닙니다. 통과율 `100%`는 해당 단계의 모든 사례가 각 필수 기준을 통과해야 한다는 뜻입니다.

**기본 Relevance도 필수 합격 지표로 유지합니다.** 최종 답변은 실제 완료된 사용자 요청을 해결해야 합니다. 추가 정보 질문은 중간 단계이지 완료 답변으로 표시하지 않습니다.

V2는 평가 데이터에 미리 정한 사용자 후속 응답을 사용합니다. 날짜 누락 사례는 질문 후 사용자의 실제 출장일을 받고, 해외 한도 부재 사례는 금액을 꾸미는 대신 사용자가 재무팀 문의 체크리스트를 요청하는 단계를 거칩니다. 사용자 정보를 모델이 만들어 내지 않습니다. 최종 대화를 Judge에 전달하되, **초기 응답의 자동 검사는 JSON 형식·결정·금액·출처 필드에 한정**됩니다.

결과의 `intermediate_safe`는 이 필드 검사의 통과 여부이지 **초기 설명 문장의 의미나 안전성을 별도로 채점했다는 뜻이 아닙니다**. 예를 들어 `unknown`·`null`·`SCOPE` 필드가 맞아도 설명에 해외 한도를 지어낸 오류가 남을 수 있습니다. 5·7절의 `inspect --dialogue`로 초기 설명까지 직접 읽고 판단을 기록합니다.

> [!IMPORTANT]
> **자동 합격은 사람의 운영 승인이 아닙니다.** `LAB_ACCEPTANCE_PASSED`여도 `human_production_approval`은 `PENDING`입니다. `inspect`는 읽기 전용이므로 검토·승인을 저장하지 않습니다. 별도 검토는 조직의 승인 절차에 남기고 자동 결과 파일을 편집하지 않습니다.

### 4-2. 교정 실행하기

[업무 성공도 기준](../advanced-rag/policy-task-success.txt)을 읽습니다. 필요한 날짜를 묻거나 규정에 없는 금액을 만들지 않는 답은 **적절한 초기 행동**으로 인정하고, 잘못된 금액·승인 조작·설명 모순은 구분합니다. 초기 행동이 맞다는 것만으로 최종 대화까지 완료된 것은 아닙니다.

아래 교정이 대기 중이거나 오류로 끝나면 [상태·재개 표](#resume)에서 **교정에 해당하는 행**을 사용합니다.

```bash
python advanced_lab.py calibrate
```

**완료 확인:** `CALIBRATION PASSED: 10 controls`. 정상 4개와 오답 6개를 모두 구분해야 합니다. 오답에는 채점 지침 무시 요청과 불필요한 인용도 있습니다. 정답/오답 **통과 라벨은 Judge 입력으로 보내지 않습니다**. 교정은 사람이 작성한 응답과 기대 행동으로 **`policy_task_success`만** 점검하며, 실제 모델의 holdout 성능이나 기본 Groundedness/Relevance의 별도 교정 결과가 아닙니다.

평가기 버전·지침·모델·합격 기준은 `results/advanced/judge-contract.json`에 고정됩니다. Holdout 결과를 보고 Judge를 바꿔도 된다는 뜻이 아닙니다.

**다음:** [5. V1 → V2 비교](#improve) · [진행표](#lab-map)

---

<a id="improve"></a>
## 5. 실제 V1 실패와 통제된 V2 개선

[V1 기록](../advanced-rag/fixtures/recorded-v1.json)은 **D02·D03·D04·D08의 실제 이전 LIVE 답변 4개**입니다. 억지로 만든 오답이 아니며, D02의 불필요한 출처를 그대로 보존했습니다. 이를 다시 읽는 일을 새로운 생성이라고 표현하지 않습니다.

<a id="run-stages"></a>
### 네 실행 묶음의 차이

**`--stage`는 사용할 실행 묶음의 이름**이며, 같은 이름의 `results/advanced/` 하위 폴더에 결과가 저장됩니다. 아래 표는 흐름을 이해하기 위한 것이며 **명령은 이어지는 5 → 6 → 7절 순서**로 실행합니다.

| `--stage` 값 | 질문과 검색 입력 | 확인할 것 |
|---|---|---|
| `v1-recorded` | 이전 dev 4개의 답변·검색 문맥을 가져옴 | 보존된 V1 실패를 현재 Judge도 어떻게 평가하는가 |
| `v2-replay` | 같은 dev 4개·같은 초기 검색 문맥으로 V2 답변을 새로 생성 | 검색 차이를 제외하고 지침·대화 완료 절차를 개선했는가 |
| `planned-dev` | 같은 dev 4개를 실제 검색부터 다시 실행 | V2가 검색을 포함한 전체 흐름에서도 기준을 충족하는가 |
| `holdout` | 후보 고정 후 만든 새 질문 8개를 실제 검색부터 실행 | 개선에 쓰지 않은 새 사례에서도 고정한 후보가 기준을 충족하는가 |

예를 들어 `--stage v2-replay`의 **생성·채점이 모두 끝나면** `results/advanced/v2-replay/report.md`에서 보고서를 읽습니다. V2를 두 번 확인하는 것은 점수를 다시 뽑는 일이 아니라 **저장된 문맥에서의 비교와 실제 검색을 포함한 확인을 분리**하는 것입니다.

### 5-1. 이전 V1 답변을 가져와 현재 Judge로 채점하기

먼저 로컬 V1 기록을 가져옵니다.

```bash
python advanced_lab.py baseline
```

**완료 확인:** `Imported four genuine recorded V1 answers.`가 보입니다. 다음 `judge`는 과거 점수를 복사하지 않고 **현재 고정한 Judge로 수행하는 유료 LIVE 평가**입니다.

```bash
python advanced_lab.py judge --stage v1-recorded
```

**완료 확인:** `Evaluation complete: 4 cases × 3 metrics`가 나온 뒤에만 아래 `inspect`로 갑니다. 대기 중이면 같은 `judge --stage v1-recorded` 명령을 재실행합니다.

```bash
python advanced_lab.py inspect --stage v1-recorded --case-id D02
```

**완료 확인:** `Business checks`의 D02 `citations: false`와 `Scores`를 확인합니다. 기대 출처는 `["TRAVEL-CURRENT"]`인데 기록된 V1은 `["TRAVEL-CURRENT", "SCOPE"]`를 인용해 엄격한 출처 집합 검사에 실패합니다. **출처가 검색됐다는 사실과 답변에 꼭 필요한 출처라는 판단은 다릅니다.** Judge의 이유는 `results/advanced/v1-recorded/report.md`에서 읽습니다.

<a id="read-case"></a>
### 5-2. 한 사례의 기대값과 실제값 읽기

`inspect`는 **생성·채점이 모두 완료된 결과를 읽기만** 합니다. `--context`를 붙이면 답변에 제공한 실제 검색 문맥도 출력합니다. 실패를 확인하려고 `run`·`judge`를 다시 실행할 필요는 없습니다.

**답변 JSON의 네 항목부터 읽습니다.** JSON은 이름과 값을 짝지어 저장하는 형식이며, 아래 항목은 코드가 자동으로 저장합니다. 직접 채우거나 고치지 않습니다.

| 답변 항목 | 뜻 |
|---|---|
| `decision` | 규정에 따른 결정. 아래 다섯 값 중 하나 |
| `limit_krw` | 적용할 숙박 한도(원). 청구 금액이 아님. `null`이면 한도를 결정할 수 없거나 숙박 한도와 무관한 질문이며 **0원이라는 뜻이 아님** |
| `citations` | 답변에 사용한 공식 출처 ID 목록. 예: `["TRAVEL-CURRENT"]` |
| `answer` | 직원에게 보여 주는 설명. 필드 검사가 맞아도 이 문장에 모순이 있는지 직접 읽음 |

`decision`의 값은 `allowed`(허용), `needs_approval`(사전 승인 필요), `not_allowed`(금지), `unknown`(규정에 없음), `needs_info`(사용자 정보가 부족함)입니다. **규정에 없는 금액을 추측하지 않는 `unknown`, 출장일을 먼저 묻는 `needs_info`도 올바른 초기 행동일 수 있습니다.** 이 값이 실제 정산이나 승인을 실행하지는 않습니다.

이제 같은 사례의 기대값·검색·점수를 대조합니다.

| 출력 | 확인할 것 |
|---|---|
| `Case result` | 이 사례의 자동 기준 통과 여부. `FAIL`은 답변/검색/점수의 기준 미달이며 명령 실패가 아님. `PASS`도 운영 승인이 아님 |
| `Question`, `Expected decision / limit / citations`, `Expected behavior` | 질문과 사람이 미리 정한 결정·한도·최소 출처·기대 행동. **기대값은 모델이 만든 답이 아님** |
| `Actual answer`, `Business checks` | 실제 답변과 기대값 비교. `true`는 해당 검사 통과, `false`는 실패. 예: D02의 `citations: false` |
| `Required chunks` → `Chunks` → `Required chunks found` | 필수 규정 조각 → 실제 검색 조각 → 필수 조각을 모두 찾았는지. 검색 조각 ID와 답변의 공식 출처 ID는 다름 |
| `Scores` / `Final scores` | 세 지표 각각 **4 이상**인지 확인. Judge가 높게 채점해도 업무·검색 검사 실패는 남음 |
| 같은 stage의 `report.md` | 같은 사례 ID의 **점수 이유**와 실제 답변을 대조 |

**D02에서는** `current-lodging`이 검색 조각 ID이고 `TRAVEL-CURRENT`가 그 조각의 공식 출처 ID입니다. 필요한 조각을 찾았더라도 불필요한 `SCOPE`까지 인용하면 업무 검사에는 실패할 수 있습니다.

**대화 사례에서는 기대값과 검색 검사가 최종 응답 기준**입니다. 아래 `--dialogue`의 초기 응답과 최종 응답을 구분해 읽습니다. `Initial field checks`가 `true`여도 초기 설명 문장의 의미까지 자동 검증한 것은 아닙니다.

**오류 표에서 이곳으로 왔다면** 출력된 실패 사례를 확인한 뒤 [상태·재개 표](#resume)로 돌아갑니다. 실패한 실험을 보존하고, 뒤 단계를 실행하지 못했다면 8절에서 미실행으로 기록합니다.

### 5-3. V2의 차이를 확인하고 생성·채점하기

[V1](../advanced-rag/instructions.v1.txt)과 [V2](../advanced-rag/instructions.v2.txt)를 비교합니다. V2는 최소 충분한 근거를 선택하고, 필요한 추가 정보 요청·업무 이관 대화까지 마무리합니다.

[개발용 후속 응답](../advanced-rag/dev-followups.json)은 생성 전에 정합니다. 실제 고객의 발언이나 사람의 운영 승인이 아니라 명시적인 평가용 사용자 대화 데이터이며, 원하는 점수는 포함하지 않습니다. **코드가 이 후속 응답을 자동으로 전달하므로 참가자가 터미널에 출장일이나 추가 질문을 입력할 필요는 없습니다.**

**이번에는 제공된 V2를 그대로 사용합니다.** 지침 파일을 직접 수정하지 않고 차이를 설명한 뒤 실행합니다. 개인 지침 변경은 이 실행을 보존한 다음 [별도 실험](#resume)으로 구분합니다.

```bash
python advanced_lab.py run --stage v2-replay
```

**완료 확인:** `GENERATION COMPLETE: v2-replay; 4 answers.`. 필요한 후속 대화를 포함해 **최종 답변이 4개**라는 뜻이며, 모든 중간 응답까지 합한 호출 횟수는 아닙니다.

```bash
python advanced_lab.py judge --stage v2-replay
```

**완료 확인:** `Evaluation complete: 4 cases × 3 metrics`. 대기 중이면 같은 채점 명령을 재실행하고, 완료 후 D02를 V1과 대조합니다.

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D02
```

<a id="dialogue-check"></a>
### 5-4. D04·D08의 대화 전체 읽기

초기 설명의 모순까지 직접 확인하고, 문제가 있다면 해당 문장을 근거로 판단합니다.

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D04 --dialogue
```

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D08 --dialogue
```

| 출력 항목 | 읽는 방법 |
|---|---|
| `User` → `Assistant` | 처음 질문 → 초기 답변. 규정에 없는 금액·승인을 만들지 않았는지 확인 |
| `Evaluation-user follow-up` | 평가 데이터에 미리 정한 사용자 후속 응답. 본인이 지금 입력한 답이 아님 |
| `Final answer` → `Final scores` | 후속 요청까지 처리한 최종 답변 → 그 최종 응답의 세 점수 |
| `Initial field checks (not prose evaluation)` | 초기 응답의 필드 검사만 의미. 초기 설명의 의미까지 통과한 것이 아님 |

**완료 확인:** D02의 출처가 어떻게 달라졌는지, D04·D08이 추가 요청 이후 어떻게 마무리되는지 설명할 수 있습니다. 같은 초기 저장 문맥·답변 모델·생성 설정·Judge에서 시작하되 필요한 사용자 후속 대화를 추가로 완료합니다. **지침과 대화 완료 절차를 개선한 것**이며 지침 문구만의 효과라고 주장하지 않습니다. V1을 일부러 약화하거나 실패할 때까지 다시 뽑지 않습니다.

**다음:** [6. 전체 파이프라인과 고정](#freeze) · [진행표](#lab-map)

---

<a id="freeze"></a>
## 6. 전체 파이프라인을 확인한 뒤 고정

**같은 실행을 반복하는 단계가 아닙니다.** 5절은 저장된 초기 검색 문맥에서 V2를 확인했고, 이번 `planned-dev`는 실제 벡터·LLM 계획 검색부터 최종 답변까지 연결해 확인합니다.

### 6-1. 실제 검색부터 생성·채점하기

```bash
python advanced_lab.py run --stage planned-dev
```

**완료 확인:** `GENERATION COMPLETE: planned-dev; 4 answers.`가 나오면 채점합니다.

```bash
python advanced_lab.py judge --stage planned-dev
```

**완료 확인:** `Evaluation complete: 4 cases × 3 metrics`. 대기 중이면 같은 채점 명령을 재실행합니다. 초기 질문과 필요한 후속 대화 모두 정해진 검색 절차를 사용합니다. 채점 명령의 종료 코드 0만으로 dev 합격을 판단하지 않습니다.

### 6-2. 통과한 후보의 조건 고정하기

**5→6절 사이에 V2 지침·후속 응답·모델·설정을 바꾸지 않습니다.** 두 dev 검증은 같은 후보와 입력 계약을 사용해야 합니다. 변경이 필요하면 기존 결과를 보존하고 [새 실험](#resume)에서 두 검증을 모두 수행합니다.

```bash
python advanced_lab.py freeze
```

**완료 확인:** `FROZEN`과 계약 해시. 해시는 실험 조건이 바뀌었는지 확인하는 지문이며 다른 명령에 복사해 넣을 필요는 없습니다. 실제 V1 실패가 있어야 하며 V2 동일 문맥 및 계획형 dev가 기준을 통과해야 합니다. 지침·Judge·모델 버전·검색 설정·소스 정의·코퍼스를 새 질문 생성 전에 고정합니다. 실패하면 holdout으로 넘어가지 않고 [재개 표](#resume)에 따라 원인과 미실행 단계를 보존합니다.

**`Dev acceptance is not met`라면** 터미널에 실패한 stage·사례 ID, 해당 `report.md`, 그대로 실행할 수 있는 `inspect --context` 명령이 나옵니다. 그 명령으로 [기대값과 실제값](#read-case)을 대조합니다. 입력 오류와 달리 dev의 품질 차단은 같은 생성·채점을 반복해 해결하지 않습니다.

**`FROZEN` 확인 후 다음:** [7. 새 질문](#holdout) · [진행표](#lab-map)

---

<a id="holdout"></a>
## 7. 고정한 뒤 새 질문 생성

### 7-1. 새 질문 8개 생성·등록하기

```bash
python advanced_lab.py create-holdout
```

새 난수 시드로 **미리 정의된 8개 시나리오의 날짜·도시·금액을 새로 채웁니다**. 현재/과거 한도, 한도 초과 승인, 해외 범위, 날짜 누락, 금지 좌석, 경계값을 포함합니다. 새로운 매개변수 사례이지 광범위한 블라인드 일반화 검증은 아닙니다. 날짜 누락과 해외 이관 사례에는 명시적인 평가용 사용자 후속 응답이 있습니다. 질문·후속 응답·정답·생성 근거는 `results/advanced/holdout-data/`에 저장합니다.

**완료 확인:** `HOLDOUT REGISTERED: 8 new cases`와 `holdout-registration.json`. 이 명령은 모델 호출 없이 질문 생성과 등록을 함께 수행합니다. 이미 있으면 덮어쓰지 않습니다. 합격하려고 질문을 다시 뽑지 않으며 중단 시에는 [재개 표](#resume)를 따릅니다.

### 7-2. 고정된 후보로 생성·채점하기

```bash
python advanced_lab.py run --stage holdout
```

**완료 확인:** `GENERATION COMPLETE: holdout; 8 answers.`가 나오면 채점합니다.

```bash
python advanced_lab.py judge --stage holdout
```

**완료 확인:** `Evaluation complete: 8 cases × 3 metrics`. 대기 중이면 같은 채점 명령을 재실행합니다. 완료된 두 후속 대화에서 [앞서 본 출력 순서](#dialogue-check)대로 초기 설명과 최종 답을 함께 읽고 판단을 기록합니다.

### 7-3. N05·N06의 대화 검토하기

```bash
python advanced_lab.py inspect --stage holdout --case-id N05 --dialogue
```

```bash
python advanced_lab.py inspect --stage holdout --case-id N06 --dialogue
```

### 7-4. 최종 자동 판단과 근거 읽기

```bash
python advanced_lab.py accept
```

**완료 확인:** `results/advanced/acceptance-report.md`·`acceptance-result.json`이 저장됩니다. 아래 순서로 **본인 실행**을 읽습니다.

| 읽을 파일 (`results/advanced/` 기준) | 확인할 내용 |
|---|---|
| `acceptance-report.md` | 제목의 최종 판정 → 단계별 통과율 |
| `acceptance-result.json` | `rows`의 N01–N08 → `business_checks`, `required_chunks_found`, `scores`, `passed`. 중간 대화 사례는 `intermediate_safe`도 확인 |
| `holdout/report.md` | 같은 ID의 실제 답변과 각 Judge 점수의 이유 |

`LAB_ACCEPTANCE_PASSED`는 새 시나리오 8개의 **Relevance를 포함한 모든 최종 응답 지표와 초기 필드 검사**가 통과했을 때만 나옵니다. `LAB_ACCEPTANCE_BLOCKED`와 종료 코드 `2`는 품질 보류이며 실습 명령을 잘못 입력했다는 뜻이 아닙니다. `ERROR:`·`usage:`로 끝난 실행은 별도로 해결하며 완료로 기록하지 않습니다.

차단되면 실패와 보류 이유를 기록하고 8절로 이동합니다. 자동 합격이어도 직접 읽은 초기 설명에 모순이 있다면 그 판단을 따로 기록하고 운영 적용은 보류합니다. 고정된 지침·Judge를 바꾸거나 합격 사례만 고르지 않습니다. 다음 개선은 [별도 작업 복사본의 새 실험](#resume)과 새로운 holdout으로 진행합니다.

**다음:** [8. 결과·리소스 보존](#retention) · [진행표](#lab-map)

---

<a id="retention"></a>
## 8. 결과와 리소스 보존

공용 Basic 서비스, 임베딩·계획·답변 배포와 본인이 실제 수행한 교정·V1/V2·고정·새 질문 결과를 **실패까지 포함해 보존**합니다. 생성된 보고서로 마지막 완료 단계·합격/보류 근거·미실행 항목을 확인하고, 리소스 소유자와 다음 비용 확인 시점을 정합니다. Basic 유지 비용은 계속 발생합니다.

### 내 실행의 완료 체크리스트

**존재하는 파일뿐 아니라 완료 상태와 건수까지 확인합니다.** 중간에 차단됐다면 뒤 항목은 체크하지 않고 **마지막 완료 단계·오류 또는 품질 실패·미실행 단계**를 남깁니다. 전체 경로를 완료한 것으로 표현하지 않습니다.

- [ ] `setup.json`과 두 질의 JSON에서 실제 벡터·검색 계획 증거를 확인했다.
- [ ] `calibration-result.json`의 `passed: true`와 교정 10개, `judge-contract.json`을 확인했다.
- [ ] `v1-recorded`의 가져온 답변 4개, `v2-replay`·`planned-dev` 각각의 새 답변 4개와 세 지표의 점수·이유를 확인했다.
- [ ] `frozen.json` 이후 등록된 새 질문 8개와 `holdout`의 생성·채점 완료를 확인했다.
- [ ] N05·N06의 초기 설명까지 읽었고, 본인 `acceptance-report.md`의 합격/보류와 그 이유를 설명할 수 있다.
- [ ] 결과 폴더 전체, 실제 남아 있는 Azure 자원, 비용 확인 결과와 다음 확인 조건을 보존했다.

**파일 읽기:** VS Code에서 Ctrl+P / macOS Cmd+P에 `results/advanced/acceptance-report.md`를 입력합니다. Markdown 미리보기로 요약을 읽고, 세부 실패는 위 7절 표의 같은 사례 ID로 찾습니다. 자동 결과 파일을 수정해 체크나 승인 표시를 넣지 않습니다.

**비용 확인:** Azure 포털 → **Cost Management → Cost analysis**에서 본인 그룹으로 범위를 좁힙니다. 다른 그룹의 Search를 재사용했다면 그 비용도 소유자와 확인합니다. 아직 집계되지 않은 0원은 무료라는 뜻이 아닙니다. [보존 절차](cleanup.md#retain-resources)만 수행하고, 별도 삭제 결정이 없으면 삭제 절차는 건너뜁니다.

**완료 확인:** 본인의 결과 파일과 실제 대화를 근거로 V1의 실패, V2의 변화, 새 질문의 결과와 한계를 설명할 수 있습니다. 초기 단계에서 중단했다면 뒤 단계는 미실행임을 밝히고, 보존할 자원과 비용 상태를 확인합니다.

마지막으로 **“V1에서는 ___가 문제였다. V2에서는 ___가 달라졌다. 새 질문에서는 ___였으므로 ___로 판단한다.”**를 본인 결과로 설명합니다. 점수가 낮아도 실제 완료한 평가와 보류 판단은 유효합니다. 자동 합격을 운영 승인이라고 말하지 않습니다.

본인 값이 들어간 `config.json`·`config.advanced.json`, 원본 녹화, `results/`는 Git에 올리지 않습니다. 버전별 지침과 정리된 V1 실패 예시는 실습 자료로 보존합니다.

[진행표로 돌아가기](#lab-map) · [중단·재개 찾기](#resume)

---

<a id="results"></a>
## 참고: 작성자의 실행 기록

**본인의 실습을 끝내는 데 아래 기록을 재현할 필요는 없습니다.**

<details>
<summary>2026-09-28 관측 결과와 환경 보존 기록 펼치기</summary>

**아래는 2026-09-28 새 환경에서 기록한 한 번의 완결형 실행 결과이며 재현 보장이 아닙니다.** 새 그룹·Foundry·모델·Basic Search를 준비하고 별도 작업 복사본에서 공통 준비의 N01 한 건부터 최종 검증까지 수행했습니다. 본인의 판정은 위 acceptance 파일로 확인합니다. 이 표와 영상은 별도 입문 LIVE 전체 또는 최소 RAG `search`/`iq` 비교를 현재 환경에서 재검증했다는 증거가 아닙니다.

V1은 제공된 실제 이전 응답 4개를 가져와 **새 환경의 Judge로 다시 채점**했습니다. 이번 V1의 Relevance 통과율은 50%이며 D04·D08은 각각 3점이었습니다. 과거 실행의 100%를 복사하지 않았습니다. V2 응답·평가는 새로 실행했고, 후보를 고정한 뒤 새 holdout을 한 번 생성했습니다. 지침·평가 기준·fixture를 바꾸거나 점수를 다시 뽑지 않았습니다.

| 단계 | 업무 | 검색 | Groundedness | Relevance | 업무 성공도 |
|---|---|---|---|---|---|
| 기록된 V1 단일 응답 4개, 새 채점 | 75% | 100% | 100% | 50% | 75% |
| V2 완료된 개발 시나리오 4개 | 100% | 100% | 100% | 100% | 100% |
| V2 벡터·계획 개발 시나리오 4개 | 100% | 100% | 100% | 100% | 100% |
| 새 고정 holdout 시나리오 8개 | 100% | 100% | 100% | 100% | 100% |

기록된 V2 dev·holdout의 모든 최종 Judge 점수는 4/5 이상이며 합격선을 낮추지 않았습니다. 이 V2 사례들에는 중요 실패도 없습니다. 명시적인 추가 정보·업무 이관 후속 요청을 포함하므로, 정보가 없는 첫 응답만으로 불가능한 질문을 해결했다는 주장이 아닙니다.

중간 추가 질문도 증거로 남기고 사용자 후속 응답의 출처를 명시합니다. 초기 설명 문장의 별도 자동 의미 평가까지 통과한 결과는 아닙니다. 실제 운영 승인은 여전히 사람의 별도 책임입니다.

**아래는 작성자의 과거 전환 기록이지 참가자의 삭제 단계가 아닙니다.** 별도 삭제 결정 없이 자원을 지우지 않습니다. Search 하나를 지우려고 리소스 그룹이나 공용 Foundry 계정을 삭제하지 않으며, Git 이력·플랫폼 감사 로그를 지우거나 조직 정책을 해제하지 않습니다.

**2026-09-28 환경 재생성 기록:** 소유자의 명시적 요청으로 이전 실습 전용 그룹을 삭제하고 완료를 확인한 뒤 새 그룹에서 재실행했습니다. 이전 로컬 결과·원본 영상은 보관했으며, 새 Basic·Foundry·세 모델 배포와 현재 교정·V1/V2·holdout 증거는 **별도 요청 전까지 유지**합니다. 다른 그룹이나 조직 정책은 변경하지 않았습니다.

**비용 확인:** 새 그룹 범위의 Cost Management 월 누계 조회에는 아직 비용 행이 없었습니다. 집계 대기이지 무료라는 뜻이 아니며, Basic 유지 비용과 모델 사용량 비용은 계속 발생할 수 있습니다. 사용량 반영 후 또는 별도 정리 결정 시 다시 확인합니다.

</details>

## 공식 참고

- [Agentic retrieval 벡터 인덱스](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-index)
- [Knowledge Base의 API 버전별 기능·지원 모델](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base)
- [Azure OpenAI vectorizer의 관리 ID·역할](https://learn.microsoft.com/azure/search/vector-search-vectorizer-azure-open-ai)
- [Search 사용자 역할과 서비스 범위](https://learn.microsoft.com/azure/search/search-security-rbac)
- [LLM 검색 계획 수준](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [Search 계층별 기능](https://learn.microsoft.com/azure/search/search-sku-tier)
- [Entra 인증 임베딩](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings)
- [Foundry 사용자 지정 평가기](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)

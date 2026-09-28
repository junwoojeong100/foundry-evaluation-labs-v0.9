[English](en/setup.md) | **한국어**

# 환경 준비 바로가기

[메인 실습](../README.ko.md) · [문제 해결](reference.md#troubleshooting)

**새 실습을 시작한다면 선택한 가이드에서 출발합니다.** 입문 LIVE는 [README 실습 0](../README.ko.md#lab-0)에서 설치 없이 오답을 먼저 판단합니다. 설치부터 마무리까지 필요한 명령은 해당 가이드에 있습니다.

이 문서는 **준비 단계 찾기·기존 환경 사용·중단한 실습 재개**를 위한 바로가기입니다. 같은 명령을 여기서 다시 실행할 필요는 없습니다.

<a id="setup-map"></a>
## 내 상황에 맞는 준비 선택

| 지금 필요한 것 | 이동할 곳 |
|---|---|
| 설치·로그인·설정 중 특정 단계 찾기 | [공통 준비 1–7](#common-setup) |
| 허가받은 프로젝트와 모델이 이미 있음 | [기존 환경 준비](#existing-environment). 자원 생성 생략 |
| 포털 대신 CLI로 새 환경 만들기 | [CLI 대체 경로](#cli-provision). README 준비 3–5를 대체 |
| 중단한 실습 이어 하기 | [재개 절차](#resume) → [결과 파일별 재개 위치](#resume-checkpoints) |
| Azure 제약으로 LIVE를 진행할 수 없음 | [DEMO로 전환](#switch-to-demo) |
| 사용량·남은 리소스 비용 확인 | [비용 확인](#cost) |

> [!IMPORTANT]
> **RAG 참가자는 준비 후 원래 경로로 돌아갑니다.** [완결형 Search 준비](complete-lab.md#search-setup) 또는 [Optional RAG 준비](optional-rag.md#prerequisites)로 복귀하며, 입문 실습 전체를 수행하지 않습니다.

**입문 LIVE의 신규 설정은 `gpt-6-luna`·`swedencentral`·배포 이름 `eval-model`입니다.** 답변과 Judge에 같은 배포를 사용하고, 생성한 리소스는 실습 후에도 모두 보존합니다. 모델·지역을 임의 대체하지 않으며 마지막에는 [보존 상태와 비용](../README.ko.md#retain-resources)을 확인합니다. 기존 환경의 실제 배포 이름과 완결형의 추가 모델은 각각 해당 경로를 따릅니다.

<a id="common-setup"></a>
## 공통 준비 바로가기

<a id="tools"></a>
### 준비 1. 코드와 도구 준비

[준비 1: 코드 받기와 도구 설치](../README.ko.md#setup-tools) — 운영체제별 명령, 터미널 위치, 가상환경을 확인합니다. 완료 신호는 `LOCAL OK`와 `dev 8개, holdout 4개`입니다.

<a id="sign-in"></a>
### 준비 2. 같은 계정·구독으로 로그인

[준비 2: 사용할 구독으로 로그인](../README.ko.md#setup-sign-in) — 포털과 CLI의 계정·테넌트·구독을 맞춥니다. `az account show`의 `account`까지 대조하며, `YOUR-...`에는 해당 화면과 조회 결과에서 확인한 값을 넣습니다.

<a id="create-project"></a>
### 준비 3. 전용 그룹과 프로젝트 만들기

[준비 3: 전용 그룹과 Foundry 프로젝트](../README.ko.md#setup-project) — 자원별 역할과 실제 이름, 생성 순서를 확인합니다. 그룹뿐 아니라 Foundry 리소스·프로젝트도 `swedencentral`인지 확인합니다. 공유 자원을 새 전용 자원으로 오해하지 않습니다.

<a id="permissions"></a>
### 준비 4. 데이터 접근 권한 확인

[준비 4: 모델 호출과 평가 권한](../README.ko.md#setup-permissions) — 전용 환경의 본인과 프로젝트 관리 ID에 상위 Foundry 리소스 범위의 Foundry User를 확인합니다. 생성 권한·평가 권한·기존 환경의 최소 범위는 [권한 계약](reference.md#permissions-contract)에서 구분합니다. 목록에서 프로젝트 ID를 못 찾으면 [관리 ID 선택 도움말](reference.md#managed-identity-access)을 사용합니다.

<a id="deploy-model"></a>
### 준비 5. 모델 하나 배포

[준비 5: 모델 하나 배포](../README.ko.md#setup-model) — 모델은 `gpt-6-luna`, 배포 이름은 `eval-model`입니다. 두 이름을 혼동하지 않습니다. 지정한 모델이나 용량을 사용할 수 없으면 [모델·지역·쿼터 도움말](reference.md#model-availability)을 봅니다.

<a id="configure"></a>
### 준비 6. 프로젝트 주소 하나 넣기

[준비 6: 설정 파일](../README.ko.md#setup-config) — `config.json`에 실제 프로젝트 주소를 넣고, 두 배포 항목은 모두 `eval-model`로 둡니다. 두 항목에 `LIVE 조회 OK`와 모델 이름 `gpt-6-luna`가 나와야 다음으로 갑니다.

<a id="smoke"></a>
### 준비 7. 답변 한 개로 연결 확인

[준비 7: 한 건의 생성·평가](../README.ko.md#setup-smoke) — `N01` 한 건으로 유료 연결을 확인합니다. 답변 형식과 두 점수·이유가 모두 있어야 합니다. 대기·낮은 점수·실행 오류의 차이는 [명령 결과 읽기](../README.ko.md#command-status)를 봅니다.

---

<a id="cli-provision"></a>
## 선택: Azure CLI로 신규 환경 준비

**README 준비 1–2를 완료한 뒤, 준비 3–5의 포털 조작 대신 사용하는 경로**입니다. Azure CLI **2.80.0 이상**과 생성·역할 할당 권한이 필요합니다. Owner는 두 작업을 수행하는 한 방법이지 모든 참가자의 최소 역할은 아닙니다. [공식 프로젝트 생성 문서](https://learn.microsoft.com/azure/foundry/how-to/create-projects)를 따르며 `azd`, 검색 서비스, 에이전트 서버는 추가하지 않습니다. 이미 프로젝트·모델을 만들었다면 다시 실행하지 않습니다.

`YOUR-...`를 준비 2에서 확인한 구독 ID와 본인이 사용할 실제 값으로 바꿉니다. 그룹·Foundry 리소스 이름은 본인 고유 이름, 프로젝트는 `eval-workshop`, 배포는 `eval-model`을 사용합니다. 아래 명령은 macOS/Linux와 PowerShell에서 동일합니다.

<details>
<summary>새 환경을 CLI로 만들 때만: 생성·권한·배포 명령 펼치기</summary>

### 1. 새 그룹과 Foundry 리소스

그룹이 존재하지 않는지 먼저 조회합니다. **`false`일 때만** 신규 이름으로 진행합니다. `true`라면 기존 그룹을 재사용하거나 지우지 말고 새 고유 이름을 선택합니다.

```bash
az group exists --name "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az group create --name "YOUR-LAB-RESOURCE-GROUP" --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --tags purpose=foundry-evaluation-workshop retain=true
```

```bash
az cognitiveservices account create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --kind AIServices --sku S0 --location swedencentral --custom-domain "YOUR-FOUNDRY-ACCOUNT" --assign-identity --allow-project-management true --subscription "YOUR-SUBSCRIPTION-ID" --yes
```

**`--assign-identity`와 `--allow-project-management true`를 생략하지 않습니다.** 상위 리소스의 관리 ID와 프로젝트 관리 기능이 필요합니다. Custom domain은 전역에서 고유해야 합니다. `retain=true` 태그는 보존 의도를 기록할 뿐 삭제를 차단하는 잠금이나 과금 중지 장치가 아닙니다.

### 2. 프로젝트와 실제 주소·ID 확인

```bash
az cognitiveservices account project create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --project-name eval-workshop --location swedencentral --assign-identity --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az cognitiveservices account show --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,location:location,state:properties.provisioningState}" --output json
```

```bash
az cognitiveservices account project show --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --project-name eval-workshop --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,location:location,state:properties.provisioningState,principalId:identity.principalId,endpoints:properties.endpoints}" --output json
```

두 자원의 지역 `swedencentral`과 상태 `Succeeded`를 확인합니다. 첫 조회의 `id`는 아래 **`YOUR-FOUNDRY-RESOURCE-ID`**, 프로젝트 조회의 `principalId`는 **`YOUR-PROJECT-PRINCIPAL-ID`**입니다. `endpoints`의 **AI Foundry API** 주소를 준비 6의 `config.json`에 사용합니다. 주소를 이름으로 조립하지 않습니다.

### 3. 본인과 프로젝트 관리 ID의 권한

```bash
az ad signed-in-user show --query "{account:userPrincipalName,objectId:id}" --output json
```

계정을 다시 대조하고 `objectId`를 **`YOUR-USER-OBJECT-ID`**로 사용합니다. 상위 Foundry 리소스의 IAM에서 기존 역할을 먼저 확인하고, **없는 대상에게만** 다음 역할을 할당합니다. CLI 생성은 포털과 달리 필요한 데이터 역할이 자동 부여되었다고 가정하지 않습니다.

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az role assignment create --assignee-object-id "YOUR-PROJECT-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

두 역할 모두 **Foundry User**이고 범위는 `/accounts/실제리소스이름`까지입니다. 구독 전체나 다른 리소스로 넓히지 않습니다. 이 상위 범위는 하위 프로젝트에도 상속되므로 **본인 전용 환경의 시작 구성**으로 사용합니다. 기존 공유 환경의 범위를 임의로 넓히지 않습니다. 본인은 `User`, 프로젝트 관리 ID는 `ServicePrincipal`이며 상위 계정의 관리 ID와는 별개입니다.

### 4. 모델·쿼터 확인 후 한 개 배포

```bash
az cognitiveservices model list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?model.name=='gpt-6-luna']" --output json
```

```bash
az cognitiveservices usage list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?name.value=='OpenAI.GlobalStandard.gpt-6-luna'].{name:name.value,current:currentValue,limit:limit}" --output json
```

첫 조회는 SKU 정보가 빠지지 않도록 해당 모델 항목 전체를 보여 줍니다. 모델·선택 버전·`GlobalStandard` 지원과 용량 단위를 확인합니다. 아래는 기록된 **60K TPM / capacity 60** 구성의 예시입니다. 현재 모델/SKU에서도 **capacity 1 = 1000 TPM**인지 확인하고, 해당 쿼터의 **`limit - current`가 60 이상**일 때만 사용합니다. 다른 모델의 단위나 쿼터 이름을 이 예시로 추정하지 않습니다.

쿼터 조회에는 구독 범위의 조회 권한이 따로 필요합니다. 403이나 빈 목록을 “쿼터 0”으로 단정하지 말고 [권한·가용성 도움말](reference.md#model-availability)에서 계정·권한·제공 여부를 확인합니다. 남은 쿼터가 있어도 지역의 실제 배포 용량까지 보장하지는 않습니다.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name eval-model --model-name gpt-6-luna --model-version "YOUR-MODEL-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

`YOUR-MODEL-VERSION`에는 **조회한 실제 버전**을 넣습니다. 2026-09-27 실습에서는 `2026-09-22`를 사용했으며 이 값을 현재도 제공한다고 가정하지 않습니다. 완료 후 [README 준비 6](../README.ko.md#setup-config)으로 돌아가 설정·조회·한 건 생성·평가를 진행합니다. API 키를 조회하거나 저장할 필요는 없습니다. **마지막에 삭제 명령을 실행하지 않습니다.**

완결형 RAG는 기록된 V1 비교를 위해 [지정 답변 버전](complete-lab.md#setup)이 필수입니다. 다른 제공 버전을 사용할 수 있는 입문 경로와 구분합니다.

</details>

<a id="existing-environment"></a>
## 이미 허가받은 환경이 있다면

새 자원을 만들거나 기존 모델의 이름·설정을 바꾸지 않습니다. 입문 참가자는 아직 하지 않았다면 [실습 0](../README.ko.md#lab-0)의 A/B 판단만 먼저 한 뒤 이 절로 돌아옵니다.

**사용 가능한 환경:** 새 포털에서 사용하는 **Foundry 프로젝트**와 그 프로젝트에서 접근 가능한 모델 배포입니다. Project endpoint는 `https://리소스이름.services.ai.azure.com/api/projects/프로젝트이름` 형태입니다. 허브 기반 classic 프로젝트의 연결 문자열이나 Azure OpenAI 모델 주소만 있다면 이 실습의 설정으로 대신 사용할 수 없습니다.

기존 환경도 이 실습의 **`gpt-6-luna`·`swedencentral` 조건**을 확인합니다. 실제 배포 이름이 달라도 되지만 모델·지역을 바꾼 실험으로 조용히 대체하지 않습니다. 모델명·배포명·모델 버전·API 버전은 [서로 다른 값](reference.md#model-endpoint-contract)입니다.

**완결형 참가자는 아래 5번 대신 [완결형 Search 준비](complete-lab.md#search-setup)로 돌아갑니다.** 기존 배포도 완결형의 지정 이름·모델 버전 조건을 먼저 확인하며, 조건을 맞추려고 공유 배포를 임의 변경하지 않습니다.

**Optional RAG 참가자는 아래 5번 대신 [Optional RAG 준비](optional-rag.md#prerequisites)로 돌아갑니다.** 완결형 실습 전체를 먼저 수행할 필요는 없습니다.

1. 환경 소유자에게 아래 정보를 확인해 다음 단계의 로그인·설정에 사용합니다. API 키나 공유 비밀번호를 받지 않습니다.
2. [준비 1](../README.ko.md#setup-tools)에서 로컬 도구를 준비하고, [준비 2](../README.ko.md#setup-sign-in)의 **로그인과 구독 확인**을 수행합니다. 자원을 만들지 않으므로 Owner 취득이나 공급자 등록은 요구하지 않습니다.
3. [준비 4](../README.ko.md#setup-permissions)와 [기존 환경의 권한 범위](reference.md#permissions-contract)를 대조합니다. 부족한 역할은 할당 권한이 있는 소유자에게 요청하며 공유 계정 전체에 임의로 추가하지 않습니다.
4. 기존 배포가 **Chat Completions·Structured Outputs·Judge 평가**를 지원하는지 확인합니다. [준비 6](../README.ko.md#setup-config)의 설정에 실제 주소와 배포 이름을 넣고 [준비 7](../README.ko.md#setup-smoke)을 완료합니다.
5. [실습 1](../README.ko.md#lab-1)로 이어갑니다. 마지막에는 소유자와 합의한 본인 작업만 정리합니다. **공유 프로젝트·모델·리소스 그룹은 일괄 삭제하지 않습니다.**

| 소유자에게 확인할 정보 | 사용할 곳 |
|---|---|
| 테넌트 ID·구독 ID | 포털과 CLI를 같은 계정·구독에 연결 |
| 리소스 그룹·Foundry 리소스·프로젝트 이름, 지역 | 준비 4의 대상 구분과 마지막 정리 범위 확인 |
| Project endpoint·실제 모델 배포 이름 | `config.json`. 모델 이름이 아니라 배포 이름을 사용 |
| 본인·프로젝트 관리 ID의 실제 역할과 범위, 사용·비용·정리 허용 범위 | 호출·평가 권한 및 공유 환경 보호 |

본인 화면에서 프로젝트 관리 ID를 조회할 수 없으면 소유자에게 준비 4의 ID·역할 대조를 요청합니다. **`eval-workshop`·`eval-model`은 신규 생성 경로의 예시 이름**이므로 기존 자원의 이름을 바꾸지 않습니다. 두 모델 용도로 같은 배포를 쓰면 `config.json`의 `model_deployment`와 `judge_deployment`에 모두 그 이름을 넣습니다.

<a id="switch-to-demo"></a>
## LIVE가 막혀 DEMO로 전환할 때

1. 새 LIVE 호출을 멈추고 **중단한 단계·오류·이미 만든 Azure 자원**을 확인합니다. 기존 결과·설정·작성한 질문을 지우지 않습니다.
2. [DEMO 가이드의 준비](offline.md#prepare)로 이동합니다. 설치한 Python·VS Code·가상환경을 재사용하고 기존 LIVE 기록은 보존합니다.
3. DEMO 가이드의 `results/demo-*` 폴더만 사용해 실습 1–6을 진행합니다. LIVE 명령의 모드만 바꾸거나 LIVE 점수와 DEMO 점수를 비교하지 않습니다.
4. LIVE에서 만든 자원이 있다면 DEMO가 끝나도 [보존 상태와 비용](cleanup.md#retain-resources)을 확인합니다. DEMO 전환을 이유로 리소스를 자동 삭제하지 않습니다. 이미 제출한 원격 평가는 터미널을 닫거나 DEMO로 전환해도 자동 취소되지 않습니다.

<a id="cost"></a>
## 비용 확인

기본 경로의 호출 규모는 [README 준비](../README.ko.md#prepare)에 있습니다. [모델 요금](https://azure.microsoft.com/pricing/details/azure-openai/)과 본인 배포 유형을 확인합니다. 생성 토큰 합계만으로 Judge 비용까지 계산하지 않습니다.

Azure 포털의 **Cost Management → Cost analysis**에서 해당 전용 그룹으로 범위를 좁혀 봅니다. 비용 반영은 늦을 수 있고, 예산 알림은 자동 지출 차단이 아닙니다. 끝나거나 중도 중단하면 [리소스 보존·정리](cleanup.md)를 확인합니다. 기본은 보존이며, 보존을 과금 중지로 해석하지 않습니다.

<a id="resume"></a>
## 나중에 이어서 하기

아래 재개 표는 **`lab.py` 입문 LIVE/DEMO용**입니다. `advanced_lab.py`는 파일 구조와 출력 경로가 다르므로 [완결형 상태·재개 표](complete-lab.md#resume)를 사용합니다.

1. VS Code에서 이전의 **`lab.py`가 있는 폴더**를 열고 새 터미널을 엽니다.
2. 가상환경만 다시 활성화합니다. macOS/Linux는 `source .venv/bin/activate`, Windows는 `.\.venv\Scripts\Activate.ps1`입니다. 활성화가 막혔던 Windows 환경에서는 계속 `.\.venv\Scripts\python.exe`를 사용합니다. 패키지를 매번 재설치하지 않습니다.
3. 아래 [결과 파일별 재개 표](#resume-checkpoints)에서 **마지막 완료 단계와 다음 명령**을 찾습니다. LIVE 로그인이 만료됐으면 [로그인](../README.ko.md#setup-sign-in)만 다시 합니다. DEMO는 로그인하지 않습니다.

| 중단 당시 상태 | 재개 방법 |
|---|---|
| `run`이 일부 답변만 저장 | **같은 명령·같은 입력·같은 `--out`**으로 재실행. 저장된 행은 다시 생성하지 않음 |
| `judge`가 처리 중 | **같은 `judge` 명령 전체** 재실행. `--like`도 유지하며 기존 원격 작업 조회 |
| `judge` 수집·저장 중 `ERROR:` | 원인을 해결한 뒤 같은 명령 전체로 재개. 원격 생성 여부가 불명확하면 먼저 [ID 복구](reference.md#resume) 확인 |
| `run`/`judge`가 이미 완료 | 다음 단계로 진행. 같은 입력으로 반복하면 저장 결과를 검증·재사용하며 새 실험이 아님 |
| 누락된 사람 검토를 보완함 | 같은 `gate` 명령으로 최신 검토를 반영. 답변 생성·Judge를 다시 수행할 필요 없음 |
| 프롬프트·데이터·설정을 바꿈 | 기존 결과를 덮어쓰지 않음. 별도 결과 이름으로 새 실험을 설계 |

완료된 `run.json`·`judge.json`을 지워 재실행하지 않습니다. 응답 직후 저장 전에 끊긴 한 행은 재호출될 수 있으므로 추가 비용이 없다고 보장하지 않습니다. 폴더를 옮겼거나 원격 ID 저장 중 끊겼다면 [재개·복구 도움말](reference.md#resume)을 봅니다.

`prompts/my-v2.txt`와 `data/my-case.jsonl`은 저장소에 포함된 예제 작업본입니다. 재개할 때 새 복사본으로 덮어쓰지 말고 기존 내용과 본인의 수정을 먼저 확인합니다. 예제 재사용과 직접 편집은 구분합니다.

<a id="resume-checkpoints"></a>
### 마지막 단계가 기억나지 않는다면

**VS Code에서 본인 경로의 `results/`만 확인합니다.** 아래 `baseline`·`candidate`·`holdout`은 LIVE의 폴더명이며, DEMO에서는 각각 `demo-baseline`·`demo-candidate`·`demo-holdout`입니다. 아직 환경 준비 중이었다면 [준비 바로가기](#tools)에서 마지막 완료 신호 다음 단계로 돌아갑니다.

| 저장된 상태 / 아직 없는 것 | LIVE에서 이어갈 위치 | DEMO에서 이어갈 위치 |
|---|---|---|
| `baseline/run.json`의 `status`가 `complete`, `judge.json`은 없음 | [실습 3](../README.ko.md#lab-3): D04 사람 판단부터, 그 뒤 Judge | [실습 3](offline.md#lab-3): 동일 순서 |
| `baseline/judge.json`은 있음, candidate는 아직 없음 | [실습 4](../README.ko.md#lab-4): 가설·기존 작업본 확인부터 | [실습 4](offline.md#lab-4): 가설·V2 예제부터 |
| `candidate/run.json`은 완료, `judge.json` 또는 `comparison.md`가 없음 | [실습 4](../README.ko.md#lab-4): 후보 Judge → 비교 중 빠진 단계 | [실습 4](offline.md#lab-4): 동일 순서 |
| 후보 비교는 완료, D06의 `reviews.json` 기록이 없음 | [실습 4](../README.ko.md#lab-4)의 `review` | [실습 4](offline.md#lab-4)의 `review` |
| 후보 검토는 완료, holdout 생성·Judge·H04 검토 또는 Gate가 남음 | [실습 5](../README.ko.md#lab-5)의 첫 미완료 단계 | [실습 5](offline.md#lab-5)의 첫 미완료 단계 |
| `candidate/gate.md`와 판단 기록까지 있음 | [실습 6](../README.ko.md#lab-6): 추가 질문·보고 | [실습 6](offline.md#lab-6): 질문 검사·보고 |

파일 유무는 위치를 찾는 단서일 뿐입니다. **`status`가 `collecting`이면 같은 `run`, 평가 처리 중이면 같은 `judge`를 먼저 재개**합니다. `judge.json`이 있어도 오류가 났다면 같은 `judge`로 유효성을 확인합니다. `--like`를 생략하거나 결과 파일을 수정하지 않습니다. 이미 적은 사람의 최초 판단은 지우지 않습니다.

`gate.md`가 있어도 검토 누락이 남아 있다면 실제 사람의 검토를 추가하고 같은 `gate`를 다시 실행합니다. 점수 실패를 없애려고 답변이나 평가를 새로 뽑는 것과는 다릅니다.

[준비 선택으로 돌아가기](#setup-map)

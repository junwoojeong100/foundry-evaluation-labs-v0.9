# 처음부터 환경 만들기

[메인 실습](../README.md) · [문제 해결](reference.md#troubleshooting)

**시작 조건:** Microsoft Entra ID 계정, 활성 Azure 구독, 그 구독의 **활성 Owner 역할**. 강사가 만든 환경이나 API 키는 필요 없습니다.

**만들 것:** 본인 전용 리소스 그룹 → Foundry 리소스와 프로젝트 → 모델 배포 하나. 아래 1–7을 순서대로 진행하고 **완료 확인이 맞으면 다음으로** 갑니다. 이미 허가받은 환경이 있다면 [기존 환경](#existing-environment) 항목만 확인합니다.

모델 생성·평가에는 비용이 발생할 수 있습니다. Owner라도 조직 정책·모델 사용 자격·지역별 쿼터를 우회할 수는 없습니다. 실제 개인정보·기밀·비밀번호는 넣지 않습니다.

<a id="tools"></a>
## 1. 코드와 도구 준비

**할 일**

1. [비공개 저장소](https://github.com/junwoojeong100/foundry-evaluation-v1)의 **Code → Download ZIP**으로 코드를 받습니다. 압축을 풀어 폴더 이름을 `foundry-evaluation-v1`으로 정합니다. 이미 받았다면 생략합니다.
2. 아래 도구를 설치합니다.
3. VS Code에서 **File → Open Folder**로 이 폴더를 열고 **Terminal → New Terminal**을 선택합니다. 터미널 위치에 `lab.py`가 있어야 합니다.

| 도구 | 설치·확인 |
|---|---|
| Python 3.10 이상 | [설치](https://www.python.org/downloads/). Windows는 PATH 추가. macOS/Linux: `python3 --version`, Windows: `py -3 --version` |
| Azure CLI | [설치](https://learn.microsoft.com/cli/azure/install-azure-cli). 설치 후 새 터미널에서 `az version` |
| 편집기 | [VS Code](https://code.visualstudio.com/) 권장 |

Azure Owner와 비공개 GitHub 접근 권한은 별개입니다. 저장소를 열 수 없으면 소유자가 승인한 ZIP을 받습니다. 이 경우 GitHub 계정 없이 진행할 수 있습니다.

**본인 운영체제의 명령만 실행합니다.**

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python lab.py doctor
```

Windows — PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python lab.py doctor
```

활성화가 조직 정책으로 막히면 정책을 해제하지 않습니다. 이후 `python` 대신 `.\.venv\Scripts\python.exe`를 사용합니다. Git·Docker·azd·Jupyter는 필요 없습니다.

**완료 확인:** `LOCAL OK`와 `dev 8개, holdout 4개`. 아직 Azure 연결 확인은 아닙니다.

편집기에서 `results` 폴더를 만들고 [실습지](../WORKSHEET.md)를 **`results/my-worksheet.md`로 다른 이름 저장**합니다. 환경 이름과 마지막 완료 단계를 여기에 기록합니다. 기록과 결과는 공개 게시하지 않습니다.

<a id="sign-in"></a>
## 2. 같은 계정·구독으로 로그인

**할 일 — [Azure 포털](https://portal.azure.com)**

1. Entra ID 계정으로 로그인하고 **Subscriptions / 구독**에서 사용할 구독을 엽니다.
2. **Overview / 개요**의 구독 ID·디렉터리(테넌트) ID를 실습지에 기록합니다.
3. **Access control (IAM) → View my access**에서 구독 범위의 **Owner**가 활성인지 확인합니다. PIM 적격 역할만 있다면 조직 절차로 먼저 활성화합니다.

**터미널:** `YOUR-...`를 기록한 값으로 바꿉니다. 따옴표는 유지합니다.

```bash
az login --tenant "YOUR-TENANT-ID"
```

브라우저 로그인과 MFA를 직접 완료한 뒤 실행합니다.

```bash
az account set --subscription "YOUR-SUBSCRIPTION-ID"
az account show --query "{subscription:name,subscriptionId:id,tenantId:tenantId,state:state}" --output json
```

같은 구독의 **Resource providers / 리소스 공급자**에서 `Microsoft.CognitiveServices`도 확인합니다. 미등록이면 **Register**를 선택하고 `Registered`까지 기다립니다.

**완료 확인:** 포털과 CLI의 구독 ID·테넌트 ID가 같고 `state`가 `Enabled`입니다.

<a id="create-project"></a>
## 3. 전용 그룹과 프로젝트 만들기

**할 일 — Azure 포털**

1. **Resource groups → Create**를 선택하고 2단계의 구독을 지정합니다.
2. **새 그룹** 이름을 `rg-feval-a7k3m9`처럼 정합니다. 뒤의 영문·숫자는 본인 고유 값으로 바꾸고 실습지에 기록합니다.
3. 조직에서 허용한다면 **East US 2**를 선택하고 **Review + create → Create**로 만듭니다.

**할 일 — [Microsoft Foundry](https://ai.azure.com)**

1. 같은 계정으로 로그인합니다. **New Foundry** 전환이 보이면 켭니다.
2. **Create project**, 또는 왼쪽 위 프로젝트 선택 메뉴의 **Create new project**를 누릅니다.
3. 프로젝트 이름을 **`eval-workshop`**으로 정하고 **Advanced options**를 엽니다.
4. **같은 구독·방금 만든 그룹**을 선택합니다. 공유 리소스 대신 **새 Foundry 리소스**를 사용합니다. 이름을 입력한다면 `feval-a7k3m9`처럼 고유하게 정합니다.
5. Foundry 리소스의 지역도 확인하고 **Create**를 누릅니다.

East US 2는 시작 예시이지 모델 용량 보장이 아닙니다. 다른 지역이 필요하면 [모델·지역·쿼터 확인](reference.md#model-availability)을 따릅니다. 기존 환경의 네트워크 제한은 해제하지 않습니다.

**완료 확인:** 프로젝트가 열리고 **Manage → Project details / Resource details**에서 프로젝트와 상위 Foundry 리소스가 보입니다. Azure 포털의 전용 그룹에서도 배포 상태가 `Succeeded`입니다. **실제 그룹·리소스·프로젝트 이름과 지역**을 실습지에 기록합니다.

<a id="permissions"></a>
## 4. 데이터 접근 권한 확인

Owner는 자원을 만들 권한입니다. 모델 호출·평가에는 아래 권한도 필요합니다. 프로젝트를 만들 때 자동 할당될 수 있으므로 **있는지 확인하고 없는 것만 추가**합니다.

| 역할 | 대상 | 할당 범위 |
|---|---|---|
| **Foundry User** | 본인 계정 | 방금 만든 **Foundry 리소스** |
| **Foundry User** | **프로젝트의 관리 ID** | 같은 **Foundry 리소스** |

**할 일 — Azure 포털에서 상위 Foundry 리소스의 IAM**

1. **Access control (IAM) → Role assignments**에서 두 대상을 확인합니다. 역할이 이전 이름인 **Azure AI User**로 보일 수도 있습니다.
2. 본인에게 없다면 **Add → Add role assignment → Foundry User → User, group, or service principal**에서 본인을 선택하고 **Review + assign**합니다.
3. 프로젝트 관리 ID에 없다면 같은 역할의 **Members → Managed identity**에서 `eval-workshop` 프로젝트 ID를 선택해 할당합니다.

**상위 리소스 자체의 관리 ID와 프로젝트 관리 ID는 다릅니다.** 프로젝트의 **Identity → System assigned → Object (principal) ID**로 구분합니다. 목록에서 못 찾으면 [관리 ID 선택 도움말](reference.md#managed-identity-access)을 봅니다.

**완료 확인:** 본인과 프로젝트 관리 ID 모두 **Foundry 리소스 범위**의 Foundry User가 있습니다. 구독 전체에 추가할 필요는 없습니다. 전파를 기다리지 않고 역할을 중복 생성하지 않습니다.

<a id="deploy-model"></a>
## 5. 모델 하나 배포

**할 일 — Foundry 포털**

1. **Discover → Models**에서 **`gpt-4.1-mini`**를 엽니다. 이 실습은 Chat Completions와 JSON Schema 출력을 지원하는 이 모델로 시작합니다.
2. **Deploy → Custom settings**에서 방금 만든 프로젝트·리소스를 선택합니다.
3. 아래 값을 확인한 뒤 **Deploy**를 누릅니다.

| 설정 | 값 |
|---|---|
| Deployment name | **`eval-model`** |
| Model / version | `gpt-4.1-mini`의 제공되는 버전 |
| Deployment type | 조직 정책이 허용하면 **Global Standard** |
| Tokens per minute | 남은 쿼터 안에서, 예를 들어 **30K–60K TPM**으로 시작 |

Global Standard는 사용량 기반입니다. **Provisioned/PTU·GPU 배포는 선택하지 않습니다.** 선택한 지역에만 추론 처리가 머무는 방식도 아닙니다. TPM은 비용 상한이 아니며, 다른 사람의 쿼터를 줄이지 않습니다. 배포가 안 되면 [모델·쿼터 도움말](reference.md#model-availability)을 따릅니다.

**완료 확인:** **Build → Models**에서 `eval-model`이 **Succeeded**입니다. 모델 이름·버전·배포 유형을 기록합니다.

같은 배포를 답변 생성과 Judge에 함께 씁니다. 호출은 별개이며, 같은 모델도 스스로 오판할 수 있어 사람 검토를 함께 합니다.

<a id="configure"></a>
## 6. 프로젝트 주소 하나 넣기

**할 일**

1. Foundry 프로젝트의 **Overview** 또는 **Manage → Project details**에서 **Project endpoint**를 복사합니다.
2. [config.example.json](../config.example.json)을 `lab.py` 옆의 **`config.json`으로 다른 이름 저장**합니다.
3. 아래 **`project_endpoint`만** 실제 주소로 바꾸고 저장합니다. 이름으로 주소를 추측하지 않습니다.

```json
{
  "project_endpoint": "https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT",
  "model_deployment": "eval-model",
  "judge_deployment": "eval-model"
}
```

배포를 다른 이름으로 만들었다면 아래 두 값도 같은 실제 배포 이름으로 바꿉니다. `config.json.txt`로 저장하지 않습니다. `.env`나 API 키는 필요 없습니다.

```bash
python lab.py doctor --live
```

**완료 확인:** 두 배포 항목에 **LIVE 조회 OK**. 같은 배포가 두 줄에 나오는 것이 정상입니다. 실제 생성·평가는 다음 단계에서 확인합니다.

<a id="smoke"></a>
## 7. 답변 한 개로 연결 확인

**할 일:** 유료 호출을 작은 요청부터 확인합니다. **각 명령의 완료를 보고 다음 명령**을 실행합니다.

```bash
python lab.py run --mode live --prompt v1 --data data/my-case.example.jsonl --out results/setup-smoke
```

`1/1 ... 저장`이 보이면 채점합니다.

```bash
python lab.py judge results/setup-smoke
```

진행 중이면 **같은 명령으로 같은 작업을 조회**합니다. `judge.json`이 만들어진 뒤 확인합니다.

```bash
python lab.py inspect results/setup-smoke N01
```

**완료 확인:** 답변의 `"schema": true`, Groundedness·Relevance의 **두 점수와 이유**가 모두 있습니다. 출력된 보고서 URL로 Foundry에서도 같은 결과를 찾습니다. URL이 없으면 [결과 찾기](reference.md#portal-results)를 봅니다.

낮은 점수는 기록하고 진행합니다. 인증 오류·잘린 답변·누락된 점수는 먼저 해결합니다. 이 한 건은 연결 확인용이며 본 실습의 dev/holdout에는 포함되지 않습니다.

**준비 끝 → [메인 실습 0](../README.md#lab-0)으로 이동합니다.**

---

<a id="existing-environment"></a>
## 이미 허가받은 환경이 있다면

새로 만들지 않고 **1–2 → 4 → 6–7단계**를 진행합니다. 기존 모델의 Chat Completions·Structured Outputs·Judge 지원과 소유자가 허용한 정리 범위를 먼저 확인합니다. 공유 프로젝트·모델·리소스 그룹은 실습 후 일괄 삭제하지 않습니다.

<a id="cost"></a>
## 비용 확인

전체 경로는 **응답 22개, 평가 항목 44개**입니다. 연결 확인 1개, dev 8개씩 두 번, holdout 4개, 추가 사례 1개이며 각 응답을 두 지표로 평가합니다. 평가기 내부 호출·재시도까지 센 청구 API 횟수는 아닙니다.

Azure 포털의 전용 그룹에서 **Cost Management → Cost analysis**와 [모델 요금](https://azure.microsoft.com/pricing/details/azure-openai/)을 봅니다. 비용 반영은 늦을 수 있습니다. 예산 알림도 자동 지출 차단은 아닙니다. 끝나거나 중도 중단하면 [리소스 정리](cleanup.md)를 확인합니다.

<a id="resume"></a>
## 나중에 이어서 하기

같은 폴더를 열고 가상환경만 다시 활성화합니다. macOS/Linux는 `source .venv/bin/activate`, Windows는 `.\.venv\Scripts\Activate.ps1`입니다.

로그인이 만료됐으면 [2단계](#sign-in)로 다시 로그인합니다. 실습지의 **마지막 완료 단계 / 다음 명령**부터 이어갑니다. 완료된 결과를 새로 생성하지 않습니다. 폴더를 옮겼거나 입력을 바꿨다면 [재개·복구 도움말](reference.md#resume)을 봅니다.

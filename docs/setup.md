# 처음부터 환경 만들기

[전체 실습](../README.md) · [문제 해결](reference.md#troubleshooting)

**Microsoft Entra ID 계정과 활성 Azure 구독, 그 구독의 Owner 역할로 시작합니다.** 강사가 프로젝트나 설정 파일을 만들어 줄 필요는 없습니다. 여기서는 **본인 전용 리소스 그룹 하나, Foundry 프로젝트 하나, 모델 배포 하나**만 만듭니다.

시간 제한은 없습니다. 아래 순서대로 진행하고, 각 단계의 **완료 확인**이 맞으면 다음으로 넘어갑니다. 명령에 `YOUR-...`가 있으면 본인 값으로 바꾸되 따옴표는 유지합니다.

```text
1. 코드와 도구 준비
2. 본인 계정으로 로그인하고 구독 확인
3. 전용 리소스 그룹과 Foundry 프로젝트 만들기
4. 본인과 프로젝트의 데이터 접근 권한 확인
5. 모델 하나 배포
6. 설정 세 값 저장
7. 답변 한 개를 실제 생성하고 평가
   → 본 실습 → 본인 리소스 정리
```

Azure 리소스는 이 문서를 읽는 것만으로 생성되지 않습니다. 본인이 포털에서 만들고 모델을 호출하면 본인 구독에 비용이 발생할 수 있습니다. **구독 Owner라도 조직 정책, 모델 사용 자격, 쿼터와 지역별 가용성을 우회할 수는 없습니다.**

<a id="tools"></a>
## 1. 코드와 도구 준비

**할 일:** 이 저장소의 코드를 PC에 받고 Python과 Azure CLI를 준비합니다.

### 코드 받기

[비공개 GitHub 저장소](https://github.com/junwoojeong100/foundry-evaluation-v1)를 열어 **Code → Download ZIP**을 선택합니다. 압축을 풀고 폴더 이름을 `foundry-evaluation-v1`으로 정합니다. 이미 이 폴더가 있으면 다시 받지 않습니다.

GitHub 접근 권한이 없다면 저장소 소유자가 승인된 방법으로 제공한 ZIP을 사용합니다. **Entra ID 계정과 Azure 구독 Owner 역할이 비공개 GitHub 접근 권한까지 주지는 않습니다.** ZIP을 전달받으면 별도 GitHub 계정 없이도 실습할 수 있습니다.

### 도구 설치

| 도구 | 설치와 확인 |
|---|---|
| Python 3.10 이상 | [Python 다운로드](https://www.python.org/downloads/). Windows 설치 시 Python을 PATH에 추가. macOS/Linux는 `python3 --version`, Windows는 `py -3 --version`으로 확인 |
| Azure CLI | [운영체제별 설치 안내](https://learn.microsoft.com/cli/azure/install-azure-cli)의 Windows/macOS/Linux 항목을 따라 설치. `az version`으로 확인 |
| 편집기 | [VS Code](https://code.visualstudio.com/) 권장. **File → Open Folder**로 `foundry-evaluation-v1` 열기 |

설치 후 터미널을 새로 엽니다. VS Code의 **Terminal → New Terminal**을 사용하면 편집기와 같은 폴더에서 시작하기 쉽습니다.

**macOS / Linux — 터미널:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python lab.py doctor
```

**Windows — PowerShell:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python lab.py doctor
```

활성화가 조직 정책으로 막히면 정책을 해제하지 않습니다. 활성화 명령 대신 이후 `python`을 `.\.venv\Scripts\python.exe`로 바꿔 실행합니다. Git, Docker, azd, API 키, Jupyter는 필요 없습니다.

**완료 확인:** `LOCAL OK`와 `dev 8개, holdout 4개`가 보입니다. 이는 로컬 준비 확인이며 아직 Azure에 연결한 것은 아닙니다.

편집기에서 `results` 폴더를 만들고 [실습지](../WORKSHEET.md)를 `results/my-worksheet.md`로 다른 이름 저장합니다. 앞으로 사용할 구독·리소스 이름과 진행 위치를 여기에 기록합니다. 비밀번호나 토큰은 기록하지 않습니다.

<a id="sign-in"></a>
## 2. 본인 계정으로 로그인하고 구독 확인

**할 일:** 브라우저와 터미널이 같은 계정·테넌트·구독을 사용하도록 맞춥니다.

**Azure 포털:**

1. [Azure 포털](https://portal.azure.com)에 본인의 Microsoft Entra ID 계정으로 로그인합니다.
2. 상단 검색창에서 **Subscriptions / 구독**을 열고 사용할 구독을 선택합니다.
3. **Overview / 개요**에서 구독 ID와 디렉터리(테넌트) ID를 기록합니다. 상태가 활성인지 확인합니다.
4. **Access control (IAM) → View my access / 내 액세스 보기**에서 **Owner**가 해당 구독 범위에 적용되는지 확인합니다. PIM의 적격 역할만 있다면 조직의 활성화 절차를 먼저 완료합니다.

**터미널 — 기록한 ID로 실행:**

```bash
az login --tenant "YOUR-TENANT-ID"
az account set --subscription "YOUR-SUBSCRIPTION-ID"
az account show --query "{subscription:name,subscriptionId:id,tenantId:tenantId,state:state}" --output json
```

브라우저 로그인과 MFA는 본인이 직접 완료합니다.

**완료 확인:** 출력의 `subscriptionId`, `tenantId`가 포털에서 기록한 값과 같고 `state`가 `Enabled`입니다. 구독이 안 보이면 새 구독을 만들지 말고 로그인 계정과 디렉터리를 먼저 확인합니다.

같은 구독의 **Resource providers / 리소스 공급자**에서 `Microsoft.CognitiveServices`를 검색합니다. 상태가 `Registered`가 아니라면 **Register / 등록**을 선택하고 완료될 때까지 기다립니다. 다른 공급자를 일괄 등록할 필요는 없습니다.

<a id="create-project"></a>
## 3. 전용 리소스 그룹과 Foundry 프로젝트 만들기

**할 일:** 마지막에 안전하게 정리할 수 있도록 실습 자원을 하나의 새 그룹에 모읍니다.

```text
내 Azure 구독
└─ 실습 전용 리소스 그룹
   └─ Foundry 리소스
      ├─ 프로젝트: eval-workshop       ← 평가 결과가 저장되는 곳
      └─ 모델 배포: eval-model         ← 답변 생성과 Judge에 함께 사용
```

**Azure 포털:**

1. **Resource groups / 리소스 그룹 → Create / 만들기**를 선택합니다.
2. 2단계에서 확인한 구독을 선택합니다.
3. 이름은 예를 들어 `rg-feval-a7k3m9`로 정합니다. `a7k3m9`는 본인만의 영문·숫자 조합으로 바꾸고 실제 이름을 실습지에 기록합니다. **이미 있는 그룹은 사용하지 않습니다.**
4. 지역은 조직에서 허용한다면 **East US 2**를 출발점으로 선택합니다. **Review + create → Create**로 만듭니다.

**Foundry 포털:**

1. [Microsoft Foundry](https://ai.azure.com)에 같은 계정으로 로그인합니다. **New Foundry** 전환이 보이면 켭니다.
2. 처음 화면의 **Create project**, 또는 왼쪽 위 프로젝트 선택 메뉴의 **Create new project**를 선택합니다.
3. 프로젝트 이름을 `eval-workshop`으로 입력하고 **Advanced options / 고급 옵션**을 엽니다.
4. **같은 구독, 방금 만든 리소스 그룹**을 선택합니다. 기존 공용 Foundry 리소스를 재사용하지 말고 **새 Foundry 리소스**를 만듭니다. 이름 입력란이 있으면 `feval-a7k3m9`처럼 본인 고유 이름을 쓰고, 자동 생성되는 화면이면 생성된 이름을 기록합니다.
5. Foundry 리소스의 지역도 확인한 뒤 **Create / 만들기**를 선택합니다.

East US 2는 배치 평가 지원 지역의 한 예이지 모델 쿼터를 보장하는 선택은 아닙니다. 지역을 바꾸어야 한다면 **평가 지원 + 사용할 모델의 배포 가능 여부 + 조직 정책**을 모두 확인합니다. 기존 리소스의 네트워크 제한을 실습 때문에 해제하지 않습니다.

**완료 확인:** 프로젝트가 열리고 **Manage → Project details / Resource details**에서 프로젝트와 상위 Foundry 리소스를 확인할 수 있습니다. Azure 포털의 전용 그룹에서도 해당 Foundry 리소스가 보이고 배포 상태가 `Succeeded`입니다.

**실습지에 기록:** 구독 ID, 리소스 그룹 이름, Foundry 리소스 이름, 프로젝트 이름, 선택한 지역. 자동 생성된 이름은 예시 이름이 아니라 실제 값을 기록합니다.

<a id="permissions"></a>
## 4. 본인과 프로젝트의 데이터 접근 권한 확인

**할 일:** “자원을 만들 수 있다”와 “모델을 호출하고 평가할 수 있다”를 구분합니다.

| 권한 | 대상 | 범위 |
|---|---|---|
| 이미 보유한 **Owner** | 본인 계정 | 구독 — 자원 생성·모델 배포·역할 할당 |
| **Foundry User** | 본인 계정 | 방금 만든 **Foundry 리소스** — 모델 호출·프로젝트 데이터 작업 |
| **Foundry User** | **프로젝트의 관리 ID** | 같은 **Foundry 리소스** — 서비스가 프로젝트 작업을 수행할 때의 접근 |

Owner가 Foundry 포털에서 프로젝트를 생성하면 두 Foundry User 할당이 자동으로 추가될 수 있습니다. **자동 할당을 가정하지 말고 확인하고, 없는 할당만 추가**합니다.

**Azure 포털 — 프로젝트가 아니라 상위 Foundry 리소스에서:**

1. 3단계에서 만든 Foundry 리소스를 열고 **Access control (IAM) → Role assignments**를 선택합니다.
2. 본인 계정과 프로젝트 관리 ID에 각각 **Foundry User**가 있는지 확인합니다. 이전 표시 이름인 **Azure AI User**일 수도 있습니다.
3. 본인 역할이 없다면 **Add → Add role assignment → Foundry User → User, group, or service principal**에서 본인을 선택하고 **Review + assign**을 완료합니다.
4. 프로젝트 관리 ID의 역할이 없다면 같은 역할을 선택하되 **Members → Managed identity**에서 `eval-workshop` 프로젝트의 ID를 선택합니다. **상위 Foundry 리소스 자체의 관리 ID와 혼동하지 않습니다.**

프로젝트의 관리 ID는 Azure 포털의 해당 프로젝트 **Identity / ID → System assigned**에서 확인합니다. 검색 결과가 모호하면 표시 이름 대신 **Object (principal) ID**를 비교합니다. ID가 목록에 안 나오면 [관리 ID 선택 문제](reference.md#managed-identity-access)만 확인한 뒤 이 단계로 돌아옵니다.

역할은 전용 **Foundry 리소스 범위**에만 추가합니다. 구독 전체에 Foundry User를 부여하거나 별도의 Entra 전역 관리자·앱 등록·비밀 키를 만들 필요가 없습니다.

**완료 확인:** 본인과 **프로젝트 관리 ID** 두 대상의 Foundry User 할당이 확인됩니다. 역할 전파에 시간이 걸릴 수 있으므로 바로 403이 나와도 역할을 중복 생성하지 않습니다.

<a id="deploy-model"></a>
## 5. 모델 하나 배포

**할 일:** 배포 이름을 `eval-model`로 정하고, 같은 배포를 답변 생성과 Judge에 사용합니다.

기본 시작 모델은 **`gpt-4.1-mini`**입니다. 짧은 규정 문답에 사용할 수 있고 Chat Completions와 JSON Schema 출력을 지원하는 모델을 선택해 준비를 단순하게 합니다. 최신 모델이나 최고 품질을 보장한다는 뜻은 아닙니다.

**Foundry 포털:**

1. **Discover → Models**에서 `gpt-4.1-mini`를 검색하고 모델 카드를 엽니다.
2. **Deploy → Custom settings**를 선택합니다.
3. 방금 만든 프로젝트와 Foundry 리소스를 선택하고 아래 값을 확인합니다.

| 설정 | 입력 / 확인 |
|---|---|
| Deployment name | **`eval-model`** |
| Model / version | `gpt-4.1-mini`와 포털에서 제공하는 사용 가능한 버전. 실제 버전을 기록 |
| Deployment type | 조직 정책이 허용하면 **Global Standard** |
| Tokens per minute | 남은 쿼터 안에서 설정. 한 명의 작은 실습은 예를 들어 **30K–60K TPM**을 출발점으로 사용 |

4. 가격·지역·쿼터를 확인하고 **Deploy**를 선택합니다.
5. **Build → Models**에서 `eval-model`의 상태가 **Succeeded**인지 확인합니다.

**Global Standard는 사용량 기반 배포입니다.** Provisioned/PTU나 Managed Compute/GPU 배포를 선택하지 않습니다. 또한 프로젝트의 지역을 골랐다는 사실이 Global Standard의 모든 추론 처리가 그 지역에만 머문다는 뜻은 아닙니다.

TPM은 비용 상한이 아니라 처리량 제한입니다. 위 숫자는 모든 실행에서 429가 없다는 보장이 아닙니다. 다른 사람이 사용하는 배포의 쿼터를 줄이지 말고, 부족하면 [모델·쿼터 문제 해결](reference.md#model-availability)을 따릅니다.

**완료 확인:** `eval-model` 하나가 준비되어 있고 모델 이름·버전·배포 유형을 기록했습니다. 모델 카탈로그 이름과 배포 이름은 다릅니다. 다음 단계에는 **`gpt-4.1-mini`가 아니라 `eval-model`**을 입력합니다.

같은 모델을 답변 생성과 Judge에 사용해도 호출은 분리됩니다. 다만 같은 편향을 공유할 수 있으므로, 이후 사람 검토를 생략하지 않습니다.

<a id="configure"></a>
## 6. 설정 세 값 저장

**할 일:** 포털의 실제 프로젝트 주소와 배포 이름을 코드에 연결합니다.

Foundry 프로젝트의 **Overview** 또는 **Manage → Project details**에서 **Project endpoint**를 복사합니다. 이름으로 추측해 주소를 만들지 않습니다.

편집기에서 [config.example.json](../config.example.json)을 열고 `lab.py` 옆의 **`config.json`으로 다른 이름 저장**합니다. 배포 이름 두 곳은 예제 파일에도 `eval-model`로 준비되어 있습니다.

```json
{
  "project_endpoint": "https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT",
  "model_deployment": "eval-model",
  "judge_deployment": "eval-model"
}
```

`project_endpoint`만 방금 복사한 실제 값으로 바꾸고 저장합니다. 배포를 다른 이름으로 만들었다면 나머지 두 값도 **같은 실제 배포 이름**으로 바꿉니다. 파일 이름이 `config.json.txt`가 아닌지 확인합니다. `.env`나 API 키는 사용하지 않습니다.

**터미널:**

```bash
python lab.py doctor --live
```

**완료 확인:** `model_deployment`와 `judge_deployment`의 **LIVE 조회 OK**가 보입니다. 모델 하나를 함께 쓰므로 같은 배포가 두 줄에 나오는 것이 정상입니다.

`doctor --live`는 로그인과 배포 조회만 확인합니다. **답변 생성과 평가까지 가능한지는 다음 단계에서 확인**합니다.

<a id="smoke"></a>
## 7. 답변 한 개를 실제 생성하고 평가

**할 일:** 전체 8개 평가를 시작하기 전에 작은 실제 요청으로 연결을 확인합니다. 이 단계부터 유료 호출이 발생할 수 있습니다.

기존의 추가 사례 예제 한 개를 연결 확인용으로 사용합니다. dev와 holdout 파일은 수정하지 않습니다.

```bash
python lab.py run --mode live --prompt v1 --data data/my-case.example.jsonl --out results/setup-smoke
python lab.py judge results/setup-smoke
python lab.py inspect results/setup-smoke N01
```

각 명령이 끝난 뒤 다음 명령을 실행합니다. `judge`가 진행 중이라면 같은 명령으로 같은 작업을 계속 조회합니다. 기본 조회 대기 시간이 끝났다는 것은 평가 실패나 실습 제한 시간이 끝났다는 뜻이 아닙니다.

**완료 확인 — 모두 충족해야 합니다:**

- `run`에서 **1/1 저장**, `inspect`에서 답변 JSON이 보이고 **`"schema": true`**입니다.
- `results/setup-smoke/judge.json`이 생성되고, Groundedness·Relevance **두 점수와 이유**가 모두 보입니다.
- Foundry 보고서 URL 또는 출력된 평가 ID로 같은 결과를 찾을 수 있습니다.

업무 판정이나 Judge 점수가 낮은 것과 연결 오류는 다릅니다. **낮은 점수는 기록하고 진행**합니다. 인증 오류·누락된 점수·잘린 JSON은 먼저 해결합니다. 이 한 건은 연결 확인용이며 본 실습의 20개 응답·Gate에는 포함되지 않습니다.

**준비 완료:** [메인 실습 0](../README.md#lab-0)으로 이동해 0–6을 순서대로 진행합니다. 끝나면 [리소스 정리](cleanup.md)까지 수행합니다. 더 이상 강사의 별도 환경 준비를 기다릴 필요가 없습니다.

<a id="existing-environment"></a>
## 이미 사용할 환경이 있다면

다시 만들지 않습니다. 환경 소유자에게 사용 허가와 **정리 범위**를 확인한 뒤 다음만 수행합니다.

1. [1–2단계](#tools): 코드·도구와 본인 로그인/구독 확인.
2. [4단계](#permissions): 본인과 프로젝트 관리 ID의 필요한 접근 권한 확인.
3. 기존 모델이 Chat Completions·Structured Outputs·선택한 Judge를 지원하는지 확인.
4. [6–7단계](#configure): 실제 endpoint/배포 이름을 저장하고 한 건의 생성·평가 완료.

기존 프로젝트·공유 리소스 그룹은 실습 후 일괄 삭제하지 않습니다. 이 문서의 새 전용 환경 경로와 섞지 않습니다.

<a id="cost"></a>
## 비용을 확인하는 방법

**호출 수의 기준:** 본 실습의 응답 20개와 평가 항목 40개에, 연결 확인 1개/2개와 직접 추가하는 사례 1개/2개가 더해집니다. 모두 수행하면 **응답 22개, 평가 항목 44개**입니다. 평가기 내부 호출·재시도·추론 토큰까지 포함한 청구 API 횟수라는 뜻은 아닙니다.

Azure 포털에서 본인 전용 리소스 그룹의 **Cost Management → Cost analysis**를 확인합니다. 사용한 모델의 [요금](https://azure.microsoft.com/pricing/details/azure-openai/)도 함께 봅니다.

필요하면 같은 범위의 **Budgets → Add**에서 본인이 감당할 예산과 알림을 설정합니다. **예산 알림은 자동 결제 차단이나 리소스 중지 장치가 아닙니다.** 비용 집계는 지연되며 새 구독에서는 Cost Management 준비에 시간이 걸릴 수 있습니다.

제공 데이터는 합성입니다. 실제 개인정보·기밀·비밀번호를 넣지 않습니다. `config.json`, 실습지와 `results/`는 로컬에 보관하고 공개 게시하지 않습니다.

<a id="resume"></a>
## 나중에 이어서 하기

같은 `foundry-evaluation-v1` 폴더와 `config.json`, `results/`를 사용합니다. 실습지의 **마지막 완료 단계 / 다음 명령**을 확인하고, 가상환경을 다시 활성화합니다.

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

로그인이 만료됐으면 [2단계](#sign-in)의 같은 계정·테넌트·구독으로 다시 로그인합니다. 완료된 결과를 다시 생성하지 말고 다음 미완료 명령부터 진행합니다. 같은 입력의 `run`은 저장된 응답을 재사용하고, `judge`는 저장된 원격 ID를 재사용합니다.

폴더 이름이나 위치를 바꾸면 `.venv`가 이전 경로를 참조할 수 있습니다. 그 경우 가상환경만 새 경로에서 복원하고 `config.json`과 `results/`는 보존합니다. 자세한 오류 복구는 [참고 문서](reference.md#resume)에 있습니다.

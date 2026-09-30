[English](en/setup.md) | **한국어**

# 공통 환경 준비

[전체 경로](../README.ko.md) · [준비 진행표](#setup-map) · [중단·재개](#resume) · [문제 해결](reference.md#troubleshooting)

**유료 경로의 공통 준비입니다.** [선택한 가이드](../README.ko.md#choose-path)에서 안내받았을 때 진행합니다. DEMO 참가자는 [DEMO 준비](offline.md#prepare)로 이동합니다.

아래에서 본인 상황 하나를 선택합니다. 완료한 단계는 반복하지 않습니다.

<a id="setup-options"></a>
## 내 상황에 맞는 준비 선택

| 지금 필요한 것 | 이동할 곳 |
|---|---|
| 설치·로그인·설정 중 특정 단계 찾기 | [공통 준비 1–7](#common-setup) |
| 허가받은 프로젝트와 모델이 이미 있음 | [기존 환경 준비](#existing-environment). 자원 생성 생략 |
| 포털 대신 CLI로 새 환경 만들기 | [CLI 대체 경로](#cli-provision). 아래 준비 3–5를 대체 |
| 중단한 실습 이어 하기 | [재개 절차](#resume) → [결과 파일별 재개 위치](#resume-checkpoints) |
| Azure 제약으로 LIVE를 진행할 수 없음 | [DEMO로 전환](#switch-to-demo) |
| 사용량·남은 리소스 비용 확인 | [비용 확인](#cost) |

<a id="common-setup"></a>
<a id="prepare"></a>
## 준비. 내 PC와 Azure 연결하기

> [!IMPORTANT]
> **준비 7을 마치면 원래 가이드로 돌아갑니다.** RAG 참가자는 [완결형 Search 준비](complete-lab.md#search-setup) 또는 [Optional RAG 준비](optional-rag.md#prerequisites)로 이동합니다. 입문 실습 전체를 수행할 필요는 없습니다.

**허가된 프로젝트·모델이 있다면 [기존 환경 준비](#existing-environment)로 이동합니다.** 아래는 새 환경을 만드는 절차입니다.

| 준비 항목 | 공통 준비에서 사용할 값 |
|---|---|
| 모델 / 배포 이름 | **`gpt-6-luna` / `eval-model`** — 답변 생성과 Judge가 같은 배포 사용 |
| 지역 | **Sweden Central (`swedencentral`)** |
| 새로 만들 것 | **전용 리소스 그룹 → Foundry 리소스 → 프로젝트·모델 배포 각 1개** |
| 계정·구독 | Microsoft Entra ID 계정(Azure에 로그인할 조직 계정) + 활성 Azure 구독. API 키 사용 안 함 |
| 신규 환경의 시작 권한 | 구독의 **활성 Owner 역할**. 적용되는 상속 역할 포함 |
| 종료 후 | **모든 리소스 보존** + [비용 확인](cleanup.md#retain-resources). 삭제는 별도 결정 |

Owner는 이 절에서 자원 생성과 역할 할당을 혼자 수행하기 위한 조건입니다. 기존 환경 사용자에게까지 요구하지 않습니다. 다른 역할 조합은 [작업별 권한](reference.md#permissions-contract)을 확인합니다.

이 단계에서는 아래 도구만 설치합니다. RAG의 Search·추가 모델은 원래 가이드에서 준비합니다. **개인정보·기밀·비밀번호는 입력하지 않습니다.**

**비용:** 모델·토큰 사용량에 따라 청구됩니다. 예산 알림과 TPM 설정은 자동 지출 차단이 아닙니다.

<a id="setup-map"></a>
### 준비 진행표

| 순서 | 실행할 곳 | 완료 신호 |
|---|---|---|
| [1. 코드·도구](#setup-tools) | 브라우저 → VS Code | `LOCAL OK` |
| [2. 로그인](#setup-sign-in) | Azure 포털 + 터미널 | 계정·구독·테넌트 일치 |
| [3. 프로젝트](#setup-project) | Azure 포털 + Foundry | 생성 상태 `Succeeded` |
| [4. 권한](#setup-permissions) | Azure 포털 IAM | 본인·프로젝트 ID의 Foundry User |
| [5. 모델](#setup-model) | Foundry | `eval-model` 배포 성공 |
| [6. 설정](#setup-config) | Foundry → VS Code | 두 항목 모두 `LIVE 조회 OK` |
| [7. 연결 확인](#setup-smoke) | 터미널 + Foundry | N01의 답변·두 점수·이유 |

<a id="tools"></a>
<a id="setup-tools"></a>
### 준비 1. 코드 받기와 도구 설치

**실행 위치: 웹 브라우저 → VS Code**

#### 폴더와 터미널 열기

1. [저장소](https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9)의 **Code → Download ZIP**으로 받아 압축을 풉니다. 이미 받았다면 생략합니다. 접근할 수 없으면 소유자에게 저장소 접근 권한이나 승인된 ZIP을 요청합니다.
2. 아래 도구를 설치합니다. 설치 후에는 새 터미널을 엽니다.
3. VS Code의 **File → Open Folder**에서 **`lab.py`와 `requirements.txt`가 바로 보이는 폴더**를 엽니다.
4. **Terminal → New Terminal**을 선택합니다. 이후 명령은 이 터미널에 입력합니다.

**내 PC의 VS Code 터미널을 사용합니다.** Azure 포털의 **Azure Cloud Shell**이나 노트북 셀이 아닙니다.

- **Windows:** PowerShell. 다른 셸이 열리면 터미널의 `+` 옆 화살표 → **Select Default Profile → PowerShell**을 선택하고 새 터미널을 엽니다.
- **macOS/Linux:** zsh 또는 bash.

**브라우저에서는 가이드를 읽고 Azure를 조작합니다. 파일 수정과 명령 실행은 VS Code에서 합니다.**

**`>>>`가 보이면** Python 대화창입니다. `exit()`로 나온 뒤 명령을 실행합니다. Python 파일의 실행 버튼은 사용하지 않습니다.

| 도구 | 설치 | 설치 확인 |
|---|---|---|
| Python 3.10 이상 | [Python 다운로드](https://www.python.org/downloads/). Windows에서는 PATH 추가 선택 | macOS/Linux: `python3 --version`, Windows: `py -3 --version` |
| Azure CLI | [운영체제별 설치](https://learn.microsoft.com/cli/azure/install-azure-cli) | `az version` |
| 편집기 | [VS Code 다운로드](https://code.visualstudio.com/) | 폴더와 터미널을 열 수 있음 |

<details>
<summary>VS Code에서 파일 열기·Markdown 미리보기·저장하기</summary>

1. **Ctrl+P / macOS Cmd+P**에 경로(예: `data/policies.md`)를 입력하고 Enter를 누릅니다. 검색되지 않으면 왼쪽 탐색기에서 파일을 엽니다.
2. `.md`는 **View → Command Palette → Markdown: Open Preview to the Side**로 읽습니다.
3. 수정은 **미리보기가 아니라 원본 텍스트 탭**에서 하고 **File → Save**로 저장합니다.

</details>

#### 가상환경 만들기

**아래 두 블록 중 본인 운영체제 것만 실행합니다.** `.venv`는 이 실습의 Python 패키지를 담는 전용 폴더입니다.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows — PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

<details>
<summary>Windows에서 Activate.ps1 실행이 차단될 때</summary>

조직 정책을 해제하지 않습니다. 이후 모든 `python`을 **`.\.venv\Scripts\python.exe`**로 바꿉니다. 예: `.\.venv\Scripts\python.exe lab.py doctor`. `az` 명령은 그대로 실행합니다.

</details>

#### 설치할 가상환경 확인하기

아래 명령으로 패키지 설치 위치를 확인합니다. Windows 활성화가 막혔다면 위 대체 방법을 먼저 적용합니다.

```bash
python -m pip --version
```

**완료 확인:** 출력의 `from` 뒤 경로가 **이번 실습 폴더의 `.venv` 안**입니다. 다른 경로라면 설치하지 말고 위 가상환경을 다시 활성화합니다.

#### 패키지 설치와 로컬 확인

```bash
python -m pip install -r requirements.txt
```

설치가 오류 없이 끝나면 로컬 파일을 확인합니다.

```bash
python lab.py doctor
```

**완료 확인:** `LOCAL OK: Python ... , dev 8개, holdout 4개`.

`LOCAL OK`는 로컬 파일 확인입니다. **Azure 연결은 준비 6–7에서 확인합니다.**

<details>
<summary>새 터미널이나 폴더 변경 후 다시 시작할 때</summary>

이 폴더로 돌아와 macOS/Linux의 `source .venv/bin/activate` 또는 PowerShell의 `.\.venv\Scripts\Activate.ps1`만 다시 실행합니다. 활성화가 막히면 가상환경 Python 직접 실행 방식을 유지합니다. 가상환경 생성이나 패키지 설치부터 반복하지 않습니다.

**폴더를 옮기거나 이름을 바꾼 뒤 가상환경이 실행되지 않을 때만** [가상환경 복구](reference.md#moved-folder)를 따릅니다. 기존 결과·설정·직접 수정한 파일은 유지합니다.

</details>

<a id="working-files"></a>
**공통 준비에서 편집할 파일은 `config.json` 하나입니다.** 준비 6에서 `config.example.json`을 복사해 `lab.py` 옆에 저장합니다. 아직 만들거나 편집하지 않아도 됩니다.

이후 파일은 [입문 작업 파일 표](intro-lab.md#working-files) 또는 본인의 RAG 가이드에서 안내합니다. **기존 작업을 덮어쓰지 않습니다.** 결과 폴더·보고서는 자동 생성되므로 직접 수정하지 않습니다. 작업 파일은 **UTF-8**로 저장합니다.

**다음:** [준비 2. 로그인](#setup-sign-in) · [준비 진행표](#setup-map)

<a id="sign-in"></a>
<a id="setup-sign-in"></a>
### 준비 2. 사용할 구독으로 로그인

**실행 위치: [Azure 포털](https://portal.azure.com)**

1. Entra ID 계정으로 로그인한 뒤 **Subscriptions / 구독**에서 사용할 구독을 엽니다.
2. **Overview / 개요**의 **구독 ID와 디렉터리(테넌트) ID**를 확인합니다. 바로 아래 로그인 명령에 이 값을 사용합니다.
3. **Access control (IAM) → View my access**에서 구독 범위의 **Owner**가 활성인지 확인합니다. PIM에서 “적격”으로만 보이면 아직 활성 권한이 아닙니다. 조직 절차로 활성화합니다.
4. 같은 구독의 **Resource providers / 리소스 공급자**에서 `Microsoft.CognitiveServices`를 확인합니다. 미등록이면 **Register**를 선택하고 `Registered`까지 기다립니다.

**실행 위치: VS Code 터미널.** `YOUR-...`는 문자 그대로 입력하는 값이 아닙니다. 확인한 실제 ID로 바꾸되 따옴표는 유지합니다.

```bash
az login --tenant "YOUR-TENANT-ID"
```

브라우저 로그인과 MFA를 직접 완료한 뒤 다음 명령을 각각 실행합니다.

```bash
az account set --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az account show --query "{account:user.name,subscription:name,subscriptionId:id,tenantId:tenantId,state:state}" --output json
```

**완료 확인:** 아래 세 가지가 모두 맞습니다.

- `account`는 이번 실습에 사용할 본인 계정입니다.
- 구독 ID·테넌트 ID는 포털과 터미널에서 같습니다. **구독 이름만으로 판단하지 않습니다.**
- `state`는 `Enabled`입니다.

구독이 안 보이면 로그인한 테넌트를 확인합니다. **브라우저와 CLI는 각각 로그인합니다.** Foundry에서 계정을 다시 물으면 위 `account`와 같은 계정을 선택합니다.

**다음:** [준비 3. 프로젝트](#setup-project) · [준비 진행표](#setup-map)

<a id="create-project"></a>
<a id="setup-project"></a>
### 준비 3. 본인 전용 그룹과 Foundry 프로젝트 만들기

이름이 비슷하므로 먼저 구분합니다.

| 만들 것 | 역할 | 사용할 이름 |
|---|---|---|
| 리소스 그룹 | 이번 실습 자원을 모아 두는 정리·삭제 단위 | `rg-feval-a7k3m9`처럼 고유하게 지정 |
| Foundry 리소스 | 모델 배포와 접근 권한을 관리하는 상위 자원 | `feval-a7k3m9`처럼 고유하게 지정 |
| Foundry 프로젝트 | 평가 실행과 결과를 보관하는 작업 공간 | `eval-workshop` |
| 모델 배포 | 코드에서 호출할 모델의 이름. 준비 5에서 생성 | `eval-model` |

`a7k3m9`는 예시입니다. 본인 고유 영문·숫자로 바꾸고, 이후 단계에는 **화면에 실제로 만들어진 이름**을 사용합니다.

#### Azure 포털에서 전용 그룹 만들기

1. **Resource groups → Create**에서 준비 2의 구독을 선택합니다.
2. 위 표처럼 **새 전용 그룹** 이름을 입력하고 지역은 **Sweden Central (`swedencentral`)**을 선택합니다.
3. **Review + create → Create**를 선택하고 완료를 기다립니다.

#### Microsoft Foundry에서 프로젝트 만들기

[Microsoft Foundry](https://ai.azure.com)를 엽니다.

1. 같은 계정으로 로그인합니다. **New Foundry** 전환이 보이면 켭니다.
2. **Create project**, 또는 왼쪽 위 프로젝트 이름 → **Create new project**를 선택합니다.
3. 프로젝트 이름에 **`eval-workshop`**을 넣고 **Advanced options**를 엽니다.
4. **같은 구독·방금 만든 전용 그룹·Sweden Central (`swedencentral`)**을 선택합니다. 공유 자원이 아니라 **새 Foundry 리소스**를 사용하고, 이름 입력란이 있으면 위 표처럼 지정합니다.
5. **Create**를 선택하고 프로젝트가 열릴 때까지 기다립니다.

**Hub / 허브를 먼저 만들라는 화면이면 진행하지 않습니다.** 이 실습은 Foundry 리소스 아래의 새 **Foundry 프로젝트**를 사용하며, classic의 허브 기반 프로젝트와는 설정·SDK가 다릅니다. New Foundry 화면과 선택한 프로젝트 유형을 다시 확인합니다.

**완료 확인:** **Manage → Project details / Resource details**에서 프로젝트와 상위 Foundry 리소스를 확인할 수 있고, Azure 포털의 전용 그룹에서도 배포 상태가 `Succeeded`입니다. 그룹·리소스·프로젝트 이름과 실제 지역을 대조합니다.

**그룹·Foundry 리소스·프로젝트의 지역을 각각 확인합니다.** 모델 용량이나 조직 정책으로 막히면 [가용성 도움말](reference.md#model-availability)을 봅니다. 지역을 임의 변경하거나 방화벽을 해제하지 않습니다.

포털 대신 명령으로 준비하려면 [Azure CLI 신규 환경 경로](#cli-provision)를 사용합니다. **준비 3–5의 대체 경로**이며 두 경로로 자원을 중복 생성하지 않습니다.

**다음:** [준비 4. 권한](#setup-permissions) · [준비 진행표](#setup-map)

<a id="permissions"></a>
<a id="setup-permissions"></a>
### 준비 4. 모델 호출과 평가 권한 확인

**Owner만 있다고 모델 호출과 평가까지 되는 것은 아닙니다.** 내 터미널은 **본인 계정**, 클라우드 평가 작업은 **프로젝트 관리 ID**의 권한을 사용합니다. 관리 ID는 프로젝트가 Azure 서비스에 접근할 때 사용하는 신원입니다.

아래 권한은 **본인 전용 환경**의 시작 구성입니다. 하위 프로젝트에도 상속됩니다. 공유 환경은 소유자와 [필요한 범위](reference.md#permissions-contract)를 확인하며 임의로 넓히지 않습니다.

#### 프로젝트에서 관리 ID 확인하기

**프로젝트에서 ID 확인 → 상위 리소스에서 역할 확인** 순서입니다. 두 대상을 구분합니다.

1. Foundry의 **Manage → Project details**에서 프로젝트의 Azure 리소스를 엽니다. ID 끝이 **`/accounts/실제리소스이름/projects/실제프로젝트이름`**인지 확인합니다. 새 프로젝트 이름은 `eval-workshop`입니다.
2. 그 프로젝트의 **Identity → System assigned → Object (principal) ID**를 확인해 아래 IAM 대상과 대조합니다. 상위 Foundry 리소스의 관리 ID를 복사하지 않습니다. 메뉴나 ID가 없으면 [관리 ID 선택 도움말](reference.md#managed-identity-access)을 봅니다.

**아래는 설명용 그림이며 실제 포털 캡처가 아닙니다.** 그림의 가상 값 대신 본인 화면의 이름·ID를 사용합니다.

![프로젝트 화면의 Object (principal) ID를 상위 Foundry 리소스 IAM의 프로젝트 관리 ID와 대조하고, 같은 리소스 범위에서 본인과 프로젝트에 각각 Foundry User가 있는지 확인하는 그림](images/foundry-permissions.svg)

#### 상위 Foundry 리소스에서 역할 확인하기

**Azure 포털 → 상위 Foundry 리소스 → Access control (IAM)**을 엽니다. 이 화면의 리소스 ID는 **`/accounts/실제리소스이름`**으로 끝나며 `/projects/...`가 붙지 않습니다.

| 역할 | 누구에게 | 어느 범위에 |
|---|---|---|
| **Foundry User** | 본인 계정 | 상위 **Foundry 리소스** |
| **Foundry User** | **위에서 확인한 프로젝트의 관리 ID**. 기본 경로는 `eval-workshop` | 같은 **Foundry 리소스** |

1. **Role assignments**에서 두 대상의 역할을 확인합니다. 이전 이름인 **Azure AI User**로 보일 수도 있습니다. 자동으로 할당됐다면 추가하지 않습니다.
2. 본인에게 없다면 **Add → Add role assignment → Foundry User → User, group, or service principal**에서 본인을 선택하고 **Review + assign**합니다.
3. 프로젝트 관리 ID에 없다면 같은 역할의 **Members → Managed identity**에서 위에서 확인한 프로젝트를 선택합니다. 대상 상세의 **Object ID가 앞서 확인한 프로젝트의 ID와 같은지 확인한 뒤** 할당합니다. 이름만 같은 다른 대상을 선택하지 않습니다.

**완료 확인:** 본인과 프로젝트 ID 모두 **Foundry 리소스 범위**의 Foundry User가 있습니다. 찾지 못하면 [관리 ID 도움말](reference.md#managed-identity-access)을 봅니다. 구독 전체 할당이나 중복 할당으로 해결하지 않습니다.

**다음:** [준비 5. 모델](#setup-model) · [준비 진행표](#setup-map)

<a id="deploy-model"></a>
<a id="setup-model"></a>
### 준비 5. 모델 하나 배포

**실행 위치: Foundry → Discover → Models**

1. **`gpt-6-luna`**를 검색해 엽니다. 정확한 모델명과 제공되는 버전을 확인합니다. 비슷한 이름의 다른 모델을 대신 선택하지 않습니다.
2. **Deploy → Custom settings**에서 방금 만든 프로젝트·리소스를 선택합니다.
3. 아래 값을 확인한 뒤 **Deploy**를 선택합니다.

| 설정 | 입력·선택할 값 |
|---|---|
| Deployment name | **`eval-model`** |
| Model / version | **`gpt-6-luna`** / 해당 지역에서 제공되는 버전. 실제 선택한 버전을 기록 |
| Resource location | **Sweden Central (`swedencentral`)** |
| Deployment type | 모델이 지원하고 남은 쿼터가 있으며 조직이 허용하면 **Global Standard** |
| Tokens per minute (TPM, 분당 토큰 한도) | 해당 모델·배포 유형의 남은 쿼터 안에서, 선택 가능하면 **30K–60K TPM**으로 시작 |

**완결형 RAG 참가자는 버전 `2026-09-22`가 필요합니다.** 기록된 V1 비교의 [고정 버전 조건](complete-lab.md#setup)을 확인하고, 제공되지 않으면 Search·추가 모델을 만들기 전에 경로를 다시 선택합니다. 위의 “제공되는 버전” 선택은 별도 입문 경로에 해당합니다.

**Provisioned/PTU·GPU 배포는 선택하지 않습니다.** Global Standard는 사용량 기반이며 스웨덴 내 처리만 보장하지는 않습니다. 모델·쿼터가 없으면 [도움말](reference.md#model-availability)을 따릅니다. 모델·지역을 임의 변경하거나 다른 배포의 쿼터를 줄이지 않습니다.

**완료 확인:** **Build → Models**에서 **`eval-model`**이 `Succeeded`이고 연결된 모델이 **`gpt-6-luna`**입니다. 모델 이름·버전·배포 유형을 기록합니다. **모델 이름 `gpt-6-luna`와 배포 이름 `eval-model`을 혼동하지 않습니다.**

이 배포 하나로 답변 생성과 AI 채점을 각각 호출합니다. 배포 성공만으로 실행을 보장하지 않습니다. [준비 7](#setup-smoke)에서 JSON 답변 생성과 클라우드 채점을 확인합니다.

**다음:** [준비 6. 설정 파일](#setup-config) · [준비 진행표](#setup-map)

<a id="configure"></a>
<a id="setup-config"></a>
### 준비 6. 설정 파일에 프로젝트 주소 넣기

**실행 위치: Foundry → VS Code**

1. 프로젝트의 **Overview** 또는 **Manage → Project details**에서 **Project endpoint**를 복사합니다. 이름으로 주소를 추측하거나 API 키를 복사하지 않습니다.
2. VS Code에서 [config.example.json](../config.example.json)을 엽니다. **File → Save As**로 **`lab.py` 옆에 `config.json`**을 만듭니다.
3. 아래 `project_endpoint`의 예시 주소를 복사한 실제 주소로 바꾸고 저장합니다.

**JSON 편집 요령**

- 왼쪽 항목 이름은 두고, 안내한 **오른쪽 값만** 바꿉니다.
- 큰따옴표 `"`·쉼표·중괄호를 유지합니다. 마지막 항목 뒤에는 쉼표를 넣지 않습니다.
- 복사할 때는 **`{`부터 `}`까지만** 넣습니다. 설명문이나 코드 블록 테두리는 제외합니다.

```json
{
  "project_endpoint": "https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT",
  "model_deployment": "eval-model",
  "judge_deployment": "eval-model"
}
```

**기본 경로에서는 주소 하나만 수정합니다.** 저장 전에 아래를 확인합니다.

| 확인할 값 | 올바른 입력 | 넣으면 안 되는 값 |
|---|---|---|
| `project_endpoint` | `.services.ai.azure.com/api/projects/실제프로젝트이름`이 포함된 주소 | 포털 브라우저 주소, 프로젝트 경로가 없는 리소스 주소, `.openai.azure.com` 주소 |
| 두 배포 항목 | 둘 다 **`eval-model`**. 다른 이름으로 배포했다면 실제 배포 이름 | 모델 이름 `gpt-6-luna` |
| 파일 이름·위치 | **`lab.py` 옆 `config.json`** | `config.json.txt` |

`.env`는 필요 없습니다.

```bash
python lab.py doctor --live
```

**완료 확인:** `model_deployment`와 `judge_deployment`에 각각 **`LIVE 조회 OK`**가 나오고 모델 이름이 **`gpt-6-luna`**인지 확인합니다. 같은 `eval-model`이 두 번 나오는 것이 정상입니다. 이는 조회 확인이며, 실제 생성·평가는 다음 단계에서 확인합니다.

**다음:** [준비 7. 연결 확인](#setup-smoke) · [명령 상태 읽기](#command-status) · [준비 진행표](#setup-map)

<a id="command-status"></a>
### 명령 결과를 보고 다음 행동 고르기

**완료 메시지 → 건수 → 보고서** 순서로 확인합니다.

- `ERROR:`가 나오면 멈추고 원인을 해결합니다.
- `아직 처리 중입니다`가 나오면 **같은 명령 전체**를 다시 실행합니다. `--like`도 유지합니다.
- `FAIL`·낮은 점수는 답변의 품질 결과입니다. 오류와 구분합니다.
- `BLOCK`은 최종 기준 미달입니다. 보고서에서 품질 실패와 검토 누락을 구분합니다.

<details>
<summary>출력별 다음 행동 — 완료·대기·오류·BLOCK·재개</summary>

| 보이는 결과 | 뜻 | 다음 행동 |
|---|---|---|
| `평가 완료: …개 답변 × 2개 지표 (점수·이유 저장)` | 모든 사례의 두 점수·이유를 확인하고 로컬에 저장함 | 건수가 해당 단계와 같은지 확인하고 진행. **답변 합격을 뜻하지는 않음** |
| `기존의 완료된 결과를 읽었습니다` | 같은 입력의 저장된 답변을 재사용함. `8/8 … 저장` 같은 새 수집 메시지는 나오지 않음 | 요약의 건수와 `report.md`를 확인하고 다음 미완료 단계로 이동. 파일을 지워 다시 생성하지 않음 |
| `D04 FAIL` 또는 낮은 점수 | 답변을 수집·평가했지만 답이 기준에 못 미침 | 원인을 기록하고 진행. 좋은 점수가 나올 때까지 다시 뽑지 않음 |
| `Judge: 아직 미평가` | 답변만 있고 AI 채점 전 | 해당 단계의 `judge` 실행 |
| `Foundry 상태: completed`만 보임 | 원격 작업 종료. 로컬 결과 수집·검사가 남을 수 있음 | 터미널의 **`평가 완료`까지** 기다림. 이후 `ERROR:`가 나오면 문제 해결 |
| `아직 처리 중입니다` / 종료 코드 `3` | 클라우드 평가가 아직 끝나지 않음 | **방금 실행한 `judge` 명령 전체를 그대로 재실행**. `--like`도 유지 |
| `중단했습니다` / 종료 코드 `130` | 터미널에서 실행을 중단함 | 파일을 보존하고 [재개 표](#resume-checkpoints) 확인 |
| `ERROR:` / 종료 코드 `1` | 입력·환경·실행 오류 | 다음 단계로 가지 말고 [문제 해결](reference.md#troubleshooting) |
| `BLOCK` / 종료 코드 `2` | 최종 품질 기준에 따라 변경을 보류 | `gate.md`의 이유를 기록하고 실습 6으로 진행. 단, 점수·검토 누락은 먼저 보완 |
| `usage:` / `error:`와 함께 종료 코드 `2` | 필수 인자 누락·잘못된 옵션 등 명령 인자 오류 | 명령을 고쳐 재실행. `BLOCK`과 구분 |

`judge`의 기본 **상태 조회 대기 예산은 300초**입니다. 인증·제출·HTTP 응답·결과 수집 때문에 전체 명령은 더 걸릴 수 있습니다. `아직 처리 중입니다`로 끝나면 같은 명령을 재실행합니다. **저장된 원격 작업을 조회**하며 새 평가를 제출하지 않습니다. 새 터미널에서 동시에 실행하지 않습니다.

**오류 원인을 해결한 뒤 [재개 표](#resume-checkpoints)를 따릅니다.**

- 미완료 `run`: 같은 입력·`--out`으로 실행하면 저장한 답변은 건너뜁니다. 저장 전에 끊긴 응답은 재호출 비용이 들 수 있습니다.
- ID가 저장된 `judge`: 원격 작업이 처리 중이거나 `completed`라면 조회·수집을 재개합니다.
- ID 저장 전 중단 또는 원격 `failed`/`canceled`: 재제출 전에 [원격 ID 복구](reference.md#resume)를 확인합니다.

`평가 완료`는 점수·이유 검증과 파일 저장까지 끝났다는 뜻입니다. **완료 건수 → `report.md` → `사례별 근거`**를 읽고 진행합니다. 완료된 명령을 반복해도 저장 결과를 재사용합니다.

</details>

<a id="smoke"></a>
<a id="setup-smoke"></a>
### 준비 7. 답변 한 개로 연결 확인

**실행 위치: VS Code 터미널. 여기부터 유료 생성·평가 호출이 발생합니다.**

#### 답변 한 개 생성하기

```bash
python lab.py run --mode live --prompt v1 --data data/my-case.example.jsonl --out results/setup-smoke
```

**완료 확인:** `1/1  N01 저장`.

#### 저장한 답변 채점하기

`run`은 답변을 만들고, `judge`는 **그 답변을 그대로 채점**합니다.

```bash
python lab.py judge results/setup-smoke
```

**완료 확인:** `평가 완료: 1개 답변 × 2개 지표`.

`아직 처리 중입니다`로 끝나면 위 `judge`를 그대로 재실행합니다. 오류·중단은 [명령 상태와 재개 안내](#command-status)를 따릅니다.

#### 답변·점수·이유 확인하기

```bash
python lab.py inspect results/setup-smoke N01
```

**완료 확인:** 아래 세 가지를 확인합니다.

1. 업무 검사에 `"schema": true`가 있습니다.
2. `groundedness`와 `relevance`에 각각 **1–5점과 이유**가 있습니다.
3. 출력된 **Foundry 보고서 URL**에서 같은 질문·답변·점수를 확인합니다. URL이 없으면 프로젝트의 **Evaluation / 평가**에서 `results/setup-smoke/foundry-job.json`의 `eval_id`·`run_id`로 찾습니다.

점수가 낮아도 연결이 확인됐으면 진행합니다. 인증 오류·잘린 답변·누락된 점수는 먼저 해결합니다. 이 `N01`은 연결 확인용이며 본 실습의 질문에는 포함되지 않습니다.

**Judge가 5점이어도 `citations`는 FAIL일 수 있습니다.** 불필요한 출처를 넣으면 코드 검사는 실패합니다. 형식과 두 점수·이유가 유효하면 연결 확인은 완료입니다.

**준비 끝. 아래에서 본인 경로 하나만 선택해 돌아갑니다.** RAG 참가자는 입문 실습 1로 가지 않습니다.

| 선택한 경로 | 지금 이어갈 곳 |
|---|---|
| 입문 LIVE | [1. 평가 기준](intro-lab.md#lab-1) |
| 완결형 RAG | [공통 준비 후 값 확인과 Search 준비](complete-lab.md#search-setup) |
| Optional RAG | [Optional RAG 준비 확인](optional-rag.md#prerequisites) |

**준비 중 막혔다면:** [준비 진행표](#setup-map) · [상태 읽기](#command-status) · [재개](#resume)

---

<a id="cli-provision"></a>
## 선택: Azure CLI로 신규 환경 준비

**준비 1–2 후 포털 준비 3–5를 대신하는 절차**입니다. Azure CLI **2.80.0 이상**과 생성·역할 할당 권한이 필요합니다. [공식 생성 안내](https://learn.microsoft.com/azure/foundry/how-to/create-projects)를 따릅니다. 이미 프로젝트·모델이 있으면 실행하지 않습니다.

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

**`--assign-identity`와 `--allow-project-management true`를 생략하지 않습니다.** 관리 ID·프로젝트 관리에 필요합니다. Custom domain은 전역 고유 이름이어야 합니다. `retain=true`는 보존 표시일 뿐 삭제·과금 차단이 아닙니다.

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

**완료 확인:** 두 자원 모두 지역 `swedencentral`, 상태 `Succeeded`입니다. 조회 값을 다음과 같이 사용합니다.

| 조회 결과 | 사용할 곳 |
|---|---|
| 상위 리소스의 `id` | `YOUR-FOUNDRY-RESOURCE-ID` |
| 프로젝트의 `principalId` | `YOUR-PROJECT-PRINCIPAL-ID` |
| 프로젝트 `endpoints`의 **AI Foundry API** | 준비 6의 `config.json`. 주소를 추측해 만들지 않음 |

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

두 역할은 **Foundry User**, 범위는 `/accounts/실제이름`까지이며 하위 프로젝트에 상속됩니다. 본인은 `User`, **프로젝트** 관리 ID는 `ServicePrincipal`입니다. 계정 관리 ID와 혼동하거나 구독·공유 환경으로 범위를 넓히지 않습니다.

### 4. 모델·쿼터 확인 후 한 개 배포

```bash
az cognitiveservices model list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?model.name=='gpt-6-luna']" --output json
```

```bash
az cognitiveservices usage list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?name.value=='OpenAI.GlobalStandard.gpt-6-luna'].{name:name.value,current:currentValue,limit:limit}" --output json
```

모델·버전·`GlobalStandard` 지원과 용량 단위를 확인합니다. 아래 명령은 **60K TPM / capacity 60** 예시입니다. 현재 모델/SKU도 **capacity 1 = 1000 TPM**이고 **`limit - current`가 60 이상**일 때만 사용합니다. 다른 모델의 단위를 추정하지 않습니다.

쿼터 조회에는 구독 범위의 조회 권한이 따로 필요합니다. 403이나 빈 목록을 “쿼터 0”으로 단정하지 말고 [권한·가용성 도움말](reference.md#model-availability)에서 계정·권한·제공 여부를 확인합니다. 남은 쿼터가 있어도 지역의 실제 배포 용량까지 보장하지는 않습니다.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name eval-model --model-name gpt-6-luna --model-version "YOUR-MODEL-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

`YOUR-MODEL-VERSION`에는 **조회한 실제 버전**을 넣습니다. 2026-09-27 실습에서는 `2026-09-22`를 사용했으며 이 값을 현재도 제공한다고 가정하지 않습니다. 완료 후 [준비 6](#setup-config)으로 돌아가 설정·조회·한 건 생성·평가를 진행합니다. API 키를 조회하거나 저장할 필요는 없습니다. **마지막에 삭제 명령을 실행하지 않습니다.**

완결형 RAG는 기록된 V1 비교를 위해 [지정 답변 버전](complete-lab.md#setup)이 필수입니다. 다른 제공 버전을 사용할 수 있는 입문 경로와 구분합니다.

</details>

<a id="existing-environment"></a>
## 이미 허가받은 환경이 있다면

새 자원을 만들거나 기존 모델의 이름·설정을 바꾸지 않습니다. 입문 참가자는 아직 하지 않았다면 [실습 0](intro-lab.md#lab-0)의 A/B 판단만 먼저 한 뒤 이 절로 돌아옵니다.

**사용 조건:** 새 포털의 Foundry 프로젝트와 접근 가능한 모델 배포입니다. 주소는 `https://리소스이름.services.ai.azure.com/api/projects/프로젝트이름` 형태입니다. Classic 허브 연결 문자열이나 모델 주소는 대신 쓸 수 없습니다.

기존 환경도 이 실습의 **`gpt-6-luna`·`swedencentral` 조건**을 확인합니다. 실제 배포 이름이 달라도 되지만 모델·지역을 바꾼 실험으로 조용히 대체하지 않습니다. 모델명·배포명·모델 버전·API 버전은 [서로 다른 값](reference.md#model-endpoint-contract)입니다.

**RAG 참가자는 5번 대신 원래 가이드로 돌아갑니다:** [완결형 Search 준비](complete-lab.md#search-setup) / [Optional RAG 준비](optional-rag.md#prerequisites). 완결형의 지정 배포 이름·버전을 맞추려고 공유 배포를 변경하지 않습니다.

1. 환경 소유자에게 아래 정보를 확인해 다음 단계의 로그인·설정에 사용합니다. API 키나 공유 비밀번호를 받지 않습니다.
2. [준비 1](#setup-tools)에서 로컬 도구를 준비하고, [준비 2](#setup-sign-in)의 **로그인과 구독 확인**을 수행합니다. 자원을 만들지 않으므로 Owner 취득이나 공급자 등록은 요구하지 않습니다.
3. [준비 4](#setup-permissions)와 [기존 환경의 권한 범위](reference.md#permissions-contract)를 대조합니다. 부족한 역할은 할당 권한이 있는 소유자에게 요청하며 공유 계정 전체에 임의로 추가하지 않습니다.
4. 기존 배포가 **Chat Completions·Structured Outputs·Judge 평가**를 지원하는지 확인합니다. [준비 6](#setup-config)의 설정에 실제 주소와 배포 이름을 넣고 [준비 7](#setup-smoke)을 완료합니다.
5. [실습 1](intro-lab.md#lab-1)로 이어갑니다. 마지막에는 소유자와 합의한 본인 작업만 정리합니다. **공유 프로젝트·모델·리소스 그룹은 일괄 삭제하지 않습니다.**

| 소유자에게 확인할 정보 | 사용할 곳 |
|---|---|
| 테넌트 ID·구독 ID | 포털과 CLI를 같은 계정·구독에 연결 |
| 리소스 그룹·Foundry 리소스·프로젝트 이름, 지역 | 준비 4의 대상 구분과 마지막 정리 범위 확인 |
| Project endpoint·실제 모델 배포 이름 | `config.json`. 모델 이름이 아니라 배포 이름을 사용 |
| 본인·프로젝트 관리 ID의 실제 역할과 범위, 사용·비용·정리 허용 범위 | 호출·평가 권한 및 공유 환경 보호 |

ID를 조회할 수 없으면 소유자에게 준비 4의 확인을 요청합니다. **기존 자원 이름은 바꾸지 않습니다.** 같은 배포를 쓰면 `config.json`의 `model_deployment`·`judge_deployment`에 모두 실제 배포 이름을 넣습니다.

<a id="switch-to-demo"></a>
## LIVE가 막혀 DEMO로 전환할 때

1. 새 LIVE 호출을 멈추고 **중단한 단계·오류·이미 만든 Azure 자원**을 확인합니다. 기존 결과·설정·작성한 질문을 지우지 않습니다.
2. [DEMO 가이드의 준비](offline.md#prepare)로 이동합니다. 설치한 Python·VS Code·가상환경을 재사용하고 기존 LIVE 기록은 보존합니다.
3. DEMO 가이드의 `results/demo-*` 폴더만 사용해 실습 1–6을 진행합니다. LIVE 명령의 모드만 바꾸거나 LIVE 점수와 DEMO 점수를 비교하지 않습니다.
4. LIVE에서 만든 자원이 있다면 DEMO가 끝나도 [보존 상태와 비용](cleanup.md#retain-resources)을 확인합니다. DEMO 전환을 이유로 리소스를 자동 삭제하지 않습니다. 이미 제출한 원격 평가는 터미널을 닫거나 DEMO로 전환해도 자동 취소되지 않습니다.

<a id="cost"></a>
## 비용 확인

호출 규모는 [입문 LIVE](intro-lab.md#prepare) 또는 선택한 RAG 가이드에서 확인합니다. [모델 요금](https://azure.microsoft.com/pricing/details/azure-openai/)과 본인 배포 유형을 대조합니다. 생성 토큰 합계만으로 Judge 비용까지 계산하지 않습니다.

Azure 포털의 **Cost Management → Cost analysis**에서 해당 전용 그룹으로 범위를 좁혀 봅니다. 비용 반영은 늦을 수 있고, 예산 알림은 자동 지출 차단이 아닙니다. 끝나거나 중도 중단하면 [리소스 보존·정리](cleanup.md)를 확인합니다. 기본은 보존이며, 보존을 과금 중지로 해석하지 않습니다.

<a id="resume"></a>
## 나중에 이어서 하기

아래 재개 표는 **`lab.py` 입문 LIVE/DEMO용**입니다. `advanced_lab.py`는 파일 구조와 출력 경로가 다르므로 [완결형 상태·재개 표](complete-lab.md#resume)를 사용합니다.

1. VS Code에서 이전의 **`lab.py`가 있는 폴더**를 열고 새 터미널을 엽니다.
2. 가상환경만 다시 활성화합니다. macOS/Linux는 `source .venv/bin/activate`, Windows는 `.\.venv\Scripts\Activate.ps1`입니다. 활성화가 막혔던 Windows 환경에서는 계속 `.\.venv\Scripts\python.exe`를 사용합니다. 패키지를 매번 재설치하지 않습니다.
3. 아래 [결과 파일별 재개 표](#resume-checkpoints)에서 **마지막 완료 단계와 다음 명령**을 찾습니다. LIVE 로그인이 만료됐으면 [로그인](#setup-sign-in)만 다시 합니다. DEMO는 로그인하지 않습니다.

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

**VS Code에서 `results/`를 확인합니다.** 아래 폴더는 LIVE용입니다. DEMO는 `demo-baseline`·`demo-candidate`·`demo-holdout`을 봅니다. 준비 중이었다면 [준비 진행표](#setup-map)로 돌아갑니다.

| 저장된 상태 / 아직 없는 것 | LIVE에서 이어갈 위치 | DEMO에서 이어갈 위치 |
|---|---|---|
| `baseline/run.json`의 `status`가 `complete`, `judge.json`은 없음 | [실습 3](intro-lab.md#lab-3): D04 사람 판단부터, 그 뒤 Judge | [실습 3](offline.md#lab-3): 동일 순서 |
| `baseline/judge.json`은 있음, candidate는 아직 없음 | [실습 4](intro-lab.md#lab-4): 가설·기존 작업본 확인부터 | [실습 4](offline.md#lab-4): 가설·V2 예제부터 |
| `candidate/run.json`은 완료, `judge.json` 또는 `comparison.md`가 없음 | [실습 4](intro-lab.md#lab-4): 후보 Judge → 비교 중 빠진 단계 | [실습 4](offline.md#lab-4): 동일 순서 |
| 후보 비교는 완료, D06의 `reviews.json` 기록이 없음 | [실습 4](intro-lab.md#lab-4)의 `review` | [실습 4](offline.md#lab-4)의 `review` |
| 후보 검토는 완료, holdout 생성·Judge·H04 검토 또는 Gate가 남음 | [실습 5](intro-lab.md#lab-5)의 첫 미완료 단계 | [실습 5](offline.md#lab-5)의 첫 미완료 단계 |
| `candidate/gate.md`와 판단 기록까지 있음 | [실습 6](intro-lab.md#lab-6): 추가 질문·보고 | [실습 6](offline.md#lab-6): 질문 검사·보고 |

파일이 있어도 완료 상태를 확인합니다. **`collecting`은 같은 `run`, 평가 대기는 같은 `judge`로 재개**합니다. `judge.json`이 있어도 오류가 났다면 같은 명령으로 확인합니다. `--like`·결과·최초 사람 판단을 유지합니다.

`gate.md`가 있어도 검토 누락이 남아 있다면 실제 사람의 검토를 추가하고 같은 `gate`를 다시 실행합니다. 점수 실패를 없애려고 답변이나 평가를 새로 뽑는 것과는 다릅니다.

[준비 선택으로 돌아가기](#setup-options)

# 수업 전 준비

[실습으로 돌아가기](../README.md)

**준비가 끝났다는 기준은 간단합니다.** 이 폴더에서 `python lab.py doctor --live`를 실행해 두 배포를 조회할 수 있어야 합니다. 실제 답변 생성과 클라우드 평가는 강사가 사전 리허설에서 추가로 확인합니다.

Azure가 준비되지 않았다면 [DEMO 경로](offline.md)로 바로 시작할 수 있습니다. 수업 중 새 인프라를 급하게 만드는 것보다 평가를 먼저 배우는 편이 낫습니다.

## 1. 환경 소유자가 준비할 것

| 항목 | 필요한 것 |
|---|---|
| 프로젝트 | 현재 Microsoft Foundry 프로젝트. Classic hub 연결 문자열 방식이 아님 |
| 답변 모델 | 프로젝트에서 호출할 수 있는 Azure OpenAI GPT 배포. Chat Completions와 JSON Schema Structured Outputs 지원 필요 |
| Judge 모델 | Groundedness/Relevance 평가기가 지원하는 GPT 채팅 모델 배포 |
| 계정 | 수강생 **본인 계정**. 프로젝트의 **Foundry User** 역할과 사용하는 모델에 필요한 접근 권한 |
| 네트워크 | 수강생 PC에서 프로젝트 endpoint에 접근 가능. 조직 정책·Private Link 조건 준수 |

**최소 구성은 모델 배포 하나**입니다. 같은 배포 이름을 답변 모델과 Judge에 넣을 수 있습니다. 가능하면 Judge는 별도 배포/모델을 사용합니다. 같은 모델을 써도 호출 자체는 분리되지만, 비슷한 편향을 공유할 수 있습니다.

모델 **카탈로그 이름**이 아니라 실제 **배포 이름**을 전달해야 합니다. 임의의 모델 이름을 붙여 넣는다고 배포가 생성되지는 않습니다.

자습 중 새 환경이 필요한 경우에는 환경 소유자가 공식 문서에 따라 먼저 준비합니다.

- [Foundry 프로젝트 만들기](https://learn.microsoft.com/azure/foundry/how-to/create-projects)
- [클라우드 평가의 프로젝트·모델·권한 사전 조건](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation#prerequisites)
- [Structured Outputs 지원과 사용 방법](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/structured-outputs)
- [평가의 지역·제한·네트워크 지원](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network)

역할이 **Azure AI User**라는 이전 이름으로 보일 수 있습니다. 이름 전환 중에도 역할 ID와 핵심 권한은 동일합니다. 권한 오류를 해결하려고 무조건 Owner를 부여하지 않습니다.

**필요 없는 것:** Hosted Agent 배포, Docker, azd, Azure AI Search, Storage 직접 연결, Application Insights, API 키, Copilot, Jupyter.

## 2. 수강생 PC 준비

필요한 도구는 **Python 3.10 이상**, 편집기, 브라우저, [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)입니다. Windows에서는 PowerShell로도 실행할 수 있으며 WSL은 필수가 아닙니다.

### 코드 폴더 열기

이미 코드가 있다면 **`foundry-evaluation-v1` 폴더**를 그대로 사용합니다. 처음 받는다면 접근 권한이 있는 GitHub 계정으로 [비공개 저장소](https://github.com/junwoojeong100/foundry-evaluation-v1)를 엽니다. **Code → Download ZIP**으로 받아 압축을 풀고 폴더 이름을 `foundry-evaluation-v1`으로 정할 수 있습니다.

Git이 설치되어 있고 GitHub 인증이 준비되어 있다면 다음 방법도 가능합니다. 이미 코드 폴더가 있다면 다시 clone하지 않습니다.

```bash
git clone https://github.com/junwoojeong100/foundry-evaluation-v1.git
cd foundry-evaluation-v1
```

GitHub 저장소 접근 권한과 Azure 프로젝트 접근 권한은 별개입니다. 아래 `az login`이 비공개 GitHub 저장소의 접근 권한을 부여하지는 않습니다.

`foundry-evaluation-v1`을 VS Code 등 편집기로 열고 그 폴더에서 터미널을 엽니다. 명령 실행 위치에 `lab.py`, `requirements.txt`, `data/`가 보여야 합니다.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

조직 정책 때문에 활성화 스크립트가 막히면 정책을 해제하지 마세요. 활성화 없이 `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`를 실행하고, 이후 명령의 `python`도 `.\.venv\Scripts\python.exe`로 바꿀 수 있습니다.

`requirements.txt`에는 LIVE 경로용 패키지만 있습니다. **DEMO에는 패키지 설치가 필요 없습니다.** 수업 도중 패키지를 임의 업그레이드하지 않습니다.

프로젝트 폴더의 이름이나 위치를 바꾼 뒤 기존 `.venv`가 이전 경로를 참조하면, 가상환경을 새 경로에서 다시 만들고 의존성을 복원해야 합니다. `config.json`과 `results/`는 가상환경과 별개이므로 그대로 보존합니다.

## 3. 설정은 세 값만 입력

편집기에서 [config.example.json](../config.example.json)을 열고 루트의 **`config.json`으로 다른 이름 저장**합니다. 기존 `config.json`이 있다면 덮어쓰지 말고 값을 확인합니다.

```json
{
  "project_endpoint": "https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT",
  "model_deployment": "YOUR-ANSWER-MODEL-DEPLOYMENT",
  "judge_deployment": "YOUR-JUDGE-MODEL-DEPLOYMENT"
}
```

| 필드 | 환경 소유자에게 받을 값 |
|---|---|
| `project_endpoint` | 프로젝트 Overview의 **Project endpoint**. `/api/projects/프로젝트이름`까지 포함 |
| `model_deployment` | 직원 질문에 답할 배포 이름 |
| `judge_deployment` | 저장된 답변을 채점할 배포 이름 |

`YOUR-...`는 모두 실제 값으로 바꿉니다. 프로젝트 endpoint는 모델 inference endpoint인 `/openai/v1/` 주소와 다릅니다.

**키·비밀번호·토큰은 넣지 않습니다.** 이 실습은 Azure CLI 로그인 자격 증명을 사용합니다. `config.json`과 `results/`는 `.gitignore`에서 제외 대상으로 지정되어 있습니다.

## 4. 본인 계정으로 로그인하고 확인

```bash
az login
python lab.py doctor --live
```

여러 테넌트에 속해 있다면 환경 소유자가 알려 준 테넌트로 `az login --tenant YOUR-TENANT-ID`를 실행합니다. 브라우저에서 직접 로그인과 MFA를 완료합니다. 다른 사람의 계정이나 토큰을 공유하지 않습니다.

**기대 출력 형태:**

```text
LOCAL OK: Python ..., dev 8개, holdout 4개
LIVE 조회 OK: model_deployment=... / ... / ...
LIVE 조회 OK: judge_deployment=... / ... / ...
로그인과 배포 조회만 확인했습니다. 모델 생성/평가 실행은 본 실습에서 확인합니다.
```

`doctor --live`는 무료 관리/정보 조회이며 답변 모델을 생성 호출하지 않습니다. 이 조회가 성공했다고 평가 권한·모델 기능·평가 서비스 가용성까지 보장되는 것은 아닙니다.

환경 소유자는 수업 전에 [강사 리허설](facilitator.md#rehearsal)을 완료합니다. 오류가 있으면 [문제 해결](reference.md#troubleshooting)에서 그 오류만 해결합니다.

## 5. 비용과 데이터 확인

핵심 경로는 **답변 20개 = dev V1 8개 + dev V2 8개 + holdout 4개**입니다. 추가 질문 하나까지 하면 답변 21개를 생성합니다.

두 평가기로 모두 채점하면 핵심 경로 **40개**, 추가 질문까지 **42개 평가 항목**입니다. 이것은 청구 API 호출 횟수의 보장이 아닙니다. 평가기 내부 호출, 추론 토큰, 실패 후 재시도 등에 따라 실제 비용이 달라집니다.

- 생성과 Judge 모두 유료일 수 있습니다. 모델·토큰·지역별 요금과 수업 인원으로 예산을 잡습니다.
- 초기 수업은 작은 데이터 그대로 시작합니다. 질문 수·반복 횟수를 늘리기 전에 비용을 확인합니다.
- 제공 데이터는 모두 합성입니다. 새 질문에도 실제 개인정보·비밀번호·기밀 규정을 넣지 않습니다.
- Judge 명령은 질문·규정·답변을 지정한 Foundry 프로젝트로 전송합니다.
- 다른 서비스가 기존에 과금 중이라면 이 실습 종료가 그 과금을 중단하지는 않습니다.

<a id="resume"></a>
## 새 터미널에서 이어서 하기

터미널에서 `foundry-evaluation-v1` 폴더로 이동한 뒤 가상환경만 다시 활성화합니다. 패키지 설치나 답변 수집을 처음부터 반복하지 않습니다.

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

이후 **다음 미완료 명령**을 실행합니다. 같은 설정으로 `run`을 재실행하면 저장된 응답을 재사용하고, `judge`는 저장된 원격 작업 ID를 재사용합니다. 상세한 중단/오류 경계는 [복구 설명](reference.md#resume)을 봅니다.

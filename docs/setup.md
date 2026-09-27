# 환경 준비 바로가기

[메인 실습](../README.md) · [문제 해결](reference.md#troubleshooting)

**처음 시작한다면 [README의 준비](../README.md#prepare)부터 순서대로 따라갑니다.** 설치·로그인·자원 생성·권한·설정·연결 확인 명령은 모두 그곳에 있습니다. 준비가 끝난 뒤 같은 문서에서 실습과 정리까지 이어집니다.

이 문서는 **필요한 준비 단계만 다시 찾거나, 기존 환경을 사용하거나, 중단한 실습을 재개할 때** 사용합니다. 같은 명령을 여기서 다시 실행할 필요는 없습니다.

<a id="tools"></a>
## 1. 코드와 도구 준비

[준비 1: 코드 받기와 도구 설치](../README.md#setup-tools) — 운영체제별 명령, 터미널 위치, 가상환경, 실습지 복사. 완료 신호는 `LOCAL OK`와 `dev 8개, holdout 4개`입니다.

<a id="sign-in"></a>
## 2. 같은 계정·구독으로 로그인

[준비 2: 사용할 구독으로 로그인](../README.md#setup-sign-in) — 포털과 CLI의 계정·테넌트·구독을 맞춥니다. `YOUR-...`에는 본인 실습지에 기록한 값을 넣습니다.

<a id="create-project"></a>
## 3. 전용 그룹과 프로젝트 만들기

[준비 3: 전용 그룹과 Foundry 프로젝트](../README.md#setup-project) — 자원별 역할과 이름, 생성 순서, 기록할 값을 확인합니다. 공유 자원을 새 전용 자원으로 오해하지 않습니다.

<a id="permissions"></a>
## 4. 데이터 접근 권한 확인

[준비 4: 모델 호출과 평가 권한](../README.md#setup-permissions) — 본인과 프로젝트 관리 ID에 필요한 역할을 확인합니다. 목록에서 프로젝트 ID를 못 찾으면 [관리 ID 선택 도움말](reference.md#managed-identity-access)을 사용합니다.

<a id="deploy-model"></a>
## 5. 모델 하나 배포

[준비 5: 모델 하나 배포](../README.md#setup-model) — 기본 배포 이름은 `eval-model`입니다. 모델이나 용량을 사용할 수 없으면 [모델·지역·쿼터 도움말](reference.md#model-availability)을 봅니다.

<a id="configure"></a>
## 6. 프로젝트 주소 하나 넣기

[준비 6: 설정 파일](../README.md#setup-config) — `config.json`에 실제 프로젝트 주소와 배포 이름을 넣습니다. 두 배포 항목에 `LIVE 조회 OK`가 나와야 다음으로 갑니다.

<a id="smoke"></a>
## 7. 답변 한 개로 연결 확인

[준비 7: 한 건의 생성·평가](../README.md#setup-smoke) — `N01` 한 건으로 유료 연결을 확인합니다. 답변 형식과 두 점수·이유가 모두 있어야 합니다. 대기·낮은 점수·실행 오류의 차이는 [명령 결과 읽기](../README.md#command-status)를 봅니다.

---

<a id="existing-environment"></a>
## 이미 허가받은 환경이 있다면

새 자원을 만들거나 기존 모델의 이름·설정을 바꾸지 않습니다.

1. 환경 소유자에게 **테넌트 ID·구독 ID·Project endpoint·모델 배포 이름·사용 및 정리 허용 범위**를 확인합니다. API 키나 공유 비밀번호를 받지 않습니다.
2. [준비 1](../README.md#setup-tools)에서 로컬 도구를 준비하고, [준비 2](../README.md#setup-sign-in)의 **로그인과 구독 확인**을 수행합니다. 자원을 만들지 않으므로 Owner 취득이나 공급자 등록은 요구하지 않습니다.
3. [준비 4](../README.md#setup-permissions)의 접근 권한을 확인합니다. 부족한 역할은 할당 권한이 있는 소유자에게 요청합니다.
4. 기존 배포가 **Chat Completions·Structured Outputs·Judge 평가**를 지원하는지 확인합니다. [준비 6](../README.md#setup-config)의 설정에 실제 주소와 배포 이름을 넣고 [준비 7](../README.md#setup-smoke)을 완료합니다.
5. [실습 0](../README.md#lab-0)으로 이어갑니다. 마지막에는 소유자와 합의한 본인 작업만 정리합니다. **공유 프로젝트·모델·리소스 그룹은 일괄 삭제하지 않습니다.**

<a id="cost"></a>
## 비용 확인

기본 경로의 호출 규모는 [README 준비](../README.md#prepare)에 있습니다. [모델 요금](https://azure.microsoft.com/pricing/details/azure-openai/)과 본인 배포 유형을 확인합니다. 생성 토큰 합계만으로 Judge 비용까지 계산하지 않습니다.

Azure 포털의 **Cost Management → Cost analysis**에서 해당 전용 그룹으로 범위를 좁혀 봅니다. 비용 반영은 늦을 수 있고, 예산 알림은 자동 지출 차단이 아닙니다. 끝나거나 중도 중단하면 [리소스 정리](cleanup.md)를 확인합니다.

<a id="resume"></a>
## 나중에 이어서 하기

1. VS Code에서 이전의 **`lab.py`가 있는 폴더**를 열고 새 터미널을 엽니다.
2. 가상환경만 다시 활성화합니다. macOS/Linux는 `source .venv/bin/activate`, Windows는 `.\.venv\Scripts\Activate.ps1`입니다. 활성화가 막혔던 Windows 환경에서는 계속 `.\.venv\Scripts\python.exe`를 사용합니다. 패키지를 매번 재설치하지 않습니다.
3. `results/my-worksheet.md`의 **마지막 완료 단계 / 다음 명령**을 확인합니다. 로그인이 만료됐으면 [로그인](../README.md#setup-sign-in)만 다시 합니다.

| 중단 당시 상태 | 재개 방법 |
|---|---|
| `run`이 일부 답변만 저장 | **같은 명령·같은 입력·같은 `--out`**으로 재실행. 저장된 행은 다시 생성하지 않음 |
| `judge`가 처리 중 | **같은 `judge` 명령 전체** 재실행. `--like`도 유지하며 기존 원격 작업 조회 |
| 명령이 이미 완료 | 다음 단계로 진행. 같은 명령은 저장 결과를 읽으며 새 실험이 아님 |
| 프롬프트·데이터·설정을 바꿈 | 기존 결과를 덮어쓰지 않음. 별도 결과 이름으로 새 실험을 설계 |

완료된 `run.json`·`judge.json`을 지워 재실행하지 않습니다. 응답 직후 저장 전에 끊긴 한 행은 재호출될 수 있으므로 추가 비용이 없다고 보장하지 않습니다. 폴더를 옮겼거나 원격 ID 저장 중 끊겼다면 [재개·복구 도움말](reference.md#resume)을 봅니다.

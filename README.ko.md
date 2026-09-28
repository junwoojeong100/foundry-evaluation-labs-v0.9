[English](README.md) | **한국어**

# AI 답변, 믿어도 될까요?

**Microsoft Foundry Evaluation 실습**

**바로 이동:** [경로 선택](#choose-path) · [환경 준비](#setup-map) · [중단·재개](docs/setup.md#resume)

가상의 **가온랩 출장비 도우미**가 규정에 맞게 답하는지 검사합니다. 이것이 **평가(Evaluation)**입니다. 명령을 복사해 실행하고 결과를 읽습니다. **Python 코드는 작성하지 않습니다.**

**진행 순서:** 기준 정하기 → 답변 검사 → 지침 개선 → 새 질문 확인 → 채택·보류 판단.

**처음이거나 Azure가 없다면 [무료 DEMO](docs/offline.md#lab-0)로 시작하세요.** 실제 모델을 평가하려면 [입문 LIVE](docs/intro-lab.md#lab-0), 검색까지 다루려면 [완결형 RAG](docs/complete-lab.md#architecture)를 선택합니다.

<details>
<summary>실습 배경과 작성자 실행 기록</summary>

사티아 나델라(Satya Nadella)의 [프런티어 생태계 글](https://snscratchpad.com/posts/frontier-ecosystem/)에서 영감을 받았습니다. 외부 순위 대신 우리 업무의 기준으로 AI를 평가하고 개선합니다.

[작성자 실행 기록](docs/reference.md#live-verification)은 참고용입니다. 본인 결과로 판단하며, 같은 점수를 얻으려고 반복 실행하지 않습니다.

</details>

<a id="choose-path"></a>
## 내게 맞는 경로 하나 고르기

**아래에서 하나만 선택합니다.** 다른 경로를 먼저 마칠 필요는 없습니다.

| 경로 | 이런 목표라면 | 필요한 환경·비용 |
|---|---|---|
| **[DEMO — 처음이라면](docs/offline.md)** | Azure 없이 평가 흐름 익히기 | Python만 사용. **무료·작성된 예제**, 실제 성능 측정 아님 |
| [입문 LIVE](docs/intro-lab.md) | 검색 없이 평가·프롬프트 개선부터 | Foundry 프로젝트·모델 배포 1개. **유료** |
| [완결형 RAG](docs/complete-lab.md) | 검색·대화 개선·새 질문 검증까지 | 지정 모델 버전·모델 배포 3개·Basic 이상 Search. **유료** |
| [Optional RAG — 검색 비교](docs/optional-rag.md) | Search 직접 검색과 Knowledge Base 비교 | 공통 준비 + Basic 이상 Search. **유료** |

**LIVE는 실제 Azure 호출, RAG는 검색한 근거로 답하는 방식**입니다. 유료 경로는 활성 구독과 사용 권한이 필요합니다. 자원 생성·권한 설정은 선택한 가이드에서 안내합니다. 기존 자원은 [소유자의 허가를 받아 재사용](docs/setup.md#existing-environment)합니다.

> [!IMPORTANT]
> **실행 완료와 답변 합격은 다릅니다.** 낮은 점수나 `BLOCK`(품질 기준 미달)도 학습 결과입니다. LIVE가 막히면 [DEMO 전환 절차](docs/setup.md#switch-to-demo)를 따르고 결과를 섞지 않습니다.

<a id="prepare"></a>
<a id="setup-map"></a>
## 공통 환경 준비 바로가기

**[공통 준비 1–7](docs/setup.md#prepare)**은 LIVE 경로가 함께 사용합니다. 끝나면 선택한 가이드로 돌아갑니다. DEMO는 [자체 준비](docs/offline.md#prepare)만 수행합니다.

| 찾는 단계 | 안내 |
|---|---|
| <a id="setup-tools"></a>1. 코드·도구 | [폴더, 터미널, 가상환경](docs/setup.md#setup-tools) |
| <a id="setup-sign-in"></a>2. 로그인 | [계정·구독·테넌트 확인](docs/setup.md#setup-sign-in) |
| <a id="setup-project"></a>3. 프로젝트 | [본인 전용 그룹과 Foundry 프로젝트](docs/setup.md#setup-project) |
| <a id="setup-permissions"></a>4. 권한 | [본인 계정과 프로젝트 관리 ID](docs/setup.md#setup-permissions) |
| <a id="setup-model"></a>5. 모델 | [모델 이름·버전·배포 이름 구분](docs/setup.md#setup-model) |
| <a id="setup-config"></a>6. 설정 | [`config.json`에 실제 주소 입력](docs/setup.md#setup-config) |
| <a id="setup-smoke"></a>7. 연결 확인 | [N01 한 건 생성·평가](docs/setup.md#setup-smoke) |

기존 환경은 생성 절차를 반복하지 않습니다. [CLI로 신규 준비](docs/setup.md#cli-provision)는 포털 준비 3–5의 **대체 경로**입니다.

<a id="lab-map"></a>
## 입문 LIVE 단계 바로가기

**입문을 선택했다면** [입문 진행표](docs/intro-lab.md#lab-map)를 따릅니다.

<a id="reading-guide"></a>
[가이드 읽는 법](docs/intro-lab.md#reading-guide): **할 일 → 명령 → 완료 확인 → 다음 단계** 순서입니다.

| 찾는 단계 | 안내 |
|---|---|
| <a id="lab-0"></a>0. 오답 발견 | [설치 없이 규정과 답변 판단](docs/intro-lab.md#lab-0) |
| <a id="lab-1"></a>1. 평가 기준 | [기대 행동과 합격선 고정](docs/intro-lab.md#lab-1) |
| <a id="lab-2"></a>2. 변경 전 답변 | [V1으로 dev 8개 생성](docs/intro-lab.md#lab-2) |
| <a id="lab-3"></a>3. Foundry 평가 | [코드·Judge·내 판단 비교](docs/intro-lab.md#lab-3) |
| <a id="lab-4"></a>4. 개선과 비교 | [지침만 바꾸고 회귀 확인](docs/intro-lab.md#lab-4) |
| <a id="lab-5"></a>5. 새 질문 | [holdout 4개와 채택·보류 판단](docs/intro-lab.md#lab-5) |
| <a id="lab-6"></a>6. 직접 적용 | [내 질문 하나와 네 문장 요약](docs/intro-lab.md#lab-6) |
| <a id="finish"></a>마무리 | [완료 체크리스트](docs/intro-lab.md#finish) |
| <a id="working-files"></a>작업 파일 | [편집할 세 파일과 시점](docs/intro-lab.md#working-files) |
| <a id="validate-extra"></a>추가 질문 검사 | [유료 호출 전 JSONL 확인](docs/intro-lab.md#validate-extra) |

<a id="help"></a>
## 필요한 때만 찾기

| 지금 필요한 것 | 안내 |
|---|---|
| <a id="command-status"></a>명령 결과 해석 | [완료·대기·오류·BLOCK 구분](docs/setup.md#command-status) |
| 중단한 실습 이어 하기 | [재개 절차와 결과 파일별 위치](docs/setup.md#resume) |
| 설치·권한·모델·점수 문제 | [문제 해결](docs/reference.md#troubleshooting) |
| <a id="retain-resources"></a>종료 후 기본 절차 | [결과·리소스 보존과 비용 확인](docs/cleanup.md#retain-resources) |
| <a id="delete-resources"></a>나중에 별도로 삭제 결정 | [소유자 승인 후 범위 확인·삭제](docs/cleanup.md#delete-resources) |
| 용어·평가 기준·공식 근거 | [상세 참고](docs/reference.md) |
| 단체 수업 진행 | [진행자 가이드](docs/facilitator.md) |
| 결과 예시를 영상으로 보기 | [국문·영문 요약과 자막](docs/media/README.md) |

**기본은 리소스 보존입니다.** 터미널을 닫아도 자원과 비용은 남을 수 있습니다. 실제 개인정보·기밀·비밀번호는 실습에 입력하지 않습니다.

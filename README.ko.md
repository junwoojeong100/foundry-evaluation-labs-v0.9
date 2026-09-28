[English](README.md) | **한국어**

# AI 답변, 믿어도 될까요?

**Microsoft Foundry Evaluation — 처음부터 끝까지 따라 하는 실습**

**바로 이동:** [경로 선택](#choose-path) · [환경 준비](#setup-map) · [중단·재개](docs/setup.md#resume)

가상의 **가온랩 출장비 도우미**가 규정에 맞게 답하는지 확인합니다. Evaluation은 **미리 정한 기준으로 AI 답변을 검사하는 일**입니다. 제공된 명령을 실행하고 답변을 읽으며 배우므로 **Python 코드를 작성할 필요는 없습니다.**

**배우는 흐름:** 기준 정하기 → 답변 검사 → 지침 개선 → 새 질문 검증 → 근거로 채택·보류 판단.

**처음이라면 [완결형 RAG의 1절](docs/complete-lab.md#architecture)부터 시작하세요.** Azure 환경 없이 먼저 체험하려면 [DEMO](docs/offline.md#lab-0)를 선택합니다. 두 경로 모두 설치 전에 규정과 답변부터 살펴봅니다.

<details>
<summary>실습의 배경과 공개 실행 기록의 범위</summary>

사티아 나델라(Satya Nadella)의 [프런티어 생태계에 관한 블로그 글](https://snscratchpad.com/posts/frontier-ecosystem/)에서 영감을 받았습니다. 외부 벤치마크만이 아니라 **우리 업무의 기준으로 AI를 평가하고, 사람의 판단을 바탕으로 개선을 반복하는 학습 루프**를 경험합니다.

[경로별 실행 기록의 범위](docs/reference.md#live-verification)를 구분합니다. 공개된 완결형 결과는 입문 LIVE의 검증을 대신하지 않습니다. 다른 실행의 점수를 예상 정답으로 사용하거나 같은 점수가 나올 때까지 반복하지 않습니다.

</details>

<a id="choose-path"></a>
## 내게 맞는 경로 하나 고르기

모든 가이드를 순서대로 끝내는 과정이 아닙니다. **목적과 사용 가능한 환경에 맞는 한 행**을 고릅니다.

| 경로 | 이런 목표라면 | 필요한 환경·비용 |
|---|---|---|
| **[완결형 RAG — 권장](docs/complete-lab.md)** | 검색부터 대화 개선·새 질문 검증까지 | 지정 모델 버전·모델 배포 3개·Basic 이상 Search. **유료** |
| [입문 LIVE](docs/intro-lab.md) | 검색 없이 평가·프롬프트 개선부터 | Foundry 프로젝트·모델 배포 1개. **유료** |
| [DEMO](docs/offline.md) | Azure 없이 평가 흐름 먼저 체험 | Python만 사용. **무료·작성된 예제**, 실제 성능 측정 아님 |
| [Optional RAG](docs/optional-rag.md) | 직접 Search와 Knowledge Base 비교 | 공통 준비 + Basic 이상 Search. **유료** |

**선택한 가이드만 순서대로 따릅니다.** 완결형·Optional RAG에 입문 전체는 선행 필수가 아닙니다. LIVE는 활성 Azure 구독과 필요한 생성·사용·역할 할당 권한을 먼저 확인합니다. 허가받은 기존 자원은 [기존 환경 준비](docs/setup.md#existing-environment)로 재사용합니다.

> [!IMPORTANT]
> **실습 완료 ≠ AI 답변 합격.** 낮은 점수나 `BLOCK`도 근거를 설명하면 유효한 결과입니다. LIVE·DEMO 명령과 결과는 섞지 않으며, 막히면 [DEMO 전환 절차](docs/setup.md#switch-to-demo)를 따릅니다.

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

**입문을 선택한 경우에만** [입문 진행표](docs/intro-lab.md#lab-map)를 따릅니다. 기존 README의 단계 링크도 아래에서 해당 안내로 이어집니다.

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

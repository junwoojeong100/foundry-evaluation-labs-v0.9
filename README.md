# AI 답변, 믿어도 될까요?

## 혼자 끝까지 해보는 Microsoft Foundry Evaluation

가상의 **가온랩 출장비 도우미**를 평가합니다. 코드는 준비되어 있습니다. 여러분은 **좋은 답의 기준을 정하고 → 답변을 확인하고 → 지침을 바꾸고 → 변경을 채택할지 판단**합니다.

> 높은 점수가 목표는 아닙니다. **“이 답변은 왜 문제이고, 이 변경은 왜 채택하거나 보류하는가?”**를 설명하면 성공입니다.

**처음이라면 [환경 만들기](docs/setup.md)부터 완료하세요.** Microsoft Entra ID 계정, 활성 Azure 구독, 해당 구독의 Owner 역할로 시작합니다. 한 프로젝트와 한 모델 배포만 사용하며, 검색 서비스나 에이전트 서버는 만들지 않습니다.

이후에는 **이 문서와 [실습지](WORKSHEET.md)만** 따라갑니다. 시간 제한 없이, `lab.py`가 있는 폴더의 같은 터미널에서 **명령 하나를 실행하고 완료를 확인한 뒤** 다음으로 넘어갑니다. 실습지는 `results/my-worksheet.md`로 저장합니다.

| 순서 | 할 일 |
|---|---|
| [0. 오답 발견](#lab-0) | 그럴듯한 답이 왜 위험한지 확인 |
| [1. 평가 기준](#lab-1) | 답변을 보기 전에 좋은 답의 조건 정하기 |
| [2. 변경 전 답변](#lab-2) | 같은 질문 8개에 답변 생성 |
| [3. Foundry 평가](#lab-3) | 코드·Judge·사람의 판단 비교 |
| [4. 개선과 비교](#lab-4) | 프롬프트만 바꿔 같은 질문으로 다시 측정 |
| [5. 새 질문과 판단](#lab-5) | 처음 보는 질문 4개로 확인하고 채택/보류 |
| [6. 직접 적용](#lab-6) | 새 사례 하나를 만들고 결과 정리 |
| [마무리](docs/cleanup.md) | 결과 보관·본인 리소스 정리 |

Azure를 사용할 수 없다면 [DEMO 경로](docs/offline.md)로 진행합니다. **아래는 LIVE 전용입니다.** DEMO는 작성된 예제 분석이며, 실제 모델의 성능 증거가 아닙니다.

---

<a id="lab-0"></a>
## 0. 그럴듯한 오답 찾기

직원이 질문합니다.

> 2026년 9월 국내 출장 숙박비가 1박 220000원입니다. 사전 승인은 없는데 바로 정산 가능한가요?

| 답변 A | 답변 B |
|---|---|
| 네, 한도는 240000원이므로 바로 정산하세요. | 공식 한도 200000원을 초과하므로 재무팀 사전 승인이 필요합니다. |

**할 일:** 먼저 선호하는 답과 이유를 정한 뒤, [출장 규정](data/policies.md)을 읽고 판단을 확인합니다.

<details>
<summary>판단한 뒤 해설 보기</summary>

B가 적절합니다. 240000원은 **미승인 초안**의 금액입니다. A는 친절하지만 잘못된 정산을 유도합니다. 유창함만 평가하면 이런 오류를 놓칩니다.

</details>

**완료:** 선택한 답과 규정에서 찾은 이유를 실습지 0–1에 한 줄로 남깁니다.

---

<a id="lab-1"></a>
## 1. 답변을 보기 전에 기준 정하기

**할 일:** [dev 질문 8개](data/dev.jsonl)를 읽습니다. `dev`는 **개선에 사용하는 질문 묶음**입니다. 아직 `data/holdout.jsonl`은 열지 않습니다. 그 4개는 마지막 확인용입니다.

`D02`의 기대 행동은 **사전 승인 필요, 한도 200000원, 근거는 TRAVEL-CURRENT**입니다. 실습지에 이 사례에서 절대 안내하면 안 되는 행동도 적습니다. 다른 질문에는 과거 규정·모르는 내용·금지 항목·규정 무시 요청·경계값·정보 부족이 있습니다.

모든 질문에 같은 출장 규정을 제공합니다. **질문과 규정은 모델에 주지만 정답은 주지 않습니다.** JSONL은 한 줄에 JSON 객체 하나인 파일입니다. 필드가 낯설면 [데이터 한 줄 읽기](docs/reference.md#data-contract)를 참고합니다.

### 평가는 세 가지를 함께 봅니다

| 방법 | 확인하는 것 | 한계 |
|---|---|---|
| **코드 검사** | 답변 형식·결정·금액·출처가 기대값과 맞는가? | 설명 문장의 의미까지 이해하지 못함 |
| **Foundry의 LLM judge** | Groundedness: 규정에 근거하는가? Relevance: 질문에 적절한가? | AI의 채점도 틀릴 수 있음 |
| **사람 검토** | 규정과 실제 답변을 대조했을 때 업무에 써도 되는가? | 모든 답변을 사람이 볼 수는 없음 |

### 이번 실습의 합격선

| 항목 | 기준 |
|---|---|
| 업무 검사 | 한 답변의 형식·결정·금액·출처 **모두** 통과 |
| Judge | Groundedness와 Relevance **각각 4/5 이상** |
| 전체 통과율 | 변경 후 dev와 holdout에서 업무·각 Judge 지표 **각각 80% 이상** |
| 중요 사례 | `critical: true`인 P0 사례는 업무·두 Judge 지표 모두 실패 0개 |
| 회귀 | 이전에 통과한 개별 검사나 Judge 지표가 새로 실패하는 경우 0개 |
| 누락·사람 검토 | 점수 누락 없이, 변경 후 dev와 holdout 각각 최소 한 사례 검토·반려 없음 |

8개에서는 **7개 이상**, 4개에서는 **4개 모두** 통과해야 80% 이상입니다. 4점은 정확도 80%라는 뜻이 아닙니다. 결과를 본 뒤 합격선을 낮추지 않습니다.

**완료:** D02의 기대 행동과 위험을 설명하고 위 기준을 확인했습니다.

---

<a id="lab-2"></a>
## 2. 변경 전 답변 8개 만들기

**할 일:** 기본 지침 V1으로 답변을 생성합니다.

```bash
python lab.py run --mode live --prompt v1 --out results/baseline
```

`baseline`은 **변경 전 결과**입니다. 이 명령은 답변을 만들고 무료 코드 검사까지 합니다. 아직 LLM judge는 실행하지 않습니다.

**완료:** `8/8 ... 저장`과 업무 통과율이 보입니다. `results/baseline/report.md`를 열어 어떤 사례가 통과·실패했는지 봅니다. 다음 단계에서는 D04 한 건을 자세히 확인합니다.

**FAIL은 발견한 평가 결과이지 실습 실패가 아닙니다.** 모두 통과해도 정상입니다. 실패가 나오거나 점수가 좋아질 때까지 다시 실행하지 않습니다.

---

<a id="lab-3"></a>
## 3. Foundry 점수와 내 판단 비교하기

**할 일 1 — 사람 먼저:** D04의 질문·답변·규정을 읽습니다.

```bash
python lab.py inspect results/baseline D04
```

`Judge: 아직 미평가`가 정상입니다. **실습지 2–3에 pass/fail과 이유를 먼저** 적습니다. 코드 결과는 보이지만 아직 Judge 점수는 보지 않습니다.

**할 일 2 — Foundry로 채점:**

```bash
python lab.py judge results/baseline
```

**새 답변을 만드는 것이 아니라 저장한 8개를 채점**합니다. Groundedness는 질문·규정·답변, Relevance는 질문·답변을 봅니다. 둘 다 정답 설명인 `ground_truth`는 받지 않습니다.

진행 중이면 같은 `judge` 명령을 다시 실행합니다. 저장된 작업을 조회하므로 새 평가를 만들지 않습니다. **두 점수와 `judge.json`이 생긴 뒤** 다음으로 갑니다.

**할 일 3 — 같은 D04를 대조:**

```bash
python lab.py inspect results/baseline D04
```

출력된 **Foundry 보고서 URL**도 엽니다. 완료된 실행에서 D04의 **같은 질문·답변·두 점수·이유**를 찾습니다. ID가 안 보이면 질문 문장으로 찾습니다. URL이나 실행을 못 찾으면 [포털 결과 찾기](docs/reference.md#portal-results)를 참고합니다.

실습지에 두 점수와 **내 판단에 동의하거나 동의하지 않는 이유**를 적습니다. 포털의 Pass 색상보다 원점수를 봅니다. 포털 합격선이 3이어도 이 실습은 4 이상입니다.

**완료:** D04를 근거로 코드·Judge·사람이 같은 판단인지 설명할 수 있습니다. 예를 들어 결정 필드는 맞아도 설명에 “승인 완료”를 지어내면 코드만으로 놓칠 수 있습니다. 한 사례를 대조했다고 Judge 정확성이 검증된 것은 아닙니다.

---

<a id="lab-4"></a>
## 4. 프롬프트만 바꿔 다시 비교하기

**할 일 1 — 가설과 수정:** 실습지에 “___ 문제를 줄이려고 ___ 지침을 바꾼다”를 적습니다. 실패가 없었다면 변경 후에도 올바른 행동이 유지되는지 확인합니다.

[V1 지침](prompts/v1.txt)을 읽고, [개선 예제 V2](prompts/v2.txt)를 **`prompts/my-v2.txt`로 다른 이름 저장**합니다. 가설에 맞게 한두 문장을 수정합니다. 막히면 제공된 V2로 진행해도 됩니다.

V2는 공식 규정과 날짜를 먼저 확인하고, 모르는 값이나 없는 승인을 만들지 않도록 안내합니다. **모델·규정·질문/정답·Judge·합격선은 그대로** 둡니다.

**할 일 2 — 같은 dev 8개로 생성·평가·비교:** 각 명령의 완료를 확인하며 순서대로 실행합니다.

```bash
python lab.py run --mode live --prompt prompts/my-v2.txt --out results/candidate
```

`candidate`는 **변경 후 후보 결과**입니다.

```bash
python lab.py judge results/candidate --like results/baseline
```

`--like`는 변경 전과 **같은 Judge 모델·평가기 버전**을 사용합니다.

```bash
python lab.py compare results/baseline results/candidate
```

`results/candidate/comparison.md`에서 **새로 통과한 사례와 회귀**를 봅니다. 회귀는 이전에 되던 것이 안 되는 변화입니다. **전체 통과율이 올라도 중요한 한 건이 나빠지면 보류**합니다.

Foundry 보고서의 **Evaluation / 평가**에서도 두 실행을 선택해 **Compare**로 답변·점수 이유를 비교합니다. 비교 버튼이 없으면 각 실행의 같은 질문을 나란히 봅니다. 점수 변화가 없다면 D06이 안전하게 유지됐는지 확인합니다.

**할 일 3 — 실제 답변 검토:**

```bash
python lab.py review results/candidate D06
```

명령이 답변을 보여 주면 `pass` 또는 `fail`과 이유를 입력합니다. 위험한 문장이 있으면 고득점이어도 `fail`입니다. 판정은 `reviews.json`에 저장됩니다.

**완료:** 실습지 4에 바꾼 지침과 좋아진/나빠진 사례를 남깁니다. 변화가 없으면 “변화 없음”으로 기록합니다.

---

<a id="lab-5"></a>
## 5. 새 질문으로 확인하고 채택/보류하기

**할 일 1 — 후보를 고정하고 새 질문 4개 실행:**

```bash
python lab.py run --mode live --frozen results/candidate --split holdout --out results/holdout
```

`holdout`은 **개선에 쓰지 않은 마지막 확인용 질문**입니다. `--frozen`은 candidate에 저장한 프롬프트·규정·모델 설정을 그대로 사용합니다. 이제 holdout 파일을 열어도 됩니다.

```bash
python lab.py judge results/holdout --like results/baseline
```

**4개 답변과 두 Judge 점수가 모두 저장되면**, H04를 읽고 판정합니다.

```bash
python lab.py review results/holdout H04
```

**할 일 2 — 처음 정한 기준으로 판단:**

```bash
python lab.py gate results/baseline results/candidate results/holdout
```

`gate`는 [실습 1의 기준](#lab-1)을 자동으로 확인하고 `results/candidate/gate.md`를 남깁니다.

| 결과 | 의미 |
|---|---|
| **BLOCK** | 이유를 읽고 보류합니다. 종료 코드 2는 의도한 품질 차단입니다. |
| **READY_FOR_HUMAN_REVIEW** | 교육용 기준 충족. **자동 배포 승인은 아닙니다.** |

**완료:** 실습지 5에 새 질문의 관찰과 내 채택/보류 이유를 적습니다. Dev와 holdout은 질문이 달라 전후 점수처럼 비교하지 않습니다. Holdout을 보고 프롬프트를 수정한다면 **다음에는 새 holdout이 필요**합니다.

---

<a id="lab-6"></a>
## 6. 내 질문 하나로 평가해 보기

**할 일 1 — 새 사례 작성:** [추가 사례 예제](data/my-case.example.jsonl)를 **`data/my-case.jsonl`로 다른 이름 저장**합니다. ID를 `N02`로 바꾸고, 출장 규정으로 판정할 수 있는 새 질문을 만듭니다.

모델 답변을 보기 전에 **정답·기대 행동·중요도**도 함께 수정합니다. 한 줄에 JSON 객체 하나로 저장합니다. 숫자는 `200000`, 미정 값은 `null`, 중요도는 `true`/`false`입니다. [필드 설명](docs/reference.md#data-contract)이 필요할 때만 참고합니다.

**할 일 2 — 생성·평가·확인:**

```bash
python lab.py run --mode live --prompt prompts/my-v2.txt --data data/my-case.jsonl --out results/my-case
```

```bash
python lab.py judge results/my-case --like results/baseline
```

```bash
python lab.py inspect results/my-case N02
```

이 한 건은 `extra`로 기록되며 기존 dev/holdout이나 Gate 결과를 바꾸지 않습니다.

**완료:** 실습지 6에 이 질문이 잡으려는 문제와 실제 결과를 적고, 마지막 네 문장 보고를 완성합니다. 다른 업무용 질문은 **질문 / 기대 행동 / 금지 행동 / 평가 방법**으로 따로 설계합니다. 출장 규정 코드 검사에 다른 업무를 억지로 넣지는 않습니다.

**마무리:** `results/`를 보관하고 **[본인 리소스 정리](docs/cleanup.md)**를 수행합니다. 터미널을 닫아도 Azure 자원은 남습니다. 공유 환경은 통째로 삭제하지 않습니다.

---

## 필요한 때만 보기

| 상황 | 이동 |
|---|---|
| 오류·점수 누락으로 진행이 안 됨 | [문제 해결](docs/reference.md#troubleshooting). 낮은 점수와 실행 오류를 구분합니다. |
| 중단했다가 다시 시작 | [재개 방법](docs/setup.md#resume). 완료한 결과는 보존합니다. |
| 평균이 올라도 보류하는 사례를 더 보고 싶음 | [회귀 함정 — 선택 연습](docs/offline.md#regression-trap). 별도 DEMO이며 LIVE 결과와 섞지 않습니다. |
| 개념을 스스로 확인하고 싶음 | [다섯 질문과 해설](docs/reference.md#self-check) |
| 단체 수업 진행 | [단체 진행 가이드](docs/facilitator.md) |

작은 질문 묶음의 한 번 실행은 운영 품질 보증이 아닙니다. [상세 기준·한계·공식 출처](docs/reference.md)는 참고용입니다. 기본 실습을 위해 먼저 읽을 필요는 없습니다.

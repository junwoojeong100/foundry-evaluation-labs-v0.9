[English](en/offline.md) | **한국어**

# Azure 없이 끝까지 해보는 DEMO

[메인 설명](../README.ko.md)

**이 문서의 순서만 따라갑니다.** 가상의 가온랩 출장비 도우미에 대해 **기준 정하기 → 답변 확인 → AI 채점 예제와 비교 → 변경 전후 비교 → 채택/보류**를 연습합니다. Python 3.10 이상만 필요하며 Azure 계정·로그인·유료 호출은 없습니다.

**답변·Judge 점수·이유는 모두 사람이 작성한 예제입니다.** 실제 모델이나 Foundry 평가기를 실행하지 않습니다. 예제의 분석 결과를 프롬프트 개선 효과나 실제 배포의 근거로 사용하지 않습니다.

**실습 0–6은 LIVE·DEMO에서 같은 번호**입니다. **0. 오답 판단 → 환경 준비 → 실습 1–6 → 마무리** 순서로 본문의 완료 확인과 자동 생성된 보고서를 사용합니다. 개인 메모는 선택 사항이며, 사람 판정은 안내된 `review` 명령으로 저장합니다.

<a id="lab-0"></a>
## 0. 그럴듯한 오답 찾기

**설치 없이 먼저 판단합니다.** “2026년 9월 국내 숙박비가 1박 220000원이고 사전 승인이 없다”는 질문에 아래 두 답 중 하나를 고릅니다.

| 답변 A | 답변 B |
|---|---|
| 한도는 240000원이므로 바로 정산하세요. | 공식 한도 200000원을 초과하므로 재무팀 사전 승인이 필요합니다. |

[출장 규정](../data/policies.md)을 브라우저에서 읽고 판단을 확인합니다.

<details>
<summary>판단한 뒤 해설 보기</summary>

B가 적절합니다. 240000원은 미승인 초안의 금액이며, 공식 한도 200000원을 초과하면 재무팀 사전 승인이 필요합니다.

</details>

**완료 확인:** 어떤 답이 규정에 맞는지 이유를 한 문장으로 설명할 수 있습니다. LIVE에서 이미 이 판단을 했다면 반복하지 않습니다.

<a id="prepare"></a>
## 준비. 코드와 터미널 준비

1. [저장소](https://github.com/junwoojeong100/foundry-evaluation-labs-v1)의 **Code → Download ZIP**으로 코드를 받아 압축을 풉니다. 접근 권한이 없다면 소유자가 승인한 ZIP을 받습니다. 이미 받았다면 생략합니다.
2. [Python 3.10 이상](https://www.python.org/downloads/)과 [VS Code](https://code.visualstudio.com/)를 설치합니다. Windows에서는 Python 설치 시 PATH 추가를 선택합니다.
3. VS Code의 **File → Open Folder**에서 `lab.py`가 바로 보이는 폴더를 열고 **Terminal → New Terminal**을 선택합니다.
4. 아래에서 본인 운영체제의 블록만 실행합니다. 이미 LIVE 준비에서 가상환경을 만들었다면 생성은 생략하고 활성화만 합니다.

**브라우저의 파일 링크는 읽기용입니다.** 수정은 VS Code의 로컬 파일에서 합니다. **Ctrl+P / macOS Cmd+P**에 파일 경로를 입력해 열고 **File → Save**로 저장합니다. 검색되지 않으면 왼쪽 탐색기에서 해당 폴더를 펼쳐 파일을 엽니다. `.md`는 **View → Command Palette → Markdown: Open Preview to the Side**로 읽되, 수정은 원본 텍스트 탭에서 합니다.

명령은 아래 코드 블록 안의 내용만 복사해 **VS Code 터미널**에 붙여 넣고 Enter를 누릅니다. Python 파일의 실행 버튼이나 `>>>` 대화창을 사용하지 않습니다. `>>>`가 보이면 `exit()`로 먼저 나옵니다.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows — PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows에서 활성화가 조직 정책으로 막히면 정책을 해제하지 않고, 이후 모든 `python`을 `.\.venv\Scripts\python.exe`로 바꿉니다. **Azure CLI와 `requirements.txt`의 패키지는 설치하지 않아도 됩니다.**

이제 같은 터미널에서 실행합니다.

```bash
python lab.py doctor
```

**완료 확인:** `LOCAL OK`와 `dev 8개, holdout 4개`가 보입니다.

<a id="working-files"></a>
**직접 편집할 파일은 실습 6의 `data/my-case.jsonl` 하나뿐입니다.** 저장소에 N02 예제 작업본이 이미 포함되어 있으므로 해당 단계에서 먼저 열어 확인합니다. 파일이 있다는 사실이 직접 작성하거나 실행했다는 뜻은 아닙니다. `config.json`은 필요 없습니다. 결과 폴더와 보고서는 명령이 자동으로 만듭니다. **생성된 JSON·보고서, 제공된 규정·질문·프롬프트는 수정하지 않습니다.** 작업본은 VS Code 기본 **UTF-8**로 저장합니다. LIVE에서 전환했다면 본인 질문·프롬프트와 기존 결과·Azure 자원을 보존합니다.

이후 **한 명령씩 실행하고 완료 확인을 본 뒤** 다음으로 갑니다. 별도 표시가 없으면 두 운영체제에서 같은 명령을 씁니다. 명령은 항상 `lab.py`가 있는 폴더에서 실행합니다. Windows 출력에서 `/` 대신 `\`가 보여도 같은 경로입니다. 기본 실습 결과 폴더는 `demo-`로 시작하며 LIVE 결과와 섞지 않습니다.

**오류·중단 시:** `ERROR:`는 [문제 해결](reference.md#troubleshooting)에서 해결한 뒤 진행하고, 낮은 점수·`FAIL`은 관찰 결과로 기록합니다. `BLOCK`은 실습 5에서 품질 실패와 증거 누락을 구분합니다. [결과 파일로 재개 위치 찾기](setup.md#resume-checkpoints)를 사용하되 완료된 `run`·`judge`를 반복하면 저장된 결과를 읽을 뿐 새 예제를 만들지 않습니다. DEMO 오류를 해결하려고 `--mode live`로 바꾸지 않습니다.

**`기존의 완료된 결과를 읽었습니다`가 나오면 정상적인 재사용입니다.** 새 `8/8 … 저장` 메시지 대신 요약의 건수와 `report.md`를 확인하고 다음 미완료 단계로 갑니다. 이 메시지를 없애려고 결과를 지우지 않습니다.

새 터미널에서는 `lab.py` 폴더로 돌아와 macOS/Linux의 `source .venv/bin/activate` 또는 PowerShell의 `.\.venv\Scripts\Activate.ps1`만 실행합니다. 생성·설치부터 반복하지 않습니다. 활성화가 막히면 가상환경 Python 직접 실행 방식을 유지합니다.

**폴더 이동·이름 변경으로 가상환경이 실행되지 않을 때만** [가상환경 복구](reference.md#moved-folder)를 따릅니다. 그 절의 LIVE 패키지 설치는 건너뛰며, 기존 DEMO 결과와 본인 질문은 보존합니다.

**준비 끝. 이제 아래 실습 1로 이어갑니다.**

<a id="lab-1"></a>
## 1. 답변을 보기 전에 기준 정하기

[dev 질문 8개](../data/dev.jsonl)를 읽습니다. `dev`는 개선에 쓰는 질문 묶음이고, `holdout`은 **마지막까지 보지 않을 새 질문 4개**입니다. 아직 `data/holdout.jsonl`은 열지 않습니다. JSONL은 한 줄에 질문과 정답을 담은 JSON 객체 하나인 파일입니다.

`D02`의 기대 행동은 **사전 승인 필요·한도 200000원·근거 TRAVEL-CURRENT**입니다. “이미 승인됐다”거나 “바로 정산하라”고 안내해서는 안 됩니다. 이 기대 행동과 위험을 먼저 판단합니다.

| 확인 방법 | 무엇을 보는가 |
|---|---|
| 코드 검사 | 답변의 형식·결정·금액·출처가 모두 정답과 같은가 |
| Judge | AI 채점자. Groundedness는 규정에 근거하는지, Relevance는 질문에 적절한지. **여기서는 점수 예제만 읽음** |
| 사람 검토 | 실제 답변의 설명까지 규정과 대조했을 때 업무에 써도 되는가 |

**고정 기준:** Judge는 각각 4/5 이상, 변경 후 dev와 holdout의 업무·각 Judge 지표 통과율은 각각 80% 이상이어야 합니다. `critical: true`인 **P0(중요 사례)** 실패, 이전 통과가 실패로 바뀌는 **회귀**, 누락은 없어야 합니다. 변경 후 dev와 holdout 각각 사람 검토도 필요하며 반려가 없어야 합니다. 8개에서는 7개 이상, 4개에서는 4개 모두 통과해야 80% 이상입니다.

**완료 확인:** D02의 기대 행동과 위험을 설명할 수 있으며, 결과를 본 뒤 기준을 낮추지 않습니다.

<a id="lab-2"></a>
## 2. 변경 전 답변 읽기

```bash
python lab.py run --mode demo --prompt v1 --out results/demo-baseline
```

`run`은 여기서 **저장된 예제 답변을 읽고 코드로 검사**합니다. `v1`은 기본 지침 버전이며 `demo-baseline`은 변경 전 결과 폴더입니다.

**완료 확인:** `8/8  D08 저장`, 업무 통과 **5/8, 62.5%**. `results/demo-baseline/report.md`를 열면 D03·D04·D08이 실패합니다. 실제 모델 성능이 아니라 예제의 결과입니다. `FAIL`은 발견한 오답이지 명령 실행 오류가 아닙니다.

<a id="lab-3"></a>
## 3. D04에서 사람과 Judge 비교

```bash
python lab.py inspect results/demo-baseline D04
```

질문·기대 행동·실제 답변이 출력됩니다. 답변의 `decision`은 결정, `limit_krw`는 숙박 한도, `citations`는 근거 문서 ID, `answer`는 설명입니다. `unknown`은 규정에 없음, `needs_info`는 질문 정보 부족을 뜻합니다.

**Judge 점수를 보기 전에** 규정과 답변을 대조하고 내 `pass`/`fail`과 이유를 정합니다. `Judge: 아직 미평가`가 정상입니다.

```bash
python lab.py judge results/demo-baseline
```

이 명령도 AI를 호출하지 않고 **작성된 점수와 이유를 읽습니다.** **`평가 완료: 8개 답변 × 2개 지표`**와 `Judge 결과: results/demo-baseline/judge.json`이 나오면 다시 D04를 엽니다.

`평가 완료`는 모든 사례의 점수·이유 확인과 파일 저장이 끝났다는 뜻이지 답변 합격이 아닙니다. JSON을 직접 셀 필요 없이 **`report.md`의 요약 표 → `사례별 근거`의 답변·점수 이유**를 읽습니다.

```bash
python lab.py inspect results/demo-baseline D04
```

**완료 확인:** 최초 판정과 두 점수를 대조해 동의/불일치 이유를 설명합니다. Groundedness는 낮고 Relevance는 높은 이유를 설명하고 “질문에 직접 답했지만 근거는 없는 답”을 구분합니다. DEMO에는 Foundry 보고서 URL이 없으며 포털 확인을 하지 않습니다.

<a id="lab-4"></a>
## 4. 같은 질문으로 V2와 비교

“___ 문제를 줄이려면 ___ 지침이 필요하다”는 가설을 정합니다. [V1](../prompts/v1.txt)과 [V2](../prompts/v2.txt)를 읽고, 공식 규정·날짜·정보 부족 처리에서 무엇이 달라졌는지 확인합니다. **제공된 파일은 수정하지 않습니다.** DEMO는 새 프롬프트의 효과를 측정하지 못하며, 아래 명령은 제공된 V2 예제를 읽습니다.

```bash
python lab.py run --mode demo --prompt v2 --out results/demo-candidate
```

```bash
python lab.py judge results/demo-candidate --like results/demo-baseline
```

`--like`는 기준 실행과 같은 채점 계약을 사용하라는 뜻입니다. **`평가 완료: 8개 답변 × 2개 지표`**와 `Judge 결과: results/demo-candidate/judge.json`을 확인하면 비교합니다.

```bash
python lab.py compare results/demo-baseline results/demo-candidate
```

`results/demo-candidate/comparison.md`에서 **새 통과 → 업무 검사 회귀 → Judge 회귀**를 읽습니다. 이어서 D06의 실제 답변을 검토합니다.

```bash
python lab.py review results/demo-candidate D06
```

명령은 입력을 기다립니다. 답변을 읽고 소문자 `pass` 또는 `fail`을 입력한 뒤 Enter, 이어서 **규정과 대조한 이유를 5자 이상** 입력하고 Enter를 누릅니다. 사람 판정은 이 명령으로 저장해야 Gate에 반영됩니다.

**판정할 때는 `answer` 문장까지 읽습니다.** [출장 규정](../data/policies.md)과 금액·날짜·사전 승인 조건을 대조하고 없는 승인을 만들어 내지 않았는지 확인합니다. 코드의 `PASS`나 Judge의 4점 이상을 그대로 사람의 `pass`로 옮기지 않습니다.

자동 실행은 [AI 보조 검토](reference.md#assisted-review)로 구분합니다. AI 판정을 사람의 승인으로 저장하지 않으며, 실제 사람 검토 미완료는 그대로 남깁니다.

**완료 확인:** 업무 검사 **8/8, 100%**, 새 통과 D03·D04·D08, 회귀 없음. `검토 저장: results/demo-candidate/reviews.json`도 보입니다. 보고서의 사례별 근거로 차이를 설명합니다. 작성된 V2 답변이 낫다는 관찰이며, 프롬프트의 실제 개선 효과는 아닙니다.

<a id="lab-5"></a>
## 5. Holdout과 채택/보류

```bash
python lab.py run --mode demo --frozen results/demo-candidate --split holdout --out results/demo-holdout
```

`--frozen`은 변경 후 candidate의 지침·규정·설정을 그대로 쓰게 합니다. **`4/4  H04 저장`**을 확인하면 `data/holdout.jsonl`을 열어도 됩니다.

```bash
python lab.py judge results/demo-holdout --like results/demo-baseline
```

**`평가 완료: 4개 답변 × 2개 지표`**와 `Judge 결과: results/demo-holdout/judge.json`을 확인하면 사람 검토를 합니다.

```bash
python lab.py review results/demo-holdout H04
```

실제 답변을 먼저 읽습니다. H04는 **출장일을 확인하지 않고 정산일로 판단**합니다. 작성된 Judge 점수는 둘 다 4점이지만 업무 검사는 실패합니다. 실제 답변대로 `pass`/`fail`과 이유를 입력하며, 통과시키려고 `pass`를 입력하지 않습니다. **`검토 저장: results/demo-holdout/reviews.json`**이 보이면 최종 기준을 확인합니다.

```bash
python lab.py gate results/demo-baseline results/demo-candidate results/demo-holdout
```

**완료 확인:** 업무 검사 **3/4, 75%**, Gate **BLOCK**, 종료 코드 `2`. H04를 `fail`로 기록하면 사람의 반려도 이유에 포함됩니다. `results/demo-candidate/gate.md`를 열어 보류 이유를 확인하고 **아래 실습 6으로 계속 진행합니다.**

이 예제의 품질 실패에 따른 `BLOCK`은 실습 실패가 아닙니다. **점수·사람 검토 누락도 `BLOCK` 사유가 될 수 있습니다.** 누락은 해당 단계를 완료한 뒤 같은 `gate` 명령을 다시 실행해 갱신합니다. 검토 저장만으로 `gate.md`가 바뀌지는 않습니다. `ERROR:`는 먼저 해결하고, 실제 품질 실패는 통과로 바꾸지 않습니다. Dev와 holdout은 질문이 달라 전후 점수로 비교하지 않습니다. Holdout을 보고 수정하면 다음에는 새로운 holdout이 필요합니다.

<a id="lab-6"></a>
## 6. 새 질문 설계와 마무리

**할 일 1 — 작업본 확인:** 먼저 `data/my-case.jsonl`을 엽니다. 저장소에는 숙박비 **180000원**인 N02 예제가 이미 포함되어 있습니다. 그대로 사용하려면 **할 일 3의 파일 확인**으로 가고 “제공 예제 그대로”라고 기록합니다. 이전 LIVE·DEMO에서 작성한 본인 질문이라면 덮어쓰지 않고 같은 검사로 가서 재사용했다고 기록합니다.

**직접 수정 연습을 하려면** 이 작업본을 사용합니다. 파일이 없을 때만 [추가 사례 예제](../data/my-case.example.jsonl)를 열고 **File → Save As**로 `data/my-case.jsonl`을 만듭니다. 원본은 바꾸지 않습니다. **작업본의 내용을 아래 한 줄 전체로 교체**한 뒤 할 일 2의 두 값을 수정합니다. 원본 예제의 N01이 아니라 **N02 한 건**을 준비합니다.

```jsonl
{"id":"N02","category":"과거 출장의 한도 초과","critical":true,"query":"2026년 6월 15일 국내 출장 숙박비가 1박 170000원입니다. 9월에 정산하면 사전 승인 없이 처리해도 되나요?","expected_decision":"needs_approval","expected_limit_krw":160000,"expected_citations":["TRAVEL-PREVIOUS"],"ground_truth":"정산일이 아니라 출장일의 과거 한도 160000원을 적용한다. 170000원은 한도 초과이므로 재무팀 사전 승인이 필요하며 바로 정산할 수 있다고 안내하면 안 된다."}
```

**할 일 2 — 처음에는 금액 두 곳만 수정:** 위 예제에서 아래 두 값을 같은 금액으로 바꾸고 저장합니다.

| 수정할 곳 | 바꿀 값 |
|---|---|
| `query`의 숙박비 | `170000` → `180000` |
| `ground_truth`의 한도 초과 금액 | `170000` → `180000` |

**나머지 값은 그대로 둡니다.** 6월 15일 출장의 규정 한도 `expected_limit_krw`는 **160000**이며 청구 금액이 아닙니다. 180000원도 한도 초과이므로 결정 `needs_approval`과 출처 `TRAVEL-PREVIOUS`는 바뀌지 않습니다.

마지막 요약에서 **예제 수정 / 직접 작성 / 예제 그대로 / 이전 질문 재사용** 중 사용한 방식을 구분합니다. 막히면 수정 전 예제를 그대로 사용했다고 설명합니다.

<details>
<summary>다른 질문을 직접 설계할 때만: 8개 필드의 의미</summary>

날짜·금액·상황을 바꾸면 규정과 대조해 기대 결정·한도·출처·이유도 함께 정합니다. ID는 `N02`로 유지합니다.

| 필드 | 채울 내용 |
|---|---|
| `id` / `category` | 사례 번호 `N02` / 확인하려는 문제 유형 |
| `critical` | 중요한 실패면 `true`, 아니면 `false` |
| `query` | 직원이 할 질문 |
| `expected_decision` | `allowed` 허용, `needs_approval` 사전 승인 필요, `not_allowed` 금지, `unknown` 규정에 없음, `needs_info` 정보 부족 중 선택 |
| `expected_limit_krw` | 적용 한도 정수 또는 `null`. 숫자에 쉼표·따옴표를 넣지 않음 |
| `expected_citations` | 필요한 공식 문서 ID의 배열. `TRAVEL-CURRENT`, `TRAVEL-PREVIOUS`, `SCOPE` 중 선택 |
| `ground_truth` | 기대 행동과 규정상 이유 |

</details>

**JSON 객체 하나를 한 줄에 저장합니다.** 자동 줄바꿈은 괜찮지만 Enter로 객체를 나누거나 빈 줄을 넣지 않습니다. 8개 필드를 모두 유지하고 `null`·`true`·`false`는 소문자로 씁니다.

**할 일 3 — 파일 확인:** `validate-data`는 로컬에서 검사만 하며 파일을 바꾸거나 모델을 호출하지 않습니다.

```bash
python lab.py validate-data data/my-case.jsonl
```

**완료 확인:** `DATA OK: 1 case(s)`. `ERROR:`가 나오면 표시된 필드나 줄을 수정하고 같은 검사만 다시 실행합니다. 2개 이상이면 다른 줄을 제거하고 N02 한 줄만 남깁니다. 이는 JSONL 문법·필수 필드·값 형식 확인이며 **정답의 타당성이나 모델 성능 검증은 아닙니다.** 정답은 규정과 직접 대조합니다. **DEMO는 N02의 답변을 생성하거나 채점하지 않습니다.** LIVE 명령을 추가로 실행하지 않습니다.

잡으려는 문제와 **“이 DEMO 경로에서는 N02 응답 생성·Judge 미실행”**을 구분합니다. 이전 LIVE 결과가 있더라도 별도 기록으로 남기고 DEMO의 실행 성과로 세지 않습니다. 마지막 네 문장으로 설명합니다.

> 작성된 ___ 예제에서 ___ 문제를 확인했다.<br>
> V1/V2 예제의 같은 질문에서는 ___, holdout 예제에서는 ___를 관찰했다.<br>
> ___ 근거 때문에 예제의 변경은 보류한다. 실제 프롬프트 개선 효과는 측정하지 않았다.<br>
> 내 업무에서는 ___ 실패부터 평가 데이터에 넣겠다.

### DEMO 완료 체크리스트

- [ ] `results/demo-baseline`, `results/demo-candidate`, `results/demo-holdout`에 각각 `report.md`·`judge.json`이 있고 업무 통과율 62.5%·100%·75%를 확인했다.
- [ ] D04의 최초 사람 판단과 Judge 예제를 비교했고, D06·H04의 실제 판정과 이유를 각 `reviews.json`에 저장했다.
- [ ] `results/demo-candidate/comparison.md`와 `gate.md`를 읽고 `BLOCK` 이유를 설명했다.
- [ ] N02의 데이터 검사와 작성·재사용 방식을 기록했고, 이 DEMO 경로에서는 답변·Judge 미실행임을 명시했다.
- [ ] 마지막 네 문장에서 **작성된 예제 분석**임을 설명하며 실제 모델 개선을 주장하지 않는다.

체크리스트까지 확인하면 **DEMO 실습 완료**입니다. 자동 리허설은 실제 사람이 하지 않은 검토를 완료로 체크하지 않습니다. `results/`를 로컬에 보관합니다. DEMO만 실행했다면 Azure 정리 대상은 없습니다. LIVE 환경을 만들다가 전환했다면 [리소스 보존·비용](cleanup.md)도 확인합니다.

---

<a id="regression-trap"></a>
## 선택 연습: 평균이 올라도 보류해야 한다면?

**기본 실습이 끝난 뒤 필요할 때만** 실행합니다. LIVE 참가자도 이 절만 독립적으로 실행할 수 있습니다. 별도 `results/trap-*` 폴더를 사용하며 모델 호출은 없습니다.

```bash
python lab.py run --mode demo --prompt v1 --out results/trap-baseline
```

```bash
python lab.py run --mode demo --prompt shortcut --out results/trap-candidate
```

```bash
python lab.py compare results/trap-baseline results/trap-candidate
```

```bash
python lab.py inspect results/trap-candidate D06
```

**예상 결과 — 작성된 예제에서만 고정:**

```text
업무 통과율: 62.5% -> 75.0%
새로 통과한 사례: D03, D08
업무 검사 회귀: D06(decision)
```

이 선택 연습은 `judge`를 실행하지 않으므로 `Judge 합격→불합격 회귀: 미평가`와 `Judge 비교: 미포함`도 정상입니다. 여기서는 **업무 검사 회귀만** 확인합니다.

평균은 좋아졌지만 D06에서 **없는 승인을 만들어 내는 새 실패**가 생겼습니다. 이 변경을 보류할 이유를 한 문장으로 설명하면 완료입니다.

예제와 무결성 정보는 `examples/`에 있습니다. 작성된 점수를 LIVE 결과나 수정한 프롬프트에 적용하지 않습니다.

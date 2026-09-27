# Azure 없이 진행하는 DEMO

[메인 설명](../README.md) · [실습지](../WORKSHEET.md)

**Python 3.10 이상만 있으면 됩니다.** 답변·Judge 점수·이유는 사람이 작성한 예제입니다. 모델 호출과 실제 Foundry 평가는 하지 않습니다.

[코드와 도구 준비](setup.md#tools)에서 **코드 받기·Python 설치·폴더 열기**만 수행합니다. Azure CLI·로그인·패키지 설치는 생략합니다. `python`이 없다면 macOS/Linux에서는 `python3`, Windows에서는 `py -3`로 바꿉니다.

**메인 실습 0–1의 설명을 읽고, 실행 명령은 아래만 사용합니다.** 실습지는 같은 파일을 쓰되 경로를 DEMO로 표시합니다. 포털 확인은 생략하고, LIVE 결과와 합쳐 비교하지 않습니다.

## 1. 변경 전 답변 읽기

```bash
python lab.py doctor
```

```bash
python lab.py run --mode demo --prompt v1 --out results/demo-baseline
```

**완료:** 업무 검사 **5/8, 62.5%**. 작성된 답변 D03·D04·D08이 실패합니다. 실제 모델 성능이 아니라 예제의 결과입니다.

## 2. D04에서 사람과 Judge 비교

```bash
python lab.py inspect results/demo-baseline D04
```

**Judge 점수를 보기 전에** 실습지 2–3에 사람 pass/fail과 이유를 적습니다. `Judge: 아직 미평가`가 정상입니다.

```bash
python lab.py judge results/demo-baseline
```

```bash
python lab.py inspect results/demo-baseline D04
```

**완료:** Groundedness는 낮고 Relevance는 높은 이유를 설명합니다. “질문에 직접 답했지만 근거는 없는 답”을 구분하고, 내 판정과 작성된 Judge 점수를 대조합니다.

## 3. 같은 질문으로 V2와 비교

메인 실습 4처럼 가설을 적고 `prompts/v1.txt`와 `prompts/v2.txt`를 읽습니다. **제공된 파일은 수정하지 않습니다.** DEMO는 새 프롬프트의 효과를 측정하지 못합니다.

```bash
python lab.py run --mode demo --prompt v2 --out results/demo-candidate
```

```bash
python lab.py judge results/demo-candidate --like results/demo-baseline
```

```bash
python lab.py compare results/demo-baseline results/demo-candidate
```

```bash
python lab.py review results/demo-candidate D06
```

답변을 읽고 `pass` 또는 `fail`과 이유를 입력합니다.

**완료:** 업무 검사 **8/8, 100%**, 새 통과 D03·D04·D08, 회귀 없음. 작성된 V2 답변이 낫다는 관찰이며, 프롬프트의 실제 개선 효과는 아닙니다.

## 4. Holdout과 채택/보류

```bash
python lab.py run --mode demo --frozen results/demo-candidate --split holdout --out results/demo-holdout
```

```bash
python lab.py judge results/demo-holdout --like results/demo-baseline
```

```bash
python lab.py review results/demo-holdout H04
```

H04는 **출장일을 확인하지 않고 정산일로 판단**합니다. 작성된 Judge 점수는 둘 다 4점이지만 업무 검사는 실패합니다. 실제 답변대로 판정하며, 통과시키려고 `pass`를 입력하지 않습니다.

```bash
python lab.py gate results/demo-baseline results/demo-candidate results/demo-holdout
```

**완료:** 업무 검사 **3/4, 75%**, Gate **BLOCK**, 종료 코드 `2`. H04를 `fail`로 기록하면 사람의 반려도 이유에 포함됩니다. 작은 예제의 점수가 모두 좋아도 DEMO는 실제 배포 판단에 사용할 수 없습니다.

## 5. 새 질문 설계와 마무리

메인 실습 6처럼 `data/my-case.example.jsonl`을 `data/my-case.jsonl`로 저장하고 **N02라는 새 질문·정답·기대 행동**을 작성합니다. 한 줄에 JSON 객체 하나로 저장합니다.

```bash
python -m json.tool data/my-case.jsonl
```

이것은 **JSON 문법 확인만** 합니다. DEMO는 새 질문의 답변을 생성하지 않습니다. 실습지에는 미실행 범위를 적고, 마지막 보고는 **“작성된 예제를 분석했다”**고 표현합니다.

DEMO만 실행했다면 Azure 정리 대상은 없습니다. LIVE 환경을 만들다가 전환했다면 [리소스 정리](cleanup.md)도 확인합니다.

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

평균은 좋아졌지만 D06에서 **없는 승인을 만들어 내는 새 실패**가 생겼습니다. 이 변경을 보류할 이유를 한 문장으로 설명하면 완료입니다.

예제와 무결성 정보는 `examples/`에 있습니다. 작성된 점수를 LIVE 결과나 수정한 프롬프트에 적용하지 않습니다.

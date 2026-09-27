# Azure 없이 진행하는 DEMO 경로

[메인 가이드](../README.md) · [실습지](../WORKSHEET.md)

**Python만 있으면 같은 180분의 학습 활동을 진행할 수 있습니다.** 다만 이 경로는 **사람이 작성한 답변·점수·이유를 읽고 분석하는 연습**입니다. 모델을 호출하거나 실제 Foundry 평가를 실행하지 않습니다.

**가능:** 평가 기준 설계, 코드 검사, 사례 분석, 회귀 탐지, holdout의 의미, 판단 기록.<br>
**불가능:** 직접 수정한 프롬프트의 실제 효과 측정, 새 질문에 대한 모델 응답 생성, Foundry 포털 결과 관찰.

DEMO 실행 결과를 LIVE 실측 보고서로 표현하면 안 됩니다. 모든 보고서에 DEMO 출처가 표시되며 두 경로를 섞어서 비교할 수 없습니다.

## 진행 방법

메인 가이드의 **설명·토론·시간표·워크시트는 그대로** 사용합니다. 실행 명령만 아래로 교체합니다. 메인 LIVE 명령을 함께 실행하지 않습니다.

| 시간 | 하는 일 |
|---|---|
| 00:00–00:15 | 메인 실습 0: 두 답변을 사람이 먼저 비교 |
| 00:15–00:35 | 메인 실습 1: 규정·8개 dev 질문·평가 계약 |
| 00:35–01:00 | 아래 1: 작성된 V1 답변을 코드로 검사 |
| 01:00–01:25 | 아래 2: 작성된 Judge 점수와 사람 판정 비교 |
| 01:25–01:35 | 휴식 |
| 01:35–02:05 | 아래 3: V2 지침을 읽고 변화의 가설·결과 분석 |
| 02:05–02:35 | 아래 4: 회귀 함정·holdout·Gate |
| 02:35–03:00 | 아래 5: 추가 질문 설계·발표·마무리 |

Python 3.10 이상이 필요합니다. 패키지 설치·Azure CLI·로그인은 필요 없습니다. macOS/Linux에서 `python` 명령이 없다면 아래 명령의 `python`을 `python3`로 바꿉니다. Windows에서는 `py -3`도 사용할 수 있습니다.

## 1. V1 답변을 읽고 코드로 채점

```bash
python lab.py doctor
python lab.py run --mode demo --prompt v1 --out results/demo-baseline
python lab.py inspect results/demo-baseline D03
python lab.py inspect results/demo-baseline D04
```

**예상:** 업무 검사 **5/8, 62.5%**. D03·D04·D08이 실패합니다.

`results/demo-baseline/report.md`를 열고 어떤 검사에서 왜 실패했는지 직접 설명합니다. 실제 모델이 62.5%라는 뜻이 아니라 **작성된 8개 답변 중 5개가 코드 기준을 통과했다**는 뜻입니다.

## 2. Judge도 틀릴 수 있음을 분석

```bash
python lab.py judge results/demo-baseline
python lab.py inspect results/demo-baseline D04
```

**점수와 이유 역시 작성된 예제**입니다. Groundedness는 낮고 Relevance는 높은 D04를 보고, “질문에 직접 답했지만 근거가 없는 답”을 구분합니다.

메인 실습 3처럼 D01·D04·D06을 사람이 먼저 판정하고 점수와 비교합니다. 포털 단계 대신 로컬 `report.md`에서 점수·이유·업무 검사를 함께 읽습니다.

## 3. V2와 같은 dev 질문 비교

메인 실습 4의 개선 가설을 먼저 씁니다. `prompts/v1.txt`와 `prompts/v2.txt`를 비교하고, 각각의 새 지침이 어떤 실패를 겨냥하는지 표시합니다.

**제공된 파일 자체는 수정하지 않습니다.** 자신의 개선안은 별도 파일에 적을 수 있지만 DEMO는 그것을 실행하지 않습니다. 변경한 프롬프트나 데이터에 기존 점수를 붙이지 않도록 도구가 재생을 거부합니다.

```bash
python lab.py run --mode demo --prompt v2 --out results/demo-candidate
python lab.py judge results/demo-candidate --like results/demo-baseline
python lab.py compare results/demo-baseline results/demo-candidate
python lab.py review results/demo-candidate D06
```

**예상:** 업무 검사 **8/8, 100%**, 새로 통과한 사례 D03·D04·D08, 회귀 없음.

검토 명령에 실제 예제 답변을 읽고 `pass` 또는 `fail`과 근거를 입력합니다. **작성된 V2 예제가 더 좋다는 관찰이지, 해당 프롬프트가 항상 더 좋다는 실측 결론은 아닙니다.**

## 4. 회귀와 holdout

먼저 메인 가이드의 [5-A 회귀 함정](../README.md#lab-5) 명령 네 개를 그대로 실행합니다. 그 명령도 DEMO이며 별도의 `results/trap-*` 폴더를 씁니다.

**예상:** 62.5% → 75.0%로 올라가지만 D06에서 없는 승인을 만들어 내는 회귀가 발생합니다.

이제 candidate를 고정한 상태로 새 질문을 확인합니다.

```bash
python lab.py run --mode demo --frozen results/demo-candidate --split holdout --out results/demo-holdout
python lab.py judge results/demo-holdout --like results/demo-baseline
python lab.py inspect results/demo-holdout H04
python lab.py review results/demo-holdout H04
python lab.py gate results/demo-baseline results/demo-candidate results/demo-holdout
```

**예상:** holdout 업무 검사 **3/4, 75%**, Gate는 **`BLOCK`**, 종료 코드 `2`.

H04의 작성된 답변은 정산일을 보고 출장일을 확인하지 않았습니다. 코드가 실패를 찾지만 작성된 Judge 점수는 둘 다 4점입니다. **Judge의 오판을 의도적으로 포함한 교육용 사례**입니다.

H04를 사람이 `fail`로 기록했다면 Gate에는 **holdout 통과율 부족**과 **사람의 반려**가 함께 나타납니다. 이 반려를 없애려고 근거 없이 `pass`로 바꾸지 않습니다.

## 5. 추가 질문과 업무 적용

메인 실습 6처럼 `data/my-case.example.jsonl`을 `data/my-case.jsonl`로 다른 이름 저장하고 질문·기대 행동·중요도를 적습니다. 동료와 정답이 규정에 맞는지 검토합니다.

DEMO는 새 질문의 답변을 생성하지 않습니다. JSON 객체가 하나인 이 추가 파일의 문법만 확인하려면 다음을 사용합니다.

```bash
python -m json.tool data/my-case.jsonl
```

이 명령은 **JSON 문법 검사**일 뿐 업무 정답이나 모델 품질의 평가가 아닙니다. LIVE 연결이 준비된 뒤 메인 실습 6의 `run --data`와 `judge`를 수행합니다.

워크시트 마지막을 **“작성된 예제를 분석했다”**는 표현으로 발표합니다. 실제 서비스 품질에 대해 내릴 수 없는 결론도 함께 말합니다.

## 예제 결과 한눈에 보기

| 작성된 예제 | 업무 검사 | 핵심 배움 |
|---|---|---|
| V1 dev | 5/8 · 62.5% | 유창해도 날짜·범위·정보 부족에서 실패 |
| V2 dev | 8/8 · 100% | 같은 질문에서 개선을 비교 |
| Shortcut dev | 6/8 · 75.0% | 평균 상승과 중요한 회귀가 동시에 가능 |
| 고정한 V2 holdout | 3/4 · 75.0% | 익숙한 질문의 100%가 새 질문의 성공을 보장하지 않음 |

예제 원본은 `examples/*.jsonl`, 출처와 무결성 정보는 `examples/manifest.json`에 있습니다. **합성 예제를 모델의 실제 실행 결과처럼 표시하지 않습니다.**

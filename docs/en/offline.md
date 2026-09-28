**English** | [한국어](../offline.md)

# Complete the DEMO without Azure

[Main guide](../../README.md)

Follow **this page only** to practice defining criteria, inspecting answers, comparing judge examples, and deciding whether to hold a change. You need Python 3.10+, not Azure, authentication, or paid calls.

**All answers, judge scores, and reasons are authored examples.** DEMO does not call a model or Foundry evaluator. Its results do not prove prompt improvement or production readiness. The same Korean fixtures are used in both language guides.

Activities **0–6** match LIVE. Follow the initial judgment, setup, activities 1–6, and finish using this page's checkpoints and generated reports. Personal notes are optional; save human verdicts through the documented `review` commands.

<a id="lab-0"></a>
## 0. Spot a plausible wrong answer

Before installation, consider a September 2026 domestic hotel expense of KRW 220000 per night with no prior approval.

| Answer A | Answer B |
|---|---|
| The limit is KRW 240000; submit the claim. | The official KRW 200000 limit is exceeded; prior Finance approval is required. |

Choose one, then read the [English policy translation](policies.md) or [Korean source](../../data/policies.md).

<details>
<summary>Explanation after deciding</summary>

B is appropriate. KRW 240000 is an unapproved draft proposal. Exceeding the official limit requires prior Finance approval.

</details>

**Checkpoint:** explain the choice in one sentence. If already done in LIVE, do not repeat the judgment.

<a id="prepare"></a>
## Setup. Prepare files and a terminal

1. On the [repository page](https://github.com/junwoojeong100/foundry-evaluation-labs-v1), choose **Code → Download ZIP** and extract it, or obtain an authorized copy. Skip this if you already have the files.
2. Install [Python 3.10+](https://www.python.org/downloads/) and [VS Code](https://code.visualstudio.com/). On Windows, enable Python PATH setup.
3. Open the folder containing `lab.py` and choose **Terminal → New Terminal**.
4. Use only your operating system's block. If a virtual environment already exists, activate rather than recreate it.

**Use your computer's terminal, not Azure Cloud Shell.** Use **PowerShell on Windows**, or **zsh/bash on macOS/Linux**. If Windows opens another shell, choose the arrow beside the terminal's `+` → **Select Default Profile → PowerShell**, then open a new terminal.

Open local files with **Ctrl+P / macOS Cmd+P** and save with **File → Save**. Browser links do not edit local files. Use Markdown preview for reading and the source tab for editing. Enter commands in the terminal, not at Python's `>>>` prompt; type `exit()` first if necessary.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows / PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is prohibited, use `.\.venv\Scripts\python.exe` in place of `python`; do not weaken organizational policy. For example, `python lab.py doctor` becomes `.\.venv\Scripts\python.exe lab.py doctor`. **Azure CLI and the packages in `requirements.txt` are unnecessary for DEMO.**

```bash
python lab.py doctor
```

**Checkpoint:** `LOCAL OK` and `dev 8개, holdout 4개`.

<a id="working-files"></a>
**The only file you edit is `data/my-case.jsonl` in activity 6.** The repository already includes an N02 example working copy; inspect it at that step. Its presence does not mean you wrote or executed it. No `config.json` is needed. Commands create result directories automatically. Keep the original policy, questions, prompts, and generated evidence unchanged. Save working files as UTF-8. If switching from LIVE, preserve your question, prompt, results, and Azure resources.

Run one command at a time from the `lab.py` folder; use only `demo-*` result folders for this path. Resolve `ERROR:` through [troubleshooting](reference.md#troubleshooting); treat FAIL and low scores as observations. For BLOCK, distinguish quality failures from missing evidence in activity 5. Use [resume checkpoints](setup.md#resume-checkpoints) after interruption; repeating a completed `run` or `judge` reads saved results rather than creating new examples. Do not switch to `--mode live` to work around a DEMO error.

**`기존의 완료된 결과를 읽었습니다` means completed results were reused successfully.** Instead of a new `8/8 … 저장` message, check the summary count and `report.md`, then continue at the next unfinished step. Do not delete results to remove this message.

In a new terminal, return to the `lab.py` folder and run only `source .venv/bin/activate` (macOS/Linux) or `.\.venv\Scripts\Activate.ps1` (PowerShell). Do not recreate the environment or repeat installation. If activation is blocked, keep using the virtual environment's Python directly.

**Only if moving or renaming the folder broke the environment**, follow [environment recovery](reference.md#moved-folder). Skip its LIVE package installation and retain your DEMO results and question.

**Setup complete. Continue to activity 1.**

<a id="lab-1"></a>
## 1. Choose criteria before seeing answers

Read [the dev cases](../../data/dev.jsonl). Do not open holdout yet. JSONL contains one question/expectation object per line.

D02 requires `needs_approval`, limit 200000, and `TRAVEL-CURRENT`. Do not advise immediate reimbursement or invent approval. Identify the expected behavior and risk first.

Code checks format, decision, limit, and citations. Groundedness asks whether policy supports the answer; Relevance asks whether it addresses the question. **Here their scores are examples, not fresh AI judgments.** A person still checks the explanation.

Keep the LIVE thresholds: each judge score ≥4/5; candidate/holdout business and each judge pass rate ≥80%; no critical P0 failures, regressions, missing evidence, or human rejection; review at least one case in each of candidate and holdout. Seven of eight and all four of four are needed for 80%.

**Checkpoint:** explain D02's expected behavior and risk, keeping the criteria unchanged after results.

<a id="lab-2"></a>
## 2. Read the baseline answers

```bash
python lab.py run --mode demo --prompt v1 --out results/demo-baseline
```

This replays authored answers and runs code checks.

**Checkpoint:** `8/8  D08 저장`, business **5/8 (62.5%)**, and `results/demo-baseline/report.md`. D03, D04, and D08 fail. These are example outcomes, not measured model performance.

<a id="lab-3"></a>
## 3. Compare your D04 judgment with the judge example

```bash
python lab.py inspect results/demo-baseline D04
```

Read the question, expectation, and actual authored answer. The answer's `decision` is the policy decision, `limit_krw` is the lodging limit (not the claimed expense), `citations` lists source IDs, and `answer` is the explanation. `null` means the limit cannot be determined or lodging limits do not apply—not zero.

Decisions are `allowed`, `needs_approval` (prior approval required), `not_allowed`, `unknown` (absent from policy), or `needs_info` (missing question information). `unknown` and `needs_info` can be correct depending on the case; none of these values executes reimbursement or grants approval.

**Before seeing judge scores**, decide pass/fail and your reason. `Judge: 아직 미평가` is expected.

```bash
python lab.py judge results/demo-baseline
```

This reads authored scores/reasons, with no AI call. Wait for **`평가 완료: 8개 답변 × 2개 지표`** and `Judge 결과: results/demo-baseline/judge.json`. Completion confirms validated saved evidence, not passing answers. Read `report.md` and `사례별 근거` for per-case evidence.

```bash
python lab.py inspect results/demo-baseline D04
```

**Checkpoint:** keep your initial verdict, both scores, and agreement/disagreement reasons. Explain how an answer can address the question while lacking grounding. DEMO has no Foundry report URL or portal check.

<a id="lab-4"></a>
## 4. Compare V2 on the same questions

Choose a hypothesis. Read [V1](../../prompts/v1.txt) and [V2](../../prompts/v2.txt), noting official policy, travel dates, and missing-information handling. **Do not edit them.** DEMO cannot measure a new prompt; it replays the provided V2 examples.

```bash
python lab.py run --mode demo --prompt v2 --out results/demo-candidate
```

**Checkpoint:** `8/8  D08 저장` and business **8/8 (100%)**. These are code-check results for the authored V2 answers; judge scores are not loaded yet. Read the score examples next:

```bash
python lab.py judge results/demo-candidate --like results/demo-baseline
```

`--like` preserves the judging contract. Confirm **`평가 완료: 8개 답변 × 2개 지표`** and `Judge 결과: results/demo-candidate/judge.json`.

```bash
python lab.py compare results/demo-baseline results/demo-candidate
```

Read newly passing cases, business regressions, and judge regressions in `comparison.md`. Then review D06:

```bash
python lab.py review results/demo-candidate D06
```

Enter `pass` or `fail`, then a policy-based reason of at least five characters. Read the `answer` text and check amounts, dates, and approval claims; do not copy the code or judge verdict. Save human verdicts through this command so the gate can use them.

Automated walkthroughs must use [assistant-attributed reviews](reference.md#assisted-review). Do not save an AI verdict as human approval; leave unperformed human review incomplete.

**Checkpoint:** business **8/8 (100%)**, newly passing D03/D04/D08, no regressions, and `검토 저장: results/demo-candidate/reviews.json`. Record the observation, not a claim of measured prompt improvement.

<a id="lab-5"></a>
## 5. Holdout and an adopt/hold decision

```bash
python lab.py run --mode demo --frozen results/demo-candidate --split holdout --out results/demo-holdout
```

`--frozen` preserves candidate instructions/policy/settings. After **`4/4  H04 저장`**, you may read holdout.

```bash
python lab.py judge results/demo-holdout --like results/demo-baseline
```

Confirm **`평가 완료: 4개 답변 × 2개 지표`** and `Judge 결과: results/demo-holdout/judge.json`.

```bash
python lab.py review results/demo-holdout H04
```

H04's authored answer incorrectly treats reimbursement timing as the travel date. Both authored judge scores are 4, but the business check fails. Record the actual verdict, not a `pass` chosen to remove a block. Confirm `검토 저장: results/demo-holdout/reviews.json`.

```bash
python lab.py gate results/demo-baseline results/demo-candidate results/demo-holdout
```

**Checkpoint:** business **3/4 (75%)**, **BLOCK**, expected exit code **2**. If H04 is reviewed as `fail`, human rejection is another reason. Read `results/demo-candidate/gate.md`, record your decision, and **continue to activity 6**.

This example's quality BLOCK is not a failure to complete the workshop. **Missing scores or human review can also cause BLOCK.** Complete those missing steps, then rerun the same `gate` command; saving a review alone does not refresh `gate.md`. Resolve `ERROR:` first, but do not change real quality failures into passes. Dev and holdout are different sets. If you change the prompt after examining holdout, use a new holdout next time.

<a id="lab-6"></a>
## 6. Design an extra question and finish

**Inspect `data/my-case.jsonl` first.** The repository includes an N02 example with an expense of **180000**. You may use it unchanged and go straight to validation below; record “provided example unchanged.” If it contains your previous LIVE or DEMO question, preserve it, validate it, and record reuse.

**To practice editing instead:** use this working file. Only if it is missing, save [the extra-case example](../../data/my-case.example.jsonl) as `data/my-case.jsonl`. Keep the original unchanged. Replace the working copy with this single line, then make the two edits below. Prepare **one N02 case**, not the source example's N01.

```jsonl
{"id":"N02","category":"과거 출장의 한도 초과","critical":true,"query":"2026년 6월 15일 국내 출장 숙박비가 1박 170000원입니다. 9월에 정산하면 사전 승인 없이 처리해도 되나요?","expected_decision":"needs_approval","expected_limit_krw":160000,"expected_citations":["TRAVEL-PREVIOUS"],"ground_truth":"정산일이 아니라 출장일의 과거 한도 160000원을 적용한다. 170000원은 한도 초과이므로 재무팀 사전 승인이 필요하며 바로 정산할 수 있다고 안내하면 안 된다."}
```

Change **`170000` → `180000`** in both `query` and `ground_truth`, but keep the **160000** policy limit, `needs_approval`, and `TRAVEL-PREVIOUS`. The question concerns a June 15 trip claimed in September; travel date determines the limit.

Distinguish editing the example, writing your own question, using the example unchanged, or reusing your previous question in your final summary. For your own question, define all eight required fields and expectations from policy first; keep ID N02. Save one JSON object per line with no blank lines, integer or `null` limits, and lowercase booleans.

```bash
python lab.py validate-data data/my-case.jsonl
```

**Checkpoint:** `DATA OK: 1 case(s)`. Fix field/line errors locally. The checker validates format, not the truth of the expectation. **DEMO does not generate or judge N02.** Do not add LIVE calls to this path.

Distinguish “N02 generation/judge not executed in this DEMO path” from completed work. Keep any previous LIVE results as separate records; do not count them as DEMO execution. Explain your findings in four sentences:

> In authored example ___, I found ___.<br>
> The same V1/V2 questions showed ___, and holdout showed ___.<br>
> Based on ___, I would hold the example change. No real prompt improvement was measured.<br>
> In my work, I would first add cases testing ___.

### Completion checklist

- [ ] The three `demo-*` folders contain reports/scores and business rates 62.5%, 100%, and 75%.
- [ ] D04's initial judgment is compared with the authored scores; D06 and H04 reviews are saved.
- [ ] Comparison and gate are read, and BLOCK is explained.
- [ ] N02 validates, its creation/reuse method is recorded, and it is explicitly not generated/judged in this DEMO path.
- [ ] The final report describes authored examples, not measured model improvement.

Automated rehearsals must not mark an unperformed human review complete. Keep `results/` locally. DEMO-only work creates no Azure resources. If you began LIVE first, verify [retention and costs](cleanup.md#retain-resources).

---

<a id="regression-trap"></a>
## Optional: a higher average can hide a regression

Do this only after the main workshop. LIVE participants can run it independently with the separate `results/trap-*` directories. No model calls occur.

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

Fixed outcomes of these authored examples:

```text
업무 통과율: 62.5% -> 75.0%
새로 통과한 사례: D03, D08
업무 검사 회귀: D06(decision)
```

This optional exercise does not run `judge`, so `Judge 합격→불합격 회귀: 미평가` and `Judge 비교: 미포함` are expected: **only business-check regressions** are measured here.

The average improves, but D06 newly invents approval. Explain why that warrants holding the change. Do not apply authored scores from `examples/` to LIVE answers or changed prompts.

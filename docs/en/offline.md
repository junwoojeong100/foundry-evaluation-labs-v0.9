**English** | [한국어](../offline.md)

# Complete the DEMO without Azure

[Main guide](../../README.md)

**Jump to:** [Start](#lab-0) · [Setup](#prepare) · [Resume](#resume) · [Finish](#finish)

**Learn the evaluation workflow without Azure.** Set criteria for the fictional Gaon Lab travel-expense assistant, inspect answers and judge examples, and decide whether to adopt or hold a change. **Follow this page only.**

| At a glance | DEMO |
|---|---|
| Requirements | **Python 3.10+ and VS Code**. No Azure account, authentication, or package installation |
| Cost | **No paid calls** |
| File you edit | Only `data/my-case.jsonl` in activity 6. No `config.json` |
| Results | `results/demo-baseline`, `demo-candidate`, and `demo-holdout` |

> [!IMPORTANT]
> **All answers, judge scores, and reasons are authored examples.** No model or Foundry evaluator is called. Results do not prove prompt improvement or production readiness. Both language guides use the same Korean fixtures.

<a id="lab-map"></a>
## Progress map

Activities 0–6 match LIVE. Follow **one command → checkpoint → next step**, saving human verdicts with `review`. Reports are generated automatically; personal notes are optional.

| Step | Action | Checkpoint |
|---|---|---|
| [0. Spot the mistake](#lab-0) | Compare policy and answers before installation | One-sentence judgment and reason |
| [Setup](#prepare) | Prepare code, Python, and terminal | `LOCAL OK` |
| [1. Criteria](#lab-1) | Set expected behavior and thresholds | Explain D02's risk |
| [2. Baseline](#lab-2) | Read V1 examples and code checks | Eight answers and `report.md` |
| [3. Judge comparison](#lab-3) | Compare your D04 judgment with authored scores | Agreement/disagreement reasons |
| [4. V2 comparison](#lab-4) | Compare matching questions and review D06 | `comparison.md` and a saved review |
| [5. Holdout and decision](#lab-5) | Read holdout, review H04, and apply the gate | `gate.md` and decision evidence |
| [6. Your question](#lab-6) | Prepare and validate one N02 case | `DATA OK: 1 case(s)` |
| [Finish](#finish) | Explain example results and limitations | Completion checklist |

**Producing a report is not the same as passing answers.** Example scores are not expected LIVE scores.

<a id="reading-guide"></a>
### How to read this guide

**Follow the action → command → checkpoint → next step.**

| Marker | How to use it |
|---|---|
| `bash` / `powershell` code block | Terminal commands. Copy one command at a time and wait for the prompt to return |
| `text` code block | Expected output, not a command to execute |
| **Checkpoint** | The message, count, or result to check before continuing |
| Collapsed explanation | Answers, exceptions, or optional exercises; expand when needed |

**Where to run:** always use the folder containing `lab.py`. Copy each long command as **one complete line**, without inserting Enter in the middle. Output folders are automatic; read `.md` reports in VS Code's Markdown preview.

**Start here:** [0. Spot a plausible wrong answer](#lab-0). Installation comes next.

---

<a id="lab-0"></a>
## 0. Spot a plausible wrong answer

Before installation, consider a September 2026 domestic hotel expense of KRW 220000 per night with no prior approval.

| Choice | Answer |
|---|---|
| **A** | The limit is KRW 240000; submit the claim. |
| **B** | The official KRW 200000 limit is exceeded; prior Finance approval is required. |

Choose one, then read the [English policy translation](policies.md) or [Korean source](../../data/policies.md).

<details>
<summary>Explanation after deciding</summary>

B is appropriate. KRW 240000 is an unapproved draft proposal. Exceeding the official limit requires prior Finance approval.

</details>

**Checkpoint:** explain the choice in one sentence. If already done in LIVE, do not repeat the judgment.

**Next:** [Setup](#prepare) · [Progress map](#lab-map)

---

<a id="prepare"></a>
## Setup. Prepare files and a terminal

### Setup 1. Open the folder and terminal

1. On the [repository page](https://github.com/junwoojeong100/foundry-evaluation-labs-v1), choose **Code → Download ZIP** and extract it, or obtain an authorized copy. Skip this if you already have the files.
2. Install [Python 3.10+](https://www.python.org/downloads/) and [VS Code](https://code.visualstudio.com/). On Windows, enable Python PATH setup.
3. Open the folder containing `lab.py` and choose **Terminal → New Terminal**.
4. Use only your operating system's block. If a virtual environment already exists, activate rather than recreate it.

**Use your computer's terminal, not Azure Cloud Shell.**

- **Windows:** PowerShell. If another shell opens, choose the arrow beside the terminal's `+` → **Select Default Profile → PowerShell**, then open a new terminal.
- **macOS/Linux:** zsh or bash.

**Browser file links are for reading.** Edit local files in VS Code.

| File task | Action in VS Code |
|---|---|
| Open | Enter the path with Ctrl+P / macOS Cmd+P; use Explorer if needed |
| Read a report | **View → Command Palette → Markdown: Open Preview to the Side** |
| Edit and save | Edit the source tab, not the preview → **File → Save** |

**Enter commands in VS Code's terminal.** Do not use a Python file's Run button or the Python `>>>` prompt; type `exit()` first if necessary.

### Setup 2. Create the virtual environment

**Run only your operating system's block.** Activate an existing environment rather than recreating it.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows / PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Azure CLI and the packages in `requirements.txt` are unnecessary for DEMO.**

<details>
<summary>If Windows blocks Activate.ps1</summary>

Use `.\.venv\Scripts\python.exe` in place of `python`; do not weaken organizational policy. For example, `python lab.py doctor` becomes `.\.venv\Scripts\python.exe lab.py doctor`.

</details>

### Setup 3. Check local files

Run this in the same terminal.

```bash
python lab.py doctor
```

**Checkpoint:** `LOCAL OK` and `dev 8개, holdout 4개`.

<a id="working-files"></a>
### Distinguish working files from results

| Category | What to do |
|---|---|
| Edit yourself | Only **`data/my-case.jsonl` in activity 6**; save it as UTF-8 |
| Not needed | `config.json`; DEMO does not use it |
| Generated automatically | Result folders, JSON, and reports; read without editing |
| Keep unchanged | Supplied policy, questions, and prompts |

The N02 example working copy is already included; **inspect it in activity 6**. Its presence does not mean you wrote or executed it. If switching from LIVE, preserve your question, prompt, results, and Azure resources.

Run one command at a time from the `lab.py` folder; use only `demo-*` result folders for this path. **Errors and low scores are different:** resolve `ERROR:` before continuing; treat FAIL and low scores as observations. Do not switch to `--mode live` to work around a DEMO error.

<a id="resume"></a>
<details>
<summary>Errors, interruptions, saved results, and a new terminal</summary>

Use [troubleshooting](reference.md#troubleshooting) for `ERROR:`. For BLOCK, distinguish quality failures from missing evidence in activity 5. Use [resume checkpoints](setup.md#resume-checkpoints) after interruption; repeating a completed `run` or `judge` reads saved results rather than creating new examples.

**`기존의 완료된 결과를 읽었습니다` means completed results were reused successfully.** Instead of a new `8/8 … 저장` message, check the summary count and `report.md`, then continue at the next unfinished step. Do not delete results to remove this message.

In a new terminal, return to the `lab.py` folder and run only `source .venv/bin/activate` (macOS/Linux) or `.\.venv\Scripts\Activate.ps1` (PowerShell). Do not recreate the environment or repeat installation. If activation is blocked, keep using the virtual environment's Python directly.

**Only if moving or renaming the folder broke the environment**, follow [environment recovery](reference.md#moved-folder). Skip its LIVE package installation and retain your DEMO results and question.

</details>

**Setup complete. Continue to activity 1.**

**Next:** [1. Criteria](#lab-1) · [Progress map](#lab-map)

---

<a id="lab-1"></a>
## 1. Choose criteria before seeing answers

### 1-1. Distinguish expected behavior and evaluation methods

Read [the dev cases](../../data/dev.jsonl). Do not open holdout yet. JSONL contains one question/expectation object per line.

D02 requires `needs_approval`, limit 200000, and `TRAVEL-CURRENT`. Do not advise immediate reimbursement or invent approval. Identify the expected behavior and risk first.

Code checks format, decision, limit, and citations. Groundedness asks whether policy supports the answer; Relevance asks whether it addresses the question. **Here their scores are examples, not fresh AI judgments.** A person still checks the explanation.

### 1-2. Fix the thresholds before seeing results

| Criterion | Requirement |
|---|---|
| Judge scores | Groundedness and Relevance each **at least 4/5** |
| Pass rates | Candidate dev and holdout each have business and each judge metric **at least 80%** |
| Critical cases and regressions | **Zero P0 failures** (`critical: true`); zero previously passing checks becoming failures |
| Completeness and human review | No missing evidence; at least one human review in candidate and holdout, with no rejection |

Reaching 80% requires **at least seven of eight**, or **all four of four**.

**Checkpoint:** explain D02's expected behavior and risk, keeping the criteria unchanged after results.

**Next:** [2. Baseline](#lab-2) · [Progress map](#lab-map)

---

<a id="lab-2"></a>
## 2. Read the baseline answers

```bash
python lab.py run --mode demo --prompt v1 --out results/demo-baseline
```

This replays authored answers and runs code checks.

**Checkpoint:** `8/8  D08 저장`, business **5/8 (62.5%)**, and `results/demo-baseline/report.md`. D03, D04, and D08 fail. These are example outcomes, not measured model performance.

**Next:** [3. Judge comparison](#lab-3) · [Progress map](#lab-map)

---

<a id="lab-3"></a>
## 3. Compare your D04 judgment with the judge example

### 3-1. Decide for yourself first

```bash
python lab.py inspect results/demo-baseline D04
```

Read the question, expectation, and actual authored answer.

| Answer field | Meaning |
|---|---|
| `decision` | Policy decision |
| `limit_krw` | Lodging limit, **not the claimed expense** |
| `citations` | Supporting document IDs |
| `answer` | Employee-facing explanation |

`null` means the limit cannot be determined or lodging limits do not apply—not zero.

Decisions are `allowed`, `needs_approval` (prior approval required), `not_allowed`, `unknown` (absent from policy), or `needs_info` (missing question information). `unknown` and `needs_info` can be correct depending on the case; none of these values executes reimbursement or grants approval.

**Before seeing judge scores**, decide pass/fail and your reason. `Judge: 아직 미평가` is expected.

### 3-2. Read the authored judge scores

```bash
python lab.py judge results/demo-baseline
```

**Checkpoint:** `평가 완료: 8개 답변 × 2개 지표` and `Judge 결과: results/demo-baseline/judge.json`.

This reads **authored scores and reasons**, with no AI call. After completion, inspect D04 again below.

Completion confirms validated saved evidence, not passing answers. Read the summary table in `report.md`, then `사례별 근거` for each answer and its scoring reasons.

### 3-3. Compare the same D04 again

```bash
python lab.py inspect results/demo-baseline D04
```

**Checkpoint:** keep your initial verdict, both scores, and agreement/disagreement reasons. Explain how an answer can address the question while lacking grounding. DEMO has no Foundry report URL or portal check.

**Next:** [4. V2 comparison](#lab-4) · [Progress map](#lab-map)

---

<a id="lab-4"></a>
## 4. Compare V2 on the same questions

### 4-1. Compare V1/V2 instructions and answer examples

Choose a hypothesis. Read [V1](../../prompts/v1.txt) and [V2](../../prompts/v2.txt), noting official policy, travel dates, and missing-information handling. **Do not edit them.** DEMO cannot measure a new prompt; it replays the provided V2 examples.

**Action 1 — read the V2 answer examples**

```bash
python lab.py run --mode demo --prompt v2 --out results/demo-candidate
```

**Checkpoint:** `8/8  D08 저장` and business **8/8 (100%)**.

These are code-check results for authored V2 answers; judge scores are not loaded yet.

**Action 2 — read score examples using the same judging contract**

```bash
python lab.py judge results/demo-candidate --like results/demo-baseline
```

**Checkpoint:** `평가 완료: 8개 답변 × 2개 지표` and `Judge 결과: results/demo-candidate/judge.json`.

`--like` preserves the baseline judging contract.

### 4-2. Check newly passing cases and regressions

```bash
python lab.py compare results/demo-baseline results/demo-candidate
```

**Checkpoint:** `비교표: results/demo-candidate/comparison.md`. Expect newly passing D03, D04, and D08, with no regressions.

Read newly passing cases, business regressions, and judge regressions in `comparison.md`. Then review D06:

### 4-3. Save your D06 verdict

```bash
python lab.py review results/demo-candidate D06
```

The command **waits for your input**; it has not stalled.

1. Read the **`answer` text** and compare amounts, dates, and approval conditions with the [policy translation](policies.md). Check that it does not invent approval.
2. Enter lowercase **`pass` or `fail`**, then press Enter.
3. Enter a **policy-based reason of at least five characters**, then press Enter.

Save through this command so the gate can use the verdict. Do not copy a code `PASS` or a judge score of 4 or higher into your human verdict.

Automated walkthroughs must use [assistant-attributed reviews](reference.md#assisted-review). Do not save an AI verdict as human approval; leave unperformed human review incomplete.

**Checkpoint:** business **8/8 (100%)**, newly passing D03/D04/D08, no regressions, and `검토 저장: results/demo-candidate/reviews.json`. Record the observation, not a claim of measured prompt improvement.

**Next:** [5. Holdout and decision](#lab-5) · [Progress map](#lab-map)

---

<a id="lab-5"></a>
## 5. Holdout and an adopt/hold decision

### 5-1. Read holdout examples for the frozen candidate

```bash
python lab.py run --mode demo --frozen results/demo-candidate --split holdout --out results/demo-holdout
```

`--frozen` preserves candidate instructions/policy/settings. After **`4/4  H04 저장`**, you may read holdout.

```bash
python lab.py judge results/demo-holdout --like results/demo-baseline
```

Confirm **`평가 완료: 4개 답변 × 2개 지표`** and `Judge 결과: results/demo-holdout/judge.json`.

### 5-2. Save your H04 verdict

```bash
python lab.py review results/demo-holdout H04
```

H04's authored answer incorrectly treats reimbursement timing as the travel date. Both authored judge scores are 4, but the business check fails. Record the actual verdict, not a `pass` chosen to remove a block. Confirm `검토 저장: results/demo-holdout/reviews.json`.

### 5-3. Read why the gate holds the change

```bash
python lab.py gate results/demo-baseline results/demo-candidate results/demo-holdout
```

**Checkpoint:** business **3/4 (75%)**, **BLOCK**, expected exit code **2**. If H04 is reviewed as `fail`, human rejection is another reason. Read `results/demo-candidate/gate.md`, record your decision, and **continue to activity 6**.

**This example's quality BLOCK is not a failure to complete the workshop.** Distinguish the cause.

- **Missing scores or human review:** finish those steps and rerun the same `gate` command. Saving a review alone does not refresh `gate.md`.
- **Genuine quality failure:** record the hold reason and continue. Do not change a failure into a pass.
- **`ERROR:`:** resolve it first.

Dev and holdout are different question sets, not a before/after pair. If you change the prompt after examining holdout, use a new holdout next time.

**Next:** [6. Your question](#lab-6) · [Progress map](#lab-map)

---

<a id="lab-6"></a>
## 6. Design an extra question and finish

### 6-1. Inspect the working copy and choose how to use it

Open `data/my-case.jsonl` first. The repository includes an N02 example with an expense of **180000**.

| Situation | Action |
|---|---|
| Use the provided example unchanged | Go to [6-3. Validation](#validate-extra); record “provided example unchanged” |
| Your previous LIVE/DEMO question is present | Preserve it and go to [6-3. Validation](#validate-extra); record reuse |
| Practice editing | Prepare the working copy below, then change two values in 6-2 |

**Only when editing:** put the following line in `data/my-case.jsonl` only if it contains no personal work to preserve. If missing, use **File → New Text File → Save As**. Prepare **one N02 case**.

```jsonl
{"id":"N02","category":"과거 출장의 한도 초과","critical":true,"query":"2026년 6월 15일 국내 출장 숙박비가 1박 170000원입니다. 9월에 정산하면 사전 승인 없이 처리해도 되나요?","expected_decision":"needs_approval","expected_limit_krw":160000,"expected_citations":["TRAVEL-PREVIOUS"],"ground_truth":"정산일이 아니라 출장일의 과거 한도 160000원을 적용한다. 170000원은 한도 초과이므로 재무팀 사전 승인이 필요하며 바로 정산할 수 있다고 안내하면 안 된다."}
```

### 6-2. Change only two amounts

Change **`170000` → `180000`** in both `query` and `ground_truth`, but keep the **160000** policy limit, `needs_approval`, and `TRAVEL-PREVIOUS`. The question concerns a June 15 trip claimed in September; travel date determines the limit.

Distinguish editing the example, writing your own question, using the example unchanged, or reusing your previous question in your final summary. For your own question, define all eight required fields and expectations from policy first; keep ID N02.

**Save one JSON object on one line.** Use VS Code's **View → Word Wrap** to read the long line. Visual wrapping is fine; do not insert Enter inside the object or add blank lines.

Preserve all eight fields, use integer or `null` limits, and keep `null`, `true`, and `false` lowercase.

<a id="validate-extra"></a>
### 6-3. Validate the file format

This local check does not modify files or call a model.

```bash
python lab.py validate-data data/my-case.jsonl
```

**Checkpoint:** `DATA OK: 1 case(s)`.

**If the result differs:** fix the field or line identified by `ERROR:` and repeat only this check. If more than one case is found, keep only the N02 line.

The checker validates JSONL syntax, required fields, and value formats. **It does not validate the expected answer or model performance**; compare expectations with policy yourself.

> [!IMPORTANT]
> **DEMO does not generate or judge N02.** Do not add LIVE calls to this path.

Distinguish “N02 generation/judge not executed in this DEMO path” from completed work. Keep any previous LIVE results as separate records; do not count them as DEMO execution. Explain your findings in four sentences:

> In authored example ___, I found ___.<br>
> The same V1/V2 questions showed ___, and holdout showed ___.<br>
> Based on ___, I would hold the example change. No real prompt improvement was measured.<br>
> In my work, I would first add cases testing ___.

**Next:** [Finish checklist](#finish) · [Progress map](#lab-map)

---

<a id="finish"></a>
## Finish. DEMO completion checklist

- [ ] The three `demo-*` folders contain reports/scores and business rates 62.5%, 100%, and 75%.
- [ ] D04's initial judgment is compared with the authored scores; D06 and H04 reviews are saved.
- [ ] Comparison and gate are read, and BLOCK is explained.
- [ ] N02 validates, its creation/reuse method is recorded, and it is explicitly not generated/judged in this DEMO path.
- [ ] The final report describes authored examples, not measured model improvement.

Automated rehearsals must not mark an unperformed human review complete. Keep `results/` locally. DEMO-only work creates no Azure resources. If you began LIVE first, verify [retention and costs](cleanup.md#retain-resources).

[Back to the progress map](#lab-map) · [Optional: averages and regressions](#regression-trap)

---

<a id="regression-trap"></a>
## Optional: a higher average can hide a regression

Do this only after the main workshop. LIVE participants can run it independently with the separate `results/trap-*` directories. No model calls occur.

<details>
<summary>Open the optional exercise: a higher average with a worse D06</summary>

```bash
python lab.py run --mode demo --prompt v1 --out results/trap-baseline
```

**Checkpoint:** `8/8  D08 저장`, business 5/8 (62.5%).

```bash
python lab.py run --mode demo --prompt shortcut --out results/trap-candidate
```

**Checkpoint:** `8/8  D08 저장`, business 6/8 (75%).

```bash
python lab.py compare results/trap-baseline results/trap-candidate
```

**Checkpoint:** `비교표: results/trap-candidate/comparison.md`. Next, inspect the regressed D06:

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

</details>

**English** | [한국어](../intro-lab.md)

# Introductory LIVE: evaluation and prompt improvement

[All paths](../../README.md) · [Shared setup](setup.md) · [Resume](setup.md#resume)

**Jump to:** [0. Spot the mistake](#lab-0) · [Progress map](#lab-map) · [Finish](#finish)

Use the fictional Gaon Lab travel-expense assistant to learn **evaluation and prompt improvement without retrieval**. This **paid path** calls a real model with the supplied policy and questions. Run commands and read the results; no Python coding is required.

> [!IMPORTANT]
> The commands below are **introductory LIVE only**. Do not simply replace `live` with `demo`. If Azure prevents progress, [switch to DEMO explicitly](setup.md#switch-to-demo), preserving existing records.

**Language:** the guides are in English, but policy inputs, questions, prompts, and CLI output remain **Korean** so both guides run the same experiment. Use the [English policy translation](policies.md) for reading, not as a replacement input.

<details>
<summary>Do not treat another path's scores as expected results</summary>

Keep [evidence scopes separate](reference.md#live-verification): the published complete-path result does not revalidate introductory LIVE. Do not rerun to reproduce another execution's scores.

</details>

<a id="lab-map"></a>
## Introductory LIVE progress map

**Start at [0. Spot the mistake](#lab-0); installation comes next.** Do not read every reference or edit files in advance.

Activities 0–6 share numbers across LIVE and DEMO; setup is separate. Follow each **Checkpoint → next step**. Generated reports replace any separate record form. Personal notes are optional; save human verdicts with `review`.

| Step | Your action | Evidence to keep |
|---|---|---|
| [0. Spot the mistake](#lab-0) | Explain why a plausible answer is unsafe | A policy-based judgment |
| [Setup](#prepare) | Prepare the shared environment, then return here | Configuration and one generated, evaluated answer |
| [1. Set criteria](#lab-1) | Define a good answer before seeing results | Fixed thresholds |
| [2. Baseline](#lab-2) | Answer eight questions using V1 | `results/baseline/report.md` |
| [3. Foundry evaluation](#lab-3) | Compare code, an AI judge, and your judgment | Reasons for the same D04 answer |
| [4. Improve and compare](#lab-4) | Change only the instructions; repeat the same questions | `results/candidate/comparison.md` |
| [5. Unseen questions and a decision](#lab-5) | Check four held-out questions | `results/candidate/gate.md` |
| [6. Apply it yourself](#lab-6) | Add one question and summarize | An extra case and four final sentences |
| [Finish](#finish) | Keep the evidence and verify retained resources | Completion and retention records |

> **Workshop completion ≠ passing AI answers.** Low scores or a final `BLOCK` are valid outcomes when you can explain the evidence and record why the change is on hold.

<a id="reading-guide"></a>
### How to read this guide

**No time limit: follow the action → command → checkpoint → next step.**

| Marker | How to use it |
|---|---|
| `bash` / `powershell` code block | Terminal commands. Copy one command at a time and wait for the prompt to return |
| `text` code block | Expected output or example input, not a command to execute |
| `YOUR-...` | Replace with a value verified in your environment; keep quotation marks |
| **Checkpoint** | The message, count, or result to check before continuing |
| Collapsed explanation | Answers, exceptions, or background; expand when needed |

**Where to run:** always use the folder containing `lab.py`. Unless stated otherwise, commands work in macOS/Linux and Windows PowerShell. Copy each long command as **one complete line**, without inserting Enter in the middle.

**Reading files:** keep the documented filenames and output directories. `results/baseline` is relative to the workshop folder; Windows may show `\` instead of `/`. Read `.md` reports in VS Code's Markdown preview. If results already exist, [resume them](setup.md#resume) instead of deleting them.

**Reusing results:** `기존의 완료된 결과를 읽었습니다` means saved results were read successfully, not regenerated. Check the count and report, then continue at the next unfinished step. See [other command messages](setup.md#command-status) when needed.

**Start here:** [0. Spot a plausible wrong answer](#lab-0)

---

<a id="lab-0"></a>
## 0. Spot a plausible wrong answer

**Start without installing anything or signing in to Azure.** An employee asks:

> My domestic business-trip hotel costs KRW 220000 per night in September 2026. I have no prior approval. Can I claim it immediately?

| Choice | Answer |
|---|---|
| **A** | Yes. The limit is KRW 240000, so submit the claim. |
| **B** | The official KRW 200000 limit is exceeded; prior Finance approval is required. |

**Do this:** choose an answer and explain why. Then read the [English policy translation](policies.md), or the [Korean source used by the model](../../data/policies.md), and check your judgment.

<details>
<summary>Read the explanation after deciding</summary>

B is appropriate. KRW 240000 appears in an **unapproved draft**. A sounds helpful but gives the wrong reimbursement advice. Fluency alone would miss this error.

</details>

**Checkpoint:** explain in one sentence which answer follows policy.

**Next:** [Setup](#prepare) · [Progress map](#lab-map)

---

<a id="prepare"></a>
## Setup. Connect the shared environment, then return

**Keep this page open and choose only the row that matches your situation.**

| Your situation | Setup to follow |
|---|---|
| You need a new environment | [Shared setup 1–7](setup.md#prepare) |
| You have an authorized project and model | [Existing-environment setup](setup.md#existing-environment); skip creation |
| N01 was already generated and evaluated in this environment | Check the saved result and continue to [activity 1](#lab-1); do not call it again |

**Return here:** after `평가 완료: 1개 답변 × 2개 지표` and N01's answer, two scores, and reasons are confirmed, **continue to activity 1 in this guide**.

<details>
<summary>Introductory LIVE response and evaluation counts</summary>

The path generates **22 responses and evaluates 44 metric items**: one setup case, eight baseline, eight candidate, four holdout, and one extra, each judged using two metrics. These are not billable API-request counts including evaluator internals and retries. Budget alerts and TPM allocations do not automatically stop spending.

</details>

<a id="working-files"></a>
### Edit each working file only when its step asks

| When | Working file | Starting material |
|---|---|---|
| Shared setup 6 | `config.json`, beside `lab.py` | Copy `config.example.json` |
| Activity 4 | `prompts/my-v2.txt` | Compare the included working copy with `prompts/v2.txt` |
| Activity 6 | `data/my-case.jsonl` | Included N02 working copy, not the N01 smoke example |

A working file's presence does not mean you edited or ran it. Preserve your earlier edits and results; do not manually change generated reports.

**Next:** [1. Set criteria](#lab-1) · [Progress map](#lab-map)

---

<a id="lab-1"></a>
## 1. Set criteria before seeing the answers

### 1-1. Read questions and expected behavior

Read the [eight dev questions](../../data/dev.jsonl). **Dev** is the set used during improvement. Do not open `data/holdout.jsonl` yet; those four questions are for the final check.

The expected D02 behavior is **prior approval required, limit 200000, source TRAVEL-CURRENT**. Identify what the assistant must never advise: claiming immediate reimbursement or inventing existing approval.

For English readers, the dev cases cover: D01 current policy, D02 missing prior approval, D03 an earlier travel date but later claim date, D04 an unknown overseas limit, D05 a prohibited business-class flight, D06 a request to ignore policy and invent approval, D07 an exact-limit boundary, and D08 a missing travel date.

Every question receives the same policy. **The model receives the question and policy, not the expected answers.** JSONL means one JSON object per line. `id` identifies a case, `query` is its question, `expected_*` supplies code-check expectations, and `ground_truth` is the human-readable explanation.

### 1-2. Understand the four answer fields

The answer has four fields. This is an **English explanation of the expected D02 answer, not actual model output**:

```json
{
  "decision": "needs_approval",
  "limit_krw": 200000,
  "citations": ["TRAVEL-CURRENT"],
  "answer": "KRW 220000 exceeds the KRW 200000 limit, so prior Finance approval is required."
}
```

| Answer field | Meaning |
|---|---|
| `decision` | Policy decision |
| `limit_krw` | Applicable lodging limit in KRW, or `null` |
| `citations` | Supporting document IDs |
| `answer` | Employee-facing explanation |

Decisions are `allowed`, `needs_approval`, `not_allowed`, `unknown`, or `needs_info`.

`limit_krw` is not the claimed expense. `null` means the limit cannot be determined or lodging limits do not apply—not zero. `unknown` and `needs_info` can be correct depending on the case; decision values do not execute reimbursement or grant approval.

### 1-3. Distinguish the three evaluation methods

| Method | What it checks | Limitation |
|---|---|---|
| **Code** | Format, decision, amount, and citations match expectations | Cannot understand the explanation's meaning |
| **Foundry LLM judge** | **Groundedness:** supported by policy? **Relevance:** responds appropriately? | The judge itself can be wrong |
| **Human review** | Policy consistency and real business risk | Cannot review every answer |

### 1-4. Fix the thresholds

| Criterion | Requirement |
|---|---|
| Business checks | All four checks pass for each passing answer |
| Judge | Groundedness and Relevance **each ≥ 4/5** |
| Pass rates | Candidate dev and holdout each have business and **each judge metric ≥ 80%** |
| Critical cases | No business or judge failures on **P0**, marked `critical: true` |
| Regression | No previously passing individual check or judge metric becomes a failure |
| Completeness and review | No missing scores; at least one actual human review in candidate and holdout, with no rejected case |

For eight cases, 80% requires **at least seven**; for four, it requires **all four**. A score of 4 is not “80% accuracy.” Do not lower thresholds after seeing results.

**Checkpoint:** explain D02's expected behavior and risk. Keep these criteria fixed.

**Next:** [2. Baseline answers](#lab-2) · [Progress map](#lab-map)

---

<a id="lab-2"></a>
## 2. Generate eight baseline answers

Use the basic V1 instructions. `v1` refers to `prompts/v1.txt`; omitting `--split` selects the eight dev cases.

```bash
python lab.py run --mode live --prompt v1 --out results/baseline
```

`baseline` is the before-change result. This command generates answers and runs free code checks, but not the LLM judge.

**Checkpoint:** see **`8/8  D08 저장`**, the business pass rate, and `results/baseline/report.md`.

| Report column | Meaning |
|---|---|
| `규칙` | `PASS` means all four business checks passed |
| `실패한 검사` | Failed `schema`, `decision`, `limit`, or `citations` check |
| Groundedness / Relevance | `미평가` (“not evaluated”) is expected for now |

A FAIL is an observed result, not failure to complete the workshop. All-pass results are also valid. Do not regenerate until the scores look better.

**Next:** [3. Foundry evaluation](#lab-3) · [Progress map](#lab-map)

---

<a id="lab-3"></a>
## 3. Compare Foundry scores with your own judgment

### 3-1. Decide before seeing judge scores

Read D04's question, answer, and policy.

```bash
python lab.py inspect results/baseline D04
```

`Judge: 아직 미평가` is expected. Decide **your pass/fail and policy-based reason first**.

### 3-2. Evaluate the eight saved answers

```bash
python lab.py judge results/baseline
```

Wait for **`평가 완료: 8개 답변 × 2개 지표`**. If still processing, repeat that exact command. `judge.json` is saved and `report.md` gains scores and reasons. Groundedness sees question, policy, and answer; Relevance sees question and answer. Neither gets `ground_truth`.

### 3-3. Compare scores and reasons for the same D04

```bash
python lab.py inspect results/baseline D04
```

Open the printed **Foundry report URL**, or locate the run using `foundry-job.json`. In the Completed run, find **D04**, or search for its original question:

> 2026년 9월 도쿄 출장의 호텔비 한도가 얼마인가요?

This asks for the Tokyo hotel limit in September 2026. Match the **same question, answer, raw scores, and reasons**, not the row position. Do not create another portal evaluation or upload the original questions again.

Read both scores and explain why you agree or disagree. The portal may call 3 a Pass, but this workshop requires 4.

**Checkpoint:** explain your original judgment, the two judge scores, and agreement/disagreement reasons. Keep the original judgment rather than changing it to match the judge.

A judge may penalize an appropriate refusal to invent an unknown amount. If its reason is “no specific amount was supplied,” compare that with the expected behavior. Record the disagreement; do not invent an amount or change thresholds to satisfy the judge.

**Next:** [4. Improve and compare](#lab-4) · [Progress map](#lab-map)

---

<a id="lab-4"></a>
## 4. Change only the prompt, then compare

### 4-1. Choose a hypothesis and edit the working copy

“To reduce ___, I will change ___.” If baseline already passes, test whether the change preserves correct behavior.

1. Open [V1](../../prompts/v1.txt) and the [V2 example](../../prompts/v2.txt).
2. Open **`prompts/my-v2.txt`**. The included example adds a missing-date guard to V2: do not list date-specific limits before the travel date is known, and cite only `SCOPE` then. Include this difference in your hypothesis. **Only if the working file is missing**, open V2 and **Save As `prompts/my-v2.txt`**. Keep the originals and any previous personal edits intact.
3. Edit one or two sentences in the working file to match your hypothesis and save. Using the included working example, or copying V2 unchanged, is also allowed; record which you used. **Always use the filename `prompts/my-v2.txt`**. V2 requires official policy, the actual travel date, no invented limits/approval, and consistent JSON and explanation.

Keep **model, policy, questions/expectations, judge, and thresholds unchanged**. Once candidate generation starts, keep this working prompt unchanged through activity 6. If candidate results already exist, [resume](setup.md#resume) rather than replacing the prompt and rerunning into the same folder.

### 4-2. Generate, evaluate, and compare the same eight dev answers

Check each command's completion before running the next.

**Action 1 — generate candidate answers**

```bash
python lab.py run --mode live --prompt prompts/my-v2.txt --out results/candidate
```

**Checkpoint:** `8/8  D08 저장`. `candidate` holds the **after-change results**.

**Action 2 — use the same judge**

```bash
python lab.py judge results/candidate --like results/baseline
```

**Checkpoint:** `평가 완료: 8개 답변 × 2개 지표` and `Judge 결과: results/candidate/judge.json`.

If still processing, repeat the command **including `--like`**. It preserves the judge model, evaluator versions, and evaluation group.

**Action 3 — compare before and after**

```bash
python lab.py compare results/baseline results/candidate
```

**Checkpoint:** `비교표: results/candidate/comparison.md`.

In `results/candidate/comparison.md`, inspect the business pass rate, newly passing cases, business regressions, and judge regressions. A regression is a previously passing check becoming a failure. **A better average does not cancel an important new failure.** Match case IDs in both reports to read actual answers and reasons.

**Compare in the portal:**

1. Under **Build → Evaluations**, open the baseline's **`straightforward-…` group name**, not just its Last run link.
2. Under **Evaluation runs**, select only **`v1-dev-…` and `my-v2-dev-…`**, then **Compare runs**.
3. Set **Baseline** explicitly to **`v1-dev-…`**; the first-selected candidate might otherwise become the reference.

Do not mix holdout, setup, or extra cases into before/after comparison.

The portal summarizes averages/statistics, not the local business checks or score-4 regressions. **Too few samples / Inconclusive** means there is insufficient evidence for a statistically established improvement. If comparison is unavailable, inspect the same question in each run.

`comparison.md`, human verdicts in `reviews.json`, and `gate.md` are **local workshop records**, not additional Foundry evaluations. A portal Pass does not replace them.

### 4-3. Read D06 and save your verdict

```bash
python lab.py review results/candidate D06
```

The command **waits for your input**; it has not stalled.

1. Read the **`answer` text** and compare amounts, dates, and approval conditions with the [policy translation](policies.md). Check that it does not invent approval.
2. Enter lowercase **`pass` or `fail`**, then press Enter.
3. Enter a **policy-based reason of at least five characters**, then press Enter.

Do not copy a code `PASS` or a judge score of 4 or higher into your human verdict.

The prompts are `사람의 판정 (pass/fail):` (“human verdict”) and `근거 문서와 답변을 비교한 이유:` (“reason after comparing policy and answer”). You may write your reason in English. Do not copy another review without checking your actual answer. Dangerous text warrants `fail` even with high scores.

For AI-operated walkthroughs, use [assistant-attributed reviews](reference.md#assisted-review). AI review is not human approval and cannot satisfy the gate's human-review requirement.

**Checkpoint:** see `검토 저장: results/candidate/reviews.json`. Use `comparison.md` and both runs' `report.md` to explain the changed instruction and improved/worsened cases, or “no change.”

**Next:** [5. Unseen questions and a decision](#lab-5) · [Progress map](#lab-map)

---

<a id="lab-5"></a>
## 5. Test unseen questions and decide

### 5-1. Freeze the candidate and generate/evaluate four holdout answers

```bash
python lab.py run --mode live --frozen results/candidate --split holdout --out results/holdout
```

`--frozen` uses the prompt, policy, and model configuration stored in candidate. Do not edit `my-v2.txt` now. After **`4/4  H04 저장`**, you may open `data/holdout.jsonl`.

```bash
python lab.py judge results/holdout --like results/baseline
```

Wait for **`평가 완료: 4개 답변 × 2개 지표`** and `Judge 결과: results/holdout/judge.json`. If still processing, repeat the same command, keeping `--like`.

### 5-2. Save the human verdict for H04

```bash
python lab.py review results/holdout H04
```

Read H04, enter your verdict and reason, and confirm **`검토 저장: results/holdout/reviews.json`**. Save human verdicts through this command so the gate can use them.

### 5-3. Apply the original criteria

```bash
python lab.py gate results/baseline results/candidate results/holdout
```

The gate writes `results/candidate/gate.md`.

| Result | Action |
|---|---|
| **BLOCK** | Record its reasons and hold the change. **Continue to activity 6.** Exit code 2 is intentional quality blocking. |
| **READY_FOR_HUMAN_REVIEW** | Educational criteria met; record your adoption-review recommendation and continue. **Not production approval.** |

**Checkpoint:** use `gate.md` to explain the result, your decision, and case-based evidence.

**If blocked, distinguish the cause.**

- **Missing scores or human review:** finish those steps and **rerun the same `gate` command**. Saving a review alone does not refresh `gate.md`.
- **Genuine quality failure:** preserve the failure and hold the change. Do not change a verdict just to pass.
- **Automated rehearsal:** explicitly leave real human review incomplete.

Dev and holdout have different questions and are not a before/after pair. If you change the prompt after inspecting holdout, **use a new holdout next time**.

**Next:** [6. Your own question](#lab-6) · [Progress map](#lab-map)

---

<a id="lab-6"></a>
## 6. Evaluate one question of your own

### 6-1. Inspect the working copy and choose how to use it

Open `data/my-case.jsonl` first. The repository includes an N02 example with an expense of **180000**.

| Situation | Action |
|---|---|
| Use the provided example unchanged | Go to [6-3. Validation](#validate-extra); record “provided example unchanged” |
| Your previous LIVE/DEMO question is present | Preserve it and go to [6-3. Validation](#validate-extra); record reuse |
| `results/my-case` already exists too | Use [resume checkpoints](setup.md#resume-checkpoints); do not replace the question |
| Practice editing | Prepare the working copy below, then change two values in 6-2 |

**Only when editing:** put the following line in `data/my-case.jsonl` only if it contains no personal work to preserve. If missing, use **File → New Text File → Save As**. This is **N02**, not setup case N01. Keep the Korean question and expectation.

```jsonl
{"id":"N02","category":"과거 출장의 한도 초과","critical":true,"query":"2026년 6월 15일 국내 출장 숙박비가 1박 170000원입니다. 9월에 정산하면 사전 승인 없이 처리해도 되나요?","expected_decision":"needs_approval","expected_limit_krw":160000,"expected_citations":["TRAVEL-PREVIOUS"],"ground_truth":"정산일이 아니라 출장일의 과거 한도 160000원을 적용한다. 170000원은 한도 초과이므로 재무팀 사전 승인이 필요하며 바로 정산할 수 있다고 안내하면 안 된다."}
```

Meaning: a June 15 trip costs KRW 170000 per night and is claimed in September. The travel-date limit is KRW 160000; exceeding it requires prior Finance approval.

### 6-2. Change only two amounts

| Field | Change |
|---|---|
| Hotel expense in `query` | `170000` → `180000` |
| Expense described in `ground_truth` | `170000` → `180000` |

Keep the **160000 limit**, `needs_approval`, and `TRAVEL-PREVIOUS`. The expense is not the policy limit. In your final summary, distinguish editing the example, writing your own question, using the example unchanged, or reusing your previous question.

For a new question, decide its expected behavior **before generating an answer**. Preserve all eight fields: `id`, `category`, boolean `critical`, `query`, `expected_decision`, integer-or-null `expected_limit_krw`, official-ID array `expected_citations`, and `ground_truth`. Keep ID `N02` for the commands below. Do not put another business domain into the travel-policy checker.

**Save one JSON object on one line.** Use VS Code's **View → Word Wrap** to read the long line. Visual wrapping is fine; do not insert Enter inside the object or add blank lines.

Numbers have no commas or quotation marks, and `null`, `true`, and `false` are lowercase. Do not add or remove fields.

<a id="validate-extra"></a>
### 6-3. Validate locally before paid calls

```bash
python lab.py validate-data data/my-case.jsonl
```

**Checkpoint:** `DATA OK: 1 case(s)`. Fix any reported field/line error and rerun validation. More than one case means another line such as N01 was left in the file. This checks structure, not whether your expected answer is correct.

### 6-4. Generate, evaluate, and inspect the extra case

Use the unchanged candidate prompt from activity 4.

```bash
python lab.py run --mode live --prompt prompts/my-v2.txt --data data/my-case.jsonl --out results/my-case
```

After **`1/1  N02 저장`**, evaluate:

```bash
python lab.py judge results/my-case --like results/baseline
```

Wait for **`평가 완료: 1개 답변 × 2개 지표`** and `Judge 결과: results/my-case/judge.json`. If still processing, repeat the same command, including `--like`.

```bash
python lab.py inspect results/my-case N02
```

This is an `extra` case. It does not change dev, holdout, or the gate.

**Checkpoint:** check its intended failure mode and actual result, then explain your findings in four sentences:

> In case ___, I found ___. / I found no error in these questions.<br>
> After changing ___, the same questions showed ___ and unseen questions showed ___.<br>
> Based on ___, I recommend adoption review / holding the change.<br>
> In my own work, I would first add cases testing ___.

For another domain, design a separate **question / expected behavior / forbidden behavior / evaluation method**. Do not run it through this domain-specific checker.

**Next:** [Finish checklist](#finish) · [Progress map](#lab-map)

---

<a id="finish"></a>
## Finish. Keep results and resources

### Completion checklist

Completion is about **execution and evidence-based judgment**, not obtaining high scores.

- [ ] Baseline, candidate, and holdout each have `report.md` and `judge.json`, containing scores and reasons for 8, 8, and 4 answers.
- [ ] Candidate `comparison.md` identifies improvements and regressions, or explicitly no change.
- [ ] Candidate D06 and holdout H04 have actual human verdicts/reasons in their `reviews.json` files.
- [ ] You can explain `results/candidate/gate.md` and your decision, including a valid `BLOCK`.
- [ ] `results/my-case/report.md` and `judge.json` contain the N02 answer and two scores; its creation method is recorded.
- [ ] D04's original judgment is compared with the judge scores, and you can explain the observations and final decision in the four sentences above.

**Automated rehearsals** may complete execution, assistant review, and the gate, but must not mark an unperformed human review as complete. Report that remaining condition honestly.

<a id="retain-resources"></a>
### Default: retain every created Azure resource

**Closing the terminal does not stop Azure charges.** Follow these steps even if you stop early.

1. Keep the full `results/` folder and the status of pending remote jobs.
2. Follow [shared retention steps](cleanup.md#retain-resources) to check actual resources and costs.
3. Record the retention reason, costs, and next check. Without a deletion date, **retain until a separate request**.

**Checkpoint:** results and resources remain, and you can explain the cost status and retention conditions. Do not mark uncreated resources or unrun stages as complete.

<a id="delete-resources"></a>
### Optional: only after a separate deletion decision

**Retention is the default.** Only after the owner's separate deletion decision, follow the [shared deletion steps](cleanup.md#delete-resources). Never delete shared resources as a group. See [retention and cleanup](cleanup.md) for the full procedure.

**The checklist plus confirmed retention or deletion status completes the workshop. Deletion is not required.** One small, single-run evaluation is not a production-quality guarantee or deployment approval.

[Back to the progress map](#lab-map) · [Choose another path](../../README.md#choose-path)

---

## Read only when needed

| Need | Reference |
|---|---|
| Find a setup step or use CLI provisioning | [Setup](setup.md) |
| Resolve errors or missing scores | [Troubleshooting](reference.md#troubleshooting) |
| Continue interrupted work | [Resume safely](setup.md#resume) |
| Explore a higher-average regression trap | [Optional DEMO exercise](offline.md#regression-trap) |
| Check your understanding | [Five questions](reference.md#self-check) |
| Lead a group | [Facilitator guide](facilitator.md) |
| Watch edited portal/CLI recordings | [Videos and subtitles](../media/README.md), from a separate complete-path run, not evidence that you completed this lab |

See [contracts, limitations, and official sources](reference.md) for details, not prerequisites to reading this guide.

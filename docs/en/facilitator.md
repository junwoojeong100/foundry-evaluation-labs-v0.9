**English** | [한국어](../facilitator.md)

# Facilitator guide

[All paths](../../README.md) · [Introductory participant guide](intro-lab.md) · [Shared setup](setup.md)

Teach **evidence-based judgment**, not just tool operation. If D06 actually regressed, “approval fabrication means I would hold the change” is more useful than “the score increased.” Require evidence and reasons, not a predetermined failure.

**Scope:** the pre-class checklist, rehearsal, and 0–6 table below are for **introductory LIVE/DEMO**. Complete RAG uses [its own checkpoints](#complete-checkpoints), not the 80% gate, D06/H04 workflow, or one-model constraint.

Introductory participants follow the [introductory guide](intro-lab.md): activity 0, shared setup, activities 1–6, and resource retention. Return to that guide after setup. Use checkpoints rather than a fixed timetable. Keep LIVE and authored DEMO evidence distinct. English documentation uses the same Korean experimental inputs as the Korean guide; use the [policy translation](policies.md) to explain them without changing the experiment.

Use generated reports and ask participants to explain cases and judgment reasons, rather than transcribing scores or completing a separate submission form.

## Before the workshop

- [ ] Participants can access the repository or an authorized ZIP.
- [ ] Each participant has the correct Entra account and active subscription. New-resource operators need creation and role-assignment permissions; existing-environment users need the agreed access. Owner is one way to provision, not every user's minimum role. Check [task-specific permission scopes](reference.md#permissions-contract).
- [ ] Activity 0 occurs before installation; participants then perform their own setup without shared passwords or prefilled credentials.
- [ ] Use one dedicated group/project and one `eval-model` deployment of **`gpt-6-luna`**, in **`swedencentral`**.
- [ ] Check each resource's region separately and match the project identity to parent-resource IAM. Owner/model lookup alone is insufficient.
- [ ] Distinguish catalog model, model version, deployment name, and API version. Do not rename shared deployments or describe `GlobalStandard` as guaranteed Sweden-only processing.
- [ ] Verify Chat Completions, Structured Outputs, judge support, project access, and region availability.
- [ ] Each participant completes the one-case smoke generation/evaluation.
- [ ] Account for shared subscription TPM/RPM, concurrent judges, delays, and costs.
- [ ] If organizational approval blocks LIVE, clearly label any temporary DEMO practice.
- [ ] Use separate local output folders; only one operator writes a given run.
- [ ] Participants can distinguish originals, included example working files, their own edits, and generated evidence. `prompts/my-v2.txt` and `data/my-case.jsonl` already exist; do not overwrite personal work or present example reuse as an edit.
- [ ] Confirm the `평가 완료` count and report reasons, not only portal Completed/Pass.
- [ ] Verify participants can reopen a terminal and resume without regenerating completed work.
- [ ] Retain created resources and record costs; never execute deletion merely because a session ended.

Shared environments are not the introductory default. If unavoidable, define permissions, quotas, output ownership, and retention scope first. Parent-resource roles are inherited by child projects; separate names or local folders do not isolate permissions. Never apply dedicated-group deletion instructions to shared infrastructure.

<a id="rehearsal"></a>
## Rehearse the real environment

Local and SDK transport tests are **not actual Azure execution**. For a full rehearsal, follow the [introductory guide](intro-lab.md) and its linked shared setup in a clean working/output location; do not delete previous `results/` or mistake a cached run for a new experiment. Paid calls occur.

| Check | Expected evidence |
|---|---|
| Generation | 8 + 8 + 4 actual comparison answers, no missing rows; N01 smoke and N02 extra case are one separate answer each |
| Evaluation | Valid Groundedness/Relevance scores and reasons for all 20 comparison answers, plus both metrics for smoke and extra case |
| Portal | Correct project/eval/run IDs; per-case results accessible |
| Comparison | Same dev, model, policy, and judge contract |
| Freeze | Candidate and holdout prompt hashes match |
| Decision | Saved gate with reasons; BLOCK is a valid learning outcome |
| Extra case | N02 validates and is generated/judged separately |

Running the whole guide afresh, including smoke and extra case, produces **22 answers × 2 metrics = 44 scores**. This is not a count of internal evaluator model calls, tokens, or billed units.

**Do not require V2 to win.** V1 may already answer well, or V2 may introduce another problem. Fix environment/SDK errors before class, but never fabricate results.

In [one recorded complete-path run](complete-lab.md#results), genuine V1 failure was followed by completed user follow-ups and every required metric—including Relevance—passed on fresh final scenarios. This does not guarantee a participant's new result or this introductory rehearsal. Earlier failure/validation records are retired. Distinguish scripted evaluation-user turns from actual human production approval.

## Facilitate by checkpoint

| Stage | Learning goal | Completion evidence |
|---|---|---|
| 0 | Fluency is not correctness | Policy-based A/B judgment |
| Setup | Account, region, identity, and deployment names matter | A real generated and evaluated smoke answer |
| 1 | Define expectations before results | D02 behavior and fixed thresholds |
| 2 | Generation is separate from judging | Eight baseline answers and code checks |
| 3 | Judge versus independent judgment | D04 before/after judgments and matching portal row |
| 4 | State a hypothesis; inspect existing `my-v2.txt`, then reuse or edit it | Disclose actual changes; compare cases and save D06 review |
| 5 | Test an unchanged candidate on new questions | Holdout, H04 review, and gate decision |
| 6 | Inspect existing N02, then reuse it or edit both amount occurrences before validation | Distinguish reuse/editing/new authorship; save N02 result and final judgment |
| Finish | Preserve evidence and resources | Retention and cost records |

Keep introductory scope at one project, one deployment, two judge metrics, and one improvement loop. During cloud waits, revisit policy and the reasoning behind answers already examined rather than expanding features.

When `judge` exits **3**, resume with the entire original command. For collection/persistence `ERROR:`, fix the cause before resuming the same command. Its default 300 seconds is a polling budget, not a deadline for evaluation success. Low scores and gate BLOCK are valid quality outcomes; missing scores/IDs/reasons and authentication/execution errors are different. After adding human review, rerun the same `gate`, not generation or judging. Use the [explicit DEMO switch](setup.md#switch-to-demo) if needed.

LIVE and DEMO share activity numbers 0–6. Additional **pre-judge judgments on baseline D01/D06**, or the [regression trap](offline.md#regression-trap), are optional practice. They do not make the main path's **candidate D06 and holdout H04 reviews optional**. Agreement on one case does not validate judge accuracy.

## Case explanations: let participants decide first

| Case | Key point |
|---|---|
| D01 | Current official limit is 200000; draft 240000 is not applicable |
| D02 | Exceeding the limit means prior approval, not automatic acceptance or blanket prohibition |
| D03 | Actual travel date controls; earlier limit is 160000 |
| D04 | No overseas amount is provided; “unknown, ask Finance” can be correct |
| D05 | Domestic business class is prohibited; a lodging limit is irrelevant |
| D06 | Following a request to fabricate approval is not good business behavior |
| D07 | “At most” includes the exact boundary |
| D08 | Without the travel date, ask rather than assume |
| H01 | One KRW over is still over the limit |
| H02 | The day before the policy change uses the earlier limit |
| H03 | A different overseas city does not justify guessing |
| H04 | Reimbursement date is not travel date; DEMO intentionally includes this failure |

## Common misconceptions

| Participant question | Response |
|---|---|
| V1 passed everything; did the exercise fail? | No. Keep the evidence and check whether the change preserves behavior. |
| Can I rerun V2 until its score rises? | Not as a fair comparison. Define repetitions and aggregation in advance for a new experiment. |
| Does 4/5 mean 80% accuracy? | No. A score and a dataset pass rate are different quantities. |
| Should an “unknown” answer always get low Relevance? | Not when policy genuinely lacks the answer. Compare the judge with domain expectations. |
| Do citations prove grounding? | An ID and actual evidential support are different things. |
| Can a higher average override a critical regression? | No. |
| Can I adjust holdout and call it unseen again? | No; prepare a new independent holdout. |
| Does READY authorize deployment? | No. Production risk, sample coverage, security, performance, and approvals are separate. |

## Final presentations

Ask for a concrete case and sentence, the changed instruction, both improvements and regressions, correct treatment of unseen questions, and a clear distinction between LIVE evidence and authored examples.

<a id="complete-checkpoints"></a>
## Dedicated complete-RAG checkpoints

Participants use the checkpoints in sections 1–8 of the [complete guide](complete-lab.md) and the generated reports. After shared setup 1–7, confirm they return to complete-path Search setup, not introductory activity 1.

| Stage | Evidence for completion or holding |
|---|---|
| Setup | Check `eval-model` / `gpt-6-luna` / `2026-09-22` before adding resources. Skip creation for existing services; distinguish user, project, and Search identities |
| Sharing scope | Reuse an authorized Basic service, but separate search-object names and local folders by participant/experiment. This is not security isolation; do not silently update existing objects |
| Retrieval | Actual 1536-dimensional vectors and `modelQueryPlanning` evidence. Preview LLM planning is distinct from GA minimal/extractive retrieval or hosted-agent execution. The Optional RAG index is not required |
| Calibration | Ten positive/negative control results. Distinguish failure from waiting using [complete-path resumption](complete-lab.md#resume) |
| Improvement | Preserve recorded V1 D02 failure; replay/planned-dev use the same candidate; personally review initial D04/D08 prose |
| Freeze | Both dev stages meet 100% criteria with identical instructions, models, and follow-up contracts. Otherwise record failure and unperformed stages |
| Fresh questions | Eight new template-based scenarios after freeze; N05/N06 dialogue review and the participant's own acceptance result |
| Finish | Distinguish initial field checks from semantic judgment, and automated acceptance from production approval. Preserve failures/blocks; check Basic capacity, embedding, planning, generation, and judge costs |

Do not present the author's 100% result as the participant's expected answer. `intermediate_safe` covers initial fields only, not automated proof of whole-dialogue safety.

Further work is outside this introductory loop: domain-reviewed representative data, high-risk cases, repeated experiments, judge calibration, regression CI, and feedback from production failures. Retrieval, tool use, and agent operations require their own evidence; this fixed-context answer workshop does not measure them.

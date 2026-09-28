**English** | [한국어](../facilitator.md)

# Facilitator guide

[Participant guide](../../README.md) · [Setup](setup.md) · [Worksheet](../../WORKSHEET.en.md)

Teach **evidence-based judgment**, not just tool operation. A useful final statement is “D06 introduced an approval fabrication, so I would hold the change,” not just “the score increased.”

Participants follow one main guide: activity 0, setup, activities 1–6, and resource retention. Use checkpoints rather than a fixed timetable. Keep LIVE and authored DEMO evidence distinct. English documentation uses the same Korean experimental inputs as the Korean guide; use the [policy translation](policies.md) to explain them without changing the experiment.

## Before the workshop

- [ ] Participants can access the repository or an authorized ZIP.
- [ ] Each new-resource participant has the correct Entra account, active subscription, and active Owner permissions.
- [ ] Activity 0 occurs before installation; participants then perform their own setup without shared passwords or prefilled credentials.
- [ ] Use one dedicated group/project and one `eval-model` deployment of **`gpt-6-luna`**, in **`swedencentral`**.
- [ ] Check each resource's region separately and match the project identity to parent-resource IAM. Owner/model lookup alone is insufficient.
- [ ] Verify Chat Completions, Structured Outputs, judge support, project access, and region availability.
- [ ] Each participant completes the one-case smoke generation/evaluation.
- [ ] Account for shared subscription TPM/RPM, concurrent judges, delays, and costs.
- [ ] If organizational approval blocks LIVE, clearly label any temporary DEMO practice.
- [ ] Use separate local output folders; only one operator writes a given run.
- [ ] Participants can distinguish originals, working copies, and generated evidence.
- [ ] Confirm the `평가 완료` count and report reasons, not only portal Completed/Pass.
- [ ] Verify participants can reopen a terminal and resume without regenerating completed work.
- [ ] Retain created resources and record costs; never execute deletion merely because a session ended.

Shared environments are not the default. If unavoidable, define permissions, quotas, output ownership, and retention scope first. Never apply dedicated-group deletion instructions to shared infrastructure.

<a id="rehearsal"></a>
## Rehearse the real environment

Local and SDK transport tests are **not actual Azure execution**. For a full rehearsal, follow the participant guide in a clean working/output location; do not delete previous `results/` or mistake a cached run for a new experiment. Paid calls occur.

| Check | Expected evidence |
|---|---|
| Generation | 8 + 8 + 4 actual answers, no missing rows |
| Evaluation | Valid Groundedness/Relevance scores and reasons for all 20 |
| Portal | Correct project/eval/run IDs; per-case results accessible |
| Comparison | Same dev, model, policy, and judge contract |
| Freeze | Candidate and holdout prompt hashes match |
| Decision | Saved gate with reasons; BLOCK is a valid learning outcome |
| Extra case | N02 validates and is generated/judged separately |

**Do not require V2 to win.** V1 may already answer well, or V2 may introduce another problem. Fix environment/SDK errors before class, but never fabricate results.

The [completed workflow](complete-lab.md) starts with a genuine V1 failure, completes necessary user follow-ups, and passes every required metric—including Relevance—on new final scenarios. Earlier failure/validation records are retired. Distinguish scripted evaluation-user turns from actual human production approval.

## Facilitate by checkpoint

| Stage | Learning goal | Completion evidence |
|---|---|---|
| 0 | Fluency is not correctness | Policy-based A/B judgment |
| Setup | Account, region, identity, and deployment names matter | A real generated and evaluated smoke answer |
| 1 | Define expectations before results | D02 behavior and fixed thresholds |
| 2 | Generation is separate from judging | Eight baseline answers and code checks |
| 3 | Judge versus independent judgment | D04 before/after notes and matching portal row |
| 4 | One controlled change; inspect regressions | Comparison and D06 review |
| 5 | Test an unchanged candidate on new questions | Holdout, H04 review, and gate decision |
| 6 | Add a well-defined case | N02 validation/result and four final sentences |
| Finish | Preserve evidence and resources | Retention and cost records |

Keep scope at one project, one deployment, two judge metrics, and one improvement loop. During cloud waits, complete the worksheet rather than expanding features.

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

Further work is outside this introductory loop: domain-reviewed representative data, high-risk cases, repeated experiments, judge calibration, regression CI, and feedback from production failures. Retrieval, tool use, and agent operations require their own evidence; this fixed-context answer workshop does not measure them.

**English** | [한국어](WORKSHEET.md)

# Workshop record: keep a judgment at every checkpoint

Follow `README.md` for LIVE or `docs/en/offline.md` for DEMO. **Activities 0–6 have the same numbers in both guides and this worksheet.** Sections 0–1 and 2–3 group related notes. Paths are relative to the folder containing `lab.py`.

**Save a copy as `results/my-worksheet.md`**, then edit that copy. When switching from LIVE to DEMO, preserve the LIVE worksheet and use `results/my-worksheet-demo.md`. Scores, run IDs, and hashes already live in result files; record **cases and reasons**, not another copy of every score. Mark unperformed work honestly. Do not record passwords, keys, or tokens.

Write your A/B judgment before installation, copy it into this file during setup, fill in D02 in activity 1, record D04 before and after judging, then complete comparison, gate, extra-case, and retention notes.

## Setup

For DEMO-only work, mark Azure fields **not applicable**. If you started LIVE first, record any created resources and the switch checkpoint.

| Field | Your record |
|---|---|
| Date / LIVE or DEMO | |
| Signed-in account (`account` in the documented `az account show` query) | |
| Tenant ID | |
| Subscription ID | |
| Dedicated or shared environment / shared owner | |
| Resource group | |
| Foundry resource / project | |
| Project managed identity Object (principal) ID | |
| Region / model name and version | |
| Deployment name / type | |
| Retention decision / next check date or condition | |
| Last completed checkpoint / complete next command | |

The LIVE target is **`gpt-6-luna`**, **`swedencentral`**, deployment **`eval-model`**. Record actual verified values and versions. **Retain all created resources**; if no deletion date is planned, write **“retain until a separate request.”** Do not mark uncreated resources or unrun evaluations as complete.

Fill in the final row before stopping, including `--like` when applicable. If you forgot your checkpoint, use `docs/en/setup.md` and its result-file resume table.

## 0–1. What makes an answer good?

- Initial A/B choice → judgment after reading policy, and why:
- D02 expected behavior and what must never be advised:

**Fixed criteria:** candidate and holdout business/each judge pass rate ≥80%; each judge score ≥4/5; zero critical failures, regressions, or missing evidence; actual human review in candidate and holdout, with no rejection. Change only the prompt, not the model, policy, questions/expectations, judge, or thresholds.

## 2–3. D04: your judgment before the judge

- **Before judging:** my pass/fail and policy-based reason:
- **After judging:** Groundedness ___/5; Relevance ___/5. Agreement/disagreement and why:

Keep the original verdict. Match the same question, answer, and scores in the portal and local results. Skip portal checks in DEMO.

## 4. What changed, and what happened?

- Hypothesis: to reduce ___ in case ___, change ___.
- Actual edit in `prompts/my-v2.txt` / V2 reused unchanged / authored DEMO example difference:
- Improved or regressed dev case IDs and reasons, or no change:

Read `results/candidate/comparison.md` for LIVE or `results/demo-candidate/comparison.md` for DEMO, plus each report. **Save D06 using the guide's `review` command.** A worksheet note alone does not create `reviews.json`.

## 5. Unseen questions and adopt/hold

- Holdout case examined and judgment:
- Gate result / adoption-review or hold recommendation / strongest evidence:

Save H04 through `review` too. Do not change `fail` to `pass` merely to remove `BLOCK`. If you changed the prompt after inspecting holdout, prepare **a new holdout** for the next experiment.

## 6. Your extra question

- N02: edited example / original question / unchanged example:
- Intended failure mode / data validation / actual answer and scores, or not executed:
- Another work-domain question / expected behavior / forbidden behavior / evaluation method:

Design the other-domain case only; do not feed it to the travel checker. In DEMO, explicitly record that N02 generation and judging were not run. If reusing an N02 created in LIVE, say so.

## Final four sentences: complete only your path

**LIVE**

> In case ___, I found ___. / No error was found in these questions.<br>
> After changing ___, the same questions showed ___ and unseen questions showed ___.<br>
> Based on ___, I recommend adoption review / holding the change.<br>
> In my work, I would first add cases testing ___.

**DEMO**

> In authored example ___, I found ___.<br>
> The V1/V2 examples showed ___ on the same questions and ___ on holdout.<br>
> Based on ___, I would hold the example change. No real prompt improvement was measured.<br>
> In my work, I would first add cases testing ___.

## Finish

- Retained resources / why not deleted / next check condition:
- Only if a later deletion was separately authorized: scope, completion, and time:
- Reported cost / still awaiting cost reporting:
- Completion checklist / unperformed items and why:

Keep the worksheet and `results/` locally. **Retain Azure resources for this LIVE path.** Respect a shared environment owner's scope. DEMO-only runs have no Azure resources or charges. AI-assisted verdicts must be labeled `assistant`; **actual human review remains incomplete** unless a person performed it.

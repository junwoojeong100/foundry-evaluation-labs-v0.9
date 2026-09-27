**English** | [한국어](../reference.md)

# Commands, contracts, troubleshooting, and sources

[Main guide](../../README.md) · [Setup](setup.md) · [Retention](cleanup.md)

The main guide is self-contained. Read this reference only for a specific question or failure. In the default path, you own the dedicated environment; organizational policies and shared infrastructure remain subject to their owners.

## Eight commands

| Command | Purpose | Paid calls |
|---|---|---|
| `doctor` | Local checks; `--live` verifies authentication/deployment lookup | No generation/evaluation |
| `validate-data` | Validate JSONL fields and values without modifying it | None |
| `run` | Generate/save answers and perform code checks | Unsaved LIVE answers only |
| `judge` | Evaluate saved answers with two metrics | A newly submitted LIVE evaluation |
| `inspect` | Read one case, answer, expectations, and scores | None |
| `compare` | Compare matching dev runs and regressions | None |
| `review` | Save a verdict/reason with human or assistant attribution | None |
| `gate` | Apply the fixed educational criteria | None |

Use `--help`, for example:

```bash
python lab.py run --help
```

Exit codes are **0** complete, **1** input/environment/execution error, **2** quality gate BLOCK, **3** evaluation still processing, and **130** interrupted. A successful `run` can contain wrong answers.

`평가 완료: N개 답변 × 2개 지표 (점수·이유 저장)` means all case IDs, scores, and reasons were validated and `judge.json`/`report.md` were saved. Low scores are valid results. Remote `completed` or file existence alone is not this checkpoint. Reusing saved results validates them but does not judge again.

<a id="data-contract"></a>
## One JSONL case

```bash
python lab.py validate-data data/my-case.jsonl
```

`DATA OK: 1 case(s)` validates one row's structure, not the correctness of its expectation. It requires no Azure authentication and does not modify inputs or create results.

| Field | Meaning |
|---|---|
| `id` | Unique case ID, such as `N02` |
| `category` | Failure mode being tested |
| `critical` | Boolean; critical cases are P0 |
| `query` | Employee question |
| `expected_decision` | `allowed`, `needs_approval`, `not_allowed`, `unknown`, or `needs_info` |
| `expected_limit_krw` | Integer policy limit or `null` |
| `expected_citations` | Array of necessary official IDs: `TRAVEL-CURRENT`, `TRAVEL-PREVIOUS`, `SCOPE` |
| `ground_truth` | Human-readable expected behavior and reason |

Use one object per line, lowercase JSON booleans/null, and numbers without commas or quotation marks. Expected answers can be wrong too; check them against policy before generating responses. Neither answer generation nor these two judges receives the `expected_*` fields or `ground_truth`.

The English guide is a translation of the workflow, not a translated experiment. The shared source data/prompts and emitted CLI messages remain Korean. Use the [reading translation](policies.md); changing model input language requires a separate controlled experiment.

## What each check does

| Signal | Contract |
|---|---|
| `schema` | Exactly four output fields; allowed decision, integer/null limit, string-array citations, nonempty answer |
| `decision` | Exact match with the expected decision |
| `limit` | Exact expected limit; strings and booleans are not numbers |
| `citations` | Exact expected ID set; missing, extra, or duplicate IDs fail |
| Business pass | All four checks pass; refused/truncated output fails |
| Groundedness | LLM judgment of support in the supplied context |
| Relevance | LLM judgment of how the answer addresses the question |
| Human review | A person's comparison of policy, explanation, and business risk |

These decisions do not actually execute approvals, payments, or reimbursements.

The code cannot understand an explanation that contradicts otherwise correct fields. Conversely, the judge may overlook exact IDs or date boundaries. An appropriate “unknown” or request for a missing date can also receive a low generic Relevance score.

Not measured here: retrieval recall/NDCG, tool-call accuracy, hosted-agent behavior, multi-turn dialogue, broad security/red-team coverage, execution authorization, or production SLA.

## Controlled comparisons

- Generation gets prompt, policy, and question only.
- Judges evaluate the **whole saved raw answer JSON**, not a replacement or only its prose.
- Groundedness gets the same context used during generation. Relevance gets question and answer, without policy or `ground_truth`.
- Before/after comparison requires the same mode, dev questions/expectations, context, deployment and reported model versions, generation settings, and business-check version.
- `judge --like` reuses the baseline evaluation group, evaluator versions, and judge contract. Do not change deployments during the experiment.
- A check or judge threshold result moving from pass to fail is a regression, even if the answer already failed another check.
- Missing, nonfinite, out-of-range, or incomplete scores are not valid evidence. Every expected case and both metrics must exist with reasons.
- Dev and holdout are not a before/after pair. Duplicate IDs or identical questions across those splits are rejected.

Hashes detect accidental evidence changes; they are not signatures or protection against malicious rewriting. Eight dev and four holdout cases are a small educational sample, not statistical proof. Do not rerun until a preferred outcome appears.

The service's default pass threshold may be **3**, while this workshop uses **raw score ≥4** locally. A 4/5 score is not 80% accuracy.

<a id="self-check"></a>
## Five understanding checks

1. Why is fluency insufficient?
2. What do code, judge, and human each check?
3. What must remain fixed in a before/after comparison?
4. Why hold a change even if its average improves?
5. What is required after changing a prompt based on holdout?

<details>
<summary>Explanation after answering</summary>

1. A fluent answer can give the wrong limit or invent approval.
2. Code checks explicit fields; the judge checks meaning; a person examines policy and business risk. None guarantees the others.
3. Questions/expectations, policy, model, generation settings, judge, and thresholds. Only the prompt changes.
4. An important new failure is not cancelled by gains elsewhere.
5. A new independent holdout, because the old one influenced development.

</details>

## Gate contract

| Area | Requirement |
|---|---|
| Inputs | Complete dev baseline/candidate and a distinct holdout created from that candidate using `--frozen` |
| Business | Candidate and holdout each ≥80% |
| Judge | Complete evidence for all three runs, matching contracts; each candidate/holdout metric pass rate ≥80% |
| P0 | Zero business or judge failures on critical candidate/holdout cases |
| Regression | Zero dev business-check or judge pass-to-fail regressions |
| Human | At least one valid human review in candidate and holdout; no latest human rejection |

Reviews append rather than overwrite history. Only the **latest human verdict per case** counts toward that requirement. Reviews do not train the model or change judge scores.

LIVE `READY_FOR_HUMAN_REVIEW` is an educational signal for a later release review, not automatic production approval. DEMO never reports LIVE readiness.

<a id="assisted-review"></a>
### AI-operated review is not human approval

The default reviewer is `human`. AI-operated walkthroughs must use **`--reviewer assistant`**:

```bash
python lab.py review results/candidate D06 --reviewer assistant
```

For noninteractive use, also supply `--verdict` and `--note` after actually examining the answer. Use the same attribution for H04.

Assistant reviews are saved but **do not meet the human-review requirement or overwrite human verdicts**. With only assistant reviews, the gate remains BLOCK. A person can later append their own review and rerun the gate. Do not relabel AI judgments as human just to pass.

Older records without a `reviewer` field retain their legacy human interpretation. This educational field is self-reported attribution, not identity verification or authorization proof.

## Saved evidence

| File | Contents |
|---|---|
| `run.json` | Cases, context/prompt snapshots, hashes, mode, deployment, responses, latency and generation usage |
| `report.md` | Business checks, judge scores/reasons, per-case and category evidence |
| `judge.json` | Foundry or explicitly authored scores, tied to the response hash and judge contract |
| `foundry-job.json` | Remote IDs, current phase, and fixed evaluator contract |
| `foundry-output.json` | All pages of original remote result rows |
| `reviews.json` | Reviewer type, verdict/reason, and response hash |
| `comparison.md` / `.json` | Matching-dev differences and regressions, in candidate |
| `gate.md` / `.json` | Decision and reasons, in candidate |

Observed generation p95 is not a production SLA. Generation token totals exclude judge consumption and do not replace the billing record.

The workshop sends small datasets inline using **`file_content`** rather than registering a dataset asset. Production workflows need versioning, access control, and retention policies.

### Foundry field mapping

| Evaluation field | Source | Mapping |
|---|---|---|
| `id` | Original case ID | Correlates output with the case |
| `query` | Employee question | Both judges' `{{item.query}}` |
| `context` | Saved full policy | Groundedness's `{{item.context}}` |
| `response` | Saved `raw_response` string | Both judges' `{{item.response}}` |

Original question JSONL has no generated `response`. Uploading it directly is not equivalent to judging the saved model outputs.

<a id="portal-results"></a>
## Find and compare portal results

Open the **Foundry report URL** from `judge`, or use the correct account/project's **Build → Evaluations**. If account selection appears, match the CLI identity.

Use `eval_id` and `run_id` from `foundry-job.json`. Find a Completed run, then match the original question or ID rather than row position. Compare its actual answer, raw scores, and reasons with `inspect`/`report.md`; do not submit another evaluation merely to find results.

With `--like`, baseline and candidate share an **evaluation ID** but have different **run IDs**. The first list may show one **`straightforward-…` group**, not two independent rows.

1. Open the **group name**, not only Last run.
2. Under **Evaluation runs**, select only **`v1-dev-…` and `my-v2-dev-…`**, then **Compare runs**. Do not select holdout/extra runs. **Analyze Results** is a different optional feature.
3. Set **Baseline** explicitly to **`v1-dev-…`**. The first-selected candidate may otherwise be the reference.
4. Read averages/statistics, then inspect the same case in both detailed runs and the local comparison.

**Too few samples / Inconclusive** means the difference is not established by this small sample. Record the comparison URL and original IDs. If comparison is unavailable, inspect runs side by side.

Portal Overall score/Pass may use threshold 3. Portal **100%** can therefore coexist with a lower local score-4 pass rate. The same raw scores with different thresholds are not a collection error. Target, generation latency, or cost fields may be blank for pre-generated-answer evaluations; use local generation logs and Cost Management instead.

<a id="troubleshooting"></a>
## Troubleshooting

| Symptom | Action |
|---|---|
| Private repository inaccessible | GitHub access is separate from Azure Owner; obtain authorized access/ZIP. |
| Subscription missing | Check account and tenant, including guest-directory sign-in. |
| Owner cannot create/assign | Check active scope/PIM, policies, deny assignments, and conditional access; do not bypass controls. |
| Provider not registered | Register `Microsoft.CognitiveServices` in the intended subscription and wait. |
| Cannot find `python` or `lab.py` | Open the correct folder and reactivate `.venv`. |
| `SyntaxError` at `>>>` | Exit the Python REPL; use a shell terminal. |
| Edits are not reflected | Edit/save the local copy, check paths, and do not overwrite completed results. |
| PowerShell activation blocked | Use `.venv\Scripts\python.exe`; do not change organizational policy. |
| Missing/mismatched LIVE packages | Install the pinned `requirements.txt` in `.venv`; do not arbitrarily upgrade. |
| Example config rejected | Replace the project endpoint and use actual deployment names; do not use model names. |
| Only a classic connection string/model endpoint exists | A new Foundry project endpoint is required. |
| `config.json` not found | Check its folder and `.json.txt` extensions. |
| `my-v2.txt` missing | Save the V2 copy under the exact documented filename. |
| JSONL validation fails | Fix the identified line/field; retain all eight fields and valid types. |
| Extra-case count is not one | Remove unintended extra rows; keep N02 only. |
| `review` appears stuck | It is waiting for verdict and reason; confirm `검토 저장`. |
| Worksheet review is not counted | Save it using `review`, not only in the worksheet. |
| Only AI reviews exist | A real human review is still required; do not relabel the AI record. |
| 401/authentication failure | Sign in with the intended user and tenant; do not paste keys into code. |
| 403 despite Owner | Check Foundry User for both user and project identity at parent scope; allow propagation. |
| Private Link/public-access restriction | Use an approved VNet/VPN/environment; do not disable the firewall. |
| Model 404 | Check the project and **deployment** name; default is `eval-model`, not `gpt-6-luna`. |
| JSON Schema/parameter 400 | Verify model support for Chat Completions, Structured Outputs, and generation options. |
| `finish_reason=length` | Output is truncated. Fix output-budget compatibility in a new experiment, not by accepting the row. |
| 429 | Check shared TPM/RPM and judge load; wait, then resume incomplete work only. |
| Model/region/quota unavailable | Follow [availability checks](#model-availability). |
| Resource-group history shows a failed `PolicyDeployment` while the model works | Inspect that deployment separately. A diagnostic policy may reference a missing central Log Analytics workspace. Preserve the warning and refer it to the policy owner; do not delete history or disable policy to manufacture success. |
| Judge exit 3 | Repeat the same entire command, preserving `--like`, to retrieve the same job. |
| Remote completed, no local completion message | Wait for collection/validation; preserve IDs and fix any explicit error. |
| Missing result ID, score, or reason | Preserve raw output/job files; investigate the SDK/service contract. Do not pass missing evidence. |
| Only one compared run has scores | Complete the other judge using the fixed contract. |
| Portal run missing/different scores | Match tenant/project/IDs and raw scores; distinguish threshold differences. |
| Input/model/judge contract mismatch | Inspect changed settings and start a separate comparable experiment. |
| Gate exit 2 | Read BLOCK reasons; this is an intentional quality decision. |
| DEMO rejects edited data/prompt | It only replays fixed fixtures; use LIVE for a separate measured experiment. |
| Forgot the last checkpoint | Use the worksheet and [resume table](setup.md#resume-checkpoints). |
| Deletion incomplete | Follow [scope/lock/status checks](cleanup.md); a request is not completion. |

When sharing errors, include only the command, checkpoint, error type, and necessary sanitized identifiers. Do not publish credentials, full customer data, or unredacted recordings.

<a id="managed-identity-access"></a>
## If the project identity cannot be selected

1. Open the project's Azure resource. Its ID ends in `/accounts/ACCOUNT/projects/PROJECT`.
2. Copy **Identity → System assigned → Object (principal) ID**, or `identity.principalId` from JSON view. Do not use the parent account's identity.
3. Copy the parent resource ID ending at `/accounts/ACCOUNT`.
4. Confirm the role is missing, then run this once with real values:

```bash
az role assignment create --assignee-object-id "YOUR-PROJECT-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

The GUID is Foundry User, formerly Azure AI User. Verify member and scope in IAM. If the project lacks a system identity, enable **Identity → System assigned → On → Save** through the authorized process; do not replace it with shared credentials.

<a id="model-availability"></a>
## Model, region, and quota

The target is **`gpt-6-luna` in `swedencentral`**, but the actual subscription catalog and deployment screen determine availability.

1. Confirm the exact model name/version in the correct account and region. Do not silently substitute another name.
2. Check supported SKUs and quota separately, including Global Standard availability.
3. If quota is unavailable, request an increase or agree on a new experiment with the owner. Do not reduce others' deployments or silently switch regions/models.
4. Keep deployment name `eval-model` and prove compatibility with the [smoke check](setup.md#smoke).

Do not assume identical Chat Completions, JSON Schema, generation-option, or judge support. Reasoning-token usage can cause truncation despite short final prose. Changing output settings requires a new baseline, not a mid-experiment edit. Do not add a model router or partner model implicitly.

If blocked, record it and optionally [switch explicitly to DEMO](setup.md#switch-to-demo). Before an agreed region change, check [evaluation support](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network) and [model availability](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability). Retain already-created resources.

<a id="resume"></a>
## Interrupted work and remote-ID recovery

Completed commands read saved evidence. Partial generation skips saved rows; a response interrupted before persistence may be billed again. Existing remote `run_id` values are retrieved, not resubmitted. Closing the terminal does not cancel cloud work. Use a new output folder when changing inputs.

If moving the repository broke the virtual environment, recreate **only `.venv`**, after preserving anything you intentionally placed there. Do not delete configuration, results, or your prompt/question copies.

macOS / Linux:

```bash
python3 -m venv --clear .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python lab.py doctor
```

Windows / PowerShell:

```powershell
py -3 -m venv --clear .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python lab.py doctor
```

Use the direct virtual-environment Python path if activation is prohibited.

**Ambiguous creation after disconnection:** `phase` may be `creating-eval` or `creating-run` without a saved ID. Do not automatically create another potentially billable job.

1. Preserve the files. Use the local `run_id` to find `straightforward-<first 8 characters>` or `<prompt>-<split>-<first 8 characters>` in the portal. Remote `workshop_run` metadata must match.
2. Only after positively identifying the exact job, restore missing IDs in `foundry-job.json`. Use `ready` if only the eval exists, or `submitted` if the run exists, then repeat the original judge command.
3. If existence is uncertain, do not resubmit. Request the owner's investigation or use a separate DEMO path. Never edit scores, evidence hashes, or contracts to manufacture completion.

For an explicitly terminated failed/canceled run, fix its cause first. An owner can preserve its original ID/status, verify termination, then set only `run_id` to `null` and `phase` to `ready` to resubmit the same saved responses under the same eval/contract. This is paid reevaluation, not score-shopping.

## SDK and verification scope

Documentation checked **2026-09-27**.

| Item | Selection |
|---|---|
| Python | 3.10+ syntax; local checks used 3.14 |
| Model/region | `gpt-6-luna` / `swedencentral`; both deployment fields `eval-model` |
| Foundry SDK | `azure-ai-projects==2.7.0` |
| Authentication | `azure-identity==1.25.3`, explicitly `AzureCliCredential` |
| OpenAI client | `openai==3.16.2`, a compatible pin, not a claim of newest release |
| Generation | `AIProjectClient.get_openai_client()` → `chat.completions.create`, JSON Schema |
| Evaluation | `evals.create`, run creation/retrieval, and all output pages |
| Evaluator catalog | `project.beta.evaluators.list_versions`; chosen versions are fixed |

Direct dependencies are pinned, not a full transitive/hash lockfile. Catalog checks confirmed `gpt-6-luna` version `2026-09-22`; the rehearsal deployed GlobalStandard 60K TPM. DataZoneStandard was only listed, not deployed.

Local tests check authored examples, gate behavior, missing/tampered evidence, docs/JSONL contracts, and installed SDK request/response shapes with an in-memory transport. They do not by themselves validate real permissions, capacity, billing, or current portal UI.

```bash
python -m unittest discover -s tests -v
```

SDK tests run when dependencies are installed; otherwise only those tests are skipped. Complete your own smoke check and, for a class, [a real rehearsal](facilitator.md#rehearsal).

<a id="live-verification"></a>
### September 27, 2026: one actual LIVE rehearsal

This is **one execution**, not expected scores or a production guarantee. New dedicated resources were created in Sweden Central, the user and project identity received parent-scoped Foundry User, and `gpt-6-luna` `2026-09-22` served generation and judging.

**22 responses, 44 metric items, five completed remote evaluation runs** were validated and saved. Structured outputs had no truncation or output errors.

| Run | Answers | Business pass | Groundedness ≥4 | Relevance ≥4 |
|---|---|---|---|---|
| Smoke N01 | 1 | 0/1 | 1/1 | 1/1 |
| Baseline dev | 8 | 7/8 | 8/8 | 7/8 |
| Candidate dev | 8 | 8/8 | 8/8 | 6/8 |
| Frozen holdout | 4 | 4/4 | 4/4 | 2/4 |
| Extra N02 | 1 | 1/1 | 1/1 | 1/1 |

V2's copy gained one sentence: until the actual travel date is known, do not list conditional date-specific limits/decisions, and cite only SCOPE. This targeted D08 before candidate/holdout generation.

N01 correctly rejected the draft but cited it, so exact citation checks failed while both judges scored 5. D08's business check improved while Relevance fell **5→3**. D04 remained 3; H03/H04 scored 2/3. The generic judge penalized correct abstention or missing-information requests. The original scores and thresholds were retained.

Portal N01/D04 rows matched local evidence. **Pass: 3** differed from the local threshold. Dev statistical comparison reported **Too few samples**.

**Final gate: BLOCK. Actual human review remains incomplete.** D04/D06/H04 were labeled `assistant`, not human approval. Relevance regression, below-threshold rates, critical-case failures, and missing actual human review all remained visible. A future experiment needs domain-informed judge calibration and a new holdout, not score manipulation.

The operator retained local raw results, remote IDs, worksheet, comparison/gate, and `results/live-verification.json`. These ignored local artifacts and `config.json` are not shipped in a fresh clone. Keep your own evidence.

During that original rehearsal, the headless profile lacked authentication, so the authenticated regular Playwright session was used for portal checks. The later headless video-production workflow is described separately in the [recording notes](../media/README.md). No credentials are published.

All Azure resources and evaluation records were retained. Cost Management succeeded but returned no reported rows yet; this is **not proof of free use or zero final cost**.

## Official sources

| Source | Topic |
|---|---|
| [Create a Foundry project](https://learn.microsoft.com/azure/foundry/how-to/create-projects) | New project and CLI prerequisites |
| [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) | User/project identity and role scope |
| [Deploy models](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/deploy-foundry-models) | Catalog, deployment names, types |
| [Azure-sold models](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure) | Model capabilities |
| [Delete a resource group](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group) | Scope, locks, irreversibility |
| [Budgets and alerts](https://learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets) | Alerts and reporting delays |
| [Cloud evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation) | Prerequisites and workflow |
| [Dataset evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-datasets) | Inline data and mappings |
| [Evaluation results](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-results) | States, pages, scores, reasons |
| [Portal comparison](https://learn.microsoft.com/azure/foundry/how-to/evaluate-results) | Runs and statistical comparison |
| [RAG evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/rag-evaluators) | Groundedness/Relevance contracts |
| [Groundedness SDK example](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/evaluations/agentic_evaluators/sample_groundedness.py) | Python API example |
| [Structured Outputs](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/structured-outputs) | JSON Schema output |
| [Regions and limits](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network) | Availability and networking |

Do not mix the new Foundry API with classic `azure-ai-evaluation` connection strings, authentication, mapping, or response contracts.

**English** | [한국어](../reference.md)

# Commands, contracts, troubleshooting, and sources

[Main guide](../../README.md) · [Setup](setup.md) · [Retention](cleanup.md)

The main guide is self-contained. Read this reference only for a specific question or failure. In the default path, you own the dedicated environment; organizational policies and shared infrastructure remain subject to their owners.

The command table below describes introductory `lab.py`. For `advanced_lab.py` status and fixed output paths, use [complete-path resumption](complete-lab.md#resume). Remote evaluation ID recovery below distinguishes each path's files.

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

Exit **2** means a quality decision only when **`BLOCK` is printed**. With `usage:` / `error:`, it instead indicates missing arguments or invalid options; correct and rerun the command.

`평가 완료: N개 답변 × 2개 지표 (점수·이유 저장)` means all case IDs, scores, and reasons were validated and `judge.json`/`report.md` were saved. Low scores are valid results. Remote `completed` or file existence alone is not this checkpoint. Reusing saved results validates them but does not judge again.

<a id="data-contract"></a>
## One JSONL case

```bash
python lab.py validate-data data/my-case.jsonl
```

`DATA OK: 1 case(s)` validates one row's structure, not the correctness of its expectation. It requires no Azure authentication and does not modify inputs or create results.

| Field | Meaning |
|---|---|
| `id` | Unique case ID starting with a letter, such as `N02` |
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

Not measured by the **fixed-policy introductory path**: retrieval recall/NDCG, tool-call accuracy, hosted-agent behavior, multi-turn dialogue, broad security/red-team coverage, execution authorization, or production SLA. Minimal-RAG retrieval metrics and complete-path dialogue/acceptance criteria belong to their dedicated guides, not the introductory gate below.

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

The file table and mappings below describe **introductory `lab.py`**. For minimal RAG, use [retrieval/input evidence](optional-rag.md#evidence); for complete RAG, use [stage-specific artifacts](complete-lab.md#resume). Minimal RAG passes retrieved context rather than the whole policy, and complete RAG has a separate dialogue evaluation contract.

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
| Provider not registered | In the intended subscription's Resource providers, check `Microsoft.CognitiveServices` for Foundry or `Microsoft.Search` for Search creation. An authorized administrator registers only the provider you need. |
| Cannot find `python` or `lab.py` | Open the correct folder and reactivate `.venv`. |
| `SyntaxError` at `>>>` | Exit the Python REPL; use a shell terminal. |
| Edits are not reflected | Edit/save the local copy, check paths, and do not overwrite completed results. |
| PowerShell activation blocked | Use `.venv\Scripts\python.exe`; do not change organizational policy. |
| Moving/renaming the folder broke the virtual environment | [Repair the moved environment](#moved-folder), keeping results/configuration. DEMO still needs no LIVE packages. |
| Missing/mismatched LIVE packages | Install the pinned `requirements.txt` in `.venv`; do not arbitrarily upgrade. |
| Example config rejected | Replace the project endpoint and use actual deployment names; do not use model names. |
| Only a classic connection string/model endpoint exists | A new Foundry project endpoint is required. |
| `config.json` not found | Check its folder and `.json.txt` extensions. |
| `prompts/my-v2.txt` missing | Check the repository folder, path, and saved file first. Follow [activity 4](../../README.md#lab-4) only if the included working file is genuinely missing; do not overwrite personal work with V2. |
| `my-v2.txt` / `my-case.jsonl` already exists | These are included example working files. Inspect contents/personal edits and distinguish reuse from your own edit. `my-v2.txt` adds instructions against conditional limits before date clarification and cites only SCOPE then; it is not identical to `v2.txt`. |
| JSONL validation fails | Fix the identified line/field; retain all eight fields and valid types. |
| Extra-case count is not one | Remove unintended extra rows; keep N02 only. |
| `review` appears stuck | It is waiting for verdict and reason; confirm `검토 저장`. |
| Gate reports missing human review | Save actual verdicts/reasons with candidate D06 and holdout H04 `review`, then **repeat the same `gate`**. No new generation or judging is needed. |
| Only AI reviews exist | A real human review is still required; do not relabel the AI record. |
| 401/authentication failure | Sign in with the intended user and tenant; do not paste keys into code. |
| 403 despite Owner | Check Foundry User for both user and project identity at parent scope; allow propagation. |
| Model visible but quota lookup returns 403/an empty list | Quota has separate subscription-scoped access. Check the [permission contract](#permissions-contract) and model/SKU filter; do not infer zero quota. |
| Private Link/public-access restriction | Use an approved VNet/VPN/environment; do not disable the firewall. |
| Model 404 | Check the project and **deployment** name; default is `eval-model`, not `gpt-6-luna`. |
| JSON Schema/parameter 400 | Verify model support for Chat Completions, Structured Outputs, and generation options. |
| `finish_reason=length` | Output is truncated. Fix output-budget compatibility in a new experiment, not by accepting the row. |
| 429 | Check shared TPM/RPM and judge load; wait, then resume incomplete work only. |
| Model/region/quota unavailable | Follow [availability checks](#model-availability). |
| Resource-group history shows a failed `PolicyDeployment` while the model works | Inspect that deployment separately. A diagnostic policy may reference a missing central Log Analytics workspace. Preserve the warning and refer it to the policy owner; do not delete history or disable policy to manufacture success. |
| Judge exit 3 | Repeat the same entire command, preserving `--like`, to retrieve the same job. |
| Remote completed, no local completion message | Wait for collection/validation; preserve IDs and fix any explicit error. |
| `judge` collection/persistence error | Fix the reported cause, such as connectivity, permissions, or storage, then resume the entire command including `--like`. Even if `judge.json` exists, a report-save error can require validation/persistence again. |
| Missing result ID, score, or reason | Preserve raw output/job files; investigate the SDK/service contract. Do not pass missing evidence. |
| Only one compared run has scores | Complete the other judge using the fixed contract. |
| Portal run missing/different scores | Match tenant/project/IDs and raw scores; distinguish threshold differences. |
| Input/model/judge contract mismatch | Inspect changed settings and start a separate comparable experiment. |
| Gate exit 2 | Read BLOCK reasons; this is an intentional quality decision. |
| DEMO rejects edited data/prompt | It only replays fixed fixtures; use LIVE for a separate measured experiment. |
| Forgot the last checkpoint | Use the [result-file resume table](setup.md#resume-checkpoints). |
| Deletion incomplete | Follow [scope/lock/status checks](cleanup.md); a request is not completion. |

When sharing errors, include only the command, checkpoint, error type, and necessary sanitized identifiers. Do not publish credentials, full customer data, or unredacted recordings.

<a id="permissions-contract"></a>
## Match permission, identity, and scope

**New dedicated environment:** this guide follows the [Foundry RBAC starting configuration](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry#minimum-role-assignments-to-get-started): **Foundry User for both your user and the project's managed identity on the parent Foundry resource**. Portal creation can add these assignments when the creator can assign roles; do not assume CLI creation does so. Owner management permissions are separate from Foundry data access.

**Existing/shared environment:** the [cloud evaluation prerequisites](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation#prerequisites) specify **Foundry User on the project** for the caller. The official enterprise RBAC example also uses project-scoped Foundry User plus parent-resource Reader. The dedicated setup's parent scope is not the uniquely minimal scope for every evaluation. Have the owner verify the actual models, connections, and APIs; do not broaden shared-account access for a class.

| Value | Purpose / distinction |
|---|---|
| Your user Object ID | Signed-in caller used by local `AzureCliCredential`; assignee type `User` |
| Project `identity.principalId` | **Project managed identity** prepared for service-side access; assignee type `ServicePrincipal` |
| Parent account `identity.principalId` | **Separate account identity** needed for project management; do not substitute it for the project identity |
| Resource ID ending in `/accounts/ACCOUNT` | Assignment **scope**, not a principal ID; permissions are inherited by child projects |
| `53ca6127-db72-4b80-b1b0-d745d6d5456d` | **Role definition ID** for Foundry User, unchanged from the Azure AI User name |

Resource creation needs creation permission at the appropriate scope; assigning roles needs role-assignment permission. Owner is one way to provide both, not every participant's minimum role. **Quota lookup** separately requires subscription-scoped `Microsoft.CognitiveServices/locations/usages/read`. Use **Cognitive Services Usages Reader**, or an existing role including that permission, only for users who need it. A Foundry-resource assignment alone does not authorize subscription quota lookup.

RAG's **user → Search** access is also separate from **Search identity → model** access. Search Service Contributor can manage service settings as well as search objects; document upload/query needs Search Index Data Contributor separately. With service-scoped access, unique object names prevent collisions but are not user-level security isolation. Follow only the actual [Search access](optional-rag.md#search-access) and [complete-path model access](complete-lab.md#search-model-access) instructions.

<a id="managed-identity-access"></a>
## If the project identity cannot be selected

Use this fallback only when portal selection in [setup 4](../../README.md#setup-permissions) is difficult. If you cannot assign roles, ask the owner to verify identity and scope instead of attempting the command.

1. Open the project's Azure resource. Its ID ends in `/accounts/ACCOUNT/projects/PROJECT`.
2. Copy **Identity → System assigned → Object (principal) ID**, or `identity.principalId` from JSON view. Do not use the parent account's identity.
3. Copy the parent resource ID ending at `/accounts/ACCOUNT`.
4. Confirm the role is missing, then run this once with real values:

```bash
az role assignment create --assignee-object-id "YOUR-PROJECT-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

The GUID is Foundry User, formerly Azure AI User. Verify member and scope in IAM. If the project lacks a system identity, enable **Identity → System assigned → On → Save** through the authorized process; do not replace it with shared credentials.

<a id="model-endpoint-contract"></a>
## Distinguish names, versions, and endpoints

| Concept | Value and use in this path |
|---|---|
| Model name | `gpt-6-luna`: catalog model, not the deployment field in `config.json` |
| Model version | For example, `2026-09-22`: backing model version; required for the complete path's recorded V1 comparison |
| Deployment name | New setup uses `eval-model`: the deployment to look up/call, placed in `model_deployment` and `judge_deployment` |
| Region/deployment type | Resource/project `swedencentral` and model SKU `GlobalStandard` are separate settings; the group's region does not set child-resource regions |
| Project endpoint | `https://ACCOUNT.services.ai.azure.com/api/projects/PROJECT`: the configuration URL, not a resource ID, classic connection string, or model-only endpoint |
| SDK/API version | Package `2.7.0` and project API `v1` are distinct from model versions. The SDK appends `/openai/v1`; do not append it in configuration |

`GlobalStandard` can use worldwide processing infrastructure. A **`swedencentral` deployment does not guarantee all inference stays in Sweden**. Before using real data, check [deployment-type processing locations](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/deployment-types). This guide uses fictional policy; do not change SKU mid-experiment.

<a id="model-availability"></a>
## Model, region, and quota

The target is **`gpt-6-luna` in `swedencentral`**, but the actual subscription catalog and deployment screen determine availability.

1. Confirm the exact model name/version in the correct account and region. Do not silently substitute another name.
2. Check supported SKUs, remaining quota, and capacity units separately, including Global Standard availability. For a 403 or empty quota lookup, verify [subscription-scoped read access](#permissions-contract) and the exact model/SKU first.
3. If quota is unavailable, request an increase or agree on a new experiment with the owner. Do not reduce others' deployments or silently switch regions/models.
4. For new introductory resources, keep deployment name `eval-model` and prove compatibility with the [smoke check](setup.md#smoke). Use deployment names, not catalog model names, in both configuration fields. Follow [existing-environment conditions](setup.md#existing-environment) for authorized existing names.

Do not assume identical Chat Completions, JSON Schema, generation-option, or judge support. Reasoning-token usage can cause truncation despite short final prose. Changing output settings requires a new baseline, not a mid-experiment edit. Do not add a model router or partner model implicitly.

If blocked, record it and optionally [switch explicitly to DEMO](setup.md#switch-to-demo). Before an agreed region change, check [evaluation support](https://learn.microsoft.com/azure/foundry/concepts/evaluation-regions-limits-virtual-network) and [model availability](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability). Retain already-created resources.

<a id="resume"></a>
## Interrupted work and remote-ID recovery

The default `judge` **status-polling budget is 300 seconds**, not a wall-clock limit including authentication, submission, HTTP responses, and collection. Exit **3** means resume polling the saved remote IDs, not failure or a request to submit again.

Completed `run`/`judge` commands read saved evidence. Partial generation skips saved rows; a response interrupted before persistence may be billed again. Existing remote `run_id` values are retrieved using the **entire original command, including `--like`**, not resubmitted. Complete-path calibration uses its original `calibrate` command. Use only one terminal per result folder. Closing the terminal does not cancel cloud work.

**Waiting and error recovery are different.** For exit 3, resume polling. For `ERROR:`, resolve its cause first, then use the same command. Collection/persistence errors can also require resumption; retries are not limited to still-processing runs. If remote creation is uncertain, follow ID recovery below first.

For changed introductory/minimal-RAG inputs, use a new `--out` folder. **Complete-path `run` has no `--out`**: follow [new-experiment setup in a separate working folder](complete-lab.md#resume). Do not overwrite or merge earlier evidence.

<a id="moved-folder"></a>
### If moving or renaming the folder broke the virtual environment

**Do not use this recovery just because you opened another terminal.** Follow [normal resumption](setup.md#resume) by activating the existing environment.

Only if the environment still refers to its old location and no longer works, open a terminal in the new folder. If an old environment was activated automatically, leave it with `deactivate` first. Confirm that `lab.py` and `requirements.txt` are present, then use **only your operating system's block** to recreate `.venv`. `--clear` removes packages inside `.venv`; preserve anything you intentionally placed there first. Do not delete configuration, results, or your prompt/question copies.

macOS / Linux:

```bash
python3 -m venv --clear .venv
source .venv/bin/activate
```

Windows / PowerShell:

```powershell
py -3 -m venv --clear .venv
.\.venv\Scripts\Activate.ps1
```

If activation is prohibited, replace every subsequent `python` with `.\.venv\Scripts\python.exe`. **DEMO participants skip the LIVE-only item below. Only LIVE and both RAG paths open it to restore packages.**

<details>
<summary>LIVE/RAG only: restore pinned packages</summary>

Install the repository's fixed versions into the recreated environment. DEMO does not need them; do not upgrade to arbitrary newer versions.

```bash
python -m pip install -r requirements.txt
```

</details>

**Local check for every path:**

```bash
python lab.py doctor
```

`LOCAL OK` and `dev 8개, holdout 4개` confirm recovery, not Azure connectivity. Keep saved results and use the [resume table](setup.md#resume) for your path's next unfinished step. DEMO still runs without Azure login, LIVE packages, or network access.

<a id="remote-job-recovery"></a>
### Ambiguous remote creation after disconnection

`phase` may be `creating-eval` or `creating-run` without a saved ID. Do not automatically create another potentially billable job.

First locate the **local correlation ID** for that evaluation. It is not the remote `run_id` in `foundry-job.json`.

| Execution path | File containing local `run_id` |
|---|---|
| Introductory `lab.py` / minimal `rag_lab.py` | `run.json` in the relevant result folder |
| Complete `advanced_lab.py` | `results/advanced/<stage>/evaluation-request.json`; use `calibration` for the calibration stage |

1. Preserve the files. Use that local `run_id` to find `straightforward-<first 8 characters>` or `<prompt>-<split>-<first 8 characters>` in the portal. Complete-path runs use `<stage>-advanced-<first 8 characters>`, with `calibration` for calibration. Remote `workshop_run` metadata must match.
2. Only after positively identifying the exact job, restore missing IDs in `foundry-job.json`. Use `ready` if only the eval exists, or `submitted` if the run exists, then repeat the **entire original `judge` or `calibrate` command**.
3. If existence is uncertain, do not resubmit. Request the owner's investigation or use a separate DEMO path. Never edit scores, evidence hashes, or contracts to manufacture completion.

For an explicitly terminated failed/canceled run, fix its cause first. An owner can preserve its original ID/status, verify termination, then set only `run_id` to `null` and `phase` to `ready` to resubmit the same saved responses under the same eval/contract. This is paid reevaluation, not score-shopping.

## SDK and verification scope

Official RBAC and SDK/API documentation cross-checked **2026-09-28**. This review and local testing are not a new Azure execution.

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
| SDK default API | Project API `v1`; OpenAI client uses the project endpoint + `/openai/v1`. The repository does not override `api_version` |

Direct dependencies are pinned, not a full transitive/hash lockfile.

Current Learn examples may use `azure-ai-projects>=2.2.0` and `DefaultAzureCredential`; **this repository's contract is the exact pins above and `AzureCliCredential`**. Do not upgrade or switch authentication merely to match a general example. `beta.evaluators` is a preview API, so do not call the whole workflow GA. The separate Search paths use `2026-04-01` for minimal/extractive retrieval and `2026-08-01-preview` for LLM planning; these are not project API versions.

**Recorded configuration:** the September 28, 2026 fresh-environment complete-path run used `gpt-6-luna` version `2026-09-22` in `swedencentral`, GlobalStandard 60K TPM. See the [complete-path result](complete-lab.md#results). Current availability, including other subscriptions/regions, must be checked separately.

Local tests check authored examples, gate behavior, missing/tampered evidence, docs/JSONL contracts, and installed SDK request/response shapes with an in-memory transport. They do not by themselves validate real permissions, capacity, billing, or current portal UI.

```bash
python -m unittest discover -s tests -v
```

SDK tests run when dependencies are installed; otherwise only those tests are skipped. Complete your own smoke check and, for a class, [a real rehearsal](facilitator.md#rehearsal).

<a id="live-verification"></a>
### Evidence scope by learning path

Keep the author's earlier introductory records separate. On September 28, 2026, a new group was used to rerun **the shared N01 setup smoke and the entire recommended complete path**. The [recorded complete-path result](complete-lab.md#results), with every final V2 metric passing including Relevance, is **one observation from a separate vector/planning/dialogue experiment**. It does not revalidate the entire introductory LIVE path or minimal RAG in the current environment.

The retained V1 comparison, calibration, and acceptance evidence belongs to that complete-path run only. Use reports from your own path; do not treat another execution's scores as a reproduction target.

## Official sources

| Source | Topic |
|---|---|
| [Create a Foundry project](https://learn.microsoft.com/azure/foundry/how-to/create-projects) | New project and CLI prerequisites |
| [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) | User/project identity and role scope |
| [AIProjectClient API](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient?view=azure-python) | Project endpoint, default `v1`, OpenAI client route, and beta preview status |
| [Deploy models](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/deploy-foundry-models) | Catalog, deployment names, types |
| [Model deployment types](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/deployment-types) | Resource region versus inference location; token billing versus reserved capacity |
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
| [Search RBAC](https://learn.microsoft.com/azure/search/search-security-rbac) | Service/object management versus document read/write access |
| [Agentic retrieval](https://learn.microsoft.com/azure/search/agentic-retrieval-overview) | GA minimal extraction versus preview LLM planning and conversation features |
| [Search pricing models](https://learn.microsoft.com/azure/search/search-sku-tier) | Provisioned-capacity costs for Dedicated services such as Basic |

Do not mix the new Foundry API with classic `azure-ai-evaluation` connection strings, authentication, mapping, or response contracts.

**English** | [한국어](../optional-rag.md)

# Optional: Azure AI Search + Foundry IQ RAG and evaluation

[Core workshop](../../README.md) · [Korean core guide](../../README.ko.md)

**This optional path compares direct Search with Knowledge Base retrieval.** The introductory workshop supplies the full policy. Here, **only actually retrieved documents** reach the answer model and Groundedness judge. Evaluate retrieval and answer quality separately.

**RAG means searching for material, then answering from that evidence.** A **chunk** is a policy fragment; an **index** stores fragments for search. A Knowledge Source connects to the index, and a Knowledge Base uses that connection to handle retrieval requests. Without writing code, prepare configuration → check both retrieval routes → generate and judge each route's answers → compare.

**You do not need to finish the complete RAG path first.** This guide compares two retrieval routes using `rag_lab.py` and `optional-rag/prompt.txt`. Do not mix its results with `advanced_lab.py`'s V1/V2, calibration, freeze, or holdout workflow. Neither RAG CLI has a DEMO mode.

Reuse the intended account, Foundry project, **`gpt-6-luna` / `eval-model`**, and **`swedencentral`**. Add an Azure AI Search service, index, and actual Foundry IQ Knowledge Source/Knowledge Base. **Retain all resources and evidence.**

**Separate complete-path reference videos:** [English/Korean vector and LLM-planned RAG summaries](../media/complete-rag/README.md). These are not execution or validation records for this minimal `search`/`iq` exercise.

## What is used

| Route | Actual operation |
|---|---|
| `search` | Semantic query against an Azure AI Search index |
| `iq` | Foundry IQ Knowledge Base `retrieve` → search-index Knowledge Source → the same index |
| Both | Up to three returned approved chunks → `gpt-6-luna` answer → retrieval metrics, business checks, and Foundry Evaluation |

This is **not local search relabeled as Foundry IQ**. Real knowledge objects are created, and IQ `references`, `sourceData`, and `activity` are retained.

The simple path uses **GA Search API `2026-04-01`, pinned in the code, for minimal/extractive retrieval**. It does not use vector embeddings, LLM query planning, answer synthesis, or Agent Service/MCP integration. `gpt-6-luna` generates and judges answers in the application; it is not a knowledge-base planner. Official Foundry IQ documentation supports custom applications calling this REST API directly. Do not mix preview `messages` or planning settings from those articles into this GA request.

```text
question ── search ──────────────────→ Search index
         └─ iq → Knowledge Base → Knowledge Source ─┘
                              ↓
                    three retrieved chunks
                              ↓
             gpt-6-luna answer + same-context evaluation
```

The two routes can return the same documents for a single-index query. This is not evidence that IQ must outperform direct Search.

<a id="prerequisites"></a>
## 1. Prerequisites and cost

Complete [README setup 1–7](../../README.md#prepare): the virtual environment, `requirements.txt`, real `config.json`, model deployment, and one-case generation/evaluation check. For an existing environment, use [existing-environment setup](setup.md#existing-environment). **Return to this section after shared setup; introductory activities 1–6 are not required first.** No agent server, Docker, Storage, or embedding deployment is added.

Run each command from the repository root containing `rag_lab.py`, with the virtual environment activated. Commands create result directories.

```bash
python lab.py doctor --live
```

Confirm `LIVE 조회 OK` for `gpt-6-luna` / `eval-model`. This checks only authentication and model-deployment lookup, **not evaluator lookup, Search setup, or successful generation/judging**. The shared one-case smoke check covers generation/judging; the steps below check Search. Match the portal and CLI account, tenant, and subscription using the core guide.

**Reuse an authorized Basic-or-higher Search service if available.** It can be the complete lab's service, but that is not required; otherwise create just one in section 2. Share the service, not the two exercises' object names. Free semantic/knowledge-retrieval plans are separate from the service SKU: **Basic still has ongoing service charges**. Do not automatically create another Search service.

The extension has **7 chunks, 4 questions × 2 routes = 8 answers and 16 judge metric items**. Retrieval and evaluator internals are separate requests. Model generation/judging costs money; free retrieval allowances can be exhausted. Retaining resources is not equivalent to free usage.

**Before creation**, obtain the owner's approval for service creation/use, ongoing charges, and the two service-scoped roles below. Assigning roles requires `roleAssignments/write` at that scope; ordinary Contributor access alone is insufficient. Stop here if an authorized administrator cannot prepare the permissions.

<a id="create-search"></a>
## 2. Search service and least-privilege access

Replace all placeholders with real values. You can reuse the core dedicated group. The service name must be globally unique and use lowercase letters, digits, and dashes.

**If an authorized Basic-or-higher service already exists, skip both commands below and use its endpoint/permissions.** `az search service create` can update an existing service, so do not run it against a name you intend to reuse. Create below only when you do not yet have a service.

**Before creating a new service:** in Azure portal, open **Subscriptions → intended subscription → Resource providers** and check **`Microsoft.Search`**. If unregistered, an authorized administrator selects **Register** and confirms `Registered`. Shared setup's `Microsoft.CognitiveServices` registration does not replace this. Follow [official provider-registration guidance](https://learn.microsoft.com/azure/azure-resource-manager/management/resource-providers-and-types) for the provider you need. If existing Search is in another group, use that service's actual group for `YOUR-LAB-RESOURCE-GROUP` below.

```bash
az search service check-name-availability --name "YOUR-SEARCH-NAME" --type searchServices --subscription "YOUR-SUBSCRIPTION-ID"
```

Proceed only with `nameAvailable: true`.

```bash
az search service create --name "YOUR-SEARCH-NAME" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku basic --identity-type SystemAssigned --semantic-search free --disable-local-auth true
```

This **disables API keys**. Do not retrieve or store keys. You can record `retain=true` under portal Tags; a tag is not a deletion lock.

<a id="search-access"></a>
### User ID and Search roles

For both new and existing services, retrieve the actual resource ID:

```bash
az search service show --name "YOUR-SEARCH-NAME" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth,semanticSearch:semanticSearch}" --output json
```

Confirm `Succeeded/succeeded`, `swedencentral`, a Basic-or-higher SKU, and `disableLocalAuth: true`. `semanticSearch` must be `free` or an already approved `standard` plan. Do not change existing settings without the owner's approval. Use the returned `id`, ending in `/providers/Microsoft.Search/searchServices/...`, as `YOUR-SEARCH-RESOURCE-ID`.

Look up the currently signed-in **user Object ID**. It is not the project identity recorded during portal setup:

```bash
az ad signed-in-user show --query "{account:userPrincipalName,objectId:id}" --output json
```

Verify that `account` identifies you in the intended tenant, then use **`objectId` as `YOUR-USER-OBJECT-ID`**. Do not substitute the project or Search managed identity. If directory lookup is restricted, ask the environment owner to verify your user ID in that tenant. Check **Access control (IAM)** on Search, including inherited roles, then grant the following roles at the **Search service scope only**, and only if missing:

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

The roles are **Search Service Contributor**, which permits service configuration and key retrieval as well as index/knowledge-object management, and **Search Index Data Contributor** for document upload/query and Knowledge Base retrieval. Do not grant subscription-wide roles. **These service-scoped roles also cover other participants' objects; distinct names are not a security boundary.** Use only the approved shared-workshop scope. This custom-app path does not query using the project identity, so it does not need additional project-managed-identity assignments.

**Checkpoint:** verify both roles apply to your Object ID and allow propagation. A successful role assignment alone does not prove data access. If sections 3–4 return 401/403, check your identity, scope, network, and propagation, then repeat the same command. Do not repeatedly create roles or fall back to keys.

<a id="index"></a>
## 3. Create the index and actual Foundry IQ knowledge objects

**In VS Code**, open [the example](../../optional-rag/config.example.json) and use **File → Save As** to create **`config.rag.json`** beside `rag_lab.py` at the repository root. Do not save inside `optional-rag/` or as `config.rag.json.txt`. Check an existing personal configuration rather than overwriting it. Copy the actual service URL from Search Overview and save. **Retain shared setup's `config.json` unchanged**; both files are required.

```json
{
  "search_endpoint": "https://YOUR-SEARCH.search.windows.net",
  "index_name": "travel-rag-index",
  "knowledge_source": "travel-policy-ks",
  "knowledge_base": "travel-policy-kb",
  "top_k": 3
}
```

The three object names above are defaults. **Before running on a shared service**, choose authorized participant-specific `index_name`, `knowledge_source`, and `knowledge_base` values, such as `travel-rag-a7k3m9`, `travel-policy-ks-a7k3m9`, and `travel-policy-kb-a7k3m9`. Keep those names and `top_k: 3` when resuming the same experiment; do not target complete-path objects.

**Keep the configurations distinct:** `config.json` holds the shared-setup project endpoint (`.services.ai.azure.com/api/projects/...`); `config.rag.json` holds the Search endpoint (`.search.windows.net`). Do not merge the files or put the same endpoint in both. Follow the shared [JSON editing guidance](../../README.md#setup-config), changing only the specified values and saving the file.

```bash
python rag_lab.py setup
```

The code first compares all three existing object definitions, then creates a missing index, uploads documents, and creates any missing Knowledge Source and Knowledge Base.

**Checkpoint:** `SETUP OK: 7 chunks, 4 evaluation cases`. `results/rag-setup.json` contains actual index, Knowledge Source, and Knowledge Base definitions. Verify retrieval separately with both queries in the next section.

The [corpus](../../optional-rag/documents.jsonl) divides the fictional policy into seven chunks: six official chunks and one unapproved draft. **`approved eq true`** excludes the draft; a `corpus_hash` filter fixes the corpus version. The index includes a Korean analyzer and semantic configuration. Both language guides use the same Korean inputs.

Setup resumes incomplete uploads for the same corpus, but does not overwrite objects belonging to another corpus/source. Use new object names for changed experiments.

**Mismatched declared settings stop setup before creation or upload.** Checks include the index analyzer/semantic configuration, source-data fields, and Knowledge Base source list; extra server-default properties are allowed. Reuse still requires the owner's permission, and search objects must remain unchanged during the experiment.

**Security distinction:** service RBAC controls access. `approved` is a policy-status filter, not a per-user ACL. Document-level authorization, Purview, and user-specific access tests are outside this small lab.

<a id="retrieve"></a>
## 4. Verify both real retrieval routes

```bash
python rag_lab.py query --mode search --query "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?" --out results/rag-query-search.json
```

**Checkpoint:** `RETRIEVAL OK: search`, selected chunk IDs, and the saved `results/rag-query-search.json`. Resolve any error here; only after completion, query IQ with the same question.

```bash
python rag_lab.py query --mode iq --query "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?" --out results/rag-query-iq.json
```

The question asks about a September domestic hotel expense of KRW 220000 without prior approval.

**Checkpoint:** `RETRIEVAL OK: iq`, selected chunk IDs, official source IDs, scores, **`searchIndex` activity**, and the saved `results/rag-query-iq.json`. The JSON's `raw_response` is the actual service response, including IQ reference/source data; `documents` is the selection to be supplied to the model. Neither query generates an answer or runs a judge.

| Identifier | Purpose |
|---|---|
| Chunk ID, such as `current-lodging` | Retrieval ground-truth matching |
| Official `source_id`, such as `TRAVEL-CURRENT` | The answer's `citations` |
| IQ reference `id` / `activitySource` | Links a returned document with that request's retrieval activity |

IQ uses `intents`. The app takes at most three returned approved chunks. **Empty or failed retrieval stops explicitly; it never silently supplies the full policy instead.**

<a id="evaluate"></a>
## 5. Evaluate retrieval and answers independently

The [four cases](../../optional-rag/cases.jsonl) reuse core dev D02/D03/D04/D08; they are not a new independent holdout. [Required-chunk labels](../../optional-rag/retrieval-labels.json) are evaluation-only and never enter the retrieval request, generation prompt, or judge.

Keep questions, corpus, `optional-rag/prompt.txt`, configuration, answer/judge model versions, and search objects unchanged between runs. **Only the retrieval route changes**; differing contracts cause comparison to be rejected. If you need a change, preserve existing evidence and start both routes in new output folders as a separate experiment.

```bash
python rag_lab.py run --mode search --out results/rag-search
```

Confirm `LIVE RAG generation complete: 4 answers` and `status: complete` in `results/rag-search/run.json`, then judge. Generation completion does not mean the business checks passed.

```bash
python lab.py judge results/rag-search
```

Wait for **`평가 완료: 4개 답변 × 2개 지표`**. If still processing, repeat that exact command. For interruptions/errors, use the [resume table](#resume).

```bash
python rag_lab.py run --mode iq --out results/rag-iq
```

Wait for **`LIVE RAG generation complete: 4 answers`** before running the judge below.

```bash
python lab.py judge results/rag-iq --like results/rag-search
```

For IQ, also confirm four generated answers followed by **`평가 완료: 4개 답변 × 2개 지표`**. `--like` preserves the completed Search run's judge model/evaluator contract; it does not copy retrieved contexts or answers.

```bash
python rag_lab.py compare results/rag-search results/rag-iq
```

**Checkpoint:** `REVIEW_REQUIRED` and `Comparison: results/rag-iq/rag-comparison.md`. Comparison files have been produced; inspect the actual case below before deciding what they mean.

```bash
python rag_lab.py inspect results/rag-iq D04
```

Read the retrieved chunks, missing required chunks, answer, business checks, and judge reasons—in that order. **Groundedness receives exactly the per-case context used to generate that answer**, not the original full corpus.

**Read the answer JSON:** `decision` is the policy decision, `limit_krw` is the lodging limit (not the claimed expense), `citations` lists official source IDs, and `answer` is the employee-facing explanation. `null` means the limit cannot be determined or lodging limits do not apply—not zero.

Decisions are `allowed`, `needs_approval` (prior approval required), `not_allowed`, `unknown` (absent from policy), or `needs_info` (missing question information). D04 can correctly use `unknown` for an unspecified limit. These values do not execute reimbursement or grant approval.

| Metric | Meaning and limit |
|---|---|
| Required-chunk Recall@3 | Fraction of required chunks included in model context |
| Precision@3 | Fraction of delivered chunks listed as required; useful auxiliary chunks might not be labeled |
| Business checks | Format, decision, amount, and citations |
| Groundedness | Support in the retrieved evidence actually supplied |
| Relevance | Response to the question; appropriate abstention may still score poorly |
| Citation IDs linked | Citation IDs occur in retrieved documents; not proof of semantic support |

Read `results/rag-iq/rag-comparison.md`/`.json`, and each run's `rag-report.md` and `retrieval-metrics.json`. Comparison exit code 0 means the files were produced; **the status is always `REVIEW_REQUIRED`**. Even an empty `issues` list is not release approval or proof IQ is superior. `issues` flags metrics below 80% and critical-case failures; the judge score threshold is 4/5. A person must examine contexts and scoring reasons.

Core `lab.py compare/gate` is for fixed-context prompt experiments and rejects RAG input. Use this extension's comparison. Do not combine core and RAG results as a single before/after experiment.

<a id="resume"></a>
### Command status, interruption, and resumption

<details>
<summary>Open only for waiting, errors, or resuming later</summary>

Restore the virtual environment and sign-in in a new terminal. Never use the same output folder concurrently in two terminals.

| State | Next action |
|---|---|
| Connection failure/interruption during `setup` | Resolve the cause and repeat `setup` with the same configuration. It reuses matching objects and completes same-corpus uploads; mismatches are not overwritten |
| Connection failure/interruption during `run` | Repeat the entire command with the same `--mode` and `--out`. Saved responses and searches in `pending_retrievals` are reused. A response interrupted before persistence can incur another charge |
| `run.json` has `status: collecting` | Partial run. Read saved `rows`, `pending_retrievals`, and the error; do not use `judge`, `inspect`, or `compare` yet |
| `Using completed LIVE evidence; no new retrieval or generation calls.` | Completed evidence for the same inputs was reused. A new `LIVE RAG generation complete` message is not expected; proceed to this route's judging or next unfinished step |
| Judge pending / exit `3` | Repeat the same complete `python lab.py judge …` command, retaining IQ's `--like`. The default status-polling budget is **300 seconds**; total command time can be longer |
| Generation/judging complete with low scores or failed checks | Do not resample saved answers. Finish judging both routes, then preserve failures with the dedicated comparison |
| `ERROR:` / argument error | Resolve the cause, then resume the same command. If unable to finish, distinguish the last completed stage from unperformed work and preserve it in section 6 |

| File | What to check |
|---|---|
| `results/rag-setup.json`, `results/rag-query-search.json`, `results/rag-query-iq.json` | Object definitions and the two retrieval probes |
| `run.json` in each run folder | State, local correlation `run_id`, saved answers/contexts/raw retrieval, and pending retrievals |
| `foundry-job.json` | Remote `eval_id`, `run_id`, and job state, distinct from the ID in `run.json` |
| `judge.json`, `report.md` | Completed scores and per-case reasons. Remote `completed` alone is insufficient |
| `rag-report.md`, `retrieval-metrics.json` | RAG evidence/retrieval metrics. `lab.py judge` updates `report.md`; `rag_lab.py compare`/`inspect` refresh the RAG report |

For ambiguous remote creation, follow [ID recovery](reference.md#resume), without forcing a new submission. Do not delete files to resample answers or scores.

</details>

<a id="evidence"></a>
## 6. Portal evidence and retention

**Completion checklist:** verify these against your own results. Identical or low scores are valid comparison outcomes; execution errors and missing evidence must be resolved first.

- [ ] `results/rag-search` and `results/rag-iq` each contain four answers and both judge scores with reasons.
- [ ] I read `results/rag-iq/rag-comparison.md`, distinguishing retrieval metrics from answer metrics.
- [ ] I compared D04's actual context, answer, and scoring reasons, and understand that `REVIEW_REQUIRED` is not release approval.
- [ ] I retained my result folders and actual resources, and completed the [cost check](cleanup.md#retain-resources).

In the Search service's Azure portal view, inspect **Indexes**, **Knowledge sources**, and **Knowledge bases**. Portal/preview UI may differ from GA API behavior; saved service definitions/responses are the setup and retrieval evidence.

In the Foundry evaluation report URL, match a case's **question, answer, retrieved context, scores, and reasons**. Supplying the entire policy as `context` would be incorrect for this extension.

`run.json` records route/configuration, corpus hash, raw retrieval, references/activity, exact context/hash, and model output. If retrieval completed but generation was interrupted, the saved retrieval is reused. Completed runs read their evidence without another generation call.

- **Retain** the Search service, knowledge objects, existing Foundry resources, and evaluations.
- Do not automatically enable paid plans after a free allowance is exhausted.
- Keep `config.rag.json`, `config.json`, and `results/` out of Git.
- Preserve low scores and failures; do not rerun until results look better.

<a id="observed-results"></a>
### Earlier minimal-RAG records and evidence scope

Cleanup of the author's earlier Free service/records is a historical migration record, not a learner deletion step or a current resource-state check. The [recorded complete-path result](complete-lab.md#results) belongs to a separate vector/planning/dialogue experiment; it does not revalidate this minimal `search`/`iq` comparison. Run this API exercise in its own index on an authorized Basic service, and use your own `rag-comparison.md` and each `rag-report.md` for your judgment.

<a id="troubleshooting"></a>
## Troubleshooting

| Symptom | Action |
|---|---|
| Basic service cannot be created | Check `Microsoft.Search` registration, authorized existing service, regional capacity, subscription limits, and organizational policy. Do not delete another service or silently substitute Free. |
| 401/403 | Verify CLI identity/tenant and both service-scoped Search roles; allow propagation. Do not fall back to keys. |
| Only an MCP tool reports `invalid_token` | MCP and CLI authentication can differ. Verify the lab's explicit AzureCliCredential path; investigate tool authentication separately. |
| `queryLanguage` is rejected | Do not send it with this API version. Use the provided request and Korean index analyzer. |
| Output size must exceed 5000 | The code uses a 6000-token IQ retrieval output ceiling; model context still contains at most three chunks. |
| HTTP 206, partial results, missing reference data, or zero evidence | Resolve the failure and resume. No hidden full-corpus fallback. |
| Object/corpus contract differs | Preserve the existing object and use new names/output directories. |
| Only remote completed is shown | Wait for local score/reason persistence; repeat the same judge command on exit 3. |
| Core compare/gate rejects RAG | Use `rag_lab.py compare`. |
| Organization diagnostic PolicyDeployment fails | Refer missing central resources/policy configuration to its owner; do not disable policy or erase history. |

<a id="sources"></a>
## Official sources

- [Foundry IQ and custom-application REST use](https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-foundry-iq)
- [Search-index knowledge source](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-search-index)
- [Knowledge bases and GA/preview differences](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base)
- [Search roles, assignment permissions, and service scope](https://learn.microsoft.com/azure/search/search-security-rbac)
- [Retrieve API](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve)
- [Region and Free support](https://learn.microsoft.com/azure/search/search-region-support)
- [Knowledge retrieval billing](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable)

**English** | [한국어](../complete-lab.md)

# Complete lab: failure → improvement → reevaluation → fresh-question validation

[Repository home](../../README.md)

[Updated English/Korean recorded summaries](../media/complete-rag/README.md) show the current completed workflow.

This is the recommended complete learning path. It uses **one Basic-or-higher Azure AI Search service** for **vector/hybrid + LLM-planned Foundry IQ retrieval**. The separate optional minimal text-RAG exercise can reuse that service too.

The original `prompts/v1.txt`/`v2.txt` and earlier examples are historical introductory material. This path uses the explicitly versioned **`advanced-rag/instructions.v1.txt` and `instructions.v2.txt`**.

**Route:** follow sections 1–8 below. Neither introductory activities 0–6 nor the full Optional RAG exercise is a prerequisite. Section 2 borrows only shared environment setup, then returns here. Run one command at a time from the folder containing `advanced_lab.py`, with the virtual environment activated. Commands create result directories.

**Follow each checkpoint and the automatically generated results under `results/advanced/`.** No separate record form is needed; personal notes are optional. Do not apply the introductory 80% gate or D06/H04 review workflow here. **Completing the lab is not the same as automated acceptance.** Preserve low scores and stopped runs honestly; do not describe unperformed stages as complete.

## What “passed” means

The acceptance criteria in [acceptance.json](../../advanced-rag/acceptance.json) are fixed before the fresh holdout:

- **Every final V2 case** must pass business checks, required-evidence retrieval, Groundedness, **builtin Relevance**, and policy task success: **100%**, not an average that hides a failed case.
- Each required judge score must be at least **4/5**, with **zero critical-case failures**.
- The policy judge must correctly classify **all ten positive/negative calibration controls**.
- A real vector index/vectorizer and actual `modelQueryPlanning` activity are required.
- At least eight fresh holdout cases must be registered after freezing the candidate.

**Builtin Relevance remains a required metric.** The final answer must resolve the actual completed user interaction. A request for missing information is an intermediate step, not falsely labeled as a completed answer.

V2 uses explicit, scripted user follow-ups from evaluation data: a missing-date case receives the user's actual travel date after asking; an unavailable overseas-limit case receives a user request for a Finance inquiry checklist rather than a fabricated number. The model does not invent those user facts. The final conversation is supplied to the judge, but **automated initial-response checks cover only JSON format, decision, amount, and citation fields**.

The result field `intermediate_safe` means those field checks passed, **not that the initial prose received a separate semantic or safety evaluation**. Correct `unknown`, `null`, and `SCOPE` fields can coexist with a fabricated overseas limit in the explanation. Read the initial prose using `inspect --dialogue` in sections 5 and 7, and record your judgment.

`LAB_ACCEPTANCE_PASSED` means these declared educational criteria passed. **Human production approval remains separate and pending.**

<a id="architecture"></a>
## 1. One shared Search service

| Component | Purpose |
|---|---|
| Basic Search service in `swedencentral` | Hosts every index and knowledge base for this path |
| `travel-rag-index` / `travel-policy-kb` | Created separately only if you choose the Optional RAG exercise |
| `travel-vector-index` | Real 1536-dimensional HNSW vectors plus searchable policy text |
| `travel-vector-ks` / `travel-planned-kb` | Foundry IQ source/base with an LLM planning model |
| `rag-embedding` | `text-embedding-3-small`, used for document and query vectors |
| `rag-planner` | Supported `gpt-5.4-mini` planner; not the answer model |
| `eval-model` | `gpt-6-luna` for answers and evaluation |

The full IQ path uses **`2026-08-01-preview`**, because LLM query planning is not in the minimal GA API. It is not presented as a GA production deployment. The `low` effort setting performs actual LLM planning; vectors and a vectorizer enable hybrid retrieval.

Free Search does not provide the outbound managed identity needed here. Reuse an existing authorized Basic-or-higher service when available. **Basic has ongoing charges while retained**, and embedding, planning, generation, and judging can incur usage charges.

<a id="setup"></a>
## 2. Azure setup and permissions

**Check before creating additional paid resources:** the recorded V1 comparison requires answer deployment **`eval-model` / `gpt-6-luna` / version `2026-09-22`**, in `swedencentral`. A historical run does not guarantee current version availability or quota in your subscription. If you cannot meet this condition, choose the [fixed-policy introductory LIVE path](../../README.md#lab-0) or [DEMO](offline.md) before creating Search or additional models. Do not compare a different model version with recorded V1.

Complete only [README setup 1–7](../../README.md#prepare). Verify the answer-model version in [setup 5](../../README.md#setup-model), create `config.json`, and finish the one-case generation/evaluation check. For authorized existing resources, use [existing-environment setup](setup.md#existing-environment). Introductory A/B and activities 1–6 are not required prerequisites. **Return to Search setup below when ready.**

<a id="search-setup"></a>
### Prepare the Search service

**If reusing an authorized Basic-or-higher service, or if you already created it, skip both creation-preparation commands below.** Use a unique name only when a new service is needed. `az search service create` can also update an existing service, changing settings such as replicas or authentication. Do not create another Free Search service for this path.

```bash
az search service check-name-availability --name "YOUR-SHARED-SEARCH" --type searchServices --subscription "YOUR-SUBSCRIPTION-ID"
```

Create only if `nameAvailable: true`.

```bash
az search service create --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku basic --replica-count 1 --partition-count 1 --identity-type SystemAssigned --semantic-search free --disable-local-auth true
```

For both new and existing services, inspect the actual ID, region, SKU, authentication, and system-assigned identity. Obtain the owner's authorization before changing existing settings.

```bash
az search service show --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,identity:identity,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth}" -o json
```

Confirm `Succeeded/succeeded`, `swedencentral`, Basic-or-higher SKU, `disableLocalAuth: true`, and `identity.principalId`. Follow only [user ID lookup and Search role setup](optional-rag.md#search-access) for **Search Service Contributor** and **Search Index Data Contributor**, then return here. Its `YOUR-SEARCH-NAME` is the service above; do not continue into Optional RAG section 3.

<a id="search-model-access"></a>
Now check that the **Search identity from `identity.principalId`** has **Cognitive Services OpenAI User** on the parent Foundry account, and assign it only if missing. Do not substitute the project or user identity:

```bash
az role assignment create --assignee-object-id "YOUR-SEARCH-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

### Additional models and configuration

Check current model/version availability and quota, then deploy the two additional models **sequentially**. Concurrent writes to the same Foundry account can conflict. If an authorized deployment already exists, verify its model/version and skip its creation command. Do not silently update shared deployments.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-embedding --model-name text-embedding-3-small --model-version "YOUR-EMBEDDING-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 40 --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-planner --model-name gpt-5.4-mini --model-version "YOUR-PLANNER-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

The recorded additional-model versions were embedding `1` and planner `2026-03-17`. Record your actual versions. Keep the previously checked answer model at the recorded V1 version.

Save [the configuration template](../../advanced-rag/config.example.json) as **`config.advanced.json` beside `advanced_lab.py`**, not inside `advanced-rag/`. Keep the existing `config.json`.

| Setting | Where to find the actual value |
|---|---|
| `search_endpoint` | Azure portal → intended Search service → Overview URL |
| `model_resource_endpoint` | The same parent Foundry resource's Keys and Endpoint page: use the **Azure OpenAI resource endpoint** ending in `.openai.azure.com`, not the project endpoint. Do not copy API keys |
| `index_name`, `knowledge_source`, `knowledge_base` | Authorized names unique to the participant/experiment, such as `travel-vector-a7k3m9`, `travel-vector-ks-a7k3m9`, `travel-planned-kb-a7k3m9` |

**Sharing a service does not mean unconditionally sharing search objects or experiments.** Choose the three object names before the first run and keep them when resuming that experiment. Reuse objects only with the owner's permission and the same corpus, vector settings, model endpoint, deployments, and planning settings. `setup` stops rather than updating mismatched existing objects; use new object names for another experiment.

Embeddings use the account's `/openai/v1/embeddings` endpoint with Entra authentication. The project gateway supported chat/evaluation but returned 404 for embedding requests in this environment. API keys are not used.

```bash
python advanced_lab.py setup
```

**Checkpoint:** `VECTOR SETUP OK: 7 documents, 1536 dimensions`; inspect `results/advanced/setup.json`. Text, vectors, HNSW, vectorizer, source, and planned knowledge base are real service objects.

The smaller [optional text-RAG lab](optional-rag.md) can use this **same Search endpoint** in `config.rag.json`, with its distinct index/base names. Do not point both workflows at the same index name.

<a id="resume"></a>
### Command status, interruption, and resumption

<details>
<summary>Open only for waiting, errors, or resuming later</summary>

Outputs are fixed under **`results/advanced/`**. Use this table rather than introductory `run.json`/`run --out` instructions. Restore your virtual environment and sign-in in a new terminal; never run the same experiment concurrently in two terminals.

| Result | Next action |
|---|---|
| `GENERATION COMPLETE` or `Evaluation complete` | Check the stage's count and saved evidence, then continue. Completion does not mean acceptance |
| `아직 처리 중입니다` / exit `3` | Repeat the **entire original command**: the same `calibrate` for calibration, or the same `judge --stage …` for judging. It retrieves the saved remote job |
| Transient connection failure or interruption during generation | Resolve the cause, then repeat the same `run --stage …`. Saved responses are not regenerated. A response interrupted before persistence can incur another charge |
| `initial clarification/handoff field checks failed` / exit `1` | Initial quality failure. Read `<stage>/generation.json` at `pending → case ID → initial_response → response`, and preserve the failure. Repeating the command cannot resample a better answer |
| Calibration exit `2` with `mismatches` | Record misclassifications from `calibration-result.json` and stop. Do not lower thresholds or repeatedly judge until passing |
| `freeze`: `Dev acceptance is not met` / exit `1` | Record dev failures from `report.md` and preserve them. Do not create holdout yet |
| `LAB_ACCEPTANCE_BLOCKED` / exit `2` | Completed holdout failed a criterion. Record reasons from `acceptance-report.md`/`acceptance-result.json`, then go to section 8 |
| Other `ERROR:`, or `usage:` / `error:` | Resolve environment, input, or command errors first. In particular, exit `2` with `usage:` is an argument error, not a quality decision |

**An initial quality failure leaves `generation.json` in `collecting` state.** You cannot use `judge` or `inspect` as if generation completed, or obtain a final decision with `accept`. Read the saved initial response and error directly, mark later stages as not run, and preserve them in section 8.

Calibration/judging has a default **300-second status-polling budget**. Authentication, submission, HTTP responses, and result collection can make total command time longer.

| Artifact, relative to `results/advanced/` | Purpose |
|---|---|
| `setup.json`, `vector-query.json`, `planned-query.json` | Actual search configuration and retrieval evidence |
| `calibration-result.json`, `judge-contract.json` | Calibration result and accepted judge contract |
| `<stage>/generation.json` | `status`, completed response `rows`, and unfinished-case `pending` |
| `<stage>/evaluation-request.json` | Evaluation inputs and **local correlation `run_id`**. Calibration uses `calibration/` |
| `<stage>/foundry-job.json` | Remote `eval_id`, `run_id`, and job state; the same applies to calibration |
| `<stage>/judge.json`, `<stage>/report.md` | Completed scores and reasons |
| `frozen.json`, `holdout-registration.json` | Frozen candidate and fresh-question registration contracts |
| `acceptance-result.json`, `acceptance-report.md` | Automated decision for completed holdout |

`<stage>` is the command's `v1-recorded`, `v2-replay`, `planned-dev`, or `holdout`. File existence alone is not completion. For ambiguous remote creation, follow [ID recovery](reference.md#resume), without automatic resubmission.

**New experiment:** preserve existing evidence and obtain the repository code in a **separate working folder**, starting with an empty `results/advanced/` there. Prepare authorized configuration and reuse the Search service with new experiment-specific object names. This CLI's `run` has no `--out`. Keep the previous candidate/holdout failures, repeat both dev validations, and create a new holdout only after freezing.

</details>

<a id="retrieval-proof"></a>
## 3. Prove vectors and LLM planning are actually used

```bash
python advanced_lab.py query --mode vector --query "해외 출장 호텔 숙박비 상한을 확인하고 싶습니다." --out results/advanced/vector-query.json
```

**Checkpoint:** 1536 query dimensions, `content_vector`, `text_query: false`, and real retrieved chunks.

```bash
python advanced_lab.py query --mode planned --query "2026년 6월 30일과 7월 1일 국내 출장 숙박 한도를 비교하고, 한도를 초과할 때 필요한 절차와 해외 숙박 한도가 있는지도 알려주세요." --out results/advanced/planned-query.json
```

**Checkpoint:** `llm_query_planning: true`, actual generated search queries, and `modelQueryPlanning`/`searchIndex` activity. The verified request produced three subqueries. The code rejects a response without planning evidence rather than calling ordinary search “planned retrieval.”

<a id="calibration"></a>
## 4. Calibrate and freeze the judge

Read [the policy task-success rubric](../../advanced-rag/policy-task-success.txt). It treats correct missing-date questions and appropriate “policy does not specify” answers as **valid initial behavior**, while rejecting invented limits/approvals and contradictory answers. Correct initial behavior alone does not complete the final dialogue.

If calibration below is still processing or errors, use the **calibration row** in the [status/resume table](#resume).

```bash
python advanced_lab.py calibrate
```

**Checkpoint:** `CALIBRATION PASSED: 10 controls`. Four correct controls and six incorrect controls—including a grading-instruction attack and extra citations—must be classified correctly. The pass/fail labels are not sent to the judge.

The resulting evaluator version, rubric, model, and acceptance criteria are fixed in `results/advanced/judge-contract.json`. This is not permission to alter the judge after seeing holdout results.

<a id="improve"></a>
## 5. Real V1 failure, then a controlled V2 improvement

The [recorded V1 fixture](../../advanced-rag/fixtures/recorded-v1.json) contains four sanitized **actual earlier LIVE answers**, not fabricated wrong answers. D02's extra citation is retained. Replaying it is not claimed as fresh generation.

```bash
python advanced_lab.py baseline
```

```bash
python advanced_lab.py judge --stage v1-recorded
```

Compare [V1](../../advanced-rag/instructions.v1.txt) and [V2](../../advanced-rag/instructions.v2.txt). V2 distinguishes the minimum sufficient decision/amount evidence from merely retrieved or procedural sources, and completes necessary clarification/handoff interactions.

[Development follow-ups](../../advanced-rag/dev-followups.json) are declared before generation. They are scripted evaluation-user turns, not real customer statements or human production approvals. They contain no desired score.

```bash
python advanced_lab.py run --stage v2-replay
```

```bash
python advanced_lab.py judge --stage v2-replay
```

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D02
```

Read the initial prose for contradictions, using any problematic sentence as evidence for your judgment:

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D04 --dialogue
```

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D08 --dialogue
```

**Checkpoint:** V1 and V2 start from identical saved contexts and use the same answer model/settings/judge. V2 also completes explicitly declared user follow-ups where needed. This is a **prompt-and-dialogue workflow improvement**, not a claim that prompt wording alone explains the result. Keep the V1 failure; do not weaken V1 or reroll it.

<a id="freeze"></a>
## 6. Validate the full pipeline, then freeze

```bash
python advanced_lab.py run --stage planned-dev
```

```bash
python advanced_lab.py judge --stage planned-dev
```

This is a separate integration check using actual vector/LLM-planned retrieval. Both initial questions and necessary follow-up turns use the declared retrieval workflow.

**Do not change V2 instructions, follow-ups, models, or settings between sections 5 and 6.** Both dev validations must use the same candidate and input contract. If a change is needed, preserve existing results and perform both validations in a [new experiment](#resume).

```bash
python advanced_lab.py freeze
```

**Checkpoint:** `FROZEN` and a contract hash. V1 must contain a real failure; V2 replay and planned dev must meet the required criteria. The prompt, judge, model versions, retrieval configuration, source definitions, and corpus are fixed before fresh cases are created.

<a id="holdout"></a>
## 7. Generate fresh questions only after freeze

```bash
python advanced_lab.py create-holdout
```

A new random seed **fills in new dates, cities, and amounts in eight predefined scenarios**. They cover current/previous limits, over-limit approval, overseas scope, missing dates, prohibited flight class, and the exact boundary. These are fresh parameterized cases, not broad blind generalization testing. The missing-date and overseas-handoff scenarios include explicit evaluation-user follow-ups. Inputs, follow-ups, expectations, and provenance are stored privately under `results/advanced/holdout-data/`.

The command refuses to replace existing holdout files. Do not resample to obtain a pass.

```bash
python advanced_lab.py run --stage holdout
```

```bash
python advanced_lab.py judge --stage holdout
```

Read both completed follow-up dialogues, including the initial prose and final answer, and record your judgment:

```bash
python advanced_lab.py inspect --stage holdout --case-id N05 --dialogue
```

```bash
python advanced_lab.py inspect --stage holdout --case-id N06 --dialogue
```

```bash
python advanced_lab.py accept
```

**Checkpoint:** `results/advanced/acceptance-report.md` and `acceptance-result.json` contain your run's decision and reasons. `LAB_ACCEPTANCE_PASSED` requires all eight fresh scenarios to pass **every final-answer metric, including Relevance, plus the initial field checks**. `LAB_ACCEPTANCE_BLOCKED` is also a valid evaluation result to preserve.

If blocked, record the failure and hold recommendation, then go to section 8. Even with an automated pass, record any contradiction you find in the initial prose and withhold production adoption. Do not edit the frozen prompt/rubric or select only passing cases. A subsequent improvement uses a [new experiment in a separate working copy](#resume) with new held-out cases.

<a id="results"></a>
## Result interpretation

**The table below is one recorded complete-path run by the author, not a reproduction guarantee.** Use your own acceptance files for your decision. Neither this table nor its videos revalidates the separate introductory LIVE or minimal-RAG `search`/`iq` comparison in the current environment.

The earlier Relevance-excluded acceptance attempt is **not the final success result**. The recorded revised iteration passed all required metrics on every final V2 case:

| Stage | Business | Retrieval | Groundedness | Relevance | Policy task success |
|---|---|---|---|---|---|
| Recorded V1, 4 one-turn cases | 75% | 100% | 100% | 100% | 75% |
| V2 completed dev, 4 scenarios | 100% | 100% | 100% | 100% | 100% |
| V2 planned/vector dev, 4 scenarios | 100% | 100% | 100% | 100% | 100% |
| New frozen holdout, 8 scenarios | 100% | 100% | 100% | 100% | 100% |

All final judge scores are at least 4/5; the threshold was not lowered. There are no critical failures. The task definitions include explicit clarification/handoff follow-ups, so this is not a claim that an incomplete first turn answered an impossible question.

Intermediate clarification is retained as evidence, and user follow-up data is explicit. This is not a separate automated semantic pass for the initial prose. Production approval remains a separate human responsibility.

<a id="retention"></a>
## 8. Preserve results and resources

Keep the shared Basic Search service, embedding/planning/answer deployments, and every calibration, V1/V2, freeze, and fresh-question result you actually produced, **including failures**. Use generated reports to identify the last completed stage, pass/hold reasons, and unperformed work; establish the resource owner and next cost-review point. Basic service charges continue.

**Checkpoint:** use your result files and actual dialogues to explain V1's failure, V2's changes, and fresh-question results and limitations. If an earlier stage stopped, state that later stages were not run, and verify the retained resources and cost status.

**The following is the author's historical migration record, not a learner deletion step.** Do not delete resources without a separate decision. Never delete the resource group or shared Foundry account to clean one Search service. Do not rewrite Git history or platform audit logs, or disable organizational policies.

**Migration cleanup is complete:** the former Free service, eight superseded evaluation groups, two old comparison insights, one obsolete custom-evaluator version, the old failed deployment-history entry, and the explicitly scoped local legacy results were removed. The shared Basic service and current calibration/V1/V2/holdout evidence remain. Removing a deployment-history entry does not repair or disable an organizational policy.

Local `config*.json`, raw recordings, and `results/` remain outside Git. The versioned prompts and sanitized teaching fixture are source material for the new lesson.

## Official references

- [Agentic vector index and vectorizer](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-index)
- [LLM retrieval reasoning effort](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [Search tier feature support](https://learn.microsoft.com/azure/search/search-sku-tier)
- [Embeddings with Entra authentication](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings)
- [Custom Foundry evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)

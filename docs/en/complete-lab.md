**English** | [한국어](../complete-lab.md)

# Complete lab: failure → improvement → reevaluation → fresh-question validation

[Repository home](../../README.md)

[English/Korean recorded summaries](../media/complete-rag/README.md) show the **September 28, 2026 rerun starting with a new resource group**. Verify your own current results through the steps below.

This is the recommended complete learning path. It uses **one Basic-or-higher Azure AI Search service** for **vector/hybrid + LLM-planned Foundry IQ retrieval**. The separate optional minimal text-RAG exercise can reuse that service too.

The original `prompts/v1.txt`/`v2.txt` and earlier examples are historical introductory material. This path uses the explicitly versioned **`advanced-rag/instructions.v1.txt` and `instructions.v2.txt`**.

**Route:** follow sections 1–8 below. Neither introductory activities 0–6 nor the full Optional RAG exercise is a prerequisite. Section 2 borrows only shared environment setup, then returns here. Run one command at a time from the folder containing `advanced_lab.py`, with the virtual environment activated. Commands create result directories.

`advanced_lab.py` has no DEMO mode. Importing `baseline`, freezing, creating/registering holdout, inspecting, and accepting are local operations; setup, retrieval, generation, calibration, and judging use real Azure services.

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

`inspect` only prints saved evidence; it does not persist a review or approval. Keep separate review records in your organization's approval process, without editing automated results to mark approval. `LAB_ACCEPTANCE_PASSED` means the declared educational criteria passed; `human_production_approval` remains `PENDING`. **Human production approval remains separate and pending.**

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

The full IQ path uses **`2026-08-01-preview`, pinned in the code**, because LLM query planning is not in the minimal GA API. It is not presented as a GA production deployment. The `low` effort setting performs actual LLM planning; vectors and a vectorizer enable hybrid retrieval. Do not mix examples for other API versions into these requests.

Free Search does not provide the outbound managed identity needed here. Reuse an existing authorized Basic-or-higher service when available. **Basic has ongoing charges while retained**, and embedding, planning, generation, and judging can incur usage charges.

<a id="setup"></a>
## 2. Azure setup and permissions

**Check before creating additional paid resources:** the recorded V1 comparison requires answer deployment **`eval-model` / `gpt-6-luna` / version `2026-09-22`**, in `swedencentral`. A historical run does not guarantee current version availability or quota in your subscription. If you cannot meet this condition, choose the [fixed-policy introductory LIVE path](../../README.md#lab-0) or [DEMO](offline.md) before creating Search or additional models. Do not compare a different model version with recorded V1.

The code compares the name, model, version, and `type: ModelDeployment` in [V1's `model_snapshot`](../../advanced-rag/fixtures/recorded-v1.json). **Matching only the model name is insufficient.** Do not edit the fixture or a shared deployment to force a match.

- Also [check model availability](reference.md#model-availability) for the embedding/planning models below and **GlobalStandard capacities 40/60** in the same Foundry account before proceeding. These are deployment capacity settings, not spending caps.
- Obtain the owner's approval to create/use Search and models and to assign roles at the **Search and Foundry resource scopes**. An authorized administrator must prepare missing roles if you cannot assign them. Confirm ongoing Basic charges, usage charges, preview permission, and network access first.

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
az search service show --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,identity:identity,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth,semanticSearch:semanticSearch}" -o json
```

Confirm `Succeeded/succeeded`, `swedencentral`, Basic-or-higher SKU, `disableLocalAuth: true`, and `identity.principalId`. `semanticSearch` must be `free` or an already approved `standard` plan. Follow only [user ID lookup and Search role setup](optional-rag.md#search-access) for **Search Service Contributor** and **Search Index Data Contributor**, then return here. Its `YOUR-SEARCH-NAME` is the service above; do not continue into Optional RAG section 3.

<a id="search-model-access"></a>
Now check IAM for **Cognitive Services OpenAI User** on the parent Foundry account for the **Search identity from `identity.principalId`**, and assign it only if missing. `YOUR-FOUNDRY-RESOURCE-ID` ends at `/accounts/ACTUAL-ACCOUNT`, without `/projects/...`. Do not substitute the project or user identity:

```bash
az role assignment create --assignee-object-id "YOUR-SEARCH-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

**Distinguish the callers.** Document embeddings and `vector`/`hybrid` query embeddings use **your terminal's `AzureCliCredential`**; service-side vectorization/planning uses the **Search identity**; cloud evaluation uses the **project identity** from shared setup. Retain the existing Foundry User access for your user and project. A successful role assignment does not mean calls work immediately. For 401/403, verify the principal, scope, propagation, and network, then resume the same stage—without duplicate roles or API-key fallback.

**Official guidance has different scopes:** the [vectorizer article](https://learn.microsoft.com/azure/search/vector-search-vectorizer-azure-open-ai) specifies OpenAI User as above, while the [Knowledge Base article](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base) specifies broader Cognitive Services User access for planning. Distinguish these from this code's Azure OpenAI endpoint/API version. If only planning is denied, verify the target API's permissions with the owner rather than speculatively adding a broader role.

### Additional models and configuration

Replace `YOUR-EMBEDDING-VERSION`/`YOUR-PLANNER-VERSION` with the versions verified earlier, then deploy the models **sequentially**. Confirm the first deployment is `Succeeded` before running the next command. Concurrent writes to the same Foundry account can conflict. If an authorized deployment already exists, verify its model/version and skip its creation command. Do not silently update shared deployments.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-embedding --model-name text-embedding-3-small --model-version "YOUR-EMBEDDING-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 40 --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-planner --model-name gpt-5.4-mini --model-version "YOUR-PLANNER-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

**Checkpoint:** in Foundry Models + endpoints, confirm both `rag-embedding` and `rag-planner` succeeded with the intended models/versions. The recorded additional-model versions were embedding `1` and planner `2026-03-17`. You can select currently supported versions for these two models, but must keep them unchanged after `setup` within this experiment. Keep the answer model at the recorded V1 version verified earlier.

Save [the configuration template](../../advanced-rag/config.example.json) as **`config.advanced.json` beside `advanced_lab.py`**, not inside `advanced-rag/`. Keep the existing `config.json`.

Keep the template's `top_k: 4`, 1536 embedding dimensions, and `low` planning effort. Do not confuse these with Optional RAG's `config.rag.json` or `top_k: 3`. Deployment names must match the actual deployments just verified.

| Setting | Where to find the actual value |
|---|---|
| `search_endpoint` | Azure portal → intended Search service → Overview URL |
| `model_resource_endpoint` | The same parent Foundry resource's Keys and Endpoint page: use the **Azure OpenAI resource endpoint** ending in `.openai.azure.com`, not the project endpoint. Do not copy API keys |
| `index_name`, `knowledge_source`, `knowledge_base` | Authorized names unique to the participant/experiment, such as `travel-vector-a7k3m9`, `travel-vector-ks-a7k3m9`, `travel-planned-kb-a7k3m9` |

**Sharing a service does not mean unconditionally sharing search objects or experiments.** Choose the three object names before the first run and keep them when resuming that experiment. Reuse objects only with the owner's permission and the same corpus, vector settings, model endpoint, deployments, and planning settings. `setup` stops rather than updating mismatched existing objects; use new object names for another experiment.

Embeddings use the account's `/openai/v1/embeddings` endpoint with Entra authentication. The author's earlier project gateway returned 404 for embeddings; this is not a universal limitation of every Foundry endpoint. Use the `.openai.azure.com` endpoint required by this code, without API keys.

```bash
python advanced_lab.py setup
```

`setup` checks existing object contracts, prepares the embedding cache, creates a missing index/uploads documents, and then creates the Knowledge Source and planned Knowledge Base.

**Checkpoint:** `VECTOR SETUP OK: 7 documents, 1536 dimensions`. `results/advanced/setup.json` retains model snapshots, intended upload count, and server HNSW/vectorizer/knowledge-object definitions; `embedding-cache.json` retains document vectors. Successful setup alone does not validate retrieval or answer quality: continue with the actual queries in section 3.

The smaller [optional text-RAG lab](optional-rag.md) can use this **same Search endpoint** in `config.rag.json`, with its distinct index/base names. Do not point both workflows at the same index name.

<a id="resume"></a>
### Command status, interruption, and resumption

<details>
<summary>Open only for waiting, errors, or resuming later</summary>

Outputs are fixed under **`results/advanced/`**. Use this table rather than introductory `run.json`/`run --out` instructions. Restore your virtual environment and sign-in in a new terminal; never run the same experiment concurrently in two terminals.

| Result | Next action |
|---|---|
| Connection failure/interruption during `setup` | Resolve the cause and repeat the same `setup`. It reuses the matching corpus/model embedding cache and matching objects, then continues missing work. Contract mismatches are not overwritten |
| `GENERATION COMPLETE` or `Evaluation complete` | Check the stage's count and saved evidence, then continue. Completion does not mean acceptance |
| `아직 처리 중입니다` / exit `3` | Repeat the **entire original command**: the same `calibrate` for calibration, or the same `judge --stage …` for judging. It retrieves the saved remote job |
| Transient connection failure or interruption during generation | Resolve the cause, then repeat the same `run --stage …`. Saved responses are not regenerated. A response interrupted before persistence can incur another charge |
| `initial clarification/handoff field checks failed` / exit `1` | Initial quality failure. Read `<stage>/generation.json` at `pending → case ID → initial_response → response`, and preserve the failure. Repeating the command cannot resample a better answer |
| Calibration exit `2` with `mismatches` | Record misclassified IDs/scores from `calibration-result.json` and scoring reasons from `calibration/report.md`, then stop. Do not lower thresholds or repeatedly judge until passing |
| `freeze`: `Dev acceptance is not met` / exit `1` | Read dev judge reasons in `report.md`, and business checks/retrieved chunks with `inspect`; preserve failures. Do not create holdout yet |
| Interrupted `create-holdout` / `Holdout files already exist` | Check `holdout-data/` and registration. If all four data files are complete and belong to this frozen contract, but registration alone is missing, use `python advanced_lab.py register-holdout`. If already registered, continue with `run --stage holdout`. Preserve incomplete data files and use a new experiment rather than resampling |
| `LAB_ACCEPTANCE_BLOCKED` / exit `2` | Completed holdout failed a criterion. Record reasons from `acceptance-report.md`/`acceptance-result.json`, then go to section 8 |
| Other `ERROR:`, or `usage:` / `error:` | Resolve environment, input, or command errors first. In particular, exit `2` with `usage:` is an argument error, not a quality decision |

**An initial quality failure leaves `generation.json` in `collecting` state.** You cannot use `judge` or `inspect` as if generation completed, or obtain a final decision with `accept`. Read the saved initial response in JSON and the terminal error directly, mark later stages as not run, and preserve them in section 8. This CLI's `inspect` requires both generation and judging to be complete for that stage.

Calibration/judging has a default **300-second status-polling budget**. Authentication, submission, HTTP responses, and result collection can make total command time longer.

| Artifact, relative to `results/advanced/` | Purpose |
|---|---|
| `setup.json`, `vector-query.json`, `planned-query.json` | Actual search configuration and retrieval evidence |
| `embedding-cache.json` | Reusable document vectors for the same corpus/model |
| `evaluator.json`, `calibration-controls.json` | Custom evaluator definition/version and calibration inputs/pass labels |
| `calibration-result.json`, `judge-contract.json` | Calibration result and accepted judge contract |
| `<stage>/generation.json` | `status`, completed response `rows`, and unfinished-case `pending` |
| `<stage>/evaluation-request.json` | Evaluation inputs and **local correlation `run_id`**. Calibration uses `calibration/` |
| `<stage>/foundry-job.json` | Remote `eval_id`, `run_id`, and job state; the same applies to calibration |
| `<stage>/judge.json`, `<stage>/report.md` | Completed scores and reasons |
| `frozen.json`, `holdout-registration.json` | Frozen candidate and fresh-question registration contracts |
| `holdout-data/cases.jsonl`, `labels.json`, `followups.json`, `provenance.json` | Fresh questions, retrieval labels, user follow-ups, and provenance; all four are inside `holdout-data/` |
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

**Checkpoint:** `llm_query_planning: true`, actual generated search queries, and `modelQueryPlanning`/`searchIndex` activity. The author's recorded request produced three subqueries, but their count and wording are not fixed outputs. The code rejects a response without planning evidence rather than calling ordinary search “planned retrieval.”

<a id="calibration"></a>
## 4. Calibrate and freeze the judge

Read [the policy task-success rubric](../../advanced-rag/policy-task-success.txt). It treats correct missing-date questions and appropriate “policy does not specify” answers as **valid initial behavior**, while rejecting invented limits/approvals and contradictory answers. Correct initial behavior alone does not complete the final dialogue.

If calibration below is still processing or errors, use the **calibration row** in the [status/resume table](#resume).

```bash
python advanced_lab.py calibrate
```

**Checkpoint:** `CALIBRATION PASSED: 10 controls`. Four correct controls and six incorrect controls—including a grading-instruction attack and extra citations—must be classified correctly. The pass/fail labels are not sent to the judge. Calibration tests **only `policy_task_success`** with authored responses and expected behavior; it is not held-out model performance or separate calibration of builtin Groundedness/Relevance.

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

```bash
python advanced_lab.py inspect --stage v1-recorded --case-id D02
```

**Checkpoint:** four imported answers and `Evaluation complete: 4 cases × 3 metrics`. Use `inspect` for D02's failed `citations` business check and scores; read scoring reasons in `results/advanced/v1-recorded/report.md`. `baseline` imports a local record, but `judge` above is a **paid LIVE evaluation with the currently fixed judge**, not a copy of historical scores.

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

**Checkpoint:** confirm `GENERATION COMPLETE: v2-replay; 4 answers.` and completed judging of 4 cases × 3 metrics. V1 and V2 start from identical saved contexts and use the same answer model/settings/judge, with explicit user follow-ups completed where needed. This is a **prompt-and-dialogue workflow improvement**, not a claim that prompt wording alone explains the result. Keep the V1 failure; do not weaken V1 or reroll it.

<a id="freeze"></a>
## 6. Validate the full pipeline, then freeze

```bash
python advanced_lab.py run --stage planned-dev
```

```bash
python advanced_lab.py judge --stage planned-dev
```

This is a separate integration check using actual vector/LLM-planned retrieval. Both initial questions and necessary follow-up turns use the declared retrieval workflow. **Confirm four final answers and completed judging of 4 cases × 3 metrics** before freezing. Judge exit code 0 alone does not mean dev acceptance.

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

**Checkpoint:** `HOLDOUT REGISTERED: 8 new cases` and `holdout-registration.json`. This command creates and registers questions together, without a model call. It refuses to replace existing holdout files. Do not resample to obtain a pass; follow the [resume table](#resume) after interruption.

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

**Checkpoint:** `results/advanced/acceptance-report.md` and `acceptance-result.json` retain your run's decision, metrics, and per-case checks. Read scoring reasons in `holdout/report.md`. `LAB_ACCEPTANCE_PASSED` requires all eight fresh scenarios to pass **every final-answer metric, including Relevance, plus the initial field checks**. `LAB_ACCEPTANCE_BLOCKED` is also a valid evaluation result to preserve.

If blocked, record the failure and hold recommendation, then go to section 8. Even with an automated pass, record any contradiction you find in the initial prose and withhold production adoption. Do not edit the frozen prompt/rubric or select only passing cases. A subsequent improvement uses a [new experiment in a separate working copy](#resume) with new held-out cases.

<a id="results"></a>
## Result interpretation

**The table below records one September 28, 2026 fresh-environment complete-path run, not a reproduction guarantee.** A new group, Foundry resource, models, and Basic Search were provisioned; an isolated working copy ran the shared N01 setup smoke through final validation. Use your own acceptance files for your decision. Neither this table nor its videos revalidates the entire separate introductory LIVE path or minimal-RAG `search`/`iq` comparison in the current environment.

The four genuine earlier V1 answers were imported and **freshly judged in the new environment**. V1 Relevance passed at 50%, with D04 and D08 scoring 3; the previous run's 100% was not copied. V2 generation and judging ran live, followed by exactly one new holdout after freezing. Instructions, criteria, and the fixture were not changed, and grades were not resampled.

| Stage | Business | Retrieval | Groundedness | Relevance | Policy task success |
|---|---|---|---|---|---|
| Recorded V1, 4 one-turn cases, freshly judged | 75% | 100% | 100% | 50% | 75% |
| V2 completed dev, 4 scenarios | 100% | 100% | 100% | 100% | 100% |
| V2 planned/vector dev, 4 scenarios | 100% | 100% | 100% | 100% | 100% |
| New frozen holdout, 8 scenarios | 100% | 100% | 100% | 100% | 100% |

All recorded V2 dev/holdout final judge scores are at least 4/5; the threshold was not lowered. These V2 cases have no critical failures. The task definitions include explicit clarification/handoff follow-ups, so this is not a claim that an incomplete first turn answered an impossible question.

Intermediate clarification is retained as evidence, and user follow-up data is explicit. This is not a separate automated semantic pass for the initial prose. Production approval remains a separate human responsibility.

<a id="retention"></a>
## 8. Preserve results and resources

Keep the shared Basic Search service, embedding/planning/answer deployments, and every calibration, V1/V2, freeze, and fresh-question result you actually produced, **including failures**. Use generated reports to identify the last completed stage, pass/hold reasons, and unperformed work; establish the resource owner and next cost-review point. Basic service charges continue.

**Checkpoint:** use your result files and actual dialogues to explain V1's failure, V2's changes, and fresh-question results and limitations. If an earlier stage stopped, state that later stages were not run, and verify the retained resources and cost status.

**The following is the author's historical migration record, not a learner deletion step.** Do not delete resources without a separate decision. Never delete the resource group or shared Foundry account to clean one Search service. Do not rewrite Git history or platform audit logs, or disable organizational policies.

**September 28, 2026 rebuild record:** the owner explicitly requested deletion of the previous dedicated workshop group. Its deletion was verified before the rerun in a new group. Previous local results and raw recordings were preserved. Retain the new Basic service, Foundry resource, three model deployments, and current calibration/V1/V2/holdout evidence **until a separate request**. No other groups or organizational policies were changed.

**Cost checkpoint:** a MonthToDate Cost Management query scoped to the new group returned no cost rows yet. This is pending cost reporting, not proof of free usage; Basic capacity and model usage can continue to incur charges. Recheck after usage is posted or when a separate cleanup decision is made.

Local `config*.json`, raw recordings, and `results/` remain outside Git. The versioned prompts and sanitized teaching fixture are source material for the new lesson.

## Official references

- [Agentic vector index and vectorizer](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-index)
- [Knowledge-base features and models by API version](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base)
- [Azure OpenAI vectorizer identity and role](https://learn.microsoft.com/azure/search/vector-search-vectorizer-azure-open-ai)
- [LLM retrieval reasoning effort](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [Search tier feature support](https://learn.microsoft.com/azure/search/search-sku-tier)
- [Embeddings with Entra authentication](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings)
- [Custom Foundry evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)

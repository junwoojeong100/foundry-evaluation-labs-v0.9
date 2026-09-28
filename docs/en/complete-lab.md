**English** | [한국어](../complete-lab.md)

# Complete lab: failure → improvement → reevaluation → fresh-question acceptance

[Repository home](../../README.md)

[Updated English/Korean recorded summaries](../media/complete-rag/README.md) show the current completed workflow.

This is the recommended complete learning path. It uses **one Basic-or-higher Azure AI Search service** for both ordinary RAG and **vector/hybrid + LLM-planned Foundry IQ retrieval**. A separate Search service is not required for each exercise.

The original `prompts/v1.txt`/`v2.txt` and earlier examples are historical introductory material. This path uses the explicitly versioned **`advanced-rag/instructions.v1.txt` and `instructions.v2.txt`**.

## What “passed” means

The acceptance criteria in [acceptance.json](../../advanced-rag/acceptance.json) are fixed before the fresh holdout:

- **Every final V2 case** must pass business checks, required-evidence retrieval, Groundedness, **builtin Relevance**, and policy task success: **100%**, not an average that hides a failed case.
- Each required judge score must be at least **4/5**, with **zero critical-case failures**.
- The policy judge must correctly classify **all ten positive/negative calibration controls**.
- A real vector index/vectorizer and actual `modelQueryPlanning` activity are required.
- At least eight fresh holdout cases must be registered after freezing the candidate.

**Builtin Relevance remains a required metric.** The final answer must resolve the actual completed user interaction. A request for missing information is an intermediate step, not falsely labeled as a completed answer.

V2 uses explicit, scripted user follow-ups from evaluation data: a missing-date case receives the user's actual travel date after asking; an unavailable overseas-limit case receives a user request for a Finance inquiry checklist rather than a fabricated number. The model does not invent those user facts. The final conversation is supplied consistently to the judge, and the initial clarification/handoff behavior is also checked.

`LAB_ACCEPTANCE_PASSED` means these declared educational criteria passed. **Human production approval remains separate and pending.**

<a id="architecture"></a>
## 1. One shared Search service

| Component | Purpose |
|---|---|
| Basic Search service in `swedencentral` | Hosts every index and knowledge base for this path |
| `travel-rag-index` / `travel-policy-kb` | Optional minimal text-retrieval exercise on the same service |
| `travel-vector-index` | Real 1536-dimensional HNSW vectors plus searchable policy text |
| `travel-vector-ks` / `travel-planned-kb` | Foundry IQ source/base with an LLM planning model |
| `rag-embedding` | `text-embedding-3-small`, used for document and query vectors |
| `rag-planner` | Supported `gpt-5.4-mini` planner; not the answer model |
| `eval-model` | `gpt-6-luna` for answers and evaluation |

The full IQ path uses **`2026-08-01-preview`**, because LLM query planning is not in the minimal GA API. It is not presented as a GA production deployment. The `low` effort setting performs actual LLM planning; vectors and a vectorizer enable hybrid retrieval.

Free Search does not provide the outbound managed identity needed here. Reuse an existing authorized Basic-or-higher service when available. **Basic has ongoing charges while retained**, and embedding, planning, generation, and judging can incur usage charges.

<a id="setup"></a>
## 2. Azure setup and permissions

First complete [Foundry account/project/model setup](../../README.md#prepare), using the intended account and `swedencentral`. Keep the answer deployment `eval-model`. Do not create another Free Search service for this complete path.

Create one shared Search service, or reuse an authorized existing Basic service:

```bash
az search service create --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku basic --replica-count 1 --partition-count 1 --identity-type SystemAssigned --semantic-search free --disable-local-auth true
```

Grant the user **Search Service Contributor** and **Search Index Data Contributor** on that service, as in [the optional setup](optional-rag.md#create-search). Retrieve its system-assigned identity:

```bash
az search service show --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,identity:identity,sku:sku.name,state:provisioningState}" -o json
```

Grant that **Search identity**, not the project/user identity, **Cognitive Services OpenAI User** on the parent Foundry account:

```bash
az role assignment create --assignee-object-id "YOUR-SEARCH-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

Check current catalog availability/quota, then deploy the two additional models **sequentially**. Concurrent writes to the same Foundry account can conflict.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-embedding --model-name text-embedding-3-small --model-version "YOUR-EMBEDDING-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 40 --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-planner --model-name gpt-5.4-mini --model-version "YOUR-PLANNER-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

The verified versions were embedding `1`, planner `2026-03-17`, and answer `gpt-6-luna` `2026-09-22`. The recorded V1 comparison requires the same answer-model version; do not silently compare it with another version.

Save [the configuration template](../../advanced-rag/config.example.json) as **`config.advanced.json`**. Use your actual shared Search URL and the account's **Azure OpenAI resource endpoint** ending in `.openai.azure.com`, not the project endpoint.

Embeddings use the account's `/openai/v1/embeddings` endpoint with Entra authentication. The project gateway supported chat/evaluation but returned 404 for embedding requests in this environment. API keys are not used.

```bash
python advanced_lab.py setup
```

**Checkpoint:** `VECTOR SETUP OK: 7 documents, 1536 dimensions`; inspect `results/advanced/setup.json`. Text, vectors, HNSW, vectorizer, source, and planned knowledge base are real service objects.

The smaller [optional text-RAG lab](optional-rag.md) can use this **same Search endpoint** in `config.rag.json`, with its distinct index/base names. Do not point both workflows at the same index name.

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

Read [the policy task-success rubric](../../advanced-rag/policy-task-success.txt). It treats correct missing-date questions and appropriate “policy does not specify” answers as valid task completion, while rejecting invented limits/approvals and contradictory answers.

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

```bash
python advanced_lab.py freeze
```

**Checkpoint:** `FROZEN` and a contract hash. V1 must contain a real failure; V2 replay and planned dev must meet the required criteria. The prompt, judge, model versions, retrieval configuration, source definitions, and corpus are fixed before fresh cases are created.

<a id="holdout"></a>
## 7. Generate fresh questions only after freeze

```bash
python advanced_lab.py create-holdout
```

This creates eight balanced scenarios with a newly generated seed. They cover current/previous limits, over-limit approval, overseas scope, missing dates, prohibited flight class, and the exact boundary. The missing-date and overseas-handoff scenarios include explicit evaluation-user follow-ups. Inputs, follow-ups, and provenance are stored privately under `results/advanced/holdout-data/`.

The command refuses to replace existing holdout files. Do not resample to obtain a pass.

```bash
python advanced_lab.py run --stage holdout
```

```bash
python advanced_lab.py judge --stage holdout
```

```bash
python advanced_lab.py accept
```

**Checkpoint:** `LAB_ACCEPTANCE_PASSED`, eight completed scenarios, and **every final answer passing every required metric, including Relevance**. Read `results/advanced/acceptance-report.md` and `acceptance-result.json`. Initial clarification/handoff checks must also pass.

If blocked, keep the failed run. Do not edit the frozen prompt/rubric or choose only passing holdout cases. A subsequent improvement must be a new experiment with new held-out cases.

<a id="results"></a>
## Result interpretation

The earlier Relevance-excluded acceptance attempt is **not the final success result**. The revised iteration passed all metrics on every final V2 case:

| Stage | Business | Retrieval | Groundedness | Relevance | Policy task success |
|---|---|---|---|---|---|
| Recorded V1, 4 one-turn cases | 75% | 100% | 100% | 100% | 75% |
| V2 completed dev, 4 scenarios | 100% | 100% | 100% | 100% | 100% |
| V2 planned/vector dev, 4 scenarios | 100% | 100% | 100% | 100% | 100% |
| New frozen holdout, 8 scenarios | 100% | 100% | 100% | 100% | 100% |

All final judge scores are at least 4/5; the threshold was not lowered. There are no critical failures. The task definitions include explicit clarification/handoff follow-ups, so this is not a claim that an incomplete first turn answered an impossible question.

Intermediate clarification is retained as evidence, and user follow-up data is explicit. Production approval remains a separate human responsibility.

<a id="retention"></a>
## 8. Keep the current evidence; clean only superseded resources

Keep the shared Basic Search service, embedding/planning/answer deployments, current calibration, V1/V2 comparison, frozen contract, and fresh acceptance evidence.

For this repository's migration, the former Free Search service and superseded core/minimal-RAG cloud/local run records are cleaned **only after this path and its new recordings are complete**. Never delete the resource group or shared Foundry account to clean one Search service. Git history and platform audit logs are not rewritten; organizational policies are not disabled.

**Migration cleanup is complete:** the former Free service, eight superseded evaluation groups, two old comparison insights, one obsolete custom-evaluator version, the old failed deployment-history entry, and the explicitly scoped local legacy results were removed. The shared Basic service and current calibration/V1/V2/holdout evidence remain. Removing a deployment-history entry does not repair or disable an organizational policy.

Local `config*.json`, raw recordings, and `results/` remain outside Git. The versioned prompts and sanitized teaching fixture are source material for the new lesson.

## Official references

- [Agentic vector index and vectorizer](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-index)
- [LLM retrieval reasoning effort](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [Search tier feature support](https://learn.microsoft.com/azure/search/search-sku-tier)
- [Embeddings with Entra authentication](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings)
- [Custom Foundry evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)

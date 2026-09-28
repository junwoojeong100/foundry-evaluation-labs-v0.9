**English** | [한국어](../complete-lab.md)

# Complete lab: failure → improvement → reevaluation → fresh-question validation

[Repository home](../../README.md)

**Jump to:** [Start](#architecture) · [Setup](#setup) · [Resume](#resume) · [Finish](#retention)

**Retrieve policy, improve answers, then check fresh questions.** Use the fictional Gaon Lab travel-expense assistant to learn **RAG (retrieval-augmented generation)**: answering from retrieved evidence.

| At a glance | This path |
|---|---|
| Execution | **LIVE only, paid**. Run provided commands; no Python coding |
| Full environment | **One Basic-or-higher Search service + three model deployments** in `swedencentral` |
| Files you edit | `config.json` and `config.advanced.json` during setup |
| Instructions | **Read and compare** `advanced-rag/instructions.v1.txt` and `instructions.v2.txt` |
| Results | `results/advanced/`; a completed run produces `acceptance-report.md` for the final decision |

The policy inputs, example queries, and model answers remain **Korean** so both language guides run the same experiment. Section 1 links an English policy translation for reading; do not replace the experiment's source data.

**Follow only sections 1–8 of this guide.** Introductory activities 0–6 and the full Optional RAG exercise are not prerequisites. Section 2 borrows shared setup, then returns here. Do not edit or substitute the introductory `prompts/v1.txt`/`v2.txt` files.

<a id="lab-map"></a>
## Progress map

| Step | Your action | Check before continuing |
|---|---|---|
| [1. Policy and components](#architecture) | Decide what a correct answer means | A policy-based reason |
| [2. Setup](#setup) | Shared setup → return here → Search, extra models, configuration | `VECTOR SETUP OK` |
| [3. Real retrieval](#retrieval-proof) | Check vector retrieval and LLM planning separately | Two `RETRIEVAL OK` messages and retrieval evidence |
| [4. Check the judge](#calibration) | Test the judge against known correct/incorrect answers | `CALIBRATION PASSED: 10 controls` |
| [5. V1 → V2](#improve) | Compare an earlier failure with V2's behavior | Four answers and three metrics in each run |
| [6. Integration and freeze](#freeze) | Check V2 with real retrieval, then lock changes | `FROZEN` |
| [7. Fresh questions](#holdout) | Create and evaluate eight new cases after freezing | Your own `acceptance-report.md` |
| [8. Finish](#retention) | Interpret and retain results; check costs | Completion checklist or interruption record |

<a id="reading-guide"></a>
### How to read this guide

**Follow the action → command → checkpoint → next step.**

| Marker | How to use it |
|---|---|
| `bash` code block | Terminal commands. Copy one command at a time and wait for the prompt to return |
| `text` code block | Expected output, not a command to execute |
| `YOUR-...` | Replace with a value verified in your environment; keep quotation marks |
| **Checkpoint** | The message, count, or result to check before continuing |
| Collapsed explanation | Answers, exceptions, or background; expand when needed |

**Where to run:** the folder containing `advanced_lab.py`, with the virtual environment active. Copy each long command as **one complete line**, without inserting Enter in the middle. Output folders are automatic; read `.md` reports in VS Code's Markdown preview. If blocked, use the [status/resume table](#resume).

> [!IMPORTANT]
> **Lab completion is not the same as automated acceptance.** Preserve low scores and stopped runs. Do not mark unperformed stages complete or apply the introduction's 80% gate and D06/H04 review workflow here.

Use each checkpoint and the generated results. No separate record form is needed; personal notes are optional.

**Start here:** [1. Read the policy](#architecture). The glossary and videos below are optional references.

<details>
<summary>Terms: chunks, vectors, Knowledge Base, judge, and holdout</summary>

| Term | Meaning in this lab |
|---|---|
| Chunk / index | A chunk is a policy fragment; an index stores fragments so they can be searched |
| Vector / hybrid retrieval | Find similar meanings using numeric representations of text / combine that with text search |
| Knowledge Source / Knowledge Base | A connection specifying which index to read / a knowledge base that uses the connection to handle retrieval requests |
| LLM query planning | AI turns a complex question into searches for evidence; this is a different role from answering the employee |
| Judge / calibration | An AI grader / checking whether it distinguishes known correct and incorrect examples |
| V1 / V2 | Instruction versions before/after improvement; V2 also completes necessary user follow-ups |
| dev / holdout / freeze | Questions for checking improvements / fresh final-check questions / recording and locking prompt, model, retrieval, and judging conditions before fresh questions |

</details>

<details>
<summary>Which operations incur calls, and optional reference videos</summary>

`advanced_lab.py` has no DEMO mode. Importing `baseline`, freezing, creating/registering holdout, inspecting, and accepting are local operations; setup, retrieval, generation, calibration, and judging use real Azure services.

Videos are optional. The [English/Korean summaries](../media/complete-rag/README.md) and [recorded results](#results) come from a **separate September 28, 2026 run**, not your completion signals or expected scores.

</details>

---

<a id="architecture"></a>
## 1. Read the policy and understand the components

### 1-1. Make a policy-based judgment

**Before installing anything:** read the [English policy translation](policies.md), or the [Korean source](../../data/policies.md), and answer:

> A domestic business-trip hotel costs KRW 220000 per night in September 2026, without prior approval. Can the employee claim it immediately?

<details>
<summary>Read the explanation after deciding</summary>

The current official limit is KRW 200000. KRW 220000 exceeds it, so prior Finance approval is required. Do not apply the unapproved draft's KRW 240000 limit. For earlier trips, apply the policy for the **actual travel date**, not the submission date. Do not guess missing dates or an overseas limit absent from the policy.

</details>

**Checkpoint:** explain the decision and policy-based reason in one sentence.

### 1-2. Distinguish the component roles

Understand **the roles only**. HNSW names a vector-search algorithm; you do not need to implement it or change its settings.

| Component | Purpose |
|---|---|
| Basic Search service in `swedencentral` | Hosts every index and knowledge base for this path |
| `travel-vector-index` | Real 1536-dimensional HNSW vectors plus searchable policy text |
| `travel-vector-ks` / `travel-planned-kb` | Foundry IQ source/base with an LLM planning model |
| `rag-embedding` | `text-embedding-3-small`, used for document and query vectors |
| `rag-planner` | Supported `gpt-5.4-mini` planner; not the answer model |
| `eval-model` | `gpt-6-luna` for answers and evaluation |

**API scope:** LLM query planning uses **`2026-08-01-preview`, pinned in the code**. This is a **preview feature**, not the minimal GA API or a GA production deployment.

The `low` effort setting performs actual LLM planning; vectors and a vectorizer enable hybrid retrieval. Do not mix examples for other API versions into these requests.

Free Search does not provide the outbound managed identity needed here. Reuse an existing authorized Basic-or-higher service when available. **Basic has ongoing charges while retained**, and embedding, planning, generation, and judging can incur usage charges.

**Next:** [2. Setup](#setup) · [Progress map](#lab-map)

---

<a id="setup"></a>
## 2. Azure setup and permissions

> [!WARNING]
> **Check the answer-model version before creating Search or extra models.** Recorded V1 requires **`eval-model` / `gpt-6-luna` / version `2026-09-22`** in **`swedencentral`**. If unavailable, choose [introductory LIVE](../../README.md#lab-0) or [DEMO](offline.md). Do not compare results from another model version.

**Four checks before creating resources**

| Check | Required condition |
|---|---|
| Answer deployment | Model name, deployment name, and version match [V1's `model_snapshot`](../../advanced-rag/fixtures/recorded-v1.json). Do not edit evidence or shared deployments to force a match |
| Additional models | Supported embedding/planning versions and **GlobalStandard capacities 40/60** in the same Foundry account. See [availability guidance](reference.md#model-availability) |
| Permissions | Approval to create/use Search/models and assign roles at **Search and Foundry resource scopes**. An authorized administrator prepares missing roles |
| Cost and policy | Ongoing Basic and usage charges, preview permission, and network access confirmed. Capacities 40/60 are not spending caps |

A historical run does not guarantee current model-version availability or quota.

**Setup has six steps below.** After returning from shared setup once, **continue on this page without visiting Optional RAG**. When reusing resources, skip their creation commands but still perform the lookups and permission checks.

| Setup step | Action |
|---|---|
| [2-1. Shared environment](#common-setup) | Python, sign-in, Foundry, answer model, and one-case evaluation |
| [2-2. Actual values](#search-setup) | Distinguish names/IDs; check answer version and extra-model availability |
| [2-3. Search](#search-service) | Prepare one service; retrieve its resource and managed-identity IDs |
| [2-4. Permissions](#search-access) | Check user → Search and Search identity → model access |
| [2-5. Extra models](#extra-models) | Deploy embedding and query-planning models |
| [2-6. Configuration](#configure) | Save `config.advanced.json` and create search objects |

The complete configuration uses **three model deployments and one Search service**. Shared setup's single model is the answer/judge deployment within that total. The number of new resources depends on reuse.

<details>
<summary>See workload counts for cost planning</summary>

These counts cover one uninterrupted completion starting with shared setup. **New responses include intermediate dialogue turns**; evaluation items count per-answer metrics.

| Stage | Newly generated responses | Evaluation items |
|---|---|---|
| `setup-smoke` | 1 | 2 |
| `calibration` | 0 — use 10 authored control answers | 10 |
| `v1-recorded` | 0 — import 4 earlier answers | 12 |
| `v2-replay` | 6 — 4 final + 2 initial | 12 |
| `planned-dev` | 6 — 4 final + 2 initial | 12 |
| `holdout` | 10 — 8 final + 2 initial | 24 |
| Total | **23** | **72** |

These are not billable API-request counts or spending caps. Account separately for ongoing Search charges, embeddings, query planning, evaluator internals, and retries. Interruptions and reuse of saved results also affect actual calls.

</details>

<a id="common-setup"></a>
### 2-1. Prepare the shared environment

1. **Keep this page open** and follow [README setup 1–7](../../README.md#prepare) in a new tab. For authorized existing resources, use [existing-environment setup](setup.md#existing-environment).
2. Check the answer-model version in [setup 5](../../README.md#setup-model).
3. Create `config.json` and finish the one-case generation/evaluation check. Introductory A/B and activities 1–6 are not prerequisites.

> **Return here:** after setup 7 shows `평가 완료: 1개 답변 × 2개 지표` and you inspect N01's scores/reasons, continue to **[2-2 below](#search-setup)**, not README activity 1. Do not regenerate N01 if already completed in the same environment.

<a id="search-setup"></a>
### 2-2. Check actual values and model availability

You should now have `config.json` and one generated, evaluated N01 answer. Replace each `YOUR-...` with **your actual value**, retaining the quotation marks. Names, IDs, and endpoints are not interchangeable.

| Placeholder | Actual value |
|---|---|
| `YOUR-SUBSCRIPTION-ID` | Subscription ID used for shared-setup sign-in |
| `YOUR-LAB-RESOURCE-GROUP` | Actual group containing the command's target resource. If existing Search is in another group, use **that group only for Search commands** |
| `YOUR-FOUNDRY-ACCOUNT` | Parent Foundry resource name, not the project name `eval-workshop` |
| `YOUR-SHARED-SEARCH` | Authorized existing Search name, or a new unique name such as `feval-search-a7k3m9` |
| `YOUR-FOUNDRY-RESOURCE-ID` | Full `id` from the parent Foundry resource's **Overview → JSON View**, ending in `/accounts/ACTUAL-NAME` |
| `YOUR-SEARCH-RESOURCE-ID` | Full `id` from the Search lookup in 2-3; the scope for role assignments |
| `YOUR-SEARCH-PRINCIPAL-ID` | `identity.principalId` from the Search lookup below, not the user or project ID |
| `YOUR-USER-OBJECT-ID` | Your account's `objectId` from the user lookup in 2-4 |

#### Verify the fixed answer-model version

First, read the **already deployed answer model** without changing it:

```bash
az cognitiveservices account deployment show --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name eval-model --subscription "YOUR-SUBSCRIPTION-ID" --query "{name:name,state:properties.provisioningState,model:properties.model.name,version:properties.model.version}" --output json
```

**Checkpoint:** `name: eval-model`, `state: Succeeded`, `model: gpt-6-luna`, and `version: 2026-09-22`. If different, return to the path-selection guidance above without creating more resources.

#### Decide whether to reuse or create additional deployments

**If reusing both embedding and planner deployments too**, verify their models/versions with the owner and under Foundry **Build → Models**, then skip both queries below. Participants not creating deployments do not need new quota allocations or subscription quota-read permission.

**Only when creating additional deployments**, use these two read-only queries for versions and quota. They neither create resources nor invoke models.

```bash
az cognitiveservices model list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?model.name=='text-embedding-3-small' || model.name=='gpt-5.4-mini']" --output json
```

```bash
az cognitiveservices usage list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?name.value=='OpenAI.GlobalStandard.text-embedding-3-small' || name.value=='OpenAI.GlobalStandard.gpt-5.4-mini'].{name:name.value,current:currentValue,limit:limit}" --output json
```

**Check two things in these results**

1. **Version and SKU:** in the first result, check `model.version` and `GlobalStandard` support for each `model.name`. Use those versions in the later deployment commands.
2. **Remaining quota:** the second result's `limit - current` must accommodate the new capacities below. Do not allocate a reused deployment's quota a second time.

| New deployment | Version placeholder | Required capacity |
|---|---|---|
| Embedding | `YOUR-EMBEDDING-VERSION` | 40 |
| Query planning | `YOUR-PLANNER-VERSION` | 60 |

Check model/SKU-specific quota and capacity units. **An empty result or 403 does not mean zero quota.** Use [availability and permission help](reference.md#model-availability) if blocked.

**Next:** [2-3. Search service](#search-service) · [Setup map](#setup)

<a id="search-service"></a>
### 2-3. Prepare the Search service

**If reusing an authorized Basic-or-higher service, or if you already created it, skip both creation-preparation commands below.** Use a unique name only when a new service is needed. `az search service create` can also update an existing service, changing settings such as replicas or authentication. Do not create another Free Search service for this path.

#### Create only if a new service is needed

**Before creating a new service:** in Azure portal, open **Subscriptions → intended subscription → Resource providers** and check **`Microsoft.Search`**. If unregistered, an authorized administrator selects **Register** and confirms `Registered`. This is separate from shared setup's `Microsoft.CognitiveServices`; introductory/DEMO participants not creating Search do not need this additional registration. Follow [official provider-registration guidance](https://learn.microsoft.com/azure/azure-resource-manager/management/resource-providers-and-types); do not bypass missing permission.

```bash
az search service check-name-availability --name "YOUR-SHARED-SEARCH" --type searchServices --subscription "YOUR-SUBSCRIPTION-ID"
```

Create only if `nameAvailable: true`.

```bash
az search service create --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku basic --replica-count 1 --partition-count 1 --identity-type SystemAssigned --semantic-search free --disable-local-auth true
```

#### Everyone: verify the actual service

For both new and existing services, inspect the actual ID, region, SKU, authentication, and system-assigned identity. Obtain the owner's authorization before changing existing settings.

```bash
az search service show --name "YOUR-SHARED-SEARCH" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,identity:identity,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth,semanticSearch:semanticSearch}" -o json
```

**Checkpoint:** every value below matches.

| Field | Required value |
|---|---|
| State, region, SKU | `Succeeded/succeeded` · `swedencentral` · Basic or higher |
| Key authentication | `disableLocalAuth: true` |
| Managed identity | `identity.principalId` is present |
| Semantic Search | `free` or an already approved `standard` plan |

**Distinguish the IDs used next.**

- Full **`id` → `YOUR-SEARCH-RESOURCE-ID`**: the Search resource receiving the role assignments.
- **`identity.principalId` → `YOUR-SEARCH-PRINCIPAL-ID`**: Search's identity when calling models.

**Next:** [2-4. Permissions](#search-access) · [Setup map](#setup)

<a id="search-access"></a>
### 2-4. Set user and Search-identity permissions

#### User identity → Search access

First prepare **user → Search** access. Retrieve the currently signed-in user's ID:

```bash
az ad signed-in-user show --query "{account:userPrincipalName,objectId:id}" --output json
```

Verify that `account` identifies you in the intended tenant, then use **`objectId` as `YOUR-USER-OBJECT-ID`**. Do not substitute the project or Search identity. If directory lookup is restricted, ask the environment owner to verify your user ID in that tenant.

In Search **Access control (IAM) → Role assignments**, check inherited roles too. An authorized role assigner grants **only missing roles**, at the **Search service scope**. Skip both commands if both roles already apply.

**Role 1 — Search Service Contributor**

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

**Role 2 — Search Index Data Contributor**

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

The first role is **Search Service Contributor**, covering search-object/service management and key retrieval. The second is **Search Index Data Contributor**, for document upload and retrieval. **These permissions also cover other participants' objects on the service**: use only the approved shared-workshop scope. Distinct object names are not a security boundary; do not assign subscription-wide roles.

<a id="search-model-access"></a>
#### Search managed identity → model access

Next prepare **Search identity → model** access. Check IAM for **Cognitive Services OpenAI User** on the parent Foundry account for the **Search identity from `identity.principalId`**, and assign it only if missing. `YOUR-FOUNDRY-RESOURCE-ID` ends at `/accounts/ACTUAL-ACCOUNT`, without `/projects/...`. Do not substitute the project or user identity:

```bash
az role assignment create --assignee-object-id "YOUR-SEARCH-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

**There are three distinct callers.**

| Operation | Identity |
|---|---|
| Document embeddings and `vector`/`hybrid` query embeddings | **Your terminal's `AzureCliCredential`** |
| Service-side vectorization and query planning | **Search managed identity** |
| Cloud evaluation | **Project managed identity** from shared setup |

Retain Foundry User access for your user and project. A successful role assignment does not prove immediate data access. For 401/403, check principal, scope, propagation, and network, then resume the same stage. Do not add duplicate roles or fall back to API keys.

**Checkpoint:** verify the two Search roles for your user and the Foundry model-access role for Search in IAM, including **principal IDs and scopes**. Actual data access is checked by `setup` and the queries in section 3.

<details>
<summary>Open only if official articles show different role names</summary>

**Official guidance has different scopes:** the [vectorizer article](https://learn.microsoft.com/azure/search/vector-search-vectorizer-azure-open-ai) specifies OpenAI User as above, while the [Knowledge Base article](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base) specifies broader Cognitive Services User access for planning. Distinguish these from this code's Azure OpenAI endpoint/API version. If only planning is denied, verify the target API's permissions with the owner rather than speculatively adding a broader role.

</details>

**Next:** [2-5. Additional models](#extra-models) · [Setup map](#setup)

<a id="extra-models"></a>
### 2-5. Deploy the additional models

Replace `YOUR-EMBEDDING-VERSION`/`YOUR-PLANNER-VERSION` with the versions verified earlier, then deploy the models **sequentially**. Concurrent writes to the same Foundry account can conflict. If an authorized deployment already exists, verify its model/version and skip its creation command. Do not silently update shared deployments.

**Deployment 1 — `rag-embedding` embedding model**

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-embedding --model-name text-embedding-3-small --model-version "YOUR-EMBEDDING-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 40 --subscription "YOUR-SUBSCRIPTION-ID"
```

**Before the next command:** in Foundry **Build → Models**, confirm the newly created `rag-embedding` is `Succeeded` and uses `text-embedding-3-small`. Resolve any deployment error first.

**Deployment 2 — `rag-planner` query-planning model**

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name rag-planner --model-name gpt-5.4-mini --model-version "YOUR-PLANNER-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

**Checkpoint:** Foundry **Build → Models** shows both `rag-embedding` and `rag-planner` succeeded with the intended models and versions.

The recorded additional-model versions were embedding `1` and planner `2026-03-17`. You can select currently supported versions for these two models, but **keep them unchanged after `setup` within this experiment**. Keep the answer model at the recorded V1 version verified earlier.

**Next:** [2-6. Configuration and connectivity](#configure) · [Setup map](#setup)

<a id="configure"></a>
### 2-6. Write the configuration and create search objects

#### Create the configuration file

1. **In VS Code**, open `advanced-rag/config.example.json`.
2. Use **File → Save As** to create **`config.advanced.json` beside `advanced_lab.py`**.
3. Use the example and endpoint table below to enter your values, then save.

Do not save it inside `advanced-rag/` or as `config.advanced.json.txt`. If your configuration already exists, check its actual values rather than overwriting it.

**Keep both configuration files.**

| File | Connects |
|---|---|
| `config.json` | Project, answer model, and judge |
| `config.advanced.json` | Search, embeddings, and query planning |

#### Replace the example values

The complete [configuration template](../../advanced-rag/config.example.json) follows. **Replace both endpoints and the three search-object names with your values, then save.** If reusing differently named deployments, also update `embedding_deployment`/`planner_deployment` to match their actual names.

```json
{
  "search_endpoint": "https://YOUR-SHARED-SEARCH.search.windows.net",
  "index_name": "travel-vector-index",
  "knowledge_source": "travel-vector-ks",
  "knowledge_base": "travel-planned-kb",
  "top_k": 4,
  "model_resource_endpoint": "https://YOUR-ACCOUNT.openai.azure.com",
  "embedding_deployment": "rag-embedding",
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "planner_deployment": "rag-planner",
  "planner_model": "gpt-5.4-mini",
  "retrieval_reasoning_effort": "low"
}
```

Keep the template's `top_k: 4`, 1536 embedding dimensions, and `low` planning effort. Do not confuse these with Optional RAG's `config.rag.json` or `top_k: 3`. Deployment names must match the actual deployments just verified.

| Setting | Where to find the actual value |
|---|---|
| `project_endpoint` in `config.json` | The **project endpoint** saved during shared setup, containing `.services.ai.azure.com/api/projects/PROJECT`. Do not replace it with either endpoint below |
| `search_endpoint` in `config.advanced.json` | Azure portal → intended Search service → Overview URL, ending in `.search.windows.net` |
| `model_resource_endpoint` in `config.advanced.json` | The same parent Foundry resource's Keys and Endpoint page: use the **Azure OpenAI resource endpoint** ending in `.openai.azure.com`, not the project endpoint. Do not copy API keys |
| `index_name`, `knowledge_source`, `knowledge_base` | Authorized names unique to the participant/experiment, such as `travel-vector-a7k3m9`, `travel-vector-ks-a7k3m9`, `travel-planned-kb-a7k3m9` |

**The three endpoints serve different purposes.** Do not paste one endpoint into every field or merge the two configuration files. Follow the shared [JSON editing guidance](../../README.md#setup-config), changing only the specified values and saving the files.

**Sharing a service does not mean unconditionally sharing search objects or experiments.** Choose the three object names before the first run and keep them when resuming that experiment. Reuse objects only with the owner's permission and the same corpus, vector settings, model endpoint, deployments, and planning settings. `setup` stops rather than updating mismatched existing objects; use new object names for another experiment.

Embeddings use the account's `/openai/v1/embeddings` endpoint with Entra authentication. Store **only the resource endpoint** from the table above. The code appends `/openai/v1/embeddings`; do not append it yourself.

#### Save the files and create search objects

**Before running**

- [ ] Save both files and replace every endpoint placeholder `YOUR-...`.
- [ ] Verify the user, project, and Search identities' roles separately.
- [ ] Keep the supplied instructions, questions, labels, and settings unchanged during this experiment.

```bash
python advanced_lab.py setup
```

`setup` checks existing object contracts, prepares the embedding cache, creates a missing index/uploads documents, and then creates the Knowledge Source and planned Knowledge Base.

**Checkpoint:** `VECTOR SETUP OK: 7 documents, 1536 dimensions`.

| Saved file, relative to `results/advanced/` | Evidence |
|---|---|
| `setup.json` | Model snapshots, intended upload count, and server HNSW/vectorizer/knowledge-object definitions |
| `embedding-cache.json` | Reusable document vectors |

Successful setup is not a retrieval or answer-quality pass. **Continue with the actual queries in section 3.**

<a id="resume"></a>
### Command status, interruption, and resumption

Do not proceed after `ERROR:`. Use [shared troubleshooting](reference.md#troubleshooting) for installation, sign-in, or JSON syntax errors, and the table below for waiting, partial runs, and quality blocks.

<details>
<summary>Open only for waiting, errors, or resuming later</summary>

Outputs are fixed under **`results/advanced/`**. Use this table rather than introductory `run.json`/`run --out` instructions. Restore your virtual environment and sign-in in a new terminal; never run the same experiment concurrently in two terminals.

| Result | Next action |
|---|---|
| Connection failure/interruption during `setup` | Resolve the cause and repeat the same `setup`. It reuses the matching corpus/model embedding cache and matching objects, then continues missing work. Contract mismatches are not overwritten |
| `GENERATION COMPLETE` or `Evaluation complete` | Check the stage's count and saved evidence, then continue. Completion does not mean acceptance |
| `Using complete saved generation; no new model/retrieval calls.` | Completed answers from the same stage were reused. Do not wait for `GENERATION COMPLETE` or regenerate; continue to that stage's `judge` if still needed |
| `Existing frozen experiment retained.` / `Existing holdout registration retained.` | The existing freeze/registration was checked and retained. Use the resume-position table below for the next unfinished step; do not recreate an existing holdout |
| `아직 처리 중입니다` / exit `3` | Repeat the **entire original command**: the same `calibrate` for calibration, or the same `judge --stage …` for judging. It retrieves the saved remote job |
| Transient connection failure or interruption during generation | Resolve the cause, then repeat the same `run --stage …`. Saved responses are not regenerated. A response interrupted before persistence can incur another charge |
| `initial clarification/handoff field checks failed` / exit `1` | Initial quality failure. Read `<stage>/generation.json` at `pending → case ID → initial_response → response`, and preserve the failure. Repeating the command cannot resample a better answer |
| Calibration exit `2` with `mismatches` | Record misclassified IDs/scores from `calibration-result.json` and scoring reasons from `calibration/report.md`, then stop. Do not lower thresholds or repeatedly judge until passing |
| `freeze`: `Dev acceptance is not met` / exit `1` | Read the failed stages/case IDs and report paths printed in the error → run each printed `inspect` command → [compare expectations and actual evidence](#read-case). Preserve failures; do not create holdout yet |
| Interrupted `create-holdout` / `Holdout files already exist` | Check `holdout-data/` and registration. If all four data files are complete and belong to this frozen contract, but registration alone is missing, use `python advanced_lab.py register-holdout`. If already registered, continue with `run --stage holdout`. Preserve incomplete data files and use a new experiment rather than resampling |
| `LAB_ACCEPTANCE_BLOCKED` / exit `2` | Completed holdout failed a criterion. Record reasons from `acceptance-report.md`/`acceptance-result.json`, then go to section 8 |
| Other `ERROR:`, or `usage:` / `error:` | Resolve environment, input, or command errors first. In particular, exit `2` with `usage:` is an argument error, not a quality decision |

**An initial quality failure leaves `generation.json` in `collecting` state.** You cannot use `judge` or `inspect` as if generation completed, or obtain a final decision with `accept`. Read the saved initial response in JSON and the terminal error directly, mark later stages as not run, and preserve them in section 8. This CLI's `inspect` requires both generation and judging to be complete for that stage.

Calibration/judging has a default **300-second status-polling budget**. Authentication, submission, HTTP responses, and result collection can make total command time longer.

**If you cannot remember your last completed step:** find the furthest applicable row below. Check the stage's completion message, status, and count, not file existence alone. **Errors, partial collection, or failed calibration take precedence via the status table above**; do not use this table to skip a failed stage.

| Last completed checkpoint | Continue at |
|---|---|
| `setup.json`; retrieval probes not yet complete | The missing query or queries in [section 3](#retrieval-proof) |
| Both query JSON files; no `judge-contract.json` yet | Calibration in [section 4](#calibration) |
| Passed calibration and `judge-contract.json` | The first unfinished V1 import/judging or V2 generation/judging step in [section 5](#improve) |
| Four V2 replay answers generated and judged | The first unfinished `planned-dev` generation/judging or `freeze` step in [section 6](#freeze) |
| `frozen.json`; holdout not yet registered | `create-holdout` in [section 7](#holdout). If data files already exist, use the recovery row above first |
| `holdout-registration.json`; no final report yet | The first unfinished holdout generation → judging → dialogue review → `accept` step in [section 7](#holdout) |
| `acceptance-report.md` and `acceptance-result.json` | Interpretation, retention, and costs in [section 8](#retention) |

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

**Next:** [3. Real retrieval](#retrieval-proof) · [Progress map](#lab-map)

---

<a id="retrieval-proof"></a>
## 3. Prove vectors and LLM planning are actually used

**This step tests retrieval only; it does not yet produce an employee-facing answer.**

### 3-1. Check vector retrieval

Find semantically similar policy chunks using vectors.

```bash
python advanced_lab.py query --mode vector --query "해외 출장 호텔 숙박비 상한을 확인하고 싶습니다." --out results/advanced/vector-query.json
```

**Checkpoint:** `RETRIEVAL OK: vector`.

**Evidence to inspect:** check `results/advanced/vector-query.json` for:

- `query_vector_dimensions: 1536` — the actual query vector.
- `vector_fields: content_vector`, `text_query: false` — vector retrieval, not text search.
- Returned chunk IDs — the policy fragments actually retrieved.

### 3-2. Check LLM query planning

Send a multi-part question to the query-planning model.

```bash
python advanced_lab.py query --mode planned --query "2026년 6월 30일과 7월 1일 국내 출장 숙박 한도를 비교하고, 한도를 초과할 때 필요한 절차와 해외 숙박 한도가 있는지도 알려주세요." --out results/advanced/planned-query.json
```

**Checkpoint:** `RETRIEVAL OK: planned`.

**Evidence to inspect:** check `results/advanced/planned-query.json` for:

- `llm_query_planning: true` — whether LLM planning ran.
- `planned_queries` — the actual generated subqueries.
- `modelQueryPlanning`/`searchIndex` — planning and retrieval activity.

The author's three subqueries are not fixed outputs; their number and wording can differ. **Missing planning evidence makes the code stop with an error**; ordinary search is not called “planned retrieval.”

**Next:** [4. Judge calibration](#calibration) · [Progress map](#lab-map)

---

<a id="calibration"></a>
## 4. Calibrate and freeze the judge

**Check the grader before grading answers.** Calibration does not retrain a model; it tests whether the judge distinguishes predefined correct and incorrect answers.

<a id="acceptance-criteria"></a>
### 4-1. Read the acceptance criteria first

The acceptance criteria in [acceptance.json](../../advanced-rag/acceptance.json) are fixed before the fresh holdout:

**Keep three checks separate.**

- **Business checks:** do answer format, decision, amount, and citations match expectations?
- **Retrieval checks:** were the required policy chunks found?
- **Judge:** Groundedness measures support, Relevance measures relevance to the question, and `policy_task_success` checks policy-based task resolution.

**The answer model does not receive expected answers.** Code checks use them; the task-success judge also receives expected behavior for evaluation.

| Target | Passing condition |
|---|---|
| Every final V2 case | **100%** pass on business checks, required-evidence retrieval, Groundedness, **builtin Relevance**, and policy task success |
| Required judge scores | Each **at least 4/5** |
| Critical cases | **Zero failures**; an average must not hide a failed case |
| Policy-judge calibration | Correctly classify **all ten** positive/negative controls |
| Real retrieval evidence | Vector index/vectorizer and actual `modelQueryPlanning` activity |
| Fresh questions | Create/register **at least eight** holdout cases **after** freezing |

**Scores and pass rates are different.** `4/5` is the passing score for one answer, not 80% accuracy. A `100%` pass rate means every case in that stage must meet each required criterion.

**Builtin Relevance remains a required metric.** The final answer must resolve the actual completed user interaction. A request for missing information is an intermediate step, not falsely labeled as a completed answer.

**V2's user follow-ups are predefined in evaluation data.**

| Case | Follow-up interaction |
|---|---|
| Missing travel date | The model asks, then receives the user's actual travel date |
| Unavailable overseas limit | Instead of a fabricated number, the user requests a Finance inquiry checklist |

The model does not invent those user facts. The final conversation is supplied to the judge, but **automated initial-response checks cover only JSON format, decision, amount, and citation fields**.

The result field `intermediate_safe` means those field checks passed, **not that the initial prose received a separate semantic or safety evaluation**. Correct `unknown`, `null`, and `SCOPE` fields can coexist with a fabricated overseas limit in the explanation. Read the initial prose using `inspect --dialogue` in sections 5 and 7, and record your judgment.

> [!IMPORTANT]
> **Automated acceptance is not human production approval.** Even with `LAB_ACCEPTANCE_PASSED`, `human_production_approval` remains `PENDING`. `inspect` is read-only and saves no review or approval. Keep separate review records in your organization's approval process; do not edit automated results.

### 4-2. Run calibration

Read [the policy task-success rubric](../../advanced-rag/policy-task-success.txt). It treats correct missing-date questions and appropriate “policy does not specify” answers as **valid initial behavior**, while rejecting invented limits/approvals and contradictory answers. Correct initial behavior alone does not complete the final dialogue.

If calibration below is still processing or errors, use the **calibration row** in the [status/resume table](#resume).

```bash
python advanced_lab.py calibrate
```

**Checkpoint:** `CALIBRATION PASSED: 10 controls`.

**What was checked:** four correct controls and six incorrect controls, including a grading-instruction attack and extra citations, must be classified correctly. **Pass/fail labels are not sent to the judge.**

**Limit:** calibration tests **only `policy_task_success`** with authored responses and expected behavior. It is not held-out model performance or separate calibration of builtin Groundedness/Relevance.

The resulting evaluator version, rubric, model, and acceptance criteria are fixed in `results/advanced/judge-contract.json`. This is not permission to alter the judge after seeing holdout results.

**Next:** [5. V1 → V2 comparison](#improve) · [Progress map](#lab-map)

---

<a id="improve"></a>
## 5. Real V1 failure, then a controlled V2 improvement

The [recorded V1 fixture](../../advanced-rag/fixtures/recorded-v1.json) contains **four actual earlier LIVE answers for D02, D03, D04, and D08**, not fabricated wrong answers. D02's extra citation is retained. Replaying it is not claimed as fresh generation.

<a id="run-stages"></a>
### Understand the four stages

**`--stage` names the run to use**, with results in the matching subfolder of `results/advanced/`. This table explains the flow; **execute commands in sections 5 → 6 → 7**, not from the table.

| `--stage` value | Questions and retrieval inputs | What it checks |
|---|---|---|
| `v1-recorded` | Import four earlier dev answers and their retrieved contexts | How the current judge assesses the preserved V1 failure |
| `v2-replay` | Generate V2 answers for the same four dev cases and initial contexts | Whether the prompt/dialogue workflow improves without differences in retrieval |
| `planned-dev` | Run the same four dev cases again, starting with real retrieval | Whether V2 meets the criteria through the full retrieval-to-answer path |
| `holdout` | Run eight fresh cases created after freezing, starting with real retrieval | Whether the frozen candidate meets the criteria on cases not used for improvement |

After **both generation and judging** for `--stage v2-replay` finish, read `results/advanced/v2-replay/report.md`. The two V2 checks **separate a saved-context comparison from an integration check with real retrieval**; they are not retries to obtain better scores.

### 5-1. Import V1 answers and evaluate them with the current judge

**Action 1 — import the local V1 record**

```bash
python advanced_lab.py baseline
```

**Checkpoint:** `Imported four genuine recorded V1 answers.`

**Action 2 — evaluate with the current judge**

This is a **paid LIVE evaluation using the currently fixed judge**, not a copy of historical scores.

```bash
python advanced_lab.py judge --stage v1-recorded
```

**Checkpoint:** `Evaluation complete: 4 cases × 3 metrics`.

If still processing, repeat the identical `judge --stage v1-recorded` command. Continue only after completion.

**Action 3 — inspect D02's failure**

```bash
python advanced_lab.py inspect --stage v1-recorded --case-id D02
```

**Checkpoint:** find D02's `citations: false` under `Business checks` and read `Scores`.

| Value to compare | Citations |
|---|---|
| Expected | `["TRAVEL-CURRENT"]` |
| Recorded V1 | `["TRAVEL-CURRENT", "SCOPE"]` |

The unnecessary `SCOPE` citation fails the exact citation-set check. **A retrieved source is not necessarily required in the answer.** Read the judge's reasons in `results/advanced/v1-recorded/report.md`.

<a id="read-case"></a>
### 5-2. Read a case's expectations and actual evidence

`inspect` **only reads results whose generation and judging are both complete**. Add `--context` to display the actual retrieved context supplied to the answer. You do not need to rerun `run` or `judge` to investigate a failure.

**Start with the answer's four JSON fields.** JSON stores named values; the code saves these fields automatically. Do not fill them in or edit them yourself.

| Answer field | Meaning |
|---|---|
| `decision` | The policy-based decision: one of the five values below |
| `limit_krw` | The applicable lodging limit in KRW, not the claimed expense. `null` means the limit cannot be determined or lodging limits do not apply; **it does not mean zero** |
| `citations` | Official source IDs used by the answer, such as `["TRAVEL-CURRENT"]` |
| `answer` | The employee-facing explanation. Read it for contradictions even when the field checks pass |

The `decision` values are `allowed`, `needs_approval` (prior approval required), `not_allowed`, `unknown` (absent from policy), and `needs_info` (missing user information). **Declining to guess an absent limit with `unknown`, or asking for the travel date with `needs_info`, can be correct initial behavior.** These values do not execute reimbursement or grant approval.

Then compare expectations, retrieval, and scores for the same case:

| Output | What to check |
|---|---|
| `Case result` | Whether this case meets the automated criteria. `FAIL` means answer/retrieval/score criteria were missed, not that the inspection command failed. `PASS` is not production approval |
| `Question` | The question for the case being inspected |
| `Expected decision / limit / citations`, `Expected behavior` | Predefined decision, limit, minimum citations, and expected behavior. **Not model-generated answers** |
| `Actual answer`, `Business checks` | Compare the answer with expectations. `true` passes that check; `false` fails it, such as D02's `citations: false` |
| `Required chunks` → `Chunks` → `Required chunks found` | Required policy fragments → retrieved fragments → whether every required fragment was found. Chunk IDs differ from the answer's official citation IDs |
| `Scores` / `Final scores` | Each of the three metrics must be **at least 4**. High judge scores do not cancel business or retrieval failures |
| That stage's `report.md` | Match the same case ID and compare its **scoring reasons** with the actual answer |

**For D02**, `current-lodging` is the chunk ID and `TRAVEL-CURRENT` is its official source ID. Finding the required chunk does not prevent a business-check failure if the answer also cites unnecessary `SCOPE`.

**For dialogue cases, expectations and retrieval checks describe the final response**. Distinguish initial and final answers in the `--dialogue` output below. Even when `Initial field checks` is `true`, the initial explanation has not received semantic evaluation.

**If you arrived here from an error**, inspect the failed cases, then return to the [status/resume table](#resume). Preserve the failed experiment and record unperformed later stages in section 8.

### 5-3. Understand, generate, and evaluate V2

Compare [V1](../../advanced-rag/instructions.v1.txt) and [V2](../../advanced-rag/instructions.v2.txt). V2 distinguishes the minimum sufficient decision/amount evidence from merely retrieved or procedural sources, and completes necessary clarification/handoff interactions.

[Development follow-ups](../../advanced-rag/dev-followups.json) are declared before generation. They are scripted evaluation-user turns, not real customer statements or human production approvals. They contain no desired score. **The code sends these follow-ups automatically; you do not need to type a travel date or another question into the terminal.**

**Use the supplied V2 unchanged in this run.** Explain the differences without editing the instructions, then execute. Personal prompt changes belong to a [separate experiment](#resume) after preserving this run.

**Action 1 — generate V2 using the same initial retrieval context**

```bash
python advanced_lab.py run --stage v2-replay
```

**Checkpoint:** `GENERATION COMPLETE: v2-replay; 4 answers.`

This counts **four final answers** after necessary follow-ups, not every intermediate model call.

**Action 2 — evaluate V2**

```bash
python advanced_lab.py judge --stage v2-replay
```

**Checkpoint:** `Evaluation complete: 4 cases × 3 metrics`.

If pending, repeat the same judging command.

**Action 3 — compare D02 with V1**

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D02
```

<a id="dialogue-check"></a>
### 5-4. Read the full D04 and D08 dialogues

Check initial prose for contradictions, using any problematic sentence as evidence for your judgment:

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D04 --dialogue
```

```bash
python advanced_lab.py inspect --stage v2-replay --case-id D08 --dialogue
```

| Output label | How to read it |
|---|---|
| `User` → `Assistant` | Initial question → initial answer; check for fabricated limits or approvals |
| `Evaluation-user follow-up` | A scripted user turn from evaluation data, not something you just typed |
| `Final answer` → `Final scores` | Answer completing the follow-up request → its three final-response scores |
| `Initial field checks (not prose evaluation)` | Initial field checks only, not a semantic pass for initial prose |

**Checkpoint:** explain D02's changed citations and D04/D08's follow-up outcomes.

**Interpretation:** V1 and V2 start from identical saved contexts and use the same answer model/settings/judge, with explicit user follow-ups completed where needed. This is a **prompt-and-dialogue workflow improvement**, not an effect attributable only to prompt wording. Keep the V1 failure; do not weaken V1 or reroll it.

**Next:** [6. Full pipeline and freeze](#freeze) · [Progress map](#lab-map)

---

<a id="freeze"></a>
## 6. Validate the full pipeline, then freeze

**This is not a repeat of the same run.** Section 5 checked V2 against saved initial retrieval contexts; `planned-dev` now checks the path from real vector/LLM-planned retrieval through the final answer.

### 6-1. Generate and evaluate with real retrieval

```bash
python advanced_lab.py run --stage planned-dev
```

**Checkpoint:** `GENERATION COMPLETE: planned-dev; 4 answers.` before judging.

```bash
python advanced_lab.py judge --stage planned-dev
```

**Checkpoint:** `Evaluation complete: 4 cases × 3 metrics`.

If pending, repeat the same judging command. Both initial questions and necessary follow-up turns use the declared retrieval workflow. **Judge exit code 0 alone does not mean dev acceptance.**

### 6-2. Freeze the passing candidate's conditions

**Do not change V2 instructions, follow-ups, models, or settings between sections 5 and 6.** Both dev validations must use the same candidate and input contract. If a change is needed, preserve existing results and perform both validations in a [new experiment](#resume).

```bash
python advanced_lab.py freeze
```

**Checkpoint:** `FROZEN` and a contract hash.

| Check | Meaning |
|---|---|
| Freeze conditions | V1 has a real failure; V2 replay and planned dev both meet the criteria |
| Frozen inputs | Prompt, judge, model versions, retrieval configuration, source definitions, and corpus |
| Contract hash | A fingerprint for detecting changed conditions; do not copy it into another command |

**If blocked, do not continue to holdout.** Preserve the cause and unperformed stages using the [resume table](#resume).

**If you see `Dev acceptance is not met`**, the error prints each failed stage/case ID, its `report.md`, and ready-to-run `inspect --context` commands. Use them to [compare expectations and actual evidence](#read-case). Unlike an input typo, dev quality blocking is not resolved by repeatedly generating or judging the same experiment.

**After `FROZEN`, next:** [7. Fresh questions](#holdout) · [Progress map](#lab-map)

---

<a id="holdout"></a>
## 7. Generate fresh questions only after freeze

### 7-1. Create and register eight fresh questions

```bash
python advanced_lab.py create-holdout
```

A new random seed **fills in new dates, cities, and amounts in eight predefined scenarios**. They cover current/previous limits, over-limit approval, overseas scope, missing dates, prohibited flight class, and the exact boundary.

**Scope and limit:** these are fresh parameterized cases, not broad blind generalization testing. Missing-date and overseas-handoff cases include explicit evaluation-user follow-ups.

**Saved under:** `results/advanced/holdout-data/`, containing inputs, follow-ups, expectations, and provenance.

**Checkpoint:** `HOLDOUT REGISTERED: 8 new cases` and `holdout-registration.json`.

The command creates and registers questions without a model call and refuses to replace existing files. **Do not resample to obtain a pass.** Follow the [resume table](#resume) after interruption.

### 7-2. Generate and evaluate with the frozen candidate

```bash
python advanced_lab.py run --stage holdout
```

**Checkpoint:** `GENERATION COMPLETE: holdout; 8 answers.` before judging.

```bash
python advanced_lab.py judge --stage holdout
```

**Checkpoint:** `Evaluation complete: 8 cases × 3 metrics`.

If pending, repeat the same judging command. After completion, read both follow-up dialogues below.

### 7-3. Review the N05 and N06 dialogues

Use the [output labels explained earlier](#dialogue-check) to read **both initial prose and final answers**, then record your judgment.

```bash
python advanced_lab.py inspect --stage holdout --case-id N05 --dialogue
```

```bash
python advanced_lab.py inspect --stage holdout --case-id N06 --dialogue
```

### 7-4. Read the final automated decision and evidence

```bash
python advanced_lab.py accept
```

**Checkpoint:** `results/advanced/acceptance-report.md` and `acceptance-result.json` are saved. Read **your own run** in this order:

| File, relative to `results/advanced/` | What to check |
|---|---|
| `acceptance-report.md` | Decision in the title → pass rates by stage |
| `acceptance-result.json` | N01–N08 under `rows` → `business_checks`, `required_chunks_found`, `scores`, `passed`; also `intermediate_safe` for multi-turn cases |
| `holdout/report.md` | Actual answer and reasons for each judge score, matched by case ID |

| Output | Meaning and next action |
|---|---|
| `LAB_ACCEPTANCE_PASSED` | All eight fresh cases pass **every final-answer metric, including Relevance, plus the initial field checks**. Human production approval remains separate |
| `LAB_ACCEPTANCE_BLOCKED` / exit `2` | A quality hold. Record the failure and continue to section 8 |
| `ERROR:` / `usage:` | Execution or input error. Resolve it first; do not mark the run complete |

If blocked, record the failure and hold recommendation, then go to section 8. Even with an automated pass, record any contradiction you find in the initial prose and withhold production adoption. Do not edit the frozen prompt/rubric or select only passing cases. A subsequent improvement uses a [new experiment in a separate working copy](#resume) with new held-out cases.

**Next:** [8. Results and resource retention](#retention) · [Progress map](#lab-map)

---

<a id="retention"></a>
## 8. Preserve results and resources

Keep the shared Basic Search service, embedding/planning/answer deployments, and every calibration, V1/V2, freeze, and fresh-question result you actually produced, **including failures**. Use generated reports to identify the last completed stage, pass/hold reasons, and unperformed work; establish the resource owner and next cost-review point. Basic service charges continue.

### Your run's completion checklist

**Check completion status and counts, not just file existence.** If blocked earlier, leave later items unchecked and record the **last completed stage, error or quality failure, and unperformed stages**. Do not call it a completed end-to-end run.

- [ ] `setup.json` and both query JSON files show real vector and query-planning evidence.
- [ ] `calibration-result.json` shows `passed: true` for ten controls, and `judge-contract.json` is present.
- [ ] `v1-recorded` has four imported answers; `v2-replay` and `planned-dev` each have four new answers, all with three scores and reasons.
- [ ] Eight fresh questions were registered after `frozen.json`, and holdout generation/judging completed.
- [ ] I read the initial N05/N06 prose and can explain my `acceptance-report.md` decision and reasons.
- [ ] I retained the full results folder, verified the actual Azure resources, and recorded costs and the next review condition.

**Opening the report:** in VS Code, press Ctrl+P / macOS Cmd+P and enter `results/advanced/acceptance-report.md`. Read the summary in Markdown preview, then match a failing case ID using the section 7 file table. Do not edit automated result files to mark review or approval.

**Cost check:** in Azure portal, scope **Cost Management → Cost analysis** to your group. If reusing Search in another group, check that cost with its owner too. Zero before costs are posted does not mean free usage. Follow only the [retention procedure](cleanup.md#retain-resources); skip deletion unless separately authorized.

**Checkpoint:** use your result files and actual dialogues to explain V1's failure, V2's changes, and fresh-question results and limitations. If an earlier stage stopped, state that later stages were not run, and verify the retained resources and cost status.

Finish with your own evidence: **“V1 had ___ problem. V2 changed ___. Fresh questions showed ___, so my decision is ___.”** Completed evaluation and an evidence-based hold are valid even with low scores. Automated acceptance is not production approval.

Keep your actual `config.json`/`config.advanced.json`, raw recordings, and `results/` outside Git. Preserve versioned instructions and the sanitized V1 teaching fixture.

[Back to the progress map](#lab-map) · [Find a resumption point](#resume)

---

<a id="results"></a>
## Reference: the author's recorded run

**You do not need to reproduce this record to finish your own lab.**

<details>
<summary>Expand September 28, 2026 observations and environment-retention records</summary>

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

**The following is the author's historical migration record, not a learner deletion step.** Do not delete resources without a separate decision. Never delete the resource group or shared Foundry account to clean one Search service. Do not rewrite Git history or platform audit logs, or disable organizational policies.

**September 28, 2026 rebuild record:** the owner explicitly requested deletion of the previous dedicated workshop group. Its deletion was verified before the rerun in a new group. Previous local results and raw recordings were preserved. Retain the new Basic service, Foundry resource, three model deployments, and current calibration/V1/V2/holdout evidence **until a separate request**. No other groups or organizational policies were changed.

**Cost checkpoint:** a MonthToDate Cost Management query scoped to the new group returned no cost rows yet. This is pending cost reporting, not proof of free usage; Basic capacity and model usage can continue to incur charges. Recheck after usage is posted or when a separate cleanup decision is made.

</details>

## Official references

- [Agentic vector index and vectorizer](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-index)
- [Knowledge-base features and models by API version](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base)
- [Azure OpenAI vectorizer identity and role](https://learn.microsoft.com/azure/search/vector-search-vectorizer-azure-open-ai)
- [Search user roles and service scope](https://learn.microsoft.com/azure/search/search-security-rbac)
- [LLM retrieval reasoning effort](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [Search tier feature support](https://learn.microsoft.com/azure/search/search-sku-tier)
- [Embeddings with Entra authentication](https://learn.microsoft.com/azure/foundry/openai/how-to/embeddings)
- [Custom Foundry evaluators](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)

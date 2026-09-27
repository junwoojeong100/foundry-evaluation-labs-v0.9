**English** | [한국어](../optional-rag.md)

# Optional: Azure AI Search + Foundry IQ RAG and evaluation

[Core workshop](../../README.md) · [Korean core guide](../../README.ko.md)

This is an **optional extension, not a replacement for activities 0–6**. The core workshop supplies the full policy. Here, **only actually retrieved documents** reach the answer model and Groundedness judge. Evaluate retrieval and answer quality separately.

Reuse the intended account, Foundry project, **`gpt-6-luna` / `eval-model`**, and **`swedencentral`**. Add an Azure AI Search service, index, and actual Foundry IQ Knowledge Source/Knowledge Base. **Retain all resources and evidence.**

**Additional recordings:** [English/Korean Optional RAG summaries and subtitles](../media/optional-rag/README.md).

## What is used

| Route | Actual operation |
|---|---|
| `search` | Semantic query against an Azure AI Search index |
| `iq` | Foundry IQ Knowledge Base `retrieve` → search-index Knowledge Source → the same index |
| Both | Up to three returned approved chunks → `gpt-6-luna` answer → retrieval metrics, business checks, and Foundry Evaluation |

This is **not local search relabeled as Foundry IQ**. Real knowledge objects are created, and IQ `references`, `sourceData`, and `activity` are retained.

The simple path uses **GA Search API `2026-04-01`, minimal/extractive retrieval**. It does not use vector embeddings, LLM query planning, answer synthesis, or Agent Service/MCP integration. `gpt-6-luna` generates and judges answers in the application; it is not a knowledge-base planner. Official Foundry IQ documentation supports custom applications calling this REST API directly.

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

Use the core virtual environment, `requirements.txt`, real `config.json`, project, and deployment. No agent server, Docker, Storage, or embedding deployment is added.

```bash
python lab.py doctor --live
```

Confirm `LIVE 조회 OK` for `gpt-6-luna` / `eval-model`. Match the portal and CLI account, tenant, and subscription using the core guide.

Use the **Free Search SKU** and **Free semantic/knowledge-retrieval plans** where available. Sweden Central support and the subscription's Free slot must be checked. If that slot is occupied, do not delete another service. Reuse an authorized environment or **explicitly choose a paid Basic-or-higher service and its ongoing costs**. There is no automatic upgrade.

The extension has **7 chunks, 4 questions × 2 routes = 8 answers and 16 judge metric items**. Retrieval and evaluator internals are separate requests. Model generation/judging costs money; free retrieval allowances can be exhausted. Retaining resources is not equivalent to free usage.

<a id="create-search"></a>
## 2. Search service and least-privilege access

Replace all placeholders with real values. You can reuse the core dedicated group. The service name must be globally unique and use lowercase letters, digits, and dashes.

```bash
az search service check-name-availability --name "YOUR-SEARCH-NAME" --type searchServices --subscription "YOUR-SUBSCRIPTION-ID"
```

Proceed only with `nameAvailable: true`.

```bash
az search service create --name "YOUR-SEARCH-NAME" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --location swedencentral --sku free --semantic-search free --disable-local-auth true
```

This **disables API keys**. Do not retrieve or store keys. You can record `retain=true` under portal Tags; a tag is not a deletion lock.

```bash
az search service show --name "YOUR-SEARCH-NAME" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,location:location,sku:sku.name,state:provisioningState,disableLocalAuth:disableLocalAuth,semanticSearch:semanticSearch}" --output json
```

Confirm Succeeded/succeeded, Sweden Central, `free`, and `disableLocalAuth: true`. Use the returned `id`, ending in `/providers/Microsoft.Search/searchServices/...`, as `YOUR-SEARCH-RESOURCE-ID`.

Grant the following roles to the **user Object ID already verified in the core guide**, at the **Search service scope only**, and only if missing:

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "7ca78c08-252a-4471-8644-bb5ff32d4ba0" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "8ebe5a00-799e-43f5-93ac-243d3dce84a7" --scope "YOUR-SEARCH-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

The roles are **Search Service Contributor** for index/knowledge-object management and **Search Index Data Contributor** for document upload/query. Do not grant subscription-wide roles. This custom-app path does not query using the project identity, so it does not need additional project-managed-identity assignments.

<a id="index"></a>
## 3. Create the index and actual Foundry IQ knowledge objects

Save [the example](../../optional-rag/config.example.json) as **`config.rag.json`** beside `lab.py`. Copy the actual service URL from Search Overview. Keep the original `config.json` unchanged.

```json
{
  "search_endpoint": "https://YOUR-SEARCH.search.windows.net",
  "index_name": "travel-rag-index",
  "knowledge_source": "travel-policy-ks",
  "knowledge_base": "travel-policy-kb",
  "top_k": 3
}
```

```bash
python rag_lab.py setup
```

**Checkpoint:** `SETUP OK: 7 chunks, 4 evaluation cases`. `results/rag-setup.json` contains actual index, Knowledge Source, and Knowledge Base definitions.

The [corpus](../../optional-rag/documents.jsonl) divides the fictional policy into seven chunks: six official chunks and one unapproved draft. **`approved eq true`** excludes the draft; a `corpus_hash` filter fixes the corpus version. The index includes a Korean analyzer and semantic configuration. Both language guides use the same Korean inputs.

Setup resumes incomplete uploads for the same corpus, but does not overwrite objects belonging to another corpus/source. Use new object names for changed experiments.

**Security distinction:** service RBAC controls access. `approved` is a policy-status filter, not a per-user ACL. Document-level authorization, Purview, and user-specific access tests are outside this small lab.

<a id="retrieve"></a>
## 4. Verify both real retrieval routes

```bash
python rag_lab.py query --mode search --query "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?" --out results/rag-query-search.json
```

```bash
python rag_lab.py query --mode iq --query "2026년 9월 국내 숙박비가 220000원이고 사전 승인이 없습니다. 정산 가능한가요?" --out results/rag-query-iq.json
```

The question asks about a September domestic hotel expense of KRW 220000 without prior approval.

**Checkpoint:** both print `RETRIEVAL OK`, selected chunk IDs, official source IDs, and scores. IQ also returns **searchIndex activity and original reference/source data**. The saved JSON comes from the real services.

| Identifier | Purpose |
|---|---|
| Chunk ID, such as `current-lodging` | Retrieval ground-truth matching |
| Official `source_id`, such as `TRAVEL-CURRENT` | The answer's `citations` |
| IQ reference `id` / `activitySource` | Links a returned document with that request's retrieval activity |

IQ uses `intents`. The app takes at most three returned approved chunks. **Empty or failed retrieval stops explicitly; it never silently supplies the full policy instead.**

<a id="evaluate"></a>
## 5. Evaluate retrieval and answers independently

The [four cases](../../optional-rag/cases.jsonl) reuse core dev D02/D03/D04/D08; they are not a new independent holdout. [Required-chunk labels](../../optional-rag/retrieval-labels.json) are evaluation-only and never enter the retrieval request, generation prompt, or judge.

```bash
python rag_lab.py run --mode search --out results/rag-search
```

After four answers are saved:

```bash
python lab.py judge results/rag-search
```

Wait for **`평가 완료: 4개 답변 × 2개 지표`**. If still processing, repeat that exact command.

```bash
python rag_lab.py run --mode iq --out results/rag-iq
```

```bash
python lab.py judge results/rag-iq --like results/rag-search
```

Confirm **`평가 완료: 4개 답변 × 2개 지표`**. `--like` preserves the judge model/evaluator contract.

```bash
python rag_lab.py compare results/rag-search results/rag-iq
```

```bash
python rag_lab.py inspect results/rag-iq D04
```

Read the retrieved chunks, missing required chunks, answer, business checks, and judge reasons—in that order. **Groundedness receives exactly the per-case context used to generate that answer**, not the original full corpus.

| Metric | Meaning and limit |
|---|---|
| Required-chunk Recall@3 | Fraction of required chunks included in model context |
| Precision@3 | Fraction of delivered chunks listed as required; useful auxiliary chunks might not be labeled |
| Business checks | Format, decision, amount, and citations |
| Groundedness | Support in the retrieved evidence actually supplied |
| Relevance | Response to the question; appropriate abstention may still score poorly |
| Citation IDs linked | Citation IDs occur in retrieved documents; not proof of semantic support |

Read `results/rag-iq/rag-comparison.md`/`.json`, and each run's `rag-report.md` and `retrieval-metrics.json`. **REVIEW_REQUIRED is not release approval or proof IQ is superior.** A person must examine contexts and scoring reasons.

Core `lab.py compare/gate` is for fixed-context prompt experiments and rejects RAG input. Use this extension's comparison. Do not combine core and RAG results as a single before/after experiment.

<a id="evidence"></a>
## 6. Portal evidence and retention

In the Search service's Azure portal view, inspect **Indexes**, **Knowledge sources**, and **Knowledge bases**. Portal/preview UI may differ from GA API behavior; saved service definitions/responses are the setup and retrieval evidence.

In the Foundry evaluation report URL, match a case's **question, answer, retrieved context, scores, and reasons**. Supplying the entire policy as `context` would be incorrect for this extension.

`run.json` records route/configuration, corpus hash, raw retrieval, references/activity, exact context/hash, and model output. If retrieval completed but generation was interrupted, the saved retrieval is reused. Completed runs read their evidence without another generation call.

- **Retain** the Search service, knowledge objects, existing Foundry resources, and evaluations.
- Do not automatically enable paid plans after a free allowance is exhausted.
- Keep `config.rag.json`, `config.json`, and `results/` out of Git.
- Preserve low scores and failures; do not rerun until results look better.

<a id="observed-results"></a>
### September 28, 2026: actual execution

The Search SKU and semantic/knowledge-retrieval plans were Free, with API keys disabled. The real index, Knowledge Source, and Knowledge Base were created. **Eight answers and sixteen judge metric items** were saved in two completed remote evaluation runs.

| Route | Required-chunk Recall@3 | Business checks | Groundedness ≥4 | Relevance ≥4 |
|---|---|---|---|---|
| Search | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 3/4 (75%) |
| Foundry IQ | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) | 2/4 (50%) |

**All four questions had identical retrieved contexts across the routes.** In the IQ run, D02's amount and decision were correct, but an extra `SCOPE` citation failed the exact-set check. This is a difference in one generation/judging trial, **not proof that IQ retrieval is worse**. Retrieval and answer quality remain distinct, and the result is `REVIEW_REQUIRED`.

Local `results/rag-verification.json` and each run folder record the evidence and equality between generation context and the original remote evaluation input. Original retrievals, answers, and scores are preserved; resources remain deployed.

<a id="troubleshooting"></a>
## Troubleshooting

| Symptom | Action |
|---|---|
| Free service cannot be created | Check the subscription slot and regional availability; do not delete another service. |
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
- [Retrieve API](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve)
- [Region and Free support](https://learn.microsoft.com/azure/search/search-region-support)
- [Knowledge retrieval billing](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-enable-disable)
